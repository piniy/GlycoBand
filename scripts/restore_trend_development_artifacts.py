"""Restore frozen Trend development artifacts without opening the final test."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from glycoband.datasets.bigideas import load_config
from glycoband.evaluation.trend_split import assign_trend_splits, validate_trend_splits
from glycoband.features.trend import (
    aggregate_bvp_history_features,
    extract_bvp_window_features,
)
from glycoband.labels.trend import load_trend_protocol


def sha256_file(path: Path) -> str:
    """Return the lower-case SHA-256 digest of a file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def restore_if_missing(
    path: Path,
    expected_sha256: str,
    builder: Callable[[Path], None],
) -> Path:
    """Restore an artifact atomically when it is absent or has the wrong digest."""

    expected = expected_sha256.lower()
    if len(expected) != 64 or any(character not in "0123456789abcdef" for character in expected):
        raise ValueError(f"Invalid expected SHA-256: {expected_sha256!r}")
    if path.exists() and sha256_file(path) == expected:
        return path

    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.unlink(missing_ok=True)
    try:
        builder(temporary)
        observed = sha256_file(temporary)
        if observed != expected:
            raise ValueError(
                "Restored artifact SHA-256 mismatch: "
                f"expected={expected} observed={observed}"
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return path


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return payload


def _expected_endpoint_digest(root: Path) -> str:
    manifest = _load_json(root / "data/manifests/trend_split-v1.json")
    if manifest.get("final_test_accessed") is not False:
        raise RuntimeError("Frozen Trend manifest does not attest final-test protection")
    artifact = manifest.get("endpoint_artifact")
    if not isinstance(artifact, dict) or artifact.get("path") != (
        "data/interim/trend/trend-label-v1.parquet"
    ):
        raise ValueError("Frozen Trend manifest has an unexpected endpoint artifact path")
    digest = artifact.get("sha256")
    if not isinstance(digest, str):
        raise ValueError("Frozen Trend manifest has no endpoint artifact SHA-256")
    return digest


def _expected_feature_digest(root: Path) -> str:
    manifest = _load_json(
        root / "reports/experiments/trend-baseline-v1/dataset_manifest.json"
    )
    if manifest.get("final_test_accessed") is not False:
        raise RuntimeError("Frozen Trend baseline manifest does not attest final-test protection")
    artifact = manifest.get("development_feature_artifact")
    if not isinstance(artifact, dict) or artifact.get("path") != (
        "data/interim/trend/trend-baseline-features-v1.parquet"
    ):
        raise ValueError("Frozen Trend baseline manifest has an unexpected feature artifact path")
    digest = artifact.get("sha256")
    if not isinstance(digest, str):
        raise ValueError("Frozen Trend baseline manifest has no feature artifact SHA-256")
    return digest


def _build_endpoint_frame(root: Path) -> pd.DataFrame:
    """Build the frozen endpoint/split frame using the registered implementation."""

    from scripts.build_trend_split_manifest import _endpoint_labels

    protocol = load_trend_protocol(root / "configs/trend/label-v1.yaml")
    audit_config = load_config(root / "configs/audits/bigideas.yaml")
    endpoints = _endpoint_labels(root, protocol, audit_config)
    split_frame = assign_trend_splits(endpoints, protocol)
    validate_trend_splits(split_frame, protocol)
    return split_frame


def _restore_endpoint_artifact(root: Path) -> Path:
    path = root / "data/interim/trend/trend-label-v1.parquet"
    expected = _expected_endpoint_digest(root)

    def build(temporary: Path) -> None:
        frame = _build_endpoint_frame(root)
        frame.to_parquet(temporary, index=False)

    restored = restore_if_missing(path, expected, build)
    observed = sha256_file(restored)
    if observed != expected.lower():
        raise AssertionError("Endpoint artifact digest changed after atomic restore")
    return restored


def _load_development_endpoints(path: Path) -> pd.DataFrame:
    """Read only train/validation rows from the frozen endpoint artifact."""

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


def _build_feature_frame(root: Path, endpoint_path: Path) -> pd.DataFrame:
    endpoints = _load_development_endpoints(endpoint_path)
    config = load_config(root / "configs/audits/bigideas.yaml")
    feature_config = yaml.safe_load(
        (root / "configs/trend/baseline-v1.yaml").read_text(encoding="utf-8")
    )
    dataset_root = root / "data/raw/bigideas/v1.1.3"
    feature_frames: list[pd.DataFrame] = []
    for participant_id, endpoint_group in endpoints.groupby("participant_id", sort=True):
        endpoint_group = endpoint_group.copy()
        endpoint_group["split_version"] = feature_config["split"]["version"]
        source_file = str(endpoint_group["bvp_source_file"].iloc[0])
        max_endpoint = pd.to_datetime(endpoint_group["timestamp"]).max()
        print(
            f"[trend-restore-v1] participant={participant_id} "
            f"stage=bvp_features stop_at={max_endpoint.isoformat()}",
            flush=True,
        )
        windows = extract_bvp_window_features(
            dataset_root / source_file,
            rate_hz=int(config["bvp_rate_hz"]),
            window_seconds=int(feature_config["feature"]["short_window_seconds"]),
            maximum_gap_seconds=float(config["maximum_bvp_gap_seconds"]),
            stop_at=max_endpoint,
        )
        windows["participant_id"] = participant_id
        participant_features = aggregate_bvp_history_features(
            windows,
            endpoint_group,
            history_minutes=int(feature_config["feature"]["history_minutes"]),
            window_seconds=int(feature_config["feature"]["short_window_seconds"]),
            minimum_complete_windows=int(feature_config["feature"]["minimum_complete_windows"]),
        )
        if len(participant_features) != len(endpoint_group):
            raise RuntimeError(
                f"Participant {participant_id} lost development endpoints: "
                f"{len(participant_features)} of {len(endpoint_group)}"
            )
        feature_frames.append(participant_features)
        print(
            f"[trend-restore-v1] participant={participant_id} "
            f"windows={len(windows)} features={len(participant_features)}",
            flush=True,
        )
    if not feature_frames:
        raise RuntimeError("No development feature rows were produced")
    features = pd.concat(feature_frames, ignore_index=True)
    if "test" in set(features["split"].astype(str)):
        raise RuntimeError("Feature artifact contains final-test rows")
    return features


def _restore_feature_artifact(root: Path, endpoint_path: Path) -> Path:
    path = root / "data/interim/trend/trend-baseline-features-v1.parquet"
    expected = _expected_feature_digest(root)

    def build(temporary: Path) -> None:
        frame = _build_feature_frame(root, endpoint_path)
        frame.to_parquet(temporary, index=False)

    restored = restore_if_missing(path, expected, build)
    if sha256_file(restored) != expected.lower():
        raise AssertionError("Feature artifact digest changed after atomic restore")
    return restored


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="GlycoBand repository root",
    )
    parser.add_argument(
        "--endpoint-only",
        action="store_true",
        help="Restore only the frozen endpoint artifact",
    )
    parser.add_argument(
        "--feature-only",
        action="store_true",
        help="Restore only the development feature artifact",
    )
    args = parser.parse_args(argv)
    if args.endpoint_only and args.feature_only:
        parser.error("--endpoint-only and --feature-only are mutually exclusive")
    root = args.repo_root.resolve()
    endpoint_path = root / "data/interim/trend/trend-label-v1.parquet"
    if not args.feature_only:
        endpoint_path = _restore_endpoint_artifact(root)
        print(f"[trend-restore-v1] endpoint_artifact={endpoint_path}", flush=True)
    elif not endpoint_path.exists():
        endpoint_path = _restore_endpoint_artifact(root)
    if not args.endpoint_only:
        feature_path = _restore_feature_artifact(root, endpoint_path)
        print(f"[trend-restore-v1] feature_artifact={feature_path}", flush=True)
    print("[trend-restore-v1] final_test_accessed=false", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
