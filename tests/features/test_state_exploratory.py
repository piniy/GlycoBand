from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from glycoband.features.state_exploratory import (
    STATE_CHANNELS,
    add_candidate_state_labels,
    assert_development_ids,
    create_state_test_reserve,
    extract_state_features,
    load_state_test_reserve,
)


def test_extract_state_features_is_finite_and_interpretable() -> None:
    time = np.arange(2000) / 200.0
    frame = pd.DataFrame(
        {
            channel: 2.0 + np.sin(2 * np.pi * (1.2 + index * 0.1) * time)
            for index, channel in enumerate(STATE_CHANNELS)
        }
    )
    features = extract_state_features(frame)
    assert features["ppg_660nm_mean"] == pytest.approx(2.0, abs=0.01)
    assert features["ppg_660nm_dominant_frequency_hz"] == pytest.approx(1.2, abs=0.11)
    assert all(np.isfinite(value) for value in features.values())


def test_state_reserve_is_deterministic_and_disjoint(tmp_path: Path) -> None:
    participants = pd.DataFrame(
        {
            "participant_id": range(1, 21),
            "glucose_mmol_l": [4.5] * 15 + [6.2] * 5,
            "state_reference_eligible": [True] * 20,
        }
    )
    path = tmp_path / "state_test_reserve-v0.json"
    first = create_state_test_reserve(participants, path, seed=7, created_date="2026-08-17")
    second = create_state_test_reserve(
        participants,
        tmp_path / "second.json",
        seed=7,
        created_date="2026-08-17",
    )
    assert first["reserved_test_ids"] == second["reserved_test_ids"]
    assert not set(first["development_ids"]) & set(first["reserved_test_ids"])
    assert load_state_test_reserve(path)["eligible_participant_count"] == 20
    with pytest.raises(AssertionError, match="reserved"):
        assert_development_ids([first["reserved_test_ids"][0]], first)


def test_candidate_labels_keep_continuous_reference_separate() -> None:
    table = pd.DataFrame({"participant_id": [1, 2, 3], "glucose_reference": [5.59, 5.6, 7.0]})
    result = add_candidate_state_labels(table)
    assert result["candidate_a_binary"].tolist() == [
        "NORMAL_RANGE",
        "ELEVATED_FASTING_RANGE",
        "ELEVATED_FASTING_RANGE",
    ]
    assert result["candidate_b_ada_3class"].tolist() == [
        "NORMAL_RANGE",
        "PREDIABETES_RANGE",
        "DIABETES_RANGE",
    ]
    assert result["candidate_d_continuous"].tolist() == [5.59, 5.6, 7.0]


def test_load_state_reserve_rejects_count_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "seed": 1,
                "dataset": "hbppg",
                "dataset_version": "hbppg-v6",
                "eligible_participant_count": 3,
                "development_ids": [1],
                "reserved_test_ids": [2],
                "source_audit": {},
                "created_date": "2026-08-17",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="counts"):
        load_state_test_reserve(path)
