from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from glycoband.evaluation.trend_split import assign_trend_splits, validate_trend_splits
from glycoband.labels.trend import load_trend_protocol


@pytest.fixture
def protocol():
    return load_trend_protocol(Path(__file__).parents[2] / "configs/trend/label-v1.yaml")


@pytest.fixture
def endpoint_frame() -> pd.DataFrame:
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
                    "bvp_source_file": f"{participant_id}/BVP_{participant_id}.csv",
                    "cgm_source_file": f"{participant_id}/Dexcom_{participant_id}.csv",
                }
            )
    return pd.DataFrame(rows)


def test_assign_trend_splits_is_deterministic_and_orders_time(
    endpoint_frame: pd.DataFrame, protocol
) -> None:
    first = assign_trend_splits(endpoint_frame, protocol)
    second = assign_trend_splits(endpoint_frame, protocol)

    pd.testing.assert_frame_equal(first, second)
    assert set(first["split"]) == {"train", "validation", "test", "excluded_embargo"}

    for participant_id, group in first.groupby("participant_id"):
        usable = group[group["split"] != "excluded_embargo"].sort_values("timestamp")
        assert set(usable["split"]) == {"train", "validation", "test"}, participant_id
        assert list(usable["split"].drop_duplicates()) == ["train", "validation", "test"]


def test_validate_trend_splits_proves_raw_history_separation(
    endpoint_frame: pd.DataFrame, protocol
) -> None:
    split = assign_trend_splits(endpoint_frame, protocol)

    validate_trend_splits(split, protocol)


def test_validate_trend_splits_rejects_history_crossing_embargo(
    endpoint_frame: pd.DataFrame, protocol
) -> None:
    split = assign_trend_splits(endpoint_frame, protocol)
    train = split[split["split"] == "train"].sort_values("timestamp").iloc[-1]
    validation_index = split.index[split["split"] == "validation"][0]
    split.loc[validation_index, "history_start"] = train["timestamp"]

    with pytest.raises(ValueError, match="raw history|embargo"):
        validate_trend_splits(split, protocol)


def test_validate_trend_splits_rejects_duplicate_endpoint_identity(
    endpoint_frame: pd.DataFrame, protocol
) -> None:
    split = assign_trend_splits(endpoint_frame, protocol)
    duplicated = pd.concat([split, split.iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="duplicate"):
        validate_trend_splits(duplicated, protocol)


def test_validate_trend_splits_rejects_non_chronological_split(
    endpoint_frame: pd.DataFrame, protocol
) -> None:
    split = assign_trend_splits(endpoint_frame, protocol)
    first_train_index = split.index[split["split"] == "train"][0]
    split.loc[first_train_index, "split"] = "test"

    with pytest.raises(ValueError, match="chronological|split"):
        validate_trend_splits(split, protocol)
