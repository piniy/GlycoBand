# Trend Endpoint Stability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a development-only, exact endpoint-level comparison of the five shortlisted BIG IDEAs Recent Trend formulations before any scientific freeze or model work.

**Architecture:** Stream each participant's immutable native BVP file once to reconstruct the same continuous-coverage spans used by the audit, then generate causal CGM labels for only the five shortlisted protocols. Compare each formulation to the working primary on the exact `(participant_id, timestamp)` endpoint key and persist compact aggregate and provenance artifacts. The probe never partitions time, fits a model, creates a reserve, or changes a scientific contract.

**Tech Stack:** Python 3.11+, pandas, NumPy, matplotlib, PyYAML, pytest, ruff, uv.

## Global Constraints

- Use BIG IDEAs v1.1.3 only; `data/raw/` remains immutable.
- Use BVP history only to establish continuous coverage; CGM constructs labels and never becomes an inference feature.
- Every label must use CGM observations at or before its endpoint.
- The probe is development-only; do not create a chronological split, final reserve, model, calibration, OOD policy, or `configs/trend/label-v1.yaml`.
- Preserve participant ID, BVP source file, CGM source file, timestamp, history start, candidate ID, slope, and label in the derived endpoint table.
- Store figures under `reports/experiments/trend_endpoint_stability-v1/figures/` and make the summary state the exploratory claim ceiling.

---

### Task 1: Build exact endpoint comparison helpers

**Files:**
- Create: `src/glycoband/evaluation/trend_endpoint_stability.py`
- Test: `tests/evaluation/test_trend_endpoint_stability.py`

**Interfaces:**
- Consumes: a DataFrame with `participant_id`, `candidate_id`, `timestamp`, `history_start`, `slope_mg_dl_min`, and `label`.
- Produces: `compare_to_primary(endpoint_labels: pd.DataFrame, primary_candidate_id: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]`, returning pooled pairwise metrics, per-participant pairwise metrics, and long-form 3x3 label-transition counts.

- [ ] **Step 1: Write failing metric tests**

```python
def test_compare_to_primary_uses_exact_participant_timestamp_keys() -> None:
    pooled, per_person, transitions = compare_to_primary(_labels(), "primary")
    candidate = pooled.set_index("candidate_id").loc["short"]
    assert candidate["primary_endpoints"] == 3
    assert candidate["candidate_endpoints"] == 3
    assert candidate["shared_endpoints"] == 2
    assert candidate["union_endpoints"] == 4
    assert candidate["endpoint_jaccard"] == 0.5
    assert candidate["exact_label_agreement"] == 0.5
    assert len(per_person) == 2
    assert transitions["count"].sum() == 2
```

- [ ] **Step 2: Run the focused test and confirm it fails because the module is absent**

Run: `uv run pytest tests/evaluation/test_trend_endpoint_stability.py -v`

Expected: `ModuleNotFoundError: No module named 'glycoband.evaluation.trend_endpoint_stability'`.

- [ ] **Step 3: Implement key validation and pairwise metrics**

```python
KEY_COLUMNS = ("participant_id", "timestamp")
LABEL_ORDER = ("FALLING", "STABLE", "RISING")

def compare_to_primary(endpoint_labels: pd.DataFrame, primary_candidate_id: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    _validate_endpoint_labels(endpoint_labels, primary_candidate_id)
    primary = endpoint_labels.loc[endpoint_labels["candidate_id"] == primary_candidate_id]
    pooled_rows, participant_rows, transition_frames = [], [], []
    for candidate_id in endpoint_labels["candidate_id"].drop_duplicates():
        candidate = endpoint_labels.loc[endpoint_labels["candidate_id"] == candidate_id]
        pooled_rows.append(_pair_metrics(primary, candidate, primary_candidate_id, candidate_id, None))
        for participant_id in sorted(endpoint_labels["participant_id"].unique()):
            participant_rows.append(_pair_metrics(primary.loc[primary.participant_id == participant_id], candidate.loc[candidate.participant_id == participant_id], primary_candidate_id, candidate_id, participant_id))
        transition_frames.append(_label_transitions(primary, candidate, candidate_id))
    return pd.DataFrame(pooled_rows), pd.DataFrame(participant_rows), pd.concat(transition_frames, ignore_index=True)
```

Implement `_pair_metrics` with an inner join on both key columns, exact label agreement only on shared endpoints, `union_endpoints = primary_endpoints + candidate_endpoints - shared_endpoints`, primary/candidate shared retention, Jaccard, Cohen's kappa only when the expected chance denominator is nonzero, and agreement/disagreement quantiles for `abs(abs(slope_primary) - primary_threshold)`. Implement `_label_transitions` as grouped primary-label/candidate-label counts for the same inner join, explicitly reindexing all nine label pairs to zero counts.

- [ ] **Step 4: Add validation tests and run them**

```python
def test_compare_to_primary_rejects_duplicate_candidate_endpoint_keys() -> None:
    duplicated = pd.concat([_labels(), _labels().iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        compare_to_primary(duplicated, "primary")
```

Run: `uv run pytest tests/evaluation/test_trend_endpoint_stability.py -v`

Expected: all endpoint-stability tests pass.

### Task 2: Add a reproducible development-only runner and evidence artifacts

**Files:**
- Create: `configs/probes/trend_endpoint_stability-v1.yaml`
- Create: `scripts/run_trend_endpoint_stability.py`
- Modify: `src/glycoband/evaluation/trend_endpoint_stability.py`
- Test: `tests/evaluation/test_trend_endpoint_stability.py`

**Interfaces:**
- Consumes: immutable `data/raw/bigideas/v1.1.3/`, the existing audit config, and the five `SHORTLIST` protocol definitions.
- Produces: `reports/experiments/trend_endpoint_stability-v1/endpoint_labels.parquet`, `pooled_pairwise.csv`, `per_participant_pairwise.csv`, `label_transitions.csv`, `metrics.json`, `run_metadata.json`, `summary.md`, and two diagnostic PNG figures.

- [ ] **Step 1: Add a fixed, non-freezing probe config**

```yaml
experiment_id: trend_endpoint_stability-v1
evidence_level: exploratory_development_only
dataset: bigideas-v1.1.3
raw_dataset_root: data/raw/bigideas/v1.1.3
primary_candidate_id: primary_h30_tau0p5_median3_ols
final_test_accessed: false
chronological_split_created: false
registered_model_started: false
```

- [ ] **Step 2: Implement participant-wise endpoint generation**

The runner must load `configs/audits/bigideas.yaml`, call `audit_bvp_csv` once per participant with the audited rate/window/gap settings, call `load_cgm`, then call `generate_recent_trend_labels` for only `SHORTLIST`. Insert `participant_id`, `bvp_source_file`, `cgm_source_file`, `candidate_id`, `history_minutes`, `threshold_mg_dl_min`, and `smoothing` into every returned row. Assert all endpoints have a timestamp no later than the last CGM record used by their own generator.

- [ ] **Step 3: Implement compact artifacts and figures**

Write the endpoint table as Parquet. Write pairwise and transition tables as CSV. Render (1) a candidate-by-participant exact-label agreement heatmap with non-shared endpoints shown separately by retention figures and (2) normalized 3x3 transition matrices versus the primary. Persist `metrics.json` with the configuration, counts, and `final_test_accessed: false`; persist `run_metadata.json` with Git revision, source config paths, raw-data reread `true`, and no split/model flags.

- [ ] **Step 4: Write summary and runner safety assertions**

The generated summary must state the question, all five candidates, exact endpoint support, agreement, Jaccard, per-participant range, slope-margin diagnostic interpretation, data and provenance, what the result does not prove, and the recommendation. It must state that no label is frozen, no chronological split/model/final test exists, and a human Gate D review is still required before registration.

- [ ] **Step 5: Run static and focused checks**

Run: `uv run ruff check src/glycoband/evaluation/trend_endpoint_stability.py scripts/run_trend_endpoint_stability.py tests/evaluation/test_trend_endpoint_stability.py`

Expected: `All checks passed!`

Run: `uv run pytest tests/evaluation/test_trend_endpoint_stability.py tests/datasets/test_bigideas.py -v`

Expected: all focused tests pass.

### Task 3: Execute and inspect the probe

**Files:**
- Create: `reports/experiments/trend_endpoint_stability-v1/*`
- Modify: `docs/research/journal.md`

**Interfaces:**
- Consumes: the runner produced in Task 2 and only the complete native BIG IDEAs v1.1.3 source.
- Produces: reviewed exploratory evidence, not a scientific freeze.

- [ ] **Step 1: Execute the exact endpoint comparison**

Run: `uv run python scripts/run_trend_endpoint_stability.py --repo-root .`

Expected: concise participant progress for 16 participants, an explicit statement that the final test was not accessed, and an artifact path under `reports/experiments/trend_endpoint_stability-v1/`.

- [ ] **Step 2: Inspect the produced artifacts**

Check that all five candidates appear, 16 participants appear in each candidate block, each pooled shared-endpoint count equals the sum of its per-participant shared counts, all transition cells sum to the same shared count, no output uses a train/validation/test column, and both figures exist.

- [ ] **Step 3: Record the evidence without changing a scientific gate**

Append one concise dated journal entry with the factual result, remaining uncertainty, and recommendation. Do not edit `docs/research/decision_register.md`, `docs/research/readiness_contract.md`, `docs/research/gate_d_decision_brief.md`, or any frozen/not-yet-frozen label/split config.

- [ ] **Step 4: Run required project verification**

Run: `uv run pytest`

Expected: all tests pass.

Run: `uv run ruff check .`

Expected: `All checks passed!`

## Self-review

- Spec coverage: Tasks 1-3 provide exact shared-endpoint agreement, endpoint retention, 3x3 transitions, participant-level visibility, slope-margin diagnostics, provenance, figures, no-future label generation, and an explicit non-freezing result.
- Placeholder scan: no unassigned scientific values are introduced; the existing audited config and shortlist are reused.
- Type consistency: the runner writes the columns validated by `compare_to_primary`; all aggregate tables derive from those exact endpoint rows.
