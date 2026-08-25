"""Development-only evaluation helpers for Trend conditioning probes."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer  # type: ignore[import-untyped]
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
from sklearn.metrics import (  # type: ignore[import-untyped]
    balanced_accuracy_score,
    f1_score,
    recall_score,
)
from sklearn.pipeline import make_pipeline  # type: ignore[import-untyped]
from sklearn.preprocessing import StandardScaler  # type: ignore[import-untyped]

from glycoband.evaluation.trend_diagnostics import (
    CLASS_ORDER,
    DEVELOPMENT_SPLITS,
    IDENTITY_COLUMNS,
)


def validate_probe_frame(frame: pd.DataFrame, *, name: str = "probe frame") -> None:
    """Reject final-test rows and duplicate endpoint identities."""

    required = set(IDENTITY_COLUMNS) | {"split", "label"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"{name} is missing columns: {sorted(missing)}")
    forbidden = set(frame["split"].astype(str)).difference(DEVELOPMENT_SPLITS)
    if forbidden:
        raise ValueError(f"{name} contains final-test or forbidden splits: {sorted(forbidden)}")
    if frame.duplicated(list(IDENTITY_COLUMNS)).any():
        raise ValueError(f"{name} contains duplicate endpoint identity keys")


def inner_chronological_folds(
    frame: pd.DataFrame, folds: int, embargo_minutes: int
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Create participant-aware train-before-assessment folds with raw-history gaps."""

    validate_probe_frame(frame, name="inner-fold frame")
    if set(frame["split"].astype(str)) != {"train"}:
        raise ValueError("Inner chronological folds require train rows only")
    if folds < 2 or embargo_minutes < 0:
        raise ValueError("folds must be >= 2 and embargo_minutes must be non-negative")
    timestamps = pd.to_datetime(frame["timestamp"])
    folds_out: list[tuple[np.ndarray, np.ndarray]] = []
    for fold_number in range(1, folds + 1):
        train_indices: list[int] = []
        assessment_indices: list[int] = []
        for _, group in frame.assign(_timestamp=timestamps).groupby("participant_id", sort=True):
            ordered = group.sort_values("_timestamp", kind="mergesort")
            count = len(ordered)
            assessment_start = max(1, int(np.floor(count * fold_number / (folds + 1))))
            assessment_end = max(
                assessment_start + 1,
                int(np.floor(count * (fold_number + 1) / (folds + 1))),
            )
            assessment_end = min(assessment_end, count)
            assessment = ordered.iloc[assessment_start:assessment_end]
            if assessment.empty:
                continue
            cutoff = pd.Timestamp(assessment["history_start"].min())
            if embargo_minutes < 0:
                raise ValueError("embargo_minutes must be non-negative")
            train = ordered[ordered["_timestamp"] < cutoff]
            if train.empty:
                continue
            train_indices.extend(train.index.to_list())
            assessment_indices.extend(assessment.index.to_list())
        if not train_indices or not assessment_indices:
            continue
        train_index = np.asarray(sorted(set(train_indices)), dtype=int)
        assessment_index = np.asarray(sorted(set(assessment_indices)), dtype=int)
        if np.intersect1d(train_index, assessment_index).size:
            raise AssertionError("Inner chronological fold has overlapping endpoint identities")
        folds_out.append((train_index, assessment_index))
    if not folds_out:
        raise ValueError("No valid chronological inner folds could be constructed")
    return folds_out


def _feature_columns(frame: pd.DataFrame) -> list[str]:
    excluded = {
        "slope_mg_dl_min",
        "quality_weight",
        "quality_retained",
    }
    columns = [
        column
        for column in frame.columns
        if column not in excluded
        and (
            column.startswith("history_")
            or column.startswith("feature_")
            or column.startswith("quality_")
        )
        and pd.api.types.is_numeric_dtype(frame[column])
    ]
    if not columns:
        raise ValueError("No numeric model feature columns found")
    return columns


def _fit_predict(
    train: pd.DataFrame,
    assessment: pd.DataFrame,
    *,
    sample_weight: np.ndarray | None = None,
) -> np.ndarray:
    columns = _feature_columns(train)
    model = make_pipeline(
        SimpleImputer(strategy="median"),
        StandardScaler(),
        LogisticRegression(max_iter=1000, random_state=20260825),
    )
    model.fit(train[columns], train["label"], logisticregression__sample_weight=sample_weight)
    return np.asarray(model.predict(assessment[columns]))


def evaluate_variant(
    frame: pd.DataFrame,
    *,
    variant: str,
    policy: str = "report_only",
    train_sample_weight: np.ndarray | None = None,
) -> tuple[dict[str, object], pd.DataFrame]:
    """Fit one LR variant on train and score unweighted validation rows."""

    validate_probe_frame(frame)
    train = frame[frame["split"] == "train"].copy()
    validation = frame[frame["split"] == "validation"].copy()
    if policy == "hard_exclude_bottom_train_decile" and "quality_retained" in validation:
        validation = validation[validation["quality_retained"].astype(bool)]
    if policy == "hard_exclude_bottom_train_decile" and "quality_retained" in train:
        train = train[train["quality_retained"].astype(bool)]
    if train.empty or validation.empty:
        raise ValueError(f"Variant {variant} has no train or validation rows after policy")
    if train_sample_weight is not None and len(train_sample_weight) != len(train):
        raise ValueError("Training sample weights do not match retained train rows")
    predictions = _fit_predict(train, validation, sample_weight=train_sample_weight)
    labels = validation["label"].astype(str).to_numpy()
    prediction_frame = validation[list(IDENTITY_COLUMNS) + ["label"]].copy()
    prediction_frame["prediction"] = predictions
    prediction_frame["variant"] = variant
    prediction_frame["quality_policy"] = policy
    report: dict[str, object] = {
        "variant": variant,
        "quality_policy": policy,
        "train_rows": int(len(train)),
        "validation_rows": int(len(validation)),
        "validation_retention": float(
            len(validation) / max(len(frame[frame["split"] == "validation"]), 1)
        ),
        "macro_f1": float(
            f1_score(
                labels,
                predictions,
                labels=list(CLASS_ORDER),
                average="macro",
                zero_division=0,
            )
        ),
        "balanced_accuracy": float(balanced_accuracy_score(labels, predictions)),
        "falling_recall": float(
            recall_score(
                labels, predictions, labels=["FALLING"], average="macro", zero_division=0
            )
        ),
        "rising_recall": float(
            recall_score(
                labels, predictions, labels=["RISING"], average="macro", zero_division=0
            )
        ),
        "validation_weighted": False,
    }
    return report, prediction_frame


def cross_validated_macro_f1(
    frame: pd.DataFrame, *, folds: int = 3, embargo_minutes: int = 30
) -> float:
    """Score a representation only on train-segment chronological folds."""

    train = frame[frame["split"] == "train"].copy()
    fold_scores: list[float] = []
    for train_index, assessment_index in inner_chronological_folds(train, folds, embargo_minutes):
        fit = train.loc[train_index]
        assessment = train.loc[assessment_index]
        prediction = _fit_predict(fit, assessment)
        fold_scores.append(
            float(
                f1_score(
                    assessment["label"],
                    prediction,
                    labels=list(CLASS_ORDER),
                    average="macro",
                    zero_division=0,
                )
            )
        )
    return float(np.mean(fold_scores)) if fold_scores else float("nan")


def evaluate_conditioning_variants(
    frame: pd.DataFrame, config: dict[str, object]
) -> dict[str, object]:
    """Small deterministic evaluator used by runner tests and development probes."""

    validate_probe_frame(frame)
    variants = [
        "raw_anchor",
        "bp_0p5_8_zscore",
        "bp_0p7_4_robust",
    ]
    reports: dict[str, dict[str, object]] = {}
    predictions: list[pd.DataFrame] = []
    for variant in variants:
        for policy in ("report_only", "soft_weight", "hard_exclude_bottom_train_decile"):
            variant_frame = frame.copy()
            if "quality_retained" not in variant_frame.columns:
                variant_frame["quality_retained"] = True
            report, prediction = evaluate_variant(
                variant_frame,
                variant=variant,
                policy=policy,
            )
            if policy == "hard_exclude_bottom_train_decile":
                retained = prediction["label"].index
                report["common_endpoint_macro_f1"] = report["macro_f1"]
                report["common_endpoint_rows"] = int(len(retained))
            reports[f"{variant}__{policy}"] = report
            predictions.append(prediction)
    experiment = config.get("experiment")
    config_id = str(experiment.get("id", "unknown")) if isinstance(experiment, dict) else "unknown"
    return {
        "validation_weighted": False,
        "variants": reports,
        "predictions": pd.concat(predictions, ignore_index=True),
        "config_id": config_id,
    }
