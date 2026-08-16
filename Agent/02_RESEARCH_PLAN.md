# GlycoBand — Current Research Plan

## Operating note

This document describes **research dependency order**, not an autonomous work queue.

An unfinished phase does not authorize Codex to execute it unless the current user task explicitly requires that work or a necessary prerequisite.

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

Does wrist BVP contain predictive information about personalized current glycemic excursion state?

Secondary only.

### RQ4 — Robustness

How does performance change under controlled degradation of real held-out native PPG/BVP?

### RQ5 — Engineering implication

What candidate sensing requirements can be inferred without claiming validation of a physical GlycoBand device?

## Research sequence

```text
verify relevant source/data contract
-> audit data
-> define and freeze target + split
-> baselines
-> classical models
-> leakage/negative controls
-> frozen held-out evaluation
-> synthetic robustness
-> engineering inference
```

Do not advance simply because the next phase exists.

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

### State target decision

Possible outcomes:

```text
3-class supported
2-class more defensible
rare class descriptive only
classification not adequately supported
```

Freeze the research label definition before final evaluation.

Do not move thresholds because a model score is inconvenient.

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

Candidate history H:

```text
15 / 30 / 60 min
```

Candidate slope methods:

- OLS primary;
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

Freeze H, tau, smoothing, alignment, gap policy, and minimum CGM support using audit + train/validation only.

## Model 1 — State

Pipeline:

```text
raw 4-wave PPG
-> integrity/SQI
-> detrend/filter
-> normalization candidate
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

Primary: participant-aware unseen-participant evaluation.

Never allow one participant into both train and final test, even through separate windows.

Primary metric: Macro-F1.

Also report:

- balanced accuracy;
- per-class precision/recall/F1;
- confusion matrix;
- support;
- participant-bootstrap CI when feasible.

Required controls/comparisons:

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

## Model 2 — Recent Trend

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

Candidate short window: ~30 s.

Temporal summaries may include:

- mean/median/SD/IQR;
- min/max;
- first-last delta;
- temporal slope;
- early-vs-late difference;
- valid-window fraction;
- good-SQI fraction.

Mandatory ablation:

```text
current-window-only vs history-H
```

### Validation

Primary: within-person chronological.

```text
PAST: TRAIN -> VALIDATION -> EMBARGO/GAP -> TEST :FUTURE
```

Forbidden:

- random shuffle of overlapping temporal windows;
- raw train/test interval overlap.

Secondary exploratory stress test: LOSO.

Because N=16, do not frame LOSO as broad population validation.

Primary metric: Macro-F1.

Also report:

- balanced accuracy;
- per-class F1;
- confusion matrix;
- participant-level results;
- opposite-direction errors.

Required baselines/controls:

- majority;
- always-STABLE;
- Logistic Regression;
- large time-shift/circular-shift BVP relative to CGM.

## Optional Model 2B

Secondary only.

Candidate labels may be generated cheaply during audit, but dedicated tuning waits until the primary Trend pipeline is stable.

## SQI, calibration, OOD

SQI is primarily a gate.

Candidate indicators:

- missingness;
- flatline;
- clipping;
- implausible pulse rate;
- low periodicity;
- template mismatch;
- poor SNR;
- motion contamination.

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

State degradation preserves four real wavelength identities.

Trend degradation starts from real native BIG IDEAs BVP.

Candidates:

- anti-aliased resampling;
- noise/SNR;
- dropout;
- clipping;
- drift;
- attenuation;
- jitter;
- motion-like corruption.

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

Open final test only after labels, preprocessing, features, model family, hyperparameters, calibration, and OOD policies are frozen.

If design changes after test inspection, document that the test is no longer pristine.
