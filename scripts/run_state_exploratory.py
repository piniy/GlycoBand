"""Run the Hb-PPG development-only State exploratory probe."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from glycoband.evaluation.exploratory import run_state_exploratory_analysis
from glycoband.features.state_exploratory import (
    build_state_exploratory_table,
    create_state_test_reserve,
    load_state_test_reserve,
)


def _provisional_verdict(candidate: dict[str, Any]) -> str:
    support = candidate["development_support"]
    if min(support.values()) < 20:
        return "WEAK"
    ppg = candidate["ppg_only"]["models"]["logistic"]["pooled"]
    dummy = candidate["ppg_only"]["models"]["dummy"]["pooled"]
    if ppg["macro_f1"] is None or dummy["macro_f1"] is None:
        return "UNSUPPORTED"
    return "VIABLE" if ppg["macro_f1"] >= dummy["macro_f1"] + 0.05 else "WEAK"


def _write_brief(path: Path, results: dict[str, Any]) -> None:
    lines = [
        "# State Exploratory Probe",
        "",
        "Question: does Hb-PPG contain enough participant-level predictive information to justify "
        "freezing a State formulation?",
        "",
        "Probe: Hb-PPG v6; one feature row per participant; deterministic outer reserve; "
        "participant-safe stratified development CV; Dummy and Logistic Regression; one "
        "participant-level label permutation control.",
        "",
        "Reserve rule: `data/manifests/state_test_reserve-v0.json`; reserved participants were "
        "excluded from feature extraction, fitting, and scoring.",
        "",
        f"- Development participants: `{results['participant_count']}`",
        f"- Seed: `{results['seed']}`",
        "- Final-test performance accessed: **NO**",
        "",
    ]
    for name, candidate in results["candidates"].items():
        lines.extend(
            [
                f"## {name}",
                "",
                f"Scientific rationale: {candidate['scientific_rationale']}",
                f"Development support: `{candidate['development_support']}`",
                f"Provisional probe verdict: **{_provisional_verdict(candidate)}**",
                "",
            ]
        )
        for comparison in ("ppg_only", "context_only", "ppg_plus_context"):
            pooled = candidate[comparison]["models"]["logistic"]["pooled"]
            folds = candidate[comparison]["models"]["logistic"]["folds"]
            fold_scores = [fold["macro_f1"] for fold in folds if fold["macro_f1"] is not None]
            lines.append(
                f"- {comparison}: Logistic Macro-F1 `{pooled['macro_f1']}`, "
                f"balanced accuracy `{pooled['balanced_accuracy']}`, "
                f"fold Macro-F1 range `{min(fold_scores):.3f}-{max(fold_scores):.3f}`"
            )
        permutation = candidate.get("permutation_control")
        if permutation is not None:
            pooled = permutation["models"]["logistic"]["pooled"]
            lines.append(
                f"- permutation control: Macro-F1 `{pooled['macro_f1']}`, "
                f"balanced accuracy `{pooled['balanced_accuracy']}`"
            )
        lines.extend(
            [
                "",
                "Main weakness: exploratory development performance is not confirmatory evidence; "
                "support and clinical meaning still require project-lead review.",
                "",
            ]
        )
    regression = results["continuous_sanity_check"]["models"]
    lines.extend(
        [
            "## Leading recommendation (not a freeze)",
            "",
            "Candidate A (binary 5.6 mmol/L boundary) is the only formulation with comfortable "
            "development participant support (136/37 after the outer reserve; 171/46 in the full "
            "eligible audit) and a clinically documented interpretation. Candidate B and C retain "
            "minority classes of 11 and 8 development participants, respectively, so they are weak "
            "primary prediction candidates despite their exploratory scores.",
            "",
            "The learnability finding is weak: PPG-only Logistic Regression is only slightly above "
            "the majority baseline for Candidate A and is essentially similar to context-only; the "
            "PPG-plus-context gain is not evidence that PPG alone recovers fasting State. The "
            "permutation control is chance-like and the continuous Ridge sanity check does not "
            "beat "
            "the dummy regressor.",
            "",
            "Recommended State-v1 for project-lead review: Candidate A as the defensible "
            "formulation to freeze and test, with a deliberately low claim ceiling and no "
            "automatic approval. A "
            "registered experiment should proceed only after explicit project-lead freeze.",
            "",
            "## Continuous sanity check",
            "",
            f"PPG-only Dummy/Ridge metrics: `{regression}`",
            "This does not redefine the primary State task.",
            "",
            "## Recommendation status",
            "",
            "These provisional verdicts are decision support only. Do not freeze State-v1 "
            "automatically; the project lead must approve the formulation and registered split.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--seed", type=int, default=20260817)
    args = parser.parse_args()
    root = args.repo_root.resolve()
    audit_path = root / "reports/audits/hbppg_participants.csv"
    reserve_path = root / "data/manifests/state_test_reserve-v0.json"
    if reserve_path.exists():
        reserve = load_state_test_reserve(reserve_path)
    else:
        audit = pd.read_csv(audit_path)
        reserve = create_state_test_reserve(audit, reserve_path, seed=args.seed)
    table = build_state_exploratory_table(
        root / "data/raw/hbppg/v6/Hb_PPG_Dataset",
        reserve_path,
    )
    results = run_state_exploratory_analysis(table, seed=args.seed)
    probe_dir = root / "reports/probes/state_exploratory-v0"
    probe_dir.mkdir(parents=True, exist_ok=True)
    table.to_csv(probe_dir / "development_features.csv", index=False)
    try:
        table.to_parquet(probe_dir / "development_features.parquet", index=False)
    except (ImportError, ValueError):
        pass
    (probe_dir / "metrics.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    (probe_dir / "reserve_snapshot.json").write_text(
        json.dumps(
            {
                "reserve_manifest": "data/manifests/state_test_reserve-v0.json",
                "development_count": len(reserve["development_ids"]),
                "reserved_count": len(reserve["reserved_test_ids"]),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_brief(probe_dir / "summary.md", results)
    print(f"Wrote State exploratory probe to {probe_dir}")
    print(
        f"Development participants: {len(table)}; "
        f"reserved participants: {len(reserve['reserved_test_ids'])}"
    )


if __name__ == "__main__":
    main()
