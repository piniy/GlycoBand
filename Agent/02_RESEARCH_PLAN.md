# GlycoBand — Current Research Plan

## Objective

Evaluate whether PPG/BVP contains reproducible predictive information for:

1. standardized fasting glycemic State across participants;
2. recent glucose Trend in free-living longitudinal conditions.

Then test frozen-model robustness under controlled degradation of real held-out native signals and derive **candidate** future sensing constraints.

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

## Phase 0 — Scientific contracts

Before modeling, document:

- task,
- inference input,
- reference source,
- independent unit,
- target/label version,
- split strategy,
- primary metric,
- baseline,
- negative control,
- claim ceiling.

Major changes require human review.

## Phase 1A — Hb-PPG audit

Required outputs:

- participant count/schema verification,
- exact fasting glucose distribution,
- min/max/quantiles/ECDF,
- missingness,
- candidate clinical-category counts,
- participant support per class,
- signal duration/sampling consistency,
- four-channel availability,
- NaN/Inf,
- flatline/clipping,
- pulse detectability,
- representative signals,
- initial SQI summary.

### State target decision

Clinical/conceptual categories can be defined before testing, but the primary evaluable class set must be supported by the dataset audit.

Possible outcomes:

```text
3-class supported
2-class more defensible
rare class retained descriptively only
classification not adequately supported
```

Freeze the research label definition before final evaluation. Do not move thresholds because a model score is inconvenient.

## Phase 1B — BIG IDEAs audit

Per participant calculate:

- BVP start/end/duration,
- CGM start/end/duration,
- BVP-CGM overlap,
- CGM point count and gaps,
- BVP gaps,
- usable aligned hours,
- valid short windows,
- SQI distribution,
- glucose distribution,
- candidate Trend counts,
- class support by participant,
- temporal coverage by class.

Important: many windows do not create many independent humans.

## Trend label-generation study

Candidate ground truth:

```text
CGM history ending at t -> slope -> FALLING/STABLE/RISING
```

Candidate history H:

```text
15 / 30 / 60 min
```

Candidate slope methods:

- OLS primary candidate,
- endpoint delta sensitivity,
- Theil-Sen sensitivity.

Candidate smoothing:

- none,
- short median,
- short moving average.

Conceptual rule:

```text
s < -tau      -> FALLING
|s| <= tau    -> STABLE
s > +tau      -> RISING
```

Freeze H, tau, smoothing, alignment, gap policy, and minimum CGM support using audit + train/validation only.

## Model 1 pipeline

```text
raw 4-wave PPG
-> integrity/SQI
-> detrend/filter
-> normalize
-> pulse/segment handling
-> features
-> QC
-> classifier
```

Candidate features:

- morphology: amplitude, width, rise/decay, area, derivatives;
- timing: pulse interval, variability, RMSSD/CV;
- statistics: SD, IQR, skewness, kurtosis, optional entropy;
- spectral: dominant/band power, harmonics, optional MFCC-like;
- multiwave: ratios/differences and wavelength ablation.

### Model 1 validation

Primary: participant-aware unseen-participant evaluation.

Never allow one participant to appear in train and final test, even via separate windows.

Primary metric: Macro-F1.

Also report balanced accuracy, per-class P/R/F1, confusion matrix, support, and participant-bootstrap CI when feasible.

Required comparisons/controls:

- majority/prior-matched baseline,
- Logistic Regression,
- context-only baseline,
- PPG+context ablation,
- participant-level label permutation,
- subject-identity leakage probe,
- wavelength ablation.

Model order:

```text
Dummy -> Logistic -> Random Forest -> XGBoost -> optional SVM -> optional deep
```

## Model 2 pipeline

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

Temporal aggregation candidates:

- mean/median/SD/IQR,
- min/max,
- first-last delta,
- temporal slope,
- early-vs-late difference,
- valid-window fraction,
- good-SQI fraction.

Mandatory ablation:

```text
current-window-only vs history-H
```

### Model 2 validation

Primary: within-person chronological evaluation.

```text
PAST: TRAIN -> VALIDATION -> EMBARGO/GAP -> TEST :FUTURE
```

Forbidden: random shuffling of overlapping temporal windows or raw train/test interval overlap.

Secondary exploratory stress test: LOSO. Because N=16, do not frame LOSO as broad population validation.

Primary metric: Macro-F1.

Also report balanced accuracy, per-class F1, confusion matrix, participant-level results, and opposite-direction errors (`RISING->FALLING`, `FALLING->RISING`).

Required baselines/controls:

- majority,
- always-STABLE,
- Logistic Regression,
- large time-shift/circular-shift BVP relative to CGM.

## Optional Model 2B

Free-Living Excursion State is secondary and not required to produce Trend.

Candidate labels may be generated cheaply during audit, but dedicated tuning should wait until the primary Trend pipeline and class-support analysis are stable.

## SQI, calibration, OOD

SQI is primarily a gate. Candidate indicators: missingness, flatline, clipping, implausible pulse rate, low periodicity, template mismatch, poor SNR, motion contamination.

Calibration: validation-only Platt or isotonic; report Brier/ECE if probabilities matter.

OOD: training-feature distribution only; candidates include robust quantile/z bounds, Mahalanobis, optional Isolation Forest.

## Synthetic robustness

Run only after predictive model freeze.

Level A: real native held-out data = primary predictive evidence.

Level B: real held-out waveform + controlled degradation + original biological label = robustness evidence.

Level C: dummy synthetic fixtures = software testing only.

State degradation must preserve four real wavelength identities. Never copy one channel into four.

Trend degradation starts from real native BIG IDEAs BVP. Never fabricate wavelength-resolved channels.

Candidates include anti-aliased resampling, noise/SNR, dropout, clipping, drift, attenuation, jitter, and motion-like corruption.

## Go / No-Go

### State minimum

- beat majority baseline,
- participant-aware evaluation,
- credible per-class support,
- negative-control collapse,
- not explained only by participant identity/context,
- reasonably stable results.

### Trend minimum

- beat always-STABLE,
- chronological evaluation,
- meaningful RISING/FALLING metrics,
- report opposite-direction errors,
- time-shift control collapses,
- result not driven by one participant/epoch.

If these fail, report hypothesis not supported or insufficient evidence.

## Final-test discipline

Final test is opened only after labels, preprocessing, features, model family, hyperparameters, calibration, and OOD policies are frozen. If design changes after test inspection, document that the test is no longer pristine.
