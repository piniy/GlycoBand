# GlycoBand — Current Research Plan

## Operating note

This document describes research logic, not an autonomous task queue.

The goal is to remove important uncertainty as cheaply as possible without contaminating final evidence.

## Objective

Evaluate whether PPG/BVP contains reproducible predictive information for:

1. standardized fasting glycemic State across participants;
2. recent glucose Trend in free-living longitudinal conditions.

Then test frozen-model robustness under controlled degradation of real held-out native signals and derive candidate future sensing constraints.

## Research questions

### RQ1 — Fasting State

Does standardized fasting four-wavelength PPG contain predictive information for fasting glycemic state in unseen participants?

### RQ2 — Recent Trend

Does recent free-living wrist BVP history contain predictive information for recent CGM-derived glucose direction within an individual?

### RQ3 — Optional Free-Living Excursion State

Secondary only.

### RQ4 — Robustness

How does performance change under controlled degradation of real held-out native PPG/BVP?

### RQ5 — Engineering implication

What candidate sensing requirements can be inferred without claiming validation of a physical GlycoBand device?

## Evidence sequence

Use:

```text
verify source/data contract
-> audit data
-> establish sealed outer test reserve when needed
-> compare candidate scientific formulations on development data
-> cheap exploratory probe if it can resolve material uncertainty
-> human review + freeze target/split
-> registered baselines
-> classical models
-> leakage/negative controls
-> freeze full pipeline
-> open final test once
-> synthetic robustness
-> engineering inference
```

Do not require a freeze before **all** model use. Require a freeze before registered/final-evidence modeling.

## Exploratory probe rule

Run a probe only when:

1. the decision is material;
2. descriptive evidence is insufficient;
3. a cheap development-only experiment can discriminate between plausible alternatives;
4. the final test remains untouched.

Default probe stack:

```text
Dummy / majority
-> Logistic Regression
-> stop unless more complexity is necessary to answer the decision
```

Exploratory results are decision support, not final evidence.

A label/protocol may not be chosen solely because it maximizes validation score.

## Phase 1A — Hb-PPG audit

Required evidence:

- participant/schema verification;
- fasting glucose distribution;
- missingness;
- candidate category counts;
- participant support per class;
- signal duration/rate consistency;
- four-channel availability;
- NaN/Inf;
- flatline/clipping;
- pulse detectability;
- representative signals;
- initial SQI summary.

### State target study

Possible candidate outcomes include:

```text
3-class supported
2-class more defensible
rare class descriptive only
classification not adequately supported
continuous regression useful as exploratory comparison
```

Evaluate candidate formulations using:

- clinical/research defensibility;
- participant support;
- sample support;
- imbalance;
- threshold sensitivity;
- likely label noise;
- optionally, cheap development-only learnability.

If simple learnability evidence could materially change the decision, run a participant-grouped exploratory probe before requesting freeze.

Then present the evidence and recommendation to the project lead.

Do not move thresholds because a final-test score is inconvenient.

## Phase 1B — BIG IDEAs audit

Per participant calculate only what is needed to establish usable aligned data and candidate Trend support:

- BVP start/end/duration;
- CGM start/end/duration;
- BVP-CGM overlap;
- CGM gaps;
- BVP gaps;
- usable aligned hours;
- valid short windows;
- SQI distribution;
- glucose distribution;
- candidate Trend counts;
- support by participant;
- temporal coverage by class.

Many windows do not create many independent humans.

## Trend label study

Candidate ground truth:

```text
CGM history ending at t -> slope -> FALLING / STABLE / RISING
```

Candidate H:

```text
15 / 30 / 60 min
```

Candidate slope methods:

- OLS primary candidate;
- endpoint delta sensitivity;
- Theil-Sen sensitivity.

Candidate smoothing:

- none;
- short median;
- short moving average.

Conceptual threshold:

```text
s < -tau      -> FALLING
|s| <= tau    -> STABLE
s > +tau      -> RISING
```

Study candidate H/tau/smoothing/alignment/gap policies using development-only data.

Useful cheap evidence includes:

- number of valid endpoints retained;
- class balance;
- participant support;
- label stability under small parameter changes;
- simple Logistic Regression learnability;
- current-window-only vs history-H comparison when needed to select H.

Freeze the selected protocol only after this study is informative enough.

## Model 1 — State registered development

Starts after State target and registered split are frozen.

Pipeline:

```text
raw 4-wave PPG
-> integrity/SQI
-> detrend/filter
-> normalization
-> pulse/segment handling
-> features
-> classifier
```

Candidate feature families:

- morphology;
- timing/variability;
- statistics;
- spectral;
- cross-wavelength relations.

### Validation

Primary: participant-aware unseen-participant development validation and sealed final test.

Never allow one participant into both development and final test.

Primary metric: Macro-F1.

Required controls/comparisons for registered evidence:

- majority/prior baseline;
- Logistic Regression;
- context-only baseline;
- PPG + context ablation;
- participant-level label permutation;
- subject-identity leakage probe;
- wavelength ablation.

Model order:

```text
Dummy -> Logistic -> Random Forest -> XGBoost -> optional SVM -> optional deep
```

## Model 2 — Recent Trend registered development

Starts after Trend label protocol and registered split are frozen.

Pipeline:

```text
raw wrist BVP
-> timestamp integrity
-> short-window segmentation
-> SQI
-> filter/normalize
-> per-window features
-> temporal aggregation over H
-> Trend classifier
```

Primary validation: within-person chronological.

```text
PAST: TRAIN -> VALIDATION -> EMBARGO/GAP -> TEST :FUTURE
```

Forbidden:

- random shuffle of overlapping temporal windows;
- raw train/test interval overlap;
- future CGM in labels.

Required registered baselines/controls:

- majority;
- always-STABLE;
- Logistic Regression;
- large time-shift/circular-shift BVP relative to CGM;
- current-window-only vs history-H ablation.

## SQI, calibration, OOD

SQI is primarily a gate.

Calibration uses validation only if probabilities matter.

OOD uses training-feature distributions only.

## Synthetic robustness

Run only after predictive model freeze.

Evidence levels:

```text
A. real native held-out data
   -> predictive evidence

B. real held-out waveform + controlled degradation
   -> robustness evidence

C. dummy synthetic fixtures
   -> software testing only
```

Synthetic robustness does not validate a physical device.

## Go / No-Go

### State minimum

- beat majority baseline;
- participant-aware evaluation;
- credible class support;
- negative-control collapse;
- not explained only by participant identity/context;
- reasonably stable results.

### Trend minimum

- beat always-STABLE;
- chronological evaluation;
- meaningful RISING/FALLING metrics;
- opposite-direction errors reported;
- time-shift control collapses;
- not driven by one participant/epoch.

Failure is a valid result.

## Final-test discipline

Open final test only after labels, preprocessing, features, model family, hyperparameters, calibration, OOD policy, and success criteria are frozen.

If design changes after test inspection, the test is no longer pristine and this must be documented.
