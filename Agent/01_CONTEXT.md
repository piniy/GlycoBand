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

- Dataset: BIG IDEAs.
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

## State-category clarification

Clinical/conceptual State categories may be specified before final testing if their boundaries come from a defensible clinical/research definition. Example vocabulary could be `LOW / NORMAL / ELEVATED`.

However, a **pre-model raw-data audit** must establish whether each category has enough participant support to be evaluated reliably.

A clinically valid rare category can still be statistically unevaluable for ML.

Correct sequence:

```text
raw-data audit
-> candidate clinically meaningful categories
-> class-support review
-> freeze research label definition
-> train / validation
-> final held-out test
-> performance audit
-> decide operational output policy
```

Forbidden:

```text
final test looks bad -> move cutoff -> retest
```

Performance audit may change the **operational output** (for example, `NORMAL / ELEVATED / UNCERTAIN`) without redefining ground truth after the fact.

## Trend-category clarification

The conceptual vocabulary `FALLING / STABLE / RISING` may be fixed from the start. But the exact label-generation protocol still requires pre-final-test selection of:

- history window H,
- slope estimator,
- smoothing,
- threshold tau,
- minimum CGM support,
- alignment/gap policy.

These are frozen using audit + train/validation only.

## CGM role in Trend

Research label generation:

```text
CGM history ending at t -> true Trend label
```

Inference:

```text
BVP history ending at t -> predicted Trend
```

CGM is not a core inference feature. A historical glucose-state prediction model is not required as an intermediate dependency for Trend.

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

Decision Engine handles protocol validity, SQI, OOD, confidence, timestamps, `UNAVAILABLE`, `NO_ESTIMATE`, and `UNCERTAIN`.

## Research philosophy

A negative result is valid. High performance is not credible until leakage and negative controls are checked. The project goal is scientific resolution, not maximizing a competition metric.
