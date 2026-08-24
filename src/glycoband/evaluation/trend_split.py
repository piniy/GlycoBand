"""Leakage-safe within-person chronological Trend splitting."""

from __future__ import annotations

import math
from typing import Final

import pandas as pd

from glycoband.labels.trend import TrendProtocol, validate_endpoint_frame

SPLIT_ORDER: Final = {"train": 0, "validation": 1, "test": 2}
USABLE_SPLITS: Final = frozenset(SPLIT_ORDER)
EXCLUDED_SPLIT = "excluded_embargo"


def _participant_boundaries(
    group: pd.DataFrame, protocol: TrendProtocol
) -> tuple[pd.Timestamp, pd.Timestamp]:
    count = len(group)
    first_index = min(max(math.floor(count * protocol.train_fraction), 1), count - 2)
    second_index = min(
        max(
            math.floor(count * (protocol.train_fraction + protocol.validation_fraction)),
            first_index + 1,
        ),
        count - 1,
    )
    timestamps = group["timestamp"].reset_index(drop=True)
    return timestamps.iloc[first_index], timestamps.iloc[second_index]


def _assign_group(group: pd.DataFrame, protocol: TrendProtocol) -> pd.DataFrame:
    ordered = group.sort_values("timestamp", kind="mergesort").copy()
    boundary_one, boundary_two = _participant_boundaries(ordered, protocol)
    count = len(ordered)
    first_index = min(max(math.floor(count * protocol.train_fraction), 1), count - 2)
    second_index = min(
        max(
            math.floor(count * (protocol.train_fraction + protocol.validation_fraction)),
            first_index + 1,
        ),
        count - 1,
    )
    positions = pd.Series(range(count), index=ordered.index)
    raw_split = pd.Series(EXCLUDED_SPLIT, index=ordered.index, dtype="object")
    raw_split.loc[positions < first_index] = "train"
    raw_split.loc[(positions >= first_index) & (positions < second_index)] = "validation"
    raw_split.loc[positions >= second_index] = "test"

    embargo = pd.Timedelta(minutes=protocol.embargo_minutes)
    timestamps = pd.to_datetime(ordered["timestamp"])
    train_boundary = (raw_split == "train") & (timestamps >= boundary_one - embargo)
    validation_boundary = (raw_split == "validation") & (
        (timestamps < boundary_one + embargo) | (timestamps >= boundary_two - embargo)
    )
    test_boundary = (raw_split == "test") & (timestamps < boundary_two + embargo)
    raw_split.loc[train_boundary | validation_boundary | test_boundary] = EXCLUDED_SPLIT
    ordered["split"] = raw_split
    ordered["participant_train_boundary"] = boundary_one
    ordered["participant_validation_boundary"] = boundary_two
    ordered["embargo_minutes"] = protocol.embargo_minutes
    return ordered


def assign_trend_splits(endpoints: pd.DataFrame, protocol: TrendProtocol) -> pd.DataFrame:
    """Assign deterministic chronological splits while excluding boundary embargo rows."""

    validate_endpoint_frame(endpoints, protocol)
    frames = [_assign_group(group, protocol) for _, group in endpoints.groupby("participant_id")]
    result = pd.concat(frames, ignore_index=True)
    return result.sort_values(["participant_id", "timestamp"], kind="mergesort").reset_index(
        drop=True
    )


def _validate_pairwise_history_gap(
    earlier: pd.DataFrame, later: pd.DataFrame, protocol: TrendProtocol
) -> None:
    earlier_end = pd.to_datetime(earlier["timestamp"]).max()
    later_start = pd.to_datetime(later["history_start"]).min()
    required_gap = pd.Timedelta(minutes=protocol.embargo_minutes)
    if later_start - earlier_end < required_gap:
        raise ValueError("Trend raw history crosses the configured embargo")


def validate_trend_splits(split_frame: pd.DataFrame, protocol: TrendProtocol) -> None:
    """Validate chronology, endpoint identity, and raw-history separation."""

    validate_endpoint_frame(split_frame, protocol)
    if "split" not in split_frame.columns:
        raise ValueError("Trend split frame is missing the split column")
    unexpected = set(split_frame["split"].dropna().unique()) - USABLE_SPLITS - {EXCLUDED_SPLIT}
    if unexpected:
        raise ValueError(f"Trend split frame contains unknown split values: {sorted(unexpected)}")

    for participant_id, group in split_frame.groupby("participant_id"):
        usable = group[group["split"] != EXCLUDED_SPLIT].copy()
        if set(usable["split"]) != USABLE_SPLITS:
            raise ValueError(f"Participant {participant_id} does not have all usable Trend splits")
        ordered = usable.sort_values("timestamp", kind="mergesort")
        split_values = ordered["split"].tolist()
        if any(
            SPLIT_ORDER[left] > SPLIT_ORDER[right]
            for left, right in zip(split_values, split_values[1:], strict=False)
        ):
            raise ValueError(f"Participant {participant_id} has non-chronological Trend splits")
        for earlier_name, later_name in (("train", "validation"), ("validation", "test")):
            earlier = usable[usable["split"] == earlier_name]
            later = usable[usable["split"] == later_name]
            _validate_pairwise_history_gap(earlier, later, protocol)
