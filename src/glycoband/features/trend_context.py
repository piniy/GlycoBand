"""Past-only context alignment helpers for exploratory Trend quality probes."""

from __future__ import annotations

import numpy as np
import pandas as pd


def align_acc_energy(
    acc: pd.DataFrame,
    *,
    endpoint_time: pd.Timestamp,
    history_start: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Return 30-second ACC RMS windows ending no later than the endpoint."""

    required = {"timestamp", "x", "y", "z"}
    missing = required.difference(acc.columns)
    if missing:
        raise ValueError(f"ACC frame is missing columns: {sorted(missing)}")
    values = acc.copy()
    values["timestamp"] = pd.to_datetime(values["timestamp"])
    values = values[values["timestamp"] <= pd.Timestamp(endpoint_time)]
    if history_start is not None:
        values = values[values["timestamp"] >= pd.Timestamp(history_start)]
    if values.empty:
        return pd.DataFrame(columns=["window_start", "window_end", "acc_rms"])
    values = values.sort_values("timestamp")
    magnitude = np.sqrt(
        values["x"].to_numpy(dtype=float) ** 2
        + values["y"].to_numpy(dtype=float) ** 2
        + values["z"].to_numpy(dtype=float) ** 2
    )
    timestamps = values["timestamp"].to_numpy(dtype="datetime64[ns]")
    rows: list[dict[str, object]] = []
    for start in range(0, len(values), 16):
        end = min(start + 16, len(values))
        if end - start < 2:
            continue
        rows.append(
            {
                "window_start": pd.Timestamp(timestamps[start]),
                "window_end": pd.Timestamp(timestamps[end - 1]),
                "acc_rms": float(np.sqrt(np.mean(magnitude[start:end] ** 2))),
            }
        )
    result = pd.DataFrame(rows)
    if not result.empty and (result["window_end"] > pd.Timestamp(endpoint_time)).any():
        raise AssertionError("ACC alignment used future samples")
    return result
