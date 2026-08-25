from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from glycoband.evaluation.trend_diagnostics import (
    class_distribution,
    feature_slope_correlations,
    flat_fraction_summary,
    phase0_gate,
    validate_development_frame,
)

_FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures/trend_probe.py"
_SPEC = importlib.util.spec_from_file_location("trend_probe_fixture", _FIXTURE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
development_probe_frames = _MODULE.development_probe_frames


def test_development_validator_rejects_final_test_rows() -> None:
    endpoints, _ = development_probe_frames()
    endpoints.loc[0, "split"] = "test"

    with pytest.raises(ValueError, match="forbidden splits"):
        validate_development_frame(endpoints, require_slope=True)


def test_development_validator_rejects_duplicate_identity() -> None:
    endpoints, _ = development_probe_frames()
    duplicated = pd.concat([endpoints, endpoints.iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="duplicate endpoint identity"):
        validate_development_frame(duplicated, require_slope=True)


def test_diagnostics_return_correlations_quality_and_gate() -> None:
    endpoints, features = development_probe_frames()
    distribution = class_distribution(endpoints)
    correlations = feature_slope_correlations(features, endpoints)
    quality = flat_fraction_summary(features)
    gate = phase0_gate(endpoints, distribution)

    assert set(distribution["label"]) == {"FALLING", "STABLE", "RISING"}
    assert set(correlations["method"]) == {"pearson", "spearman"}
    assert correlations.loc[
        (correlations["feature"] == "history_mean_mean")
        & (correlations["method"] == "pearson"),
        "pooled_correlation",
    ].iloc[0] == pytest.approx(1.0)
    assert set(quality["threshold"]) == {0.01, 0.05, 0.10}
    assert gate["status"] == "PASS"
