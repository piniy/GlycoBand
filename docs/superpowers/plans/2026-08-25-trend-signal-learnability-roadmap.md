# Trend Signal Learnability Roadmap Implementation Plan

> **Historical status (2026-08-25):** Phase 0 diagnostics and Phase 1 conditioning/SQI were completed. The predeclared Phase 1 promotion gate failed, producing `NOT_SUPPORTED_BY_CONDITIONING`. Tasks for physiological enrichment, alternate formulations, capacity escalation, and final-test evaluation were intentionally not executed. The unchecked steps below preserve the original predeclared roadmap; they are not an active backlog.

> **For agentic workers:** REQUIRED SUB-SKILL: Use `deliver-in-lakes` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Do not execute later phases after a stop gate fails.

**Goal:** Determine, using development-only BIG IDEAs data, whether defensible BVP signal conditioning, SQI, and physiological feature families reveal Recent Trend information beyond the existing constant and shifted controls.

**Architecture:** Preserve `trend-label-v1`, `trend-split-v1`, and the sealed final test. Add a separate exploratory pipeline beside the immutable `trend-feature-v1` baseline: first produce descriptive diagnostics, then compare fixed conditioning/SQI variants with Logistic Regression, then add physiological feature-family ablations, then evaluate binary/hierarchical formulations and fixed classical models only when the preceding gate passes. Every candidate uses identical development endpoint identities where possible and reports common-endpoint metrics when hard SQI exclusion changes retention.

**Tech Stack:** Python 3.11+, pandas, NumPy, SciPy signal processing, scikit-learn, XGBoost already locked in `uv.lock`, PyArrow/Parquet, Matplotlib, pytest, Ruff, mypy, `uv`.

## Global Constraints

- This plan concerns the existing backward-looking Recent Trend question only: BVP history ending at `t` predicts CGM history ending at `t`.
- Future prediction at 15/30/45 minutes is a separate scientific target and is out of scope.
- Dataset is BIG IDEAs v1.1.3 only; independent unit is the participant; participant count is 16.
- Frozen label remains `trend-label-v1`: H30, median3, OLS, tau 0.5 mg/dL/min, at least 80% CGM support, continuous BVP history.
- Frozen split remains `trend-split-v1`: within-person chronological 60/20/20 with a 30-minute embargo.
- Read only `train` and `validation`; never load, count, plot, fit, score, or inspect `test` rows.
- Preserve the current baseline artifact and code path. New work uses `trend-feature-v2-*` and new report directories; it never overwrites `trend-baseline-v1`.
- Raw reference glucose is used only for labels and evaluation. It never enters an inference feature.
- BVP-only, context-only, and BVP-plus-context results remain separate. ACC, temperature, and food timing cannot silently become core predictors.
- Threshold 0.3/0.7 sensitivity is descriptive/exploratory; it cannot replace tau 0.5 or become the scientific target without project-lead review.
- Binary and hierarchical results are exploratory alternate tasks. They cannot supersede the frozen three-class target without project-lead review.
- All preprocessing parameters and SQI thresholds are fit from `train` only. Validation metrics are always unweighted, even when training uses soft SQI weights.
- No random shuffle of temporally overlapping samples. No sample-level cross-validation that ignores participant and time.
- Macro-F1 remains primary. Always report FALLING and RISING recall, opposite-direction error, per-participant Macro-F1 median/IQR, and participant-paired uncertainty.
- Final test remains sealed until preprocessing, SQI, feature set, target, model family, hyperparameters, calibration/OOD, and success criteria are frozen by human review.
- Preserve the user's existing uncommitted changes in `AGENTS.md` and `Agent/05_EXPERIMENT_AGENT.md`.
- Run experiment implementation from a clean isolated worktree; do not use the current dirty working tree for registered artifacts.
- Every experiment runner prints concise participant/stage progress and writes compact Parquet/CSV/JSON/Markdown plus scientifically useful PNG figures.
- Do not add LightGBM: XGBoost is already locked and is sufficient for the single fixed nonlinear comparison.
- Do not use raw-waveform deep learning in this plan.

---

## Ocean and exit gate

The approved ocean for this plan is not “obtain a better score.” It is:

> Decide whether the weak baseline is explained by an obviously inadequate BVP representation/quality policy, or whether development evidence still fails to support Recent Trend learnability.

Ocean completion requires one of these auditable conclusions:

1. `SUPPORTED_FOR_FREEZE_REVIEW`: one predeclared BVP-only candidate passes every final development gate below;
2. `PARTIALLY_SUPPORTED`: a candidate improves some directional evidence but fails at least one stability/control gate;
3. `NOT_SUPPORTED`: conditioning and physiological classical candidates fail to produce meaningful stable gain;
4. `INSUFFICIENT_EVIDENCE`: source, alignment, quality, or participant support prevents a defensible comparison.

The final development promotion gate is deliberately stronger than a small numerical bump:

- validation Macro-F1 delta versus the best constant is at least `0.04`;
- participant-bootstrap 95% CI lower bound for that delta is greater than `0`;
- FALLING recall is at least `0.15` and RISING recall is at least `0.15`;
- selected candidate beats its large temporal-shift control with bootstrap CI lower bound greater than `0`;
- median per-participant Macro-F1 delta versus the best constant is at least `0.03`;
- at least 12 of 16 participants have a non-negative Macro-F1 delta;
- hard-SQI variants retain at least 80% of validation endpoints and pass the same gate on the paired common-endpoint subset;
- no single participant removal changes a passing Macro-F1 delta into a negative delta;
- final-test access is recorded as `false` in every artifact.

Passing this gate authorizes a recommendation for human freeze review, not final-test access.

## File map

### Preserve unchanged

- `configs/trend/label-v1.yaml` — frozen scientific target.
- `data/manifests/trend_split-v1.json` — frozen chronological split contract.
- `src/glycoband/features/trend.py` — legacy `trend-feature-v1` baseline representation.
- `src/glycoband/evaluation/trend_baseline.py` — registered baseline anchor.
- `reports/experiments/trend-baseline-v1/` — immutable baseline evidence.

### Create

- `configs/probes/trend_signal_learnability-v1.yaml` — all fixed exploratory variants, thresholds, models, seeds, and gates.
- `src/glycoband/evaluation/trend_diagnostics.py` — class/slope/correlation/quality diagnostics.
- `src/glycoband/features/trend_conditioning.py` — detrending, bandpass, robust normalization, and window SQI primitives.
- `src/glycoband/features/trend_physiology.py` — BVP-derived pulse, HRV, morphology, and spectral feature families.
- `src/glycoband/features/trend_context.py` — past-only ACC, temperature, and food-log alignment for declared context comparisons.
- `src/glycoband/evaluation/trend_exploratory.py` — weighted LR, feature-family ablations, hierarchical evaluation, paired metrics, and fixed RF/XGBoost comparisons.
- `scripts/restore_trend_development_artifacts.py` — regenerate missing ignored endpoint/feature artifacts and verify hashes without rewriting frozen manifests or reports.
- `scripts/run_trend_signal_diagnostics.py` — Phase 0 runner.
- `scripts/run_trend_signal_probe.py` — Phases 1–3 runner with explicit `--phase` and non-overwrite semantics.
- `tests/evaluation/test_trend_diagnostics.py`.
- `tests/features/test_trend_conditioning.py`.
- `tests/features/test_trend_physiology.py`.
- `tests/features/test_trend_context.py`.
- `tests/evaluation/test_trend_exploratory.py`.
- `tests/fixtures/trend_probe.py` — deterministic shared development-only fixtures for diagnostics, quality, context, physiology, and model tests.
- `tests/scripts/test_restore_trend_development_artifacts.py`.
- `tests/scripts/test_run_trend_signal_probe.py`.

### Generated, ignored, or evidence artifacts

- `data/interim/trend/trend-label-v1.parquet` — restored and hash-checked frozen endpoints.
- `data/interim/trend/trend-feature-v2-windows.parquet` — development short-window features and SQI.
- `data/interim/trend/trend-feature-v2-history.parquet` — development endpoint features.
- `reports/probes/trend-signal-diagnostics-v1/` — Phase 0 evidence.
- `reports/probes/trend-signal-conditioning-v1/` — Phase 1 evidence.
- `reports/probes/trend-feature-enrichment-v1/` — Phase 2 evidence.
- `reports/probes/trend-formulation-v1/` — Phase 3 evidence.
- `reports/probes/trend-signal-learnability-v1-decision.md` — final development recommendation.

---

### Task 1: Restore and lock the development source view

**Files:**

- Create: `scripts/restore_trend_development_artifacts.py`
- Test: `tests/scripts/test_restore_trend_development_artifacts.py`
- Read: `data/manifests/trend_split-v1.json`
- Read: `reports/experiments/trend-baseline-v1/dataset_manifest.json`

**Interfaces:**

- Consumes: frozen manifest paths and SHA-256 digests, verified BIG IDEAs archive/extracted files.
- Produces: `restore_if_missing(path: Path, expected_sha256: str, builder: Callable[[Path], None]) -> Path` and a CLI that never rewrites frozen JSON/report artifacts.

- [ ] **Step 1: Write the failing hash-protection tests**

```python
def test_restore_refuses_mismatched_artifact(tmp_path: Path) -> None:
    destination = tmp_path / "artifact.parquet"

    def builder(path: Path) -> None:
        path.write_bytes(b"wrong")

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        restore_if_missing(destination, "0" * 64, builder)


def test_restore_does_not_overwrite_matching_artifact(tmp_path: Path) -> None:
    destination = tmp_path / "artifact.parquet"
    destination.write_bytes(b"stable")
    expected = hashlib.sha256(b"stable").hexdigest()
    called = False

    def builder(path: Path) -> None:
        nonlocal called
        called = True

    assert restore_if_missing(destination, expected, builder) == destination
    assert called is False
```

- [ ] **Step 2: Run the focused test and verify failure**

Run:

```powershell
uv run --frozen pytest tests/scripts/test_restore_trend_development_artifacts.py -q
```

Expected: collection or import failure because the restore module does not exist.

- [ ] **Step 3: Implement atomic restore with digest verification**

```python
def restore_if_missing(
    path: Path,
    expected_sha256: str,
    builder: Callable[[Path], None],
) -> Path:
    if path.exists() and sha256_file(path) == expected_sha256:
        return path
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.unlink(missing_ok=True)
    builder(temporary)
    observed = sha256_file(temporary)
    if observed != expected_sha256:
        temporary.unlink(missing_ok=True)
        raise ValueError(
            f"Restored artifact SHA-256 mismatch: expected={expected_sha256} observed={observed}"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary.replace(path)
    return path
```

The CLI must:

1. reject any request for test rows;
2. regenerate `trend-label-v1.parquet` from the frozen config and split code;
3. compare its digest with `data/manifests/trend_split-v1.json`;
4. optionally regenerate the legacy development feature artifact and compare it with the digest in `trend-baseline-v1/dataset_manifest.json`;
5. leave both frozen manifest files and `reports/experiments/trend-baseline-v1/` untouched;
6. print `final_test_accessed=false`.

- [ ] **Step 4: Restore extracted source only when absent**

Before running the CLI, check free space and exact archive membership:

```powershell
Get-PSDrive -Name D | Select-Object Name,Free
uv run --frozen python -c "from pathlib import Path; from glycoband.datasets.bigideas import verify_archive_membership; r=Path.cwd(); print(verify_archive_membership(r/'data/raw/bigideas/big-ideas-glycemic-wearable-1.1.3.zip', r/'data/raw/bigideas/SHA256SUMS.txt'))"
```

Expected: `exact_archive_membership` is `True`. If `data/raw/bigideas/v1.1.3/001/BVP_001.csv` is absent, extract through the existing verified `extract_and_verify_archive` helper. Do not re-download the ZIP and do not mutate its contents.

- [ ] **Step 5: Run targeted restoration verification**

```powershell
uv run --frozen pytest tests/scripts/test_restore_trend_development_artifacts.py -q
uv run --frozen python scripts/restore_trend_development_artifacts.py --endpoint-only
```

Expected: tests pass; restored digest equals the frozen manifest; terminal ends with `final_test_accessed=false`.

- [ ] **Step 6: Commit the restoration utility**

```powershell
git add scripts/restore_trend_development_artifacts.py tests/scripts/test_restore_trend_development_artifacts.py
git commit -m "feat(trend): restore frozen development artifacts safely"
```

**Stop gate:** Any digest mismatch is `BLOCKED`. Do not regenerate a new manifest, change the expected hash, or continue to diagnostics.

---

### Task 2: Implement Phase 0 class, slope, correlation, and flatness diagnostics

**Files:**

- Create: `configs/probes/trend_signal_learnability-v1.yaml`
- Create: `src/glycoband/evaluation/trend_diagnostics.py`
- Create: `scripts/run_trend_signal_diagnostics.py`
- Create: `tests/evaluation/test_trend_diagnostics.py`
- Create: `tests/fixtures/trend_probe.py`

**Interfaces:**

- Consumes: endpoint rows containing `participant_id`, `timestamp`, `split`, `label`, and `slope_mg_dl_min`; legacy 50-dimensional development features joined on exact endpoint identity.
- Produces:
  - `class_distribution(frame: pd.DataFrame) -> pd.DataFrame`;
  - `feature_slope_correlations(frame: pd.DataFrame, features: Sequence[str]) -> pd.DataFrame`;
  - `quality_proxy_summary(frame: pd.DataFrame) -> pd.DataFrame`;
  - Phase 0 CSV/JSON/Markdown/PNG artifacts.

- [ ] **Step 1: Create deterministic shared fixtures**

```python
def probe_fixture() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    labels = ("FALLING", "STABLE", "RISING")
    for participant_index, participant_id in enumerate(("001", "002", "003")):
        for index in range(30):
            timestamp = pd.Timestamp("2020-01-01") + pd.Timedelta(minutes=5 * index)
            row: dict[str, object] = {
                "participant_id": participant_id,
                "timestamp": timestamp,
                "history_start": timestamp - pd.Timedelta(minutes=30),
                "split": "train" if index < 20 else "validation",
                "label": labels[index % 3],
                "slope_mg_dl_min": (-0.8, 0.0, 0.8)[index % 3],
                "feature_version": "trend-feature-v1",
            }
            for feature_index in range(50):
                row[f"feature_{feature_index:02d}"] = float(
                    participant_index + index / 100 + feature_index / 1000
                )
            rows.append(row)
    return pd.DataFrame(rows)


def quality_fixture() -> pd.DataFrame:
    frame = probe_fixture()[["participant_id", "timestamp", "split"]].copy()
    frame["sqi"] = np.linspace(0.05, 0.95, len(frame))
    return frame


def acc_fixture() -> pd.DataFrame:
    timestamps = pd.date_range("2020-01-01", periods=61, freq="30s")
    return pd.DataFrame(
        {"timestamp": timestamps, "x": 0.1, "y": 0.2, "z": 0.9}
    )


def synthetic_pulse_train(*, rate_hz: int, seconds: int, bpm: float) -> np.ndarray:
    time = np.arange(rate_hz * seconds, dtype=float) / rate_hz
    phase = np.mod(time, 60.0 / bpm)
    return np.exp(-0.5 * ((phase - 0.12) / 0.04) ** 2)


def probe_config() -> dict[str, object]:
    root = Path(__file__).resolve().parents[2]
    return yaml.safe_load(
        (root / "configs/probes/trend_signal_learnability-v1.yaml").read_text(
            encoding="utf-8"
        )
    )
```

- [ ] **Step 2: Write tests that reject sealed-test data and duplicate endpoint identities**

```python
def test_diagnostics_refuse_test_rows() -> None:
    frame = probe_fixture()
    frame.loc[0, "split"] = "test"
    with pytest.raises(ValueError, match="final-test"):
        validate_diagnostic_frame(frame)


def test_diagnostics_require_unique_endpoint_identity() -> None:
    frame = pd.concat([probe_fixture(), probe_fixture().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        validate_diagnostic_frame(frame)
```

- [ ] **Step 3: Write the within-participant correlation test**

```python
def test_correlations_report_pooled_and_within_participant_values() -> None:
    result = feature_slope_correlations(
        probe_fixture(), ["feature_00", "feature_01"]
    )
    assert set(result["method"]) == {"pearson", "spearman"}
    assert {
        "feature",
        "method",
        "pooled_correlation",
        "participant_median_correlation",
        "participant_iqr",
        "participants_with_finite_value",
    }.issubset(result.columns)
```

- [ ] **Step 4: Run tests and confirm failure**

```powershell
uv run --frozen pytest tests/evaluation/test_trend_diagnostics.py -q
```

Expected: import failure because the diagnostics module is absent.

- [ ] **Step 5: Implement exact endpoint validation and descriptive summaries**

`feature_slope_correlations` must calculate both pooled correlation and correlations separately inside each participant. It must report participant median/IQR so a pooled subject-identity effect cannot masquerade as physiological association. It must not choose or rank features using validation labels.

Use these fixed flatness thresholds from config:

```yaml
diagnostics:
  flat_fraction_thresholds: [0.01, 0.05, 0.10]
  correlation_methods: [pearson, spearman]
  class_order: [FALLING, STABLE, RISING]
```

The class table must contain one row per `participant_id × split × label` and fill absent combinations with zero.

- [ ] **Step 6: Implement the Phase 0 runner and artifact set**

Write:

```text
reports/probes/trend-signal-diagnostics-v1/
    config.yaml
    dataset_manifest.json
    class_distribution.csv
    slope_summary.csv
    feature_slope_correlations.csv
    flat_fraction_summary.csv
    summary.md
    figures/class_distribution_by_participant.png
    figures/slope_distribution_thresholds.png
    figures/correlation_rank.png
    figures/flat_fraction_distribution.png
```

The slope plot must draw vertical lines at `-0.5` and `+0.5` without accessing test data. The summary must state `Final-test performance accessed: NO`.

- [ ] **Step 7: Run the diagnostics**

```powershell
uv run --frozen pytest tests/evaluation/test_trend_diagnostics.py -q
uv run --frozen python scripts/run_trend_signal_diagnostics.py
```

Expected: command exits zero, reports 16 development participants, writes all four PNG figures, and records observed rather than predetermined correlations.

- [ ] **Step 8: Commit Phase 0**

```powershell
git add configs/probes/trend_signal_learnability-v1.yaml src/glycoband/evaluation/trend_diagnostics.py scripts/run_trend_signal_diagnostics.py tests/fixtures/trend_probe.py tests/evaluation/test_trend_diagnostics.py reports/probes/trend-signal-diagnostics-v1
git commit -m "research(trend): add signal learnability diagnostics"
```

**Decision gate:**

- `BLOCKED` if endpoint identity, slope/label reconciliation, or participant count fails.
- `LABEL_SUPPORT_RISK` if either directional class is absent from development data for more than 4 participants or if median per-participant directional support is below 5%; pause model expansion and review whether the current evaluation can support per-participant claims.
- Otherwise proceed to Phase 1 even if correlations are near zero, because conditioning/SQI is the cheapest remaining discriminating probe.

---

### Task 3: Add deterministic BVP conditioning variants

**Files:**

- Create: `src/glycoband/features/trend_conditioning.py`
- Create: `tests/features/test_trend_conditioning.py`
- Modify: `configs/probes/trend_signal_learnability-v1.yaml`

**Interfaces:**

- Produces:
  - `ConditioningSpec(name: str, detrend: str, low_hz: float, high_hz: float, order: int, normalization: str)`;
  - `FloatArray = NDArray[np.float64]`;
  - `condition_window(values: NDArray[np.float64], rate_hz: int, spec: ConditioningSpec) -> NDArray[np.float64]`;
  - fixed variants `raw_anchor`, `bp_0p5_8_zscore`, and `bp_0p7_4_robust`.

- [ ] **Step 1: Write signal-preservation and invalid-band tests**

```python
def test_bandpass_preserves_two_hz_and_attenuates_baseline_drift() -> None:
    rate_hz = 64
    time = np.arange(rate_hz * 30) / rate_hz
    values = np.sin(2 * np.pi * 2.0 * time) + 2.0 * np.sin(2 * np.pi * 0.1 * time)
    filtered = condition_window(values, rate_hz, BP_0P5_8_ZSCORE)
    assert abs(filtered.mean()) < 1e-6
    assert np.std(filtered) == pytest.approx(1.0, rel=0.05)
    reference = np.sin(2 * np.pi * 2.0 * time)
    assert np.corrcoef(filtered, reference)[0, 1] > 0.90


def test_conditioning_rejects_band_above_nyquist() -> None:
    spec = ConditioningSpec("bad", "linear", 0.5, 40.0, 4, "zscore")
    with pytest.raises(ValueError, match="Nyquist"):
        condition_window(np.ones(1920), 64, spec)
```

- [ ] **Step 2: Run tests and verify failure**

```powershell
uv run --frozen pytest tests/features/test_trend_conditioning.py -q
```

Expected: import failure.

- [ ] **Step 3: Implement the fixed pipelines**

Use SciPy fourth-order Butterworth SOS plus `sosfiltfilt`, with all transformations applied independently inside each past-only 30-second BVP window:

```python
def condition_window(values: FloatArray, rate_hz: int, spec: ConditioningSpec) -> FloatArray:
    validate_finite_window(values, rate_hz)
    detrended = signal.detrend(values, type="linear") if spec.detrend == "linear" else values
    sos = signal.butter(
        spec.order,
        [spec.low_hz, spec.high_hz],
        btype="bandpass",
        fs=rate_hz,
        output="sos",
    )
    filtered = signal.sosfiltfilt(sos, detrended)
    if spec.normalization == "zscore":
        return (filtered - filtered.mean()) / max(filtered.std(), 1e-12)
    median = np.median(filtered)
    scale = max(np.subtract(*np.percentile(filtered, [75, 25])), 1e-12)
    return (filtered - median) / scale
```

Do not sweep filter order, cutoff, or normalization. These are three predeclared representations, not a search grid.

- [ ] **Step 4: Run focused tests**

```powershell
uv run --frozen pytest tests/features/test_trend_conditioning.py tests/features/test_trend.py -q
```

Expected: new tests pass and the legacy raw feature tests remain unchanged.

- [ ] **Step 5: Commit conditioning primitives**

```powershell
git add src/glycoband/features/trend_conditioning.py tests/features/test_trend_conditioning.py configs/probes/trend_signal_learnability-v1.yaml
git commit -m "feat(trend): add fixed BVP conditioning variants"
```

---

### Task 4: Add SQI and motion-aware quality policies

**Files:**

- Modify: `src/glycoband/features/trend_conditioning.py`
- Create: `src/glycoband/features/trend_context.py`
- Modify: `tests/features/test_trend_conditioning.py`
- Create: `tests/features/test_trend_context.py`
- Modify: `configs/probes/trend_signal_learnability-v1.yaml`

**Interfaces:**

- Consumes: raw BVP 30-second window, conditioned BVP window, and past-only aligned tri-axial ACC samples.
- Produces:
  - `WindowQuality(flat_fraction, log_iqr, bandpower_ratio, acc_rms, sqi)`;
  - `compute_window_quality(...) -> WindowQuality`;
  - `fit_participant_quality_thresholds(train_windows: pd.DataFrame) -> pd.DataFrame`;
  - `apply_quality_policy(history: pd.DataFrame, policy: str, thresholds: pd.DataFrame) -> pd.DataFrame`.

- [ ] **Step 1: Write train-only threshold and future-exclusion tests**

```python
def test_quality_thresholds_use_train_rows_only() -> None:
    windows = quality_fixture()
    thresholds = fit_participant_quality_thresholds(windows)
    assert thresholds.loc["001", "hard_exclusion_cutoff"] == pytest.approx(
        windows.query("participant_id == '001' and split == 'train'")["sqi"].quantile(0.10)
    )


def test_context_alignment_never_uses_future_acc() -> None:
    aligned = align_acc_energy(acc_fixture(), endpoint_time=pd.Timestamp("2020-01-01 00:30"))
    assert aligned["window_end"].max() <= pd.Timestamp("2020-01-01 00:30")
```

- [ ] **Step 2: Implement SQI components and fixed policies**

The composite SQI is a bounded proxy, not a validated clinical SQI:

```text
flat_score      = clip(1 - flat_fraction / 0.05, 0, 1)
amplitude_score = train-participant robust centrality of log(IQR)
spectral_score  = clip(power[0.5–8 Hz] / power[0–32 Hz], 0, 1)
motion_score    = 1 - train-participant empirical CDF of ACC RMS
sqi             = geometric_mean(flat_score, amplitude_score, spectral_score, motion_score)
```

Aggregate window SQI into one endpoint value using the 25th percentile across the past 30-minute history. Use three policies:

```yaml
quality_policies:
  - report_only
  - soft_weight
  - hard_exclude_bottom_train_decile
soft_weight:
  minimum_weight: 0.25
hard_exclusion:
  train_quantile: 0.10
  minimum_validation_retention: 0.80
```

Soft weights apply only to model fitting. Validation metrics remain ordinary unweighted metrics. Hard exclusion applies participant-specific thresholds fitted on that participant's train period and must report both retained-set and common-endpoint metrics.

- [ ] **Step 3: Run quality tests**

```powershell
uv run --frozen pytest tests/features/test_trend_conditioning.py tests/features/test_trend_context.py -q
```

Expected: thresholds ignore validation/test fixtures; all aligned context timestamps are at or before the endpoint.

- [ ] **Step 4: Commit SQI and ACC alignment**

```powershell
git add src/glycoband/features/trend_conditioning.py src/glycoband/features/trend_context.py tests/features/test_trend_conditioning.py tests/features/test_trend_context.py configs/probes/trend_signal_learnability-v1.yaml
git commit -m "feat(trend): add motion-aware SQI policies"
```

---

### Task 5: Build versioned development feature artifacts and run Phase 1

**Files:**

- Create: `scripts/run_trend_signal_probe.py`
- Create: `tests/scripts/test_run_trend_signal_probe.py`
- Create: `src/glycoband/evaluation/trend_exploratory.py`
- Create: `tests/evaluation/test_trend_exploratory.py`
- Modify: `configs/probes/trend_signal_learnability-v1.yaml`

**Interfaces:**

- Consumes: development-only endpoints, raw BVP, ACC, fixed conditioning specs, SQI policies.
- Produces: window/history Parquet artifacts, model predictions, participant metrics, paired comparison table, and Phase 1 report.

- [ ] **Step 1: Write runner guards**

```python
def test_probe_loader_refuses_test_rows() -> None:
    frame = probe_fixture()
    frame.loc[0, "split"] = "test"
    with pytest.raises(ValueError, match="final-test"):
        validate_probe_frame(frame)


def test_probe_output_is_non_overwriting(tmp_path: Path) -> None:
    output = tmp_path / "trend-signal-conditioning-v1"
    output.mkdir()
    with pytest.raises(FileExistsError):
        prepare_probe_output(output)
```

- [ ] **Step 2: Write soft-weight and common-endpoint metric tests**

```python
def test_soft_weights_affect_training_not_validation_metric_weights() -> None:
    report = evaluate_conditioning_variants(probe_fixture(), probe_config())
    assert report["validation_weighted"] is False


def test_hard_exclusion_reports_common_endpoint_comparison() -> None:
    report = evaluate_conditioning_variants(probe_fixture(), probe_config())
    hard = report["variants"]["bp_0p7_4_robust__hard_exclude_bottom_train_decile"]
    assert 0.0 <= hard["validation_retention"] <= 1.0
    assert "common_endpoint_macro_f1" in hard
```

- [ ] **Step 3: Implement a cache-first participant pipeline**

The runner must stream one participant at a time, print the participant and stage, and save reusable window-level features before model evaluation. It must not keep 600 million BVP rows in memory.

Endpoint feature identity remains:

```python
ENDPOINT_IDENTITY = ["participant_id", "timestamp"]
PROVENANCE = [
    "history_start",
    "split",
    "label",
    "slope_mg_dl_min",
    "bvp_source_file",
    "protocol_version",
    "split_version",
    "feature_version",
    "conditioning_version",
    "quality_version",
]
```

- [ ] **Step 4: Implement fixed Phase 1 comparisons using Logistic Regression only**

Compare exactly:

1. legacy raw anchor;
2. `bp_0p5_8_zscore` with report-only SQI;
3. `bp_0p7_4_robust` with report-only SQI;
4. the train-resampled better filter with per-participant robust amplitude scaling fitted on that participant's train period;
5. the better conditioning/normalization variant by train-only internal chronological resampling plus soft weighting;
6. the same chosen conditioning variant plus bottom-train-decile hard exclusion;
7. large circular-shift control for the selected candidate.

Implement `inner_chronological_folds(frame: pd.DataFrame, folds: int, embargo_minutes: int) -> list[tuple[np.ndarray, np.ndarray]]`. Each fold must order rows inside every participant, keep training before assessment, and reject any fold whose raw `[history_start, timestamp]` intervals overlap. The choice between variants 2 and 3 and the two normalization policies must use these folds inside the frozen train segment. Validation is evaluated only after one conditioning/normalization choice is locked in the run metadata.

Add this test before implementation:

```python
def test_inner_folds_are_chronological_and_history_disjoint() -> None:
    folds = inner_chronological_folds(probe_fixture().query("split == 'train'"), 3, 30)
    for train_index, assessment_index in folds:
        train = probe_fixture().loc[train_index]
        assessment = probe_fixture().loc[assessment_index]
        for participant_id in assessment["participant_id"].unique():
            left = train[train["participant_id"] == participant_id]
            right = assessment[assessment["participant_id"] == participant_id]
            assert left["timestamp"].max() < right["history_start"].min()
```

- [ ] **Step 5: Write Phase 1 artifacts**

```text
reports/probes/trend-signal-conditioning-v1/
    config.yaml
    environment.txt
    dataset_manifest.json
    metrics.json
    variant_metrics.csv
    per_participant.csv
    quality_retention.csv
    predictions.parquet
    summary.md
    figures/quality_by_participant.png
    figures/quality_vs_error.png
    figures/conditioning_macro_f1.png
    figures/directional_recall.png
```

- [ ] **Step 6: Run Phase 1**

```powershell
uv run --frozen pytest tests/features/test_trend_conditioning.py tests/features/test_trend_context.py tests/evaluation/test_trend_exploratory.py tests/scripts/test_run_trend_signal_probe.py -q
uv run --frozen python scripts/run_trend_signal_probe.py --phase conditioning
```

Expected: the run produces measured development metrics and records `final_test_accessed=false`; no expected score is asserted.

- [ ] **Step 7: Commit Phase 1 code and evidence**

```powershell
git add scripts/run_trend_signal_probe.py src/glycoband/evaluation/trend_exploratory.py tests/scripts/test_run_trend_signal_probe.py tests/evaluation/test_trend_exploratory.py reports/probes/trend-signal-conditioning-v1
git commit -m "research(trend): evaluate conditioning and SQI"
```

**Decision gate:** Proceed to physiological enrichment if at least one of these is true:

- selected conditioning candidate improves validation Macro-F1 by at least `0.02` versus the raw LR anchor and has nonzero recall for both directions;
- high-SQI validation endpoints outperform low-SQI endpoints by at least `0.03` Macro-F1 with the same fixed model;
- within-participant slope correlations increase consistently for a coherent BVP feature family.

Otherwise conclude `NOT_SUPPORTED_BY_CONDITIONING` and stop before feature/model expansion unless the error analysis identifies one concrete, testable peak-detection or alignment failure.

---

### Task 6: Add BVP-derived physiological feature families and Phase 2 ablations

**Files:**

- Create: `src/glycoband/features/trend_physiology.py`
- Create: `tests/features/test_trend_physiology.py`
- Modify: `scripts/run_trend_signal_probe.py`
- Modify: `src/glycoband/evaluation/trend_exploratory.py`
- Modify: `tests/evaluation/test_trend_exploratory.py`
- Modify: `configs/probes/trend_signal_learnability-v1.yaml`

**Interfaces:**

- Consumes: selected conditioned BVP windows from Phase 1.
- Produces four separable feature families: `pulse_rate`, `hrv_30m`, `morphology`, and `spectral_30m`.

- [ ] **Step 1: Write synthetic pulse-train tests**

```python
def test_peak_features_recover_known_sixty_bpm_signal() -> None:
    rate_hz = 64
    values = synthetic_pulse_train(rate_hz=rate_hz, seconds=30, bpm=60)
    features = pulse_window_features(values, rate_hz)
    assert features["heart_rate_median_bpm"] == pytest.approx(60.0, abs=3.0)
    assert features["valid_peak_count"] >= 28


def test_hrv_requires_sufficient_beat_history() -> None:
    result = hrv_history_features(np.array([1.0, 1.0, 1.0]))
    assert result["hrv_valid"] is False
    assert np.isnan(result["rmssd_ms"])
```

- [ ] **Step 2: Implement robust peak and morphology features**

Peak detection must operate on selected conditioned BVP and declare physiologic bounds rather than tuning to validation:

```text
heart-rate bounds: 35–220 bpm
minimum peak distance: floor(64 × 60 / 220) samples
minimum valid peaks per 30-second window: 15
prominence scale: 0.25 × window robust IQR
```

Per-window pulse features:

- valid peak count;
- median/IQR heart rate;
- median/IQR inter-beat interval;
- median/IQR pulse amplitude;
- median/IQR rise time;
- median/IQR pulse width at half prominence;
- peak-detection validity fraction.

- [ ] **Step 3: Implement 30-minute HRV and spectral features**

Compute SDNN, RMSSD, and pNN50 from valid BVP-derived beat intervals over the full past 30-minute history. Compute LF/HF only at the 30-minute history level, never from a 30-second window. Require at least 5 minutes of valid beat coverage and report an explicit validity flag.

Spectral features use Welch PSD and include:

- dominant BVP frequency in 0.5–4 Hz;
- normalized power in 0.5–4 Hz;
- spectral entropy;
- HRV LF power 0.04–0.15 Hz;
- HRV HF power 0.15–0.40 Hz;
- LF/HF ratio when both bands have finite support.

- [ ] **Step 4: Run physiological feature tests**

```powershell
uv run --frozen pytest tests/features/test_trend_physiology.py tests/features/test_trend_conditioning.py -q
```

Expected: known synthetic pulse rates are recovered; invalid short histories yield flagged missing values rather than fabricated values.

- [ ] **Step 5: Evaluate single-family ablations with LR**

Compare on identical validation endpoints:

```text
conditioned_statistics
conditioned_statistics + pulse_rate
conditioned_statistics + hrv_30m
conditioned_statistics + morphology
conditioned_statistics + spectral_30m
conditioned_statistics + all physiological families
```

Run unweighted LR first, then `class_weight="balanced"` only for the best train-resampled family. Do not oversample in this phase; duplicating autocorrelated windows adds less information than class weighting.

- [ ] **Step 6: Add declared context/confounding comparisons**

Create past-only endpoint features:

- ACC RMS mean/max/trend over 30 minutes;
- skin-temperature mean/trend over 30 minutes;
- elapsed minutes since the most recent food-log event at or before `t`, capped at 720 minutes;
- hour-of-day sine/cosine.

Report three models separately:

```text
context_only
bvp_only
bvp_plus_context
```

If `context_only` matches or exceeds `bvp_plus_context`, do not claim that BVP carries the gain.

- [ ] **Step 7: Run and save Phase 2**

```powershell
uv run --frozen pytest tests/features/test_trend_physiology.py tests/features/test_trend_context.py tests/evaluation/test_trend_exploratory.py -q
uv run --frozen python scripts/run_trend_signal_probe.py --phase enrichment
```

Expected: output includes feature-family validity/coverage, correlation diagnostics, common-endpoint ablations, participant metrics, shift controls, and `final_test_accessed=false`.

- [ ] **Step 8: Commit Phase 2**

```powershell
git add src/glycoband/features/trend_physiology.py src/glycoband/features/trend_context.py tests/features/test_trend_physiology.py tests/features/test_trend_context.py scripts/run_trend_signal_probe.py src/glycoband/evaluation/trend_exploratory.py tests/evaluation/test_trend_exploratory.py reports/probes/trend-feature-enrichment-v1
git commit -m "research(trend): evaluate physiological feature families"
```

**Decision gate:** Proceed to Phase 3 only if one BVP-only feature family improves Macro-F1 by at least `0.02` over the selected Phase 1 candidate, both directional recalls are nonzero, and the temporal-shift control loses the gain. Otherwise stop with `NOT_SUPPORTED_BY_ENRICHED_FEATURES`.

---

### Task 7: Evaluate binary and hierarchical formulations without replacing the target

**Files:**

- Modify: `src/glycoband/evaluation/trend_exploratory.py`
- Modify: `tests/evaluation/test_trend_exploratory.py`
- Modify: `scripts/run_trend_signal_probe.py`
- Modify: `configs/probes/trend_signal_learnability-v1.yaml`

**Interfaces:**

- Consumes: the selected Phase 2 BVP-only feature set and unchanged frozen three-class labels.
- Produces: binary `STABLE/CHANGE` metrics and end-to-end hierarchical three-class metrics.

- [ ] **Step 1: Write hierarchical routing tests**

```python
def test_hierarchical_prediction_routes_stable_without_direction_model() -> None:
    stage_one = pd.Series(["STABLE", "CHANGE", "CHANGE"])
    stage_two = pd.Series(["RISING", "FALLING"])
    assert hierarchical_labels(stage_one, stage_two).tolist() == [
        "STABLE",
        "RISING",
        "FALLING",
    ]


def test_direction_stage_trains_only_on_true_directional_train_rows() -> None:
    train = probe_fixture()
    selected = direction_training_rows(train)
    assert set(selected["label"]) == {"FALLING", "RISING"}
    assert set(selected["split"]) == {"train"}
```

- [ ] **Step 2: Implement the fixed formulations**

```text
Binary:
  STABLE -> STABLE
  FALLING/RISING -> CHANGE

Hierarchical stage 1:
  class-weighted LR predicts STABLE vs CHANGE

Hierarchical stage 2:
  class-weighted LR trained only on true FALLING/RISING train rows
  predicts FALLING vs RISING only when stage 1 predicts CHANGE
```

Report binary Macro-F1/change recall and full end-to-end three-class Macro-F1, directional recalls, and opposite-direction error. Do not report stage-2 performance alone as the system result.

- [ ] **Step 3: Add descriptive tau sensitivity without target promotion**

Using development slope values only, produce class support and label-transition tables for tau `0.3`, `0.5`, and `0.7` mg/dL/min. If a cheap LR comparison is run, label it `exploratory_learnability` and state that score cannot determine the clinically/scientifically correct threshold.

- [ ] **Step 4: Run Phase 3**

```powershell
uv run --frozen pytest tests/evaluation/test_trend_exploratory.py -q
uv run --frozen python scripts/run_trend_signal_probe.py --phase formulation
```

Expected: current target remains untouched; the report distinguishes three-class, binary, and hierarchical questions and records no test access.

- [ ] **Step 5: Commit Phase 3**

```powershell
git add src/glycoband/evaluation/trend_exploratory.py tests/evaluation/test_trend_exploratory.py scripts/run_trend_signal_probe.py configs/probes/trend_signal_learnability-v1.yaml reports/probes/trend-formulation-v1
git commit -m "research(trend): compare binary and hierarchical probes"
```

**Human checkpoint:** Binary/hierarchical or tau changes cannot become registered evidence until the project lead explicitly approves a target/label revision. A better score is not approval.

---

### Task 8: Run fixed three-class Random Forest and XGBoost capacity checks only after the feature gate

**Files:**

- Modify: `src/glycoband/evaluation/trend_exploratory.py`
- Modify: `tests/evaluation/test_trend_exploratory.py`
- Modify: `configs/probes/trend_signal_learnability-v1.yaml`
- Modify: `scripts/run_trend_signal_probe.py`

**Interfaces:**

- Consumes: exactly one selected BVP-only feature representation and the unchanged frozen three-class target. Binary/hierarchical capacity expansion requires a later human-approved plan.
- Produces: fixed-capacity comparisons, not a hyperparameter sweep.

- [ ] **Step 1: Add deterministic model-factory tests**

```python
def test_model_factory_uses_fixed_capacity_and_seed() -> None:
    models = build_capacity_models(seed=20260825)
    assert models["random_forest"].n_estimators == 300
    assert models["random_forest"].max_depth == 6
    assert models["xgboost"].n_estimators == 300
    assert models["xgboost"].max_depth == 3
```

- [ ] **Step 2: Implement the fixed models**

```python
RandomForestClassifier(
    n_estimators=300,
    max_depth=6,
    min_samples_leaf=20,
    class_weight="balanced_subsample",
    n_jobs=4,
    random_state=20260825,
)

XGBClassifier(
    n_estimators=300,
    max_depth=3,
    learning_rate=0.03,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="multi:softprob",
    num_class=3,
    eval_metric="mlogloss",
    n_jobs=4,
    random_state=20260825,
)
```

Do not add a grid search, Bayesian optimization, early-stopping choice on sealed data, or model-family expansion.

- [ ] **Step 3: Run capacity comparisons and negative controls**

```powershell
uv run --frozen pytest tests/evaluation/test_trend_exploratory.py -q
uv run --frozen python scripts/run_trend_signal_probe.py --phase capacity
```

Each model must run the same aligned features, current-window ablation where meaningful, and large temporal-shift control.

- [ ] **Step 4: Commit fixed-capacity evidence**

```powershell
git add src/glycoband/evaluation/trend_exploratory.py tests/evaluation/test_trend_exploratory.py configs/probes/trend_signal_learnability-v1.yaml scripts/run_trend_signal_probe.py reports/probes/trend-feature-enrichment-v1
git commit -m "research(trend): add gated classical capacity checks"
```

**Stop gate:** If enriched LR fails the Task 6 gate, Task 8 must not run. XGBoost cannot rescue an empty representation into a scientific claim.

---

### Task 9: Produce the final development decision package

**Files:**

- Create: `reports/probes/trend-signal-learnability-v1-decision.md`
- Modify: `docs/research/journal.md` only with the final concise finding, not a transcript.
- Modify: `docs/research/readiness_contract.md` only if an evidence artifact genuinely changes a gate status.
- Do not modify: `docs/research/decision_register.md` without explicit project-lead freeze approval.

**Interfaces:**

- Consumes: completed phase summaries and exact paired endpoint/participant metrics.
- Produces: one conclusion and one next action.

- [ ] **Step 1: Reconcile artifacts programmatically**

Verify:

```text
same dataset version
same frozen label version
same split version
same allowed endpoint identities
no test rows
all config and artifact hashes present
all chosen candidates have baseline and shift-control comparisons
all per-participant totals reconcile with pooled totals
```

- [ ] **Step 2: Apply the predeclared promotion gate**

The decision writer must derive one of the four ocean outcomes mechanically from recorded metrics. It must not relax thresholds after seeing results.

- [ ] **Step 3: Write the methodology paragraph**

Use this wording unless the measured evidence requires a more conservative statement:

```text
The initial classical baseline using 50 simple statistical features from unconditioned wrist BVP did not show directional information beyond the constant predictor (development-validation Macro-F1 0.2889 versus 0.2869). We therefore tested, on development data only, whether fixed signal conditioning, an explicit motion-aware SQI, and predeclared physiological feature families changed learnability under the same frozen Recent Trend label and chronological split. Model capacity was increased only after a feature-level gate, and all comparisons retained constant, current-window, temporal-shift, per-class, and per-participant controls. These results remain feasibility evidence and do not establish direct glucose measurement, new-user generalization, clinical utility, or device validity.
```

- [ ] **Step 4: Run proportional final verification**

```powershell
uv sync --frozen
uv lock --check
uv run --frozen pytest
uv run --frozen ruff check .
uv run --frozen mypy
```

Expected: all checks pass or pre-existing unrelated failures are separated with exact evidence. Verify the report contains `Final-test performance accessed: NO`.

- [ ] **Step 5: Commit the decision package**

```powershell
git add reports/probes/trend-signal-learnability-v1-decision.md docs/research/journal.md docs/research/readiness_contract.md
git commit -m "docs(trend): record signal learnability decision"
```

Do not open the final test. If the result is `SUPPORTED_FOR_FREEZE_REVIEW`, stop and request project-lead review of the exact preprocessing, SQI, features, target, model, and success criteria.

---

## Explicitly deferred work

These are not implementation tasks in this plan:

- future prediction at 15/30/45 minutes;
- raw-BVP 1D-CNN/LSTM/Transformer;
- promotion of ACC, temperature, food timing, or other modalities into the core predictor;
- oversampling temporally correlated feature rows;
- calibration/OOD/device integration;
- opening or evaluating the sealed test;
- adding another dataset or claiming unseen-subject generalization.

If and only if the final development gate passes, write a separate registered-experiment freeze plan. If it fails, the correct result is a bounded negative finding, not another automatic model family.
