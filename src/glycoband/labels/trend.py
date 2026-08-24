"""Approved BIG IDEAs Recent Trend protocol and endpoint validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from numbers import Real
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

TREND_CLASSES = ("FALLING", "STABLE", "RISING")
REQUIRED_ENDPOINT_COLUMNS = frozenset(
    {
        "participant_id",
        "timestamp",
        "history_start",
        "label",
        "support_points",
        "bvp_source_file",
        "cgm_source_file",
    }
)


@dataclass(frozen=True)
class TrendProtocol:
    """Frozen Trend label and split contract loaded from YAML."""

    version: str
    dataset_name: str
    dataset_version: str
    classes: tuple[str, str, str]
    source: str
    history_minutes: int
    smoothing: str
    slope_method: str
    threshold_mg_dl_min: float
    minimum_support_fraction: float
    maximum_cgm_gap_minutes: float
    requires_continuous_bvp_history: bool
    split_type: str
    train_fraction: float
    validation_fraction: float
    test_fraction: float
    embargo_minutes: int


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"Trend protocol field {name!r} must be a mapping")
    return value


def _string(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Trend protocol field {key!r} must be a non-empty string")
    return value


def _integer(mapping: Mapping[str, Any], key: str) -> int:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Trend protocol field {key!r} must be an integer")
    return value


def _number(mapping: Mapping[str, Any], key: str) -> float:
    value = mapping.get(key)
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"Trend protocol field {key!r} must be numeric")
    return float(value)


def _boolean(mapping: Mapping[str, Any], key: str) -> bool:
    value = mapping.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"Trend protocol field {key!r} must be boolean")
    return value


def load_trend_protocol(path: Path) -> TrendProtocol:
    """Load and validate the approved Trend protocol from YAML."""

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    root = _mapping(payload, "root")
    dataset = _mapping(root.get("dataset"), "dataset")
    label = _mapping(root.get("label"), "label")
    split = _mapping(root.get("split"), "split")
    classes_value = label.get("classes")
    if not isinstance(classes_value, list) or not all(
        isinstance(item, str) for item in classes_value
    ):
        raise ValueError("Trend protocol field 'classes' must be a list of strings")

    protocol = TrendProtocol(
        version=_string(root, "version"),
        dataset_name=_string(dataset, "name"),
        dataset_version=_string(dataset, "version"),
        classes=tuple(classes_value),
        source=_string(label, "source"),
        history_minutes=_integer(label, "history_minutes"),
        smoothing=_string(label, "smoothing"),
        slope_method=_string(label, "slope_method"),
        threshold_mg_dl_min=_number(label, "threshold_mg_dl_min"),
        minimum_support_fraction=_number(label, "minimum_cgm_support_fraction"),
        maximum_cgm_gap_minutes=_number(label, "maximum_cgm_gap_minutes"),
        requires_continuous_bvp_history=_boolean(label, "requires_continuous_bvp_history"),
        split_type=_string(split, "type"),
        train_fraction=_number(split, "train_fraction"),
        validation_fraction=_number(split, "validation_fraction"),
        test_fraction=_number(split, "test_fraction"),
        embargo_minutes=_integer(split, "embargo_minutes"),
    )
    validate_trend_protocol(protocol)
    return protocol


def validate_trend_protocol(protocol: TrendProtocol) -> None:
    """Reject protocol values that violate the approved Trend contract."""

    if protocol.version != "trend-label-v1":
        raise ValueError("Unsupported Trend protocol version")
    if (protocol.dataset_name, protocol.dataset_version) != ("big_ideas", "1.1.3"):
        raise ValueError("Trend protocol must target BIG IDEAs v1.1.3")
    if protocol.classes != TREND_CLASSES:
        raise ValueError(f"Trend classes must be exactly {TREND_CLASSES}")
    if protocol.source != "cgm_history_ending_at_t":
        raise ValueError("Trend labels must use causal CGM history ending at the endpoint")
    if protocol.history_minutes != 30:
        raise ValueError("Trend protocol history must be 30 minutes")
    if protocol.smoothing != "median3":
        raise ValueError("Trend protocol smoothing must be median3")
    if protocol.slope_method != "ols":
        raise ValueError("Trend protocol slope method must be OLS")
    if protocol.threshold_mg_dl_min != 0.5:
        raise ValueError("Trend protocol threshold must be 0.5 mg/dL/min")
    if not 0 < protocol.minimum_support_fraction <= 1:
        raise ValueError("Trend CGM support fraction must be in (0, 1]")
    if protocol.maximum_cgm_gap_minutes <= 0:
        raise ValueError("Trend maximum CGM gap must be positive")
    if not protocol.requires_continuous_bvp_history:
        raise ValueError("Trend protocol requires continuous BVP history")
    if protocol.split_type != "within_person_chronological":
        raise ValueError("Trend split must be within-person chronological")
    fractions = (protocol.train_fraction, protocol.validation_fraction, protocol.test_fraction)
    if any(value <= 0 or value >= 1 for value in fractions) or sum(fractions) != 1:
        raise ValueError("Trend split fractions must be positive and sum to 1")
    if protocol.embargo_minutes < protocol.history_minutes:
        raise ValueError("Trend embargo must be at least the history window")


def validate_endpoint_frame(frame: pd.DataFrame, protocol: TrendProtocol) -> None:
    """Validate causal endpoint identity, provenance, and label fields."""

    validate_trend_protocol(protocol)
    missing = REQUIRED_ENDPOINT_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Trend endpoint frame is missing columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError("Trend endpoint frame must not be empty")

    identity = frame[["participant_id", "timestamp"]]
    if identity.duplicated().any():
        raise ValueError("Trend endpoint frame contains duplicate participant/timestamp identities")
    if frame["label"].isna().any() or not frame["label"].isin(protocol.classes).all():
        raise ValueError("Trend endpoint frame contains an invalid Trend label")
    if (frame["support_points"] <= 0).any():
        raise ValueError("Trend endpoint frame contains non-positive CGM support")
    timestamps = pd.to_datetime(frame["timestamp"], errors="coerce")
    history_start = pd.to_datetime(frame["history_start"], errors="coerce")
    if timestamps.isna().any() or history_start.isna().any():
        raise ValueError("Trend endpoint timestamps must be parseable")
    if not (history_start < timestamps).all():
        raise ValueError("Every Trend history_start must precede its endpoint timestamp")
    if "available_cgm_end" in frame.columns:
        available_end = pd.to_datetime(frame["available_cgm_end"], errors="coerce")
        if available_end.isna().any() or (timestamps > available_end).any():
            raise ValueError("Trend endpoint occurs after available CGM data")
