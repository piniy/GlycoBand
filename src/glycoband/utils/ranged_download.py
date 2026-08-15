"""Resumable concurrent HTTP range download utilities."""

from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.request
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

CONTENT_RANGE = re.compile(r"^bytes (\d+)-(\d+)/(\d+)$")


@dataclass(frozen=True)
class ByteRange:
    """One inclusive byte range in a remote file."""

    index: int
    start: int
    end: int

    @property
    def size(self) -> int:
        return self.end - self.start + 1


def plan_ranges(total_bytes: int, chunk_bytes: int) -> tuple[ByteRange, ...]:
    """Split a positive file size into contiguous inclusive ranges."""

    if total_bytes <= 0:
        raise ValueError("total_bytes must be positive")
    if chunk_bytes <= 0:
        raise ValueError("chunk_bytes must be positive")
    ranges: list[ByteRange] = []
    for index, start in enumerate(range(0, total_bytes, chunk_bytes)):
        end = min(start + chunk_bytes - 1, total_bytes - 1)
        ranges.append(ByteRange(index=index, start=start, end=end))
    return tuple(ranges)


def parse_content_range(value: str) -> tuple[int, int, int]:
    """Parse and validate an HTTP Content-Range header."""

    match = CONTENT_RANGE.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"Invalid Content-Range: {value!r}")
    start, end, total = (int(part) for part in match.groups())
    if start > end or end >= total:
        raise ValueError(f"Impossible Content-Range: {value!r}")
    return start, end, total


def _write_progress(
    path: Path,
    *,
    url: str,
    expected_bytes: int,
    chunk_bytes: int,
    completed: Iterable[int],
) -> None:
    payload = {
        "schema_version": 2,
        "url": url,
        "expected_bytes": expected_bytes,
        "chunk_bytes": chunk_bytes,
        "completed_ranges": sorted(completed),
    }
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _load_progress(path: Path, *, url: str, expected_bytes: int, chunk_bytes: int) -> set[int]:
    if not path.is_file():
        return set()
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 2:
        raise ValueError("Unsupported progress schema; restart without the stale progress file")
    if payload.get("url") != url:
        raise ValueError("Progress file belongs to a different remote URL")
    if payload.get("expected_bytes") != expected_bytes:
        raise ValueError("Progress file belongs to a different remote size")
    if payload.get("chunk_bytes") != chunk_bytes:
        raise ValueError("Progress file uses a different range size")
    completed = payload.get("completed_ranges")
    if not isinstance(completed, list) or not all(isinstance(index, int) for index in completed):
        raise ValueError("Progress file contains invalid range indexes")
    return set(completed)


def download_ranges(
    url: str,
    output_path: Path,
    expected_bytes: int,
    *,
    workers: int = 12,
    chunk_bytes: int = 64 * 1024 * 1024,
    attempts: int = 5,
) -> None:
    """Download a remote file concurrently with resumable range checkpoints."""

    if workers <= 0 or attempts <= 0:
        raise ValueError("workers and attempts must be positive")
    ranges = plan_ranges(expected_bytes, chunk_bytes)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path = output_path.with_suffix(output_path.suffix + ".ranges.json")
    completed = _load_progress(
        progress_path,
        url=url,
        expected_bytes=expected_bytes,
        chunk_bytes=chunk_bytes,
    )

    unknown_indexes = completed.difference(item.index for item in ranges)
    if unknown_indexes:
        raise ValueError(f"Progress file contains unknown ranges: {sorted(unknown_indexes)}")

    if not output_path.exists():
        with output_path.open("wb") as stream:
            stream.truncate(expected_bytes)
    elif output_path.stat().st_size != expected_bytes:
        if completed:
            raise ValueError("Existing output size does not match resumable progress")
        raise ValueError("Existing output is not a ranged-download target; move it before retrying")

    lock = threading.Lock()

    def download_one(byte_range: ByteRange) -> int:
        if byte_range.index in completed:
            return byte_range.index
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            request = urllib.request.Request(
                url,
                headers={
                    "Range": f"bytes={byte_range.start}-{byte_range.end}",
                    "User-Agent": "GlycoBand/0.1",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310
                    if response.status != 206:
                        raise OSError(f"Expected HTTP 206, received {response.status}")
                    header = response.headers.get("Content-Range", "")
                    observed_start, observed_end, observed_total = parse_content_range(header)
                    if (observed_start, observed_end, observed_total) != (
                        byte_range.start,
                        byte_range.end,
                        expected_bytes,
                    ):
                        raise OSError(f"Unexpected Content-Range: {header}")
                    written = 0
                    with output_path.open("r+b", buffering=0) as output:
                        output.seek(byte_range.start)
                        while chunk := response.read(1024 * 1024):
                            output.write(chunk)
                            written += len(chunk)
                    if written != byte_range.size:
                        raise OSError(
                            f"Range {byte_range.index} wrote {written} bytes, "
                            f"expected {byte_range.size}"
                        )
                with lock:
                    completed.add(byte_range.index)
                    _write_progress(
                        progress_path,
                        url=url,
                        expected_bytes=expected_bytes,
                        chunk_bytes=chunk_bytes,
                        completed=completed,
                    )
                    print(f"completed {len(completed)}/{len(ranges)} ranges", flush=True)
                return byte_range.index
            except (OSError, ValueError) as error:
                last_error = error
                if attempt < attempts:
                    time.sleep(min(2**attempt, 20))
        message = f"Range {byte_range.index} failed after {attempts} attempts"
        raise RuntimeError(message) from last_error

    pending = [item for item in ranges if item.index not in completed]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(download_one, item) for item in pending]
        for future in as_completed(futures):
            future.result()

    if len(completed) != len(ranges) or output_path.stat().st_size != expected_bytes:
        raise RuntimeError("Download finished without complete range coverage")
    progress_path.unlink(missing_ok=True)
