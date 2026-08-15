# GlycoBand Research & Development Agent Context
## AGENT.md — Research Plan v2

> **Purpose:** starting context for a coding/research agent helping execute the GlycoBand research and development workflow.
>
> **Project status:** feasibility research framework, not a validated medical device.
>
> **Primary scientific question:** does PPG contain useful information for (1) **fasting glycemic state** and (2) **recent glucose trend**, when each task is evaluated using the dataset structure that actually supports it?

---

# 1. Core Thesis

GlycoBand does **not** begin by assuming that one wrist PPG sensor is already capable of behaving like a non-invasive CGM.

The project decomposes the problem into two independent experts:

```text
Hb-PPG
fingertip + 4 wavelengths + fasting venous glucose
        ↓
FASTING STATE EXPERT

PhysioCGM
wrist PPG + longitudinal CGM + T1D cohort
        ↓
RECENT TREND EXPERT
```

The outputs are then handled by a deterministic **Decision Engine**.

Future engineering ambition:

```text
ONE FUTURE PPG SENSOR
        │
   ┌────┴────┐
   ↓         ↓
 STATE     TREND
 EXPERT    EXPERT
   │         │
   └────┬────┘
        ↓
DECISION ENGINE
```

That common physical sensor is a **future engineering hypothesis**, not something validated by the two public datasets.

---

# 2. Frozen Research Questions

## RQ1 — Fasting State

> Does multi-wavelength PPG contain enough predictive information to classify **fasting glycemic state** across individuals under participant-aware validation?

## RQ2 — Recent Trend

> Does longitudinal wrist PPG contain predictive information about **recent glucose direction** under within-person chronological evaluation in the available PhysioCGM T1D cohort?

## RQ3 — Robustness

> How sensitive is each expert to controlled waveform degradation representing limitations of future PPG acquisition?

## RQ4 — Engineering Integration

> What candidate sensor requirements and decision logic can be derived from the independently validated State and Trend experts for a future single-sensor GlycoBand?

---

# 3. Claims and Non-Claims

## Allowed if supported by results

- PPG contains predictive information for fasting glycemic state under participant-aware evaluation.
- Temporal PPG contains predictive information for recent glucose direction within the evaluated T1D cohort.
- Certain wavelengths/features contribute more strongly to the State task.
- Controlled degradation produces measurable performance loss and can suggest engineering requirements.
- State and Trend outputs can be composed semantically through a deterministic decision architecture.

## Not allowed at the current evidence level

- GlycoBand measures blood glucose.
- GlycoBand is a non-invasive CGM.
- GlycoBand replaces a glucometer/CGM.
- GlycoBand diagnoses diabetes or prediabetes.
- GlycoBand prevents diabetes.
- GlycoBand provides insulin or therapy guidance.
- One wrist sensor has already been validated for both experts.
- T1D Trend results generalize to healthy, prediabetes, T2D, or the general population.
- Fingertip State results generalize to wrist acquisition.
- Synthetic data proves physical-device accuracy.
- Combining State and Trend automatically improves accuracy.

---

# 4. Evidence Levels

Keep four evidence layers separate in code, reports, plots, and paper wording.

## Level A — Native Predictive Validation

```text
real held-out Hb-PPG      → State Expert
real held-out PhysioCGM   → Trend Expert
```

This is the strongest project evidence.

## Level B — Native-Derived Synthetic Robustness

```text
real held-out waveform
      ↓
controlled degradation
      ↓
frozen model
```

This tests robustness **inside the native model domain**.

## Level C — Software Integration Demonstration

Synthetic/fixture inputs may verify:

- adapters;
- inference APIs;
- Decision Engine;
- error handling;
- output schemas;
- UI/demo flow.

This does **not** validate predictive capability.

## Level D — Engineering Inference

Combine findings from the two independent robustness studies to propose candidate sensor requirements.

This does **not** validate a common physical GlycoBand sensor.

---

# 5. Dataset A — Hb-PPG 2026

**Paper:** *A Four-Wavelength Photoplethysmography dataset for non-invasive hemoglobin assessment*  
**Journal:** Scientific Data, 2026  
**DOI:** `10.1038/s41597-026-06945-6`  
**Dataset DOI:** `10.6084/m9.figshare.22256143.v6`

## Relevant properties

- about 252 adults;
- four PPG wavelengths:
  - 660 nm;
  - 730 nm;
  - 850 nm;
  - 940 nm;
- reflective PPG;
- left index fingertip;
- approximately 200 Hz;
- approximately 12-bit ADC;
- approximately 45–60 s signal recordings;
- fasting venous blood glucose;
- fasting protocol approximately ≥8 h without caloric intake;
- metadata includes age, sex/gender, height, weight, Hb, blood glucose, SBP, DBP, signal length.

## Research role

```text
Hb-PPG → FASTING STATE EXPERT
```

## Unique advantage

```text
MANY PEOPLE
+
MULTI-WAVELENGTH
+
STANDARDIZED FASTING REFERENCE
```

This is useful for cross-person State and wavelength analysis.

## What it does not directly support

- arbitrary-time glucose state;
- post-meal state;
- wrist inference;
- continuous trend;
- repeated same-person dynamics;
- a validated wrist GlycoBand.

---

# 6. Dataset B — PhysioCGM 2025

**Paper:** *A multimodal physiological dataset for non-invasive blood glucose estimation*  
**Journal:** Scientific Data, 2025  
**DOI:** `10.1038/s41597-025-06090-6`  
**Repository:** `https://github.com/PSI-TAMU/PhysioCGM`

## Relevant properties

- 10 participants;
- all have Type 1 Diabetes;
- ambulatory recording;
- up to approximately 17 days;
- Empatica E4 wrist PPG/BVP approximately 64 Hz;
- additional E4 modalities: EDA, accelerometer, skin temperature, derived HR;
- Zephyr modalities include ECG, respiration, accelerometry, HR-related outputs;
- Dexcom G6 interstitial glucose approximately every 5 min;
- synchronized longitudinal physiological and glucose timeline.

## Research role

```text
PhysioCGM → RECENT TREND EXPERT
```

## Unique advantage

```text
FEW PEOPLE
+
LOTS OF TIME
+
WRIST PPG
+
REPEATED GLUCOSE REFERENCE
```

## Core limitation

All participants are T1D.

Therefore the strongest Trend claim is limited to the available T1D cohort unless future population-transfer evidence is collected.

`T1D=true` is a **population descriptor**, not a useful model feature because it has no variance in this dataset.

Never create a synthetic non-T1D participant by changing metadata to `T1D=false`.

---

# 7. Why the Two Datasets Need Different Experts

Oversimplified:

```text
Hb-PPG
= many people × little time
= strong candidate for cross-person fasting STATE

PhysioCGM
= few people × lots of time
= strong candidate for within-person TREND
```

Their strengths combine **conceptually**, not statistically.

Hb-PPG does not make PhysioCGM a 252-person longitudinal dataset.

PhysioCGM does not validate State on the wrist.

---

# 8. Repository Architecture

Recommended repository:

```text
glycoband/
├── AGENT.md
├── README.md
├── pyproject.toml
│
├── configs/
│   ├── state.yaml
│   ├── trend.yaml
│   ├── synthetic_state.yaml
│   ├── synthetic_trend.yaml
│   └── integration.yaml
│
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   └── manifests/
│
├── notebooks/
│   ├── 01_hbppg_audit.ipynb
│   ├── 02_physiocgm_audit.ipynb
│   ├── 03_state_experiments.ipynb
│   └── 04_trend_experiments.ipynb
│
├── src/glycoband/
│   ├── datasets/
│   │   ├── hbppg.py
│   │   └── physiocgm.py
│   ├── preprocessing/
│   │   ├── integrity.py
│   │   ├── filtering.py
│   │   ├── normalization.py
│   │   ├── segmentation.py
│   │   └── sqi.py
│   ├── features/
│   │   ├── morphology.py
│   │   ├── timing.py
│   │   ├── spectral.py
│   │   ├── statistics.py
│   │   ├── wavelength.py
│   │   └── temporal.py
│   ├── labels/
│   │   ├── state.py
│   │   └── trend.py
│   ├── models/
│   │   ├── baselines.py
│   │   ├── state.py
│   │   ├── trend.py
│   │   └── calibration.py
│   ├── evaluation/
│   │   ├── splits.py
│   │   ├── metrics.py
│   │   ├── leakage.py
│   │   ├── bootstrap.py
│   │   ├── permutation.py
│   │   └── ood.py
│   ├── synthetic/
│   │   ├── state_degradation.py
│   │   └── trend_degradation.py
│   ├── decision/
│   │   ├── schemas.py
│   │   ├── gates.py
│   │   └── engine.py
│   └── utils/
│
├── scripts/
│   ├── audit_hbppg.py
│   ├── audit_physiocgm.py
│   ├── train_state.py
│   ├── train_trend.py
│   ├── evaluate_state.py
│   ├── evaluate_trend.py
│   ├── run_state_robustness.py
│   ├── run_trend_robustness.py
│   └── integration_demo.py
│
├── tests/
│   ├── test_splits.py
│   ├── test_no_subject_leakage.py
│   ├── test_no_temporal_leakage.py
│   ├── test_label_generation.py
│   ├── test_synthetic_label_preservation.py
│   └── test_decision_engine.py
│
└── reports/
    ├── audits/
    ├── state/
    ├── trend/
    ├── robustness/
    └── integration/
```

---

# 9. Reproducibility Rules

## Raw data

Never modify raw source data in place.

Use:

```text
data/raw/
data/interim/
data/processed/
```

## Dataset manifests

For every usable signal store:

- dataset/version;
- participant ID;
- file path;
- recording ID;
- modality;
- wavelength/channel;
- sampling rate;
- timestamp range;
- reference availability;
- missingness;
- exclusion reason;
- preprocessing version.

## Every experiment must log

- git commit;
- random seed;
- dataset version;
- split manifest;
- config;
- preprocessing version;
- feature version;
- model hyperparameters;
- calibration method;
- thresholds;
- metrics;
- artifact paths.

Prefer MLflow/W&B or a simple structured local registry.

---

# 10. Phase 1 — Hb-PPG Audit

Before training any State model, audit:

## Structure

- unique participant count;
- recordings per participant;
- wavelength availability;
- equal/unequal channel lengths;
- actual vs expected sampling rate;
- corrupt files;
- duplicate/near-duplicate signals;
- missing fasting glucose;
- missing metadata;
- signal duration.

## Signal quality

Per channel:

- NaN/Inf rate;
- zero variance;
- long constant runs;
- clipping;
- discontinuities;
- implausible timing gaps;
- approximate SNR;
- pulse detectability;
- pulse periodicity;
- cross-channel alignment.

## Glucose distribution

Inspect:

- histogram;
- quantiles;
- min/max;
- outliers;
- candidate class counts;
- participant support per class.

Do **not** freeze the State labels before this audit.

---

# 11. Phase 1 — PhysioCGM Audit

For each participant:

- recording start/end;
- usable duration;
- PPG coverage;
- CGM coverage;
- overlap between PPG and CGM;
- gaps;
- continuous blocks;
- motion-heavy periods if accelerometer is available;
- SQI distribution.

For CGM:

- duplicate timestamps;
- missing values;
- glucose distribution;
- rate-of-change distribution;
- candidate FALLING/STABLE/RISING counts;
- long stable periods;
- rapid excursions.

For PPG:

- observed sampling rate;
- missing samples;
- clipping;
- amplitude distribution;
- pulse detectability;
- drift;
- motion contamination.

---

# 12. Cleaning and Preprocessing Principles

Cleaning must be conservative.

The objective is not to make every signal aesthetically smooth. The objective is to remove obvious acquisition corruption without erasing plausible physiology.

General pipeline:

```text
raw waveform
    ↓
integrity check
    ↓
timestamp check
    ↓
SQI
    ↓
detrend/filter
    ↓
normalization candidate
    ↓
segmentation
    ↓
feature extraction
    ↓
feature QC
```

## Candidate filter

A research starting band around:

```text
0.5–8 Hz
```

may be tested for pulse morphology, but this is a **configurable candidate**, not a sacred fixed rule.

Filter choice must be selected on train/validation only.

## Normalization ablation

Compare:

1. raw-scaled features where meaningful;
2. robust per-record normalization;
3. z-score normalization;
4. AC/DC-like features;
5. morphology-only features.

Normalization can remove useful amplitude information, so treat it as an experiment rather than an automatic step.

---

# 13. Signal Quality Index (SQI)

Candidate SQI components:

- missing fraction;
- clipped fraction;
- zero-variance fraction;
- implausible pulse rate;
- beat-detection success;
- waveform template correlation;
- periodicity;
- spectral concentration;
- approximate SNR;
- abrupt amplitude jumps.

For PhysioCGM, accelerometer may be used as **quality/context information** for motion contamination.

Do not silently make accelerometer a glucose predictor in the PPG-only core model.

Suggested states:

```text
GOOD
MARGINAL
POOR
```

Core gate:

```text
POOR → NO_ESTIMATE
```

---

# 14. Model 1 — Fasting State Expert

## Task

```text
multi-wavelength fasting fingertip PPG
        ↓
fasting glycemic state
```

This model is **not** an arbitrary-time current-glucose estimator.

## Core input

```text
PPG_660
PPG_730
PPG_850
PPG_940
```

## Ground truth

```text
fasting venous blood glucose
```

---

# 15. Model 1 — Feature Families

## Morphology

- pulse amplitude;
- pulse width;
- rise time;
- decay time;
- area;
- symmetry;
- peak-to-foot timing;
- slope features;
- first/second derivative extrema.

## Timing

- beat interval;
- mean pulse interval;
- PPG-derived RMSSD-like statistic;
- interval SD;
- coefficient of variation;
- pulse-rate estimate.

## Statistical

- mean;
- median;
- SD;
- MAD;
- skewness;
- kurtosis;
- entropy candidates.

## Spectral

- dominant frequency;
- band power;
- harmonic energy;
- spectral centroid;
- spectral entropy;
- optional MFCC-like representation only if justified.

## Cross-wavelength

- normalized amplitude ratios;
- morphology ratios;
- spectral energy ratios;
- other physically interpretable wavelength relationships.

Do not invent meaningless ratios solely to increase feature count.

---

# 16. Model 1 — Context Ablation

Run three branches:

```text
A. PPG only
B. age + sex + BMI only
C. PPG + age + sex + BMI
```

Why:

- A tests the real sensing hypothesis.
- B measures demographic prior.
- C tests whether context adds information.

If:

```text
C ≈ B
```

then PPG may contribute little incremental information.

Do not use Hb or blood pressure as core product-facing predictors.

---

# 17. Model 1 — State Labels

Do not hardcode final thresholds until the Hb-PPG glucose distribution is audited.

Workflow:

1. inspect glucose distribution;
2. define clinically interpretable candidate categories;
3. verify sample support;
4. merge categories if needed;
5. freeze labels in config before final model selection;
6. never use final test performance to redefine labels.

Primary target should remain coarse classification if data support it.

Secondary target:

```text
PPG → fasting glucose regression
```

Regression is exploratory/secondary unless it survives strict participant-aware evaluation.

---

# 18. Model 1 — Algorithms

Always begin simple.

## Baselines

- majority class;
- stratified random classifier;
- context-only logistic regression.

## Candidate models

### Logistic Regression

- standardized features;
- class weights if needed;
- L1/L2/elastic-net candidates.

### Random Forest

Tune inside training/validation only:

- trees;
- depth;
- min samples;
- max features;
- class weighting.

### XGBoost

Tune:

- max depth;
- learning rate;
- estimators;
- subsampling;
- column sampling;
- regularization.

### SVM

Optional after standardized features.

### Deep learning

Not primary.

Only consider it after classical models show real signal.

---

# 19. Model 1 — Splitting

Participant-aware splitting is **non-negotiable**.

Never allow windows/recordings from the same person in train and test.

Preferred pattern:

```text
participants
     ↓
frozen subject-level final test set
     ↓
remaining participants
     ↓
group-aware inner CV
```

Use, depending on class support:

- `GroupShuffleSplit`;
- `StratifiedGroupKFold`;
- `GroupKFold`.

Fit only on training data:

- scaler;
- imputer;
- feature selector;
- PCA if used;
- calibration;
- OOD model.

---

# 20. Model 1 — Evaluation

Primary:

```text
Macro-F1
```

Also report:

- balanced accuracy;
- per-class precision/recall/F1;
- confusion matrix;
- support;
- calibration;
- Brier score;
- ECE or equivalent;
- participant-level bootstrap CI.

Regression:

- MAE;
- RMSE;
- R²;
- mean bias;
- residual plots.

Correlation alone is not acceptable as the main result.

---

# 21. Model 1 — Wavelength Ablation

Mandatory.

Run single wavelengths:

```text
660
730
850
940
```

Then selected/all combinations:

```text
660+730
660+850
660+940
730+850
730+940
850+940
all four
```

Purpose:

> derive which optical channels appear necessary for the State task.

This is one of the key bridges to future hardware requirements.

---

# 22. Model 1 — Negative Controls

## Participant-level label permutation

Shuffle fasting glucose/state labels across participants.

Expected:

```text
performance → baseline
```

If not, inspect leakage or identity proxies.

## Context-only comparison

PPG must show incremental information beyond context if the sensing thesis is to be strong.

## Identity probe

Optionally test how strongly features identify subjects.

High identity information increases leakage risk and reinforces the need for group-aware evaluation.

---

# 23. Model 2 — Recent Trend Expert

## Task

```text
recent wrist PPG history
        ↓
FALLING / STABLE / RISING
```

This is **recent observed direction**, not future forecasting.

## Core input

```text
PPG only
```

CGM is not an input feature.

T1D status is not an input feature.

Age/BMI/sex are not primary predictors.

---

# 24. Model 2 — CGM Label Generation

CGM is used to construct trend labels.

Example:

```text
08:00 160
08:05 171
08:10 183
08:15 194
```

Compute recent slope:

```text
s_t = dG/dt
```

Then:

```text
s_t < -tau   → FALLING
|s_t| <= tau → STABLE
s_t > tau    → RISING
```

## Primary slope method

Use ordinary least-squares slope over CGM points in the recent history window.

Reasons:

- simple;
- interpretable;
- reproducible;
- uses all points, not just endpoints.

Sensitivity candidates:

- endpoint delta;
- Theil–Sen robust slope.

Freeze the final method on train/validation only.

---

# 25. Trend Windowing

Do **not** assume that CGM every 5 minutes means the model history must equal 5 minutes.

Candidate history horizons:

```text
15 min
30 min
60 min
```

Exact H must be chosen from train/validation results and class feasibility.

The PPG may first be divided into short windows, e.g. candidate:

```text
30 s
```

Then features are aggregated over the longer H.

---

# 26. Trend Temporal Features

For each short PPG window, extract morphology/timing/spectral/statistical/SQI features.

Across H, derive:

- mean;
- median;
- SD;
- min/max;
- first-to-last delta;
- OLS slope;
- robust slope;
- coefficient of variation;
- early-vs-late difference;
- HR change;
- morphology change;
- spectral change;
- low-SQI fraction.

The initial Trend models should use these fixed-dimensional temporal summaries.

---

# 27. Model 2 — Algorithms

## Baselines

- majority class;
- always-STABLE;
- logistic regression.

## Classical models

- Random Forest;
- XGBoost;
- optional SVM.

## Sequence models — optional

Only after classical models show meaningful signal:

- TCN;
- GRU;
- LSTM.

Do not confuse millions of PPG samples with millions of independent humans.

Independent participant count remains 10.

---

# 28. Model 2 — Primary Validation

Primary evaluation is **within-person chronological**.

For each participant:

```text
early ~65–70%  → train
next ~10–15%   → validation
final ~20%     → test
```

Use contiguous time ranges, not shuffled windows.

## Temporal embargo

If history window is H:

```text
embargo >= H
```

between train/validation/test.

No raw PPG sample or overlapping history window may cross a split boundary.

---

# 29. Model 2 — Subject-Dependent Modeling

Primary evidence may use one model per participant with the same algorithmic pipeline.

Report:

- each participant separately;
- median/mean performance;
- variability;
- number of participants that beat baseline.

A model working on only 1–2 participants is not strong Trend evidence.

---

# 30. Model 2 — Secondary LOSO Stress Test

Optional:

```text
train 9 participants
→ test the 10th
```

This evaluates cross-person transfer.

Because the dataset is small and physiology varies strongly between participants, LOSO is a stress test rather than the primary success criterion.

---

# 31. Model 2 — Metrics

Primary:

```text
Macro-F1
```

Also:

- balanced accuracy;
- per-class F1;
- confusion matrix;
- class support;
- calibration;
- per-participant metrics;
- confidence intervals.

Track **opposite-direction error** separately:

```text
RISING → FALLING
FALLING → RISING
```

These are more semantically severe than RISING/FALLING → STABLE.

---

# 32. Model 2 — Negative Controls

## Time-shift control

Break the real PPG–CGM temporal alignment while preserving temporal autocorrelation.

Example:

```text
circularly shift CGM-derived labels by a large offset
```

Expected:

```text
performance should collapse
```

If performance stays high, inspect:

- leakage;
- time-of-day confounding;
- participant identity;
- class imbalance.

## Always-STABLE baseline

Accuracy alone is unacceptable because STABLE may dominate.

## Input leakage audit

No CGM/current/future glucose-derived value may enter X.

---

# 33. Calibration

If models emit probabilities, calibrate using validation data only.

Candidates:

- Platt scaling;
- isotonic regression;
- temperature scaling for neural models.

Output must expose:

```text
label
probabilities
confidence
calibration status
```

---

# 34. OOD Detection

Fit OOD logic on training features only.

Candidate methods:

1. robust z-score/quantile bounds;
2. Mahalanobis distance;
3. Isolation Forest as exploratory.

Output:

```text
OOD = true/false
OOD_score
```

OOD should inform the Decision Engine.

---

# 35. Synthetic Waveform Policy — Critical

Scientific robustness uses **two different synthetic pipelines**.

Do not force one universal waveform into both models for validation.

General rule:

```text
real held-out native waveform
        ↓
controlled sensor degradation
        ↓
synthetic degraded waveform
```

Keep the original real biological label.

Never create:

```text
random PPG + invented glucose
```

and call it validation.

---

# 36. Synthetic Input — Model 1

Source:

```text
real held-out Hb-PPG
```

Preserve:

- four real channels/wavelengths;
- real participant;
- real fasting glucose label.

Candidate degradation experiments:

## Downsampling

```text
200 → 100 → 64 → 50 → 32 Hz
```

Use proper anti-aliasing/resampling.

## Quantization

Candidate ADC depths:

```text
12 → 10 → 8 bit
```

## Additive noise

Candidate SNR levels:

```text
30 dB
20 dB
10 dB
5 dB
```

## Other degradations

- baseline drift;
- amplitude attenuation;
- clipping;
- missing samples;
- bounded timing jitter.

## Forbidden

Do not:

- copy one PPG channel into all wavelengths;
- invent wavelength relationships;
- invent glucose labels;
- alter metadata to make fake people;
- call synthetic degradations new participants.

---

# 37. Synthetic Input — Model 2

Source:

```text
real held-out PhysioCGM wrist PPG
```

Preserve:

- real participant;
- real chronology;
- original CGM-derived Trend label.

Candidate degradation experiments:

## Downsampling

```text
64 → 32 → 16 Hz
```

## Quantization

Simulate reduced ADC resolution.

## Additive noise

Controlled SNR.

## Motion-like contamination

Possible approaches:

- controlled band-limited disturbance;
- amplitude modulation;
- natural high-motion/low-SQI windows as observed robustness strata.

Do not claim a synthetic motion generator is physiologically equivalent to all real motion artifacts.

## Other degradations

- dropout;
- missing short windows;
- baseline drift;
- clipping;
- amplitude attenuation;
- timing jitter.

## Forbidden

Do not:

- set `T1D=false` to create a synthetic healthy person;
- invent prediabetes participants;
- invent CGM trajectories;
- pair arbitrary PPG with arbitrary glucose;
- use synthetic metadata as population validation.

---

# 38. Why Synthetic Inputs Must Differ

State native domain:

```text
fingertip
4 wavelengths
~200 Hz
short controlled fasting recording
```

Trend native domain:

```text
wrist
Empatica E4
~64 Hz
ambulatory longitudinal recording
T1D cohort
```

Therefore:

```text
Synthetic_State != Synthetic_Trend
```

for scientific robustness evaluation.

That is not a flaw. It is the correct consequence of the evidence available.

---

# 39. One Common Synthetic Waveform

A common waveform may be used only for:

```text
SOFTWARE / INTERFACE / INTEGRATION TEST
```

It can verify:

- adapter routing;
- API shape;
- model-service orchestration;
- Decision Engine logic;
- output formatting;
- error handling.

It does **not** validate:

- physiological compatibility;
- domain transfer;
- model accuracy;
- one physical sensor.

Prefer integration fixtures containing two domain-compatible payloads under one simulated session to avoid confusing a functional test with scientific evidence.

---

# 40. Three Distinct Test Suites

## A. Predictive Validation

```text
native HbPPG test → State
native PhysioCGM test → Trend
```

Answers:

> Does each model work in the domain it learned from?

## B. Synthetic Robustness

```text
native held-out PPG
+
controlled degradation
```

Answers:

> How robust is each model to sensor limitations?

## C. Integration Demonstration

```text
fixture/synthetic adapter input
→ models/services
→ Decision Engine
```

Answers:

> Does the software architecture work end-to-end?

Never mix these three evidence levels in one metric table.

---

# 41. Decision Engine

The Decision Engine is deterministic.

It is **not Model 3**.

It does not estimate new glucose.

## State output schema

Example:

```json
{
  "type": "FASTING_STATE",
  "label": "ELEVATED",
  "probabilities": {
    "LOW": 0.04,
    "TARGET": 0.12,
    "ELEVATED": 0.84
  },
  "confidence": 0.84,
  "timestamp": "...",
  "protocol": {
    "fasting": true,
    "fasting_hours": 8.4
  },
  "sqi": "GOOD",
  "ood": false,
  "model_version": "state-v1"
}
```

## Trend output schema

```json
{
  "type": "RECENT_TREND",
  "label": "FALLING",
  "probabilities": {
    "FALLING": 0.78,
    "STABLE": 0.16,
    "RISING": 0.06
  },
  "confidence": 0.78,
  "timestamp": "...",
  "history_minutes": 30,
  "sqi": "GOOD",
  "ood": false,
  "population_scope": "PhysioCGM_T1D",
  "model_version": "trend-v1"
}
```

---

# 42. Decision Rules

## Rule 1 — poor SQI

```text
POOR → NO_ESTIMATE
```

## Rule 2 — State protocol not satisfied

```text
not fasting → STATE_UNAVAILABLE
```

Trend may still be available.

## Rule 3 — insufficient Trend history

```text
history < H → TREND_UNAVAILABLE
```

## Rule 4 — OOD

```text
OOD → UNCERTAIN / OUT_OF_DOMAIN
```

## Rule 5 — low confidence

Use thresholds determined from validation/calibration.

Do not hardcode arbitrary confidence cutoffs before analysis.

## Rule 6 — both valid

Display independently:

```text
LAST FASTING STATE
ELEVATED — 07:42

RECENT TREND
FALLING — 09:05
```

## Rule 7 — no arithmetic fusion

Never do:

```text
HIGH - FALLING = TARGET
```

or any equivalent numerical operation.

## Rule 8 — do not infer hidden path

```text
TARGET + RISING
```

does not imply that the person came from LOW.

## Rule 9 — timestamp semantics

An older fasting State must be labeled as a **last fasting anchor**, not silently presented as current state throughout the day.

---

# 43. Robustness Evaluation Algorithm

For every degradation level:

1. load frozen held-out native sample;
2. store original prediction/metric;
3. apply raw-signal degradation;
4. rerun the full preprocessing pipeline;
5. rerun frozen inference;
6. compare to the unchanged original biological label;
7. record metric delta;
8. record SQI rejection;
9. record OOD rejection.

Store:

```text
clean_metric
degraded_metric
absolute_delta
relative_delta
failure_rate
SQI_rejection_rate
OOD_rejection_rate
```

---

# 44. Candidate Engineering Envelope

After both robustness suites, summarize:

| Parameter | State | Trend | Candidate common implication |
|---|---|---|---|
| sampling rate | measured | measured | stricter requirement |
| wavelengths | ablation | compatible PPG channel | unresolved/derived |
| ADC/quantization | measured | measured | stricter requirement |
| SNR | measured | measured | stricter requirement |
| clipping | measured | measured | stricter requirement |
| motion | limited/native context | important | SQI/accelerometer likely |
| placement | fingertip native | wrist native | unresolved |
| population | broader cross-sectional | T1D only | unresolved |

The final column is an **engineering inference**, not a validation result.

---

# 45. Future Single-Sensor Concept

Candidate physical chain:

```text
LED wavelength(s)
      ↓
tissue
      ↓
photodiode
      ↓
TIA / analog front end
      ↓
filter / gain
      ↓
ADC
      ↓
MCU / buffer
      ↓
local processing / BLE
      ↓
PPG pipeline
      ↓
┌──────────────┬──────────────┐
│ State branch │ Trend branch │
└──────────────┴──────────────┘
      ↓
Decision Engine
```

Possible support hardware:

- accelerometer for motion/SQI;
- contact-quality detection;
- ambient-light shielding;
- stable LED current driver;
- battery/power management.

Do not freeze placement before the evidence justifies it.

---

# 46. Two Major Unresolved Bridges

## Sensor/domain bridge

```text
fingertip State
       ↓
future wrist/common sensor
```

Unvalidated.

## Population bridge

```text
T1D Trend
       ↓
prediabetes / healthy / T2D / general population
```

Unvalidated.

These must appear in limitations and final conclusions.

---

# 47. Execution Plan

## Phase 0 — Scientific freeze

Freeze:

- thesis;
- RQs;
- allowed/prohibited claims;
- State = fasting;
- Trend = recent observed direction;
- PPG-only core;
- no synthetic patients;
- no common-sensor validation claim.

## Phase 1 — Dataset audit

Deliver:

```text
reports/audits/hbppg_audit.md
reports/audits/physiocgm_audit.md
```

## Phase 2 — Freeze targets

State:

- class definitions;
- class counts;
- secondary regression scope.

Trend:

- H;
- tau;
- slope method;
- smoothing if used;
- alignment offset if used;
- window/stride;
- minimum valid history.

Never choose these from the final test set.

## Phase 3 — Preprocessing infrastructure

Implement and test:

- readers/adapters;
- timestamp checks;
- filters;
- normalization;
- SQI;
- segmentation;
- feature extraction.

## Phase 4 — State baselines

Run:

- majority;
- context-only logistic;
- PPG logistic.

## Phase 5 — State nonlinear models

Run:

- Random Forest;
- XGBoost;
- optional SVM;
- wavelength ablation;
- feature-family ablation;
- context ablation;
- calibration;
- OOD;
- final held-out evaluation.

## Phase 6 — PhysioCGM sanity check

Before the novel Trend task, try to reproduce a simple PPG-only glucose-related experiment from the PhysioCGM paper sufficiently to validate synchronization and preprocessing.

This is a pipeline sanity check, not the primary novelty.

## Phase 7 — Trend label generation

For each participant:

1. find usable CGM periods;
2. align PPG coverage;
3. compute recent glucose slope;
4. assign FALLING/STABLE/RISING;
5. inspect class balance;
6. remove invalid windows;
7. save a label manifest.

## Phase 8 — Trend baselines

Run:

- majority;
- always-STABLE;
- logistic regression.

## Phase 9 — Trend classical models

Run:

- Random Forest;
- XGBoost;
- optional SVM.

## Phase 10 — Optional sequence models

Only if classical evidence justifies it:

- TCN;
- GRU;
- LSTM.

## Phase 11 — Go/No-Go review

State must meaningfully beat baseline under participant-aware validation.

Trend must meaningfully beat majority/always-STABLE on chronological held-out data across multiple participants.

If 3-class Trend is unsupported, a simpler pre-declared target such as:

```text
CHANGING vs STABLE
```

may be evaluated, but do not repeatedly redefine targets after seeing final-test results.

## Phase 12 — Synthetic State robustness

Native held-out Hb-PPG only.

## Phase 13 — Synthetic Trend robustness

Native held-out PhysioCGM PPG only.

## Phase 14 — Engineering envelope

Compare robustness results and wavelength requirements.

## Phase 15 — Decision Engine

Implement all gates and timestamp semantics.

## Phase 16 — Integration demo

Demonstrate adapters → inference → Decision Engine → output.

Do not label it physical validation.

---

# 48. Hyperparameter Search Policy

Prefer modest search spaces.

Use:

- grid search for small spaces;
- randomized search for larger spaces;
- Optuna only if experiment tracking is disciplined.

All tuning occurs on training/validation only.

No test-set optimization.

---

# 49. Leakage Checklist

## State

- no participant appears in train and test;
- preprocessing fits on train only;
- imputation fits on train only;
- feature selection fits on train only;
- calibration fits on validation only;
- OOD fits on train only;
- no target-derived feature enters X.

## Trend

- chronological split;
- no overlapping PPG history across split boundaries;
- embargo ≥ H;
- CGM used only for labels;
- no future glucose leaks into features;
- no final-test tuning of H/tau/filter/alignment;
- no synthetic metadata used as biological evidence.

---

# 50. Statistical Reliability

## State

Bootstrap at participant level, not at window level.

## Trend

Report per-participant results first.

Use participant-level summaries and, if needed, temporal block bootstrap to respect autocorrelation.

Report:

- median;
- mean;
- IQR;
- worst/best participant;
- pooled metrics only as secondary context.

---

# 51. Model Selection Principle

Do not ask:

```text
Which model has the highest accuracy?
```

Ask:

```text
Which model gives the strongest reproducible evidence
under the correct validation structure?
```

Prefer simpler models when performance is comparable and calibration/robustness/interpretability are better.

---

# 52. Interpretation Tools

For tree models:

- permutation importance;
- SHAP only after leakage controls and model stability.

For linear models:

- standardized coefficients.

For wavelength relevance:

- explicit ablation is preferred over generic feature importance.

Never turn feature importance into biological causality.

---

# 53. Optional Multimodal Experiments

Core model remains PPG-only.

Secondary exploratory comparison may test:

```text
PPG only
vs
PPG + accelerometer/SQI
vs
multimodal exploratory model
```

Do not use multimodal success as evidence that PPG alone works.

---

# 54. Ideal Future Dataset

The current dual-expert plan exists because no single ideal dataset is currently used.

A dream validation dataset would contain:

```text
many diverse participants
×
many days/weeks
×
one standardized sensor
×
one standardized placement
×
multiple useful wavelengths
×
continuous glucose reference
×
periodic stronger reference checks
×
healthy
×
prediabetes
×
T1D
×
T2D
×
meals
×
exercise
×
sleep
×
motion
```

That dataset could directly test:

```text
one PPG history
      ↓
current state + recent trend
```

in one acquisition domain.

The current project cannot claim this.

---

# 55. Stop/Pivot Rules

## State

Downgrade or stop the State claim if:

- participant-aware performance is near baseline;
- performance disappears after context control;
- one class has inadequate support;
- wavelength effects are unstable;
- negative controls remain strong.

## Trend

Downgrade or pivot if:

- performance is near always-STABLE;
- only one or two participants work;
- time-shift control remains strong;
- opposite-direction errors are excessive;
- the intended claim exceeds the population evidence.

## Robustness

Be cautious if:

- small degradation causes total collapse;
- usable coverage after SQI rejection becomes negligible.

Negative results are valid research outcomes.

---

# 56. Required Outputs

## Dataset artifacts

- manifests;
- audit reports;
- exclusion logs;
- frozen split manifests.

## State artifacts

- baseline report;
- model comparison;
- wavelength ablation;
- context ablation;
- calibration;
- OOD analysis;
- held-out metrics;
- error analysis.

## Trend artifacts

- timeline audit;
- trend-label report;
- baselines;
- per-participant evaluation;
- optional LOSO;
- calibration;
- opposite-direction errors;
- time-shift negative control.

## Robustness artifacts

- State degradation curves;
- Trend degradation curves;
- SQI/OOD rejection analysis;
- engineering envelope.

## Integration artifacts

- Decision Engine unit tests;
- example schemas;
- integration logs;
- architecture diagram.

---

# 57. Suggested Config — State

```yaml
dataset:
  name: hbppg
  version: v6

task:
  name: fasting_state
  type: classification

input:
  wavelengths_nm: [660, 730, 850, 940]
  core_predictor: ppg_only

preprocessing:
  filter:
    enabled: true
    band_hz: [0.5, 8.0]
  normalization_candidates:
    - robust
    - zscore
    - acdc
  sqi:
    enabled: true

features:
  morphology: true
  timing: true
  spectral: true
  statistics: true
  cross_wavelength: true

split:
  type: participant_aware
  final_test_fraction: 0.20
  inner_cv: stratified_group_if_possible

models:
  - logistic_regression
  - random_forest
  - xgboost
  - svm_optional

evaluation:
  primary_metric: macro_f1
  calibration: true
  bootstrap_unit: participant

labels:
  thresholds: TBD_AFTER_AUDIT
```

---

# 58. Suggested Config — Trend

```yaml
dataset:
  name: physiocgm

task:
  name: recent_trend
  classes: [FALLING, STABLE, RISING]

input:
  core_predictor: ppg_only
  native_ppg_rate_hz: 64

windowing:
  short_window_sec: 30
  history_candidates_min: [15, 30, 60]
  stride: TBD

label_generation:
  source: cgm
  cgm_interval_min: 5
  slope_method:
    primary: ols
    sensitivity: [endpoint_delta, theil_sen]
  tau: TBD_ON_TRAIN_VALIDATION
  smoothing: TBD_ON_TRAIN_VALIDATION
  alignment_offset_min: TBD_ON_TRAIN_VALIDATION

split:
  primary: within_person_chronological
  train_fraction: 0.65
  validation_fraction: 0.15
  test_fraction: 0.20
  embargo: at_least_history_window

models:
  baselines: [majority, always_stable, logistic_regression]
  primary: [random_forest, xgboost]
  optional_sequence: [tcn, gru, lstm]

evaluation:
  primary_metric: macro_f1
  per_subject: true
  opposite_direction_error: true
  loso_secondary: true
```

---

# 59. Agent Behavioral Rules

The coding/research agent must:

1. preserve the distinction between native validation, synthetic robustness, and integration demonstration;
2. never silently random-split participant or temporal data;
3. never use the final test set to choose thresholds or hyperparameters;
4. never fabricate synthetic patients;
5. never treat metadata edits as biological evidence;
6. never claim a common physical sensor has been validated;
7. expose domain/population limitations in generated reports;
8. prefer reproducible scripts over notebook-only logic;
9. unit-test split integrity and label generation;
10. stop and surface uncertainty when the real dataset contradicts assumptions in this file;
11. version any change to a frozen scientific assumption.

---

# 60. Primary Source Library

## Hb-PPG

- `https://www.nature.com/articles/s41597-026-06945-6`
- `https://doi.org/10.1038/s41597-026-06945-6`
- `https://doi.org/10.6084/m9.figshare.22256143.v6`

## PhysioCGM

- `https://www.nature.com/articles/s41597-025-06090-6`
- `https://doi.org/10.1038/s41597-025-06090-6`
- `https://github.com/PSI-TAMU/PhysioCGM`

## Methodological warning

*Reassessing the Feasibility of PPG-Based Non-Invasive Blood Glucose Level Estimation*  
Preprint: `https://arxiv.org/abs/2608.01820`

Treat the arXiv source as a **preprint**, not peer-reviewed consensus.

---

# 61. One-Sentence Definition

> **GlycoBand is a PPG feasibility research framework that separately evaluates fasting glycemic State and recent glucose Trend using the datasets best suited to each task, rigorously tests leakage and sensor robustness, preserves uncertainty through a deterministic Decision Engine, and derives—rather than assumes—the requirements of a future single-sensor wearable.**

---

# 62. Final Mental Model

```text
DO NOT START WITH:
“How do I build a glucose bracelet?”

START WITH:
“Does each PPG dataset support the exact information claim assigned to it?”
        ↓
“Does that claim survive correct validation?”
        ↓
“How robust is it to realistic signal degradation?”
        ↓
“What engineering requirements follow?”
        ↓
“Can State and Trend be composed without inventing information?”
        ↓
“Only then: what might a future common sensor require?”
```

The product architecture must be derived from evidence rather than forcing the evidence to justify a predetermined device.
