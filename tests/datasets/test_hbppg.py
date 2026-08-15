from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from glycoband.datasets.hbppg import (
    Category,
    _channel_metrics,
    audit_participant,
    classify_value,
)


def test_classify_value_uses_half_open_boundaries() -> None:
    categories = [Category("A", None, 5.6), Category("B", 5.6, 7.0), Category("C", 7.0, None)]
    assert classify_value(5.59, categories) == "A"
    assert classify_value(5.6, categories) == "B"
    assert classify_value(7.0, categories) == "C"


def test_classify_value_rejects_gaps_and_overlaps() -> None:
    with pytest.raises(ValueError, match="matched 0"):
        classify_value(2.0, [Category("A", 3.0, None)])
    with pytest.raises(ValueError, match="matched 2"):
        classify_value(4.0, [Category("A", None, 5.0), Category("B", 3.0, None)])


def test_channel_metrics_use_configured_spectral_bands() -> None:
    time = np.arange(2000) / 200
    signal = np.sin(2 * np.pi * time)
    included = _channel_metrics(signal, 200, (0.5, 4.0), (0.1, 10.0))
    excluded = _channel_metrics(signal, 200, (2.0, 4.0), (0.1, 10.0))
    assert included["pulse_band_ratio"] > 0.9
    assert excluded["pulse_band_ratio"] < 0.1


def test_audit_participant_preserves_identity_and_flags_rate(tmp_path: Path) -> None:
    path = tmp_path / "7.csv"
    signal = np.sin(np.linspace(0, 20 * np.pi, 1000))
    pd.DataFrame({name: signal for name in ["660nm", "730nm", "850nm", "940nm"]}).to_csv(
        path, index=False
    )
    metadata = pd.Series(
        {"Blood glucose (mmol/L)": 5.8, "Signal length (second)": 10}
    )
    result = audit_participant(
        7,
        metadata,
        path,
        ["660nm", "730nm", "850nm", "940nm"],
        200,
        {
            "maximum_flat_difference_fraction": 0.2,
            "maximum_extrema_fraction": 0.05,
            "minimum_pulse_band_ratio": 0.1,
            "pulse_band_hz": [0.5, 4.0],
            "spectral_reference_band_hz": [0.1, 10.0],
        },
    )
    assert result["participant_id"] == 7
    assert result["source_file"] == "data_csv/7.csv"
    assert result["rows"] == 1000
    assert "IMPLIED_RATE_MISMATCH" in result["exclusion_reasons"]
    assert "DUPLICATE_WAVELENGTH_CONTENT" in result["exclusion_reasons"]


def test_audit_participant_detects_copied_wavelengths_at_valid_rate(tmp_path: Path) -> None:
    path = tmp_path / "11.csv"
    signal = np.sin(np.linspace(0, 20 * np.pi, 2000))
    pd.DataFrame({name: signal for name in ["660nm", "730nm", "850nm", "940nm"]}).to_csv(
        path, index=False
    )
    metadata = pd.Series(
        {"Blood glucose (mmol/L)": 5.8, "Signal length (second)": 10}
    )
    result = audit_participant(
        11,
        metadata,
        path,
        ["660nm", "730nm", "850nm", "940nm"],
        200,
        {
            "maximum_flat_difference_fraction": 0.2,
            "maximum_extrema_fraction": 0.05,
            "minimum_pulse_band_ratio": 0.1,
            "pulse_band_hz": [0.5, 4.0],
            "spectral_reference_band_hz": [0.1, 10.0],
        },
    )
    assert result["audit_usable"] is False
    assert result["duplicate_channel_pairs"]
    assert "DUPLICATE_WAVELENGTH_CONTENT" in result["exclusion_reasons"]


def test_audit_participant_reports_missing_file(tmp_path: Path) -> None:
    metadata = pd.Series(
        {"Blood glucose (mmol/L)": "/", "Signal length (second)": 60}
    )
    result = audit_participant(
        9,
        metadata,
        tmp_path / "9.csv",
        ["660nm", "730nm", "850nm", "940nm"],
        200,
        {
            "maximum_flat_difference_fraction": 0.2,
            "maximum_extrema_fraction": 0.05,
            "minimum_pulse_band_ratio": 0.1,
            "pulse_band_hz": [0.5, 4.0],
            "spectral_reference_band_hz": [0.1, 10.0],
        },
    )
    assert result["file_exists"] is False
    assert result["exclusion_reasons"] == "MISSING_CSV;MISSING_GLUCOSE_REFERENCE"
