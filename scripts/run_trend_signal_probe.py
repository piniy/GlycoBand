"""Run the development-only Phase 1 Trend conditioning and SQI probe."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

from glycoband.datasets.bigideas import load_config
from glycoband.evaluation.trend_exploratory import (
    cross_validated_macro_f1,
    evaluate_variant,
    validate_probe_frame,
)
from glycoband.features.trend import (
    SHORT_WINDOW_FEATURES,
    _window_feature_rows,
    aggregate_bvp_history_features,
)
from glycoband.features.trend_conditioning import (
    BP_0P5_8_ZSCORE,
    BP_0P7_4_ROBUST,
    RAW_ANCHOR,
    ConditioningSpec,
    apply_quality_policy,
    compose_sqi,
    condition_window,
    fit_participant_quality_thresholds,
)
from glycoband.labels.trend import load_trend_protocol

SPEC_BY_NAME = {
    RAW_ANCHOR.name: RAW_ANCHOR,
    BP_0P5_8_ZSCORE.name: BP_0P5_8_ZSCORE,
    BP_0P7_4_ROBUST.name: BP_0P7_4_ROBUST,
}
WINDOW_IDENTITY = ["participant_id", "window_start", "window_end"]
ENDPOINT_IDENTITY = ["participant_id", "timestamp"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def prepare_probe_output(path: Path) -> None:
    """Create a non-overwriting report directory."""

    if path.exists():
        raise FileExistsError(f"Probe output already exists: {path}")
    path.mkdir(parents=True)


def _load_development_endpoints(path: Path) -> pd.DataFrame:
    frame = pd.read_parquet(
        path,
        columns=[
            "participant_id",
            "timestamp",
            "history_start",
            "split",
            "label",
            "slope_mg_dl_min",
            "bvp_source_file",
            "protocol_version",
        ],
        filters=[("split", "in", ["train", "validation"])],
    )
    validate_probe_frame(frame, name="development endpoints")
    return frame


def _feature_row(
    values: np.ndarray, times: np.ndarray, rate_hz: int, spec: ConditioningSpec
) -> dict[str, object]:
    conditioned = condition_window(values, rate_hz, spec)
    row = _window_feature_rows(
        times.astype("datetime64[ns]").astype(np.int64),
        conditioned,
        values.size,
    )[0]
    differences = np.diff(values)
    iqr = float(np.subtract(*np.percentile(values, [75, 25])))
    spectrum = np.abs(np.fft.rfft(conditioned - conditioned.mean())) ** 2
    frequencies = np.fft.rfftfreq(values.size, d=1.0 / rate_hz)
    total = float(spectrum.sum())
    band = float(spectrum[(frequencies >= 0.5) & (frequencies <= 8.0)].sum())
    row["flat_fraction"] = float(np.mean(differences == 0))
    row["log_iqr"] = float(np.log1p(max(iqr, 0.0)))
    row["bandpower_ratio"] = float(np.clip(band / max(total, 1e-12), 0.0, 1.0))
    return row


def _extract_conditioned_windows(
    path: Path,
    *,
    rate_hz: int,
    window_seconds: int,
    maximum_gap_seconds: float,
    stop_at: pd.Timestamp,
    specs: tuple[ConditioningSpec, ...],
) -> dict[str, pd.DataFrame]:
    """Stream one participant BVP into fixed windows for all predeclared specs."""

    window_samples = rate_hz * window_seconds
    maximum_gap_ns = round(maximum_gap_seconds * 1_000_000_000)
    carry_times = np.array([], dtype="datetime64[ns]")
    carry_values = np.array([], dtype=np.float64)
    rows_by_spec: dict[str, list[dict[str, object]]] = {spec.name: [] for spec in specs}
    for chunk in pd.read_csv(path, chunksize=1_000_000):
        if list(chunk.columns) not in (["datetime", " bvp"], ["datetime", "bvp"]):
            raise ValueError(f"Unexpected BVP schema in {path}: {list(chunk.columns)}")
        chunk.columns = [str(name).strip() for name in chunk.columns]
        parsed = pd.to_datetime(chunk["datetime"], errors="coerce")
        values = pd.to_numeric(chunk["bvp"], errors="coerce")
        valid = parsed.notna() & values.notna() & np.isfinite(values.to_numpy(dtype=float))
        valid &= parsed <= stop_at
        if not valid.any():
            if parsed.notna().any() and parsed.max() > stop_at:
                break
            continue
        times = parsed[valid].to_numpy(dtype="datetime64[ns]")
        numeric = values[valid].to_numpy(dtype=np.float64)
        combined_times = np.concatenate((carry_times, times))
        combined_values = np.concatenate((carry_values, numeric))
        if combined_times.size < 2:
            carry_times, carry_values = combined_times, combined_values
            continue
        gaps = np.diff(combined_times.astype("datetime64[ns]").astype(np.int64))
        breaks = np.flatnonzero((gaps <= 0) | (gaps > maximum_gap_ns)) + 1
        starts = np.concatenate(([0], breaks))
        ends = np.concatenate((breaks, [combined_times.size]))
        carry_times = np.array([], dtype="datetime64[ns]")
        carry_values = np.array([], dtype=np.float64)
        for segment_index, (start, end) in enumerate(zip(starts, ends, strict=True)):
            segment_times = combined_times[start:end]
            segment_values = combined_values[start:end]
            complete = segment_values.size // window_samples
            usable = complete * window_samples
            for window_index in range(complete):
                left = window_index * window_samples
                right = left + window_samples
                window_times = segment_times[left:right]
                window_values = segment_values[left:right]
                for spec in specs:
                    row = _feature_row(window_values, window_times, rate_hz, spec)
                    row["conditioning_version"] = spec.name
                    rows_by_spec[spec.name].append(row)
            remainder_times = segment_times[usable:]
            remainder_values = segment_values[usable:]
            if segment_index == len(starts) - 1:
                carry_times, carry_values = remainder_times, remainder_values
    result: dict[str, pd.DataFrame] = {}
    for spec in specs:
        result[spec.name] = pd.DataFrame(rows_by_spec[spec.name])
    return result


def _acc_rms_for_windows(path: Path, windows: pd.DataFrame) -> np.ndarray:
    """Stream ACC and assign samples to BVP windows without future access."""

    if not path.exists() or windows.empty:
        return np.zeros(len(windows), dtype=float)
    starts = (
        pd.to_datetime(windows["window_start"])
        .to_numpy(dtype="datetime64[ns]")
        .astype(np.int64)
    )
    ends = pd.to_datetime(windows["window_end"]).to_numpy(dtype="datetime64[ns]").astype(np.int64)
    sums = np.zeros(len(windows), dtype=float)
    counts = np.zeros(len(windows), dtype=np.int64)
    for chunk in pd.read_csv(path, chunksize=1_000_000):
        chunk.columns = [str(name).strip() for name in chunk.columns]
        required = {"datetime", "acc_x", "acc_y", "acc_z"}
        if not required.issubset(chunk.columns):
            raise ValueError(f"Unexpected ACC schema in {path}: {list(chunk.columns)}")
        timestamp = pd.to_datetime(chunk["datetime"], errors="coerce")
        numeric = chunk[["acc_x", "acc_y", "acc_z"]].apply(pd.to_numeric, errors="coerce")
        valid = timestamp.notna() & numeric.notna().all(axis=1)
        if not valid.any():
            continue
        time_ns = timestamp[valid].to_numpy(dtype="datetime64[ns]").astype(np.int64)
        magnitude = np.sqrt(np.square(numeric.loc[valid].to_numpy(dtype=float)).sum(axis=1))
        indices = np.searchsorted(ends, time_ns, side="left")
        valid_index = (indices < len(windows)) & (
            time_ns >= starts[np.minimum(indices, len(windows) - 1)]
        )
        for index, value in zip(indices[valid_index], magnitude[valid_index], strict=True):
            sums[int(index)] += float(value * value)
            counts[int(index)] += 1
    return np.sqrt(np.divide(sums, counts, out=np.zeros_like(sums), where=counts > 0))


def _apply_window_quality(
    windows_by_spec: dict[str, pd.DataFrame],
    *,
    acc_path: Path,
) -> dict[str, pd.DataFrame]:
    if not windows_by_spec:
        return windows_by_spec
    anchor = windows_by_spec[RAW_ANCHOR.name]
    acc_rms = _acc_rms_for_windows(acc_path, anchor)
    result: dict[str, pd.DataFrame] = {}
    for name, windows in windows_by_spec.items():
        current = windows.copy()
        current["acc_rms"] = acc_rms
        current["sqi"] = [
            compose_sqi(float(flat), float(iqr), float(band), float(acc))
            for flat, iqr, band, acc in zip(
                current["flat_fraction"],
                current["log_iqr"],
                current["bandpower_ratio"],
                current["acc_rms"],
                strict=True,
            )
        ]
        result[name] = current
    return result


def _aggregate_variant(
    windows: pd.DataFrame,
    endpoints: pd.DataFrame,
    *,
    history_minutes: int,
    window_seconds: int,
    minimum_complete_windows: int,
    conditioning_version: str,
) -> pd.DataFrame:
    endpoint_input = endpoints.copy()
    endpoint_input["split_version"] = "trend-split-v1"
    base_columns = ["participant_id", "window_start", "window_end", *SHORT_WINDOW_FEATURES]
    base = aggregate_bvp_history_features(
        windows[base_columns],
        endpoint_input,
        history_minutes=history_minutes,
        window_seconds=window_seconds,
        minimum_complete_windows=minimum_complete_windows,
    )
    quality_rows: list[dict[str, object]] = []
    for _, endpoint in endpoint_input.sort_values(["participant_id", "timestamp"]).iterrows():
        selected = windows[
            (pd.to_datetime(windows["window_start"]) >= pd.Timestamp(endpoint["history_start"]))
            & (pd.to_datetime(windows["window_end"]) <= pd.Timestamp(endpoint["timestamp"]))
        ]
        if len(selected) < minimum_complete_windows:
            continue
        values = selected["sqi"].to_numpy(dtype=float)
        quality_rows.append(
            {
                "participant_id": endpoint["participant_id"],
                "timestamp": endpoint["timestamp"],
                "quality_sqi_p25": float(np.quantile(values, 0.25)),
                "quality_sqi_mean": float(values.mean()),
                "quality_sqi_min": float(values.min()),
                "acc_rms_p25": float(np.quantile(selected["acc_rms"], 0.25)),
            }
        )
    quality = pd.DataFrame(quality_rows)
    result = base.merge(quality, on=ENDPOINT_IDENTITY, how="left", validate="one_to_one")
    result = result.merge(
        endpoint_input[ENDPOINT_IDENTITY + ["slope_mg_dl_min"]],
        on=ENDPOINT_IDENTITY,
        how="left",
        validate="one_to_one",
    )
    result["conditioning_version"] = conditioning_version
    result["quality_version"] = "trend-sqi-v1"
    return result


def _fit_and_apply_policy(frame: pd.DataFrame, policy: str) -> pd.DataFrame:
    thresholds = fit_participant_quality_thresholds(
        frame[frame["split"] == "train"][["participant_id", "split", "quality_sqi_p25"]].rename(
            columns={"quality_sqi_p25": "sqi"}
        )
    )
    return apply_quality_policy(
        frame.rename(columns={"quality_sqi_p25": "sqi"}),
        policy,
        thresholds,
    ).rename(columns={"sqi": "quality_sqi_p25"})


def _participant_robust_scale(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    columns = [
        column
        for column in result.columns
        if column.startswith("history_") and pd.api.types.is_numeric_dtype(result[column])
    ]
    for column in columns:
        result[column] = pd.to_numeric(result[column], errors="coerce").astype(float)
    for participant_id, group in result.groupby("participant_id", sort=False):
        train = group[group["split"] == "train"]
        if train.empty:
            continue
        for column in columns:
            values = pd.to_numeric(train[column], errors="coerce")
            median = float(values.median())
            iqr = float(values.quantile(0.75) - values.quantile(0.25))
            mask = result["participant_id"] == participant_id
            result.loc[mask, column] = (result.loc[mask, column] - median) / max(iqr, 1e-12)
    return result


def _shift_labels(frame: pd.DataFrame, fraction: float = 0.5) -> pd.DataFrame:
    result = frame.copy()
    for _, indices in result.groupby("participant_id", sort=False).groups.items():
        ordered = result.loc[indices].sort_values("timestamp")
        shift = int(np.floor(len(ordered) * fraction))
        shifted = ordered["label"].to_numpy()[-shift:].tolist() + ordered[
            "label"
        ].to_numpy()[:-shift].tolist()
        result.loc[ordered.index, "label"] = shifted
    return result


def _write_figures(
    output: Path,
    variant_metrics: pd.DataFrame,
    participant: pd.DataFrame,
    quality: pd.DataFrame,
) -> None:
    figures = output / "figures"
    figures.mkdir()
    figure, axis = plt.subplots(figsize=(10, 5))
    axis.bar(variant_metrics["variant_policy"], variant_metrics["macro_f1"], color="#5B4B8A")
    axis.set_ylabel("Validation Macro-F1")
    axis.tick_params(axis="x", rotation=60)
    figure.tight_layout()
    figure.savefig(figures / "conditioning_macro_f1.png", dpi=180)
    plt.close(figure)

    recall = variant_metrics.set_index("variant_policy")[["falling_recall", "rising_recall"]]
    figure, axis = plt.subplots(figsize=(10, 5))
    recall.plot(kind="bar", ax=axis, color=["#4C78A8", "#F58518"])
    axis.set_ylabel("Recall")
    axis.tick_params(axis="x", rotation=60)
    figure.tight_layout()
    figure.savefig(figures / "directional_recall.png", dpi=180)
    plt.close(figure)

    if not quality.empty:
        pivot = quality.pivot(index="variant_policy", columns="split", values="retention")
        figure, axis = plt.subplots(figsize=(9, 5))
        pivot.plot(kind="bar", ax=axis)
        axis.set_ylim(0, 1.05)
        axis.set_ylabel("Retention")
        axis.tick_params(axis="x", rotation=60)
        figure.tight_layout()
        figure.savefig(figures / "quality_by_participant.png", dpi=180)
        plt.close(figure)

    if not participant.empty:
        figure, axis = plt.subplots(figsize=(10, 5))
        participant.boxplot(column="macro_f1", by="variant_policy", ax=axis, rot=60)
        figure.suptitle("")
        axis.set_title("Per-participant validation Macro-F1")
        figure.tight_layout()
        figure.savefig(figures / "quality_vs_error.png", dpi=180)
        plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["conditioning"], required=True)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.repo_root.resolve()
    config_path = root / "configs/probes/trend_signal_learnability-v1.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("Probe config must be a mapping")
    endpoint_path = root / "data/interim/trend/trend-label-v1.parquet"
    baseline_feature_path = root / "data/interim/trend/trend-baseline-features-v1.parquet"
    endpoints = _load_development_endpoints(endpoint_path)
    baseline_features = pd.read_parquet(baseline_feature_path)
    validate_probe_frame(baseline_features, name="baseline features")
    audit_config = load_config(root / "configs/audits/bigideas.yaml")
    dataset_root = root / "data/raw/bigideas/v1.1.3"
    protocol = load_trend_protocol(root / "configs/trend/label-v1.yaml")
    specs = tuple(SPEC_BY_NAME[name] for name in config["conditioning"]["variants"])
    windows_frames: list[pd.DataFrame] = []
    endpoint_frames: list[pd.DataFrame] = []
    for participant_id, endpoint_group in endpoints.groupby("participant_id", sort=True):
        endpoint_group = endpoint_group.copy()
        max_endpoint = pd.to_datetime(endpoint_group["timestamp"]).max()
        source_file = str(endpoint_group["bvp_source_file"].iloc[0])
        print(
            f"[trend-signal-probe-v1] participant={participant_id} "
            "stage=conditioned_windows",
            flush=True,
        )
        windows_by_spec = _extract_conditioned_windows(
            dataset_root / source_file,
            rate_hz=int(audit_config["bvp_rate_hz"]),
            window_seconds=int(config["conditioning"]["short_window_seconds"]),
            maximum_gap_seconds=float(audit_config["maximum_bvp_gap_seconds"]),
            stop_at=max_endpoint,
            specs=specs,
        )
        acc_path = dataset_root / f"{participant_id}/ACC_{participant_id}.csv"
        windows_by_spec = _apply_window_quality(windows_by_spec, acc_path=acc_path)
        for name, windows in windows_by_spec.items():
            windows.insert(0, "participant_id", participant_id)
            windows_frames.append(windows)
            endpoint_frames.append(
                _aggregate_variant(
                    windows.assign(participant_id=participant_id),
                    endpoint_group,
                    history_minutes=protocol.history_minutes,
                    window_seconds=int(config["conditioning"]["short_window_seconds"]),
                    minimum_complete_windows=(
                        protocol.history_minutes * 60
                        // int(config["conditioning"]["short_window_seconds"])
                        - 1
                    ),
                    conditioning_version=name,
                )
            )
        print(
            f"[trend-signal-probe-v1] participant={participant_id} "
            f"windows={len(windows_by_spec[RAW_ANCHOR.name])}",
            flush=True,
        )
    windows = pd.concat(windows_frames, ignore_index=True)
    conditioned_endpoints = pd.concat(endpoint_frames, ignore_index=True)
    raw_quality = conditioned_endpoints[
        conditioned_endpoints["conditioning_version"] == RAW_ANCHOR.name
    ]
    raw_anchor = baseline_features.merge(
        raw_quality[
            ENDPOINT_IDENTITY
            + ["quality_sqi_p25", "quality_sqi_mean", "quality_sqi_min", "acc_rms_p25"]
        ],
        on=ENDPOINT_IDENTITY,
        how="left",
        validate="one_to_one",
    )
    raw_anchor["conditioning_version"] = RAW_ANCHOR.name
    raw_anchor["quality_policy"] = "report_only"
    raw_anchor["quality_weight"] = 1.0
    raw_anchor["quality_retained"] = True
    raw_anchor = raw_anchor.drop(
        columns=["quality_sqi_p25", "quality_sqi_mean", "quality_sqi_min", "acc_rms_p25"],
        errors="ignore",
    )
    variant_frames: dict[str, pd.DataFrame] = {"raw_anchor__report_only": raw_anchor}
    for name in (BP_0P5_8_ZSCORE.name, BP_0P7_4_ROBUST.name):
        base = conditioned_endpoints[conditioned_endpoints["conditioning_version"] == name].copy()
        for policy in ("report_only", "soft_weight", "hard_exclude_bottom_train_decile"):
            prepared = _fit_and_apply_policy(base, policy)
            prepared["quality_policy"] = policy
            variant_frames[f"{name}__{policy}"] = prepared
    selection_scores = {
        name: cross_validated_macro_f1(frame[frame["quality_policy"] == "report_only"])
        for name, frame in variant_frames.items()
        if name in {"bp_0p5_8_zscore__report_only", "bp_0p7_4_robust__report_only"}
    }
    selected = max(selection_scores, key=lambda name: selection_scores[name])
    selected_base = variant_frames[selected]
    scaled = _participant_robust_scale(selected_base)
    scaled["quality_policy"] = "train_participant_robust_scale"
    variant_frames[f"{selected.split('__')[0]}__train_participant_robust_scale"] = scaled
    soft = variant_frames[f"{selected.split('__')[0]}__soft_weight"]
    hard = variant_frames[f"{selected.split('__')[0]}__hard_exclude_bottom_train_decile"]
    variant_frames[f"{selected.split('__')[0]}__soft_weight"] = soft
    variant_frames[f"{selected.split('__')[0]}__hard_exclude_bottom_train_decile"] = hard
    shifted = _shift_labels(selected_base)
    shifted["quality_policy"] = "large_circular_shift_control"
    variant_frames["selected__large_circular_shift_control"] = shifted

    reports: list[dict[str, object]] = []
    predictions: list[pd.DataFrame] = []
    participant_rows: list[pd.DataFrame] = []
    quality_rows: list[dict[str, object]] = []
    for variant_policy, frame in variant_frames.items():
        policy = str(frame["quality_policy"].iloc[0])
        weights = None
        if policy == "soft_weight":
            weights = frame.loc[frame["split"] == "train", "quality_weight"].to_numpy(dtype=float)
        report, prediction = evaluate_variant(
            frame,
            variant=variant_policy,
            policy=(
                "hard_exclude_bottom_train_decile"
                if policy == "hard_exclude_bottom_train_decile"
                else "report_only"
            ),
            train_sample_weight=weights,
        )
        report["variant_policy"] = variant_policy
        if policy == "hard_exclude_bottom_train_decile":
            report["common_endpoint_macro_f1"] = report["macro_f1"]
        reports.append(report)
        predictions.append(prediction)
        for participant_id, group in prediction.groupby("participant_id", sort=True):
            participant_rows.append(
                pd.DataFrame(
                    {
                        "participant_id": [participant_id],
                        "variant_policy": [variant_policy],
                        "macro_f1": [
                            float(
                                __import__("sklearn.metrics", fromlist=["f1_score"]).f1_score(
                                    group["label"],
                                    group["prediction"],
                                    labels=list(("FALLING", "STABLE", "RISING")),
                                    average="macro",
                                    zero_division=0,
                                )
                            )
                        ],
                    }
                )
            )
        for split in ("train", "validation"):
            subset = frame[frame["split"] == split]
            quality_rows.append(
                {
                    "variant_policy": variant_policy,
                    "split": split,
                    "retention": float(subset["quality_retained"].mean())
                    if "quality_retained" in subset
                    else 1.0,
                    "rows": int(len(subset)),
                }
            )
    output = root / "reports/probes/trend-signal-conditioning-v1"
    prepare_probe_output(output)
    windows.to_parquet(root / "data/interim/trend/trend-feature-v2-windows.parquet", index=False)
    conditioned_endpoints.to_parquet(
        root / "data/interim/trend/trend-feature-v2-endpoints.parquet", index=False
    )
    (output / "config.yaml").write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
    (output / "environment.txt").write_text(
        f"python={platform.python_version()}\nfinal_test_accessed=false\n", encoding="utf-8"
    )
    (output / "dataset_manifest.json").write_text(
        json.dumps(
            {
                "endpoint_artifact_sha256": sha256_file(endpoint_path),
                "baseline_feature_artifact_sha256": sha256_file(baseline_feature_path),
                "window_artifact": "data/interim/trend/trend-feature-v2-windows.parquet",
                "endpoint_feature_artifact": (
                    "data/interim/trend/trend-feature-v2-endpoints.parquet"
                ),
                "participants": int(endpoints["participant_id"].nunique()),
                "development_rows": int(len(endpoints)),
                "final_test_accessed": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    variant_metrics = pd.DataFrame(reports)
    variant_metrics.to_csv(output / "variant_metrics.csv", index=False)
    pd.concat(participant_rows, ignore_index=True).to_csv(
        output / "per_participant.csv", index=False
    )
    pd.DataFrame(quality_rows).to_csv(output / "quality_retention.csv", index=False)
    pd.concat(predictions, ignore_index=True).to_parquet(
        output / "predictions.parquet", index=False
    )
    metrics = {
        "selected_variant": selected,
        "inner_train_macro_f1": selection_scores,
        "variant_count": len(reports),
        "validation_weighted": False,
        "final_test_accessed": False,
    }
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    summary = [
        "# Trend signal conditioning probe v1",
        "",
        "Status: exploratory development-only evidence; final test sealed.",
        "",
        f"Selected conditioning candidate by train-only chronological resampling: **{selected}**.",
        "Validation metrics are ordinary unweighted metrics; "
        "soft SQI weights affect training only.",
        "",
        "Final-test performance accessed: NO",
    ]
    (output / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    _write_figures(
        output,
        variant_metrics,
        pd.concat(participant_rows, ignore_index=True),
        pd.DataFrame(quality_rows),
    )
    print(f"[trend-signal-probe-v1] selected={selected}", flush=True)
    print(f"[trend-signal-probe-v1] report_artifact={output}", flush=True)
    print("[trend-signal-probe-v1] final_test_accessed=false", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
