from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from glycoband.features.trend import (
    SHORT_WINDOW_FEATURES,
    aggregate_bvp_history_features,
    extract_bvp_window_features,
)


def _write_bvp(path: Path, *, rows: int = 40) -> None:
    timestamps = pd.date_range("2020-01-01", periods=rows, freq="250ms")
    values = np.linspace(0.0, 1.0, rows)
    pd.DataFrame({"datetime": timestamps, "bvp": values}).to_csv(path, index=False)


def _valid_windows() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    start = pd.Timestamp("2020-01-01")
    for index in range(60):
        window_start = start + pd.Timedelta(seconds=30 * index)
        rows.append(
            {
                "participant_id": "001",
                "window_start": window_start,
                "window_end": window_start + pd.Timedelta(seconds=29),
                **{feature: float(index) for feature in SHORT_WINDOW_FEATURES},
            }
        )
    return pd.DataFrame(rows)


def _valid_endpoints() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "participant_id": "001",
                "timestamp": pd.Timestamp("2020-01-01 00:30:00"),
                "history_start": pd.Timestamp("2020-01-01 00:00:00"),
                "split": "train",
                "label": "RISING",
                "bvp_source_file": "001/BVP_001.csv",
                "protocol_version": "trend-label-v1",
                "split_version": "trend-split-v1",
            }
        ]
    )


def test_extract_bvp_window_features_streams_contiguous_windows(tmp_path: Path) -> None:
    path = tmp_path / "BVP.csv"
    _write_bvp(path)

    windows = extract_bvp_window_features(
        path,
        rate_hz=4,
        window_seconds=2,
        maximum_gap_seconds=0.251,
        chunksize=7,
    )

    assert len(windows) == 5
    assert list(windows.columns) == ["window_start", "window_end", *SHORT_WINDOW_FEATURES]
    assert windows["window_start"].is_monotonic_increasing
    assert (windows["std"] > 0).all()


def test_extract_bvp_window_features_stops_before_future_data(tmp_path: Path) -> None:
    path = tmp_path / "BVP.csv"
    _write_bvp(path)

    windows = extract_bvp_window_features(
        path,
        rate_hz=4,
        window_seconds=2,
        maximum_gap_seconds=0.251,
        stop_at=pd.Timestamp("2020-01-01 00:00:05"),
    )

    assert windows["window_end"].max() <= pd.Timestamp("2020-01-01 00:00:05")


def test_window_slope_is_reported_per_minute(tmp_path: Path) -> None:
    path = tmp_path / "BVP.csv"
    timestamps = pd.date_range("2020-01-01", periods=8, freq="250ms")
    seconds = np.arange(8, dtype=float) / 4.0
    pd.DataFrame({"datetime": timestamps, "bvp": seconds}).to_csv(path, index=False)

    windows = extract_bvp_window_features(
        path,
        rate_hz=4,
        window_seconds=2,
        maximum_gap_seconds=0.251,
    )

    assert windows.loc[0, "slope_per_min"] == pytest.approx(60.0)


def test_history_aggregation_requires_participant_identity() -> None:
    windows = _valid_windows().drop(columns="participant_id")

    with pytest.raises(ValueError, match="participant_id"):
        aggregate_bvp_history_features(
            windows,
            _valid_endpoints(),
            history_minutes=30,
            window_seconds=30,
            minimum_complete_windows=59,
        )


def test_history_aggregation_rejects_final_test_rows() -> None:
    endpoints = _valid_endpoints()
    endpoints.loc[0, "split"] = "test"

    with pytest.raises(ValueError, match="final-test|development splits"):
        aggregate_bvp_history_features(
            _valid_windows(),
            endpoints,
            history_minutes=30,
            window_seconds=30,
            minimum_complete_windows=59,
        )


def test_history_aggregation_preserves_provenance() -> None:
    features = aggregate_bvp_history_features(
        _valid_windows(),
        _valid_endpoints(),
        history_minutes=30,
        window_seconds=30,
        minimum_complete_windows=59,
    )

    assert {
        "participant_id",
        "bvp_source_file",
        "protocol_version",
        "split_version",
        "feature_version",
    }.issubset(features.columns)
    assert set(features["feature_version"]) == {"trend-feature-v1"}


def test_aggregate_bvp_history_features_excludes_future_windows() -> None:
    features = aggregate_bvp_history_features(
        _valid_windows(),
        _valid_endpoints(),
        history_minutes=30,
        window_seconds=30,
        minimum_complete_windows=59,
    )

    assert len(features) == 1
    assert features.loc[0, "history_window_count"] == 60
    assert features.loc[0, "history_mean_last"] == pytest.approx(59.0)
