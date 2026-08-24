from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from glycoband.evaluation.trend_baseline import (
    evaluate_trend_baselines,
    load_trend_baseline_config,
)
from glycoband.features.trend import SHORT_WINDOW_FEATURES


def _config() -> dict[str, object]:
    root = Path(__file__).resolve().parents[2]
    return load_trend_baseline_config(root / "configs/trend/baseline-v1.yaml")


def _features() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    labels = ["FALLING", "STABLE", "RISING"] * 8
    for index, label in enumerate(labels):
        row: dict[str, object] = {
            "participant_id": f"{index % 4 + 1:03d}",
            "timestamp": pd.Timestamp("2020-01-01") + pd.Timedelta(minutes=index),
            "history_start": pd.Timestamp("2019-12-31 23:30") + pd.Timedelta(minutes=index),
            "split": "train" if index < 12 else "validation",
            "label": label,
            "bvp_source_file": f"{index % 4 + 1:03d}/BVP.csv",
            "protocol_version": "trend-label-v1",
            "split_version": "trend-split-v1",
            "feature_version": "trend-feature-v1",
            "history_window_count": 59,
        }
        for feature_index, feature in enumerate(SHORT_WINDOW_FEATURES):
            for aggregation_index, aggregation in enumerate(("mean", "std", "min", "max", "last")):
                row[f"history_{feature}_{aggregation}"] = float(
                    index + feature_index * 0.1 + aggregation_index * 0.01
                )
        rows.append(row)
    return pd.DataFrame(rows)


def test_evaluate_trend_baselines_uses_train_and_validation_only() -> None:
    report, predictions, participant_metrics = evaluate_trend_baselines(_features(), _config())

    assert report["final_test_accessed"] is False
    assert report["train_rows"] == 12
    assert report["validation_rows"] == 12
    assert report["feature_count"] == 50
    assert {str(value) for value in predictions["model"].unique()} == {
        "majority",
        "always_stable",
        "logistic_history",
        "logistic_current_window",
        "logistic_shifted_control",
    }
    assert len(predictions) == 60
    assert {"participant_id", "model", "macro_f1"}.issubset(participant_metrics.columns)


def test_evaluator_ignores_numeric_provenance_columns() -> None:
    features = _features().assign(embargo_minutes=30)
    report, _, _ = evaluate_trend_baselines(features, _config())

    assert "history_window_count" not in report["history_feature_columns"]
    assert "embargo_minutes" not in report["history_feature_columns"]


def test_evaluator_reports_opposite_direction_errors_and_bootstrap_deltas() -> None:
    report, _, _ = evaluate_trend_baselines(_features(), _config())

    history = next(row for row in report["models"] if row["model"] == "logistic_history")
    assert 0.0 <= history["opposite_direction_error_rate"] <= 1.0
    assert set(report["paired_participant_bootstrap"]) == {
        "history_minus_best_constant",
        "history_minus_shifted_control",
        "history_minus_current_window",
    }


def test_evaluate_trend_baselines_rejects_test_rows() -> None:
    features = _features()
    features.loc[0, "split"] = "test"

    with pytest.raises(ValueError, match="final-test"):
        evaluate_trend_baselines(features, _config())


def test_evaluate_trend_baselines_requires_explicit_history_features() -> None:
    features = _features().drop(columns=["history_mean_mean"])

    with pytest.raises(ValueError, match="explicit columns"):
        evaluate_trend_baselines(features, _config())
