"""Small, auditable Hb-PPG State exploratory feature pipeline.

This module deliberately produces one row per participant.  It is for development-only
exploration and does not create a registered label, split, or final-test result.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd
from scipy.signal import detrend, find_peaks, periodogram
from sklearn.model_selection import train_test_split  # type: ignore[import-untyped]

STATE_CHANNELS = ("660nm", "730nm", "850nm", "940nm")
STATE_DATASET_VERSION = "hbppg-v6"
STATE_LABEL_BOUNDARY_Mmol_L = 5.6


def _finite_array(values: Any) -> np.ndarray:
    array = pd.to_numeric(pd.Series(values), errors="coerce").to_numpy(dtype=np.float64)
    finite = array[np.isfinite(array)]
    if finite.size == 0:
        raise ValueError("A signal channel contains no finite samples")
    return np.asarray(finite, dtype=np.float64)


def _safe_statistic(value: Any) -> float:
    numeric = float(value)
    return numeric if np.isfinite(numeric) else 0.0


def _channel_features(values: Any, sampling_rate_hz: float) -> dict[str, float]:
    signal = _finite_array(values)
    centered = signal - float(np.mean(signal))
    std = float(np.std(signal))
    q25, median, q75 = np.quantile(signal, [0.25, 0.5, 0.75])
    features = {
        "mean": _safe_statistic(np.mean(signal)),
        "std": _safe_statistic(std),
        "median": _safe_statistic(median),
        "iqr": _safe_statistic(q75 - q25),
        "minimum": _safe_statistic(np.min(signal)),
        "maximum": _safe_statistic(np.max(signal)),
        "range": _safe_statistic(np.max(signal) - np.min(signal)),
        "skew": _safe_statistic(pd.Series(signal).skew()),
        "kurtosis": _safe_statistic(pd.Series(signal).kurt()),
    }

    frequencies, power = periodogram(detrend(signal), fs=sampling_rate_hz)
    pulse_band = (frequencies >= 0.5) & (frequencies <= 4.0)
    if np.any(pulse_band) and float(np.sum(power[pulse_band])) > 0:
        pulse_power = power[pulse_band]
        pulse_frequencies = frequencies[pulse_band]
        peak_index = int(np.argmax(pulse_power))
        features["dominant_frequency_hz"] = _safe_statistic(pulse_frequencies[peak_index])
        total_power = float(np.sum(power[(frequencies >= 0.1) & (frequencies <= 10.0)]))
        features["pulse_band_ratio"] = _safe_statistic(
            float(np.sum(pulse_power)) / total_power if total_power > 0 else 0.0
        )
    else:
        features["dominant_frequency_hz"] = 0.0
        features["pulse_band_ratio"] = 0.0

    if std > 0:
        peaks, properties = find_peaks(
            centered,
            distance=max(1, int(0.25 * sampling_rate_hz)),
            prominence=max(std * 0.1, np.finfo(float).eps),
        )
        intervals = np.diff(peaks) / sampling_rate_hz
        prominences = np.asarray(properties.get("prominences", []), dtype=np.float64)
        features["estimated_pulse_rate_bpm"] = _safe_statistic(
            60.0 / float(np.mean(intervals)) if intervals.size else 0.0
        )
        features["peak_interval_mean_s"] = (
            _safe_statistic(np.mean(intervals)) if intervals.size else 0.0
        )
        features["peak_interval_std_s"] = (
            _safe_statistic(np.std(intervals)) if intervals.size else 0.0
        )
        features["peak_prominence_mean"] = (
            _safe_statistic(np.mean(prominences)) if prominences.size else 0.0
        )
        features["peak_prominence_std"] = (
            _safe_statistic(np.std(prominences)) if prominences.size else 0.0
        )
    else:
        features.update(
            {
                "estimated_pulse_rate_bpm": 0.0,
                "peak_interval_mean_s": 0.0,
                "peak_interval_std_s": 0.0,
                "peak_prominence_mean": 0.0,
                "peak_prominence_std": 0.0,
            }
        )
    return features


def extract_state_features(
    frame: pd.DataFrame, sampling_rate_hz: float = 200.0
) -> dict[str, float]:
    """Extract cheap statistics, spectral summaries, pulse summaries, and relations."""

    missing = [channel for channel in STATE_CHANNELS if channel not in frame.columns]
    if missing:
        raise ValueError(f"Missing required Hb-PPG channels: {missing}")
    channel_values: dict[str, np.ndarray] = {}
    output: dict[str, float] = {}
    for channel in STATE_CHANNELS:
        values = _finite_array(frame[channel])
        channel_values[channel] = values
        for name, value in _channel_features(values, sampling_rate_hz).items():
            output[f"ppg_{channel}_{name}"] = float(value)

    for left_index, left in enumerate(STATE_CHANNELS):
        for right in STATE_CHANNELS[left_index + 1 :]:
            length = min(len(channel_values[left]), len(channel_values[right]))
            left_values = channel_values[left][:length]
            right_values = channel_values[right][:length]
            correlation = np.corrcoef(left_values, right_values)[0, 1]
            output[f"cross_corr_{left}_{right}"] = _safe_statistic(correlation)
            left_amplitude = float(np.ptp(left_values))
            right_amplitude = float(np.ptp(right_values))
            output[f"cross_amplitude_ratio_{left}_{right}"] = _safe_statistic(
                left_amplitude / right_amplitude if right_amplitude > 0 else 0.0
            )
            left_variability = float(np.std(left_values))
            right_variability = float(np.std(right_values))
            output[f"cross_variability_ratio_{left}_{right}"] = _safe_statistic(
                left_variability / right_variability if right_variability > 0 else 0.0
            )
    return output


def _read_metadata(metadata_path: Path) -> pd.DataFrame:
    frame = pd.read_excel(metadata_path, dtype=object)
    required = {
        "ID",
        "Gender",
        "Age (year)",
        "Height (cm)",
        "Weight (kg)",
        "Blood glucose (mmol/L)",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Hb-PPG metadata is missing columns: {missing}")
    result = pd.DataFrame(
        {
            "participant_id": pd.to_numeric(frame["ID"], errors="raise").astype(int),
            "glucose_reference": pd.to_numeric(frame["Blood glucose (mmol/L)"], errors="coerce"),
            "age": pd.to_numeric(frame["Age (year)"], errors="coerce"),
            "sex": frame["Gender"].astype("string"),
            "height_cm": pd.to_numeric(frame["Height (cm)"], errors="coerce"),
            "weight_kg": pd.to_numeric(frame["Weight (kg)"], errors="coerce"),
        }
    )
    result["bmi"] = result["weight_kg"] / (result["height_cm"] / 100.0) ** 2
    result["sex_code"] = result["sex"].str.lower().map({"female": 0.0, "male": 1.0})
    return result


def create_state_test_reserve(
    participants: pd.DataFrame,
    output_path: Path,
    *,
    seed: int = 20260817,
    test_fraction: float = 0.20,
    created_date: str | None = None,
) -> dict[str, Any]:
    """Create the immutable outer reserve from audit participants."""

    required = {"participant_id", "glucose_mmol_l", "state_reference_eligible"}
    missing = sorted(required - set(participants.columns))
    if missing:
        raise ValueError(f"Audit participant table is missing columns: {missing}")
    eligible = participants.loc[participants["state_reference_eligible"].astype(bool)].copy()
    eligible["glucose_mmol_l"] = pd.to_numeric(eligible["glucose_mmol_l"], errors="coerce")
    eligible = eligible.loc[eligible["glucose_mmol_l"].notna()].copy()
    if eligible.empty:
        raise ValueError("No reference-eligible State participants are available")
    if not 0 < test_fraction < 1:
        raise ValueError("test_fraction must be between zero and one")
    labels = np.where(
        eligible["glucose_mmol_l"].to_numpy() < STATE_LABEL_BOUNDARY_Mmol_L,
        "NORMAL_RANGE",
        "ELEVATED_FASTING_RANGE",
    )
    development_ids, reserved_ids = train_test_split(
        eligible["participant_id"].astype(int).to_numpy(),
        test_size=test_fraction,
        random_state=seed,
        stratify=labels,
    )
    payload: dict[str, Any] = {
        "schema_version": 1,
        "seed": seed,
        "dataset": "hbppg",
        "dataset_version": STATE_DATASET_VERSION,
        "eligible_participant_count": int(len(eligible)),
        "development_ids": sorted(int(value) for value in development_ids),
        "reserved_test_ids": sorted(int(value) for value in reserved_ids),
        "source_audit": {
            "participants_path": "reports/audits/hbppg_participants.csv",
            "audit_path": "reports/audits/hbppg_audit.json",
            "eligible_reference_count": int(len(eligible)),
            "candidate_label_boundary_mmol_l": STATE_LABEL_BOUNDARY_Mmol_L,
            "candidate_label_support": {
                str(key): int(value) for key, value in pd.Series(labels).value_counts().items()
            },
        },
        "created_date": created_date or date.today().isoformat(),
    }
    if set(payload["development_ids"]) & set(payload["reserved_test_ids"]):
        raise AssertionError("State reserve participant overlap")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def load_state_test_reserve(path: Path) -> dict[str, Any]:
    """Load and validate a State outer reserve manifest."""

    payload = cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    for key in (
        "schema_version",
        "seed",
        "dataset",
        "dataset_version",
        "eligible_participant_count",
        "development_ids",
        "reserved_test_ids",
        "source_audit",
        "created_date",
    ):
        if key not in payload:
            raise ValueError(f"State reserve is missing {key}")
    development = {int(value) for value in payload["development_ids"]}
    reserved = {int(value) for value in payload["reserved_test_ids"]}
    if not development or not reserved or development & reserved:
        raise ValueError("State reserve must have non-empty, disjoint participant sets")
    if len(development) + len(reserved) != int(payload["eligible_participant_count"]):
        raise ValueError("State reserve counts do not match eligible_participant_count")
    payload["development_ids"] = sorted(development)
    payload["reserved_test_ids"] = sorted(reserved)
    return payload


def assert_development_ids(ids: Any, reserve: dict[str, Any]) -> None:
    """Reject any exploratory table that includes a reserved participant."""

    observed = {int(value) for value in ids}
    reserved = {int(value) for value in reserve["reserved_test_ids"]}
    overlap = sorted(observed & reserved)
    if overlap:
        raise AssertionError(f"Exploratory data includes reserved State participants: {overlap}")
    development = set(int(value) for value in reserve["development_ids"])
    if not observed <= development:
        raise AssertionError(
            "Exploratory data includes participants outside the development reserve"
        )


def build_state_exploratory_table(
    dataset_root: Path,
    reserve_path: Path,
    *,
    metadata_path: Path | None = None,
    sampling_rate_hz: float = 200.0,
) -> pd.DataFrame:
    """Build one development-only feature row per participant."""

    reserve = load_state_test_reserve(reserve_path)
    metadata_path = metadata_path or dataset_root / "subject information.xlsx"
    metadata = _read_metadata(metadata_path)
    metadata = metadata.loc[metadata["participant_id"].isin(reserve["development_ids"])].copy()
    assert_development_ids(metadata["participant_id"], reserve)
    rows: list[dict[str, Any]] = []
    for record in metadata.sort_values("participant_id").to_dict("records"):
        participant_id = int(record["participant_id"])
        source_path = dataset_root / "data_csv" / f"{participant_id}.csv"
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        frame = pd.read_csv(source_path)
        feature_row: dict[str, Any] = extract_state_features(frame, sampling_rate_hz)
        feature_row.update(
            {
                "dataset": "hbppg",
                "dataset_version": STATE_DATASET_VERSION,
                "participant_id": participant_id,
                "source_file": f"data_csv/{participant_id}.csv",
                "glucose_reference": float(record["glucose_reference"]),
                "age": float(record["age"]) if pd.notna(record["age"]) else np.nan,
                "sex": str(record["sex"]),
                "sex_code": float(record["sex_code"]) if pd.notna(record["sex_code"]) else np.nan,
                "bmi": float(record["bmi"]) if pd.notna(record["bmi"]) else np.nan,
            }
        )
        rows.append(feature_row)
    table = pd.DataFrame(rows)
    assert_development_ids(table["participant_id"], reserve)
    if table["participant_id"].duplicated().any():
        raise AssertionError("Exploratory State table must have one row per participant")
    return table


def add_candidate_state_labels(table: pd.DataFrame) -> pd.DataFrame:
    """Add documented candidate labels without treating one as frozen."""

    result = table.copy()
    glucose = pd.to_numeric(result["glucose_reference"], errors="raise")
    result["candidate_a_binary"] = np.where(
        glucose < STATE_LABEL_BOUNDARY_Mmol_L, "NORMAL_RANGE", "ELEVATED_FASTING_RANGE"
    )
    result["candidate_b_ada_3class"] = pd.cut(
        glucose,
        bins=[-np.inf, 5.6, 7.0, np.inf],
        labels=["NORMAL_RANGE", "PREDIABETES_RANGE", "DIABETES_RANGE"],
        right=False,
    ).astype(str)
    result["candidate_c_who_3class"] = pd.cut(
        glucose,
        bins=[-np.inf, 6.1, 7.0, np.inf],
        labels=["BELOW_IFG_THRESHOLD", "IFG_RANGE", "DIABETES_RANGE"],
        right=False,
    ).astype(str)
    result["candidate_d_continuous"] = glucose.astype(float)
    return result


def ppg_feature_columns(table: pd.DataFrame) -> list[str]:
    """Return only waveform-derived features, excluding identifiers and references."""

    return [column for column in table.columns if column.startswith(("ppg_", "cross_"))]


def context_feature_columns(table: pd.DataFrame) -> list[str]:
    """Return the declared context comparator features."""

    return [column for column in ("age", "sex_code", "bmi") if column in table.columns]
