from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from glycoband.features.trend_conditioning import (
    BP_0P5_8_ZSCORE,
    apply_quality_policy,
    compute_window_quality,
    condition_window,
    fit_participant_quality_thresholds,
)


def test_bandpass_preserves_two_hz_and_attenuates_baseline_drift() -> None:
    rate_hz = 64
    time = np.arange(rate_hz * 30) / rate_hz
    values = np.sin(2 * np.pi * 2.0 * time) + 2.0 * np.sin(2 * np.pi * 0.1 * time)
    filtered = condition_window(values, rate_hz, BP_0P5_8_ZSCORE)
    assert abs(filtered.mean()) < 1e-6
    assert np.std(filtered) == pytest.approx(1.0, rel=0.05)
    reference = np.sin(2 * np.pi * 2.0 * time)
    assert np.corrcoef(filtered, reference)[0, 1] > 0.90


def test_conditioning_rejects_band_above_nyquist() -> None:
    from glycoband.features.trend_conditioning import ConditioningSpec

    spec = ConditioningSpec("bad", "linear", 0.5, 40.0, 4, "zscore")
    with pytest.raises(ValueError, match="Nyquist"):
        condition_window(np.ones(1920), 64, spec)


def test_quality_thresholds_use_train_rows_only() -> None:
    windows = pd.DataFrame(
        {
            "participant_id": ["001", "001", "001", "001"],
            "split": ["train", "train", "train", "validation"],
            "sqi": [0.1, 0.2, 0.3, 0.99],
        }
    )
    thresholds = fit_participant_quality_thresholds(windows.query("split == 'train'"))
    assert thresholds.loc["001", "hard_exclusion_cutoff"] == pytest.approx(0.12)
    with pytest.raises(ValueError, match="train rows only"):
        fit_participant_quality_thresholds(windows)


def test_quality_policy_marks_hard_exclusion_and_soft_weight() -> None:
    history = pd.DataFrame({"participant_id": ["001", "001"], "sqi": [0.1, 0.9]})
    thresholds = pd.DataFrame(
        {"hard_exclusion_cutoff": [0.2], "soft_weight_floor": [0.5]}, index=["001"]
    )
    hard = apply_quality_policy(history, "hard_exclude_bottom_train_decile", thresholds)
    soft = apply_quality_policy(history, "soft_weight", thresholds)
    assert hard["quality_retained"].tolist() == [False, True]
    assert soft["quality_weight"].tolist() == [0.25, 1.0]


def test_window_quality_is_bounded() -> None:
    raw = np.sin(np.linspace(0, 20, 1920))
    quality = compute_window_quality(raw, condition_window(raw, 64, BP_0P5_8_ZSCORE), rate_hz=64)
    assert 0 <= quality.sqi <= 1
