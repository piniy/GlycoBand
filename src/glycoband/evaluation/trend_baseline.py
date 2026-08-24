"""Registered development baselines and controls for frozen Trend data."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from sklearn.impute import SimpleImputer  # type: ignore[import-untyped]
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
from sklearn.metrics import (  # type: ignore[import-untyped]
    balanced_accuracy_score,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]
from sklearn.preprocessing import StandardScaler  # type: ignore[import-untyped]

from glycoband.features.trend import SHORT_WINDOW_FEATURES

BASELINE_NAMES = (
    "majority",
    "always_stable",
    "logistic_history",
    "logistic_current_window",
    "logistic_shifted_control",
)
LABELS = ("FALLING", "STABLE", "RISING")
IDENTITY_COLUMNS = {
    "participant_id",
    "timestamp",
    "history_start",
    "split",
    "label",
    "bvp_source_file",
    "protocol_version",
    "split_version",
    "feature_version",
    "history_window_count",
}


def load_trend_baseline_config(path: Path) -> dict[str, Any]:
    """Load and validate the predeclared Trend baseline configuration."""

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("Trend baseline config must be a mapping")
    config = dict(payload)
    if config["experiment"]["id"] != "trend-baseline-v1":
        raise ValueError("Unsupported Trend baseline experiment ID")
    if config["label"]["version"] != "trend-label-v1":
        raise ValueError("Trend baseline label version mismatch")
    if config["split"]["version"] != "trend-split-v1":
        raise ValueError("Trend baseline split version mismatch")
    if config["feature"]["version"] != "trend-feature-v1":
        raise ValueError("Trend baseline feature version mismatch")
    return config


def _history_feature_columns() -> list[str]:
    return [
        f"history_{feature}_{aggregation}"
        for feature in SHORT_WINDOW_FEATURES
        for aggregation in ("mean", "std", "min", "max", "last")
    ]


def _current_window_feature_columns() -> list[str]:
    return [f"history_{feature}_last" for feature in SHORT_WINDOW_FEATURES]


def _majority_label(labels: Iterable[str]) -> str:
    counts = pd.Series(list(labels), dtype="string").value_counts()
    return str(sorted(counts[counts == counts.max()].index.astype(str))[0])


def _pipeline(config: Mapping[str, Any]) -> Pipeline:
    settings = config["logistic_regression"]
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy=str(settings["imputer"]))),
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    max_iter=int(settings["max_iter"]),
                    random_state=int(settings["random_state"]),
                    class_weight=settings.get("class_weight"),
                ),
            ),
        ]
    )


def _opposite_direction_error_rate(actual: pd.Series, predicted: pd.Series) -> float:
    opposite = ((actual == "FALLING") & (predicted == "RISING")) | (
        (actual == "RISING") & (predicted == "FALLING")
    )
    return float(opposite.mean())


def _metrics(
    model_name: str,
    frame: pd.DataFrame,
    predictions: pd.Series,
    feature_columns: list[str],
) -> dict[str, object]:
    actual = frame["label"].astype(str)
    predicted = predictions.astype(str)
    precision, recall, f1, support = precision_recall_fscore_support(
        actual, predicted, labels=list(LABELS), zero_division=0
    )
    per_class = {
        label: {
            "precision": float(precision[index]),
            "recall": float(recall[index]),
            "f1": float(f1[index]),
            "support": int(support[index]),
        }
        for index, label in enumerate(LABELS)
    }
    return {
        "model": model_name,
        "feature_set": feature_columns,
        "macro_f1": float(
            f1_score(actual, predicted, labels=list(LABELS), average="macro", zero_division=0)
        ),
        "balanced_accuracy": float(balanced_accuracy_score(actual, predicted)),
        "opposite_direction_error_rate": _opposite_direction_error_rate(actual, predicted),
        "per_class": per_class,
    }


def _participant_metrics(
    model_name: str,
    frame: pd.DataFrame,
    predictions: pd.Series,
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    prediction_frame = frame[["participant_id", "label"]].copy()
    prediction_frame["prediction"] = predictions.to_numpy()
    for participant_id, group in prediction_frame.groupby("participant_id", sort=True):
        result.append(
            {
                "participant_id": str(participant_id),
                "model": model_name,
                "macro_f1": float(
                    f1_score(
                        group["label"],
                        group["prediction"],
                        labels=list(LABELS),
                        average="macro",
                        zero_division=0,
                    )
                ),
                "support": int(len(group)),
            }
        )
    return result


def _circular_shift_features(
    frame: pd.DataFrame,
    feature_columns: list[str],
    fraction: float,
) -> pd.DataFrame:
    if not 0 < fraction < 1:
        raise ValueError("Circular shift fraction must be between zero and one")
    shifted = frame.copy()
    for _, index in shifted.groupby(["participant_id", "split"], sort=True).groups.items():
        ordered_index = shifted.loc[index].sort_values("timestamp").index
        offset = max(1, round(len(ordered_index) * fraction))
        values = shifted.loc[ordered_index, feature_columns].to_numpy(copy=True)
        shifted.loc[ordered_index, feature_columns] = np.roll(values, shift=offset, axis=0)
    return shifted


def _bootstrap_mean_delta(
    left: pd.Series,
    right: pd.Series,
    *,
    repeats: int,
    seed: int,
) -> dict[str, float]:
    delta = left.to_numpy(dtype=float) - right.to_numpy(dtype=float)
    generator = np.random.default_rng(seed)
    draws = np.empty(repeats, dtype=float)
    for index in range(repeats):
        sample = generator.choice(delta, size=delta.size, replace=True)
        draws[index] = sample.mean()
    return {
        "mean_delta": float(delta.mean()),
        "ci_lower": float(np.quantile(draws, 0.025)),
        "ci_upper": float(np.quantile(draws, 0.975)),
    }


def _fit_predict(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    feature_columns: list[str],
    config: Mapping[str, Any],
) -> pd.Series:
    estimator = _pipeline(config)
    estimator.fit(train[feature_columns], train["label"].astype(str))
    return pd.Series(
        estimator.predict(validation[feature_columns]),
        index=validation.index,
        dtype="string",
    )


def evaluate_trend_baselines(
    features: pd.DataFrame,
    config: Mapping[str, Any],
) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame]:
    """Evaluate constants, aligned history, current-window, and shift control."""

    required = {
        "participant_id",
        "timestamp",
        "history_start",
        "split",
        "label",
    }
    missing = required.difference(features.columns)
    if missing:
        raise ValueError(f"Trend baseline features are missing columns: {sorted(missing)}")
    if "test" in set(features["split"].dropna().astype(str)):
        raise ValueError("Trend baseline evaluator refuses final-test rows")
    train = features[features["split"] == "train"].copy()
    validation = features[features["split"] == "validation"].copy()
    if train.empty or validation.empty:
        raise ValueError("Trend baseline evaluation requires train and validation rows")
    history_columns = _history_feature_columns()
    current_columns = _current_window_feature_columns()
    missing_features = set(history_columns).difference(features.columns)
    if missing_features:
        raise ValueError(
            "Trend baseline features are missing explicit columns: "
            f"{sorted(missing_features)}"
        )

    report_models: list[dict[str, object]] = []
    prediction_frames: list[pd.DataFrame] = []
    participant_rows: list[dict[str, object]] = []

    def record(model_name: str, predictions: pd.Series, feature_columns: list[str]) -> None:
        report_models.append(_metrics(model_name, validation, predictions, feature_columns))
        participant_rows.extend(_participant_metrics(model_name, validation, predictions))
        prediction_frames.append(
            validation[["participant_id", "timestamp", "history_start", "split", "label"]].assign(
                model=model_name, prediction=predictions.to_numpy()
            )
        )

    majority_prediction = pd.Series(
        _majority_label(train["label"].astype(str)), index=validation.index, dtype="string"
    )
    record("majority", majority_prediction, [])
    record(
        "always_stable",
        pd.Series("STABLE", index=validation.index, dtype="string"),
        [],
    )
    record(
        "logistic_history",
        _fit_predict(train, validation, history_columns, config),
        history_columns,
    )
    record(
        "logistic_current_window",
        _fit_predict(train, validation, current_columns, config),
        current_columns,
    )

    shift_fraction = float(config["control"]["circular_shift_fraction"])
    shifted = _circular_shift_features(features, history_columns, shift_fraction)
    shifted_train = shifted[shifted["split"] == "train"]
    shifted_validation = shifted[shifted["split"] == "validation"]
    record(
        "logistic_shifted_control",
        _fit_predict(shifted_train, shifted_validation, history_columns, config),
        history_columns,
    )

    participant_metrics = pd.DataFrame(participant_rows)
    metric_by_model = {str(row["model"]): row for row in report_models}
    constants: dict[str, float] = {}
    for name in ("majority", "always_stable"):
        macro_f1 = metric_by_model[name]["macro_f1"]
        assert isinstance(macro_f1, (float, int))
        constants[name] = float(macro_f1)
    best_constant = max(constants, key=constants.__getitem__)
    participant_pivot = participant_metrics.pivot(
        index="participant_id", columns="model", values="macro_f1"
    )
    evaluation = config["evaluation"]
    bootstrap = {
        "history_minus_best_constant": _bootstrap_mean_delta(
            participant_pivot["logistic_history"],
            participant_pivot[best_constant],
            repeats=int(evaluation["bootstrap_participant_repeats"]),
            seed=int(evaluation["bootstrap_seed"]),
        ),
        "history_minus_shifted_control": _bootstrap_mean_delta(
            participant_pivot["logistic_history"],
            participant_pivot["logistic_shifted_control"],
            repeats=int(evaluation["bootstrap_participant_repeats"]),
            seed=int(evaluation["bootstrap_seed"]) + 1,
        ),
        "history_minus_current_window": _bootstrap_mean_delta(
            participant_pivot["logistic_history"],
            participant_pivot["logistic_current_window"],
            repeats=int(evaluation["bootstrap_participant_repeats"]),
            seed=int(evaluation["bootstrap_seed"]) + 2,
        ),
    }
    history = metric_by_model["logistic_history"]
    per_class = history["per_class"]
    assert isinstance(per_class, dict)
    falling = per_class["FALLING"]
    rising = per_class["RISING"]
    assert isinstance(falling, dict) and isinstance(rising, dict)
    decision = "supported_for_classical_followup"
    if (
        bootstrap["history_minus_best_constant"]["ci_lower"] <= 0
        or bootstrap["history_minus_shifted_control"]["ci_lower"] <= 0
        or float(falling["recall"]) <= 0
        or float(rising["recall"]) <= 0
    ):
        decision = "not_supported_for_classical_followup"

    report: dict[str, object] = {
        "experiment_id": config["experiment"]["id"],
        "evidence_level": config["experiment"]["evidence_level"],
        "dataset": f"{config['dataset']['name']} v{config['dataset']['version']}",
        "protocol_version": config["label"]["version"],
        "split_version": config["split"]["version"],
        "feature_version": config["feature"]["version"],
        "final_test_accessed": False,
        "train_rows": int(len(train)),
        "validation_rows": int(len(validation)),
        "participant_count": int(features["participant_id"].nunique()),
        "feature_count": len(history_columns),
        "history_feature_columns": history_columns,
        "current_window_feature_columns": current_columns,
        "models": report_models,
        "paired_participant_bootstrap": bootstrap,
        "best_constant": best_constant,
        "decision": decision,
    }
    return report, pd.concat(prediction_frames, ignore_index=True), participant_metrics
