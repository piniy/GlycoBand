import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

from glycoband.utils.preflight import (
    DEFAULT_CHECKS,
    CheckSpec,
    collect_preflight,
    sha256_file,
    write_preflight,
)


def completed(
    command: Sequence[str], return_code: int = 0, stdout: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, return_code, stdout=stdout, stderr="")


def clean_runner(
    command: Sequence[str], _cwd: Path
) -> subprocess.CompletedProcess[str]:
    if tuple(command) == ("git", "rev-parse", "HEAD"):
        return completed(command, stdout="abc123\n")
    return completed(command)


def test_sha256_file(tmp_path: Path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text("glycoband\n", encoding="utf-8")

    assert sha256_file(sample) == "54aff6787aa9d2f727ce240565b6848bf1c6c2f4291e02c4a0ab5742c9a4497b"


def test_collect_preflight_without_running_checks() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    report = collect_preflight(repo_root, checks=())

    assert report["schema_version"] == 1
    assert report["environment_gate"] == "NO_GO"
    assert report["storage"]["gate"] == "DATA_REQUIRED"  # type: ignore[index]
    assert report["lockfile"]["path"] == "uv.lock"  # type: ignore[index]


def test_default_checks_cover_required_verification() -> None:
    assert [check.name for check in DEFAULT_CHECKS] == [
        "sync",
        "lock",
        "tests",
        "lint",
        "types",
    ]


def test_collect_preflight_passes_only_when_checks_pass_and_git_is_clean() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    checks = (CheckSpec("example", ("example", "--check")),)

    report = collect_preflight(repo_root, checks=checks, runner=clean_runner)

    assert report["environment_gate"] == "PASS"
    assert report["repository"] == {"commit": "abc123", "dirty": False}
    assert report["checks"][0]["passed"] is True  # type: ignore[index]


def test_collect_preflight_fails_when_a_required_check_fails() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    checks = (CheckSpec("failure", ("failure",)),)

    def failing_runner(
        command: Sequence[str], cwd: Path
    ) -> subprocess.CompletedProcess[str]:
        if tuple(command) == ("failure",):
            return completed(command, return_code=1, stdout="failed\n")
        return clean_runner(command, cwd)

    report = collect_preflight(repo_root, checks=checks, runner=failing_runner)

    assert report["environment_gate"] == "NO_GO"
    assert report["checks"][0]["passed"] is False  # type: ignore[index]


def test_collect_preflight_fails_when_git_is_dirty() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    checks = (CheckSpec("example", ("example",)),)

    def dirty_runner(
        command: Sequence[str], cwd: Path
    ) -> subprocess.CompletedProcess[str]:
        if tuple(command) == ("git", "status", "--porcelain"):
            return completed(command, stdout=" M AGENTS.md\n")
        return clean_runner(command, cwd)

    report = collect_preflight(repo_root, checks=checks, runner=dirty_runner)

    assert report["environment_gate"] == "NO_GO"
    assert report["repository"] == {"commit": "abc123", "dirty": True}


def test_write_preflight_serializes_compact_json(tmp_path: Path) -> None:
    output = tmp_path / "preflight.json"
    report: dict[str, object] = {"environment_gate": "PASS", "checks": []}

    write_preflight(report, output)

    assert json.loads(output.read_text(encoding="utf-8")) == report
    assert output.read_text(encoding="utf-8").endswith("\n")
