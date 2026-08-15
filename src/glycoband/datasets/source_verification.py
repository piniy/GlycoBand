"""Verify configured source identity and calculate acquisition storage budget."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

SHA256_LINE = re.compile(r"^([0-9a-f]{64})\s+(.+)$")


def hash_file(path: Path, algorithm: str) -> str:
    """Hash a file with a supported hashlib algorithm."""

    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_sha256_manifest(text: str) -> dict[str, str]:
    """Parse the PhysioNet checksum manifest and reject malformed lines."""

    entries: dict[str, str] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        match = SHA256_LINE.fullmatch(line)
        if match is None:
            raise ValueError(f"Malformed SHA256 line {line_number}: {raw_line!r}")
        checksum, relative_path = match.groups()
        if relative_path in entries:
            raise ValueError(f"Duplicate checksum path: {relative_path}")
        entries[relative_path] = checksum
    if not entries:
        raise ValueError("SHA256 manifest is empty")
    return entries


def calculate_storage_budget(
    archive_bytes: int,
    uncompressed_bytes: int,
    reserve_bytes: int,
    current_free_bytes: int,
    already_acquired_bytes: int,
) -> dict[str, int | str]:
    """Calculate whether remaining acquisition fits on the current data volume."""

    total_required = archive_bytes + uncompressed_bytes + reserve_bytes
    remaining_required = max(total_required - already_acquired_bytes, 0)
    headroom = current_free_bytes - remaining_required
    return {
        "archive_bytes": archive_bytes,
        "uncompressed_bytes": uncompressed_bytes,
        "working_reserve_bytes": reserve_bytes,
        "total_required_bytes": total_required,
        "already_acquired_bytes": already_acquired_bytes,
        "remaining_required_bytes": remaining_required,
        "current_free_bytes": current_free_bytes,
        "headroom_after_acquisition_bytes": headroom,
        "gate": "PASS" if headroom >= 0 else "NO_GO",
    }


def _load_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected mapping in {path}")
    return loaded


def _request_bytes(url: str, method: str = "GET") -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(url, method=method, headers={"User-Agent": "GlycoBand/0.1"})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        headers = {key.lower(): value for key, value in response.headers.items()}
        return response.read(), headers


def build_source_manifest(repo_root: Path, config_path: Path) -> dict[str, object]:
    """Verify remote metadata and local archives against the configured contracts."""

    root = repo_root.resolve()
    config = _load_yaml(config_path)
    datasets = config["datasets"]
    hb_config = datasets["hbppg"]
    big_config = datasets["bigideas"]

    figshare_bytes, _ = _request_bytes(hb_config["metadata_url"])
    figshare = json.loads(figshare_bytes)
    hb_file = next(
        item for item in figshare["files"] if item["id"] == hb_config["archive"]["file_id"]
    )
    hb_path = root / hb_config["archive"]["local_path"]
    hb_local_exists = hb_path.is_file()
    hb_local_size = hb_path.stat().st_size if hb_local_exists else 0
    hb_local_checksum = (
        hash_file(hb_path, hb_config["archive"]["checksum_algorithm"])
        if hb_local_exists
        else None
    )
    hb_verified = bool(
        figshare["version"] == hb_config["version"]
        and figshare["doi"] == hb_config["doi"]
        and figshare["license"]["name"] == hb_config["license"]
        and hb_file["name"] == hb_config["archive"]["name"]
        and hb_file["size"] == hb_config["archive"]["expected_bytes"]
        and hb_file["computed_md5"] == hb_config["archive"]["expected_checksum"]
        and hb_local_exists
        and hb_local_size == hb_config["archive"]["expected_bytes"]
        and hb_local_checksum == hb_config["archive"]["expected_checksum"]
    )

    _, big_headers = _request_bytes(big_config["archive"]["download_url"], method="HEAD")
    big_remote_bytes = int(big_headers["content-length"])
    checksum_bytes, _ = _request_bytes(big_config["archive"]["checksum_manifest_url"])
    checksum_text = checksum_bytes.decode("utf-8")
    checksum_entries = parse_sha256_manifest(checksum_text)
    license_bytes, _ = _request_bytes(big_config["archive"]["license_file_url"])

    big_path = root / big_config["archive"]["local_path"]
    big_local_exists = big_path.is_file()
    big_local_size = big_path.stat().st_size if big_local_exists else 0
    big_verified = bool(
        big_remote_bytes == big_config["archive"]["expected_bytes"]
        and len(checksum_entries) > 0
        and len(license_bytes) > 0
    )

    archive_bytes = (
        hb_config["archive"]["expected_bytes"] + big_config["archive"]["expected_bytes"]
    )
    uncompressed_bytes = (
        hb_config["archive"]["project_verified_uncompressed_bytes"]
        + big_config["archive"]["reported_uncompressed_bytes"]
    )
    already_acquired = hb_local_size + big_local_size
    free_bytes = shutil.disk_usage(root / "data").free
    storage = calculate_storage_budget(
        archive_bytes,
        uncompressed_bytes,
        config["storage"]["working_reserve_bytes"],
        free_bytes,
        already_acquired,
    )

    source_gate = "PASS" if hb_verified and big_verified and storage["gate"] == "PASS" else "NO_GO"
    return {
        "schema_version": 1,
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "download_authority": {
            "confirmed": True,
            "confirmed_on": "2026-08-15",
            "scope": ["hbppg-v6", "bigideas-v1.1.3"],
        },
        "datasets": {
            "hbppg": {
                "version": hb_config["version"],
                "doi": hb_config["doi"],
                "license": hb_config["license"],
                "remote_archive": {
                    "file_id": hb_file["id"],
                    "name": hb_file["name"],
                    "bytes": hb_file["size"],
                    "md5": hb_file["computed_md5"],
                },
                "local_archive": {
                    "path": hb_config["archive"]["local_path"],
                    "exists": hb_local_exists,
                    "bytes": hb_local_size,
                    "md5": hb_local_checksum,
                },
                "source_status": "VERIFIED" if hb_verified else "NO_GO",
            },
            "bigideas": {
                "version": big_config["version"],
                "doi": big_config["doi"],
                "license": big_config["license"],
                "remote_archive": {
                    "name": big_config["archive"]["name"],
                    "bytes": big_remote_bytes,
                    "official_archive_checksum": None,
                },
                "official_file_checksums": {
                    "algorithm": "sha256",
                    "manifest_url": big_config["archive"]["checksum_manifest_url"],
                    "manifest_sha256": hashlib.sha256(checksum_bytes).hexdigest(),
                    "entry_count": len(checksum_entries),
                },
                "license_file_sha256": hashlib.sha256(license_bytes).hexdigest(),
                "local_archive": {
                    "path": big_config["archive"]["local_path"],
                    "exists": big_local_exists,
                    "bytes": big_local_size,
                    "sha256": hash_file(big_path, "sha256") if big_local_exists else None,
                },
                "source_status": "VERIFIED" if big_verified else "NO_GO",
                "post_extraction_requirement": (
                    "Verify every extracted file against the official SHA256 manifest."
                ),
            },
        },
        "storage": storage,
        "source_gate": source_gate,
    }


def write_source_manifest(manifest: dict[str, object], output_path: Path) -> None:
    """Write source verification evidence as JSON."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
