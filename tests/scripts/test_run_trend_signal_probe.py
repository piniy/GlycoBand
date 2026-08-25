from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts/run_trend_signal_probe.py"
_SPEC = importlib.util.spec_from_file_location("run_trend_signal_probe", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
prepare_probe_output = _MODULE.prepare_probe_output
validate_probe_frame = _MODULE.validate_probe_frame


def test_probe_loader_refuses_test_rows() -> None:
    frame = pd.DataFrame(
        {
            "participant_id": ["001", "001"],
            "timestamp": pd.date_range("2020-01-01", periods=2, freq="min"),
            "split": ["train", "test"],
            "label": ["STABLE", "RISING"],
        }
    )
    with pytest.raises(ValueError, match="final-test"):
        validate_probe_frame(frame)


def test_probe_output_is_non_overwriting(tmp_path: Path) -> None:
    output = tmp_path / "trend-signal-conditioning-v1"
    output.mkdir()
    with pytest.raises(FileExistsError):
        prepare_probe_output(output)
