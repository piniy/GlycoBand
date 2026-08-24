# Trend Protocol and Chronological Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the approved BIG IDEAs Recent Trend label contract and leakage-safe within-person chronological split manifest, without starting model training or opening final-test results.

**Architecture:** Keep the existing causal CGM-history label calculation in `glycoband.datasets.bigideas`, and add a small typed Trend protocol boundary in `glycoband.labels.trend`. Add a separate split module that assigns endpoint rows per participant, applies the approved 60/20/20 chronological rule and 30-minute embargo, validates raw-history disjointness, and writes a provenance-rich JSON manifest. The generated manifest is a sealed contract for later registered baselines; this plan does not implement features or models.

**Tech Stack:** Python 3.11, pandas, PyYAML, NumPy, pytest, pathlib, JSON, and the existing `uv.lock` environment.

## Global Constraints

- Use BIG IDEAs v1.1.3 only; never combine its rows with Hb-PPG.
- Use BVP history only as the inference input; CGM is used only to construct and evaluate labels.
- Use the approved Trend vocabulary `FALLING`, `STABLE`, and `RISING`.
- Use the approved candidate protocol: 30-minute history, median-of-three CGM smoothing, ordinary least-squares slope, and `0.5 mg/dL/min` threshold.
- Require at least 80% valid CGM support and continuous BVP coverage according to the audited gap rules.
- Split each participant chronologically into the first 60% train, next 20% validation, and final 20% test, with a 30-minute embargo at each boundary.
- Do not modify `data/raw/`.
- Do not access final-test performance or use it to change the protocol, split, or claim wording.
- Do not change `docs/research/decision_register.md` or `docs/research/readiness_contract.md` from code; the project lead records the scientific approval separately.
- Do not begin registered Trend modeling until the project lead has approved the Gate D package and the split manifest passes all validators.
- Run the locked environment checks before declaring the lake complete: `uv sync --frozen`, `uv lock --check`, `uv run --frozen pytest`, `uv run --frozen ruff check .`, and `uv run --frozen mypy`.

## Approval checkpoint before implementation

The project lead must choose `APPROVE TREND GATE D PACKAGE`, `REVISE`, or `NO_GO` in [`docs/research/gate_d_decision_brief.md`](../../research/gate_d_decision_brief.md).

If the decision is `REVISE`, stop before creating `configs/trend/label-v1.yaml` or `data/manifests/trend_split-v1.json` and update this plan's protocol values to match the approved revision. If the decision is `NO_GO`, stop this lake and retain the existing exploratory artifacts. No implementation task below may infer approval from a `PENDING` status.

---

### Task 1: Add the approved Trend protocol contract

**Files:**
- Create after approval: `configs/trend/label-v1.yaml`
- Create: `src/glycoband/labels/trend.py`
- Modify: `src/glycoband/labels/__init__.py`
- Create: `tests/labels/test_trend.py`

**Interfaces:**
- Consumes: one YAML protocol file and the existing BIG IDEAs audit configuration.
- Produces: `TrendProtocol`, `load_trend_protocol(path: Path) -> TrendProtocol`, and `validate_endpoint_frame(frame: pd.DataFrame, protocol: TrendProtocol) -> None`.

- [ ] **Step 1: Write the failing protocol-loader tests.**

Add tests for the exact approved contract:

```python
def test_load_trend_protocol_reads_approved_values(repo_root: Path) -> None:
    protocol = load_trend_protocol(repo_root / "configs/trend/label-v1.yaml")

    assert protocol.version == "trend-label-v1"
    assert protocol.history_minutes == 30
    assert protocol.threshold_mg_dl_min == 0.5
    assert protocol.smoothing == "median3"
    assert protocol.slope_method == "ols"
    assert protocol.minimum_support_fraction == 0.8
    assert protocol.classes == ("FALLING", "STABLE", "RISING")
```

Also test that the loader rejects a non-causal label source, a negative threshold, a history shorter than the audited 30-minute candidate, missing classes, and a support fraction outside `[0, 1]`.

- [ ] **Step 2: Run the focused tests and confirm they fail because the contract module/config does not exist.**

Run:

```powershell
uv run --frozen pytest tests/labels/test_trend.py -q
```

Expected: collection or import failure for the new `load_trend_protocol` interface.

- [ ] **Step 3: Implement the typed contract and YAML file.**

Use this protocol shape:

```yaml
version: trend-label-v1
dataset:
  name: big_ideas
  version: 1.1.3
label:
  classes: [FALLING, STABLE, RISING]
  source: cgm_history_ending_at_t
  history_minutes: 30
  smoothing: median3
  slope_method: ols
  threshold_mg_dl_min: 0.5
  minimum_cgm_support_fraction: 0.8
  maximum_cgm_gap_minutes: 15.0
  requires_continuous_bvp_history: true
split:
  type: within_person_chronological
  train_fraction: 0.6
  validation_fraction: 0.2
  test_fraction: 0.2
  embargo_minutes: 30
```

Implement the dataclass with explicit fields rather than passing arbitrary dictionaries through the pipeline:

```python
@dataclass(frozen=True)
class TrendProtocol:
    version: str
    dataset_name: str
    dataset_version: str
    classes: tuple[str, str, str]
    source: str
    history_minutes: int
    smoothing: str
    slope_method: str
    threshold_mg_dl_min: float
    minimum_support_fraction: float
    maximum_cgm_gap_minutes: float
    requires_continuous_bvp_history: bool
```

`load_trend_protocol` must call `yaml.safe_load`, reject non-mapping YAML, validate every field, and return the dataclass. `validate_endpoint_frame` must require `participant_id`, `timestamp`, `history_start`, `label`, `support_points`, `bvp_source_file`, and `cgm_source_file`; reject duplicate `(participant_id, timestamp)` identities; reject labels outside the approved class set; reject endpoints later than the participant's available CGM data when that bound is supplied; and verify `history_start < timestamp`.

- [ ] **Step 4: Run the focused tests and static checks.**

Run:

```powershell
uv run --frozen pytest tests/labels/test_trend.py -q
uv run --frozen ruff check src/glycoband/labels tests/labels
uv run --frozen mypy src/glycoband/labels
```

Expected: all focused tests pass with no Ruff or mypy errors.

- [ ] **Step 5: Commit the contract lake.**

```powershell
git add configs/trend/label-v1.yaml src/glycoband/labels tests/labels
git commit -m "feat(trend): add approved label protocol contract"
```

### Task 2: Add chronological split generation and leakage validation

**Files:**
- Create: `src/glycoband/evaluation/trend_split.py`
- Modify: `src/glycoband/evaluation/__init__.py`
- Create: `tests/evaluation/test_trend_split.py`

**Interfaces:**
- Consumes: a validated endpoint DataFrame with participant IDs, endpoint timestamps, and raw-history start timestamps; a `TrendProtocol`.
- Produces: `assign_trend_splits(endpoints: pd.DataFrame, protocol: TrendProtocol) -> pd.DataFrame` and `validate_trend_splits(split_frame: pd.DataFrame, protocol: TrendProtocol) -> None`.

- [ ] **Step 1: Write failing split tests using a small deterministic fixture.**

Use two participants with 10-minute endpoint spacing and 30-minute histories. Test that the output contains only `train`, `validation`, and `test`, preserves the endpoint identity, and is deterministic.

Add explicit boundary tests:

```python
def test_split_has_no_raw_history_overlap_across_boundaries(endpoint_frame: pd.DataFrame) -> None:
    split = assign_trend_splits(endpoint_frame, protocol)

    validate_trend_splits(split, protocol)

    assert set(split["split"]) <= {"train", "validation", "test"}
    assert not _history_intervals_overlap(split, "train", "validation")
    assert not _history_intervals_overlap(split, "validation", "test")
```

Also test that the validator rejects a manually modified frame with a duplicated endpoint, a participant appearing in a different split order, a history interval that overlaps a later split, or a boundary with less than 30 minutes of embargo.

- [ ] **Step 2: Run the focused tests and confirm the split implementation is absent.**

Run:

```powershell
uv run --frozen pytest tests/evaluation/test_trend_split.py -q
```

Expected: import failure for `glycoband.evaluation.trend_split`.

- [ ] **Step 3: Implement deterministic per-participant split assignment.**

For each participant:

1. Sort by `timestamp` and reject duplicate endpoint identities.
2. Define the first and second cut points at the 60th and 80th percentile positions of that participant's ordered endpoints.
3. Assign train endpoints before the first cut point.
4. Assign validation endpoints at or after the first cut point plus 30 minutes and before the second cut point.
5. Assign test endpoints at or after the second cut point plus 30 minutes.
6. Leave boundary rows in an explicit `excluded_embargo` status rather than silently assigning them.

The function must return the original endpoint columns plus `split`, `participant_train_end`, `participant_validation_end`, and `embargo_minutes`. It must not shuffle rows, use a random seed, or inspect final-test labels or metrics.

Use interval checks based on `[history_start, timestamp]`. The validator must confirm, per participant, that every train interval ends before every validation interval begins with the configured embargo, and that every validation interval ends before every test interval begins with the configured embargo. It must also confirm that split timestamps are monotonically ordered and no excluded boundary row is assigned to a usable split.

- [ ] **Step 4: Run the focused split tests and static checks.**

Run:

```powershell
uv run --frozen pytest tests/evaluation/test_trend_split.py -q
uv run --frozen ruff check src/glycoband/evaluation/trend_split.py tests/evaluation/test_trend_split.py
uv run --frozen mypy src/glycoband/evaluation/trend_split.py
```

Expected: all split and adversarial leakage tests pass.

- [ ] **Step 5: Commit the split-validator lake.**

```powershell
git add src/glycoband/evaluation/trend_split.py src/glycoband/evaluation/__init__.py tests/evaluation/test_trend_split.py
git commit -m "feat(trend): add chronological split leakage validation"
```

### Task 3: Build the approved label and split manifest runner

**Files:**
- Create: `scripts/build_trend_split_manifest.py`
- Create after approval: `data/manifests/trend_split-v1.json`
- Create: `tests/scripts/test_build_trend_split_manifest.py`

**Interfaces:**
- Consumes: `configs/trend/label-v1.yaml`, `configs/audits/bigideas.yaml`, and immutable raw files under `data/raw/bigideas/v1.1.3`.
- Produces: a Parquet endpoint artifact under `data/interim/trend/trend-label-v1.parquet` and the JSON split manifest under `data/manifests/trend_split-v1.json`.

- [ ] **Step 1: Write runner safety tests before touching raw data.**

Test the runner's pure manifest writer with a fixture endpoint frame. The JSON must contain:

```json
{
  "manifest_version": "trend-split-v1",
  "protocol_version": "trend-label-v1",
  "dataset": "BIG IDEAs v1.1.3",
  "participant_count": 16,
  "final_test_accessed": false,
  "embargo_minutes": 30,
  "participants": [],
  "endpoint_identity": ["participant_id", "timestamp"],
  "raw_history_identity": ["history_start", "timestamp"]
}
```

The test must reject a manifest whose protocol version does not match the label config, whose participant count is not 16 for the real run, or whose endpoint rows lack source-file provenance.

- [ ] **Step 2: Implement the participant-wise runner.**

Reuse `participant_source_paths`, `audit_bvp_csv`, `load_cgm`, and `generate_recent_trend_labels` from `glycoband.datasets.bigideas`. For participants `001` through `016`, stream one BVP file, generate only the approved H30/τ0.5/median3/OLS labels, attach source-file and protocol provenance, and release each participant's in-memory frames before processing the next participant.

The runner must print concise progress such as:

```text
[trend-split-v1] participant=001 stage=label_generation
[trend-split-v1] participant=001 endpoints=... train=... validation=... test=... excluded_embargo=...
```

Before writing artifacts, call `validate_endpoint_frame`, `assign_trend_splits`, and `validate_trend_splits`. Write the endpoint Parquet first, then write the JSON manifest containing participant counts, split counts, boundary timestamps, source file names, protocol values, Git revision, and `final_test_accessed: false`.

- [ ] **Step 3: Run the runner against the verified development data only.**

Run:

```powershell
uv run --frozen python scripts/build_trend_split_manifest.py
```

Expected:

- all 16 BIG IDEAs participants are processed;
- every participant has causal labels and source provenance;
- no raw history overlaps a split boundary;
- the manifest records `final_test_accessed: false`;
- the test reserve is represented only by IDs, timestamps, and split metadata, not by model scores.

- [ ] **Step 4: Inspect the artifacts without changing the protocol.**

Check:

```powershell
uv run --frozen python -c "import json; from pathlib import Path; p=json.loads(Path('data/manifests/trend_split-v1.json').read_text()); print(p['manifest_version'], p['participant_count'], p['final_test_accessed'])"
uv run --frozen python -c "import pandas as pd; x=pd.read_parquet('data/interim/trend/trend-label-v1.parquet'); print(x.groupby(['split']).size()); print(x.groupby(['participant_id','split']).size().head())"
```

Do not use the resulting test rows to choose preprocessing, features, model family, or success criteria.

- [ ] **Step 5: Commit the manifest runner and approved artifacts.**

```powershell
git add scripts/build_trend_split_manifest.py tests/scripts/test_build_trend_split_manifest.py data/manifests/trend_split-v1.json data/interim/trend/trend-label-v1.parquet
git commit -m "feat(trend): create versioned chronological split manifest"
```

### Task 4: Complete the lake verification and handoff

**Files:**
- Modify: `docs/research/journal.md`
- Modify: `README.md`
- Modify: `docs/research/readiness_contract.md` only if the generated evidence satisfies the documented gate conditions and the project lead has recorded approval

**Interfaces:**
- Consumes: the approved protocol, endpoint Parquet, split manifest, focused tests, and full locked-environment verification.
- Produces: a compact evidence record and a clear handoff to the downstream registered-baseline lake.

- [ ] **Step 1: Run the complete locked verification.**

Run serially:

```powershell
uv sync --frozen
uv lock --check
uv run --frozen pytest
uv run --frozen ruff check .
uv run --frozen mypy
```

Expected: all commands exit with code 0. A partial or interrupted run is not a pass.

- [ ] **Step 2: Record the decision-relevant result.**

Append one dated journal entry containing:

- the approved protocol version;
- participant count and endpoint count;
- per-split endpoint counts and per-participant support;
- excluded embargo counts;
- confirmation that CGM was used only for labels;
- confirmation that BVP history is the only predictor-side data represented;
- confirmation that no final-test performance was accessed;
- remaining limitation: no Trend learnability result exists yet;
- next action: implement the registered majority, always-`STABLE`, and Logistic Regression baselines.

- [ ] **Step 3: Update the README frontier text only after the artifacts exist.**

State that Trend protocol and chronological split contracts are versioned, while registered modeling remains the next lake. Do not claim Trend predictive validity, device validation, or clinical utility.

- [ ] **Step 4: Commit the verified handoff.**

```powershell
git add docs/research/journal.md README.md
git commit -m "docs(trend): record split contract handoff"
```

## Exit Gate

This plan is complete only when:

- the project lead has approved the Trend Gate D package;
- `configs/trend/label-v1.yaml` is versioned and validated;
- `data/interim/trend/trend-label-v1.parquet` contains causal labels with provenance;
- `data/manifests/trend_split-v1.json` records a deterministic 60/20/20 within-person split and 30-minute embargo;
- adversarial tests prove no raw BVP history overlaps train/validation/test boundaries;
- all locked-environment checks pass;
- the journal explicitly states that no Trend model result exists yet;
- the next lake is registered baseline modeling, not deep learning or synthetic robustness.

## Downstream Work Deliberately Excluded

The following are not part of this lake: BVP feature engineering, training-only preprocessing, baseline model training, time-shift controls, current-window-only ablation, calibration, OOD policy, model freezing, final-test evaluation, synthetic robustness, physical-device claims, and Decision Engine integration. Those require this contract and split manifest to pass first.
