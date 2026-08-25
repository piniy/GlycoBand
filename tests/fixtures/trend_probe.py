from __future__ import annotations

import pandas as pd


def development_probe_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    for participant_id in ("001", "002"):
        for index, (label, slope) in enumerate(
            (("FALLING", -0.8), ("STABLE", -0.1), ("RISING", 0.8), ("STABLE", 0.0))
        ):
            timestamp = pd.Timestamp("2020-01-01") + pd.Timedelta(minutes=5 * index)
            rows.append(
                {
                    "participant_id": participant_id,
                    "timestamp": timestamp,
                    "history_start": timestamp - pd.Timedelta(minutes=30),
                    "split": "train" if index < 3 else "validation",
                    "label": label,
                    "slope_mg_dl_min": slope,
                    "bvp_source_file": f"{participant_id}/BVP_{participant_id}.csv",
                    "protocol_version": "trend-label-v1",
                }
            )
    endpoints = pd.DataFrame(rows)
    features = endpoints.drop(columns=["slope_mg_dl_min", "history_start"]).copy()
    features["history_mean_mean"] = endpoints["slope_mg_dl_min"]
    features["history_flat_fraction_max"] = [0.0, 0.1, 0.2, 0.0] * 2
    features["feature_version"] = "trend-feature-v1"
    return endpoints, features
