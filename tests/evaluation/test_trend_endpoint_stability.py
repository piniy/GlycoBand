from __future__ import annotations

import pandas as pd
import pytest

from glycoband.evaluation.trend_endpoint_stability import compare_to_primary


def _labels() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "participant_id": "001",
                "candidate_id": "primary",
                "timestamp": "2020-01-01 00:00:00",
                "history_start": "2019-12-31 23:30:00",
                "slope_mg_dl_min": 0.6,
                "threshold_mg_dl_min": 0.5,
                "label": "RISING",
            },
            {
                "participant_id": "001",
                "candidate_id": "primary",
                "timestamp": "2020-01-01 00:05:00",
                "history_start": "2019-12-31 23:35:00",
                "slope_mg_dl_min": 0.0,
                "threshold_mg_dl_min": 0.5,
                "label": "STABLE",
            },
            {
                "participant_id": "002",
                "candidate_id": "primary",
                "timestamp": "2020-01-01 00:00:00",
                "history_start": "2019-12-31 23:30:00",
                "slope_mg_dl_min": -0.9,
                "threshold_mg_dl_min": 0.5,
                "label": "FALLING",
            },
            {
                "participant_id": "001",
                "candidate_id": "short",
                "timestamp": "2020-01-01 00:00:00",
                "history_start": "2019-12-31 23:45:00",
                "slope_mg_dl_min": 0.1,
                "threshold_mg_dl_min": 0.5,
                "label": "STABLE",
            },
            {
                "participant_id": "002",
                "candidate_id": "short",
                "timestamp": "2020-01-01 00:00:00",
                "history_start": "2019-12-31 23:45:00",
                "slope_mg_dl_min": -0.7,
                "threshold_mg_dl_min": 0.5,
                "label": "FALLING",
            },
            {
                "participant_id": "002",
                "candidate_id": "short",
                "timestamp": "2020-01-01 00:05:00",
                "history_start": "2019-12-31 23:50:00",
                "slope_mg_dl_min": 0.8,
                "threshold_mg_dl_min": 0.5,
                "label": "RISING",
            },
        ]
    ).assign(
        timestamp=lambda frame: pd.to_datetime(frame["timestamp"]),
        history_start=lambda frame: pd.to_datetime(frame["history_start"]),
    )


def test_compare_to_primary_uses_exact_participant_timestamp_keys() -> None:
    pooled, per_person, transitions = compare_to_primary(_labels(), "primary")

    candidate = pooled.set_index("candidate_id").loc["short"]
    assert candidate["primary_endpoints"] == 3
    assert candidate["candidate_endpoints"] == 3
    assert candidate["shared_endpoints"] == 2
    assert candidate["union_endpoints"] == 4
    assert candidate["endpoint_jaccard"] == 0.5
    assert candidate["exact_label_agreement"] == 0.5
    assert len(per_person.loc[per_person["candidate_id"] == "short"]) == 2
    assert transitions.loc[transitions["candidate_id"] == "short", "count"].sum() == 2


def test_compare_to_primary_rejects_duplicate_candidate_endpoint_keys() -> None:
    duplicated = pd.concat([_labels(), _labels().iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="duplicate"):
        compare_to_primary(duplicated, "primary")
