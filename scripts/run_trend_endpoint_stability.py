"""Run a development-only exact endpoint stability probe for Trend formulations."""

# Markdown evidence sentences are intentionally kept readable in the generated report.
# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from glycoband.datasets.bigideas import (
    audit_bvp_csv,
    generate_recent_trend_labels,
    load_cgm,
    load_config,
    participant_source_paths,
)
from glycoband.evaluation.trend_endpoint_stability import LABEL_ORDER, compare_to_primary
from glycoband.evaluation.trend_formulation import SHORTLIST


def _git_revision(root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _git_dirty(root: Path) -> bool | None:
    try:
        return bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=root,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        )
    except (OSError, subprocess.CalledProcessError):
        return None


def _endpoint_labels(root: Path, audit_config: dict[str, Any]) -> pd.DataFrame:
    """Rebuild only shortlisted causal labels while streaming each BVP source once."""

    dataset_root = root / "data/raw/bigideas/v1.1.3"
    frames: list[pd.DataFrame] = []
    expected_participants = int(audit_config["expected_participants"])
    for number in range(1, expected_participants + 1):
        participant_id = f"{number:03d}"
        bvp_source, cgm_source = participant_source_paths(participant_id)
        print(f"[trend-endpoint-stability-v1] participant={participant_id} stage=stream_bvp")
        bvp = audit_bvp_csv(
            dataset_root / bvp_source,
            rate_hz=int(audit_config["bvp_rate_hz"]),
            window_seconds=int(audit_config["short_window_seconds"]),
            maximum_gap_seconds=float(audit_config["maximum_bvp_gap_seconds"]),
        )
        cgm = load_cgm(dataset_root / cgm_source, float(audit_config["maximum_cgm_gap_minutes"])).frame
        for protocol in SHORTLIST:
            labels = generate_recent_trend_labels(
                cgm,
                bvp.spans,
                history_minutes=int(protocol["history_minutes"]),
                threshold_mg_dl_min=float(protocol["threshold_mg_dl_min"]),
                smoothing=str(protocol["smoothing"]),
                minimum_support_fraction=float(audit_config["minimum_cgm_support_fraction"]),
                maximum_gap_minutes=float(audit_config["maximum_cgm_gap_minutes"]),
                slope_method=str(protocol["slope_method"]),
            )
            if not labels.empty and labels["timestamp"].gt(cgm["timestamp"].max()).any():
                raise RuntimeError("Generated a Trend endpoint after available CGM")
            labels.insert(0, "participant_id", participant_id)
            labels.insert(1, "candidate_id", str(protocol["candidate_id"]))
            labels.insert(2, "bvp_source_file", bvp_source)
            labels.insert(3, "cgm_source_file", cgm_source)
            labels.insert(4, "history_minutes", int(protocol["history_minutes"]))
            labels.insert(5, "threshold_mg_dl_min", float(protocol["threshold_mg_dl_min"]))
            labels.insert(6, "smoothing", str(protocol["smoothing"]))
            frames.append(labels)
        print(
            "[trend-endpoint-stability-v1] "
            f"participant={participant_id} stage=labels_complete candidates={len(SHORTLIST)}"
        )
    labels = pd.concat(frames, ignore_index=True)
    if labels["participant_id"].nunique() != expected_participants:
        raise RuntimeError("Exact endpoint probe did not process every expected participant")
    return labels


def _write_agreement_figure(per_participant: pd.DataFrame, output: Path) -> None:
    candidates = list(per_participant["candidate_id"].drop_duplicates())
    participants = sorted(per_participant["participant_id"].dropna().unique())
    matrix = per_participant.pivot(
        index="participant_id", columns="candidate_id", values="exact_label_agreement"
    ).reindex(index=participants, columns=candidates)
    figure, axis = plt.subplots(figsize=(11, 6.5))
    image = axis.imshow(matrix.to_numpy(dtype=float), aspect="auto", vmin=0, vmax=1, cmap="viridis")
    axis.set_xticks(range(len(candidates)), [value.replace("_", "\n") for value in candidates], fontsize=8)
    axis.set_yticks(range(len(participants)), participants)
    axis.set_xlabel("Candidate formulation vs working primary")
    axis.set_ylabel("Participant")
    axis.set_title("Exact shared-endpoint label agreement")
    figure.colorbar(image, ax=axis, label="Agreement fraction")
    figure.tight_layout()
    figure.savefig(output, dpi=180)
    plt.close(figure)


def _write_transition_figure(transitions: pd.DataFrame, output: Path) -> None:
    candidates = list(transitions["candidate_id"].drop_duplicates())
    figure, axes = plt.subplots(
        1, len(candidates), figsize=(3.4 * len(candidates), 3.8), squeeze=False
    )
    for index, (axis, candidate_id) in enumerate(zip(axes[0], candidates, strict=True)):
        table = transitions.loc[transitions["candidate_id"] == candidate_id].pivot(
            index="primary_label", columns="candidate_label", values="count"
        ).reindex(index=LABEL_ORDER, columns=LABEL_ORDER, fill_value=0)
        total = int(table.to_numpy().sum())
        values = table.to_numpy(dtype=float) / total if total else np.zeros((3, 3))
        axis.imshow(values, vmin=0, vmax=1, cmap="magma")
        for row, _primary_label in enumerate(LABEL_ORDER):
            for column, _candidate_label in enumerate(LABEL_ORDER):
                axis.text(
                    column,
                    row,
                    f"{values[row, column]:.2f}",
                    ha="center",
                    va="center",
                    color="white" if values[row, column] < 0.45 else "black",
                    fontsize=8,
                )
        axis.set_xticks(range(3), LABEL_ORDER, rotation=45, ha="right", fontsize=8)
        axis.set_yticks(range(3), LABEL_ORDER if index == 0 else [], fontsize=8)
        axis.set_title(candidate_id.replace("_", "\n"), fontsize=8)
        axis.set_xlabel("Candidate label")
        if axis is axes[0][0]:
            axis.set_ylabel("Primary label")
    figure.suptitle("Exact label transitions versus working primary", y=1.02)
    figure.tight_layout()
    figure.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(figure)


def _write_summary(output: Path, pooled: pd.DataFrame, config: dict[str, Any]) -> None:
    lines = [
        "# Trend exact endpoint stability - BIG IDEAs development-only probe",
        "",
        "Status: **exploratory development-only; Trend label and chronological split remain PENDING**",
        "",
        "## Question",
        "",
        "Across the five shortlisted causal Recent Trend formulations, how often are the exact same participant-timestamp endpoints eligible and assigned the same direction label?",
        "",
        "## Method",
        "",
        "- Re-streamed immutable BIG IDEAs v1.1.3 BVP files once per participant to reconstruct continuous-coverage eligibility.",
        "- Regenerated only the five shortlisted labels from CGM history ending at each endpoint; no future CGM observation enters a label.",
        "- Compared each formulation with the working primary H30 / tau0.5 / median3 / OLS using `(participant_id, timestamp)` exact keys.",
        "- No chronological split, final reserve, model, calibration, OOD policy, or final-test data was created or accessed.",
        "",
        "## Pooled exact-endpoint comparison",
        "",
        "| Candidate | Shared / primary | Shared / candidate | Jaccard | Exact agreement | Cohen kappa |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in pooled.iterrows():
        lines.append(
            f"| `{row['candidate_id']}` | {row['primary_shared_retention']:.3f} | "
            f"{row['candidate_shared_retention']:.3f} | {row['endpoint_jaccard']:.3f} | "
            f"{row['exact_label_agreement']:.3f} | {row['cohen_kappa']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "Exact agreement is reported only on shared endpoints; retention and Jaccard expose endpoint eligibility changes. The slope-margin quantiles in `pooled_pairwise.csv` separate primary-margin distributions for agreements and disagreements, but do not establish clinical correctness or choose a protocol automatically.",
            "",
            "## What this does not prove",
            "",
            "This probe does not establish BVP learnability, create a leakage-safe chronological split, validate a device, or freeze a Trend label. A project-lead Gate D review remains required before versioning the selected label protocol and split manifest.",
            "",
            "## Evidence artifacts",
            "",
            "- `endpoint_labels.parquet` - exact endpoint and label provenance for the five candidates.",
            "- `pooled_pairwise.csv` and `per_participant_pairwise.csv` - endpoint retention, agreement, kappa, and slope-margin diagnostics.",
            "- `label_transitions.csv` - all nine primary-to-candidate label transitions.",
            "- `figures/exact_agreement_by_participant.png` and `figures/label_transition_matrices.png` - visual diagnostics.",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.repo_root.resolve()
    probe_config = load_config(root / "configs/probes/trend_endpoint_stability-v1.yaml")
    audit_config = load_config(root / str(probe_config["source_audit_config"]))
    output_dir = root / "reports/experiments" / str(probe_config["experiment_id"])
    figure_dir = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    print("[trend-endpoint-stability-v1] identity=exact endpoint stability")
    print("[trend-endpoint-stability-v1] dataset=BIG IDEAs v1.1.3 development=16 reserve=not created")
    print("[trend-endpoint-stability-v1] stage=regenerate causal labels from immutable raw data")
    endpoint_labels = _endpoint_labels(root, audit_config)
    primary_id = str(probe_config["primary_candidate_id"])
    print("[trend-endpoint-stability-v1] stage=compare exact participant-timestamp keys")
    pooled, per_participant, transitions = compare_to_primary(endpoint_labels, primary_id)
    print("[trend-endpoint-stability-v1] stage=write compact artifacts and figures")
    endpoint_labels.to_parquet(output_dir / "endpoint_labels.parquet", index=False)
    pooled.to_csv(output_dir / "pooled_pairwise.csv", index=False)
    per_participant.to_csv(output_dir / "per_participant_pairwise.csv", index=False)
    transitions.to_csv(output_dir / "label_transitions.csv", index=False)
    _write_agreement_figure(per_participant, figure_dir / "exact_agreement_by_participant.png")
    _write_transition_figure(transitions, figure_dir / "label_transition_matrices.png")
    metrics = {
        "experiment_id": probe_config["experiment_id"],
        "evidence_level": probe_config["evidence_level"],
        "dataset": probe_config["dataset"],
        "primary_candidate_id": primary_id,
        "participants": int(endpoint_labels["participant_id"].nunique()),
        "candidates": list(endpoint_labels["candidate_id"].drop_duplicates()),
        "final_test_accessed": False,
        "chronological_split_created": False,
        "registered_model_started": False,
        "pooled_pairwise": pooled.to_dict(orient="records"),
    }
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    metadata = {
        "experiment_id": probe_config["experiment_id"],
        "dataset": probe_config["dataset"],
        "config": "configs/probes/trend_endpoint_stability-v1.yaml",
        "source_audit_config": probe_config["source_audit_config"],
        "git_revision": _git_revision(root),
        "git_dirty": _git_dirty(root),
        "python": sys.version,
        "platform": platform.platform(),
        "raw_data_reread": True,
        "final_test_accessed": False,
        "chronological_split_created": False,
        "registered_model_started": False,
    }
    (output_dir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    _write_summary(output_dir / "summary.md", pooled, probe_config)
    print("[trend-endpoint-stability-v1] final_test_accessed=false split_created=false")
    print(f"[trend-endpoint-stability-v1] result=artifacts written to {output_dir}")


if __name__ == "__main__":
    main()
