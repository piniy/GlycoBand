"""Deterministic BVP history features for registered Trend development."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

FEATURE_VERSION = "trend-feature-v1"
DEVELOPMENT_SPLITS = frozenset({"train", "validation"})
SHORT_WINDOW_FEATURES = (
    "mean",
    "std",
    "min",
    "max",
    "q25",
    "q75",
    "mean_abs_diff",
    "diff_std",
    "flat_fraction",
    "slope_per_min",
)
ENDPOINT_COLUMNS = (
    "participant_id",
    "timestamp",
    "history_start",
    "split",
    "label",
    "bvp_source_file",
    "protocol_version",
    "split_version",
)


def _window_feature_rows(
    times: np.ndarray, values: np.ndarray, window_samples: int
) -> list[dict[str, object]]:
    complete = values.size // window_samples
    if complete == 0:
        return []
    usable = complete * window_samples
    matrix = values[:usable].reshape(complete, window_samples)
    time_matrix = times[:usable].reshape(complete, window_samples)
    time_ns = time_matrix.astype("datetime64[ns]").astype(np.int64)
    elapsed_minutes = (time_ns - time_ns[:, [0]]) / (60.0 * 1_000_000_000.0)
    centered_minutes = elapsed_minutes - elapsed_minutes.mean(axis=1, keepdims=True)
    denominator = np.sum(centered_minutes**2, axis=1)
    if np.any(denominator <= 0):
        raise ValueError("BVP window timestamps must span positive elapsed time")
    differences = np.diff(matrix, axis=1)
    means = matrix.mean(axis=1)
    slopes = np.sum(
        (matrix - means[:, None]) * centered_minutes, axis=1
    ) / denominator
    rows: list[dict[str, object]] = []
    for index in range(complete):
        row: dict[str, object] = {
            "window_start": pd.Timestamp(time_matrix[index, 0]),
            "window_end": pd.Timestamp(time_matrix[index, -1]),
            "mean": float(means[index]),
            "std": float(matrix[index].std()),
            "min": float(matrix[index].min()),
            "max": float(matrix[index].max()),
            "q25": float(np.quantile(matrix[index], 0.25)),
            "q75": float(np.quantile(matrix[index], 0.75)),
            "mean_abs_diff": float(np.abs(differences[index]).mean()),
            "diff_std": float(differences[index].std()),
            "flat_fraction": float(np.mean(differences[index] == 0)),
            "slope_per_min": float(slopes[index]),
        }
        rows.append(row)
    return rows


def extract_bvp_window_features(
    path: Path,
    *,
    rate_hz: int,
    window_seconds: int,
    maximum_gap_seconds: float,
    stop_at: pd.Timestamp | None = None,
    chunksize: int = 1_000_000,
) -> pd.DataFrame:
    """Stream contiguous native BVP windows without reading beyond stop_at."""

    if rate_hz <= 0 or window_seconds <= 0:
        raise ValueError("BVP rate and window duration must be positive")
    if maximum_gap_seconds <= 0:
        raise ValueError("BVP maximum gap must be positive")
    window_samples = rate_hz * window_seconds
    maximum_gap = pd.Timedelta(seconds=maximum_gap_seconds).value
    carry_times = np.array([], dtype="datetime64[ns]")
    carry_values = np.array([], dtype=np.float64)
    rows: list[dict[str, object]] = []

    for chunk in pd.read_csv(path, chunksize=chunksize):
        if list(chunk.columns) not in (["datetime", " bvp"], ["datetime", "bvp"]):
            raise ValueError(f"Unexpected BVP schema in {path}: {list(chunk.columns)}")
        chunk.columns = [str(name).strip() for name in chunk.columns]
        parsed = pd.to_datetime(chunk["datetime"], errors="coerce")
        values = pd.to_numeric(chunk["bvp"], errors="coerce")
        valid = parsed.notna() & values.notna() & np.isfinite(values.to_numpy(dtype=float))
        if stop_at is not None:
            valid &= parsed <= stop_at
        if not valid.any():
            if stop_at is not None and parsed.notna().any() and parsed.max() > stop_at:
                break
            continue
        times = parsed[valid].to_numpy(dtype="datetime64[ns]")
        numeric_values = values[valid].to_numpy(dtype=np.float64)
        combined_times = np.concatenate((carry_times, times))
        combined_values = np.concatenate((carry_values, numeric_values))
        if combined_times.size < 2:
            carry_times = combined_times
            carry_values = combined_values
            continue
        gaps = np.diff(combined_times.astype("datetime64[ns]").astype(np.int64))
        breaks = np.flatnonzero((gaps <= 0) | (gaps > maximum_gap)) + 1
        starts = np.concatenate(([0], breaks))
        ends = np.concatenate((breaks, [combined_times.size]))
        carry_times = np.array([], dtype="datetime64[ns]")
        carry_values = np.array([], dtype=np.float64)
        for index, (start, end) in enumerate(zip(starts, ends, strict=True)):
            segment_times = combined_times[start:end]
            segment_values = combined_values[start:end]
            if segment_times.size == 0:
                continue
            complete = segment_times.size // window_samples
            usable = complete * window_samples
            if usable:
                rows.extend(
                    _window_feature_rows(
                        segment_times[:usable].astype("datetime64[ns]").astype(np.int64),
                        segment_values[:usable],
                        window_samples,
                    )
                )
            remainder_times = segment_times[usable:]
            remainder_values = segment_values[usable:]
            if index == len(starts) - 1:
                carry_times = remainder_times
                carry_values = remainder_values
    return pd.DataFrame.from_records(
        rows,
        columns=["window_start", "window_end", *SHORT_WINDOW_FEATURES],
    )


def _aggregate_history(
    windows: pd.DataFrame,
    endpoint: pd.Series,
    *,
    minimum_windows: int,
) -> dict[str, object] | None:
    start = pd.Timestamp(endpoint["history_start"])
    end = pd.Timestamp(endpoint["timestamp"])
    selected = windows[
        (pd.to_datetime(windows["window_start"]) >= start)
        & (pd.to_datetime(windows["window_end"]) <= end)
    ]
    if len(selected) < minimum_windows:
        return None
    result: dict[str, object] = {
        "participant_id": endpoint["participant_id"],
        "timestamp": endpoint["timestamp"],
        "history_start": endpoint["history_start"],
        "split": endpoint["split"],
        "label": endpoint["label"],
        "bvp_source_file": endpoint["bvp_source_file"],
        "protocol_version": endpoint["protocol_version"],
        "split_version": endpoint["split_version"],
        "feature_version": FEATURE_VERSION,
        "history_window_count": int(len(selected)),
    }
    for feature in SHORT_WINDOW_FEATURES:
        values = selected[feature].to_numpy(dtype=np.float64)
        result[f"history_{feature}_mean"] = float(values.mean())
        result[f"history_{feature}_std"] = float(values.std())
        result[f"history_{feature}_min"] = float(values.min())
        result[f"history_{feature}_max"] = float(values.max())
        result[f"history_{feature}_last"] = float(values[-1])
    return result


def aggregate_bvp_history_features(
    windows: pd.DataFrame,
    endpoints: pd.DataFrame,
    *,
    history_minutes: int,
    window_seconds: int,
    minimum_complete_windows: int,
) -> pd.DataFrame:
    """Aggregate only past short-window BVP features for development endpoints."""

    missing_endpoints = set(ENDPOINT_COLUMNS).difference(endpoints.columns)
    if missing_endpoints:
        raise ValueError(f"Trend endpoints are missing columns: {sorted(missing_endpoints)}")
    missing_windows = {
        "participant_id",
        "window_start",
        "window_end",
        *SHORT_WINDOW_FEATURES,
    }.difference(windows.columns)
    if missing_windows:
        raise ValueError(f"BVP windows are missing columns: {sorted(missing_windows)}")
    if history_minutes <= 0 or window_seconds <= 0 or minimum_complete_windows <= 0:
        raise ValueError("History, window duration, and minimum windows must be positive")
    derived_minimum = history_minutes * 60 // window_seconds - 1
    if minimum_complete_windows != derived_minimum:
        raise ValueError("Minimum complete windows must be derived from H30 and window duration")
    splits = set(endpoints["split"].astype(str))
    if not splits.issubset(DEVELOPMENT_SPLITS):
        raise ValueError("Trend feature aggregation accepts development splits only")
    frames: list[pd.DataFrame] = []
    for participant_id, endpoint_group in endpoints.groupby("participant_id", sort=True):
        participant_windows = windows[windows["participant_id"] == participant_id]
        participant_windows = participant_windows.sort_values("window_end")
        rows = [
            aggregated
            for _, endpoint in endpoint_group.sort_values("timestamp").iterrows()
            if (aggregated := _aggregate_history(
                participant_windows,
                endpoint,
                minimum_windows=minimum_complete_windows,
            ))
            is not None
        ]
        if rows:
            frames.append(pd.DataFrame(rows))
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).sort_values(
        ["participant_id", "timestamp"], kind="mergesort"
    ).reset_index(drop=True)
