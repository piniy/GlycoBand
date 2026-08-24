# Trend Registered Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the first reproducible, leakage-safe BIG IDEAs Trend development-validation evidence package using majority, always-`STABLE`, and Logistic Regression baselines without accessing final-test performance.

**Architecture:** First repair the Gate D approval and manifest provenance so registered development has a clean scientific anchor. Then repair and freeze a minimal BVP feature contract, evaluate explicit baseline and negative-control variants through one configuration-driven evaluator, and generate a non-overwriting experiment bundle from train/validation rows only. The sealed test remains represented in the split contract but is never loaded into the feature or modeling path.

**Tech Stack:** Python 3.11, pandas, NumPy, PyArrow, scikit-learn, PyYAML, matplotlib, pytest, Ruff, mypy, `uv`, JSON, Parquet, and Git.

## Global Constraints

- Use BIG IDEAs v1.1.3 only; never combine its rows with Hb-PPG.
- Use native wrist BVP history only as predictor input; CGM remains label/reference data only.
- Preserve `trend-label-v1`: H30, median3, OLS, `tau=0.5 mg/dL/min`, at least 80% CGM support, and continuous BVP history.
- Preserve `trend-split-v1`: within-person chronological 60/20/20 with a 30-minute embargo and no raw-history overlap.
- Read only `train` and `validation` rows during this plan. Reject `test` and `excluded_embargo` rows at every development boundary.
- Do not modify `data/raw/`.
- Do not reopen State, Model 2B, PhysioCGM, synthetic robustness, Decision Engine integration, or physical-device claims.
- Do not introduce deep learning, hyperparameter search, calibration, or OOD modeling in this baseline lake.
- Do not silently alter the frozen Trend label, split, claim ceiling, or final-test policy.
- Do not overwrite an existing experiment directory or frozen artifact.
- Preserve unrelated worktree changes; stage and commit only files named by the active task.
- Run the locked environment checks serially before declaring the ocean complete.

## Ocean, Lakes, and Exit Gates

**Authorized ocean:** A registered-development Trend baseline evidence package on the frozen train/validation contract.

**Lake 1 — Scientific anchor repair:** Project-lead approval is versioned before a clean manifest regeneration; the manifest records a clean Git revision plus endpoint and source-manifest hashes.

**Lake 2 — Feature contract:** The BVP feature implementation has correct physical units, participant isolation, causal H30 coverage, explicit provenance, and tests that reject the demonstrated failure modes.

**Lake 3 — Registered baseline:** Constants, aligned Logistic Regression, current-window ablation, and within-participant circular-shift control produce validation-only metrics and diagnostic artifacts.

**Ocean exit gate:** Every lake passes; the full locked test/lint/type suite passes; a read-only reviewer returns `PASS`; the resulting report states `supported`, `partially supported`, `not supported`, or `insufficient evidence`; and no final-test performance was loaded or reported.

## Non-goals

- Opening or scoring the final-test partition.
- Selecting a production model.
- Random Forest, XGBoost, SVM, or neural-network development.
- Calibration, OOD policy, synthetic degradation, device validation, or clinical interpretation.
- Changing Trend label semantics to improve a model result.

---

### Task 1: Version the Existing Project-Lead Approval

**Files:**
- Inspect: `docs/research/gate_d_decision_brief.md`
- Commit only: `docs/research/gate_d_decision_brief.md`

**Interfaces:**
- Consumes: the existing worktree line `APPROVE TREND GATE D PACKAGE - RNA`.
- Produces: a Git commit that predates the regenerated Trend manifest and is auditable as the human approval record.

- [x] **Step 1: Verify the approval is present without manufacturing or rewriting it**

Run:

```powershell
Select-String -LiteralPath docs/research/gate_d_decision_brief.md -Pattern '^APPROVE TREND GATE D PACKAGE - RNA$'
git diff -- docs/research/gate_d_decision_brief.md
```

Expected: exactly one matching approval line, and the diff adds only that signed approval record.

- [x] **Step 2: Confirm unrelated work remains unstaged**

Run:

```powershell
git status --short
git diff --cached --name-only
```

Expected: the worktree may contain unrelated changes, but the index is empty.

- [x] **Step 3: Commit only the approval record**

```powershell
git add -- docs/research/gate_d_decision_brief.md
git diff --cached --check
git diff --cached --name-only
git commit -m "docs(research): record Trend Gate D approval"
```

Expected: the staged-name check lists only `docs/research/gate_d_decision_brief.md`; the commit succeeds.

- [x] **Step 4: Record the approval commit for later verification**

Run:

```powershell
git log -1 --format='%H %aI %s'
git show HEAD:docs/research/gate_d_decision_brief.md | Select-String 'APPROVE TREND GATE D PACKAGE - RNA'
```

Expected: the committed file contains the signed approval line.

---

### Task 2: Enforce the Frozen Endpoint Contract and Clean Manifest Provenance

**Files:**
- Modify: `src/glycoband/labels/trend.py`
- Modify: `src/glycoband/evaluation/trend_manifest.py`
- Modify: `scripts/build_trend_split_manifest.py`
- Modify: `tests/labels/test_trend.py`
- Modify: `tests/scripts/test_build_trend_split_manifest.py`

**Interfaces:**
- Consumes: `TrendProtocol`, the generated endpoint frame, `data/manifests/source_manifest.json`, and the ignored endpoint Parquet.
- Produces: `validate_endpoint_frame(...)` that enforces H30/support/provenance and `build_manifest_payload(...)` that refuses dirty revisions and records SHA-256 identities.

- [x] **Step 1: Add failing endpoint-contract tests**

Add these tests to `tests/labels/test_trend.py`:

```python
def test_validate_endpoint_frame_rejects_wrong_history_duration() -> None:
    protocol = load_trend_protocol(_protocol_path())
    frame = _endpoints().copy()
    frame["protocol_version"] = protocol.version
    frame["slope_method"] = protocol.slope_method
    frame.loc[0, "history_start"] = frame.loc[0, "timestamp"] - pd.Timedelta(minutes=15)

    with pytest.raises(ValueError, match="30-minute history"):
        validate_endpoint_frame(frame, protocol)


def test_validate_endpoint_frame_rejects_insufficient_cgm_support() -> None:
    protocol = load_trend_protocol(_protocol_path())
    frame = _endpoints().copy()
    frame["protocol_version"] = protocol.version
    frame["slope_method"] = protocol.slope_method
    frame.loc[0, "support_points"] = 1

    with pytest.raises(ValueError, match="CGM support"):
        validate_endpoint_frame(frame, protocol)


def test_validate_endpoint_frame_rejects_protocol_provenance_mismatch() -> None:
    protocol = load_trend_protocol(_protocol_path())
    frame = _endpoints().copy()
    frame["protocol_version"] = "wrong-version"
    frame["slope_method"] = protocol.slope_method

    with pytest.raises(ValueError, match="protocol version"):
        validate_endpoint_frame(frame, protocol)
```

Also update `_endpoints()` so valid fixtures include:

```python
"protocol_version": ["trend-label-v1"] * 3,
"slope_method": ["ols"] * 3,
```

- [x] **Step 2: Run the endpoint tests and confirm the demonstrated hazards fail**

Run:

```powershell
uv run --frozen pytest -q tests/labels/test_trend.py
```

Expected: the three new tests fail because the validator currently accepts short history, one support point, and mismatched protocol provenance.

- [x] **Step 3: Implement exact endpoint validation**

In `src/glycoband/labels/trend.py`, add `math`, require the two provenance columns, and extend `validate_endpoint_frame` with:

```python
BIG_IDEAS_CGM_CADENCE_MINUTES = 5

REQUIRED_ENDPOINT_COLUMNS = frozenset(
    {
        "participant_id",
        "protocol_version",
        "timestamp",
        "history_start",
        "label",
        "support_points",
        "slope_method",
        "bvp_source_file",
        "cgm_source_file",
    }
)


def _minimum_cgm_support_points(protocol: TrendProtocol) -> int:
    expected = protocol.history_minutes / BIG_IDEAS_CGM_CADENCE_MINUTES + 1
    return math.ceil(expected * protocol.minimum_support_fraction)
```

After parsing timestamps in `validate_endpoint_frame`, add:

```python
expected_history = pd.Timedelta(minutes=protocol.history_minutes)
if not ((timestamps - history_start) == expected_history).all():
    raise ValueError("Every Trend endpoint must retain the frozen 30-minute history")
if (frame["support_points"] < _minimum_cgm_support_points(protocol)).any():
    raise ValueError("Trend endpoint does not satisfy frozen CGM support")
if not (frame["protocol_version"].astype(str) == protocol.version).all():
    raise ValueError("Trend endpoint protocol version does not match the frozen contract")
if not (frame["slope_method"].astype(str) == protocol.slope_method).all():
    raise ValueError("Trend endpoint slope method does not match the frozen contract")
for column in ("participant_id", "bvp_source_file", "cgm_source_file"):
    if frame[column].isna().any() or frame[column].astype(str).str.strip().eq("").any():
        raise ValueError(f"Trend endpoint column {column!r} contains empty provenance")
```

- [x] **Step 4: Run endpoint tests**

Run:

```powershell
uv run --frozen pytest -q tests/labels/test_trend.py tests/evaluation/test_trend_split.py
```

Expected: all tests pass.

- [x] **Step 5: Add failing clean-manifest and checksum tests**

Update `tests/scripts/test_build_trend_split_manifest.py` so every `build_manifest_payload` call passes endpoint and source hashes. Add:

Also update `_split_frame()` before split assignment:

```python
frame["protocol_version"] = protocol.version
frame["slope_method"] = protocol.slope_method
```

Then add:

```python
def test_manifest_payload_refuses_dirty_git_state(protocol) -> None:
    with pytest.raises(ValueError, match="clean Git revision"):
        build_manifest_payload(
            _split_frame(protocol),
            protocol,
            git_revision="abc123",
            git_dirty=True,
            endpoint_artifact_sha256="a" * 64,
            source_manifest_sha256="b" * 64,
        )


def test_manifest_payload_records_artifact_hashes(protocol) -> None:
    payload = build_manifest_payload(
        _split_frame(protocol),
        protocol,
        git_revision="abc123",
        git_dirty=False,
        endpoint_artifact_sha256="a" * 64,
        source_manifest_sha256="b" * 64,
    )

    assert payload["endpoint_artifact"] == {
        "path": "data/interim/trend/trend-label-v1.parquet",
        "sha256": "a" * 64,
    }
    assert payload["source_manifest_sha256"] == "b" * 64
```

- [x] **Step 6: Run the manifest tests and verify failure**

Run:

```powershell
uv run --frozen pytest -q tests/scripts/test_build_trend_split_manifest.py
```

Expected: failure because the manifest function does not accept or record hashes and does not reject dirty Git state.

- [x] **Step 7: Implement clean manifest requirements**

Change `build_manifest_payload` in `src/glycoband/evaluation/trend_manifest.py` to accept:

```python
def build_manifest_payload(
    split_frame: pd.DataFrame,
    protocol: TrendProtocol,
    *,
    git_revision: str | None,
    git_dirty: bool | None,
    endpoint_artifact_sha256: str,
    source_manifest_sha256: str,
) -> dict[str, object]:
```

Validate and include:

```python
if not git_revision or git_dirty is not False:
    raise ValueError("Frozen Trend manifest requires a clean Git revision")
for name, digest in (
    ("endpoint artifact", endpoint_artifact_sha256),
    ("source manifest", source_manifest_sha256),
):
    if len(digest) != 64 or any(character not in "0123456789abcdefABCDEF" for character in digest):
        raise ValueError(f"{name} SHA-256 is invalid")
```

Add these payload fields:

```python
"endpoint_artifact": {
    "path": "data/interim/trend/trend-label-v1.parquet",
    "sha256": endpoint_artifact_sha256.lower(),
},
"source_manifest_sha256": source_manifest_sha256.lower(),
```

- [x] **Step 8: Hash artifacts in the manifest runner before writing JSON**

Add to `scripts/build_trend_split_manifest.py`:

```python
import hashlib


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
```

Replace the manifest call with:

```python
manifest = build_manifest_payload(
    split_frame,
    protocol,
    git_revision=_git_revision(root),
    git_dirty=_git_dirty(root),
    endpoint_artifact_sha256=_sha256(endpoint_path),
    source_manifest_sha256=_sha256(root / "data/manifests/source_manifest.json"),
)
```

- [x] **Step 9: Run focused tests, lint, and types**

Run:

```powershell
uv run --frozen pytest -q tests/labels/test_trend.py tests/evaluation/test_trend_split.py tests/scripts/test_build_trend_split_manifest.py
uv run --frozen ruff check src/glycoband/labels/trend.py src/glycoband/evaluation/trend_manifest.py scripts/build_trend_split_manifest.py tests/labels/test_trend.py tests/scripts/test_build_trend_split_manifest.py
uv run --frozen mypy src/glycoband/labels/trend.py src/glycoband/evaluation/trend_manifest.py scripts/build_trend_split_manifest.py
```

Expected: all commands exit `0`.

- [x] **Step 10: Commit the endpoint and manifest guards**

```powershell
git add -- src/glycoband/labels/trend.py src/glycoband/evaluation/trend_manifest.py scripts/build_trend_split_manifest.py tests/labels/test_trend.py tests/scripts/test_build_trend_split_manifest.py
git diff --cached --check
git commit -m "fix(trend): enforce frozen endpoint provenance"
```

---

### Task 3: Regenerate the Trend Split Anchor From a Clean Revision

**Files:**
- Regenerate: `data/interim/trend/trend-label-v1.parquet`
- Modify: `data/manifests/trend_split-v1.json`
- Modify: `docs/research/journal.md`

**Interfaces:**
- Consumes: committed project-lead approval and committed endpoint/manifest guards.
- Produces: a clean, hashed `trend-split-v1` anchor for downstream registered development.

- [x] **Step 1: Verify the scoped source tree is clean enough to regenerate**

Run:

```powershell
git status --short
git diff -- docs/research/gate_d_decision_brief.md src/glycoband/labels/trend.py src/glycoband/evaluation/trend_manifest.py scripts/build_trend_split_manifest.py
```

Expected: no changes in the listed scientific-anchor files. Unrelated user changes may remain, but the manifest runner must still refuse to write a frozen manifest while Git reports dirty.

- [x] **Step 2: Use a clean worktree at execution time if unrelated changes remain**

Do not stash, reset, or discard the user’s work. Create a temporary clean worktree from the current committed branch using the execution workflow’s worktree skill, copy no uncommitted files into it, and run all remaining Task 3 commands there.

Expected: `git status --porcelain` in the execution worktree returns no output.

- [x] **Step 3: Regenerate the endpoint Parquet and split manifest**

Run:

```powershell
uv run --frozen python scripts/build_trend_split_manifest.py
```

Expected: 16 participants, 27,913 endpoints, 27,529 usable endpoints, 384 embargo exclusions, and `final_test_accessed=false`.

- [x] **Step 4: Verify Git identity and both hashes**

Run:

```powershell
uv run --frozen python -c "import hashlib,json,pathlib,subprocess; root=pathlib.Path('.'); m=json.loads((root/'data/manifests/trend_split-v1.json').read_text()); endpoint=root/m['endpoint_artifact']['path']; h=lambda p: hashlib.sha256(p.read_bytes()).hexdigest(); head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(); assert m['git_revision']==head; assert m['git_dirty'] is False; assert m['endpoint_artifact']['sha256']==h(endpoint); assert m['source_manifest_sha256']==h(root/'data/manifests/source_manifest.json'); assert m['final_test_accessed'] is False; print('PASS clean revision and hashes')"
```

Expected: `PASS clean revision and hashes`.

- [x] **Step 5: Append a compact audit correction to the journal**

Append this exact section to `docs/research/journal.md`:

```markdown
## 2026-08-25 — Trend split provenance repaired

Question:
Can the frozen Trend split be regenerated after the project-lead approval is versioned and from a clean, reproducible Git revision?

Evidence / implementation:
The signed Gate D approval was committed before regeneration. The endpoint Parquet and source manifest now have SHA-256 identities in `trend-split-v1`, and the manifest records `git_dirty=false` for the exact generator revision.

Finding:
The Trend label and chronological split now provide a clean registered-development anchor. Endpoint counts and split boundaries are unchanged from the approved package.

What this does not prove:
This repair does not establish BVP learnability and does not authorize final-test access.

Decision / next direction:
Proceed to the predeclared train/validation-only baseline feature and control package.
```

- [x] **Step 6: Commit the regenerated anchor and journal correction**

```powershell
git add -- data/manifests/trend_split-v1.json docs/research/journal.md
git diff --cached --check
git commit -m "fix(trend): regenerate clean split provenance"
```

Do not force-add the ignored endpoint Parquet; its content identity is carried by the committed manifest hash.

---

### Task 4: Repair and Freeze the Minimal Trend Feature Contract

**Files:**
- Create: `configs/trend/baseline-v1.yaml`
- Modify: `src/glycoband/features/trend.py`
- Modify: `src/glycoband/features/__init__.py`
- Modify: `tests/features/test_trend.py`

**Interfaces:**
- Consumes: BVP CSV paths, development endpoints, `trend-label-v1`, and `trend-split-v1`.
- Produces: `extract_bvp_window_features(...) -> pd.DataFrame` and `aggregate_bvp_history_features(...) -> pd.DataFrame` with causal H30 features and explicit provenance.

- [x] **Step 1: Create the predeclared baseline configuration**

Create `configs/trend/baseline-v1.yaml` with:

```yaml
experiment:
  id: trend-baseline-v1
  evidence_level: registered_development
  claim_ceiling: feasibility_only
dataset:
  name: big_ideas
  version: 1.1.3
  independent_unit: participant
label:
  version: trend-label-v1
split:
  version: trend-split-v1
  allowed_development_splits: [train, validation]
  forbidden_splits: [test, excluded_embargo]
feature:
  version: trend-feature-v1
  short_window_seconds: 30
  history_minutes: 30
  minimum_complete_windows: 59
  short_window_features:
    - mean
    - std
    - min
    - max
    - q25
    - q75
    - mean_abs_diff
    - diff_std
    - flat_fraction
    - slope_per_min
  history_aggregations: [mean, std, min, max, last]
preprocessing:
  detrend: none
  filter: none
  amplitude_normalization: none
  sqi_policy: report_only_no_exclusion
models:
  - majority
  - always_stable
  - logistic_history
  - logistic_current_window
  - logistic_shifted_control
logistic_regression:
  imputer: median
  scaler: standard
  class_weight: null
  max_iter: 1000
  random_state: 20260825
control:
  circular_shift_fraction: 0.5
evaluation:
  primary_metric: macro_f1
  bootstrap_participant_repeats: 2000
  bootstrap_seed: 20260825
  report_balanced_accuracy: true
  report_directional_recall: true
  report_opposite_direction_error_rate: true
go_no_go:
  require_aligned_ci_above_best_constant: true
  require_aligned_ci_above_shift_control: true
  require_nonzero_falling_recall: true
  require_nonzero_rising_recall: true
```

The value `59` is derived, not tuned: a continuous arbitrary-alignment 30-minute interval contains at least 59 complete non-overlapping 30-second windows.

The preprocessing policy is intentionally a frozen raw-feature baseline, not an optimized pipeline. Signal-quality fields remain visible for interpretation, but this lake does not select an SQI threshold from validation performance.

- [x] **Step 2: Add failing physical-unit, isolation, coverage, provenance, and test-seal tests**

Add to `tests/features/test_trend.py`:

```python
def test_window_slope_is_reported_per_minute(tmp_path: Path) -> None:
    path = tmp_path / "BVP.csv"
    timestamps = pd.date_range("2020-01-01", periods=8, freq="250ms")
    seconds = np.arange(8, dtype=float) / 4.0
    pd.DataFrame({"datetime": timestamps, "bvp": seconds}).to_csv(path, index=False)

    windows = extract_bvp_window_features(
        path,
        rate_hz=4,
        window_seconds=2,
        maximum_gap_seconds=0.251,
    )

    assert windows.loc[0, "slope_per_min"] == pytest.approx(60.0)


def test_history_aggregation_requires_participant_identity() -> None:
    windows = _valid_windows().drop(columns="participant_id")
    endpoints = _valid_endpoints()

    with pytest.raises(ValueError, match="participant_id"):
        aggregate_bvp_history_features(
            windows,
            endpoints,
            history_minutes=30,
            window_seconds=30,
            minimum_complete_windows=59,
        )


def test_history_aggregation_rejects_final_test_rows() -> None:
    endpoints = _valid_endpoints()
    endpoints.loc[0, "split"] = "test"

    with pytest.raises(ValueError, match="final-test|development splits"):
        aggregate_bvp_history_features(
            _valid_windows(),
            endpoints,
            history_minutes=30,
            window_seconds=30,
            minimum_complete_windows=59,
        )


def test_history_aggregation_preserves_provenance() -> None:
    features = aggregate_bvp_history_features(
        _valid_windows(),
        _valid_endpoints(),
        history_minutes=30,
        window_seconds=30,
        minimum_complete_windows=59,
    )

    assert {
        "participant_id",
        "bvp_source_file",
        "protocol_version",
        "split_version",
        "feature_version",
    }.issubset(features.columns)
    assert set(features["feature_version"]) == {"trend-feature-v1"}
```

Implement `_valid_windows()` and `_valid_endpoints()` as deterministic 30-minute fixtures with one participant, 60 contiguous 30-second windows, `train` split, `trend-label-v1`, `trend-split-v1`, and a real-looking source path.

- [x] **Step 3: Run the feature tests and confirm failure**

Run:

```powershell
uv run --frozen pytest -q tests/features/test_trend.py
```

Expected: failures expose the current `15` versus `60` slope error, missing participant enforcement, test-row acceptance, and lost provenance.

- [x] **Step 4: Correct slope units using actual timestamps**

In `_window_feature_rows`, calculate OLS slopes against elapsed minutes rather than sample indices:

```python
time_ns = time_matrix.astype("datetime64[ns]").astype(np.int64)
elapsed_minutes = (time_ns - time_ns[:, [0]]) / (60.0 * 1_000_000_000.0)
centered_minutes = elapsed_minutes - elapsed_minutes.mean(axis=1, keepdims=True)
denominator = np.sum(centered_minutes**2, axis=1)
if np.any(denominator <= 0):
    raise ValueError("BVP window timestamps must span positive elapsed time")
slopes = np.sum((matrix - means[:, None]) * centered_minutes, axis=1) / denominator
```

Remove the existing sample-index calculation and the `* 60.0` scaling.

- [x] **Step 5: Enforce development-only participant-isolated aggregation**

Set:

```python
FEATURE_VERSION = "trend-feature-v1"
DEVELOPMENT_SPLITS = frozenset({"train", "validation"})
ENDPOINT_COLUMNS = (
    "participant_id",
    "timestamp",
    "history_start",
    "split",
    "label",
    "bvp_source_file",
    "protocol_version",
    "split_version",
)
```

Change the public aggregation signature to:

```python
def aggregate_bvp_history_features(
    windows: pd.DataFrame,
    endpoints: pd.DataFrame,
    *,
    history_minutes: int,
    window_seconds: int,
    minimum_complete_windows: int,
) -> pd.DataFrame:
```

Before grouping, require `participant_id` in `windows`, reject endpoint splits outside `DEVELOPMENT_SPLITS`, require positive settings, and assert:

```python
derived_minimum = history_minutes * 60 // window_seconds - 1
if minimum_complete_windows != derived_minimum:
    raise ValueError("Minimum complete windows must be derived from H30 and window duration")
```

Within `_aggregate_history`, require at least `minimum_complete_windows`, require all selected rows to match the endpoint participant, and add these fields to the result:

```python
"bvp_source_file": endpoint["bvp_source_file"],
"protocol_version": endpoint["protocol_version"],
"split_version": endpoint["split_version"],
"feature_version": FEATURE_VERSION,
```

- [x] **Step 6: Export the feature contract**

Update `src/glycoband/features/__init__.py` to import in Ruff-sorted order and export:

```python
from glycoband.features.trend import (
    FEATURE_VERSION,
    SHORT_WINDOW_FEATURES,
    aggregate_bvp_history_features,
    extract_bvp_window_features,
)

__all__ = [
    "FEATURE_VERSION",
    "SHORT_WINDOW_FEATURES",
    "aggregate_bvp_history_features",
    "extract_bvp_window_features",
]
```

- [x] **Step 7: Run feature validation**

Run:

```powershell
uv run --frozen pytest -q tests/features/test_trend.py
uv run --frozen ruff check configs/trend/baseline-v1.yaml src/glycoband/features/trend.py src/glycoband/features/__init__.py tests/features/test_trend.py
uv run --frozen mypy src/glycoband/features/trend.py
```

Expected: all commands exit `0`. If Ruff does not accept YAML paths in the installed version, rerun Ruff on the Python paths only and validate YAML by loading it with `yaml.safe_load`.

- [x] **Step 8: Commit the feature contract**

```powershell
git add -- configs/trend/baseline-v1.yaml src/glycoband/features/trend.py src/glycoband/features/__init__.py tests/features/test_trend.py
git diff --cached --check
git commit -m "feat(trend): freeze baseline BVP features"
```

---

### Task 5: Complete Baselines, Ablation, Negative Control, and Metrics

**Files:**
- Modify: `src/glycoband/evaluation/trend_baseline.py`
- Modify: `src/glycoband/evaluation/__init__.py`
- Modify: `tests/evaluation/test_trend_baseline.py`

**Interfaces:**
- Consumes: `trend-feature-v1` development rows and `configs/trend/baseline-v1.yaml`.
- Produces: `evaluate_trend_baselines(features, config) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame]` containing aggregate metrics, predictions, and per-participant metrics.

- [x] **Step 1: Add failing explicit-column and control tests**

Add tests that require:

```python
def test_evaluator_ignores_numeric_provenance_columns() -> None:
    features = _features().assign(history_window_count=59, embargo_minutes=30)
    report, _, _ = evaluate_trend_baselines(features, _config())

    assert "history_window_count" not in report["history_feature_columns"]
    assert "embargo_minutes" not in report["history_feature_columns"]


def test_evaluator_reports_required_model_and_control_variants() -> None:
    report, predictions, participant_metrics = evaluate_trend_baselines(_features(), _config())

    assert {row["model"] for row in report["models"]} == {
        "majority",
        "always_stable",
        "logistic_history",
        "logistic_current_window",
        "logistic_shifted_control",
    }
    assert set(predictions["model"]) == {
        "majority",
        "always_stable",
        "logistic_history",
        "logistic_current_window",
        "logistic_shifted_control",
    }
    assert {"participant_id", "model", "macro_f1"}.issubset(participant_metrics.columns)


def test_evaluator_reports_opposite_direction_errors_and_bootstrap_deltas() -> None:
    report, _, _ = evaluate_trend_baselines(_features(), _config())

    history = next(row for row in report["models"] if row["model"] == "logistic_history")
    assert 0.0 <= history["opposite_direction_error_rate"] <= 1.0
    assert set(report["paired_participant_bootstrap"]) == {
        "history_minus_best_constant",
        "history_minus_shifted_control",
        "history_minus_current_window",
    }
```

The `_config()` fixture must load `configs/trend/baseline-v1.yaml`; `_features()` must include all explicit history `mean/std/min/max/last` columns for every `SHORT_WINDOW_FEATURES` entry and all required provenance fields.

- [x] **Step 2: Run tests and confirm failure**

Run:

```powershell
uv run --frozen pytest -q tests/evaluation/test_trend_baseline.py
```

Expected: failure because the current evaluator auto-selects numeric columns and lacks the ablation, shift control, bootstrap deltas, and opposite-direction metric.

- [x] **Step 3: Load and validate the baseline config**

Add:

```python
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml


def load_trend_baseline_config(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("Trend baseline config must be a mapping")
    config = dict(payload)
    if config["experiment"]["id"] != "trend-baseline-v1":
        raise ValueError("Unsupported Trend baseline experiment ID")
    if config["label"]["version"] != "trend-label-v1":
        raise ValueError("Trend baseline label version mismatch")
    if config["split"]["version"] != "trend-split-v1":
        raise ValueError("Trend baseline split version mismatch")
    if config["feature"]["version"] != "trend-feature-v1":
        raise ValueError("Trend baseline feature version mismatch")
    return config
```

- [x] **Step 4: Select predictor columns explicitly**

Add:

```python
def _history_feature_columns() -> list[str]:
    return [
        f"history_{feature}_{aggregation}"
        for feature in SHORT_WINDOW_FEATURES
        for aggregation in ("mean", "std", "min", "max", "last")
    ]


def _current_window_feature_columns() -> list[str]:
    return [f"history_{feature}_last" for feature in SHORT_WINDOW_FEATURES]
```

Reject missing columns. Do not infer predictors by numeric dtype.

- [x] **Step 5: Implement the deterministic within-participant shift control**

Add:

```python
def _circular_shift_features(
    frame: pd.DataFrame,
    feature_columns: list[str],
    fraction: float,
) -> pd.DataFrame:
    shifted = frame.copy()
    for (_, _), index in shifted.groupby(["participant_id", "split"], sort=True).groups.items():
        ordered_index = shifted.loc[index].sort_values("timestamp").index
        offset = max(1, round(len(ordered_index) * fraction))
        values = shifted.loc[ordered_index, feature_columns].to_numpy(copy=True)
        shifted.loc[ordered_index, feature_columns] = np.roll(values, shift=offset, axis=0)
    return shifted
```

Use the shifted training features to fit the shifted-control pipeline and shifted validation features to evaluate it. Keep labels and split membership fixed.

- [x] **Step 6: Implement the missing metric and paired participant bootstrap**

Add:

```python
def _opposite_direction_error_rate(actual: pd.Series, predicted: pd.Series) -> float:
    opposite = ((actual == "FALLING") & (predicted == "RISING")) | (
        (actual == "RISING") & (predicted == "FALLING")
    )
    return float(opposite.mean())


def _bootstrap_mean_delta(
    left: pd.Series,
    right: pd.Series,
    *,
    repeats: int,
    seed: int,
) -> dict[str, float]:
    delta = left.to_numpy(dtype=float) - right.to_numpy(dtype=float)
    generator = np.random.default_rng(seed)
    draws = np.empty(repeats, dtype=float)
    for index in range(repeats):
        sample = generator.choice(delta, size=delta.size, replace=True)
        draws[index] = sample.mean()
    return {
        "mean_delta": float(delta.mean()),
        "ci_lower": float(np.quantile(draws, 0.025)),
        "ci_upper": float(np.quantile(draws, 0.975)),
    }
```

Build participant-aligned Macro-F1 series for `logistic_history` versus the best constant, shifted control, and current-window ablation. Use the exact repeat count and seed from the config.

- [x] **Step 7: Return all five variants and the predeclared decision status**

Change the public signature to:

```python
def evaluate_trend_baselines(
    features: pd.DataFrame,
    config: Mapping[str, Any],
) -> tuple[dict[str, object], pd.DataFrame, pd.DataFrame]:
```

Keep the current train-only imputer/scaler/Logistic Regression pipeline. Fit separate pipelines for `logistic_history`, `logistic_current_window`, and `logistic_shifted_control`. Add `opposite_direction_error_rate` to every model metric. Derive:

```python
decision = "supported_for_classical_followup"
if (
    bootstrap["history_minus_best_constant"]["ci_lower"] <= 0
    or bootstrap["history_minus_shifted_control"]["ci_lower"] <= 0
    or history_falling_recall <= 0
    or history_rising_recall <= 0
):
    decision = "not_supported_for_classical_followup"
```

The `history_minus_current_window` comparison is interpretive: if its interval includes zero, report that H30 history adds no demonstrated advantage over the latest 30-second window, but do not change the Trend label.

- [x] **Step 8: Export evaluator interfaces in sorted order**

Update `src/glycoband/evaluation/__init__.py`:

```python
from glycoband.evaluation.trend_baseline import (
    evaluate_trend_baselines,
    load_trend_baseline_config,
)
from glycoband.evaluation.trend_split import assign_trend_splits, validate_trend_splits

__all__ = [
    "assign_trend_splits",
    "evaluate_trend_baselines",
    "load_trend_baseline_config",
    "validate_trend_splits",
]
```

- [x] **Step 9: Run evaluator validation**

Run:

```powershell
uv run --frozen pytest -q tests/evaluation/test_trend_baseline.py
uv run --frozen ruff check src/glycoband/evaluation/trend_baseline.py src/glycoband/evaluation/__init__.py tests/evaluation/test_trend_baseline.py
uv run --frozen mypy src/glycoband/evaluation/trend_baseline.py
```

Expected: all commands exit `0`.

- [x] **Step 10: Commit the registered evaluator**

```powershell
git add -- src/glycoband/evaluation/trend_baseline.py src/glycoband/evaluation/__init__.py tests/evaluation/test_trend_baseline.py
git diff --cached --check
git commit -m "feat(trend): add registered baseline controls"
```

---

### Task 6: Make the Runner Reproducible and Non-overwriting

**Files:**
- Modify: `scripts/run_trend_baseline.py`
- Create: `tests/scripts/test_run_trend_baseline.py`
- Generate at run time: `data/interim/trend/trend-baseline-features-v1.parquet`
- Generate at run time: `reports/experiments/trend-baseline-v1/`

**Interfaces:**
- Consumes: baseline YAML, source/split manifests, development endpoint Parquet, raw participant BVP, feature functions, and evaluator.
- Produces: config, environment, manifests, features, metrics, per-participant metrics, predictions, diagnostic figures, summary, and trained development pipelines under one immutable experiment directory.

- [x] **Step 1: Add runner safety tests**

Create `tests/scripts/test_run_trend_baseline.py` with tests for:

```python
def test_load_development_endpoints_never_returns_test_rows(tmp_path: Path) -> None:
    path = tmp_path / "endpoints.parquet"
    _endpoint_fixture().to_parquet(path, index=False)

    frame = _load_development_endpoints(path)

    assert set(frame["split"]) == {"train", "validation"}


def test_prepare_output_directory_refuses_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "trend-baseline-v1"
    output.mkdir()

    with pytest.raises(FileExistsError, match="already exists"):
        _prepare_output_directory(output)


def test_environment_record_does_not_claim_final_test_access(tmp_path: Path) -> None:
    record = _environment_record(
        root=tmp_path,
        command="uv run --frozen python scripts/run_trend_baseline.py",
        config_sha256="a" * 64,
        split_manifest_sha256="b" * 64,
    )

    assert record["final_test_accessed"] is False
```

The endpoint fixture must contain train, validation, test, and excluded rows so the filter is exercised.

- [x] **Step 2: Run runner tests and confirm failure**

Run:

```powershell
uv run --frozen pytest -q tests/scripts/test_run_trend_baseline.py
```

Expected: failure because output refusal and environment recording are not implemented.

- [x] **Step 3: Implement output refusal and compact environment identity**

Add:

```python
def _prepare_output_directory(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"Experiment directory already exists: {path}")
    path.mkdir(parents=True)


def _environment_record(
    *,
    root: Path,
    command: str,
    config_sha256: str,
    split_manifest_sha256: str,
) -> dict[str, object]:
    return {
        "git_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "git_dirty": bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=root, text=True
            ).strip()
        ),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "command": command,
        "config_sha256": config_sha256,
        "split_manifest_sha256": split_manifest_sha256,
        "final_test_accessed": False,
    }
```

Refuse a real registered run when `git_dirty` is true. A fixture-only smoke test may run dirty but must write only to pytest’s temporary directory.

Capture the environment record before creating report files so the runner records the clean committed input state rather than its own newly generated artifacts.

- [x] **Step 4: Update the development feature path**

Load the baseline config and split-manifest hash. Add `split_version="trend-split-v1"` to development endpoints after verifying the loaded split manifest version. For each participant:

```python
participant_windows = extract_bvp_window_features(
    dataset_root / source_file,
    rate_hz=int(audit_config["bvp_rate_hz"]),
    window_seconds=int(config["feature"]["short_window_seconds"]),
    maximum_gap_seconds=float(audit_config["maximum_bvp_gap_seconds"]),
    stop_at=max_endpoint,
)
participant_windows["participant_id"] = participant_id
participant_features = aggregate_bvp_history_features(
    participant_windows,
    endpoint_group,
    history_minutes=int(config["feature"]["history_minutes"]),
    window_seconds=int(config["feature"]["short_window_seconds"]),
    minimum_complete_windows=int(config["feature"]["minimum_complete_windows"]),
)
```

Continue to require one feature row per development endpoint. Never fall back to fewer windows or silently drop an endpoint.

Evaluate with the frozen config and persist all three returned tables:

```python
report, predictions, participant_metrics = evaluate_trend_baselines(features, config)
predictions.to_parquet(report_dir / "predictions.parquet", index=False)
participant_metrics.to_csv(report_dir / "per_participant.csv", index=False)
(report_dir / "metrics.json").write_text(
    json.dumps(report, indent=2) + "\n",
    encoding="utf-8",
)
```

- [x] **Step 5: Write the complete registered-development artifact set**

The runner must create this exact structure:

```text
reports/experiments/trend-baseline-v1/
    config.yaml
    environment.json
    dataset_manifest.json
    split_manifest.json
    metrics.json
    per_participant.csv
    predictions.parquet
    summary.md
    figures/
        model_macro_f1.png
        participant_macro_f1.png
        validation_confusion_matrices.png
```

Copy the exact config and manifests used. Write development features to `data/interim/trend/trend-baseline-features-v1.parquet` with provenance. Do not include test rows in any generated file.

- [x] **Step 6: Generate interpretation-relevant figures**

Implement:

```python
def _plot_model_macro_f1(report: Mapping[str, Any], path: Path) -> None:
    rows = report["models"]
    names = [str(row["model"]) for row in rows]
    values = [float(row["macro_f1"]) for row in rows]
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.bar(names, values, color="#5B4B8A")
    axis.set_ylabel("Validation Macro-F1")
    axis.set_ylim(0, 1)
    axis.tick_params(axis="x", rotation=25)
    figure.tight_layout()
    figure.savefig(path, dpi=200)
    plt.close(figure)
```

Add a paired per-participant plot for the five variants and normalized validation confusion matrices for the three learned variants. Figures must expose weak participants, class confusion, and controls rather than decorate the report.

- [x] **Step 7: Write an evidence-bounded summary**

The summary generator must include:

```markdown
# Trend registered development baseline v1

Status: development-validation evidence; final test sealed.

## Question

Does aligned H30 wrist BVP contain validation-set predictive information for recent CGM-derived direction beyond constant baselines and a within-participant temporal-shift control?

## Contract

- Dataset: BIG IDEAs v1.1.3
- Independent unit: participant
- Inference input: native wrist BVP only
- Label: trend-label-v1
- Split: trend-split-v1, train/validation only
- Feature: trend-feature-v1
- Preprocessing: no detrending, filtering, amplitude normalization, or SQI exclusion; train-fitted median imputation and standard scaling only
- Primary metric: Macro-F1
- Claim ceiling: feasibility only

## Finding

The finding is populated from the predeclared decision rule and validation metrics.

## What this does not prove

This development result does not establish held-out final-test performance, general-population validity, direct glucose measurement, clinical utility, or physical-device validity.

## Next decision

Follow the predeclared Go/No-Go result. Do not open the final test in this lake.
```

Populate numeric tables deterministically from `metrics.json`; do not manually transcribe metrics.

- [x] **Step 8: Run runner unit validation**

Run:

```powershell
uv run --frozen pytest -q tests/scripts/test_run_trend_baseline.py tests/features/test_trend.py tests/evaluation/test_trend_baseline.py
uv run --frozen ruff check scripts/run_trend_baseline.py tests/scripts/test_run_trend_baseline.py
uv run --frozen mypy scripts/run_trend_baseline.py
```

Expected: all commands exit `0`.

- [x] **Step 9: Commit the runner before any real experiment**

```powershell
git add -- scripts/run_trend_baseline.py tests/scripts/test_run_trend_baseline.py
git diff --cached --check
git commit -m "feat(trend): add reproducible baseline runner"
```

---

### Task 7: Execute and Independently Evaluate the Train/Validation Baseline

**Files:**
- Generate: `data/interim/trend/trend-baseline-features-v1.parquet`
- Generate: `reports/experiments/trend-baseline-v1/`
- Inspect only: all files generated by the run

**Interfaces:**
- Consumes: the fully committed scientific anchor, feature contract, evaluator, controls, and runner.
- Produces: one immutable development-validation evidence package plus an independent `PASS`, `REPAIR`, or `BLOCKED` verdict.

- [x] **Step 1: Run the full locked preflight before the real experiment**

Run serially:

```powershell
uv sync --frozen
uv lock --check
uv run --frozen pytest
uv run --frozen ruff check .
uv run --frozen mypy
git status --porcelain
```

Expected: all commands exit `0`, and Git status is empty in the execution worktree.

- [x] **Step 2: Run the real train/validation experiment once**

Run:

```powershell
uv run --frozen python scripts/run_trend_baseline.py
```

Expected live progress: one participant at a time, development endpoint counts, feature counts, final headline validation metrics, artifact paths, and `final_test_accessed=false`. Do not persist the full terminal transcript.

- [x] **Step 3: Verify no final-test rows entered any artifact**

Run:

```powershell
uv run --frozen python -c "import json,pandas as pd,pathlib; root=pathlib.Path('.'); f=pd.read_parquet(root/'data/interim/trend/trend-baseline-features-v1.parquet',columns=['split']); p=pd.read_parquet(root/'reports/experiments/trend-baseline-v1/predictions.parquet',columns=['split']); m=json.loads((root/'reports/experiments/trend-baseline-v1/metrics.json').read_text()); assert set(f['split']) <= {'train','validation'}; assert set(p['split']) == {'validation'}; assert m['final_test_accessed'] is False; print('PASS final test sealed')"
```

Expected: `PASS final test sealed`.

- [x] **Step 4: Verify artifact completeness and cross-references**

Run:

```powershell
uv run --frozen python -c "import json,pathlib,yaml; p=pathlib.Path('reports/experiments/trend-baseline-v1'); required={'config.yaml','environment.json','dataset_manifest.json','split_manifest.json','metrics.json','per_participant.csv','predictions.parquet','summary.md'}; assert required <= {x.name for x in p.iterdir()}; c=yaml.safe_load((p/'config.yaml').read_text()); m=json.loads((p/'metrics.json').read_text()); assert c['experiment']['id']==m['experiment_id']=='trend-baseline-v1'; assert (p/'figures/model_macro_f1.png').exists(); assert (p/'figures/participant_macro_f1.png').exists(); assert (p/'figures/validation_confusion_matrices.png').exists(); print('PASS artifact contract')"
```

Expected: `PASS artifact contract`.

- [x] **Step 5: Perform independent read-only evaluation**

The evaluator must inspect the actual config, manifests, feature schema, metrics, per-participant table, predictions, figures, and Git diff. Return:

```text
Scientific contract: PASS | REPAIR | BLOCKED
Final-test seal: PASS | REPAIR | BLOCKED
Predictor purity: PASS | REPAIR | BLOCKED
Temporal/participant leakage: PASS | REPAIR | BLOCKED
Required baselines and controls: PASS | REPAIR | BLOCKED
Per-class/per-participant interpretation: PASS | REPAIR | BLOCKED
Artifact reproducibility: PASS | REPAIR | BLOCKED
Claim discipline: PASS | REPAIR | BLOCKED
Overall: PASS | REPAIR | BLOCKED
```

Any objective in-scope `REPAIR` finding returns to its owning task, followed by rerunning the failed check and this independent evaluation. The evaluator must not repair its own findings.

- [x] **Step 6: Record the ignored feature artifact by identity and commit only after independent PASS**

Before committing the report, add the feature artifact's relative path, SHA-256, row count, column schema, and regeneration command to `dataset_manifest.json`. Verify the recorded digest:

```powershell
uv run --frozen python -c "import hashlib,json,pathlib,pandas as pd; root=pathlib.Path('.'); feature=root/'data/interim/trend/trend-baseline-features-v1.parquet'; manifest_path=root/'reports/experiments/trend-baseline-v1/dataset_manifest.json'; manifest=json.loads(manifest_path.read_text()); digest=hashlib.sha256(feature.read_bytes()).hexdigest(); assert manifest['development_feature_artifact']['path']=='data/interim/trend/trend-baseline-features-v1.parquet'; assert manifest['development_feature_artifact']['sha256']==digest; assert manifest['development_feature_artifact']['rows']==len(pd.read_parquet(feature,columns=['participant_id'])); print('PASS feature artifact identity')"
```

Expected: `PASS feature artifact identity`.

```powershell
git add -- reports/experiments/trend-baseline-v1
git diff --cached --check
git commit -m "research(trend): record registered baseline development"
```

Keep the development feature Parquet ignored according to repository storage policy. The committed dataset manifest is its reproducibility anchor.

---

### Task 8: Record the Scientific Result and Handoff Without Opening the Test

**Files:**
- Modify: `docs/research/journal.md`
- Modify: `README.md`
- Do not modify: `docs/research/readiness_contract.md`
- Do not modify: `docs/research/decision_register.md`

**Interfaces:**
- Consumes: independently passed `trend-baseline-v1` artifacts.
- Produces: a compact project-status update and the next scientific decision without changing Gate D or final-test status.

- [x] **Step 1: Append one evidence record to the journal**

Use this exact structure with numeric values copied programmatically from `metrics.json`:

```markdown
## 2026-08-25 — Trend registered development baseline

Question:
Does aligned H30 wrist BVP contain development-validation predictive information for recent CGM-derived direction beyond constants and a within-participant temporal-shift control?

Probe or evidence used:
`trend-baseline-v1` used BIG IDEAs v1.1.3 train/validation rows only, `trend-label-v1`, `trend-split-v1`, `trend-feature-v1`, majority, always-STABLE, aligned Logistic Regression, current-window Logistic Regression, and a half-sequence within-participant circular-shift control.

Finding:
Summarize the predeclared decision status, Macro-F1 comparison, directional recalls, opposite-direction error rate, participant-bootstrap intervals, and whether H30 history improved on the current-window ablation.

What it does not prove:
No final-test performance was accessed. The result does not establish general-population validity, direct glucose measurement, clinical utility, or physical-device validity.

Confidence:
State the uncertainty implied by 16 participants, per-participant variation, and the paired participant bootstrap.

Recommended next action:
Follow the predeclared decision: either stop Trend model expansion, repair a demonstrated validity defect, or authorize one classical-model comparison. Do not open the final test from this result alone.
```

- [x] **Step 2: Update README status with the evidence level, not a marketing claim**

Replace the “next Trend lake is registered baseline development” sentence with one sentence stating that `trend-baseline-v1` is complete on development validation, naming its decision status, and explicitly saying the final test remains sealed.

- [x] **Step 3: Verify status consistency**

Run:

```powershell
rg -n "trend-baseline-v1|final test|PARKED|PASS|FROZEN|SEALED" README.md docs/research/journal.md docs/research/readiness_contract.md docs/research/decision_register.md reports/experiments/trend-baseline-v1/summary.md
git diff --check
```

Expected: State remains parked; D-Trend remains passed; `SCI-FINAL-TEST` remains sealed; no text claims held-out, clinical, or device validation.

- [x] **Step 4: Run final locked verification**

Run serially:

```powershell
uv sync --frozen
uv lock --check
uv run --frozen pytest
uv run --frozen ruff check .
uv run --frozen mypy
```

Expected: every command exits `0`.

- [x] **Step 5: Commit the handoff**

```powershell
git add -- docs/research/journal.md README.md
git diff --cached --check
git commit -m "docs(trend): record baseline development decision"
```

## Final Completion Check

Before reporting completion, verify all of the following:

- The signed Trend approval is committed before the regenerated manifest.
- `trend-split-v1` records a clean Git revision and matching endpoint/source hashes.
- The development feature artifact contains only train/validation rows and complete provenance.
- The BVP slope physical-unit test passes at `60.0 units/min` for the synthetic linear fixture.
- Participant identity is mandatory in feature aggregation.
- Explicit predictor columns exclude counts, timestamps, embargo values, labels, slopes, and CGM-derived fields.
- Majority, always-STABLE, aligned Logistic Regression, current-window Logistic Regression, and shifted-control Logistic Regression all run.
- Macro-F1, balanced accuracy, directional recall, opposite-direction errors, per-participant metrics, and paired participant-bootstrap intervals are saved.
- Required diagnostic figures exist and reveal class/participant/control behavior.
- The independent evaluator returns `PASS` after the last repair.
- The full locked environment suite passes on the exact committed implementation.
- The final test remains sealed and no final-test result appears in any artifact, log, document, or claim.
