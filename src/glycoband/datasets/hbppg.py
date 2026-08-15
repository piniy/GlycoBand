"""Hb-PPG v6 loading and raw-data audit utilities."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from matplotlib import pyplot as plt
from scipy.signal import detrend, periodogram

METADATA_FILE = "subject information.xlsx"
GLUCOSE_COLUMN = "Blood glucose (mmol/L)"
DURATION_COLUMN = "Signal length (second)"
ID_COLUMN = "ID"


@dataclass(frozen=True)
class Category:
    """One half-open numeric category [lower, upper)."""

    name: str
    lower: float | None
    upper: float | None


def load_config(path: Path) -> dict[str, Any]:
    """Load the versioned Hb-PPG audit configuration."""

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Hb-PPG audit config must be a mapping")
    return payload


def classify_value(value: float, categories: Sequence[Category]) -> str:
    """Assign a finite value to exactly one configured half-open category."""

    matches = [
        category.name
        for category in categories
        if (category.lower is None or value >= category.lower)
        and (category.upper is None or value < category.upper)
    ]
    if len(matches) != 1:
        raise ValueError(f"Value {value} matched {len(matches)} categories: {matches}")
    return matches[0]


def _channel_metrics(
    values: np.ndarray,
    sampling_rate_hz: float,
    pulse_band_hz: tuple[float, float],
    reference_band_hz: tuple[float, float],
) -> dict[str, float | bool]:
    finite = np.isfinite(values)
    finite_values = values[finite]
    if finite_values.size == 0:
        return {
            "missing_fraction": 1.0,
            "standard_deviation": float("nan"),
            "unique_fraction": 0.0,
            "flat_difference_fraction": float("nan"),
            "extrema_fraction": float("nan"),
            "pulse_peak_hz": float("nan"),
            "pulse_band_ratio": float("nan"),
        }

    differences = np.diff(finite_values)
    flat_fraction = float(np.mean(differences == 0)) if differences.size else float("nan")
    minimum = float(np.min(finite_values))
    maximum = float(np.max(finite_values))
    extrema_fraction = float(np.mean((finite_values == minimum) | (finite_values == maximum)))

    pulse_peak_hz = float("nan")
    pulse_band_ratio = float("nan")
    if finite_values.size >= sampling_rate_hz * 5 and float(np.std(finite_values)) > 0:
        frequencies, power = periodogram(detrend(finite_values), fs=sampling_rate_hz)
        reference = (frequencies >= reference_band_hz[0]) & (
            frequencies <= reference_band_hz[1]
        )
        pulse = (frequencies >= pulse_band_hz[0]) & (frequencies <= pulse_band_hz[1])
        reference_power = float(np.sum(power[reference]))
        if reference_power > 0 and np.any(pulse):
            pulse_power = power[pulse]
            pulse_frequencies = frequencies[pulse]
            pulse_peak_hz = float(pulse_frequencies[int(np.argmax(pulse_power))])
            pulse_band_ratio = float(np.sum(pulse_power) / reference_power)

    return {
        "missing_fraction": float(1.0 - np.mean(finite)),
        "standard_deviation": float(np.std(finite_values)),
        "unique_fraction": float(np.unique(finite_values).size / finite_values.size),
        "flat_difference_fraction": flat_fraction,
        "extrema_fraction": extrema_fraction,
        "pulse_peak_hz": pulse_peak_hz,
        "pulse_band_ratio": pulse_band_ratio,
    }


def audit_participant(
    participant_id: int,
    metadata_row: pd.Series,
    csv_path: Path,
    required_channels: Sequence[str],
    declared_rate_hz: float,
    screen: Mapping[str, Any],
) -> dict[str, Any]:
    """Audit one participant while preserving all observed anomalies."""

    reasons: list[str] = []
    result: dict[str, Any] = {
        "dataset": "hbppg",
        "dataset_version": "v6",
        "participant_id": participant_id,
        "source_file": f"data_csv/{participant_id}.csv",
        "file_exists": csv_path.is_file(),
        "glucose_raw": str(metadata_row[GLUCOSE_COLUMN]),
        "glucose_mmol_l": pd.to_numeric(metadata_row[GLUCOSE_COLUMN], errors="coerce"),
        "declared_duration_seconds": float(metadata_row[DURATION_COLUMN]),
    }
    if pd.isna(result["glucose_mmol_l"]):
        reasons.append("MISSING_GLUCOSE_REFERENCE")
    if not csv_path.is_file():
        reasons.append("MISSING_CSV")
        result.update(
            {
                "rows": 0,
                "implied_rate_hz": float("nan"),
                "signal_screen_pass": False,
                "state_reference_eligible": "MISSING_GLUCOSE_REFERENCE" not in reasons,
                "audit_usable": False,
            }
        )
        result["exclusion_reasons"] = ";".join(sorted(reasons))
        return result

    frame = pd.read_csv(csv_path)
    observed_channels = list(frame.columns)
    result["observed_channels"] = "|".join(observed_channels)
    result["channel_order_valid"] = observed_channels == list(required_channels)
    if not result["channel_order_valid"]:
        reasons.append("INVALID_CHANNEL_SCHEMA")

    rows = len(frame)
    duration = float(metadata_row[DURATION_COLUMN])
    implied_rate = rows / duration if duration > 0 else float("nan")
    result.update({"rows": rows, "implied_rate_hz": implied_rate})
    if not np.isclose(implied_rate, declared_rate_hz, rtol=0, atol=0.01):
        reasons.append("IMPLIED_RATE_MISMATCH")

    max_flat = float(screen["maximum_flat_difference_fraction"])
    max_extrema = float(screen["maximum_extrema_fraction"])
    min_pulse_ratio = float(screen["minimum_pulse_band_ratio"])
    pulse_band = tuple(float(value) for value in screen["pulse_band_hz"])
    reference_band = tuple(float(value) for value in screen["spectral_reference_band_hz"])
    if len(pulse_band) != 2 or len(reference_band) != 2:
        raise ValueError("Spectral bands must each contain lower and upper bounds")
    available_channels = [channel for channel in required_channels if channel in frame]
    duplicate_channel_pairs = [
        f"{left}={right}"
        for index, left in enumerate(available_channels)
        for right in available_channels[index + 1 :]
        if np.array_equal(
            pd.to_numeric(frame[left], errors="coerce").to_numpy(dtype=np.float64),
            pd.to_numeric(frame[right], errors="coerce").to_numpy(dtype=np.float64),
            equal_nan=True,
        )
    ]
    result["duplicate_channel_pairs"] = "|".join(duplicate_channel_pairs)
    if duplicate_channel_pairs:
        reasons.append("DUPLICATE_WAVELENGTH_CONTENT")
    for channel in required_channels:
        prefix = f"ch_{channel}_"
        if channel not in frame:
            reasons.append(f"MISSING_CHANNEL_{channel}")
            continue
        numeric = pd.to_numeric(frame[channel], errors="coerce").to_numpy(dtype=np.float64)
        metrics = _channel_metrics(
            numeric,
            declared_rate_hz,
            (pulse_band[0], pulse_band[1]),
            (reference_band[0], reference_band[1]),
        )
        result.update({prefix + key: value for key, value in metrics.items()})
        if float(metrics["missing_fraction"]) > 0:
            reasons.append(f"NONFINITE_{channel}")
        flat = float(metrics["flat_difference_fraction"])
        if np.isfinite(flat) and flat > max_flat:
            reasons.append(f"FLAT_SCREEN_{channel}")
        extrema = float(metrics["extrema_fraction"])
        if np.isfinite(extrema) and extrema > max_extrema:
            reasons.append(f"EXTREMA_SCREEN_{channel}")
        ratio = float(metrics["pulse_band_ratio"])
        if not np.isfinite(ratio) or ratio < min_pulse_ratio:
            reasons.append(f"PULSE_SCREEN_{channel}")

    unique_reasons = sorted(set(reasons))
    signal_reasons = [reason for reason in unique_reasons if reason != "MISSING_GLUCOSE_REFERENCE"]
    result["signal_screen_pass"] = not signal_reasons
    result["state_reference_eligible"] = "MISSING_GLUCOSE_REFERENCE" not in unique_reasons
    result["exclusion_reasons"] = ";".join(unique_reasons)
    result["audit_usable"] = not unique_reasons
    return result


def _categories_from_config(items: Sequence[Mapping[str, Any]]) -> list[Category]:
    return [
        Category(
            name=str(item["name"]),
            lower=None if item.get("lower") is None else float(item["lower"]),
            upper=None if item.get("upper") is None else float(item["upper"]),
        )
        for item in items
    ]


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(value) else float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def audit_hbppg(
    dataset_root: Path, config: Mapping[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run the complete Hb-PPG metadata and waveform audit."""

    metadata = pd.read_excel(dataset_root / METADATA_FILE, dtype=object)
    if metadata[ID_COLUMN].duplicated().any():
        duplicates = metadata.loc[metadata[ID_COLUMN].duplicated(), ID_COLUMN].tolist()
        raise ValueError(f"Duplicate metadata IDs: {duplicates}")

    required_channels = [str(item) for item in config["required_channels"]]
    declared_rate = float(config["sampling_rate_hz"])
    records = [
        audit_participant(
            int(row[ID_COLUMN]),
            row,
            dataset_root / "data_csv" / f"{int(row[ID_COLUMN])}.csv",
            required_channels,
            declared_rate,
            config["descriptive_signal_screen"],
        )
        for _, row in metadata.iterrows()
    ]
    participants = pd.DataFrame.from_records(records).sort_values("participant_id")

    csv_ids = {int(path.stem) for path in (dataset_root / "data_csv").glob("*.csv")}
    mat_ids = {int(path.stem) for path in (dataset_root / "data_mat").glob("*.mat")}
    metadata_ids = set(participants["participant_id"].astype(int))
    glucose = pd.to_numeric(participants["glucose_mmol_l"], errors="coerce").dropna()
    quantiles = glucose.quantile([0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1])

    schemes: dict[str, Any] = {}
    for scheme_name, scheme in config["candidate_glucose_schemes"].items():
        categories = _categories_from_config(scheme["categories"])
        labels = glucose.map(
            lambda value, current=categories: classify_value(float(value), current)
        )
        schemes[str(scheme_name)] = {
            "source": str(scheme["source"]),
            "counts": {str(key): int(value) for key, value in labels.value_counts().items()},
            "eligible_participants": int(labels.size),
        }

    summary = {
        "schema_version": 1,
        "dataset": str(config["dataset"]),
        "participant_inventory": {
            "metadata": len(metadata_ids),
            "csv": len(csv_ids),
            "mat": len(mat_ids),
            "metadata_without_csv": sorted(metadata_ids - csv_ids),
            "csv_without_metadata": sorted(csv_ids - metadata_ids),
            "metadata_without_mat": sorted(metadata_ids - mat_ids),
            "mat_without_metadata": sorted(mat_ids - metadata_ids),
        },
        "glucose_mmol_l": {
            "valid": int(glucose.size),
            "missing": int(participants["glucose_mmol_l"].isna().sum()),
            "mean": float(glucose.mean()),
            "standard_deviation": float(glucose.std()),
            "quantiles": {str(index): float(value) for index, value in quantiles.items()},
            "sorted_values": sorted(float(value) for value in glucose),
        },
        "candidate_glucose_schemes": schemes,
        "signal_integrity": {
            "channel_schema_valid": int(participants["channel_order_valid"].fillna(False).sum()),
            "signal_screen_pass": int(participants["signal_screen_pass"].fillna(False).sum()),
            "state_reference_eligible": int(
                participants["state_reference_eligible"].fillna(False).sum()
            ),
            "audit_usable": int(participants["audit_usable"].fillna(False).sum()),
            "with_exclusion_reasons": int((participants["exclusion_reasons"] != "").sum()),
            "duration_counts_seconds": {
                str(key): int(value)
                for key, value in participants["declared_duration_seconds"].value_counts().items()
            },
            "implied_rate_hz": {
                "minimum": float(participants["implied_rate_hz"].min()),
                "median": float(participants["implied_rate_hz"].median()),
                "maximum": float(participants["implied_rate_hz"].max()),
            },
        },
    }
    return participants, _json_safe(summary)


def write_hbppg_artifacts(
    dataset_root: Path,
    participants: pd.DataFrame,
    summary: Mapping[str, Any],
    reports_root: Path,
) -> None:
    """Write compact, reproducible Hb-PPG audit tables, report, and figures."""

    audits = reports_root / "audits"
    figures = reports_root / "figures"
    audits.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    participants.to_csv(audits / "hbppg_participants.csv", index=False)
    (audits / "hbppg_audit.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    glucose_summary = summary["glucose_mmol_l"]
    inventory = summary["participant_inventory"]
    integrity = summary["signal_integrity"]
    scheme_lines = []
    for name, scheme in summary["candidate_glucose_schemes"].items():
        counts = ", ".join(f"{label}={count}" for label, count in scheme["counts"].items())
        scheme_lines.append(f"- `{name}`: {counts} (sensitivity only; source in config)")
    verdict = (
        f"The audit accounted for {inventory['metadata']} metadata participants, "
        f"{inventory['csv']} CSV files, and {inventory['mat']} MAT files. "
        f"{glucose_summary['valid']} participants have numeric fasting-glucose "
        f"references; {glucose_summary['missing']} do not. This report does not freeze "
        "a State label or split."
    )
    glucose_range = (
        f"{glucose_summary['quantiles']['0.0']:.3f} / "
        f"{glucose_summary['quantiles']['0.5']:.3f} / "
        f"{glucose_summary['quantiles']['1.0']:.3f} mmol/L"
    )
    rate_range = (
        f"{integrity['implied_rate_hz']['minimum']:.3f} / "
        f"{integrity['implied_rate_hz']['median']:.3f} / "
        f"{integrity['implied_rate_hz']['maximum']:.3f} Hz"
    )
    report = f"""# Hb-PPG v6 Raw-Data Audit

## Verdict

{verdict}

## Inventory and joins

- Metadata without CSV: `{inventory['metadata_without_csv']}`
- CSV without metadata: `{inventory['csv_without_metadata']}`
- Metadata without MAT: `{inventory['metadata_without_mat']}`
- MAT without metadata: `{inventory['mat_without_metadata']}`
- Four-channel schema valid: {integrity['channel_schema_valid']}
- Passed descriptive signal screens: {integrity['signal_screen_pass']}
- Eligible reference + signal records for State review: {integrity['audit_usable']}
- Flagged for explicit review: {integrity['with_exclusion_reasons']}

## Glucose support

- Numeric: {glucose_summary['valid']}
- Missing/non-numeric: {glucose_summary['missing']}
- Mean: {glucose_summary['mean']:.3f} mmol/L
- Minimum / median / maximum: {glucose_range}

## Candidate category sensitivity

{chr(10).join(scheme_lines)}

These are descriptive counts under external threshold schemes. They are not diagnoses and are
not an approved project label. Repeat-testing and clinical-context requirements are outside this
dataset.

## Signal observations

- Declared duration counts: `{integrity['duration_counts_seconds']}`
- Implied rate min / median / max: {rate_range}
- Participant-level flags and channel metrics: `hbppg_participants.csv`

## Gate consequence

This audit supplies evidence for human review. It does not authorize label freeze, split creation,
architecture selection, model training, or final-test access.
"""
    (audits / "hbppg_audit.md").write_text(report, encoding="utf-8")

    glucose = pd.to_numeric(participants["glucose_mmol_l"], errors="coerce").dropna().sort_values()
    plt.figure(figsize=(7, 4))
    plt.step(glucose.to_numpy(), np.arange(1, len(glucose) + 1) / len(glucose), where="post")
    plt.xlabel("Fasting glucose (mmol/L)")
    plt.ylabel("Empirical cumulative proportion")
    plt.title("Hb-PPG v6 fasting-glucose ECDF")
    plt.tight_layout()
    plt.savefig(figures / "hbppg_glucose_ecdf.png", dpi=160)
    plt.close()

    representative_ids = [
        int(participants.loc[glucose.index[0], "participant_id"]),
        int(participants.loc[glucose.index[len(glucose) // 2], "participant_id"]),
        int(participants.loc[glucose.index[-1], "participant_id"]),
    ]
    figure, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True)
    for axis, participant_id in zip(axes, representative_ids, strict=True):
        frame = pd.read_csv(dataset_root / "data_csv" / f"{participant_id}.csv").iloc[:2000]
        normalized = (frame - frame.mean()) / frame.std(ddof=0)
        for channel in frame.columns:
            axis.plot(
                np.arange(len(frame)) / 200.0,
                normalized[channel],
                label=channel,
                linewidth=0.7,
            )
        glucose_value = participants.loc[
            participants["participant_id"] == participant_id, "glucose_mmol_l"
        ].iloc[0]
        axis.set_title(f"Participant {participant_id}; glucose={glucose_value} mmol/L")
        axis.set_ylabel("z score")
    axes[0].legend(ncol=4, fontsize=8)
    axes[-1].set_xlabel("Seconds (first 10 s)")
    figure.tight_layout()
    figure.savefig(figures / "hbppg_representative_signals.png", dpi=160)
    plt.close(figure)
