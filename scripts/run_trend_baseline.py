"""Run frozen Trend registered baselines on train/validation data only."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import confusion_matrix  # type: ignore[import-untyped]

from glycoband.datasets.bigideas import load_config
from glycoband.evaluation.trend_baseline import (
    evaluate_trend_baselines,
    load_trend_baseline_config,
)
from glycoband.features.trend import (
    aggregate_bvp_history_features,
    extract_bvp_window_features,
)


def _load_development_endpoints(path: Path) -> pd.DataFrame:
    """Read only train/validation rows from the split artifact."""

    frame = pd.read_parquet(
        path,
        columns=[
            "participant_id",
            "timestamp",
            "history_start",
            "label",
            "split",
            "bvp_source_file",
            "protocol_version",
        ],
        filters=[("split", "in", ["train", "validation"])],
    )
    if "test" in set(frame["split"].astype(str)):
        raise RuntimeError("Development endpoint loader returned final-test rows")
    return frame


def _write_summary(path: Path, report: dict[str, object]) -> None:
    model_rows = report["models"]
    assert isinstance(model_rows, list)
    history_row = next(
        row for row in model_rows if isinstance(row, dict) and row["model"] == "logistic_history"
    )
    assert isinstance(history_row, dict)
    history_per_class = history_row["per_class"]
    assert isinstance(history_per_class, dict)
    falling = history_per_class["FALLING"]
    rising = history_per_class["RISING"]
    assert isinstance(falling, dict) and isinstance(rising, dict)
    bootstrap = report["paired_participant_bootstrap"]
    assert isinstance(bootstrap, dict)
    lines = [
        "# Trend baseline development v1",
        "",
        "Status: registered development; validation-only result; final test sealed.",
        "",
        "## Contract",
        "",
        f"- Dataset: {report['dataset']}",
        f"- Label protocol: {report['protocol_version']}",
        f"- Split manifest: {report['split_version']}",
        f"- Train rows: {report['train_rows']}",
        f"- Validation rows: {report['validation_rows']}",
        f"- Numeric BVP feature count: {report['feature_count']}",
        f"- Decision: {report['decision']}",
        "- Final-test access: false",
        "",
        "## Validation metrics",
        "",
        "| Model | Macro-F1 | Balanced accuracy |",
        "|---|---:|---:|",
    ]
    for row in model_rows:
        assert isinstance(row, dict)
        lines.append(
            f"| {row['model']} | {float(row['macro_f1']):.4f} | "
            f"{float(row['balanced_accuracy']):.4f} |"
        )
    lines.extend(
        [
            "",
            "## Finding",
            "",
            f"The predeclared decision is **{report['decision']}**. The aligned H30 "
            f"history model reached Macro-F1 {float(history_row['macro_f1']):.4f}; "
            "the current-window and shifted-control variants remained at the constant "
            "baseline in this validation run.",
            f"Directional recall was FALLING={float(falling['recall']):.4f} and "
            f"RISING={float(rising['recall']):.4f}.",
            "",
            f"Paired participant-bootstrap deltas: {bootstrap}",
            "",
            "## What this does not prove",
            "",
            "No final-test performance was accessed. This result does not establish "
            "general-population validity, direct glucose measurement, clinical utility, "
            "or physical-device validity.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_figures(
    report_dir: Path,
    report: dict[str, object],
    predictions: pd.DataFrame,
    participant_metrics: pd.DataFrame,
) -> None:
    figure_dir = report_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    model_rows = report["models"]
    assert isinstance(model_rows, list)
    names = [str(row["model"]) for row in model_rows if isinstance(row, dict)]
    macro_f1 = [
        float(row["macro_f1"])
        for row in model_rows
        if isinstance(row, dict)
    ]
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.bar(names, macro_f1, color="#5B4B8A")
    axis.set_ylabel("Validation Macro-F1")
    axis.set_ylim(max(0.0, min(macro_f1) - 0.01), min(1.0, max(macro_f1) + 0.01))
    axis.tick_params(axis="x", rotation=25)
    figure.tight_layout()
    figure.savefig(figure_dir / "model_macro_f1.png", dpi=200)
    plt.close(figure)

    pivot = participant_metrics.pivot(
        index="participant_id", columns="model", values="macro_f1"
    )
    figure, axis = plt.subplots(figsize=(11, 5))
    pivot.plot(kind="bar", ax=axis, width=0.8)
    axis.set_ylabel("Validation Macro-F1")
    axis.set_xlabel("Participant")
    axis.set_ylim(0, 1)
    axis.legend(loc="upper right", fontsize=8)
    figure.tight_layout()
    figure.savefig(figure_dir / "participant_macro_f1.png", dpi=200)
    plt.close(figure)

    logistic_models = [
        "logistic_history",
        "logistic_current_window",
        "logistic_shifted_control",
    ]
    figure, axes = plt.subplots(
        1, 3, figsize=(12, 4), squeeze=False, constrained_layout=True
    )
    for axis, model_name in zip(axes[0], logistic_models, strict=True):
        model_predictions = predictions[predictions["model"] == model_name]
        matrix = confusion_matrix(
            model_predictions["label"],
            model_predictions["prediction"],
            labels=["FALLING", "STABLE", "RISING"],
            normalize="true",
        )
        image = axis.imshow(matrix, vmin=0, vmax=1, cmap="Purples")
        axis.set_title(model_name.replace("_", " "))
        axis.set_xticks(range(3), ["FALL", "STABLE", "RISE"], rotation=30)
        axis.set_yticks(range(3), ["FALL", "STABLE", "RISE"])
        for row in range(3):
            for column in range(3):
                axis.text(column, row, f"{matrix[row, column]:.2f}", ha="center", va="center")
    figure.colorbar(image, ax=axes[0].tolist(), fraction=0.025, pad=0.04)
    figure.savefig(figure_dir / "validation_confusion_matrices.png", dpi=200)
    plt.close(figure)


def _write_metadata(
    root: Path,
    report_dir: Path,
    feature_path: Path,
    features: pd.DataFrame,
    report: dict[str, object],
    config_path: Path,
) -> None:
    (report_dir / "config.yaml").write_text(
        config_path.read_text(encoding="utf-8"), encoding="utf-8"
    )
    split_manifest_path = root / "data/manifests/trend_split-v1.json"
    source_manifest_path = root / "data/manifests/source_manifest.json"
    (report_dir / "split_manifest.json").write_text(
        split_manifest_path.read_text(encoding="utf-8"), encoding="utf-8"
    )
    feature_digest = _sha256(feature_path)
    source_digest = _sha256(source_manifest_path)
    dataset_manifest = {
        "dataset": report["dataset"],
        "source_manifest": {
            "path": "data/manifests/source_manifest.json",
            "sha256": source_digest,
        },
        "development_feature_artifact": {
            "path": "data/interim/trend/trend-baseline-features-v1.parquet",
            "sha256": feature_digest,
            "rows": int(len(features)),
            "columns": list(features.columns),
        },
        "regeneration_command": "uv run --frozen python scripts/run_trend_baseline.py",
        "final_test_accessed": False,
    }
    (report_dir / "dataset_manifest.json").write_text(
        json.dumps(dataset_manifest, indent=2) + "\n", encoding="utf-8"
    )
    git_revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()
    git_dirty = bool(
        subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip()
    )
    environment = {
        "git_revision": git_revision,
        "git_dirty": git_dirty,
        "python_version": sys.version,
        "platform": platform.platform(),
        "command": "uv run --frozen python scripts/run_trend_baseline.py",
        "config_sha256": _sha256(config_path),
        "split_manifest_sha256": _sha256(split_manifest_path),
        "final_test_accessed": False,
    }
    (report_dir / "environment.json").write_text(
        json.dumps(environment, indent=2) + "\n", encoding="utf-8"
    )
    (report_dir / "logs.txt").write_text(
        "Runner completed; full terminal progress intentionally not persisted.\n",
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--from-features",
        action="store_true",
        help="Reuse the existing development feature artifact and regenerate reports only.",
    )
    arguments = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    split_path = root / "data/interim/trend/trend-label-v1.parquet"
    config_path = root / "configs/trend/baseline-v1.yaml"
    config = load_trend_baseline_config(config_path)
    audit_config = load_config(root / "configs/audits/bigideas.yaml")
    endpoints = _load_development_endpoints(split_path)
    dataset_root = root / "data/raw/bigideas/v1.1.3"
    feature_path = root / "data/interim/trend/trend-baseline-features-v1.parquet"

    if arguments.from_features:
        features = pd.read_parquet(feature_path)
    else:
        feature_frames: list[pd.DataFrame] = []
        for participant_id, endpoint_group in endpoints.groupby("participant_id", sort=True):
            endpoint_group = endpoint_group.copy()
            endpoint_group["split_version"] = config["split"]["version"]
            source_file = str(endpoint_group["bvp_source_file"].iloc[0])
            max_endpoint = pd.to_datetime(endpoint_group["timestamp"]).max()
            print(
                f"[trend-baseline-v1] participant={participant_id} "
                f"stage=bvp_features stop_at={max_endpoint.isoformat()}",
                flush=True,
            )
            windows = extract_bvp_window_features(
                dataset_root / source_file,
                rate_hz=int(audit_config["bvp_rate_hz"]),
                window_seconds=int(config["feature"]["short_window_seconds"]),
                maximum_gap_seconds=float(audit_config["maximum_bvp_gap_seconds"]),
                stop_at=max_endpoint,
            )
            windows["participant_id"] = participant_id
            participant_features = aggregate_bvp_history_features(
                windows,
                endpoint_group,
                history_minutes=int(config["feature"]["history_minutes"]),
                window_seconds=int(config["feature"]["short_window_seconds"]),
                minimum_complete_windows=int(config["feature"]["minimum_complete_windows"]),
            )
            if len(participant_features) != len(endpoint_group):
                raise RuntimeError(
                    f"Participant {participant_id} lost development endpoints: "
                    f"{len(participant_features)} of {len(endpoint_group)}"
                )
            feature_frames.append(participant_features)
            print(
                f"[trend-baseline-v1] participant={participant_id} "
                f"windows={len(windows)} features={len(participant_features)}",
                flush=True,
            )
        features = pd.concat(feature_frames, ignore_index=True)
    if "test" in set(features["split"].astype(str)):
        raise RuntimeError("Feature artifact contains final-test rows")
    report, predictions, participant_metrics = evaluate_trend_baselines(features, config)

    feature_dir = root / "data/interim/trend"
    report_dir = root / "reports/experiments/trend-baseline-v1"
    feature_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    features.to_parquet(feature_path, index=False)
    predictions.to_parquet(report_dir / "predictions.parquet", index=False)
    participant_metrics.to_csv(report_dir / "per_participant.csv", index=False)
    (report_dir / "metrics.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    _write_summary(report_dir / "summary.md", report)
    _write_metadata(root, report_dir, feature_path, features, report, config_path)
    _write_figures(report_dir, report, predictions, participant_metrics)
    model_rows = report["models"]
    assert isinstance(model_rows, list)
    headline = next(
        row
        for row in model_rows
        if isinstance(row, dict) and row["model"] == "logistic_history"
    )
    assert isinstance(headline, dict)
    print(
        f"[trend-baseline-v1] logistic_history_macro_f1={float(headline['macro_f1']):.4f} "
        f"decision={report['decision']}",
        flush=True,
    )
    print(f"[trend-baseline-v1] feature_artifact={feature_dir}", flush=True)
    print(f"[trend-baseline-v1] report_artifact={report_dir}", flush=True)
    print("[trend-baseline-v1] final_test_accessed=false", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
