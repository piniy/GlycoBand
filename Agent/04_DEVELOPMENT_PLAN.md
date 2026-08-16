# GlycoBand — Coding and Development Plan

## Objective

Build a reproducible research codebase that can:

- audit data;
- freeze labels/splits;
- preprocess signals;
- extract features;
- train baselines/models;
- detect leakage;
- run controls;
- evaluate calibration/SQI/OOD;
- run native-derived robustness tests;
- generate paper-ready artifacts.

The codebase should make accidental leakage difficult.

## Repository

```text
glycoband/
├── README.md
├── AGENTS.md
├── pyproject.toml
├── requirements.lock
├── docs/
├── configs/
│   ├── state/
│   ├── trend/
│   ├── excursion/
│   └── synthetic/
├── data/
│   ├── raw/hbppg/
│   ├── raw/bigideas/
│   ├── interim/
│   ├── processed/state/
│   ├── processed/trend/
│   └── manifests/
├── notebooks/
├── src/glycoband/
│   ├── datasets/
│   ├── adapters/
│   ├── preprocessing/
│   ├── labels/
│   ├── features/
│   ├── models/
│   ├── evaluation/
│   ├── synthetic/
│   ├── decision/
│   └── utils/
├── scripts/
├── tests/
└── reports/
    ├── audits/
    ├── experiments/
    ├── figures/
    ├── tables/
    └── final/
```

## Coding standards

Prefer:

- Python 3.11+;
- type hints;
- dataclasses/typed schemas;
- `pathlib`;
- pure transformation functions;
- config-driven experiments;
- pytest;
- structured logging;
- deterministic seeds;
- Parquet for large derived data.

Avoid:

- hardcoded paths;
- notebook-only core logic;
- hidden mutable globals;
- magic thresholds;
- manual preprocessing;
- test-set branching;
- overwriting artifacts without versioning.

## Data loaders

### Hb-PPG

Responsibilities:

- discover participant files;
- load metadata;
- load four waveform channels;
- validate channel names/lengths;
- preserve participant ID.

Suggested:

```python
load_hbppg_recording(participant_id) -> HbPPGRecord
```

### BIG IDEAs

Responsibilities:

- load one participant at a time;
- parse BVP and CGM;
- preserve timestamps;
- expose chunk/iterator access;
- avoid loading the full dataset into RAM.

Suggested:

```python
iter_bigideas_bvp(participant_id, chunk_size=...)
load_bigideas_cgm(participant_id)
```

## Adapters

`StateAdapter` accepts only compatible four-wave input and validates wavelength identity/order/rate/duration/missingness.

`DynamicAdapter` accepts BVP-compatible temporal input and validates timestamps/order/rate/history/gaps.

Adapters do not predict labels.

## Config-driven science

Scientific choices live in config files, not hidden constants.

Example Trend:

```yaml
trend:
  history_minutes: 30
  slope_method: ols
  smoothing: none
  threshold: TBD
  min_cgm_points: TBD
  gap_policy: TBD
```

Example State:

```yaml
state:
  formulation: TBD
  clinical_reference: TBD
  categories: TBD_AFTER_AUDIT_AND_REVIEW
```

## Split manifests

State:

- participant IDs assigned once to train/validation/test;
- automated disjointness assertions.

Trend:

- temporal ranges assigned to train/validation/embargo/test;
- automated raw-history overlap checks.

Do not regenerate splits casually between experiments.

## Training-only transformations

Fit on training only:

- scaler;
- imputer;
- selector;
- PCA if used;
- OOD distribution.

Validation may select hyperparameters/calibration.

Final test uses frozen objects only.

## Experiment artifacts

Use two levels.

### Exploratory analysis

Minimum reproducible record:

```text
question
config/parameters
data version
code commit
result
```

Do not force full model-bundle ceremony for simple audits or sanity checks.

### Registered experiment

Create:

```text
reports/experiments/<experiment_id>/
├── config.yaml
├── environment.txt
├── dataset_manifest.json
├── split_manifest.json
├── metrics.json
├── per_participant.csv
├── predictions.parquet
├── confusion_matrix.png
└── model_bundle/
```

Add detailed logs only when diagnostically useful.

Model bundle should contain enough information to reproduce inference and interpretation:

- model;
- feature list;
- preprocessing config;
- scaler/imputer/selector;
- calibrator/OOD object if used;
- label definition;
- dataset version;
- split IDs;
- seed;
- git commit;
- metrics summary.

## Mandatory tests

- State: no participant leakage.
- Trend: no material temporal overlap.
- Trend labels: no future-CGM usage.
- Synthetic: original participant/label/source provenance preserved.
- Resampling: rate/length/anti-alias behavior.
- Decision Engine: valid, unavailable, poor SQI, OOD, low confidence, timestamp handling.

Run only tests whose assumptions are affected unless a full-suite run is explicitly needed.

## Compute strategy

Core stack:

```text
NumPy
SciPy
pandas/Polars
PyArrow
scikit-learn
XGBoost
matplotlib
```

Use PyTorch only for justified later sequence models.

BIG IDEAs workflow:

```text
participant
-> chunk
-> preprocess
-> window
-> features
-> Parquet
-> release memory
```

## Experiment completion

A registered experiment is complete when it has:

- immutable config;
- explicit data version;
- split manifest;
- baseline comparison;
- applicable leakage checks;
- applicable negative control;
- required per-class/per-participant metrics;
- saved predictions;
- reproducible artifacts;
- interpretation;
- claim ceiling;
- limitations.

Do not turn this checklist into a requirement for unrelated small tasks.
