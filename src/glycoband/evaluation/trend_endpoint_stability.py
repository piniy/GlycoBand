"""Exact endpoint-level stability metrics for exploratory Trend formulations."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

KEY_COLUMNS = ("participant_id", "timestamp")
LABEL_ORDER = ("FALLING", "STABLE", "RISING")
REQUIRED_COLUMNS = {
    *KEY_COLUMNS,
    "candidate_id",
    "history_start",
    "slope_mg_dl_min",
    "threshold_mg_dl_min",
    "label",
}


def _validate_endpoint_labels(endpoint_labels: pd.DataFrame, primary_candidate_id: str) -> None:
    missing = REQUIRED_COLUMNS.difference(endpoint_labels.columns)
    if missing:
        raise ValueError(f"Endpoint labels are missing columns: {sorted(missing)}")
    if endpoint_labels.empty:
        raise ValueError("Endpoint labels must not be empty")
    if primary_candidate_id not in set(endpoint_labels["candidate_id"]):
        raise ValueError(f"Primary candidate {primary_candidate_id!r} is absent")
    duplicate = endpoint_labels.duplicated(["candidate_id", *KEY_COLUMNS])
    if duplicate.any():
        raise ValueError("Endpoint labels contain duplicate candidate endpoint keys")
    labels = set(endpoint_labels["label"])
    unsupported = labels.difference(LABEL_ORDER)
    if unsupported:
        raise ValueError(f"Endpoint labels contain unsupported classes: {sorted(unsupported)}")
    if endpoint_labels["timestamp"].isna().any() or endpoint_labels["history_start"].isna().any():
        raise ValueError("Endpoint labels contain missing timestamps")
    if (endpoint_labels["history_start"] > endpoint_labels["timestamp"]).any():
        raise ValueError("Endpoint label history starts after its endpoint")
    if endpoint_labels["threshold_mg_dl_min"].le(0).any():
        raise ValueError("Trend thresholds must be positive")


def _quantiles(values: Iterable[float]) -> dict[str, float]:
    array = np.asarray(list(values), dtype=float)
    if array.size == 0:
        return {"q10": float("nan"), "q50": float("nan"), "q90": float("nan")}
    return {
        "q10": float(np.quantile(array, 0.1)),
        "q50": float(np.quantile(array, 0.5)),
        "q90": float(np.quantile(array, 0.9)),
    }


def _cohen_kappa(primary: pd.Series, candidate: pd.Series) -> float:
    if primary.empty:
        return float("nan")
    observed = float((primary == candidate).mean())
    expected = sum(
        float((primary == label).mean()) * float((candidate == label).mean())
        for label in LABEL_ORDER
    )
    denominator = 1 - expected
    return float("nan") if denominator == 0 else (observed - expected) / denominator


def _pair_metrics(
    primary: pd.DataFrame,
    candidate: pd.DataFrame,
    *,
    primary_candidate_id: str,
    candidate_id: str,
    participant_id: str | None,
) -> dict[str, object]:
    shared = primary.merge(
        candidate,
        on=list(KEY_COLUMNS),
        how="inner",
        suffixes=("_primary", "_candidate"),
        validate="one_to_one",
    )
    primary_endpoints = len(primary)
    candidate_endpoints = len(candidate)
    shared_endpoints = len(shared)
    union_endpoints = primary_endpoints + candidate_endpoints - shared_endpoints
    primary_retention = shared_endpoints / primary_endpoints if primary_endpoints else float("nan")
    candidate_retention = (
        shared_endpoints / candidate_endpoints if candidate_endpoints else float("nan")
    )
    agreement = (
        float((shared["label_primary"] == shared["label_candidate"]).mean())
        if shared_endpoints
        else float("nan")
    )
    margins = np.abs(
        np.abs(shared["slope_mg_dl_min_primary"].to_numpy(dtype=float))
        - shared["threshold_mg_dl_min_primary"].to_numpy(dtype=float)
    )
    agreed = shared["label_primary"] == shared["label_candidate"]
    agreement_margins = _quantiles(margins[agreed.to_numpy()])
    disagreement_margins = _quantiles(margins[(~agreed).to_numpy()])
    return {
        "primary_candidate_id": primary_candidate_id,
        "candidate_id": candidate_id,
        "participant_id": participant_id,
        "primary_endpoints": primary_endpoints,
        "candidate_endpoints": candidate_endpoints,
        "shared_endpoints": shared_endpoints,
        "union_endpoints": union_endpoints,
        "primary_shared_retention": primary_retention,
        "candidate_shared_retention": candidate_retention,
        "endpoint_jaccard": shared_endpoints / union_endpoints if union_endpoints else float("nan"),
        "exact_label_agreement": agreement,
        "cohen_kappa": _cohen_kappa(shared["label_primary"], shared["label_candidate"]),
        "agreement_count": int(agreed.sum()),
        "disagreement_count": int((~agreed).sum()),
        "primary_margin_agreement_q10": agreement_margins["q10"],
        "primary_margin_agreement_q50": agreement_margins["q50"],
        "primary_margin_agreement_q90": agreement_margins["q90"],
        "primary_margin_disagreement_q10": disagreement_margins["q10"],
        "primary_margin_disagreement_q50": disagreement_margins["q50"],
        "primary_margin_disagreement_q90": disagreement_margins["q90"],
    }


def _label_transitions(
    primary: pd.DataFrame, candidate: pd.DataFrame, candidate_id: str
) -> pd.DataFrame:
    shared = primary.merge(
        candidate,
        on=list(KEY_COLUMNS),
        how="inner",
        suffixes=("_primary", "_candidate"),
        validate="one_to_one",
    )
    counts = (
        shared.groupby(["label_primary", "label_candidate"], observed=False)
        .size()
        .reindex(
            pd.MultiIndex.from_product(
                [LABEL_ORDER, LABEL_ORDER], names=["primary_label", "candidate_label"]
            ),
            fill_value=0,
        )
        .rename("count")
        .reset_index()
    )
    counts.insert(0, "candidate_id", candidate_id)
    return counts


def compare_to_primary(
    endpoint_labels: pd.DataFrame, primary_candidate_id: str
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Compare each formulation with a working primary by exact endpoint identity."""

    _validate_endpoint_labels(endpoint_labels, primary_candidate_id)
    primary = endpoint_labels.loc[
        endpoint_labels["candidate_id"] == primary_candidate_id
    ].copy()
    candidate_ids = list(endpoint_labels["candidate_id"].drop_duplicates())
    participants = sorted(str(value) for value in endpoint_labels["participant_id"].unique())
    pooled_rows: list[dict[str, object]] = []
    participant_rows: list[dict[str, object]] = []
    transition_frames: list[pd.DataFrame] = []
    for candidate_id in candidate_ids:
        candidate = endpoint_labels.loc[endpoint_labels["candidate_id"] == candidate_id].copy()
        pooled_rows.append(
            _pair_metrics(
                primary,
                candidate,
                primary_candidate_id=primary_candidate_id,
                candidate_id=str(candidate_id),
                participant_id=None,
            )
        )
        for participant_id in participants:
            participant_rows.append(
                _pair_metrics(
                    primary.loc[primary["participant_id"] == participant_id],
                    candidate.loc[candidate["participant_id"] == participant_id],
                    primary_candidate_id=primary_candidate_id,
                    candidate_id=str(candidate_id),
                    participant_id=participant_id,
                )
            )
        transition_frames.append(_label_transitions(primary, candidate, str(candidate_id)))
    return (
        pd.DataFrame.from_records(pooled_rows),
        pd.DataFrame.from_records(participant_rows),
        pd.concat(transition_frames, ignore_index=True),
    )
