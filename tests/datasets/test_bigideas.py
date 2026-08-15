from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from glycoband.datasets.bigideas import (
    NANOSECONDS_PER_SECOND,
    TimeSpan,
    audit_bvp_csv,
    extract_and_verify_archive,
    generate_recent_trend_labels,
    intersect_duration_ns,
    load_cgm,
    match_archive_members,
    parse_sha256_manifest,
    participant_source_paths,
    summarize_candidate_support,
    verify_extracted_files,
    verify_manifest_anchor,
)


def test_parse_manifest_rejects_duplicate_paths(tmp_path: Path) -> None:
    digest = "a" * 64
    path = tmp_path / "SHA256SUMS.txt"
    path.write_text(f"{digest}  001/BVP_001.csv\n{digest}  001/BVP_001.csv\n")
    try:
        parse_sha256_manifest(path)
    except ValueError as error:
        assert "Duplicate" in str(error)
    else:
        raise AssertionError("Expected duplicate manifest path to fail")


def test_parse_manifest_accepts_official_single_space_format(tmp_path: Path) -> None:
    digest = "a" * 64
    path = tmp_path / "SHA256SUMS.txt"
    path.write_text(f"{digest} 001/BVP_001.csv\n")
    assert parse_sha256_manifest(path) == {"001/BVP_001.csv": digest}


def test_archive_member_matching_allows_one_root_folder() -> None:
    matched, unexpected = match_archive_members(
        ["dataset/001/BVP_001.csv", "dataset/SHA256SUMS.txt"], ["001/BVP_001.csv"]
    )
    assert matched == {"001/BVP_001.csv": "dataset/001/BVP_001.csv"}
    assert unexpected == []


def test_manifest_anchor_rejects_modified_manifest(tmp_path: Path) -> None:
    path = tmp_path / "SHA256SUMS.txt"
    path.write_text(f"{'a' * 64}  001/BVP_001.csv\n")
    observed = hashlib.sha256(path.read_bytes()).hexdigest()
    assert verify_manifest_anchor(path, observed, 1)["anchor_verified"] is True
    with np.testing.assert_raises_regex(ValueError, "digest"):
        verify_manifest_anchor(path, "b" * 64, 1)


def test_participant_source_paths_are_portable_and_validate_identity() -> None:
    assert participant_source_paths("001") == ("001/BVP_001.csv", "001/Dexcom_001.csv")
    with np.testing.assert_raises_regex(ValueError, "participant ID"):
        participant_source_paths("1")


def test_extract_verifies_each_official_file(tmp_path: Path) -> None:
    content = b"datetime,bvp\n2020-01-01,0\n"
    digest = hashlib.sha256(content).hexdigest()
    manifest = tmp_path / "SHA256SUMS.txt"
    manifest.write_text(f"{digest}  001/BVP_001.csv\n")
    archive_path = tmp_path / "data.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("root/001/BVP_001.csv", content)
    result = extract_and_verify_archive(archive_path, tmp_path / "out", manifest)
    assert result["all_official_files_verified"] is True
    assert (tmp_path / "out/001/BVP_001.csv").read_bytes() == content


def test_verify_extracted_files_reports_unexpected_destination_file(tmp_path: Path) -> None:
    content = b"official"
    digest = hashlib.sha256(content).hexdigest()
    manifest = tmp_path / "SHA256SUMS.txt"
    manifest.write_text(f"{digest}  001/BVP_001.csv\n")
    destination = tmp_path / "out"
    (destination / "001").mkdir(parents=True)
    (destination / "001/BVP_001.csv").write_bytes(content)
    (destination / "unexpected.csv").write_text("extra")
    result = verify_extracted_files(destination, manifest)
    assert result["all_official_files_verified"] is True
    assert result["exact_destination_membership"] is False
    assert result["unexpected_extracted_files"] == ["unexpected.csv"]


def test_intersection_does_not_bridge_gaps() -> None:
    left = [TimeSpan(0, 10), TimeSpan(20, 30)]
    right = [TimeSpan(5, 25)]
    assert intersect_duration_ns(left, right) == 10


def test_recent_trend_uses_no_future_points() -> None:
    timestamps = pd.date_range("2020-01-01", periods=8, freq="5min")
    base = pd.DataFrame({"timestamp": timestamps, "glucose_mg_dl": np.arange(8) * 10 + 80})
    span = [
        TimeSpan(
            int(timestamps[0].value - 60 * 60 * NANOSECONDS_PER_SECOND),
            int(timestamps[-1].value),
        )
    ]
    original = generate_recent_trend_labels(
        base,
        span,
        history_minutes=15,
        threshold_mg_dl_min=0.5,
        smoothing="none",
        minimum_support_fraction=0.8,
        maximum_gap_minutes=10,
    )
    changed = base.copy()
    changed.loc[changed.index[-1], "glucose_mg_dl"] = -999
    modified = generate_recent_trend_labels(
        changed,
        span,
        history_minutes=15,
        threshold_mg_dl_min=0.5,
        smoothing="none",
        minimum_support_fraction=0.8,
        maximum_gap_minutes=10,
    )
    cutoff = timestamps[-2]
    pd.testing.assert_frame_equal(
        original.loc[original["timestamp"] <= cutoff].reset_index(drop=True),
        modified.loc[modified["timestamp"] <= cutoff].reset_index(drop=True),
    )


def test_bvp_audit_streams_across_chunk_boundaries(tmp_path: Path) -> None:
    timestamps = pd.date_range("2020-01-01", periods=128, freq="15625us")
    frame = pd.DataFrame({"datetime": timestamps, " bvp": np.sin(np.linspace(0, 4, 128))})
    path = tmp_path / "BVP.csv"
    frame.to_csv(path, index=False)
    result = audit_bvp_csv(
        path,
        rate_hz=64,
        window_seconds=1,
        maximum_gap_seconds=0.03125,
        chunksize=50,
    )
    assert result.fields["bvp_rows"] == 128
    assert result.fields["valid_short_windows"] == 2
    assert result.fields["bvp_gap_count"] == 0
    assert result.fields["bvp_implied_rate_hz"] == 64.0


def test_bvp_duplicate_timestamps_and_constant_values_are_explicit(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        {
            "datetime": ["2020-01-01 00:00:00"] * 64,
            " bvp": [2.0] * 64,
        }
    )
    path = tmp_path / "BVP.csv"
    frame.to_csv(path, index=False)
    result = audit_bvp_csv(
        path,
        rate_hz=64,
        window_seconds=1,
        maximum_gap_seconds=0.03125,
        chunksize=20,
    )
    assert result.fields["bvp_duplicate_timestamps"] == 63
    assert np.isnan(result.fields["bvp_implied_rate_hz"])
    assert result.fields["bvp_constant_signal"] is True
    assert result.fields["bvp_extrema_fraction"] == 1.0


def test_cgm_audit_records_anomalies_before_cleaning(tmp_path: Path) -> None:
    path = tmp_path / "Dexcom.csv"
    path.write_text(
        "Event Type,Timestamp (YYYY-MM-DDThh:mm:ss),Glucose Value (mg/dL)\n"
        "EGV,2020-01-01 00:05:00,100\n"
        "EGV,2020-01-01 00:00:00,90\n"
        "EGV,2020-01-01 00:00:00,91\n"
        "EGV,invalid,92\n"
        "EGV,2020-01-01 00:10:00,invalid\n",
        encoding="utf-8",
    )
    audit = load_cgm(path, maximum_gap_minutes=10)
    assert len(audit.frame) == 2
    assert audit.fields["cgm_duplicate_timestamp_rows"] == 1
    assert audit.fields["cgm_backwards_timestamp_pairs"] == 1
    assert audit.fields["cgm_invalid_timestamp_rows"] == 1
    assert audit.fields["cgm_invalid_glucose_rows"] == 1


def test_all_candidate_slope_methods_use_only_history() -> None:
    timestamps = pd.date_range("2020-01-01", periods=8, freq="5min")
    cgm = pd.DataFrame({"timestamp": timestamps, "glucose_mg_dl": np.arange(8) * 5 + 80})
    spans = [TimeSpan(int(timestamps[0].value), int(timestamps[-1].value))]
    for method in ("ols", "endpoint_delta", "theil_sen"):
        labels = generate_recent_trend_labels(
            cgm,
            spans,
            history_minutes=15,
            threshold_mg_dl_min=0.5,
            smoothing="none",
            minimum_support_fraction=0.8,
            maximum_gap_minutes=10,
            slope_method=method,
        )
        assert set(labels["slope_method"]) == {method}
        assert set(labels["label"]) == {"RISING"}


def test_candidate_support_separates_windows_from_people() -> None:
    candidates = pd.DataFrame(
        [
            {
                "participant_id": "001",
                "history_minutes": 15,
                "threshold_mg_dl_min": 1.0,
                "smoothing": "none",
                "slope_method": "ols",
                "falling": 100,
                "stable": 0,
                "rising": 0,
                "eligible_endpoints": 100,
            },
            {
                "participant_id": "002",
                "history_minutes": 15,
                "threshold_mg_dl_min": 1.0,
                "smoothing": "none",
                "slope_method": "ols",
                "falling": 1,
                "stable": 1,
                "rising": 1,
                "eligible_endpoints": 3,
            },
        ]
    )
    totals, people = summarize_candidate_support(candidates)
    assert totals.loc[0, "falling"] == 101
    assert people.loc[0, "falling_supported"] == 2
    assert people.loc[0, "stable_supported"] == 1
