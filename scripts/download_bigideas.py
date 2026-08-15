"""Download the verified BIG IDEAs v1.1.3 ZIP with resumable parallel ranges."""

from __future__ import annotations

import argparse
from pathlib import Path

from glycoband.utils.ranged_download import download_ranges

URL = "https://physionet.org/content/big-ideas-glycemic-wearable/get-zip/1.1.3/"
EXPECTED_BYTES = 5_015_250_233


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=32)
    parser.add_argument("--chunk-mib", type=int, default=8)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    output = repo_root / "data/raw/bigideas/big-ideas-glycemic-wearable-1.1.3.zip"
    download_ranges(
        URL,
        output,
        EXPECTED_BYTES,
        workers=args.workers,
        chunk_bytes=args.chunk_mib * 1024 * 1024,
    )


if __name__ == "__main__":
    main()
