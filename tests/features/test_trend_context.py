from __future__ import annotations

import pandas as pd

from glycoband.features.trend_context import align_acc_energy


def test_context_alignment_never_uses_future_acc() -> None:
    timestamps = pd.date_range("2020-01-01", periods=61, freq="30s")
    acc = pd.DataFrame({"timestamp": timestamps, "x": 0.1, "y": 0.2, "z": 0.9})
    aligned = align_acc_energy(acc, endpoint_time=pd.Timestamp("2020-01-01 00:30"))
    assert aligned["window_end"].max() <= pd.Timestamp("2020-01-01 00:30")
