from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from glycoband.labels.trend import (
    TREND_CLASSES,
    load_trend_protocol,
    validate_endpoint_frame,
)


def _protocol_path() -> Path:
    return Path(__file__).parents[2] / "configs/trend/label-v1.yaml"


def _endpoints() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "participant_id": ["001", "001", "002"],
            "protocol_version": ["trend-label-v1"] * 3,
            "timestamp": pd.to_datetime(
                ["2020-01-01 00:30", "2020-01-01 00:35", "2020-01-01 00:30"]
            ),
            "history_start": pd.to_datetime(
                ["2020-01-01 00:00", "2020-01-01 00:05", "2020-01-01 00:00"]
            ),
            "label": ["RISING", "STABLE", "FALLING"],
            "support_points": [7, 7, 7],
            "slope_method": ["ols"] * 3,
            "bvp_source_file": ["001/BVP_001.csv"] * 2 + ["002/BVP_002.csv"],
            "cgm_source_file": ["001/Dexcom_001.csv"] * 2 + ["002/Dexcom_002.csv"],
        }
    )


def test_load_trend_protocol_reads_approved_values() -> None:
    protocol = load_trend_protocol(_protocol_path())

    assert protocol.version == "trend-label-v1"
    assert protocol.dataset_version == "1.1.3"
    assert protocol.history_minutes == 30
    assert protocol.threshold_mg_dl_min == 0.5
    assert protocol.smoothing == "median3"
    assert protocol.slope_method == "ols"
    assert protocol.minimum_support_fraction == 0.8
    assert protocol.classes == TREND_CLASSES
    assert protocol.embargo_minutes == 30


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("source", "future_cgm", "causal CGM"),
        ("history_minutes", 15, "history"),
        ("threshold_mg_dl_min", 1.0, "threshold"),
        ("minimum_cgm_support_fraction", 1.2, "support"),
    ],
)
def test_load_trend_protocol_rejects_unapproved_values(
    tmp_path: Path, field: str, value: object, message: str
) -> None:
    text = _protocol_path().read_text(encoding="utf-8")
    if isinstance(value, str):
        text = text.replace("cgm_history_ending_at_t", value)
    else:
        text = text.replace(
            f"{field}: {field_value(field)}",
            f"{field}: {value}",
        )
    path = tmp_path / "label.yaml"
    path.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        load_trend_protocol(path)


def field_value(field: str) -> str:
    return {
        "history_minutes": "30",
        "threshold_mg_dl_min": "0.5",
        "minimum_cgm_support_fraction": "0.80",
    }[field]


def test_validate_endpoint_frame_accepts_causal_provenance() -> None:
    protocol = load_trend_protocol(_protocol_path())

    validate_endpoint_frame(_endpoints(), protocol)


def test_validate_endpoint_frame_rejects_duplicate_endpoint_identity() -> None:
    protocol = load_trend_protocol(_protocol_path())
    frame = pd.concat([_endpoints(), _endpoints().iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="duplicate"):
        validate_endpoint_frame(frame, protocol)


def test_validate_endpoint_frame_rejects_future_or_invalid_rows() -> None:
    protocol = load_trend_protocol(_protocol_path())
    frame = _endpoints().copy()
    frame.loc[0, "history_start"] = frame.loc[0, "timestamp"]

    with pytest.raises(ValueError, match="history_start"):
        validate_endpoint_frame(frame, protocol)

    frame = _endpoints().copy()
    frame.loc[0, "label"] = "UNKNOWN"
    with pytest.raises(ValueError, match="invalid Trend label"):
        validate_endpoint_frame(frame, protocol)


def test_validate_endpoint_frame_rejects_wrong_history_duration() -> None:
    protocol = load_trend_protocol(_protocol_path())
    frame = _endpoints().copy()
    frame.loc[0, "history_start"] = frame.loc[0, "timestamp"] - pd.Timedelta(minutes=15)

    with pytest.raises(ValueError, match="30-minute history"):
        validate_endpoint_frame(frame, protocol)


def test_validate_endpoint_frame_rejects_insufficient_cgm_support() -> None:
    protocol = load_trend_protocol(_protocol_path())
    frame = _endpoints().copy()
    frame.loc[0, "support_points"] = 1

    with pytest.raises(ValueError, match="CGM support"):
        validate_endpoint_frame(frame, protocol)


def test_validate_endpoint_frame_rejects_protocol_provenance_mismatch() -> None:
    protocol = load_trend_protocol(_protocol_path())
    frame = _endpoints().copy()
    frame.loc[0, "protocol_version"] = "wrong-version"

    with pytest.raises(ValueError, match="protocol version"):
        validate_endpoint_frame(frame, protocol)
