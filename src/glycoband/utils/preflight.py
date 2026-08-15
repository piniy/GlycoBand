"""Collect compact, reproducible environment-preflight evidence."""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class CheckSpec:
    """One repository verification command."""

    name: str
    command: tuple[str, ...]


DEFAULT_CHECKS: tuple[CheckSpec, ...] = (
    CheckSpec("sync", ("uv", "sync", "--frozen")),
    CheckSpec("lock", ("uv", "lock", "--check")),
    CheckSpec("tests", ("uv", "run", "--frozen", "pytest", "-q")),
    CheckSpec("lint", ("uv", "run", "--frozen", "ruff", "check", ".")),
    CheckSpec("types", ("uv", "run", "--frozen", "mypy")),
)

CommandRunner = Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]]


def sha256_file(path: Path) -> str:
    """Return the SHA-256 checksum for a file."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def collect_preflight(
    repo_root: Path,
    checks: Sequence[CheckSpec] = DEFAULT_CHECKS,
    runner: CommandRunner = _run,
    source_manifest_path: Path | None = None,
) -> dict[str, object]:
    """Collect environment and verification evidence without exposing secrets."""

    root = repo_root.resolve()
    lock_path = root / "uv.lock"
    if not lock_path.is_file():
        raise FileNotFoundError(f"Missing lockfile: {lock_path}")

    git_commit = runner(("git", "rev-parse", "HEAD"), root)
    git_status = runner(("git", "status", "--porcelain"), root)
    disk = shutil.disk_usage(root / "data")
    resolved_source_manifest = (
        source_manifest_path
        if source_manifest_path is not None
        else root / "data/manifests/source_manifest.json"
    )

    check_results: list[dict[str, object]] = []
    for check in checks:
        result = runner(check.command, root)
        check_results.append(
            {
                "name": check.name,
                "command": list(check.command),
                "passed": result.returncode == 0,
                "return_code": result.returncode,
                "summary": (result.stdout or result.stderr).strip()[-1000:],
            }
        )

    storage: dict[str, object] = {
        "data_volume_total_bytes": disk.total,
        "data_volume_free_bytes": disk.free,
        "required_bytes": None,
        "gate": "DATA_REQUIRED",
        "reason": "Official source sizes and derived-data reserve are not verified yet.",
    }
    source_access: dict[str, object] = {
        "gate": "IN_PROGRESS",
        "reason": "Official source identity and access conditions are handled by Gate B.",
    }
    if resolved_source_manifest.is_file():
        source_manifest = json.loads(resolved_source_manifest.read_text(encoding="utf-8"))
        manifest_storage = source_manifest.get("storage")
        if isinstance(manifest_storage, dict):
            storage = manifest_storage
        try:
            manifest_display_path = str(resolved_source_manifest.relative_to(root))
        except ValueError:
            manifest_display_path = str(resolved_source_manifest)
        source_access = {
            "gate": source_manifest.get("source_gate", "NO_GO"),
            "manifest": manifest_display_path,
        }

    return {
        "schema_version": 1,
        "captured_at_utc": datetime.now(UTC).isoformat(),
        "repository": {
            "commit": git_commit.stdout.strip() if git_commit.returncode == 0 else None,
            "dirty": bool(git_status.stdout.strip()),
        },
        "runtime": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
            "operating_system": platform.platform(),
            "architecture": platform.machine(),
        },
        "lockfile": {
            "path": "uv.lock",
            "sha256": sha256_file(lock_path),
        },
        "storage": storage,
        "source_access": source_access,
        "checks": check_results,
        "environment_gate": "PASS"
        if (
            check_results
            and all(bool(item["passed"]) for item in check_results)
            and git_commit.returncode == 0
            and not git_status.stdout.strip()
        )
        else "NO_GO",
    }


def write_preflight(report: dict[str, object], output_path: Path) -> None:
    """Write a stable JSON preflight report."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def check_specs_as_dicts(checks: Sequence[CheckSpec]) -> list[dict[str, object]]:
    """Expose check specifications for tests and documentation."""

    return [asdict(check) for check in checks]
