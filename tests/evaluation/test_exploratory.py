from __future__ import annotations

import numpy as np
import pandas as pd

from glycoband.evaluation.exploratory import (
    _classifier,
    evaluate_classifier,
    evaluate_label_permutation_distribution,
    evaluate_paired_predictor_sets,
    evaluate_permutation_control,
    evaluate_repeated_classifier,
    run_state_exploratory_analysis,
)


def _table() -> pd.DataFrame:
    rng = np.random.default_rng(3)
    glucose = np.array([4.5] * 15 + [6.2] * 15)
    values = rng.normal(size=(30, 3))
    return pd.DataFrame(
        {
            "participant_id": np.arange(30),
            "glucose_reference": glucose,
            "age": rng.normal(40, 5, size=30),
            "sex_code": rng.integers(0, 2, size=30),
            "bmi": rng.normal(24, 2, size=30),
            "ppg_feature_a": values[:, 0],
            "ppg_feature_b": values[:, 1],
            "cross_corr_660nm_730nm": values[:, 2],
        }
    )


def test_evaluate_classifier_reports_fold_and_pooled_metrics() -> None:
    table = _table()
    table["label"] = np.where(table["glucose_reference"] < 5.6, "NORMAL", "ELEVATED")
    result = evaluate_classifier(table, "label", ["ppg_feature_a", "ppg_feature_b"], seed=4)
    assert result["participant_count"] == 30
    assert set(result["models"]) == {"dummy", "logistic"}
    assert len(result["models"]["logistic"]["folds"]) == 5
    assert "macro_f1" in result["models"]["logistic"]["pooled"]


def test_permutation_control_is_explicit() -> None:
    table = _table()
    table["label"] = np.where(table["glucose_reference"] < 5.6, "NORMAL", "ELEVATED")
    result = evaluate_permutation_control(table, "label", ["ppg_feature_a"], seed=4)
    assert result["control"] == "participant-level label permutation"


def test_state_analysis_keeps_candidates_separate() -> None:
    result = run_state_exploratory_analysis(_table(), seed=4)
    assert set(result["candidates"]) == {
        "candidate_a_binary",
        "candidate_b_ada_3class",
        "candidate_c_who_3class",
    }
    assert "continuous_sanity_check" in result


def test_repeated_cv_reports_pr_auc_and_fold_local_pipeline() -> None:
    table = _table()
    table["label"] = np.where(table["glucose_reference"] < 5.6, "NORMAL", "ELEVATED")
    result = evaluate_repeated_classifier(
        table,
        "label",
        ["ppg_feature_a", "ppg_feature_b"],
        seed=4,
        n_repeats=2,
    )
    assert result["repeats"] == 2
    assert len(result["folds"]) == 10
    assert "macro_pr_auc" in result["pooled"]
    assert "sensitivity" in result["folds"][0]["per_class"]["NORMAL"]
    assert "specificity" in result["folds"][0]["per_class"]["NORMAL"]
    assert result["preprocessing_contract"]["fit_scope"] == (
        "new Pipeline fit on each training fold only"
    )
    pipeline = _classifier("logistic", seed=4)
    assert list(pipeline.named_steps) == ["imputer", "scaler", "model"]


def test_paired_context_delta_uses_identical_folds() -> None:
    table = _table()
    table["label"] = np.where(table["glucose_reference"] < 5.6, "NORMAL", "ELEVATED")
    result = evaluate_paired_predictor_sets(
        table,
        "label",
        {
            "context_only": ["age", "sex_code", "bmi"],
            "ppg_plus_context": [
                "age",
                "sex_code",
                "bmi",
                "ppg_feature_a",
                "ppg_feature_b",
            ],
        },
        seed=4,
        n_repeats=2,
    )
    deltas = result["paired_deltas"]["context_to_ppg_plus_context"]
    assert len(deltas["folds"]) == 10
    assert deltas["direction"] == "ppg_plus_context minus context_only"


def test_permutation_distribution_requires_decisive_count_and_records_null() -> None:
    table = _table()
    table["label"] = np.where(table["glucose_reference"] < 5.6, "NORMAL", "ELEVATED")
    result = evaluate_label_permutation_distribution(
        table,
        "label",
        {
            "context_only": ["age", "sex_code", "bmi"],
            "ppg_plus_context": ["age", "sex_code", "bmi", "ppg_feature_a"],
        },
        seed=4,
        n_permutations=500,
    )
    assert result["permutations"] == 500
    assert len(result["records"]) == 500
    assert "ppg_plus_context_macro_f1" in result["summary"]
    assert "macro_f1_delta" in result["summary"]
