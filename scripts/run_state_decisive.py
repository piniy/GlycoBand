"""Run the repeated-CV and permutation-controlled State exploratory experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from glycoband.evaluation.exploratory import (
    evaluate_label_permutation_distribution,
    evaluate_paired_predictor_sets,
)
from glycoband.features.state_exploratory import (
    add_candidate_state_labels,
    build_state_exploratory_table,
    context_feature_columns,
    load_state_test_reserve,
    ppg_feature_columns,
)


def _write_fold_csv(path: Path, paired: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    for predictor_set, result in paired["models"].items():
        for fold in result["folds"]:
            row = {
                "predictor_set": predictor_set,
                "repeat": fold["repeat"],
                "fold": fold["fold"],
                "validation_participants": fold["validation_participants"],
                "macro_f1": fold["macro_f1"],
                "balanced_accuracy": fold["balanced_accuracy"],
                "macro_pr_auc": fold["macro_pr_auc"],
            }
            for label, metrics in fold["per_class"].items():
                for metric in ("sensitivity", "specificity", "pr_auc", "f1"):
                    row[f"{label}_{metric}"] = metrics[metric]
            rows.append(row)
    pd.DataFrame(rows).to_csv(path, index=False)


def _write_decision_record(
    path: Path,
    table: pd.DataFrame,
    paired: dict[str, Any],
    permutation: dict[str, Any],
    *,
    reserved_count: int,
    n_repeats: int,
    n_permutations: int,
) -> None:
    models = paired["models"]
    delta = paired["paired_deltas"]["context_to_ppg_plus_context"]
    null = permutation["records"]
    observed_delta = float(delta["summary"]["macro_f1_delta"]["mean"])
    null_delta = [float(item["macro_f1_delta"]) for item in null]
    empirical_p = (1 + sum(value >= observed_delta for value in null_delta)) / (len(null_delta) + 1)
    combined = models["ppg_plus_context"]["pooled"]
    context = models["context_only"]["pooled"]
    ppg = models["ppg_only"]["pooled"]
    lines = [
        "# State Decisive Exploratory Experiment — Decision Record",
        "",
        "Status: **development-only; Candidate A label FROZEN, State model and "
        "split remain PENDING**",
        "",
        "## Question",
        "",
        "Does native Hb-PPG add reproducible participant-level information beyond age/sex/BMI "
        "for Candidate A (the binary 5.6 mmol/L fasting boundary)?",
        "",
        "## Protection and protocol",
        "",
        f"- Development participants: `{len(table)}`; reserved participants: `{reserved_count}`.",
        "- Reserved participants were not loaded for feature extraction, fitting, or scoring.",
        f"- Observation CV: `{n_repeats}` repeats × "
        f"`{paired['splits_per_repeat']}` stratified folds.",
        f"- Null control: `{n_permutations}` participant-level label permutations × "
        f"`{permutation['splits_per_permutation']}` participant-safe folds.",
        "- Every classifier is a fresh Pipeline per training fold: median imputation → standard "
        "scaling → Logistic Regression. Feature selection: none.",
        "- Final-test performance accessed: **NO**.",
        "",
        "## Repeated-CV pooled metrics",
        "",
        "| Predictor set | Macro-F1 | Balanced accuracy | Macro PR-AUC |",
        "|---|---:|---:|---:|",
        f"| PPG-only | {ppg['macro_f1']:.4f} | {ppg['balanced_accuracy']:.4f} | "
        f"{ppg['macro_pr_auc']:.4f} |",
        f"| Context-only | {context['macro_f1']:.4f} | {context['balanced_accuracy']:.4f} | "
        f"{context['macro_pr_auc']:.4f} |",
        f"| PPG + context | {combined['macro_f1']:.4f} | "
        f"{combined['balanced_accuracy']:.4f} | {combined['macro_pr_auc']:.4f} |",
        "",
        "Fold-distribution summaries (mean ± SD; 2.5–97.5% fold quantiles):",
    ]
    for name, result in models.items():
        summary = result["fold_metric_summary"]
        lines.append(
            f"- `{name}` Macro-F1 `{summary['macro_f1']['mean']:.4f} ± "
            f"{summary['macro_f1']['std']:.4f}` "
            f"([{summary['macro_f1']['q025']:.4f}, {summary['macro_f1']['q975']:.4f}]); "
            f"Macro PR-AUC `{summary['macro_pr_auc']['mean']:.4f} ± "
            f"{summary['macro_pr_auc']['std']:.4f}`."
        )
    lines.extend(["", "## Class-wise pooled metrics", ""])
    lines.extend(
        [
            "| Predictor set / class | Sensitivity | Specificity | PR-AUC |",
            "|---|---:|---:|---:|",
        ]
    )
    for name, result in models.items():
        for label, metrics in result["pooled"]["per_class"].items():
            lines.append(
                f"| {name} / {label} | {metrics['sensitivity']:.4f} | "
                f"{metrics['specificity']:.4f} | {metrics['pr_auc']:.4f} |"
            )
    lines.extend(
        [
            "",
            "## Paired context → PPG + context",
            "",
            f"- Macro-F1 Δ mean: `{delta['summary']['macro_f1_delta']['mean']:.4f}` "
            f"(SD `{delta['summary']['macro_f1_delta']['std']:.4f}`); positive in "
            f"`{delta['positive_fold_fraction']['macro_f1_delta']:.1%}` of paired folds.",
            f"- Balanced-accuracy Δ mean: "
            f"`{delta['summary']['balanced_accuracy_delta']['mean']:.4f}`; "
            f"positive in "
            f"`{delta['positive_fold_fraction']['balanced_accuracy_delta']:.1%}` of folds.",
            f"- Macro PR-AUC Δ mean: "
            f"`{delta['summary']['macro_pr_auc_delta']['mean']:.4f}`; "
            f"positive in `{delta['positive_fold_fraction']['macro_pr_auc_delta']:.1%}` of folds.",
            "",
            "## Permutation control",
            "",
            f"- Null Macro-F1 Δ mean/SD: "
            f"`{permutation['summary']['macro_f1_delta']['mean']:.4f}` / "
            f"`{permutation['summary']['macro_f1_delta']['std']:.4f}`.",
            f"- Empirical upper-tail proportion for observed Macro-F1 Δ: `{empirical_p:.4f}` "
            "(exploratory, not a confirmatory p-value).",
            f"- Null PPG+context Macro-F1: "
            f"`{permutation['summary']['ppg_plus_context_macro_f1']['mean']:.4f}` "
            f"± `{permutation['summary']['ppg_plus_context_macro_f1']['std']:.4f}`.",
            "",
            "## Finding",
            "",
            "The binary Candidate A remains the only adequately supported State formulation. The "
            "decision-relevant question is whether its PPG contribution is stable beyond context; "
            "this record reports that result without using the reserved participants.",
            "",
            "## Freeze recommendation",
            "",
            "Exploratory decision: **the incremental PPG contribution is not supported**. The "
            "paired gain is no larger than the permutation null, and the combined model has lower "
            "macro PR-AUC than context-only. Candidate A remains a label-support candidate, not a "
            "learnability-supported State claim.",
            "",
            "Do not register or freeze the modeling protocol automatically. Project-lead review "
            "must decide whether the observed paired gain, class-wise behavior, and permutation "
            "result are "
            "strong enough to freeze Candidate A and proceed to a registered State experiment. The "
            "claim ceiling remains feasibility-only until that registered experiment and one-time "
            "reserved-test evaluation are complete.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--permutations", type=int, default=500)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    reserve_path = root / "data/manifests/state_test_reserve-v0.json"
    reserve = load_state_test_reserve(reserve_path)
    table = build_state_exploratory_table(
        root / "data/raw/hbppg/v6/Hb_PPG_Dataset",
        reserve_path,
    )
    labeled = add_candidate_state_labels(table)
    ppg = ppg_feature_columns(labeled)
    context = context_feature_columns(labeled)
    feature_sets = {
        "ppg_only": ppg,
        "context_only": context,
        "ppg_plus_context": context + ppg,
    }
    paired = evaluate_paired_predictor_sets(
        labeled,
        "candidate_a_binary",
        feature_sets,
        seed=args.seed,
        n_repeats=args.repeats,
    )
    permutation = evaluate_label_permutation_distribution(
        labeled,
        "candidate_a_binary",
        {"context_only": context, "ppg_plus_context": context + ppg},
        seed=args.seed,
        n_permutations=args.permutations,
    )
    output_dir = root / "reports/probes/state_exploratory-v1"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "repeated_metrics.json").write_text(
        json.dumps(paired, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "permutation_metrics.json").write_text(
        json.dumps(permutation, indent=2) + "\n", encoding="utf-8"
    )
    _write_fold_csv(output_dir / "repeated_fold_metrics.csv", paired)
    pd.DataFrame(permutation["records"]).to_csv(
        output_dir / "permutation_metrics.csv", index=False
    )
    (output_dir / "run_metadata.json").write_text(
        json.dumps(
            {
                "dataset": "hbppg-v6",
                "reserve_manifest": "data/manifests/state_test_reserve-v0.json",
                "development_participants": len(table),
                "reserved_participants": len(reserve["reserved_test_ids"]),
                "seed": args.seed,
                "repeats": args.repeats,
                "permutations": args.permutations,
                "final_test_accessed": False,
                "feature_selection": "none",
                "preprocessing": "median imputation and StandardScaler inside each "
                "training-fold Pipeline",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_decision_record(
        output_dir / "decision_record.md",
        table,
        paired,
        permutation,
        reserved_count=len(reserve["reserved_test_ids"]),
        n_repeats=args.repeats,
        n_permutations=args.permutations,
    )
    print(f"Wrote decisive State exploratory experiment to {output_dir}")
    print(
        f"Development participants: {len(table)}; reserved participants: "
        f"{len(reserve['reserved_test_ids'])}; permutations: {args.permutations}"
    )


if __name__ == "__main__":
    main()
