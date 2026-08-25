from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_SCRIPT_PATH = (
    Path(__file__).resolve().parents[2] / "scripts/restore_trend_development_artifacts.py"
)
_SPEC = importlib.util.spec_from_file_location("restore_trend_development_artifacts", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
restore_if_missing = _MODULE.restore_if_missing
sha256_file = _MODULE.sha256_file


def test_restore_if_missing_rejects_digest_mismatch(tmp_path: Path) -> None:
    target = tmp_path / "artifact.bin"

    def build(path: Path) -> None:
        path.write_bytes(b"wrong")

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        restore_if_missing(target, "0" * 64, build)

    assert not target.exists()
    assert not target.with_suffix(".bin.partial").exists()


def test_restore_if_missing_does_not_overwrite_matching_artifact(tmp_path: Path) -> None:
    target = tmp_path / "artifact.bin"
    target.write_bytes(b"frozen")
    expected = sha256_file(target)
    called = False

    def build(path: Path) -> None:
        nonlocal called
        called = True
        path.write_bytes(b"replacement")

    restored = restore_if_missing(target, expected, build)

    assert restored == target
    assert target.read_bytes() == b"frozen"
    assert called is False
