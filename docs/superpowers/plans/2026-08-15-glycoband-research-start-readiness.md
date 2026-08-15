# GlycoBand Research Start Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare a verified, leakage-resistant research foundation that is ready for architecture design and model experimentation without opening the final test data or making unsupported scientific choices.

**Architecture:** Use a preparation-first sequence: governance and environment, source verification, raw-data audits, scientific contract freeze, split freeze, then architecture and experiment readiness. Hb-PPG and BIG IDEAs remain separate evidence domains. No predictive model is built or trained in this plan.

**Tech Stack:** Python 3.11, uv, YAML, JSON, Parquet, NumPy, SciPy, pandas/Polars, PyArrow, pytest, Ruff, mypy, Git.

## Global Constraints

- Hb-PPG v6 is the only current dataset for Model 1 Fasting State.
- BIG IDEAs v1.1.3 is the only current dataset for Model 2 Recent Trend.
- PhysioCGM remains outside core training, validation, and synthetic-testing scope.
- `data/raw/` is immutable and excluded from Git.
- State evaluation is participant-aware; Trend evaluation is within-person chronological.
- Reference glucose is never a core inference feature.
- Final-test data cannot select labels, thresholds, preprocessing, features, models, calibration, OOD policy, or claims.
- State labels, Trend label protocol, split manifests, final-test opening, core predictors, new datasets, and claim changes require human review.
- Follow `RESEARCH_STANDARDS.md` for artifact, environment, and reporting requirements.
- This is a planning artifact only. Creating this plan does not authorize downloads, implementation, model training, or experiments.

---

## Readiness sequence

```text
Gate A: repository and environment verified
    -> Gate B: source access, storage, versions, and checksums verified
    -> Gate C: both raw-data audits completed
    -> Gate D: targets, labels, and splits human-frozen
    -> Gate E: architecture and experiment contracts approved
    -> only then: build data pipeline and baseline models
```

If a gate fails, stop with `DATA REQUIRED`, `NO-GO`, or a named review decision. Do not compensate by adding model complexity.

## Planned file map

| Path | Responsibility |
|---|---|
| `docs/research/readiness_contract.md` | Single checklist and current Gate A-E status |
| `docs/research/decision_register.md` | Human-reviewed scientific decisions and version history |
| `configs/data_sources.yaml` | Canonical dataset identifiers, versions, sources, expected modalities |
| `data/manifests/source_manifest.json` | Downloaded file identity, checksum, size, and source provenance |
| `reports/audits/environment_preflight.json` | Compact environment, storage, and access evidence |
| `reports/audits/hbppg_audit.md` | Full Hb-PPG schema, quality, glucose, and participant-support audit |
| `reports/audits/bigideas_audit.md` | Full BIG IDEAs coverage, alignment, gap, SQI, and class-feasibility audit |
| `configs/state/label-v1.yaml` | Human-approved State label definition, if support is adequate |
| `configs/trend/label-v1.yaml` | Human-approved Trend history, slope, threshold, smoothing, and gap policy |
| `data/manifests/state_split-v1.json` | Frozen participant-disjoint State split |
| `data/manifests/trend_split-v1.json` | Frozen chronological Trend ranges and embargoes |
| `docs/architecture/readiness_brief.md` | Evidence-based requirements for the later software architecture |
| `docs/research/experiment_contract.md` | Required fields, controls, artifacts, and final-test access rules |
| `reports/audits/model_readiness.md` | Final GO / GO WITH LIMITS / NO-GO / DATA REQUIRED decision |

---

### Task 1: Establish the research readiness contract

**Files:**

- Create: `docs/research/readiness_contract.md`
- Create: `docs/research/decision_register.md`
- Modify: `AGENTS.md`

**Interfaces:**

- Consumes: `Agent/00_INDEX.md` through `Agent/05_EXPERIMENT_AGENT.md` and `RESEARCH_STANDARDS.md`.
- Produces: one visible status page and one versioned record for human review gates.

- [ ] **Step 1: Create the readiness checklist**

  Include Gate A-E, an owner, evidence path, status, blocker, reviewer, and approval date. Allowed statuses are `NOT_STARTED`, `IN_PROGRESS`, `PASS`, `DATA_REQUIRED`, `NO_GO`, and `SUPERSEDED`.

- [ ] **Step 2: Create the decision register**

  Reserve these decision IDs without deciding their values:

  ```text
  SCI-STATE-LABEL-001
  SCI-TREND-LABEL-001
  SCI-STATE-SPLIT-001
  SCI-TREND-SPLIT-001
  SCI-FINAL-TEST-001
  ARCH-PIPELINE-001
  CLAIM-CEILING-001
  ```

  Each entry must record evidence considered, chosen decision, alternatives rejected, reviewer, version, and superseded decision if applicable.

- [ ] **Step 3: Add the readiness contract to repository instructions**

  Add one link under the human-review section of `AGENTS.md`. Do not duplicate the full checklist there.

- [ ] **Step 4: Verify precedence and scope language**

  Run:

  ```powershell
  rg -n "BIG IDEAs|PhysioCGM|human review|final test" AGENTS.md docs/research Agent/00_INDEX.md Agent/05_EXPERIMENT_AGENT.md
  ```

  Expected: BIG IDEAs is current, PhysioCGM is out of core scope, and every final-test action points to a human gate.

**Exit gate:** Gate definitions are unambiguous and no scientific value has been silently frozen.

---

### Task 2: Verify repository, environment, access, and storage

**Files:**

- Create: `reports/audits/environment_preflight.json`
- Modify only if required by observed failure: `pyproject.toml`, `uv.lock`, `.python-version`

**Interfaces:**

- Consumes: local runtime, Git state, dependency lock, data-source access requirements, and available disk capacity.
- Produces: Gate A evidence and a storage/access decision for Gate B.

- [ ] **Step 1: Establish a reviewable Git baseline**

  Inspect all current untracked initialization files. Create the initial commit only after the project lead confirms the scaffold is the intended baseline. Record the resulting commit in the preflight report.

- [ ] **Step 2: Restore the locked environment**

  Run:

  ```powershell
  uv sync --frozen
  uv lock --check
  uv run --frozen pytest
  uv run --frozen ruff check .
  uv run --frozen mypy
  ```

  Expected: dependency restoration succeeds and all checks pass. Any version change requires a reviewed lockfile update rather than manual installation into `.venv`.

- [ ] **Step 3: Measure storage before downloading data**

  Record free space on the target data volume. Calculate required space as the documented raw downloads plus planned interim/processed outputs plus a safety reserve. Gate B fails if available space is less than that documented requirement.

- [ ] **Step 4: Verify data access conditions**

  Confirm that both exact versions are accessible, their licenses/terms permit the intended research use, and any account or credential requirement is known before download. Do not copy credentials into the repository or report.

- [ ] **Step 5: Write the compact preflight report**

  Store only Python version, OS/architecture, Git commit/dirty state, `uv.lock` checksum, check results, data-volume free space, calculated storage requirement, and source-access status.

**Exit gate:** Gate A is `PASS`; Gate B may proceed without an unresolved environment, access, or storage blocker.

---

### Task 3: Verify source identity before bulk acquisition

**Files:**

- Create: `configs/data_sources.yaml`
- Create: `data/manifests/source_manifest.json`
- Create: `docs/research/source_verification.md`

**Interfaces:**

- Consumes: official source pages, DOI/version identifiers, downloaded metadata, file sizes, and checksums.
- Produces: the only approved source list for later audits.

- [ ] **Step 1: Record canonical source contracts**

  `configs/data_sources.yaml` must identify Hb-PPG Figshare v6 and BIG IDEAs PhysioNet v1.1.3, including DOI, expected sensor type, expected modalities, expected participant count, and allowed task.

- [ ] **Step 2: Inspect metadata or one representative participant before bulk processing**

  Confirm actual archive/file naming, encoding, timestamp format, channel representation, units, and metadata columns. Document mismatches from `Agent/03_BASE_DATA.md`; do not adapt assumptions silently.

- [ ] **Step 3: Build the source manifest**

  For every acquired source file record dataset, version, source URL or DOI, relative local path, byte size, SHA-256 checksum, acquisition date, and verification status.

- [ ] **Step 4: Verify immutability**

  Confirm raw paths are ignored by Git and checksum verification detects a modified fixture or copied source file.

**Exit gate:** Gate B is `PASS` only when version, access, file identity, and expected schema are verified. A schema conflict triggers human review before any full audit implementation.

---

### Task 4: Define audit contracts before running full audits

**Files:**

- Create: `docs/research/hbppg_audit_contract.md`
- Create: `docs/research/bigideas_audit_contract.md`
- Create: `tests/fixtures/hbppg/README.md`
- Create: `tests/fixtures/bigideas/README.md`

**Interfaces:**

- Consumes: verified representative schemas from Task 3.
- Produces: exact audit outputs, exclusions, and fixture requirements for separate audit-tool implementation plans.

- [ ] **Step 1: Define the Hb-PPG audit output**

  Require participant/file counts, four-channel availability, rate/duration consistency, missingness, corrupt/duplicate signals, flatline/clipping, pulse detectability, glucose distribution, candidate clinical-category support, participant support per class, and exclusion reasons.

- [ ] **Step 2: Define the BIG IDEAs audit output**

  Require per-participant BVP/CGM start/end/duration, overlap, CGM/BVP gaps, usable aligned hours, valid short windows, SQI distribution, glucose distribution, candidate Trend counts, participant support, and temporal coverage by class.

- [ ] **Step 3: Define audit invariants**

  Include tests that fail on missing participant identity, fake wavelength channels, timestamp disorder, duplicate timestamps, future-CGM label use, loss of source provenance, or reporting window count as participant count.

- [ ] **Step 4: Define privacy-safe fixtures**

  Fixtures must be minimal synthetic software-test data or redistributable excerpts. They cannot be presented as biological evidence or new participants.

**Exit gate:** Audit contracts are reviewable without committing to label thresholds, preprocessing filters, feature sets, or model architecture.

---

### Task 5: Complete the two raw-data audits

**Files:**

- Create through focused implementation plans: `scripts/audit_hbppg.py`, `scripts/audit_bigideas.py`
- Create through those plans: `src/glycoband/datasets/hbppg.py`, `src/glycoband/datasets/bigideas.py`
- Test through those plans: `tests/datasets/test_hbppg.py`, `tests/datasets/test_bigideas.py`
- Produce: `reports/audits/hbppg_audit.md`, `reports/audits/bigideas_audit.md`

**Interfaces:**

- Consumes: verified raw sources, source manifest, and audit contracts.
- Produces: measured evidence needed for all later scientific and architecture decisions.

- [ ] **Step 1: Write a separate TDD implementation plan for the Hb-PPG audit**

  The plan must use real observed schema names, keep all four wavelength identities, preserve participant IDs, and specify exact tests and commands.

- [ ] **Step 2: Implement and run the Hb-PPG audit under that approved plan**

  Do not train a classifier. Report class feasibility as support evidence, not as a final label decision.

- [ ] **Step 3: Review Hb-PPG exclusions and anomalies**

  Every exclusion must have a deterministic reason and source path. Unexplained data loss blocks Gate C.

- [ ] **Step 4: Write a separate TDD implementation plan for the BIG IDEAs audit**

  The plan must process participant-wise/chunk-wise, treat `BVP.csv` as one native stream, preserve timestamps, and avoid loading the full dataset into memory.

- [ ] **Step 5: Implement and run the BIG IDEAs audit under that approved plan**

  Do not train a Trend model. Candidate Trend protocols may be counted, but no final protocol is selected from final-test behavior.

- [ ] **Step 6: Review BIG IDEAs exclusions, gaps, and independence limits**

  Report both valid windows and contributing participants. Sixteen participants remain sixteen independent humans regardless of window count.

**Exit gate:** Gate C is `PASS` only when both reports are complete, reproducible, and independently reviewed. Otherwise return `DATA REQUIRED` or `NO_GO` for the affected task.

---

### Task 6: Freeze scientific targets and split manifests

**Files:**

- Create: `configs/state/label-v1.yaml`
- Create: `configs/trend/label-v1.yaml`
- Create: `data/manifests/state_split-v1.json`
- Create: `data/manifests/trend_split-v1.json`
- Create: `reports/audits/label_and_split_review.md`
- Modify: `docs/research/decision_register.md`

**Interfaces:**

- Consumes: Gate C audit evidence and approved clinical/research definitions.
- Produces: versioned labels and sealed evaluation boundaries for later experiments.

- [ ] **Step 1: Decide State formulation from clinical meaning and participant support**

  Evaluate whether three classes, two classes, a descriptive rare class, or no primary classification is defensible. Record the rejected alternatives and claim consequences. Obtain human approval before writing `label-v1.yaml`.

- [ ] **Step 2: Freeze the State participant split**

  Assign participants once to train/validation/test. Verify disjoint IDs and adequate train/validation support. Seal the test IDs before model or feature selection.

- [ ] **Step 3: Define Trend chronological candidate partitions without using model scores**

  For each participant, define contiguous train, validation, embargo, and future-test ranges from coverage and chronology. No raw history window may cross a boundary.

- [ ] **Step 4: Select the Trend label protocol using audit plus train/validation only**

  Review the candidate 15/30/60-minute histories, slope method, smoothing, threshold, minimum CGM support, alignment tolerance, and gap policy. The future-test range remains sealed.

- [ ] **Step 5: Freeze the Trend label and split manifests**

  Obtain human approval and record the exact history, slope, threshold, smoothing, support, alignment, gap, stride, temporal ranges, and embargo in versioned files.

- [ ] **Step 6: Run leakage assertions**

  Expected: no State participant overlap, no Trend raw-history overlap, embargo at least the selected history, and no future-CGM use in recent-observed labels.

**Exit gate:** Gate D is `PASS`. Any post-freeze change increments the version and records why; final-test inspection cannot justify the change.

---

### Task 7: Prepare the architecture readiness brief

**Files:**

- Create: `docs/architecture/readiness_brief.md`
- Create: `docs/architecture/data_flow.md`
- Modify: `docs/research/decision_register.md`

**Interfaces:**

- Consumes: measured file schemas, volumes, timestamps, audit failure modes, frozen labels, and split contracts.
- Produces: constraints for a later architecture plan, not implementation.

- [ ] **Step 1: Document measured workload shape**

  Record actual file sizes, participant counts, sample rates, window volume, memory constraints, alignment behavior, and expected derived-table size from the audits.

- [ ] **Step 2: Define required boundaries**

  Specify separate Hb-PPG and BIG IDEAs loaders/adapters, shared provenance types, training-only transformations, label modules, split validators, artifact writer, and deterministic Decision Engine boundary.

- [ ] **Step 3: Define failure behavior**

  Require explicit failures for schema mismatch, unknown wavelength identity, corrupt timestamps, insufficient history, poor SQI, OOD, unresolved labels, unsealed splits, and attempted final-test tuning.

- [ ] **Step 4: Record the simplest justified architecture direction**

  Prefer a modular Python package and participant-wise chunk processing. Reject microservices, workflow orchestration platforms, deep-learning infrastructure, and experiment SaaS unless a measured constraint requires them.

- [ ] **Step 5: Review before architecture implementation**

  Confirm every proposed component is justified by an observed requirement. Create the detailed architecture implementation plan only after this review passes.

**Exit gate:** The project can explain what architecture is required and why without having built it prematurely.

---

### Task 8: Prepare the experiment contract without training

**Files:**

- Create: `docs/research/experiment_contract.md`
- Create: `docs/research/final_test_access.md`
- Create: `configs/experiments/baseline_matrix.yaml`

**Interfaces:**

- Consumes: frozen labels/splits, claim boundaries, required metrics, and controls.
- Produces: the exact rules a later baseline/model plan must follow.

- [ ] **Step 1: Define the run contract**

  Require objective, dataset/version, independent unit, inference input, label/split version, baseline, model, primary/secondary metrics, leakage risks, negative control, expected artifacts, Go/No-Go rule, and claim ceiling.

- [ ] **Step 2: Define the baseline and control matrix**

  State requires majority, Logistic Regression, context-only comparison, participant-level label permutation, identity probe, and wavelength ablation. Trend requires majority, always-STABLE, Logistic Regression, time-shift/circular-shift control, and current-window-only versus history ablation.

- [ ] **Step 3: Define reporting metrics**

  Require Macro-F1, balanced accuracy, class support, confusion matrix, per-class metrics, and participant-level results. State adds participant bootstrap where feasible; Trend adds opposite-direction errors.

- [ ] **Step 4: Define final-test access discipline**

  Name the reviewer, approved config/label/split versions, opening condition, one-time evaluation command, artifact destination, and disclosure rule if design changes afterward.

- [ ] **Step 5: Define compact artifact requirements**

  Follow `RESEARCH_STANDARDS.md`: structured predictions and metrics, minimal environment record, diagnostic logs only, and no activity journal.

**Exit gate:** A later experiment cannot start without a complete contract and cannot silently change its success rule after seeing results.

---

### Task 9: Run the final readiness review

**Files:**

- Create: `reports/audits/model_readiness.md`
- Modify: `docs/research/readiness_contract.md`
- Modify: `docs/research/decision_register.md`

**Interfaces:**

- Consumes: Gate A-D evidence plus architecture and experiment readiness briefs.
- Produces: one explicit authorization outcome for the next planning stage.

- [ ] **Step 1: Verify all evidence paths**

  Every `PASS` must link to an existing manifest, report, config, test result, or signed decision. An assertion without evidence is not a pass.

- [ ] **Step 2: Classify readiness per task**

  Give State and Trend separate outcomes: `GO`, `GO_WITH_LIMITS`, `NO_GO`, or `DATA_REQUIRED`. One task may proceed even if the other is blocked; their evidence is independent.

- [ ] **Step 3: Record remaining claim limits and unresolved bridges**

  Keep fingertip-to-wrist transfer, common-sensor validation, and broader-population transfer explicitly unresolved unless new direct evidence exists.

- [ ] **Step 4: Choose the next plan, not the next model**

  If `GO`, write a separate data-pipeline architecture plan first, followed by a baseline-experiment plan. If `GO_WITH_LIMITS`, encode those limits as non-negotiable constraints. If `NO_GO` or `DATA_REQUIRED`, stop and define the smallest evidence-gathering action.

**Exit gate:** Gate E is approved. Only then may architecture implementation or baseline experimentation begin.

---

## Overall completion gate

This preparation plan is complete only when:

- environment and source identity are reproducible;
- storage and access are adequate;
- both raw datasets have evidence-backed audits or an explicit task-level No-Go;
- target and split decisions are human-reviewed and versioned;
- final-test data is sealed;
- architecture requirements come from measured data behavior;
- experiment controls, metrics, artifacts, and stopping rules are fixed;
- State and Trend receive separate readiness outcomes.

Until then, do not build a predictive model, optimize architecture, add deep learning, or open the final test set.
