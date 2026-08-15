import json
from pathlib import Path

import pytest

from glycoband.utils.ranged_download import (
    _load_progress,
    _write_progress,
    parse_content_range,
    plan_ranges,
)


def test_plan_ranges_covers_file_without_gaps() -> None:
    ranges = plan_ranges(total_bytes=10, chunk_bytes=4)

    assert [(item.index, item.start, item.end, item.size) for item in ranges] == [
        (0, 0, 3, 4),
        (1, 4, 7, 4),
        (2, 8, 9, 2),
    ]


@pytest.mark.parametrize("total_bytes,chunk_bytes", [(0, 1), (1, 0), (-1, 2)])
def test_plan_ranges_rejects_nonpositive_sizes(total_bytes: int, chunk_bytes: int) -> None:
    with pytest.raises(ValueError):
        plan_ranges(total_bytes, chunk_bytes)


def test_parse_content_range() -> None:
    assert parse_content_range("bytes 10-19/100") == (10, 19, 100)


@pytest.mark.parametrize(
    "value",
    ["bytes */100", "10-19/100", "bytes 20-10/100", "bytes 10-100/100"],
)
def test_parse_content_range_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        parse_content_range(value)


def test_progress_binds_url_size_and_range_plan(tmp_path: Path) -> None:
    path = tmp_path / "progress.json"
    _write_progress(
        path,
        url="https://example.test/data",
        expected_bytes=100,
        chunk_bytes=10,
        completed={1, 3},
    )
    assert _load_progress(
        path,
        url="https://example.test/data",
        expected_bytes=100,
        chunk_bytes=10,
    ) == {1, 3}
    with pytest.raises(ValueError, match="range size"):
        _load_progress(
            path,
            url="https://example.test/data",
            expected_bytes=100,
            chunk_bytes=20,
        )


def test_progress_rejects_legacy_schema(tmp_path: Path) -> None:
    path = tmp_path / "progress.json"
    path.write_text(json.dumps({"schema_version": 1, "completed_ranges": [0]}))
    with pytest.raises(ValueError, match="Unsupported progress schema"):
        _load_progress(path, url="https://example.test/data", expected_bytes=1, chunk_bytes=1)
