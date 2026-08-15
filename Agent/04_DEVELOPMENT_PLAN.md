# GlycoBand — Coding and Development Plan

## Objective

Build a reproducible research codebase that can audit data, freeze labels/splits, preprocess signals, extract features, train baselines/models, detect leakage, run controls, evaluate calibration/SQI/OOD, perform native-derived robustness testing, and generate paper-ready artifacts.

The codebase should make accidental test leakage difficult.

## Recommended repository

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
│   ├── 01_hbppg_data_understanding.ipynb
│   ├── 02_bigideas_data_understanding.ipynb
│   ├── 03_state_baselines.ipynb
│   └── 04_trend_baselines.ipynb
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

Prefer Python 3.11+, type hints, dataclasses/typed schemas, pathlib, pure transformation functions, config-driven experiments, pytest, structured logging, deterministic seeds, and Parquet for large derived data.

Avoid hardcoded paths, notebook-only core logic, hidden mutable globals, magic thresholds, manual preprocessing, test-set branching, and overwriting artifacts without versioning.

## Data loaders

### Hb-PPG loader

Responsibilities:

- discover participant files,
- load metadata,
- load four waveform channels,
- validate channel names/lengths,
- preserve participant ID.

Suggested interface:

```python
load_hbppg_recording(participant_id) -> HbPPGRecord
```

### BIG IDEAs loader

Responsibilities:

- load one participant at a time,
- parse BVP and Dexcom,
- preserve timestamps,
- expose chunk/iterator access,
- avoid requiring the full dataset in RAM.

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

Scientific choices must live in config files, not hidden constants.

Example Trend config:

```yaml
trend:
  history_minutes: 30
  slope_method: ols
  smoothing: none
  threshold: TBD
  min_cgm_points: TBD
  gap_policy: TBD
```

Example State config:

```yaml
state:
  formulation: TBD
  clinical_reference: TBD
  categories: TBD_AFTER_AUDIT_AND_REVIEW
```

## Split manifests

State: participant IDs assigned once to train/validation/test; automated disjointness assertions.

Trend: temporal ranges assigned to train/validation/embargo/test; automated raw-history overlap checks.

Do not regenerate splits casually between experiments.

## Training-only transformations

Fit on training only:

- scaler,
- imputer,
- selector,
- PCA if ever used,
- OOD distribution.

Validation may select hyperparameters/calibration. Final test uses frozen objects only.

## Experiment artifacts

Each run should create:

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
├── logs.txt
└── model_bundle/
```

Model bundle should contain model, feature list, preprocessing config, scaler/imputer/selector, calibrator, OOD model, label definition, dataset version, split IDs, seed, git commit, and metrics summary.

## Mandatory tests

- State: no participant leakage.
- Trend: no material temporal overlap.
- Trend labels: no future-CGM usage for recent-observed Trend.
- Synthetic: original participant/label/source provenance preserved.
- Resampling: rate/length/anti-alias behavior.
- Decision Engine: valid, unavailable, poor SQI, OOD, low confidence, mixed timestamps.

## Compute strategy

Core stack: NumPy, SciPy, pandas/Polars, PyArrow, scikit-learn, XGBoost, matplotlib. PyTorch only for justified later sequence models.

BIG IDEAs workflow:

```text
participant -> chunk -> preprocess -> window -> features -> Parquet -> release memory
```

## Milestones

1. Source verification + manifests.
2. Hb-PPG and BIG IDEAs Data Understanding Reports.
3. Human-reviewed target + split freeze.
4. Baselines.
5. Classical models + ablations.
6. Leakage/negative controls + calibration/SQI/OOD.
7. Frozen held-out evaluation.
8. Synthetic robustness.
9. Candidate engineering envelope.
10. Optional Model 2B / small sequence models / integration demo.

## Definition of done

An experiment is done only when it has immutable config, explicit data version, split manifest, baseline comparison, leakage checks, negative control where applicable, per-class/per-participant metrics, saved predictions, reproducible artifacts, interpretation, claim ceiling, and limitations.
