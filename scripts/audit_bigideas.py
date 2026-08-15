"""Verify, extract, and audit BIG IDEAs v1.1.3."""

from __future__ import annotations

import json
from pathlib import Path

from glycoband.datasets.bigideas import (
    audit_bigideas,
    extract_and_verify_archive,
    load_config,
    verify_archive_membership,
    verify_extracted_files,
    verify_manifest_anchor,
    write_bigideas_artifacts,
)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    raw_root = repo_root / "data/raw/bigideas"
    archive = raw_root / "big-ideas-glycemic-wearable-1.1.3.zip"
    manifest = raw_root / "SHA256SUMS.txt"
    extracted = raw_root / "v1.1.3"
    integrity_path = repo_root / "data/manifests/bigideas_extraction_integrity.json"
    config = load_config(repo_root / "configs/audits/bigideas.yaml")
    manifest_anchor = verify_manifest_anchor(
        manifest,
        str(config["official_manifest_sha256"]),
        int(config["official_manifest_entries"]),
    )
    archive_membership = verify_archive_membership(archive, manifest)
    if not archive_membership["exact_archive_membership"]:
        raise RuntimeError("BIG IDEAs archive membership differs from the official manifest")
    integrity = verify_extracted_files(extracted, manifest)
    if not integrity["all_official_files_verified"]:
        extract_and_verify_archive(archive, extracted, manifest)
        integrity = verify_extracted_files(extracted, manifest)
    integrity["archive_membership"] = archive_membership
    integrity["manifest_anchor"] = manifest_anchor
    integrity["integrity_pass"] = bool(
        integrity["all_official_files_verified"]
        and integrity["exact_destination_membership"]
        and archive_membership["exact_archive_membership"]
        and manifest_anchor["anchor_verified"]
    )
    integrity_path.write_text(json.dumps(integrity, indent=2) + "\n", encoding="utf-8")
    if not integrity["integrity_pass"]:
        raise RuntimeError("BIG IDEAs source integrity did not pass")
    participants, candidates, summary = audit_bigideas(extracted, config, integrity)
    write_bigideas_artifacts(participants, candidates, summary, repo_root / "reports")
    print(
        "BIG IDEAs audit complete: "
        f"{summary['participants']} participants, "
        f"{summary['participant_totals']['overlap_hours']:.2f} overlap hours"
    )


if __name__ == "__main__":
    main()
