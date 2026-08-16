"""Participant-safe development-only evaluation for the State exploratory probe."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier, DummyRegressor  # type: ignore[import-untyped]
from sklearn.impute import SimpleImputer  # type: ignore[import-untyped]
from sklearn.linear_model import LogisticRegression, Ridge  # type: ignore[import-untyped]
from sklearn.metrics import (  # type: ignore[import-untyped]
    average_precision_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import (  # type: ignore[import-untyped]
    KFold,
    RepeatedStratifiedKFold,
    StratifiedKFold,
)
from sklearn.pipeline import Pipeline, make_pipeline  # type: ignore[import-untyped]
from sklearn.preprocessing import StandardScaler  # type: ignore[import-untyped]

from glycoband.features.state_exploratory import (
    add_candidate_state_labels,
    context_feature_columns,
    ppg_feature_columns,
)


def _json_number(value: float) -> float | None:
    return float(value) if np.isfinite(value) else None


def _candidate_folds(labels: pd.Series, seed: int, max_splits: int = 5) -> StratifiedKFold:
    counts = labels.value_counts()
    minimum = int(counts.min())
    n_splits = min(max_splits, minimum)
    if n_splits < 2:
        raise ValueError(
            "At least two examples per class are needed for grouped CV: "
            f"{counts.to_dict()}"
        )
    return StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)


def _classifier(name: str, seed: int) -> Any:
    if name == "dummy":
        estimator: Any = DummyClassifier(strategy="most_frequent")
    elif name == "logistic":
        estimator = LogisticRegression(max_iter=2000, random_state=seed)
    else:
        raise ValueError(f"Unsupported exploratory classifier: {name}")
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("model", estimator),
        ]
    )


def _classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    labels: list[str],
    y_score: np.ndarray | None = None,
) -> dict[str, Any]:
    report = classification_report(
        y_true,
        y_pred,
        labels=labels,
        output_dict=True,
        zero_division=0,
    )
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    total = int(matrix.sum())
    per_class: dict[str, Any] = {}
    pr_auc_values: list[float] = []
    for index, label in enumerate(labels):
        true_positive = int(matrix[index, index])
        false_negative = int(matrix[index, :].sum() - true_positive)
        false_positive = int(matrix[:, index].sum() - true_positive)
        true_negative = total - true_positive - false_negative - false_positive
        sensitivity = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else 0.0
        )
        specificity = (
            true_negative / (true_negative + false_positive)
            if true_negative + false_positive
            else 0.0
        )
        pr_auc: float | None = None
        if y_score is not None and y_score.shape[1] == len(labels):
            target = (y_true == label).astype(int)
            pr_auc = _json_number(float(average_precision_score(target, y_score[:, index])))
            if pr_auc is not None:
                pr_auc_values.append(pr_auc)
        per_class[label] = {
            "precision": _json_number(float(report[label]["precision"])),
            "recall": _json_number(float(report[label]["recall"])),
            "sensitivity": _json_number(float(sensitivity)),
            "specificity": _json_number(float(specificity)),
            "f1": _json_number(float(report[label]["f1-score"])),
            "pr_auc": pr_auc,
            "support": int(report[label]["support"]),
        }
    return {
        "macro_f1": _json_number(float(report["macro avg"]["f1-score"])),
        "balanced_accuracy": _json_number(float(balanced_accuracy_score(y_true, y_pred))),
        "macro_pr_auc": _json_number(float(np.mean(pr_auc_values))) if pr_auc_values else None,
        "per_class": per_class,
        "confusion_matrix": matrix.tolist(),
    }


def _aligned_probabilities(estimator: Any, x: pd.DataFrame, labels: list[str]) -> np.ndarray:
    """Return probability columns in the declared label order."""

    raw = np.asarray(estimator.predict_proba(x), dtype=float)
    model = estimator.named_steps["model"]
    classes = [str(value) for value in model.classes_]
    aligned = np.zeros((len(x), len(labels)), dtype=float)
    for index, label in enumerate(labels):
        if label in classes:
            aligned[:, index] = raw[:, classes.index(label)]
    return aligned


def _repeated_splits(
    y: np.ndarray,
    *,
    seed: int,
    n_splits: int = 5,
    n_repeats: int = 20,
) -> tuple[list[tuple[int, int, np.ndarray, np.ndarray]], int]:
    counts = pd.Series(y).value_counts()
    actual_splits = min(n_splits, int(counts.min()))
    if actual_splits < 2:
        raise ValueError(f"At least two examples per class are needed: {counts.to_dict()}")
    splitter = RepeatedStratifiedKFold(
        n_splits=actual_splits,
        n_repeats=n_repeats,
        random_state=seed,
    )
    placeholder = np.zeros((len(y), 1), dtype=float)
    result: list[tuple[int, int, np.ndarray, np.ndarray]] = []
    for split_index, (train_index, validation_index) in enumerate(splitter.split(placeholder, y)):
        repeat = split_index // actual_splits + 1
        fold = split_index % actual_splits + 1
        result.append((repeat, fold, train_index, validation_index))
    return result, actual_splits


def _summary(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"mean": None, "std": None, "q025": None, "q50": None, "q975": None}
    array = np.asarray(values, dtype=float)
    return {
        "mean": _json_number(float(np.mean(array))),
        "std": _json_number(float(np.std(array, ddof=1))) if len(array) > 1 else 0.0,
        "q025": _json_number(float(np.quantile(array, 0.025))),
        "q50": _json_number(float(np.quantile(array, 0.5))),
        "q975": _json_number(float(np.quantile(array, 0.975))),
    }


def _evaluate_model_on_splits(
    table: pd.DataFrame,
    y: np.ndarray,
    labels: list[str],
    feature_columns: list[str],
    splits: list[tuple[int, int, np.ndarray, np.ndarray]],
    *,
    model_name: str,
    seed: int,
    retain_folds: bool = True,
) -> dict[str, Any]:
    x = table[feature_columns].apply(pd.to_numeric, errors="coerce")
    fold_results: list[dict[str, Any]] = []
    all_true: list[str] = []
    all_pred: list[str] = []
    all_score: list[np.ndarray] = []
    for split_index, (repeat, fold, train_index, validation_index) in enumerate(splits):
        estimator = _classifier(model_name, seed + split_index)
        estimator.fit(x.iloc[train_index], y[train_index])
        predictions = estimator.predict(x.iloc[validation_index]).astype(str)
        probabilities = _aligned_probabilities(estimator, x.iloc[validation_index], labels)
        metrics = _classification_metrics(
            y[validation_index], predictions, labels, probabilities
        )
        metrics.update(
            {
                "repeat": repeat,
                "fold": fold,
                "validation_participants": int(len(validation_index)),
            }
        )
        if retain_folds:
            fold_results.append(metrics)
        all_true.extend(y[validation_index].tolist())
        all_pred.extend(predictions.tolist())
        all_score.append(probabilities)
    pooled = _classification_metrics(
        np.asarray(all_true),
        np.asarray(all_pred),
        labels,
        np.vstack(all_score),
    )
    result: dict[str, Any] = {
        "pooled": pooled,
        "folds": fold_results,
        "preprocessing_contract": {
            "imputation": "SimpleImputer(strategy=median)",
            "scaling": "StandardScaler",
            "feature_selection": "none",
            "fit_scope": "new Pipeline fit on each training fold only",
        },
    }
    if fold_results:
        result["fold_metric_summary"] = {
            metric: _summary(
                [float(fold[metric]) for fold in fold_results if fold[metric] is not None]
            )
            for metric in ("macro_f1", "balanced_accuracy", "macro_pr_auc")
        }
    return result


def evaluate_repeated_classifier(
    table: pd.DataFrame,
    label_column: str,
    feature_columns: list[str],
    *,
    seed: int = 20260817,
    n_splits: int = 5,
    n_repeats: int = 20,
    model_name: str = "logistic",
) -> dict[str, Any]:
    """Run repeated participant-safe CV with fold-local preprocessing."""

    if table["participant_id"].duplicated().any():
        raise ValueError("Exploratory evaluation requires one row per participant")
    labels = table[label_column].astype(str)
    class_labels = sorted(labels.unique().tolist())
    y = labels.to_numpy()
    splits, actual_splits = _repeated_splits(
        y, seed=seed, n_splits=n_splits, n_repeats=n_repeats
    )
    result = _evaluate_model_on_splits(
        table,
        y,
        class_labels,
        feature_columns,
        splits,
        model_name=model_name,
        seed=seed,
    )
    fold_metrics = result["folds"]
    result.update(
        {
            "label_column": label_column,
            "feature_columns": feature_columns,
            "class_support": {
                str(key): int(value) for key, value in labels.value_counts().items()
            },
            "participant_count": int(len(table)),
            "repeats": n_repeats,
            "splits_per_repeat": actual_splits,
            "fold_metric_summary": {
                metric: _summary(
                    [float(fold[metric]) for fold in fold_metrics if fold[metric] is not None]
                )
                for metric in ("macro_f1", "balanced_accuracy", "macro_pr_auc")
            },
        }
    )
    return result


def evaluate_paired_predictor_sets(
    table: pd.DataFrame,
    label_column: str,
    feature_sets: dict[str, list[str]],
    *,
    seed: int = 20260817,
    n_splits: int = 5,
    n_repeats: int = 20,
    model_name: str = "logistic",
) -> dict[str, Any]:
    """Evaluate feature sets on identical repeated folds and report paired deltas."""

    labels = table[label_column].astype(str)
    class_labels = sorted(labels.unique().tolist())
    y = labels.to_numpy()
    splits, actual_splits = _repeated_splits(
        y, seed=seed, n_splits=n_splits, n_repeats=n_repeats
    )
    results = {
        name: _evaluate_model_on_splits(
            table,
            y,
            class_labels,
            columns,
            splits,
            model_name=model_name,
            seed=seed,
        )
        for name, columns in feature_sets.items()
    }
    fold_by_set = {
        name: result["folds"] for name, result in results.items()
    }
    paired: dict[str, Any] = {}
    if "context_only" in fold_by_set and "ppg_plus_context" in fold_by_set:
        context_folds = fold_by_set["context_only"]
        combined_folds = fold_by_set["ppg_plus_context"]
        deltas = []
        for context, combined in zip(context_folds, combined_folds, strict=True):
            deltas.append(
                {
                    "repeat": context["repeat"],
                    "fold": context["fold"],
                    "macro_f1_delta": combined["macro_f1"] - context["macro_f1"],
                    "balanced_accuracy_delta": combined["balanced_accuracy"]
                    - context["balanced_accuracy"],
                    "macro_pr_auc_delta": combined["macro_pr_auc"] - context["macro_pr_auc"],
                }
            )
        paired["context_to_ppg_plus_context"] = {
            "direction": "ppg_plus_context minus context_only",
            "folds": deltas,
            "summary": {
                metric: _summary(
                    [float(item[metric]) for item in deltas if item[metric] is not None]
                )
                for metric in (
                    "macro_f1_delta",
                    "balanced_accuracy_delta",
                    "macro_pr_auc_delta",
                )
            },
            "positive_fold_fraction": {
                metric: float(
                    np.mean([float(item[metric]) > 0 for item in deltas])
                )
                for metric in (
                    "macro_f1_delta",
                    "balanced_accuracy_delta",
                    "macro_pr_auc_delta",
                )
            },
        }
    return {
        "label_column": label_column,
        "participant_count": int(len(table)),
        "repeats": n_repeats,
        "splits_per_repeat": actual_splits,
        "feature_sets": feature_sets,
        "models": results,
        "paired_deltas": paired,
    }


def evaluate_label_permutation_distribution(
    table: pd.DataFrame,
    label_column: str,
    feature_sets: dict[str, list[str]],
    *,
    seed: int = 20260817,
    n_permutations: int = 500,
    n_splits: int = 5,
    model_name: str = "logistic",
) -> dict[str, Any]:
    """Run participant-safe label permutations using one development CV repeat each."""

    if n_permutations < 500 or n_permutations > 1000:
        raise ValueError("Use 500-1000 label permutations for the decisive exploratory control")
    observed_labels = table[label_column].astype(str).to_numpy()
    class_labels = sorted(np.unique(observed_labels).tolist())
    rng = np.random.default_rng(seed)
    records: list[dict[str, Any]] = []
    for permutation_index in range(n_permutations):
        permuted = rng.permutation(observed_labels)
        splits, _ = _repeated_splits(
            permuted,
            seed=seed + permutation_index,
            n_splits=n_splits,
            n_repeats=1,
        )
        permutation_record: dict[str, Any] = {"permutation": permutation_index + 1}
        model_results: dict[str, Any] = {}
        for name, columns in feature_sets.items():
            result = _evaluate_model_on_splits(
                table,
                permuted,
                class_labels,
                columns,
                splits,
                model_name=model_name,
                seed=seed + permutation_index,
                retain_folds=False,
            )["pooled"]
            model_results[name] = result
            permutation_record[f"{name}_macro_f1"] = result["macro_f1"]
            permutation_record[f"{name}_balanced_accuracy"] = result["balanced_accuracy"]
            permutation_record[f"{name}_macro_pr_auc"] = result["macro_pr_auc"]
        if "context_only" in model_results and "ppg_plus_context" in model_results:
            for metric, key in (
                ("macro_f1", "macro_f1_delta"),
                ("balanced_accuracy", "balanced_accuracy_delta"),
                ("macro_pr_auc", "macro_pr_auc_delta"),
            ):
                permutation_record[key] = (
                    model_results["ppg_plus_context"][metric]
                    - model_results["context_only"][metric]
                )
        records.append(permutation_record)

    summaries = {
        key: _summary(
            [float(record[key]) for record in records if record[key] is not None]
        )
        for key in records[0]
        if key != "permutation"
    }
    return {
        "label_column": label_column,
        "participant_count": int(len(table)),
        "permutations": n_permutations,
        "splits_per_permutation": min(
            n_splits, int(pd.Series(observed_labels).value_counts().min())
        ),
        "model_name": model_name,
        "feature_sets": feature_sets,
        "summary": summaries,
        "records": records,
    }


def evaluate_classifier(
    table: pd.DataFrame,
    label_column: str,
    feature_columns: list[str],
    *,
    seed: int = 20260817,
    model_names: tuple[str, ...] = ("dummy", "logistic"),
) -> dict[str, Any]:
    """Evaluate simple models with participant-level (one-row-per-person) CV."""

    if table["participant_id"].duplicated().any():
        raise ValueError("Exploratory evaluation requires one row per participant")
    labels = table[label_column].astype(str)
    class_labels = sorted(labels.unique().tolist())
    splitter = _candidate_folds(labels, seed)
    x = table[feature_columns].apply(pd.to_numeric, errors="coerce")
    y = labels.to_numpy()
    model_results: dict[str, Any] = {}
    for model_name in model_names:
        fold_results: list[dict[str, Any]] = []
        all_true: list[str] = []
        all_pred: list[str] = []
        for fold, (train_index, validation_index) in enumerate(splitter.split(x, y), start=1):
            estimator = _classifier(model_name, seed)
            estimator.fit(x.iloc[train_index], y[train_index])
            predictions = estimator.predict(x.iloc[validation_index]).astype(str)
            metrics = _classification_metrics(y[validation_index], predictions, class_labels)
            metrics["fold"] = fold
            metrics["validation_participants"] = int(len(validation_index))
            fold_results.append(metrics)
            all_true.extend(y[validation_index].tolist())
            all_pred.extend(predictions.tolist())
        pooled = _classification_metrics(np.asarray(all_true), np.asarray(all_pred), class_labels)
        model_results[model_name] = {"pooled": pooled, "folds": fold_results}
    return {
        "label_column": label_column,
        "feature_columns": feature_columns,
        "class_support": {str(key): int(value) for key, value in labels.value_counts().items()},
        "participant_count": int(len(table)),
        "models": model_results,
    }


def evaluate_permutation_control(
    table: pd.DataFrame,
    label_column: str,
    feature_columns: list[str],
    *,
    seed: int = 20260817,
) -> dict[str, Any]:
    """Run one deterministic participant-level label permutation with Logistic Regression."""

    labels = table[label_column].astype(str).to_numpy()
    permutation = np.random.default_rng(seed).permutation(labels)
    permuted = table.copy()
    permuted["_permuted_label"] = permutation
    result = evaluate_classifier(
        permuted,
        "_permuted_label",
        feature_columns,
        seed=seed,
        model_names=("logistic",),
    )
    result["control"] = "participant-level label permutation"
    result["seed"] = seed
    return result


def evaluate_regression(
    table: pd.DataFrame,
    feature_columns: list[str],
    *,
    seed: int = 20260817,
) -> dict[str, Any]:
    """Run a lightweight continuous sanity check; this is not the primary State task."""

    x = table[feature_columns].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(table["candidate_d_continuous"], errors="raise").to_numpy(dtype=float)
    splitter = KFold(n_splits=min(5, len(table)), shuffle=True, random_state=seed)
    models: dict[str, Any] = {
        "dummy": DummyRegressor(strategy="mean"),
        "ridge": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge()),
    }
    results: dict[str, Any] = {}
    for name, model in models.items():
        true_values: list[float] = []
        predictions: list[float] = []
        for train_index, validation_index in splitter.split(x):
            model.fit(x.iloc[train_index], y[train_index])
            predictions.extend(float(value) for value in model.predict(x.iloc[validation_index]))
            true_values.extend(float(value) for value in y[validation_index])
        true = np.asarray(true_values)
        pred = np.asarray(predictions)
        results[name] = {
            "mae_mmol_l": _json_number(float(mean_absolute_error(true, pred))),
            "rmse_mmol_l": _json_number(float(np.sqrt(mean_squared_error(true, pred)))),
            "r2": _json_number(float(r2_score(true, pred))),
        }
    return {
        "feature_columns": feature_columns,
        "participant_count": int(len(table)),
        "models": results,
    }


def run_state_exploratory_analysis(table: pd.DataFrame, *, seed: int = 20260817) -> dict[str, Any]:
    """Compare documented candidate State formulations and predictor sets."""

    labeled = add_candidate_state_labels(table)
    ppg = ppg_feature_columns(labeled)
    context = context_feature_columns(labeled)
    combined = ppg + context
    candidates = {
        "candidate_a_binary": "binary 5.6 mmol/L boundary",
        "candidate_b_ada_3class": "ADA-inspired three-range formulation",
        "candidate_c_who_3class": "WHO-inspired three-range formulation",
    }
    results: dict[str, Any] = {
        "seed": seed,
        "participant_count": int(len(labeled)),
        "candidates": {},
        "continuous_sanity_check": evaluate_regression(labeled, ppg, seed=seed),
    }
    for label_column, rationale in candidates.items():
        candidate = {
            "scientific_rationale": rationale,
            "development_support": {
                str(key): int(value) for key, value in labeled[label_column].value_counts().items()
            },
            "ppg_only": evaluate_classifier(labeled, label_column, ppg, seed=seed),
            "context_only": evaluate_classifier(labeled, label_column, context, seed=seed),
            "ppg_plus_context": evaluate_classifier(labeled, label_column, combined, seed=seed),
            "permutation_control": evaluate_permutation_control(
                labeled, label_column, ppg, seed=seed
            )
            if label_column == "candidate_a_binary"
            else None,
        }
        results["candidates"][label_column] = candidate
    return results
