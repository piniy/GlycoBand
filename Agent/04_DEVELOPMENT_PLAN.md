# GlycoBand — Coding and Development Plan

## Objective

Build a reproducible research codebase that can audit data, run cheap exploratory probes, freeze labels/splits, train registered models, detect leakage, run controls, and generate defensible research artifacts.

The codebase should make accidental final-test leakage difficult without turning every exploratory question into a large implementation ceremony.

## Repository

```text
glycoband/
├── README.md
├── AGENTS.md
├── Agent/
├── configs/
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── manifests/
├── notebooks/
├── src/glycoband/
├── scripts/
├── tests/
└── reports/
    ├── audits/
    ├── probes/
    ├── experiments/
    ├── figures/
    ├── tables/
    └── final/
```

## Coding standards

Prefer:

- Python 3.11+;
- type hints;
- pure transformation functions;
- config-driven experiments;
- deterministic seeds;
- pytest;
- Parquet for large derived data.

Avoid:

- hardcoded paths;
- hidden mutable globals;
- test-set branching;
- reference glucose in inference features;
- random participant/time leakage;
- unnecessary framework or orchestration complexity.

## Split protection

State:

- participant-disjoint outer test reserve;
- participant-grouped development validation.

Trend:

- chronological outer test reserve;
- no raw-history overlap across boundaries;
- embargo at least as large as the active history requirement when needed.

Do not regenerate a reserve because a development result is weak.

## Two computational artifact levels

### Exploratory probe

Purpose: answer one uncertainty cheaply.

Minimum record:

```text
question
candidate(s) compared
data version
reserve/split rule
simple method
seed if relevant
result
interpretation
what it does not prove
```

Exploratory probes:

- may run before target/protocol freeze;
- use development data only;
- normally use descriptive analysis, Dummy/majority, or Logistic Regression;
- do not require full model bundles, calibration, OOD, or paper-ready reporting;
- are stored under `reports/probes/` when worth retaining;
- must never touch the sealed final test.

### Registered experiment

Purpose: produce evidence for the scientific conclusion.

Requires relevant target/split contract frozen.

Recommended artifact set:

```text
reports/experiments/<experiment_id>/
├── config.yaml
├── dataset_manifest.json
├── split_manifest.json
├── metrics.json
├── per_participant.csv
├── predictions.parquet
└── model_bundle/
```

Add artifacts only when they improve reproducibility or interpretation.

## Training-only transformations

For registered experiments, fit on training only:

- scaler;
- imputer;
- selector;
- PCA if used;
- OOD distribution.

Validation may select hyperparameters/calibration.

Final test uses frozen objects only.

Exploratory probes may use a simpler development-only preprocessing path, but it must still avoid leakage across the development validation boundary.

## Mandatory tests by risk

Always preserve these invariants when relevant:

- State: no participant leakage into outer test.
- Trend: no temporal/raw-history overlap into outer test.
- Trend labels: no future-CGM usage.
- Reference glucose/CGM: never core inference feature.

Do not force the full registered-experiment checklist onto a cheap exploratory probe.

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

BIG IDEAs:

```text
participant
-> chunk
-> preprocess
-> window
-> features
-> Parquet
-> release memory
```

## Implementation priority

When scientific uncertainty remains:

```text
small script/notebook/probe
-> answer the uncertainty
-> only then build reusable production-style module if still needed
```

Do not build a large contract/module/test stack merely to discover that the underlying scientific formulation should be changed.
