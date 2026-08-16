# GlycoBand — Project Context

## Project identity

GlycoBand is a computational biomedical research project for Healthynovation NEST UI 2026 under **Diagnostic Intelligence**.

Main question:

> What glucose-related information, if any, can be recovered from PPG under the domains represented by available public datasets?

This project is not currently a clinically validated wearable, glucometer, CGM replacement, diabetes diagnostic system, or treatment-decision system.

## Scientific principle

PPG does not directly measure glucose molecules.

The project tests whether physiological/hemodynamic information in PPG/BVP contains reproducible predictive information associated with glycemic condition.

Use:

```text
data -> evidence -> claim -> future engineering concept
```

Do not force data to support a predetermined wearable narrative.

## Model 1 — Fasting State Expert

- Dataset: Hb-PPG.
- Domain: reflection fingertip PPG.
- Channels: 660 / 730 / 850 / 940 nm.
- Reference: fasting venous blood glucose.
- Task: cross-person fasting glycemic-state classification.
- Primary validation: participant-aware / unseen participants.

Mental model: **Anchor** — what is the standardized fasting glycemic state?

## Model 2 — Free-Living Dynamic Expert

- Dataset: BIG IDEAs v1.1.3.
- Domain: Empatica E4 wrist BVP/PPG.
- Optical input: one native BVP stream, ~64 Hz.
- Reference: Dexcom G6 interstitial CGM.
- Primary task: Recent Trend.
- Conceptual classes: `FALLING / STABLE / RISING`.
- Primary validation: within-person chronological with temporal separation.

Mental model: **Compass** — which direction has glucose moved recently?

## Optional Model 2B

Possible personalized free-living state-like output such as `PersLow / PersNorm / PersHigh`.

It is secondary and is not the same target as Model 1 fasting State.

## Dataset separation

Hb-PPG and BIG IDEAs differ in sensor, placement, optical channels, reference modality, acquisition protocol, population, and temporal structure.

Therefore:

- do not concatenate them as one training table;
- do not imply they jointly validate one physical sensor;
- do not numerically fuse their outputs into glucose mg/dL.

## PhysioCGM status

PhysioCGM is outside current core training, validation, and synthetic-testing scope unless explicitly reopened.

It may be used as literature or methodological context.

## State-category rule

Clinical/conceptual State categories may be defined before final testing if boundaries are defensible.

However, the raw-data audit must establish whether each category has enough participant support to be evaluated reliably.

A clinically valid rare category can still be statistically unevaluable.

Correct:

```text
raw-data audit
-> candidate clinically meaningful categories
-> support review
-> freeze label definition
-> train / validation
-> final held-out test
```

Forbidden:

```text
final test looks bad -> move cutoff -> retest
```

Operational output policy may change after evaluation without redefining ground truth.

## Trend-category rule

The vocabulary `FALLING / STABLE / RISING` may be fixed conceptually.

The exact label-generation protocol must be frozen before final testing:

- history window H;
- slope estimator;
- smoothing;
- threshold tau;
- minimum CGM support;
- alignment/gap policy.

Use audit + train/validation only.

## CGM role in Trend

Ground-truth generation:

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

Age/sex/BMI may be used only as explicitly declared comparators or ablations.

Do not silently use laboratory glucose, Hb, SBP, or DBP as predictor inputs.

### Model 2

Core predictor: BVP/PPG temporal history only.

Other BIG IDEAs modalities may support SQI, artifact/confounding analysis, or explicitly declared multimodal comparisons, but must not silently enter the core model.

## Claim boundaries

Potentially defensible after proper evidence:

- PPG contained predictive information for fasting glycemic-state classification within the evaluated Hb-PPG cohort.
- Longitudinal BVP contained predictive information for recent CGM-derived glucose direction within the evaluated BIG IDEAs cohort.
- Controlled degradation suggested candidate sensing requirements for future validation.

Do not claim:

- GlycoBand directly measures blood glucose.
- GlycoBand replaces glucometer/CGM.
- GlycoBand diagnoses diabetes.
- GlycoBand is clinically validated.
- Model 1 estimates arbitrary-time current glucose.
- BIG IDEAs proves general-population performance.
- synthetic robustness validates a physical wearable.

## Decision Engine

Decision Engine is deterministic, not a learned third model.

Example:

```text
Last fasting state: ELEVATED (07:30)
Recent trend: FALLING (14:05)
```

Never infer `ELEVATED + FALLING = NORMAL` or a new mg/dL value.

It may handle protocol validity, SQI, OOD, confidence, timestamps, `UNAVAILABLE`, `NO_ESTIMATE`, and `UNCERTAIN`.

## Research philosophy

A negative result is valid.

High performance is suspicious until leakage and negative controls are checked.

The goal is scientific resolution, not maximizing a competition metric.
