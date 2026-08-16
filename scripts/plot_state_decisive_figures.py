"""Render journal-ready figures from the completed Hb-PPG exploratory artifacts.

The script is deliberately read-only with respect to experiment inputs: it consumes
the recorded development-only metrics and writes figures beside the experiment.
It never loads the sealed reserve or raw Hb-PPG signals.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

plt.switch_backend("Agg")


PREDICTOR_LABELS = {
    "ppg_only": "PPG only",
    "context_only": "Context only",
    "ppg_plus_context": "PPG + context",
}
PREDICTOR_COLORS = {
    "ppg_only": "#0072B2",
    "context_only": "#E69F00",
    "ppg_plus_context": "#009E73",
}
METRICS = {
    "macro_f1": "Macro-F1",
    "balanced_accuracy": "Balanced accuracy",
    "macro_pr_auc": "Macro PR-AUC",
}


def _save(figure: plt.Figure, output: Path) -> None:
    """Save the journal-resolution PNG artifact."""
    figure.savefig(output.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(figure)


def _style(axis: plt.Axes) -> None:
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis="y", color="#D9D9D9", linewidth=0.7, zorder=0)
    axis.set_axisbelow(True)


def _load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _cohort_figure(experiment_dir: Path, output: Path) -> None:
    metadata = _load_json(experiment_dir / "run_metadata.json")
    reserve = _load_json(Path("data/manifests/state_test_reserve-v0.json"))
    support = reserve["source_audit"]["candidate_label_support"]
    eligible = int(reserve["eligible_participant_count"])
    development = int(metadata["development_participants"])
    reserved = int(metadata["reserved_participants"])
    excluded = 252 - eligible

    figure, axes = plt.subplots(1, 2, figsize=(11.2, 4.6), gridspec_kw={"width_ratios": [1.2, 1]})
    flow_axis, label_axis = axes

    stages = [
        ("252\nHb-PPG v6\nparticipants", "#4D4D4D"),
        (f"{eligible}\nnumeric glucose\nreference", "#56B4E9"),
        (f"{development}\nexploratory\ndevelopment", "#0072B2"),
        (f"{reserved}\nsealed outer\nreserve", "#999999"),
    ]
    x_positions = [0.01, 0.27, 0.53, 0.79]
    for index, ((label, color), x_position) in enumerate(zip(stages, x_positions, strict=True)):
        flow_axis.add_patch(
            FancyBboxPatch(
                (x_position, 0.35),
                0.19,
                0.32,
                boxstyle="round,pad=0.01,rounding_size=0.02",
                facecolor=color,
                edgecolor="white",
                transform=flow_axis.transAxes,
            )
        )
        flow_axis.text(
            x_position + 0.095,
            0.51,
            label,
            ha="center",
            va="center",
            color="white",
            fontsize=9,
            fontweight="bold",
            transform=flow_axis.transAxes,
        )
        if index < len(stages) - 1:
            flow_axis.annotate(
                "",
                xy=(x_position + 0.255, 0.51),
                xytext=(x_position + 0.20, 0.51),
                xycoords=flow_axis.transAxes,
                arrowprops={"arrowstyle": "->", "color": "#4D4D4D", "lw": 1.4},
            )
    flow_axis.text(
        0.365,
        0.23,
        f"{excluded} excluded: missing glucose reference",
        ha="center",
        va="center",
        fontsize=8.5,
        color="#4D4D4D",
        transform=flow_axis.transAxes,
    )
    flow_axis.text(
        0.885,
        0.76,
        "Reserve not loaded for\nfeatures, fitting, or scoring",
        ha="center",
        va="center",
        fontsize=8,
        color="#4D4D4D",
        transform=flow_axis.transAxes,
    )
    flow_axis.set_yticks([])
    flow_axis.set_xticks([])
    for spine in flow_axis.spines.values():
        spine.set_visible(False)
    flow_axis.set_title(
        "A  Participant flow and protected development set",
        loc="left",
        fontweight="bold",
    )

    labels = ["Normal range\n< 5.6 mmol/L", "Elevated fasting range\n≥ 5.6 mmol/L"]
    values = [int(support["NORMAL_RANGE"]), int(support["ELEVATED_FASTING_RANGE"])]
    bars = label_axis.bar(labels, values, color=["#56B4E9", "#D55E00"], width=0.62, zorder=3)
    for bar, value in zip(bars, values, strict=True):
        label_axis.text(
            bar.get_x() + bar.get_width() / 2,
            value + 4,
            str(value),
            ha="center",
            va="bottom",
            fontweight="bold",
        )
    label_axis.set_ylim(0, 200)
    label_axis.set_ylabel("Participants in full audited cohort")
    label_axis.set_title("B  Frozen Candidate A label support", loc="left", fontweight="bold")
    _style(label_axis)
    figure.suptitle(
        "Hb-PPG v6 exploratory State experiment: cohort and label support",
        y=1.03,
        fontweight="bold",
    )
    figure.tight_layout()
    _save(figure, output)


def _metric_distribution_figure(folds: pd.DataFrame, output: Path) -> None:
    order = list(PREDICTOR_LABELS)
    figure, axes = plt.subplots(1, 3, figsize=(12.6, 4.2), sharey=True)
    rng = np.random.default_rng(20260817)
    for axis, (column, label) in zip(axes, METRICS.items(), strict=True):
        data = [folds.loc[folds["predictor_set"] == name, column].to_numpy() for name in order]
        box = axis.boxplot(data, patch_artist=True, widths=0.58, showfliers=False)
        for patch, name in zip(box["boxes"], order, strict=True):
            patch.set_facecolor(PREDICTOR_COLORS[name])
            patch.set_alpha(0.35)
            patch.set_edgecolor(PREDICTOR_COLORS[name])
        for component in ("whiskers", "caps", "medians"):
            for artist in box[component]:
                artist.set_color("#4D4D4D")
        for position, values, name in zip(range(1, len(order) + 1), data, order, strict=True):
            jitter = rng.uniform(-0.10, 0.10, len(values))
            axis.scatter(
                np.full(len(values), position) + jitter,
                values,
                s=13,
                color=PREDICTOR_COLORS[name],
                alpha=0.42,
                linewidths=0,
                zorder=3,
            )
        axis.set_xticks(
            range(1, len(order) + 1),
            [PREDICTOR_LABELS[name] for name in order],
            rotation=20,
            ha="right",
        )
        axis.set_title(label, fontweight="bold")
        axis.set_ylim(0.25, 0.9)
        _style(axis)
    axes[0].set_ylabel("Repeated-CV fold score")
    figure.suptitle(
        "Repeated participant-safe CV performance (20 repeats × 5 folds; "
        "development participants only)",
        y=1.04,
        fontweight="bold",
    )
    figure.tight_layout()
    _save(figure, output)


def _paired_delta_figure(repeated: dict[str, object], output: Path) -> None:
    paired = repeated["paired_deltas"]["context_to_ppg_plus_context"]
    deltas = pd.DataFrame(paired["folds"])
    summary = paired["summary"]
    columns = list(METRICS)
    figure, axes = plt.subplots(1, 3, figsize=(12.6, 4.2), sharey=False)
    rng = np.random.default_rng(20260818)
    for axis, column in zip(axes, columns, strict=True):
        delta_column = f"{column}_delta"
        values = deltas[delta_column].to_numpy()
        jitter = rng.uniform(-0.11, 0.11, len(values))
        axis.axhline(0, color="#4D4D4D", linewidth=1.0, zorder=1)
        axis.scatter(jitter, values, color="#0072B2", alpha=0.58, s=20, linewidths=0, zorder=3)
        axis.errorbar(
            0,
            float(summary[delta_column]["mean"]),
            yerr=float(summary[delta_column]["std"]),
            fmt="D",
            color="#D55E00",
            markersize=6,
            capsize=4,
            zorder=4,
            label="Mean ± SD",
        )
        axis.set_xlim(-0.22, 0.22)
        axis.set_xticks([])
        axis.set_title(METRICS[column], fontweight="bold")
        axis.set_ylabel("PPG + context minus context only")
        axis.text(
            0.03,
            0.96,
            f"mean = {summary[delta_column]['mean']:+.3f}\n"
            f"positive folds = {paired['positive_fold_fraction'][delta_column]:.0%}",
            transform=axis.transAxes,
            ha="left",
            va="top",
            fontsize=9,
        )
        _style(axis)
    axes[-1].legend(frameon=False, loc="lower right")
    figure.suptitle("Paired fold-level change after adding PPG features", y=1.04, fontweight="bold")
    figure.tight_layout()
    _save(figure, output)


def _permutation_figure(experiment_dir: Path, repeated: dict[str, object], output: Path) -> None:
    permutation = pd.read_csv(experiment_dir / "permutation_metrics.csv")
    observed = float(
        repeated["paired_deltas"]["context_to_ppg_plus_context"]["summary"]["macro_f1_delta"][
            "mean"
        ]
    )
    null = permutation["macro_f1_delta"].to_numpy()
    upper_tail = (1 + np.count_nonzero(null >= observed)) / (len(null) + 1)
    figure, axis = plt.subplots(figsize=(8.7, 4.9))
    axis.hist(null, bins=24, color="#999999", edgecolor="white", zorder=2)
    axis.axvline(0, color="#4D4D4D", linewidth=1.0, zorder=3)
    axis.axvline(observed, color="#D55E00", linewidth=2.2, zorder=4, label="Observed mean Δ")
    axis.text(
        observed + 0.004,
        axis.get_ylim()[1] * 0.94,
        f"Observed Δ = {observed:+.3f}\nUpper-tail proportion = {upper_tail:.3f}",
        ha="left",
        va="top",
        color="#A13B00",
        fontsize=10,
    )
    axis.set_xlabel("Macro-F1 change: PPG + context minus context only")
    axis.set_ylabel("Participant-level label permutations")
    axis.set_title("Permutation null for incremental PPG Macro-F1", loc="left", fontweight="bold")
    axis.text(
        0.01,
        -0.20,
        "500 participant-level label permutations; development-only control. The upper-tail "
        "proportion is exploratory, not a confirmatory p-value.",
        transform=axis.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        color="#4D4D4D",
    )
    _style(axis)
    axis.legend(frameon=False, loc="upper left")
    figure.tight_layout()
    _save(figure, output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--experiment-dir",
        type=Path,
        default=Path("reports/probes/state_exploratory-v1"),
        help="Completed State exploratory artifact directory.",
    )
    args = parser.parse_args()
    experiment_dir = args.experiment_dir.resolve()
    figures_dir = experiment_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    repeated = _load_json(experiment_dir / "repeated_metrics.json")
    folds = pd.read_csv(experiment_dir / "repeated_fold_metrics.csv")

    _cohort_figure(experiment_dir, figures_dir / "fig01_cohort_and_label_support")
    _metric_distribution_figure(folds, figures_dir / "fig02_repeated_cv_metric_distributions")
    _paired_delta_figure(repeated, figures_dir / "fig03_paired_incremental_ppg_effect")
    _permutation_figure(
        experiment_dir,
        repeated,
        figures_dir / "fig04_permutation_null_incremental_ppg",
    )
    print(f"Wrote four Hb-PPG exploratory figures to {figures_dir}")


if __name__ == "__main__":
    main()
