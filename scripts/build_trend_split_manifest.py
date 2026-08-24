"""Build the approved BIG IDEAs Trend endpoint and chronological split artifacts."""

# ruff: noqa: E501

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd

from glycoband.datasets.bigideas import (
    audit_bvp_csv,
    generate_recent_trend_labels,
    load_cgm,
    load_config,
    participant_source_paths,
)
from glycoband.evaluation.trend_manifest import build_manifest_payload
from glycoband.evaluation.trend_split import assign_trend_splits, validate_trend_splits
from glycoband.labels.trend import (
    TrendProtocol,
    load_trend_protocol,
)

# The runner emits compact progress and Markdown-safe evidence strings.


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


def _endpoint_labels(
    root: Path, protocol: TrendProtocol, audit_config: dict[str, Any]
) -> pd.DataFrame:
    dataset_root = root / "data/raw/bigideas/v1.1.3"
    expected_participants = int(audit_config["expected_participants"])
    frames: list[pd.DataFrame] = []
    for number in range(1, expected_participants + 1):
        participant_id = f"{number:03d}"
        bvp_source, cgm_source = participant_source_paths(participant_id)
        print(f"[trend-split-v1] participant={participant_id} stage=label_generation", flush=True)
        bvp = audit_bvp_csv(
            dataset_root / bvp_source,
            rate_hz=int(audit_config["bvp_rate_hz"]),
            window_seconds=int(audit_config["short_window_seconds"]),
            maximum_gap_seconds=float(audit_config["maximum_bvp_gap_seconds"]),
        )
        cgm = load_cgm(
            dataset_root / cgm_source,
            float(audit_config["maximum_cgm_gap_minutes"]),
        ).frame
        labels = generate_recent_trend_labels(
            cgm,
            bvp.spans,
            history_minutes=protocol.history_minutes,
            threshold_mg_dl_min=protocol.threshold_mg_dl_min,
            smoothing=protocol.smoothing,
            minimum_support_fraction=protocol.minimum_support_fraction,
            maximum_gap_minutes=protocol.maximum_cgm_gap_minutes,
            slope_method=protocol.slope_method,
        )
        if labels.empty:
            raise RuntimeError(f"Participant {participant_id} produced no Trend endpoints")
        if labels["timestamp"].gt(cgm["timestamp"].max()).any():
            raise RuntimeError(f"Participant {participant_id} produced a future-CGM endpoint")
        labels.insert(0, "participant_id", participant_id)
        labels.insert(1, "protocol_version", protocol.version)
        labels.insert(2, "bvp_source_file", bvp_source)
        labels.insert(3, "cgm_source_file", cgm_source)
        labels["available_cgm_end"] = cgm["timestamp"].max()
        frames.append(labels)
        print(
            f"[trend-split-v1] participant={participant_id} "
            f"endpoints={len(labels)}",
            flush=True,
        )
    result = pd.concat(frames, ignore_index=True)
    if result["participant_id"].nunique() != expected_participants:
        raise RuntimeError("Trend manifest runner did not process every expected participant")
    return result


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
    protocol = load_trend_protocol(root / "configs/trend/label-v1.yaml")
    audit_config = load_config(root / "configs/audits/bigideas.yaml")
    endpoints = _endpoint_labels(root, protocol, audit_config)
    split_frame = assign_trend_splits(endpoints, protocol)
    validate_trend_splits(split_frame, protocol)

    interim_dir = root / "data/interim/trend"
    manifest_dir = root / "data/manifests"
    interim_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    endpoint_path = interim_dir / "trend-label-v1.parquet"
    manifest_path = manifest_dir / "trend_split-v1.json"
    split_frame.to_parquet(endpoint_path, index=False)
    manifest = build_manifest_payload(
        split_frame,
        protocol,
        git_revision=_git_revision(root),
        git_dirty=_git_dirty(root),
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"[trend-split-v1] endpoint_artifact={endpoint_path}", flush=True)
    print(f"[trend-split-v1] split_manifest={manifest_path}", flush=True)
    print("[trend-split-v1] final_test_accessed=false", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
