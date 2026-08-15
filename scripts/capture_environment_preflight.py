"""Capture Gate A environment evidence for GlycoBand."""

from __future__ import annotations

import argparse
from pathlib import Path

from glycoband.utils.preflight import collect_preflight, write_preflight


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/audits/environment_preflight.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    report = collect_preflight(repo_root)
    write_preflight(report, repo_root / args.output)
    return 0 if report["environment_gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
