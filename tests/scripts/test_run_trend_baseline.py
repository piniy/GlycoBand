from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts/run_trend_baseline.py"
_SPEC = importlib.util.spec_from_file_location("run_trend_baseline", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
_load_development_endpoints = _MODULE._load_development_endpoints


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
