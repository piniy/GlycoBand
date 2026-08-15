"""BIG IDEAs v1.1.3 extraction, verification, and raw-data audit utilities."""

from __future__ import annotations

import hashlib
import json
import math
import os
import zipfile
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import IO, Any

import numpy as np
import pandas as pd
import yaml
from scipy.stats import theilslopes

NANOSECONDS_PER_SECOND = 1_000_000_000
CGM_TIMESTAMP = "Timestamp (YYYY-MM-DDThh:mm:ss)"
CGM_GLUCOSE = "Glucose Value (mg/dL)"


@dataclass(frozen=True)
class TimeSpan:
    """A closed continuous time span represented in nanoseconds."""

    start_ns: int
    end_ns: int


@dataclass(frozen=True)
class BvpAudit:
    """Streaming BVP audit result and compact alignment helpers."""

    fields: dict[str, Any]
    spans: tuple[TimeSpan, ...]
    valid_window_starts_ns: tuple[int, ...]
    valid_window_ends_ns: tuple[int, ...]


@dataclass(frozen=True)
class CgmAudit:
    """Clean EGV reference data plus explicit source-quality evidence."""

    frame: pd.DataFrame
    spans: tuple[TimeSpan, ...]
    fields: dict[str, Any]


def load_config(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("BIG IDEAs audit config must be a mapping")
    return payload


def parse_sha256_manifest(path: Path) -> dict[str, str]:
    """Parse the official two-column SHA-256 manifest."""

    entries: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"Invalid checksum manifest line {line_number}")
        digest, relative = parts
        relative = relative.replace("\\", "/")
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError(f"Invalid checksum manifest line {line_number}")
        if relative in entries:
            raise ValueError(f"Duplicate checksum path: {relative}")
        entries[relative] = digest.lower()
    return entries


def verify_manifest_anchor(
    path: Path, expected_sha256: str, expected_entries: int
) -> dict[str, Any]:
    """Anchor the local official manifest to its pinned digest and entry count."""

    observed_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    entries = parse_sha256_manifest(path)
    if observed_sha256 != expected_sha256:
        raise ValueError("Official checksum manifest digest differs from the pinned source")
    if len(entries) != expected_entries:
        raise ValueError("Official checksum manifest entry count differs from the pinned source")
    return {"sha256": observed_sha256, "entries": len(entries), "anchor_verified": True}


def participant_source_paths(participant_id: str) -> tuple[str, str]:
    """Return portable native source paths for one canonical participant ID."""

    if len(participant_id) != 3 or not participant_id.isdigit():
        raise ValueError(f"Invalid BIG IDEAs participant ID: {participant_id}")
    return (
        f"{participant_id}/BVP_{participant_id}.csv",
        f"{participant_id}/Dexcom_{participant_id}.csv",
    )


def sha256_stream(stream: IO[bytes], output: IO[bytes] | None = None) -> str:
    """Hash a stream and optionally copy it to an output stream."""

    digest = hashlib.sha256()
    while block := stream.read(1024 * 1024):
        digest.update(block)
        if output is not None:
            output.write(block)
    return digest.hexdigest()


def _safe_relative_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe archive member path: {value}")
    return path


def match_archive_members(
    member_names: Iterable[str], expected_paths: Iterable[str]
) -> tuple[dict[str, str], list[str]]:
    """Match archive members to manifest paths, tolerating one top-level folder."""

    expected = {_safe_relative_path(path).as_posix() for path in expected_paths}
    matches: dict[str, str] = {}
    unexpected: list[str] = []
    for member_name in member_names:
        if member_name.endswith("/"):
            continue
        safe = _safe_relative_path(member_name)
        candidates = [safe.as_posix()]
        if len(safe.parts) > 1:
            candidates.append(PurePosixPath(*safe.parts[1:]).as_posix())
        matching = [candidate for candidate in candidates if candidate in expected]
        if len(matching) == 1:
            manifest_path = matching[0]
            if manifest_path in matches:
                raise ValueError(f"Duplicate archive mapping for {manifest_path}")
            matches[manifest_path] = member_name
        elif safe.name != "SHA256SUMS.txt":
            unexpected.append(member_name)
    return matches, sorted(unexpected)


def verify_archive_membership(archive_path: Path, checksum_manifest: Path) -> dict[str, Any]:
    """Verify exact official archive membership without extracting content."""

    expected = parse_sha256_manifest(checksum_manifest)
    with zipfile.ZipFile(archive_path) as archive:
        mapping, unexpected = match_archive_members(archive.namelist(), expected)
    missing = sorted(set(expected) - set(mapping))
    return {
        "expected_files": len(expected),
        "matched_official_files": len(mapping),
        "missing_official_files": missing,
        "unexpected_archive_members": unexpected,
        "exact_archive_membership": not missing and not unexpected,
    }


def extract_and_verify_archive(
    archive_path: Path,
    destination: Path,
    checksum_manifest: Path,
) -> dict[str, Any]:
    """Extract only official files and verify each digest during decompression."""

    expected = parse_sha256_manifest(checksum_manifest)
    destination.mkdir(parents=True, exist_ok=True)
    verified: list[str] = []
    mismatches: list[str] = []
    with zipfile.ZipFile(archive_path) as archive:
        mapping, unexpected = match_archive_members(archive.namelist(), expected)
        missing = sorted(set(expected) - set(mapping))
        if missing:
            raise ValueError(f"Archive is missing {len(missing)} official files")
        if unexpected:
            raise ValueError(f"Archive has unexpected files: {unexpected}")
        for relative, member_name in sorted(mapping.items()):
            output_path = destination.joinpath(*PurePosixPath(relative).parts)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = output_path.with_suffix(output_path.suffix + ".partial")
            with archive.open(member_name) as source, temporary.open("wb") as output:
                observed = sha256_stream(source, output)
            if observed == expected[relative]:
                os.replace(temporary, output_path)
                verified.append(relative)
            else:
                temporary.unlink(missing_ok=True)
                mismatches.append(relative)
    if mismatches:
        raise ValueError(f"Checksum mismatch for: {mismatches}")
    return {
        "expected_files": len(expected),
        "verified_files": len(verified),
        "missing_files": [],
        "unexpected_files": [],
        "all_official_files_verified": len(verified) == len(expected),
    }


def verify_extracted_files(destination: Path, checksum_manifest: Path) -> dict[str, Any]:
    """Re-hash every extracted official file before an audit trusts it."""

    expected = parse_sha256_manifest(checksum_manifest)
    missing: list[str] = []
    mismatches: list[str] = []
    verified: list[str] = []
    expected_paths = {PurePosixPath(relative).as_posix() for relative in expected}
    for relative, expected_digest in sorted(expected.items()):
        path = destination.joinpath(*PurePosixPath(relative).parts)
        if not path.is_file():
            missing.append(relative)
            continue
        with path.open("rb") as stream:
            observed = sha256_stream(stream)
        if observed == expected_digest:
            verified.append(relative)
        else:
            mismatches.append(relative)
    observed_paths = {
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file()
    }
    unexpected = sorted(observed_paths - expected_paths)
    return {
        "expected_files": len(expected),
        "verified_files": len(verified),
        "missing_files": missing,
        "checksum_mismatches": mismatches,
        "unexpected_extracted_files": unexpected,
        "exact_destination_membership": not missing and not unexpected,
        "all_official_files_verified": not missing
        and not mismatches
        and len(verified) == len(expected),
    }


def continuous_spans(timestamps_ns: np.ndarray, maximum_gap_ns: int) -> tuple[TimeSpan, ...]:
    """Split ordered timestamps into continuous spans at invalid or large gaps."""

    if timestamps_ns.size == 0:
        return ()
    differences = np.diff(timestamps_ns)
    boundaries = np.flatnonzero((differences <= 0) | (differences > maximum_gap_ns)) + 1
    starts = np.concatenate(([0], boundaries))
    ends = np.concatenate((boundaries - 1, [timestamps_ns.size - 1]))
    return tuple(
        TimeSpan(int(timestamps_ns[start]), int(timestamps_ns[end]))
        for start, end in zip(starts, ends, strict=True)
    )


def intersect_duration_ns(left: Sequence[TimeSpan], right: Sequence[TimeSpan]) -> int:
    """Compute exact duration covered by both sorted span lists."""

    total = 0
    left_index = 0
    right_index = 0
    while left_index < len(left) and right_index < len(right):
        left_span = left[left_index]
        right_span = right[right_index]
        start = max(left_span.start_ns, right_span.start_ns)
        end = min(left_span.end_ns, right_span.end_ns)
        if end > start:
            total += end - start
        if left_span.end_ns <= right_span.end_ns:
            left_index += 1
        else:
            right_index += 1
    return total


def merge_time_spans(spans: Iterable[TimeSpan]) -> tuple[TimeSpan, ...]:
    """Return the sorted union of possibly overlapping wall-clock spans."""

    ordered = sorted(spans, key=lambda span: (span.start_ns, span.end_ns))
    if not ordered:
        return ()
    merged = [ordered[0]]
    for span in ordered[1:]:
        current = merged[-1]
        if span.start_ns <= current.end_ns:
            merged[-1] = TimeSpan(current.start_ns, max(current.end_ns, span.end_ns))
        else:
            merged.append(span)
    return tuple(merged)


def span_covers(spans: Sequence[TimeSpan], start_ns: int, end_ns: int) -> bool:
    """Return whether one continuous span contains the complete interval."""

    return any(span.start_ns <= start_ns and span.end_ns >= end_ns for span in spans)


def _weighted_median(counter: Counter[int]) -> float:
    total = sum(counter.values())
    if total == 0:
        return float("nan")
    target = (total - 1) // 2
    cumulative = 0
    for value, count in sorted(counter.items()):
        cumulative += count
        if cumulative > target:
            return float(value)
    raise AssertionError("Unreachable weighted median state")


def timestamps_to_ns(values: pd.Series) -> np.ndarray:
    """Normalize pandas timestamp resolution to integer nanoseconds."""

    return values.to_numpy(dtype="datetime64[ns]").astype(np.int64)


def audit_bvp_csv(
    path: Path,
    *,
    rate_hz: int,
    window_seconds: int,
    maximum_gap_seconds: float,
    chunksize: int = 1_000_000,
) -> BvpAudit:
    """Audit one BVP file chunk-wise without loading the participant into RAM."""

    rows = 0
    finite_rows = 0
    duplicate_timestamps = 0
    backwards_timestamps = 0
    gap_count = 0
    maximum_gap_ns_observed = 0
    delta_counts: Counter[int] = Counter()
    flat_differences = 0
    valid_differences = 0
    global_min = float("inf")
    global_max = float("-inf")
    global_min_count = 0
    global_max_count = 0
    first_ns: int | None = None
    last_ns: int | None = None
    previous_ns: int | None = None
    previous_value: float | None = None
    span_start_ns: int | None = None
    spans: list[TimeSpan] = []
    maximum_gap_ns = round(maximum_gap_seconds * NANOSECONDS_PER_SECOND)
    window_samples = rate_hz * window_seconds
    carry_times = np.array([], dtype=np.int64)
    carry_values = np.array([], dtype=np.float64)
    window_starts: list[int] = []
    window_ends: list[int] = []
    window_std: list[float] = []
    window_flat_fraction: list[float] = []

    for chunk in pd.read_csv(path, chunksize=chunksize):
        if list(chunk.columns) != ["datetime", " bvp"] and list(chunk.columns) != [
            "datetime",
            "bvp",
        ]:
            raise ValueError(f"Unexpected BVP schema in {path}: {list(chunk.columns)}")
        chunk.columns = [name.strip() for name in chunk.columns]
        parsed = pd.to_datetime(chunk["datetime"], errors="coerce")
        times = timestamps_to_ns(parsed)
        invalid_time = parsed.isna().to_numpy()
        values = pd.to_numeric(chunk["bvp"], errors="coerce").to_numpy(dtype=np.float64)
        valid = (~invalid_time) & np.isfinite(values)
        rows += len(chunk)
        finite_rows += int(valid.sum())

        valid_values = values[valid]
        if valid_values.size:
            chunk_min = float(valid_values.min())
            chunk_max = float(valid_values.max())
            if chunk_min < global_min:
                global_min = chunk_min
                global_min_count = int(np.sum(valid_values == chunk_min))
            elif chunk_min == global_min:
                global_min_count += int(np.sum(valid_values == chunk_min))
            if chunk_max > global_max:
                global_max = chunk_max
                global_max_count = int(np.sum(valid_values == chunk_max))
            elif chunk_max == global_max:
                global_max_count += int(np.sum(valid_values == chunk_max))

        if previous_ns is not None:
            assert previous_value is not None
            times = np.concatenate(([previous_ns], times))
            values = np.concatenate(([previous_value], values))
            valid = np.concatenate(([True], valid))
            leading_previous = True
        else:
            leading_previous = False

        valid_pairs = valid[:-1] & valid[1:]
        differences = np.diff(times)
        valid_deltas = differences[valid_pairs]
        unique_deltas, delta_frequencies = np.unique(valid_deltas, return_counts=True)
        for delta, frequency in zip(unique_deltas, delta_frequencies, strict=True):
            delta_counts[int(delta)] += int(frequency)
        duplicate_timestamps += int(np.sum(valid_deltas == 0))
        backwards_timestamps += int(np.sum(valid_deltas < 0))
        positive_deltas = valid_deltas[valid_deltas > 0]
        if positive_deltas.size:
            maximum_gap_ns_observed = max(maximum_gap_ns_observed, int(positive_deltas.max()))
        gap_count += int(np.sum(valid_deltas > maximum_gap_ns))
        comparable_values = np.diff(values)[valid_pairs]
        flat_differences += int(np.sum(comparable_values == 0))
        valid_differences += int(comparable_values.size)

        if leading_previous:
            times = times[1:]
            values = values[1:]
            valid = valid[1:]
        if times.size:
            first_valid = np.flatnonzero(valid)
            if first_valid.size:
                if first_ns is None:
                    first_ns = int(times[first_valid[0]])
                last_valid_index = int(first_valid[-1])
                last_ns = int(times[last_valid_index])
                previous_ns = last_ns
                previous_value = float(values[last_valid_index])

        combined_times = np.concatenate((carry_times, times))
        combined_values = np.concatenate((carry_values, values))
        combined_valid = np.isfinite(combined_values) & (combined_times != np.iinfo(np.int64).min)
        combined_breaks = np.flatnonzero(
            (~combined_valid[1:])
            | (~combined_valid[:-1])
            | (np.diff(combined_times) <= 0)
            | (np.diff(combined_times) > maximum_gap_ns)
        ) + 1
        segment_starts = np.concatenate(([0], combined_breaks))
        segment_ends = np.concatenate((combined_breaks, [combined_times.size]))
        carry_times = np.array([], dtype=np.int64)
        carry_values = np.array([], dtype=np.float64)
        for index, (start, end) in enumerate(zip(segment_starts, segment_ends, strict=True)):
            segment_times = combined_times[start:end]
            segment_values = combined_values[start:end]
            if segment_times.size == 0 or not np.all(np.isfinite(segment_values)):
                continue
            if span_start_ns is None:
                span_start_ns = int(segment_times[0])
            complete = segment_times.size // window_samples
            if complete:
                usable = complete * window_samples
                matrix = segment_values[:usable].reshape(complete, window_samples)
                time_matrix = segment_times[:usable].reshape(complete, window_samples)
                window_starts.extend(int(value) for value in time_matrix[:, 0])
                window_ends.extend(int(value) for value in time_matrix[:, -1])
                window_std.extend(float(value) for value in np.std(matrix, axis=1))
                window_flat_fraction.extend(
                    float(value) for value in np.mean(np.diff(matrix, axis=1) == 0, axis=1)
                )
                segment_times = segment_times[usable:]
                segment_values = segment_values[usable:]
            is_final_segment = index == len(segment_starts) - 1
            if is_final_segment:
                carry_times = segment_times
                carry_values = segment_values
            elif span_start_ns is not None:
                spans.append(TimeSpan(span_start_ns, int(combined_times[end - 1])))
                span_start_ns = None

    if span_start_ns is not None and last_ns is not None:
        spans.append(TimeSpan(span_start_ns, last_ns))
    duration_seconds = (
        (last_ns - first_ns) / NANOSECONDS_PER_SECOND
        if first_ns is not None and last_ns is not None
        else float("nan")
    )
    median_delta_ns = _weighted_median(delta_counts)
    implied_rate_hz = (
        NANOSECONDS_PER_SECOND / median_delta_ns
        if np.isfinite(median_delta_ns) and median_delta_ns > 0
        else float("nan")
    )
    extrema_count = (
        global_min_count if global_min == global_max else global_min_count + global_max_count
    )
    fields = {
        "bvp_rows": rows,
        "bvp_finite_rows": finite_rows,
        "bvp_missing_fraction": 1.0 - finite_rows / rows if rows else float("nan"),
        "bvp_start": pd.Timestamp(first_ns).isoformat() if first_ns is not None else None,
        "bvp_end": pd.Timestamp(last_ns).isoformat() if last_ns is not None else None,
        "bvp_duration_hours": duration_seconds / 3600,
        "bvp_duplicate_timestamps": duplicate_timestamps,
        "bvp_backwards_timestamps": backwards_timestamps,
        "bvp_gap_count": gap_count,
        "bvp_maximum_gap_seconds": maximum_gap_ns_observed / NANOSECONDS_PER_SECOND,
        "bvp_median_delta_seconds": median_delta_ns / NANOSECONDS_PER_SECOND,
        "bvp_implied_rate_hz": implied_rate_hz,
        "bvp_flat_difference_fraction": flat_differences / valid_differences
        if valid_differences
        else float("nan"),
        "bvp_minimum": global_min if finite_rows else float("nan"),
        "bvp_maximum": global_max if finite_rows else float("nan"),
        "bvp_extrema_fraction": extrema_count / finite_rows
        if finite_rows
        else float("nan"),
        "bvp_constant_signal": bool(finite_rows and global_min == global_max),
        "valid_short_windows": len(window_starts),
        "window_std_median": float(np.median(window_std)) if window_std else float("nan"),
        "window_std_q05": float(np.quantile(window_std, 0.05)) if window_std else float("nan"),
        "window_flat_fraction_q95": float(np.quantile(window_flat_fraction, 0.95))
        if window_flat_fraction
        else float("nan"),
    }
    return BvpAudit(fields, tuple(spans), tuple(window_starts), tuple(window_ends))


def load_cgm(path: Path, maximum_gap_minutes: float) -> CgmAudit:
    """Load Dexcom EGV rows while preserving all data-quality anomalies."""

    source = pd.read_csv(path, low_memory=False)
    egv = source.loc[source["Event Type"] == "EGV", [CGM_TIMESTAMP, CGM_GLUCOSE]].copy()
    egv["timestamp"] = pd.to_datetime(egv[CGM_TIMESTAMP], errors="coerce")
    egv["glucose_mg_dl"] = pd.to_numeric(egv[CGM_GLUCOSE], errors="coerce")
    invalid_timestamp = int(egv["timestamp"].isna().sum())
    invalid_glucose = int(egv["glucose_mg_dl"].isna().sum())
    valid = egv.dropna(subset=["timestamp", "glucose_mg_dl"]).copy()
    original_times = timestamps_to_ns(valid["timestamp"])
    original_deltas = np.diff(original_times)
    backwards = int(np.sum(original_deltas < 0))
    duplicate_rows = int(valid["timestamp"].duplicated(keep="first").sum())
    frame = valid.sort_values("timestamp").drop_duplicates(subset="timestamp", keep="first")
    frame = frame.reset_index(drop=True)
    timestamps_ns = timestamps_to_ns(frame["timestamp"])
    deltas_minutes = np.diff(timestamps_ns) / (60 * NANOSECONDS_PER_SECOND)
    spans = continuous_spans(
        timestamps_ns, round(maximum_gap_minutes * 60 * NANOSECONDS_PER_SECOND)
    )
    fields = {
        "cgm_source_rows": len(source),
        "cgm_egv_rows": len(egv),
        "cgm_invalid_timestamp_rows": invalid_timestamp,
        "cgm_invalid_glucose_rows": invalid_glucose,
        "cgm_duplicate_timestamp_rows": duplicate_rows,
        "cgm_backwards_timestamp_pairs": backwards,
        "cgm_gap_count": int(np.sum(deltas_minutes > maximum_gap_minutes)),
        "cgm_median_gap_minutes": float(np.median(deltas_minutes))
        if deltas_minutes.size
        else float("nan"),
        "cgm_q95_gap_minutes": float(np.quantile(deltas_minutes, 0.95))
        if deltas_minutes.size
        else float("nan"),
        "cgm_maximum_gap_minutes": float(deltas_minutes.max())
        if deltas_minutes.size
        else float("nan"),
    }
    return CgmAudit(frame[["timestamp", "glucose_mg_dl"]], spans, fields)


def smooth_glucose(values: pd.Series, method: str) -> pd.Series:
    if method == "none":
        return values.astype(float)
    if method == "median3":
        return values.rolling(3, min_periods=1).median()
    if method == "mean3":
        return values.rolling(3, min_periods=1).mean()
    raise ValueError(f"Unsupported smoothing method: {method}")


def generate_recent_trend_slopes(
    cgm: pd.DataFrame,
    bvp_spans: Sequence[TimeSpan],
    *,
    history_minutes: int,
    smoothing: str,
    minimum_support_fraction: float,
    maximum_gap_minutes: float,
    slope_method: str = "ols",
) -> pd.DataFrame:
    """Generate causal candidate slopes using observations at or before each endpoint."""

    timestamps_ns = timestamps_to_ns(cgm["timestamp"])
    smoothed = smooth_glucose(cgm["glucose_mg_dl"], smoothing).to_numpy(dtype=float)
    history_ns = history_minutes * 60 * NANOSECONDS_PER_SECOND
    expected_points = history_minutes / 5 + 1
    minimum_points = math.ceil(expected_points * minimum_support_fraction)
    maximum_gap_ns = maximum_gap_minutes * 60 * NANOSECONDS_PER_SECOND
    rows: list[dict[str, Any]] = []
    left = 0
    for right, endpoint_ns in enumerate(timestamps_ns):
        start_ns = endpoint_ns - history_ns
        while left <= right and timestamps_ns[left] < start_ns:
            left += 1
        window_times = timestamps_ns[left : right + 1]
        if window_times.size < minimum_points:
            continue
        if window_times[0] > start_ns + maximum_gap_ns:
            continue
        if np.any(np.diff(window_times) > maximum_gap_ns):
            continue
        if not span_covers(bvp_spans, start_ns, int(endpoint_ns)):
            continue
        minutes = (window_times - endpoint_ns) / (60 * NANOSECONDS_PER_SECOND)
        window_values = smoothed[left : right + 1]
        if slope_method == "ols":
            slope = float(np.polyfit(minutes, window_values, 1)[0])
        elif slope_method == "endpoint_delta":
            elapsed = float(minutes[-1] - minutes[0])
            if elapsed <= 0:
                continue
            slope = float((window_values[-1] - window_values[0]) / elapsed)
        elif slope_method == "theil_sen":
            slope = float(theilslopes(window_values, minutes).slope)
        else:
            raise ValueError(f"Unsupported slope method: {slope_method}")
        rows.append(
            {
                "timestamp": pd.Timestamp(endpoint_ns),
                "history_start": pd.Timestamp(start_ns),
                "slope_mg_dl_min": slope,
                "support_points": int(window_times.size),
                "slope_method": slope_method,
            }
        )
    return pd.DataFrame.from_records(
        rows,
        columns=[
            "timestamp",
            "history_start",
            "slope_mg_dl_min",
            "support_points",
            "slope_method",
        ],
    )


def classify_trend_slopes(slopes: pd.DataFrame, threshold_mg_dl_min: float) -> pd.DataFrame:
    """Classify already-computed causal slopes for one sensitivity threshold."""

    labels = slopes.copy()
    values = labels["slope_mg_dl_min"].to_numpy(dtype=float)
    labels["label"] = np.where(
        values < -threshold_mg_dl_min,
        "FALLING",
        np.where(values > threshold_mg_dl_min, "RISING", "STABLE"),
    )
    return labels


def generate_recent_trend_labels(
    cgm: pd.DataFrame,
    bvp_spans: Sequence[TimeSpan],
    *,
    history_minutes: int,
    threshold_mg_dl_min: float,
    smoothing: str,
    minimum_support_fraction: float,
    maximum_gap_minutes: float,
    slope_method: str = "ols",
) -> pd.DataFrame:
    """Generate causal candidate labels for one threshold."""

    slopes = generate_recent_trend_slopes(
        cgm,
        bvp_spans,
        history_minutes=history_minutes,
        smoothing=smoothing,
        minimum_support_fraction=minimum_support_fraction,
        maximum_gap_minutes=maximum_gap_minutes,
        slope_method=slope_method,
    )
    return classify_trend_slopes(slopes, threshold_mg_dl_min)


def summarize_candidate_support(candidates: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Keep window totals distinct from the number of supporting participants."""

    grouping = ["history_minutes", "threshold_mg_dl_min", "smoothing", "slope_method"]
    totals = (
        candidates.groupby(grouping)[["falling", "stable", "rising", "eligible_endpoints"]]
        .sum()
        .reset_index()
    )
    participant_support = (
        candidates.assign(
            falling_supported=candidates["falling"] > 0,
            stable_supported=candidates["stable"] > 0,
            rising_supported=candidates["rising"] > 0,
        )
        .groupby(grouping)[
            ["falling_supported", "stable_supported", "rising_supported"]
        ]
        .sum()
        .reset_index()
    )
    return totals, participant_support


def audit_bigideas(
    dataset_root: Path,
    config: Mapping[str, Any],
    integrity: Mapping[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Run all participant audits and candidate Trend support analyses."""

    participant_rows: list[dict[str, Any]] = []
    candidate_rows: list[dict[str, Any]] = []
    participant_count = int(config["expected_participants"])
    for number in range(1, participant_count + 1):
        participant_id = f"{number:03d}"
        bvp_source, cgm_source = participant_source_paths(participant_id)
        bvp = audit_bvp_csv(
            dataset_root / bvp_source,
            rate_hz=int(config["bvp_rate_hz"]),
            window_seconds=int(config["short_window_seconds"]),
            maximum_gap_seconds=float(config["maximum_bvp_gap_seconds"]),
        )
        cgm_audit = load_cgm(
            dataset_root / cgm_source,
            float(config["maximum_cgm_gap_minutes"]),
        )
        cgm = cgm_audit.frame
        cgm_spans = cgm_audit.spans
        row = dict(bvp.fields)
        row.update(cgm_audit.fields)
        aligned_windows = [
            TimeSpan(start, end)
            for start, end in zip(
                bvp.valid_window_starts_ns,
                bvp.valid_window_ends_ns,
                strict=True,
            )
            if span_covers(cgm_spans, start, end)
        ]
        unique_aligned_windows = merge_time_spans(aligned_windows)
        row.update(
            {
                "participant_id": participant_id,
                "dataset": str(config["dataset"]),
                "bvp_source_file": bvp_source,
                "cgm_source_file": cgm_source,
                "cgm_points": len(cgm),
                "cgm_start": cgm["timestamp"].min().isoformat(),
                "cgm_end": cgm["timestamp"].max().isoformat(),
                "cgm_duration_hours": (
                    cgm["timestamp"].max() - cgm["timestamp"].min()
                ).total_seconds()
                / 3600,
                "glucose_minimum_mg_dl": float(cgm["glucose_mg_dl"].min()),
                "glucose_median_mg_dl": float(cgm["glucose_mg_dl"].median()),
                "glucose_maximum_mg_dl": float(cgm["glucose_mg_dl"].max()),
                "overlap_hours": intersect_duration_ns(bvp.spans, cgm_spans)
                / NANOSECONDS_PER_SECOND
                / 3600,
                "valid_aligned_short_windows": sum(
                    1 for _ in aligned_windows
                ),
            }
        )
        row["usable_aligned_hours"] = sum(
            span.end_ns - span.start_ns for span in unique_aligned_windows
        ) / (NANOSECONDS_PER_SECOND * 3600)
        participant_rows.append(row)

        protocols = config["candidate_trend_protocols"]
        for history in protocols["history_minutes"]:
            for smoothing in protocols["smoothing"]:
                for slope_method in protocols["slope_method"]:
                    slopes = generate_recent_trend_slopes(
                        cgm,
                        bvp.spans,
                        history_minutes=int(history),
                        smoothing=str(smoothing),
                        minimum_support_fraction=float(
                            config["minimum_cgm_support_fraction"]
                        ),
                        maximum_gap_minutes=float(config["maximum_cgm_gap_minutes"]),
                        slope_method=str(slope_method),
                    )
                    for threshold in protocols["slope_threshold_mg_dl_min"]:
                        labels = classify_trend_slopes(slopes, float(threshold))
                        counts = (
                            labels["label"].value_counts()
                            if not labels.empty
                            else pd.Series(dtype=int)
                        )
                        temporal: dict[str, Any] = {}
                        for label in ("FALLING", "STABLE", "RISING"):
                            label_times = labels.loc[labels["label"] == label, "timestamp"]
                            prefix = label.lower()
                            temporal[f"{prefix}_first_timestamp"] = (
                                label_times.min().isoformat() if not label_times.empty else None
                            )
                            temporal[f"{prefix}_last_timestamp"] = (
                                label_times.max().isoformat() if not label_times.empty else None
                            )
                            temporal[f"{prefix}_active_dates"] = (
                                int(label_times.dt.date.nunique()) if not label_times.empty else 0
                            )
                        candidate_rows.append(
                            {
                                "dataset": str(config["dataset"]),
                                "participant_id": participant_id,
                                "bvp_source_file": bvp_source,
                                "cgm_source_file": cgm_source,
                                "history_minutes": int(history),
                                "threshold_mg_dl_min": float(threshold),
                                "smoothing": str(smoothing),
                                "slope_method": str(slope_method),
                                "eligible_endpoints": len(labels),
                                "falling": int(counts.get("FALLING", 0)),
                                "stable": int(counts.get("STABLE", 0)),
                                "rising": int(counts.get("RISING", 0)),
                                **temporal,
                            }
                        )

    participants = pd.DataFrame.from_records(participant_rows)
    candidates = pd.DataFrame.from_records(candidate_rows)
    support, participant_support = summarize_candidate_support(candidates)
    summary = {
        "schema_version": 1,
        "dataset": str(config["dataset"]),
        "source_integrity": dict(integrity),
        "participants": len(participants),
        "participant_totals": {
            "bvp_rows": int(participants["bvp_rows"].sum()),
            "cgm_points": int(participants["cgm_points"].sum()),
            "valid_short_windows": int(participants["valid_short_windows"].sum()),
            "overlap_hours": float(participants["overlap_hours"].sum()),
            "usable_aligned_hours": float(participants["usable_aligned_hours"].sum()),
        },
        "anomalies": {
            "bvp_duplicate_timestamps": int(participants["bvp_duplicate_timestamps"].sum()),
            "bvp_backwards_timestamps": int(participants["bvp_backwards_timestamps"].sum()),
            "bvp_gap_count": int(participants["bvp_gap_count"].sum()),
            "bvp_constant_signals": int(participants["bvp_constant_signal"].sum()),
            "cgm_invalid_timestamp_rows": int(
                participants["cgm_invalid_timestamp_rows"].sum()
            ),
            "cgm_invalid_glucose_rows": int(participants["cgm_invalid_glucose_rows"].sum()),
            "cgm_duplicate_timestamp_rows": int(
                participants["cgm_duplicate_timestamp_rows"].sum()
            ),
            "cgm_backwards_timestamp_pairs": int(
                participants["cgm_backwards_timestamp_pairs"].sum()
            ),
            "cgm_gap_count": int(participants["cgm_gap_count"].sum()),
        },
        "candidate_protocol_totals": json.loads(support.to_json(orient="records")),
        "candidate_protocol_participant_support": json.loads(
            participant_support.to_json(orient="records")
        ),
    }
    return participants, candidates, summary


def write_bigideas_artifacts(
    participants: pd.DataFrame,
    candidates: pd.DataFrame,
    summary: Mapping[str, Any],
    reports_root: Path,
) -> None:
    """Write compact audit artifacts without dumping execution logs."""

    audits = reports_root / "audits"
    audits.mkdir(parents=True, exist_ok=True)
    participants.to_csv(audits / "bigideas_participants.csv", index=False)
    candidates.to_csv(audits / "bigideas_trend_candidates.csv", index=False)
    (audits / "bigideas_audit.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    totals = summary["participant_totals"]
    integrity = summary["source_integrity"]
    anomalies = summary["anomalies"]
    bvp_timestamp_anomalies = (
        f"{anomalies['bvp_duplicate_timestamps']} / "
        f"{anomalies['bvp_backwards_timestamps']}"
    )
    invalid_cgm_rows = (
        f"{anomalies['cgm_invalid_timestamp_rows']} / "
        f"{anomalies['cgm_invalid_glucose_rows']}"
    )
    cgm_timestamp_anomalies = (
        f"{anomalies['cgm_duplicate_timestamp_rows']} / "
        f"{anomalies['cgm_backwards_timestamp_pairs']}"
    )
    verdict = (
        f"All {integrity['verified_files']} official files passed their published SHA-256 "
        f"digests. The audit accounted for {summary['participants']} participants. This "
        "report does not freeze a Trend label or chronological split."
    )
    report = f"""# BIG IDEAs v1.1.3 Raw-Data Audit

## Verdict

{verdict}

## Coverage

- BVP rows: {totals['bvp_rows']}
- Numeric CGM EGV points: {totals['cgm_points']}
- Contiguous non-overlapping 30-second BVP windows: {totals['valid_short_windows']}
- Total BVP-CGM continuous overlap: {totals['overlap_hours']:.2f} hours
- Usable aligned 30-second window-hours: {totals['usable_aligned_hours']:.2f} hours
- Participant-level details: `bigideas_participants.csv`

## Explicit anomalies

- BVP duplicate / backward timestamps: {bvp_timestamp_anomalies}
- BVP gaps over policy: {anomalies['bvp_gap_count']}
- Constant BVP recordings: {anomalies['bvp_constant_signals']}
- Invalid CGM timestamp / glucose rows: {invalid_cgm_rows}
- CGM duplicate / backward timestamps: {cgm_timestamp_anomalies}
- CGM gaps over policy: {anomalies['cgm_gap_count']}

## Candidate Trend sensitivity

The complete H / threshold / smoothing grid is in `bigideas_trend_candidates.csv`. Counts are
reported by participant and must not be interpreted as independent-human counts. Every candidate
endpoint uses only past and present CGM and requires continuous BVP history.

## Gate consequence

This audit supplies evidence for human review. It does not authorize label freeze, split creation,
architecture selection, model training, or final-test access.
"""
    (audits / "bigideas_audit.md").write_text(report, encoding="utf-8")
