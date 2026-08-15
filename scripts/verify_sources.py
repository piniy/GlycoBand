"""Verify official GlycoBand data sources and calculate the storage gate."""

from __future__ import annotations

from pathlib import Path

from glycoband.datasets.source_verification import build_source_manifest, write_source_manifest


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    manifest = build_source_manifest(repo_root, repo_root / "configs/data_sources.yaml")
    output = repo_root / "data/manifests/source_manifest.json"
    write_source_manifest(manifest, output)
    return 0 if manifest["source_gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
