# GlycoBand — Project Context

## Project identity

GlycoBand is a computational biomedical research project for Healthynovation NEST UI 2026 under **Diagnostic Intelligence**.

Main question:

> What glucose-related information, if any, can be recovered from PPG under the domains represented by available public datasets?

This is not currently a clinically validated wearable, glucometer, CGM replacement, diabetes diagnostic system, or treatment-decision system.

## Scientific principle

PPG does not directly measure glucose molecules. The project tests whether physiological/hemodynamic patterns in PPG/BVP contain predictive information associated with glycemic condition.

Use:

```text
data -> evidence -> claim -> future engineering concept
```

Never force data to support a predetermined wearable narrative.

## Model 1 — Fasting State Expert

- Dataset: Hb-PPG.
- Domain: reflection fingertip PPG.
- Channels: 660 / 730 / 850 / 940 nm.
- Reference: fasting venous blood glucose.
- Task: cross-person fasting glycemic-state classification.
- Primary validation: participant-aware / unseen participants.

Mental model: **Anchor** — where is standardized fasting glycemic state?

## Model 2 — Free-Living Dynamic Expert

- Dataset: BIG IDEAs v1.1.3.
- Domain: Empatica E4 wrist BVP/PPG.
- Available optical input: one native BVP stream, ~64 Hz.
- Reference: Dexcom G6 interstitial CGM, ~5-minute spacing.
- Primary task: Recent Trend.
- Conceptual classes: `FALLING / STABLE / RISING`.
- Primary validation: within-person chronological with temporal separation.

Mental model: **Compass** — which direction has glucose moved recently?

## Optional Model 2B

Possible personalized free-living state-like output such as `PersLow / PersNorm / PersHigh`.

It is secondary and is **not the same target** as Model 1 fasting State.

## Dataset separation

Hb-PPG and BIG IDEAs differ in sensor, placement, optical channels, reference modality, acquisition protocol, population, and temporal structure.

Therefore:

- do not concatenate them as one training table;
- do not imply they jointly validate one physical sensor;
- do not numerically fuse their outputs into glucose mg/dL.

## PhysioCGM status

PhysioCGM is out of current core training/validation/synthetic-testing scope. It may be used only as literature or methodological context unless explicitly reopened.

## Exploration vs final evidence

GlycoBand distinguishes three levels:

```text
AUDIT
-> descriptive evidence

EXPLORATORY PROBE
-> development-only experiment used to reduce uncertainty

REGISTERED EXPERIMENT
-> frozen-contract evidence used for scientific conclusions
```

A pending scientific decision blocks **registered/final evidence**, not all experimentation.

Exploratory probes may be used before freeze when they are the cheapest valid way to learn, provided they do not access the sealed final test and are not presented as final evidence.

## State-category clarification

Clinical/conceptual State categories must be scientifically defensible and supported by enough independent participants.

A clinically meaningful rare category can still be statistically unevaluable for ML.

Correct sequence:

```text
raw-data audit
-> candidate scientifically meaningful formulations
-> participant/class-support review
-> if uncertainty remains: development-only exploratory probe
-> project-lead decision
-> freeze research label definition
-> registered model development
-> final held-out test
```

An exploratory probe may compare simple learnability of plausible formulations, but model score alone must not define what glucose categories mean.

Forbidden:

```text
final test looks bad -> move cutoff -> retest
```

## Trend-category clarification

The vocabulary `FALLING / STABLE / RISING` may be fixed conceptually while the generation protocol remains open.

Candidate decisions include:

- history window H;
- slope estimator;
- smoothing;
- threshold tau;
- minimum CGM support;
- alignment/gap policy.

These may be studied on development data with candidate-label audits and cheap exploratory probes.

Freeze them before registered/final evaluation.

## CGM role in Trend

Research label generation:

```text
CGM history ending at t -> true Trend label
```

Inference:

```text
BVP history ending at t -> predicted Trend
```

CGM is not a core inference feature.

## Core predictor policy

### Model 1

Core predictor: PPG-derived information only.

Age/sex/BMI may be used only as explicitly declared context-only comparators or ablations. Do not silently use laboratory glucose, Hb, SBP, or DBP as predictor inputs.

### Model 2

Core predictor: BVP/PPG temporal history only.

Other BIG IDEAs modalities may support SQI/artifact/confounding analysis or explicitly declared multimodal comparisons, but must not silently enter the core model.

## Claim boundaries

Potentially defensible after proper evidence:

- PPG contained predictive information for fasting glycemic-state classification within the evaluated Hb-PPG cohort.
- Longitudinal BVP contained predictive information for recent CGM-derived glucose direction within the evaluated BIG IDEAs cohort.
- Controlled degradation suggested candidate sensing requirements for future validation.

Do not claim:

- GlycoBand directly measures blood glucose;
- GlycoBand replaces glucometer/CGM;
- GlycoBand diagnoses diabetes;
- GlycoBand is clinically validated;
- Model 1 estimates arbitrary-time current glucose;
- BIG IDEAs proves general-population performance;
- synthetic robustness validates a physical wearable.

## Decision Engine

Decision Engine is deterministic, not a learned third model.

Example:

```text
Last fasting state: ELEVATED (07:30)
Recent trend: FALLING (14:05)
```

Never infer `ELEVATED + FALLING = NORMAL` or a new mg/dL value.

Decision Engine handles protocol validity, SQI, OOD, confidence, timestamps, `UNAVAILABLE`, `NO_ESTIMATE`, and `UNCERTAIN`.

## Research philosophy

A negative result is valid. High performance is not credible until leakage and negative controls are checked.

Be **loose about reversible exploration and strict about evidence used for claims**.
