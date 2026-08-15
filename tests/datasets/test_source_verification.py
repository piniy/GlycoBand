from pathlib import Path

import pytest

from glycoband.datasets.source_verification import (
    calculate_storage_budget,
    hash_file,
    parse_sha256_manifest,
    ranged_checkpoint_bytes,
)


def test_hash_file_supports_declared_md5(tmp_path: Path) -> None:
    sample = tmp_path / "source.bin"
    sample.write_bytes(b"glycoband\n")

    assert hash_file(sample, "md5") == "268fe53fe10e9305a836afdc9ee51d4b"


def test_parse_sha256_manifest() -> None:
    checksum = "a" * 64

    assert parse_sha256_manifest(f"{checksum} 001/BVP_001.csv\n") == {
        "001/BVP_001.csv": checksum
    }


@pytest.mark.parametrize(
    "text",
    ["", "not-a-checksum file.csv", f"{'a' * 64} duplicate.csv\n{'b' * 64} duplicate.csv\n"],
)
def test_parse_sha256_manifest_rejects_invalid_input(text: str) -> None:
    with pytest.raises(ValueError):
        parse_sha256_manifest(text)


def test_storage_budget_passes_with_positive_headroom() -> None:
    result = calculate_storage_budget(
        archive_bytes=5_000,
        uncompressed_bytes=34_000,
        reserve_bytes=10_000,
        current_free_bytes=60_000,
        already_acquired_bytes=1_000,
    )

    assert result["gate"] == "PASS"
    assert result["remaining_required_bytes"] == 48_000
    assert result["headroom_after_acquisition_bytes"] == 12_000


def test_storage_budget_fails_when_remaining_bytes_do_not_fit() -> None:
    result = calculate_storage_budget(
        archive_bytes=5_000,
        uncompressed_bytes=34_000,
        reserve_bytes=10_000,
        current_free_bytes=40_000,
        already_acquired_bytes=0,
    )

    assert result["gate"] == "NO_GO"
    assert result["headroom_after_acquisition_bytes"] == -9_000


def test_ranged_checkpoint_counts_only_completed_ranges(tmp_path: Path) -> None:
    progress = tmp_path / "archive.zip.ranges.json"
    progress.write_text(
        '{"schema_version":2,"expected_bytes":25,"chunk_bytes":10,'
        '"completed_ranges":[0,2]}',
        encoding="utf-8",
    )
    assert ranged_checkpoint_bytes(progress, 25) == 15


def test_ranged_checkpoint_rejects_wrong_source_size(tmp_path: Path) -> None:
    progress = tmp_path / "archive.zip.ranges.json"
    progress.write_text(
        '{"schema_version":2,"expected_bytes":25,"chunk_bytes":10,'
        '"completed_ranges":[0]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="source contract"):
        ranged_checkpoint_bytes(progress, 26)
