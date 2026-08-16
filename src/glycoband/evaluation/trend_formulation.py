"""Descriptive selection helpers for the BIG IDEAs Trend protocol grid.

These functions intentionally stop at protocol comparison.  They do not create a
chronological split, fit a model, or access a reserved test set.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

PROTOCOL_COLUMNS = [
    "history_minutes",
    "threshold_mg_dl_min",
    "smoothing",
    "slope_method",
]
CLASS_COLUMNS = ["falling", "stable", "rising"]

SHORTLIST = (
    {
        "candidate_id": "primary_h30_tau0p5_median3_ols",
        "history_minutes": 30,
        "threshold_mg_dl_min": 0.5,
        "smoothing": "median3",
        "slope_method": "ols",
        "role": "primary",
        "rationale": "Best balance of causal history, class support, and auditable slope.",
    },
    {
        "candidate_id": "short_h15_tau0p5_median3_ols",
        "history_minutes": 15,
        "threshold_mg_dl_min": 0.5,
        "smoothing": "median3",
        "slope_method": "ols",
        "role": "history sensitivity",
        "rationale": "Tests whether a shorter recent window improves temporal responsiveness.",
    },
    {
        "candidate_id": "long_h60_tau0p5_median3_ols",
        "history_minutes": 60,
        "threshold_mg_dl_min": 0.5,
        "smoothing": "median3",
        "slope_method": "ols",
        "role": "history sensitivity",
        "rationale": "Tests whether a longer window produces a more stable physiological trend.",
    },
    {
        "candidate_id": "conservative_h30_tau1p0_median3_ols",
        "history_minutes": 30,
        "threshold_mg_dl_min": 1.0,
        "smoothing": "median3",
        "slope_method": "ols",
        "role": "threshold sensitivity",
        "rationale": "Tests a conservative direction margin without the severe class loss at 1.5.",
    },
    {
        "candidate_id": "robust_h30_tau0p5_median3_theil_sen",
        "history_minutes": 30,
        "threshold_mg_dl_min": 0.5,
        "smoothing": "median3",
        "slope_method": "theil_sen",
        "role": "estimator sensitivity",
        "rationale": (
            "Tests resistance to isolated CGM excursions while retaining the same window "
            "and margin."
        ),
    },
)


def _check_columns(candidates: pd.DataFrame) -> None:
    required = set(PROTOCOL_COLUMNS + ["participant_id"] + CLASS_COLUMNS + ["eligible_endpoints"])
    missing = required.difference(candidates.columns)
    if missing:
        raise ValueError(f"Candidate audit is missing columns: {sorted(missing)}")


def _protocol_mask(frame: pd.DataFrame, protocol: dict[str, object]) -> pd.Series:
    mask = pd.Series(True, index=frame.index)
    for column in PROTOCOL_COLUMNS:
        mask &= frame[column].eq(protocol[column])
    return mask


def candidate_metrics(
    candidates: pd.DataFrame, shortlist: Sequence[dict[str, object]] = SHORTLIST
) -> pd.DataFrame:
    """Return aggregate and participant-composition metrics for selected protocols."""

    _check_columns(candidates)
    rows: list[dict[str, object]] = []
    for protocol in shortlist:
        selected = candidates.loc[_protocol_mask(candidates, protocol)].copy()
        if selected.empty:
            raise ValueError(f"Protocol not found in candidate audit: {protocol}")
        selected["total"] = selected[CLASS_COLUMNS].sum(axis=1)
        if (selected["total"] <= 0).any():
            raise ValueError("Candidate audit contains a participant with no eligible labels")
        for column in CLASS_COLUMNS:
            selected[f"{column}_fraction"] = selected[column] / selected["total"]
        participant_fraction_sd = selected[[f"{c}_fraction" for c in CLASS_COLUMNS]].std().mean()
        baseline = candidates.loc[
            _protocol_mask(
                candidates,
                {
                    "history_minutes": 30,
                    "threshold_mg_dl_min": 0.5,
                    "smoothing": "median3",
                    "slope_method": "ols",
                },
            )
        ].set_index("participant_id")
        current = selected.set_index("participant_id")
        baseline["total"] = baseline[CLASS_COLUMNS].sum(axis=1)
        for column in CLASS_COLUMNS:
            baseline[f"{column}_fraction"] = baseline[column] / baseline["total"]
        shared = baseline.index.intersection(current.index)
        total_variation = (
            baseline.loc[shared, [f"{c}_fraction" for c in CLASS_COLUMNS]].to_numpy()
            - current.loc[shared, [f"{c}_fraction" for c in CLASS_COLUMNS]].to_numpy()
        )
        tv_mean = float(abs(total_variation).sum(axis=1).mean() / 2)
        tv_max = float(abs(total_variation).sum(axis=1).max() / 2)
        total = int(selected["total"].sum())
        counts = {column: int(selected[column].sum()) for column in CLASS_COLUMNS}
        fractions = {f"{column}_fraction": counts[column] / total for column in CLASS_COLUMNS}
        rows.append(
            {
                **{key: protocol[key] for key in PROTOCOL_COLUMNS},
                "candidate_id": protocol["candidate_id"],
                "role": protocol["role"],
                "rationale": protocol["rationale"],
                "participants": int(selected["participant_id"].nunique()),
                "eligible_endpoints": int(selected["eligible_endpoints"].sum()),
                **counts,
                **fractions,
                "minority_fraction": min(
                    fractions["falling_fraction"], fractions["rising_fraction"]
                ),
                "participant_support_falling": int((selected["falling"] > 0).sum()),
                "participant_support_stable": int((selected["stable"] > 0).sum()),
                "participant_support_rising": int((selected["rising"] > 0).sum()),
                "mean_participant_class_fraction_sd": float(participant_fraction_sd),
                "min_participant_falling_fraction": float(selected["falling_fraction"].min()),
                "min_participant_rising_fraction": float(selected["rising_fraction"].min()),
                "composition_tv_vs_primary_mean": tv_mean,
                "composition_tv_vs_primary_max": tv_max,
            }
        )
    return pd.DataFrame(rows)


def participant_compositions(
    candidates: pd.DataFrame, shortlist: Sequence[dict[str, object]] = SHORTLIST
) -> pd.DataFrame:
    """Return one row per participant and selected protocol with class fractions."""

    _check_columns(candidates)
    frames: list[pd.DataFrame] = []
    for protocol in shortlist:
        selected = candidates.loc[_protocol_mask(candidates, protocol)].copy()
        selected["candidate_id"] = protocol["candidate_id"]
        selected["total"] = selected[CLASS_COLUMNS].sum(axis=1)
        for column in CLASS_COLUMNS:
            selected[f"{column}_fraction"] = selected[column] / selected["total"]
        frames.append(
            selected[["participant_id", "candidate_id"] + [f"{c}_fraction" for c in CLASS_COLUMNS]]
        )
    return pd.concat(frames, ignore_index=True)
