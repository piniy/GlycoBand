from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from glycoband.evaluation.trend_manifest import build_manifest_payload
from glycoband.labels.trend import load_trend_protocol


@pytest.fixture
def protocol():
    return load_trend_protocol(Path(__file__).parents[2] / "configs/trend/label-v1.yaml")


def _split_frame(protocol) -> pd.DataFrame:
    from glycoband.evaluation.trend_split import assign_trend_splits

    rows: list[dict[str, object]] = []
    for participant_id in ("001", "002"):
        for index in range(120):
            timestamp = pd.Timestamp("2020-01-01") + pd.Timedelta(minutes=5 * index)
            rows.append(
                {
                    "participant_id": participant_id,
                    "timestamp": timestamp,
                    "history_start": timestamp - pd.Timedelta(minutes=30),
                    "label": ("RISING", "STABLE", "FALLING")[index % 3],
                    "support_points": 7,
                    "slope_method": protocol.slope_method,
                    "bvp_source_file": f"{participant_id}/BVP_{participant_id}.csv",
                    "cgm_source_file": f"{participant_id}/Dexcom_{participant_id}.csv",
                }
            )
    frame = pd.DataFrame(rows)
    frame["protocol_version"] = protocol.version
    return assign_trend_splits(frame, protocol)


def test_manifest_payload_records_contract_and_sealed_test(protocol) -> None:
    payload = build_manifest_payload(
        _split_frame(protocol),
        protocol,
        git_revision="abc123",
        git_dirty=False,
        endpoint_artifact_sha256="a" * 64,
        source_manifest_sha256="b" * 64,
    )

    assert payload["manifest_version"] == "trend-split-v1"
    assert payload["protocol_version"] == "trend-label-v1"
    assert payload["participant_count"] == 2
    assert payload["final_test_accessed"] is False
    assert payload["registered_model_started"] is False
    assert payload["endpoint_identity"] == ["participant_id", "timestamp"]
    assert payload["endpoint_artifact"] == {
        "path": "data/interim/trend/trend-label-v1.parquet",
        "sha256": "a" * 64,
    }
    assert payload["source_manifest_sha256"] == "b" * 64


def test_manifest_payload_rejects_protocol_mismatch(protocol) -> None:
    frame = _split_frame(protocol)
    frame["protocol_version"] = "wrong-version"

    with pytest.raises(ValueError, match="protocol version"):
        build_manifest_payload(
            frame,
            protocol,
            git_revision=None,
            git_dirty=None,
            endpoint_artifact_sha256="a" * 64,
            source_manifest_sha256="b" * 64,
        )


def test_manifest_payload_requires_source_provenance(protocol) -> None:
    frame = _split_frame(protocol).drop(columns=["bvp_source_file"])

    with pytest.raises(ValueError, match="missing columns|provenance"):
        build_manifest_payload(
            frame,
            protocol,
            git_revision="abc123",
            git_dirty=False,
            endpoint_artifact_sha256="a" * 64,
            source_manifest_sha256="b" * 64,
        )


def test_manifest_payload_refuses_dirty_git_state(protocol) -> None:
    with pytest.raises(ValueError, match="clean Git revision"):
        build_manifest_payload(
            _split_frame(protocol),
            protocol,
            git_revision="abc123",
            git_dirty=True,
            endpoint_artifact_sha256="a" * 64,
            source_manifest_sha256="b" * 64,
        )


def test_manifest_payload_rejects_invalid_hash(protocol) -> None:
    with pytest.raises(ValueError, match="SHA-256 is invalid"):
        build_manifest_payload(
            _split_frame(protocol),
            protocol,
            git_revision="abc123",
            git_dirty=False,
            endpoint_artifact_sha256="not-a-hash",
            source_manifest_sha256="b" * 64,
        )
