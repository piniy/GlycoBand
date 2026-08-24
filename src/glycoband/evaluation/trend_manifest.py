"""Manifest construction for the approved BIG IDEAs Trend split."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd

from glycoband.evaluation.trend_split import validate_trend_splits
from glycoband.labels.trend import TrendProtocol, validate_endpoint_frame


def build_manifest_payload(
    split_frame: pd.DataFrame,
    protocol: TrendProtocol,
    *,
    git_revision: str | None,
    git_dirty: bool | None,
    endpoint_artifact_sha256: str,
    source_manifest_sha256: str,
) -> dict[str, object]:
    """Create a JSON-serializable manifest from a validated split frame."""

    validate_endpoint_frame(split_frame, protocol)
    validate_trend_splits(split_frame, protocol)
    if not git_revision or git_dirty is not False:
        raise ValueError("Frozen Trend manifest requires a clean Git revision")
    for name, digest in (
        ("endpoint artifact", endpoint_artifact_sha256),
        ("source manifest", source_manifest_sha256),
    ):
        if len(digest) != 64 or any(
            character not in "0123456789abcdefABCDEF" for character in digest
        ):
            raise ValueError(f"{name} SHA-256 is invalid")
    required_provenance = {"protocol_version", "bvp_source_file", "cgm_source_file"}
    missing = required_provenance.difference(split_frame.columns)
    if missing:
        raise ValueError(f"Trend manifest is missing provenance columns: {sorted(missing)}")
    if not (split_frame["protocol_version"] == protocol.version).all():
        raise ValueError("Trend manifest protocol versions do not match the loaded contract")

    participants: list[dict[str, object]] = []
    for participant_id, group in split_frame.groupby("participant_id", sort=True):
        usable = group[group["split"] != "excluded_embargo"]
        participants.append(
            {
                "participant_id": str(participant_id),
                "bvp_source_file": str(group["bvp_source_file"].iloc[0]),
                "cgm_source_file": str(group["cgm_source_file"].iloc[0]),
                "endpoint_count": int(len(group)),
                "usable_endpoint_count": int(len(usable)),
                "split_counts": {
                    str(name): int(count)
                    for name, count in group["split"].value_counts().sort_index().items()
                },
                "first_timestamp": pd.to_datetime(group["timestamp"]).min().isoformat(),
                "last_timestamp": pd.to_datetime(group["timestamp"]).max().isoformat(),
                "train_boundary": pd.to_datetime(
                    group["participant_train_boundary"].iloc[0]
                ).isoformat(),
                "validation_boundary": pd.to_datetime(
                    group["participant_validation_boundary"].iloc[0]
                ).isoformat(),
            }
        )

    split_counts = {
        str(name): int(count)
        for name, count in split_frame["split"].value_counts().sort_index().items()
    }
    return {
        "manifest_version": "trend-split-v1",
        "protocol_version": protocol.version,
        "dataset": "BIG IDEAs v1.1.3",
        "participant_count": int(split_frame["participant_id"].nunique()),
        "endpoint_count": int(len(split_frame)),
        "usable_endpoint_count": int((split_frame["split"] != "excluded_embargo").sum()),
        "split_counts": split_counts,
        "final_test_accessed": False,
        "chronological_split_created": True,
        "registered_model_started": False,
        "git_revision": git_revision,
        "git_dirty": git_dirty,
        "endpoint_artifact": {
            "path": "data/interim/trend/trend-label-v1.parquet",
            "sha256": endpoint_artifact_sha256.lower(),
        },
        "source_manifest_sha256": source_manifest_sha256.lower(),
        "protocol": asdict(protocol),
        "participants": participants,
        "endpoint_identity": ["participant_id", "timestamp"],
        "raw_history_identity": ["participant_id", "history_start", "timestamp"],
    }
