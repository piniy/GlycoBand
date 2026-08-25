"""Run the leakage-safe Phase 0 Trend signal diagnostics."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import yaml

from glycoband.evaluation.trend_diagnostics import (
    class_distribution,
    feature_slope_correlations,
    flat_fraction_summary,
    phase0_gate,
    slope_distribution,
    slope_threshold_summary,
    validate_development_frame,
)
from glycoband.labels.trend import load_trend_protocol


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return payload


def _load_development_endpoints(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(
        path,
        columns=[
            "participant_id",
            "timestamp",
            "history_start",
            "split",
            "label",
            "slope_mg_dl_min",
            "bvp_source_file",
            "protocol_version",
        ],
        filters=[("split", "in", ["train", "validation"])],
    )
    validate_development_frame(frame, require_slope=True, name="development endpoints")
    return frame


def _load_development_features(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(path)
    validate_development_frame(frame, name="development features")
    return frame


def _prepare_output_directory(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"Diagnostic output already exists: {path}")
    path.mkdir(parents=True)


def _write_figures(
    output: Path,
    endpoints: pd.DataFrame,
    distribution: pd.DataFrame,
    quality: pd.DataFrame,
) -> None:
    figure_dir = output / "figures"
    figure_dir.mkdir()
    slopes = endpoints["slope_mg_dl_min"].to_numpy(dtype=float)
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.hist(slopes, bins=80, color="#5B4B8A", alpha=0.85)
    axis.axvline(-0.5, color="#C84C4C", linestyle="--", linewidth=1)
    axis.axvline(0.5, color="#C84C4C", linestyle="--", linewidth=1)
    axis.set_xlabel("CGM slope (mg/dL/min)")
    axis.set_ylabel("Development endpoints")
    axis.set_title("Continuous CGM slope before thresholded Trend labels")
    figure.tight_layout()
    figure.savefig(figure_dir / "slope_distribution.png", dpi=200)
    plt.close(figure)

    aggregate = (
        distribution.groupby(["split", "label"], observed=False)["count"]
        .sum()
        .unstack(fill_value=0)
        .reindex(columns=["FALLING", "STABLE", "RISING"], fill_value=0)
    )
    figure, axis = plt.subplots(figsize=(8, 5))
    aggregate.plot(kind="bar", stacked=True, color=["#4C78A8", "#BDBDBD", "#F58518"], ax=axis)
    axis.set_xlabel("Development split")
    axis.set_ylabel("Endpoints")
    axis.set_title("Trend class distribution")
    axis.legend(title="Label")
    figure.tight_layout()
    figure.savefig(figure_dir / "class_distribution.png", dpi=200)
    plt.close(figure)

    maximum = quality[quality["feature"] == "history_flat_fraction_max"]
    if not maximum.empty:
        plot_data = maximum.pivot(index="threshold", columns="split", values="fraction")
        figure, axis = plt.subplots(figsize=(8, 5))
        plot_data.plot(marker="o", ax=axis)
        axis.set_xlabel("Flat-fraction threshold")
        axis.set_ylabel("Fraction of endpoints at or above threshold")
        axis.set_ylim(0, 1)
        axis.set_title("Baseline flat-fraction quality proxy")
        figure.tight_layout()
        figure.savefig(figure_dir / "flat_fraction_quality.png", dpi=200)
        plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="GlycoBand repository root",
    )
    args = parser.parse_args()
    root = args.repo_root.resolve()
    config_path = root / "configs/probes/trend_signal_learnability-v1.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("Phase 0 probe config must be a mapping")
    endpoint_path = root / "data/interim/trend/trend-label-v1.parquet"
    feature_path = root / "data/interim/trend/trend-baseline-features-v1.parquet"
    split_manifest_path = root / "data/manifests/trend_split-v1.json"
    baseline_manifest_path = root / "reports/experiments/trend-baseline-v1/dataset_manifest.json"
    split_manifest = _load_json(split_manifest_path)
    baseline_manifest = _load_json(baseline_manifest_path)
    expected_endpoint_sha = split_manifest["endpoint_artifact"]["sha256"]
    expected_feature_sha = baseline_manifest["development_feature_artifact"]["sha256"]
    if _sha256(endpoint_path) != expected_endpoint_sha:
        raise ValueError("Endpoint artifact does not match frozen split manifest")
    if _sha256(feature_path) != expected_feature_sha:
        raise ValueError("Feature artifact does not match frozen baseline manifest")
    print("[trend-signal-diagnostics-v1] stage=load_development_only", flush=True)
    endpoints = _load_development_endpoints(endpoint_path)
    features = _load_development_features(feature_path)
    print(
        f"[trend-signal-diagnostics-v1] endpoints={len(endpoints)} features={len(features)} "
        f"participants={endpoints['participant_id'].nunique()}",
        flush=True,
    )
    distribution = class_distribution(endpoints)
    slopes = slope_distribution(endpoints)
    threshold = load_trend_protocol(root / "configs/trend/label-v1.yaml").threshold_mg_dl_min
    slope_regions = slope_threshold_summary(endpoints, threshold_mg_dl_min=threshold)
    methods = tuple(config["diagnostics"]["correlation_methods"])
    correlations = feature_slope_correlations(features, endpoints, methods=methods)
    quality = flat_fraction_summary(
        features,
        thresholds=tuple(config["diagnostics"]["flat_fraction_thresholds"]),
    )
    gate = phase0_gate(endpoints, distribution)
    output = root / "reports/probes/trend-signal-diagnostics-v1"
    _prepare_output_directory(output)
    distribution.to_csv(output / "class_distribution.csv", index=False)
    slopes.to_csv(output / "slope_distribution.csv", index=False)
    slope_regions.to_csv(output / "slope_threshold_summary.csv", index=False)
    correlations.to_csv(output / "feature_slope_correlations.csv", index=False)
    quality.to_csv(output / "quality_proxy_summary.csv", index=False)
    (output / "config.yaml").write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
    dataset_manifest = {
        "dataset": "BIG IDEAs v1.1.3",
        "endpoint_artifact": {
            "path": "data/interim/trend/trend-label-v1.parquet",
            "sha256": _sha256(endpoint_path),
            "development_rows": int(len(endpoints)),
        },
        "feature_artifact": {
            "path": "data/interim/trend/trend-baseline-features-v1.parquet",
            "sha256": _sha256(feature_path),
            "development_rows": int(len(features)),
        },
        "participant_count": int(endpoints["participant_id"].nunique()),
        "development_splits": sorted(endpoints["split"].astype(str).unique()),
        "final_test_accessed": False,
    }
    (output / "dataset_manifest.json").write_text(
        json.dumps(dataset_manifest, indent=2) + "\n", encoding="utf-8"
    )
    metrics = {
        "experiment": config["experiment"],
        "class_counts": {
            str(split): {
                str(label): int(count)
                for label, count in (
                    distribution[distribution["split"] == split]
                    .groupby("label", observed=False)["count"]
                    .sum()
                    .items()
                )
            }
            for split in ("train", "validation")
        },
        "slope_threshold_mg_dl_min": threshold,
        "phase0_gate": gate,
        "final_test_accessed": False,
    }
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    _write_figures(output, endpoints, distribution, quality)
    print(f"[trend-signal-diagnostics-v1] gate={gate['status']}", flush=True)
    print(f"[trend-signal-diagnostics-v1] report_artifact={output}", flush=True)
    print("[trend-signal-diagnostics-v1] final_test_accessed=false", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
