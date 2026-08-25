"""Fixed conditioning and quality primitives for exploratory Trend probes."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import signal


@dataclass(frozen=True)
class ConditioningSpec:
    """A predeclared deterministic BVP conditioning representation."""

    name: str
    detrend: str
    low_hz: float
    high_hz: float
    order: int
    normalization: str


RAW_ANCHOR = ConditioningSpec("raw_anchor", "none", 0.0, 0.0, 0, "none")
BP_0P5_8_ZSCORE = ConditioningSpec("bp_0p5_8_zscore", "linear", 0.5, 8.0, 4, "zscore")
BP_0P7_4_ROBUST = ConditioningSpec("bp_0p7_4_robust", "linear", 0.7, 4.0, 4, "robust")
CONDITIONING_VARIANTS = (RAW_ANCHOR, BP_0P5_8_ZSCORE, BP_0P7_4_ROBUST)


@dataclass(frozen=True)
class WindowQuality:
    """Bounded quality proxy components for one short BVP window."""

    flat_fraction: float
    log_iqr: float
    bandpower_ratio: float
    acc_rms: float
    sqi: float


def compose_sqi(
    flat_fraction: float,
    log_iqr: float,
    bandpower_ratio: float,
    acc_rms: float,
) -> float:
    """Compose the bounded proxy SQI from stored window components."""

    if not all(np.isfinite(value) for value in (flat_fraction, log_iqr, bandpower_ratio, acc_rms)):
        raise ValueError("SQI components must be finite")
    if flat_fraction < 0 or log_iqr < 0 or not 0 <= bandpower_ratio <= 1 or acc_rms < 0:
        raise ValueError("SQI components are outside their valid ranges")
    flat_score = float(np.clip(1.0 - flat_fraction / 0.05, 0.0, 1.0))
    amplitude_score = float(np.clip(log_iqr / max(log_iqr + 1.0, 1e-12), 0.0, 1.0))
    motion_score = float(np.exp(-acc_rms))
    geometric_mean = (flat_score * amplitude_score * bandpower_ratio * motion_score) ** 0.25
    return float(np.clip(geometric_mean, 0.0, 1.0))


def _validate_window(values: np.ndarray, rate_hz: int) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or array.size < 16:
        raise ValueError("BVP window must be a one-dimensional array with at least 16 samples")
    if rate_hz <= 0:
        raise ValueError("BVP sampling rate must be positive")
    if not np.isfinite(array).all():
        raise ValueError("BVP window contains non-finite values")
    return array


def condition_window(values: np.ndarray, rate_hz: int, spec: ConditioningSpec) -> np.ndarray:
    """Apply one fixed, past-only BVP conditioning representation."""

    array = _validate_window(values, rate_hz)
    if spec.detrend not in {"none", "linear"}:
        raise ValueError(f"Unsupported detrend mode: {spec.detrend}")
    if spec.normalization not in {"none", "zscore", "robust"}:
        raise ValueError(f"Unsupported normalization mode: {spec.normalization}")
    if spec.name == RAW_ANCHOR.name:
        filtered = array.copy()
    else:
        nyquist = rate_hz / 2.0
        if spec.low_hz <= 0 or spec.high_hz <= spec.low_hz:
            raise ValueError("Bandpass cutoffs must satisfy 0 < low_hz < high_hz")
        if spec.high_hz >= nyquist:
            raise ValueError(f"Bandpass high_hz must be below Nyquist ({nyquist:g} Hz)")
        detrended = signal.detrend(array, type="linear") if spec.detrend == "linear" else array
        sos = signal.butter(
            spec.order,
            [spec.low_hz, spec.high_hz],
            btype="bandpass",
            fs=rate_hz,
            output="sos",
        )
        filtered = signal.sosfiltfilt(sos, detrended)
    if spec.normalization == "none":
        return filtered.astype(np.float64, copy=False)
    if spec.normalization == "zscore":
        scale = max(float(filtered.std()), 1e-12)
        return np.asarray((filtered - filtered.mean()) / scale, dtype=np.float64)
    median = float(np.median(filtered))
    iqr = float(np.subtract(*np.percentile(filtered, [75, 25])))
    return np.asarray((filtered - median) / max(iqr, 1e-12), dtype=np.float64)


def _bandpower_ratio(values: np.ndarray, rate_hz: int) -> float:
    frequencies = np.fft.rfftfreq(values.size, d=1.0 / rate_hz)
    spectrum = np.abs(np.fft.rfft(values - values.mean())) ** 2
    denominator = float(spectrum[(frequencies >= 0) & (frequencies <= rate_hz / 2)].sum())
    numerator = float(spectrum[(frequencies >= 0.5) & (frequencies <= 8.0)].sum())
    return float(np.clip(numerator / max(denominator, 1e-12), 0.0, 1.0))


def compute_window_quality(
    raw_values: np.ndarray,
    conditioned_values: np.ndarray,
    *,
    rate_hz: int,
    acc_rms: float = 0.0,
) -> WindowQuality:
    """Compute an interpretable bounded quality proxy for one BVP window."""

    raw = _validate_window(raw_values, rate_hz)
    conditioned = _validate_window(conditioned_values, rate_hz)
    if raw.size != conditioned.size:
        raise ValueError("Raw and conditioned windows must have equal length")
    if not np.isfinite(acc_rms) or acc_rms < 0:
        raise ValueError("ACC RMS must be finite and non-negative")
    differences = np.diff(raw)
    flat_fraction = float(np.mean(differences == 0))
    iqr = float(np.subtract(*np.percentile(raw, [75, 25])))
    log_iqr = float(np.log1p(max(iqr, 0.0)))
    bandpower_ratio = _bandpower_ratio(conditioned, rate_hz)
    sqi = compose_sqi(flat_fraction, log_iqr, bandpower_ratio, float(acc_rms))
    return WindowQuality(flat_fraction, log_iqr, bandpower_ratio, float(acc_rms), sqi)


def fit_participant_quality_thresholds(train_windows: pd.DataFrame) -> pd.DataFrame:
    """Fit participant-specific SQI cutoffs using train rows only."""

    required = {"participant_id", "split", "sqi"}
    missing = required.difference(train_windows.columns)
    if missing:
        raise ValueError(f"Quality windows are missing columns: {sorted(missing)}")
    if set(train_windows["split"].astype(str)).difference({"train"}):
        raise ValueError("Quality thresholds must be fit from train rows only")
    rows: list[dict[str, object]] = []
    for participant_id, group in train_windows.groupby("participant_id", sort=True):
        values = pd.to_numeric(group["sqi"], errors="coerce").dropna()
        if values.empty:
            raise ValueError(f"Participant {participant_id} has no finite train SQI values")
        rows.append(
            {
                "participant_id": participant_id,
                "hard_exclusion_cutoff": float(values.quantile(0.10)),
                "soft_weight_floor": float(values.quantile(0.25)),
            }
        )
    return pd.DataFrame(rows).set_index("participant_id")


def apply_quality_policy(
    history: pd.DataFrame,
    policy: str,
    thresholds: pd.DataFrame,
    *,
    minimum_weight: float = 0.25,
) -> pd.DataFrame:
    """Apply report-only, soft-weight, or hard-exclusion quality policy."""

    required = {"participant_id", "sqi"}
    missing = required.difference(history.columns)
    if missing:
        raise ValueError(f"History is missing quality columns: {sorted(missing)}")
    if policy not in {"report_only", "soft_weight", "hard_exclude_bottom_train_decile"}:
        raise ValueError(f"Unsupported quality policy: {policy}")
    result = history.copy()
    if policy == "report_only":
        result["quality_weight"] = 1.0
        result["quality_retained"] = True
        return result
    if minimum_weight <= 0 or minimum_weight > 1:
        raise ValueError("minimum_weight must lie in (0, 1]")
    lookup = thresholds.reindex(result["participant_id"])
    if lookup.isna().any(axis=None):
        raise ValueError("Quality thresholds are missing a participant")
    sqi = pd.to_numeric(result["sqi"], errors="coerce")
    if sqi.isna().any():
        raise ValueError("History contains non-finite SQI values")
    if policy == "soft_weight":
        floor = lookup["soft_weight_floor"].to_numpy(dtype=float)
        normalized = np.divide(
            sqi.to_numpy(dtype=float),
            np.maximum(floor, 1e-12),
            out=np.ones(len(result), dtype=float),
            where=floor > 0,
        )
        result["quality_weight"] = np.clip(normalized, minimum_weight, 1.0)
        result["quality_retained"] = True
    else:
        cutoff = lookup["hard_exclusion_cutoff"].to_numpy(dtype=float)
        result["quality_weight"] = 1.0
        result["quality_retained"] = sqi.to_numpy(dtype=float) >= cutoff
    return result
