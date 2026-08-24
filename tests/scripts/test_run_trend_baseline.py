from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts/run_trend_baseline.py"
_SPEC = importlib.util.spec_from_file_location("run_trend_baseline", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
_load_development_endpoints = _MODULE._load_development_endpoints
_prepare_output_directory = _MODULE._prepare_output_directory
_environment_record = _MODULE._environment_record


def test_load_development_endpoints_filters_final_test(tmp_path) -> None:
    path = tmp_path / "trend-label.parquet"
    frame = pd.DataFrame(
        {
            "participant_id": ["001", "001", "001"],
            "timestamp": pd.date_range("2020-01-01", periods=3, freq="min"),
            "history_start": pd.date_range("2019-12-31 23:30", periods=3, freq="min"),
            "label": ["STABLE", "RISING", "FALLING"],
            "split": ["train", "validation", "test"],
            "bvp_source_file": ["001/BVP.csv"] * 3,
            "protocol_version": ["trend-label-v1"] * 3,
        }
    )
    frame.to_parquet(path, index=False)

    loaded = _load_development_endpoints(path)

    assert set(loaded["split"]) == {"train", "validation"}
    assert len(loaded) == 2


def test_prepare_output_directory_refuses_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "trend-baseline-v1"
    output.mkdir()

    with pytest.raises(FileExistsError, match="already exists"):
        _prepare_output_directory(output)


def test_environment_record_does_not_claim_final_test_access() -> None:
    root = Path(__file__).resolve().parents[2]
    record = _environment_record(
        root=root,
        command="uv run --frozen python scripts/run_trend_baseline.py",
        config_sha256="a" * 64,
        split_manifest_sha256="b" * 64,
    )

    assert record["final_test_accessed"] is False
