from __future__ import annotations

import pandas as pd

from glycoband.evaluation.trend_formulation import candidate_metrics, participant_compositions


def _candidate_rows() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    protocols = [
        (30, 0.5, "median3", "ols"),
        (15, 0.5, "median3", "ols"),
        (60, 0.5, "median3", "ols"),
        (30, 1.0, "median3", "ols"),
        (30, 0.5, "median3", "theil_sen"),
    ]
    for protocol in protocols:
        for participant_id in ("001", "002"):
            falling = 2 if participant_id == "001" else 1
            rising = 1 if participant_id == "001" else 2
            rows.append(
                {
                    "participant_id": participant_id,
                    "history_minutes": protocol[0],
                    "threshold_mg_dl_min": protocol[1],
                    "smoothing": protocol[2],
                    "slope_method": protocol[3],
                    "eligible_endpoints": 4,
                    "falling": falling,
                    "stable": 1,
                    "rising": rising,
                }
            )
    return pd.DataFrame(rows)


def test_candidate_metrics_preserve_support_and_primary_distance() -> None:
    metrics = candidate_metrics(_candidate_rows())
    assert len(metrics) == 5
    assert set(metrics["participants"]) == {2}
    assert set(metrics["participant_support_falling"]) == {2}
    assert metrics.iloc[0]["composition_tv_vs_primary_mean"] == 0


def test_participant_compositions_has_one_row_per_protocol_participant() -> None:
    compositions = participant_compositions(_candidate_rows())
    assert len(compositions) == 10
    assert compositions["candidate_id"].nunique() == 5
    assert compositions.filter(like="_fraction").sum(axis=1).round(8).eq(1).all()
