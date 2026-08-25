from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

from glycoband.evaluation.trend_exploratory import (
    evaluate_conditioning_variants,
    inner_chronological_folds,
)

_FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures/trend_probe.py"
_SPEC = importlib.util.spec_from_file_location("trend_probe_fixture", _FIXTURE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
development_probe_frames = _MODULE.development_probe_frames


def _long_train_frame() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for participant_id in ("001", "002", "003"):
        for index in range(30):
            timestamp = pd.Timestamp("2020-01-01") + pd.Timedelta(minutes=5 * index)
            rows.append(
                {
                    "participant_id": participant_id,
                    "timestamp": timestamp,
                    "history_start": timestamp - pd.Timedelta(minutes=30),
                    "split": "train",
                    "label": ("FALLING", "STABLE", "RISING")[index % 3],
                    "feature_00": float(index),
                    "feature_01": float(index % 5),
                }
            )
    return pd.DataFrame(rows)


def test_inner_folds_are_chronological_and_history_disjoint() -> None:
    frame = _long_train_frame()
    folds = inner_chronological_folds(frame, 3, 30)

    assert folds
    for train_index, assessment_index in folds:
        train = frame.loc[train_index]
        assessment = frame.loc[assessment_index]
        for participant_id in assessment["participant_id"].unique():
            left = train[train["participant_id"] == participant_id]
            right = assessment[assessment["participant_id"] == participant_id]
            assert left["timestamp"].max() < right["history_start"].min()


def test_conditioning_report_marks_validation_as_unweighted() -> None:
    endpoints, features = development_probe_frames()
    frame = features.merge(
        endpoints[["participant_id", "timestamp", "label"]],
        on=["participant_id", "timestamp", "label"],
        validate="one_to_one",
    )
    report = evaluate_conditioning_variants(frame, {"experiment": {"id": "test"}})

    assert report["validation_weighted"] is False
    hard = report["variants"]["bp_0p7_4_robust__hard_exclude_bottom_train_decile"]
    assert 0.0 <= hard["validation_retention"] <= 1.0
    assert "common_endpoint_macro_f1" in hard
