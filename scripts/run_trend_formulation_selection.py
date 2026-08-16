"""Select a small, development-only BIG IDEAs Trend formulation set."""

# Markdown evidence sentences are intentionally kept readable in the generated report.
# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from glycoband.evaluation.trend_formulation import (
    CLASS_COLUMNS,
    candidate_metrics,
    participant_compositions,
)


def _git_revision(root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _write_balance_figure(metrics: pd.DataFrame, output: Path) -> None:
    labels = [str(value).replace("_", "\n") for value in metrics["candidate_id"]]
    figure, axis = plt.subplots(figsize=(11, 6.5))
    bottom = [0.0] * len(metrics)
    colors = {"falling": "#377eb8", "stable": "#bdbdbd", "rising": "#e41a1c"}
    for column in CLASS_COLUMNS:
        values = metrics[f"{column}_fraction"].to_numpy()
        axis.bar(labels, values, bottom=bottom, label=column.title(), color=colors[column])
        bottom = [left + right for left, right in zip(bottom, values, strict=True)]
    axis.set_ylim(0, 1)
    axis.set_ylabel("Fraction of eligible endpoints")
    axis.set_title("Selected Trend formulations: global class composition")
    axis.legend(ncols=3, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    axis.tick_params(axis="x", labelsize=8)
    figure.tight_layout()
    figure.savefig(output, dpi=180)
    plt.close(figure)


def _write_participant_heatmaps(compositions: pd.DataFrame, output: Path) -> None:
    candidates = [str(value) for value in compositions["candidate_id"].drop_duplicates()]
    participants = sorted(compositions["participant_id"].unique())
    figure, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    for axis, column in zip(axes, CLASS_COLUMNS, strict=True):
        matrix = compositions.pivot(
            index="participant_id", columns="candidate_id", values=f"{column}_fraction"
        ).reindex(index=participants, columns=candidates)
        image = axis.imshow(matrix.to_numpy(), aspect="auto", vmin=0, vmax=1, cmap="viridis")
        axis.set_ylabel(column.title())
        axis.set_yticks(range(len(participants)), [str(value) for value in participants])
        figure.colorbar(image, ax=axis, fraction=0.02, pad=0.01)
    axes[-1].set_xticks(
        range(len(candidates)), [value.replace("_", "\n") for value in candidates], fontsize=8
    )
    axes[-1].set_xlabel("Selected formulation")
    figure.suptitle("Participant-level class fractions (audit counts)")
    figure.tight_layout()
    figure.savefig(output, dpi=180)
    plt.close(figure)


def _write_stability_figure(metrics: pd.DataFrame, output: Path) -> None:
    figure, axis = plt.subplots(figsize=(10, 5.5))
    labels = [str(value).replace("_", "\n") for value in metrics["candidate_id"]]
    values = metrics["composition_tv_vs_primary_mean"].to_numpy()
    bars = axis.bar(labels, values, color="#4daf4a")
    axis.set_ylabel("Mean total variation vs primary")
    axis.set_title("Participant composition shift relative to H30 / tau0.5 / median3 / OLS")
    axis.tick_params(axis="x", labelsize=8)
    axis.bar_label(bars, fmt="%.3f", padding=3, fontsize=8)
    axis.set_ylim(0, max(0.05, float(values.max()) * 1.25))
    figure.tight_layout()
    figure.savefig(output, dpi=180)
    plt.close(figure)


def _write_summary(output: Path, metrics: pd.DataFrame, source: str) -> None:
    primary = metrics.iloc[0]
    lines = [
        "# Trend formulation selection — BIG IDEAs development-only probe",
        "",
        "Status: **development-only; Trend formulation and chronological split remain PENDING**",
        "",
        "## Question",
        "",
        (
            "Which smallest set of causal Recent Trend label formulations is scientifically "
            "defensible for a later development comparison?"
        ),
        "",
        "## Evidence",
        "",
        (
            f"- Source: `{source}` (existing BIG IDEAs v1.1.3 audit; 16 participants; "
            "no raw data reread)."
        ),
        (
            "- The audit grid contains 81 protocols: 15/30/60-minute history, thresholds "
            "0.5/1.0/1.5 mg/dL/min, three smoothing choices, and three slope estimators."
        ),
        (
            "- Every protocol has nonzero FALLING, STABLE, and RISING counts for all 16 "
            "participants. This is support, not a guarantee of adequate per-person class precision."
        ),
        (
            "- Eligibility is causal and already requires continuous BVP coverage, CGM support, "
            "and no future CGM values; no chronological split was created."
        ),
        "",
        "## Shortlist",
        "",
        (
            "| Candidate | History | Threshold | Smoothing | Slope | Eligible | Falling | "
            "Stable | Rising | Minority fraction |"
        ),
        "|---|---:|---:|---|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in metrics.iterrows():
        lines.append(
            
                f"| `{row['candidate_id']}` | {int(row['history_minutes'])} min | "
                f"{row['threshold_mg_dl_min']:.1f} | {row['smoothing']} | {row['slope_method']} | "
                f"{int(row['eligible_endpoints'])} | {int(row['falling'])} | "
                f"{int(row['stable'])} | {int(row['rising'])} | "
                f"{row['minority_fraction']:.3f} |"
            
        )
    lines.extend(
        [
            "",
            "## Finding",
            "",
            f"The primary candidate is H30 / tau0.5 / median3 / OLS: it retains {int(primary['eligible_endpoints'])} eligible endpoints, has {primary['minority_fraction']:.1%} in the smaller directional class, and preserves all three classes in every participant. H15 and H60 are the minimal temporal sensitivities; tau1.0 is a conservative but still supported margin; Theil–Sen is the only estimator robustness check retained.",
            "",
            "The 1.5 mg/dL/min threshold is excluded from the shortlist because it leaves only about 1% of endpoints in the smaller directional class. Endpoint-delta and unsmoothed variants are not carried forward: they add no distinct temporal question, while the audit counts show either lower directional support or only small composition changes relative to the primary. Median3 plus OLS remains the most auditable physiological rate formulation; Theil–Sen tests whether isolated CGM excursions change that conclusion.",
            "",
            "Label stability here is a participant-level composition proxy from audit counts, not exact endpoint-by-endpoint agreement. The next development comparison should therefore use only these five formulations and quantify shared-endpoint agreement before any model or split is registered.",
            "",
            "## Decision / claim ceiling",
            "",
            "**Recommend the five-formulation development-only comparison above, with H30 / tau0.5 / median3 / OLS as the working primary.** Do not freeze the Trend protocol, create a final chronological split, register a model, or open a reserve from this descriptive selection probe.",
            "",
            "## Figures",
            "",
            "- `figures/class_balance_shortlist.png` — global class composition.",
            "- `figures/participant_class_fractions.png` — participant-level support/composition.",
            "- `figures/composition_shift_vs_primary.png` — stability proxy relative to the primary.",
            "",
            "## Evidence refs",
            "",
            "- `reports/audits/bigideas_audit.md`",
            "- `reports/audits/bigideas_audit.json`",
            "- `reports/audits/bigideas_trend_candidates.csv`",
            "- `configs/audits/bigideas.yaml`",
            "",
        ]
    )
    lines = [line.replace("\u00e2\u20ac\u201d", "-") for line in lines]
    lines[0] = "# Trend formulation selection - BIG IDEAs development-only probe"
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.repo_root.resolve()
    output_dir = root / "reports/experiments/trend_formulation-v0"
    figure_dir = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    source = root / "reports/audits/bigideas_trend_candidates.csv"
    print("[trend-formulation-v0] identity=BIG IDEAs Trend formulation selection")
    print(
        "[trend-formulation-v0] dataset=BIG IDEAs v1.1.3; development=16 participants; reserve=not created/opened"
    )
    print("[trend-formulation-v0] stage=load existing candidate-protocol audit")
    candidates = pd.read_csv(source)
    print(
        f"[trend-formulation-v0] loaded={len(candidates)} participant-protocol rows; protocols=81"
    )
    print("[trend-formulation-v0] stage=compute class support, composition, and stability proxy")
    metrics = candidate_metrics(candidates)
    compositions = participant_compositions(candidates)
    print("[trend-formulation-v0] selected=5 formulations; final chronological split=NO")
    print("[trend-formulation-v0] stage=write diagnostic figures")
    _write_balance_figure(metrics, figure_dir / "class_balance_shortlist.png")
    _write_participant_heatmaps(compositions, figure_dir / "participant_class_fractions.png")
    _write_stability_figure(metrics, figure_dir / "composition_shift_vs_primary.png")
    print("[trend-formulation-v0] stage=write compact evidence artifacts")
    metrics.to_csv(output_dir / "candidate_comparison.csv", index=False)
    compositions.to_csv(output_dir / "participant_compositions.csv", index=False)
    metrics_payload = {
        "dataset": "bigideas-v1.1.3",
        "source_audit": str(source.relative_to(root)),
        "development_participants": 16,
        "reserved_participants": 0,
        "reserve_status": "not created or opened",
        "chronological_split_created": False,
        "registered_model_started": False,
        "candidate_protocols_in_source": 81,
        "shortlist_size": len(metrics),
        "shortlist": metrics.to_dict(orient="records"),
        "label_stability_measure": "participant class-composition total variation proxy; no endpoint-level agreement",
    }
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics_payload, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "run_metadata.json").write_text(
        json.dumps(
            {
                "experiment_id": "trend_formulation-v0",
                "dataset": "bigideas-v1.1.3",
                "source_audit": str(source.relative_to(root)),
                "git_revision": _git_revision(root),
                "development_participants": 16,
                "reserved_participants": 0,
                "reserve_accessed": False,
                "chronological_split_created": False,
                "registered_model_started": False,
                "raw_data_reread": False,
                "purpose": "select a minimal development-only Trend formulation set",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_summary(output_dir / "summary.md", metrics, str(source.relative_to(root)))
    print("[trend-formulation-v0] result=shortlist written")
    print(f"[trend-formulation-v0] artifacts={output_dir}")


if __name__ == "__main__":
    main()
