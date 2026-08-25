"""Leakage-safe descriptive diagnostics for Trend development artifacts."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Literal, cast

import numpy as np
import pandas as pd

DEVELOPMENT_SPLITS = frozenset({"train", "validation"})
CLASS_ORDER = ("FALLING", "STABLE", "RISING")
IDENTITY_COLUMNS = ("participant_id", "timestamp")
SLOPE_COLUMN = "slope_mg_dl_min"


def validate_development_frame(
    frame: pd.DataFrame,
    *,
    require_slope: bool = False,
    name: str = "frame",
) -> None:
    """Validate identity and final-test exclusion for a development-only frame."""

    required = set(IDENTITY_COLUMNS) | {"participant_id", "split", "label"}
    if require_slope:
        required.add(SLOPE_COLUMN)
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{name} is missing columns: {sorted(missing)}")
    splits = set(frame["split"].astype(str))
    forbidden = splits.difference(DEVELOPMENT_SPLITS)
    if forbidden:
        raise ValueError(f"{name} contains forbidden splits: {sorted(forbidden)}")
    if frame.duplicated(list(IDENTITY_COLUMNS)).any():
        raise ValueError(f"{name} contains duplicate endpoint identity keys")
    if frame["participant_id"].isna().any() or frame["timestamp"].isna().any():
        raise ValueError(f"{name} contains null endpoint identity values")
    labels = set(frame["label"].astype(str))
    unknown = labels.difference(CLASS_ORDER)
    if unknown:
        raise ValueError(f"{name} contains unknown labels: {sorted(unknown)}")


def class_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    """Return participant/split class counts and within-group fractions."""

    validate_development_frame(frame, require_slope=False)
    participants = sorted(frame["participant_id"].astype(str).unique())
    splits = [split for split in ("train", "validation") if split in set(frame["split"])]
    index = pd.MultiIndex.from_product(
        [participants, splits, CLASS_ORDER],
        names=["participant_id", "split", "label"],
    )
    counts = (
        frame.assign(participant_id=frame["participant_id"].astype(str))
        .groupby(["participant_id", "split", "label"], observed=False)
        .size()
        .reindex(index, fill_value=0)
        .rename("count")
        .reset_index()
    )
    totals = counts.groupby(["participant_id", "split"], observed=False)["count"].transform(
        "sum"
    )
    counts["fraction"] = np.divide(
        counts["count"].to_numpy(dtype=float),
        totals.to_numpy(dtype=float),
        out=np.zeros(len(counts), dtype=float),
        where=totals.to_numpy(dtype=float) > 0,
    )
    return counts


def slope_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize the continuous CGM slope before thresholded labels."""

    validate_development_frame(frame, require_slope=True)
    values = pd.to_numeric(frame[SLOPE_COLUMN], errors="coerce")
    if values.isna().any() or not np.isfinite(values.to_numpy(dtype=float)).all():
        raise ValueError("Slope diagnostic contains non-finite values")
    groups: list[tuple[str, pd.Series]] = [("all", values)]
    groups.extend(
        (str(split), values[frame["split"] == split]) for split in ("train", "validation")
    )
    rows: list[dict[str, object]] = []
    for split, series in groups:
        array = series.to_numpy(dtype=float)
        rows.append(
            {
                "split": split,
                "count": int(array.size),
                "min": float(np.min(array)),
                "p01": float(np.quantile(array, 0.01)),
                "p05": float(np.quantile(array, 0.05)),
                "p25": float(np.quantile(array, 0.25)),
                "median": float(np.median(array)),
                "p75": float(np.quantile(array, 0.75)),
                "p95": float(np.quantile(array, 0.95)),
                "p99": float(np.quantile(array, 0.99)),
                "max": float(np.max(array)),
                "mean": float(np.mean(array)),
                "std": float(np.std(array)),
            }
        )
    return pd.DataFrame(rows)


def slope_threshold_summary(
    frame: pd.DataFrame, *, threshold_mg_dl_min: float = 0.5
) -> pd.DataFrame:
    """Count slope values in the stable and directional threshold regions."""

    validate_development_frame(frame, require_slope=True)
    if threshold_mg_dl_min <= 0:
        raise ValueError("Slope threshold must be positive")
    values = pd.to_numeric(frame[SLOPE_COLUMN], errors="coerce").to_numpy(dtype=float)
    masks = {
        "FALLING_region": values < -threshold_mg_dl_min,
        "STABLE_region": np.abs(values) <= threshold_mg_dl_min,
        "RISING_region": values > threshold_mg_dl_min,
    }
    rows: list[dict[str, object]] = []
    total = len(values)
    for region, mask in masks.items():
        count = int(mask.sum())
        rows.append(
            {
                "split": "all",
                "region": region,
                "threshold_mg_dl_min": threshold_mg_dl_min,
                "count": count,
                "fraction": count / total if total else 0.0,
            }
        )
        for split in ("train", "validation"):
            split_mask = frame["split"].to_numpy(dtype=object) == split
            split_count = int((mask & split_mask).sum())
            split_total = int(split_mask.sum())
            rows.append(
                {
                    "split": split,
                    "region": region,
                    "threshold_mg_dl_min": threshold_mg_dl_min,
                    "count": split_count,
                    "fraction": split_count / split_total if split_total else 0.0,
                }
            )
    return pd.DataFrame(rows)


CorrelationMethod = Literal["pearson", "spearman"]


def _correlation(x: pd.Series, y: pd.Series, method: CorrelationMethod) -> float:
    valid = pd.concat([x, y], axis=1).replace([np.inf, -np.inf], np.nan).dropna()
    if len(valid) < 3 or valid.iloc[:, 0].nunique() < 2 or valid.iloc[:, 1].nunique() < 2:
        return float("nan")
    return float(valid.iloc[:, 0].corr(valid.iloc[:, 1], method=method))


def feature_slope_correlations(
    features: pd.DataFrame,
    endpoints: pd.DataFrame,
    *,
    methods: Sequence[str] = ("pearson", "spearman"),
    feature_columns: Iterable[str] | None = None,
) -> pd.DataFrame:
    """Measure pooled and participant-level correlations with continuous CGM slope."""

    validate_development_frame(features, name="features")
    validate_development_frame(endpoints, require_slope=True, name="endpoints")
    keys = list(IDENTITY_COLUMNS)
    endpoint_values = endpoints[keys + [SLOPE_COLUMN]].copy()
    merged = features.merge(endpoint_values, on=keys, how="inner", validate="one_to_one")
    if len(merged) != len(features) or len(merged) != len(endpoint_values):
        raise ValueError("Feature and endpoint artifacts do not have identical development keys")
    if feature_columns is None:
        selected = [
            column
            for column in features.columns
            if column.startswith("history_") and pd.api.types.is_numeric_dtype(features[column])
        ]
    else:
        selected = list(feature_columns)
    if not selected:
        raise ValueError("No numeric history feature columns were supplied")
    unknown_methods = set(methods).difference({"pearson", "spearman"})
    if unknown_methods:
        raise ValueError(f"Unsupported correlation methods: {sorted(unknown_methods)}")
    rows: list[dict[str, object]] = []
    for feature in selected:
        if feature not in merged.columns:
            raise ValueError(f"Feature column not found: {feature}")
        pooled_x = pd.to_numeric(merged[feature], errors="coerce")
        pooled_y = pd.to_numeric(merged[SLOPE_COLUMN], errors="coerce")
        for method in methods:
            method_value = cast(CorrelationMethod, method)
            participant_values = [
                _correlation(group[feature], group[SLOPE_COLUMN], method_value)
                for _, group in merged.groupby("participant_id", sort=True)
            ]
            finite = np.asarray([value for value in participant_values if np.isfinite(value)])
            rows.append(
                {
                    "feature": feature,
                    "method": method,
                    "pooled_n": int(pd.concat([pooled_x, pooled_y], axis=1).dropna().shape[0]),
                    "pooled_correlation": _correlation(pooled_x, pooled_y, method_value),
                    "participant_count": int(finite.size),
                    "participant_mean": float(np.mean(finite)) if finite.size else float("nan"),
                    "participant_median": float(np.median(finite)) if finite.size else float("nan"),
                    "participant_iqr": (
                        float(np.quantile(finite, 0.75) - np.quantile(finite, 0.25))
                        if finite.size
                        else float("nan")
                    ),
                    "participant_min": float(np.min(finite)) if finite.size else float("nan"),
                    "participant_max": float(np.max(finite)) if finite.size else float("nan"),
                }
            )
    return pd.DataFrame(rows)


def flat_fraction_summary(
    features: pd.DataFrame, *, thresholds: Sequence[float] = (0.01, 0.05, 0.10)
) -> pd.DataFrame:
    """Summarize the baseline flat-fraction proxies by split and threshold."""

    validate_development_frame(features, name="features")
    if any(threshold < 0 or threshold > 1 for threshold in thresholds):
        raise ValueError("Flat-fraction thresholds must lie in [0, 1]")
    columns = [
        column
        for column in features.columns
        if column.startswith("history_flat_fraction_")
        and pd.api.types.is_numeric_dtype(features[column])
    ]
    if not columns:
        raise ValueError("No history flat-fraction features were supplied")
    rows: list[dict[str, object]] = []
    for split in ("train", "validation"):
        subset = features[features["split"] == split]
        for column in columns:
            values = pd.to_numeric(subset[column], errors="coerce").dropna().to_numpy(dtype=float)
            for threshold in thresholds:
                count = int((values >= threshold).sum())
                rows.append(
                    {
                        "split": split,
                        "feature": column,
                        "threshold": float(threshold),
                        "count": count,
                        "fraction": count / len(values) if len(values) else 0.0,
                        "median": float(np.median(values)) if len(values) else float("nan"),
                        "p95": float(np.quantile(values, 0.95)) if len(values) else float("nan"),
                    }
                )
    return pd.DataFrame(rows)


def phase0_gate(
    endpoints: pd.DataFrame,
    distribution: pd.DataFrame,
    *,
    minimum_directional_fraction: float = 0.05,
    maximum_missing_directional_participants: int = 4,
) -> dict[str, object]:
    """Return a descriptive gate for whether Phase 1 is worth running."""

    validate_development_frame(endpoints, require_slope=True, name="endpoints")
    participant_totals = endpoints.groupby("participant_id", observed=False).size()
    directional = distribution[distribution["label"].isin(["FALLING", "RISING"])].groupby(
        "participant_id", observed=False
    )["count"].sum()
    directional = directional.reindex(participant_totals.index, fill_value=0)
    directional_fraction = directional / participant_totals
    missing_falling = int(
        distribution[distribution["label"] == "FALLING"].groupby("participant_id")["count"].sum()
        .reindex(participant_totals.index, fill_value=0)
        .eq(0)
        .sum()
    )
    missing_rising = int(
        distribution[distribution["label"] == "RISING"].groupby("participant_id")["count"].sum()
        .reindex(participant_totals.index, fill_value=0)
        .eq(0)
        .sum()
    )
    median_fraction = float(directional_fraction.median()) if len(directional_fraction) else 0.0
    status = "PASS"
    reasons: list[str] = []
    if (
        missing_falling > maximum_missing_directional_participants
        or missing_rising > maximum_missing_directional_participants
        or median_fraction < minimum_directional_fraction
    ):
        status = "LABEL_SUPPORT_RISK"
        if missing_falling > maximum_missing_directional_participants:
            reasons.append("too_many_participants_without_FALLING")
        if missing_rising > maximum_missing_directional_participants:
            reasons.append("too_many_participants_without_RISING")
        if median_fraction < minimum_directional_fraction:
            reasons.append("median_directional_fraction_below_5_percent")
    return {
        "status": status,
        "missing_falling_participants": missing_falling,
        "missing_rising_participants": missing_rising,
        "median_directional_fraction": median_fraction,
        "minimum_directional_fraction": minimum_directional_fraction,
        "maximum_missing_directional_participants": maximum_missing_directional_participants,
        "reasons": reasons,
    }
