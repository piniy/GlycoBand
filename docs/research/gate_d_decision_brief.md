# Gate D Decision Brief

## What this decision does

Gate D locks the meaning of each answer and the rules for separating development data from final-test data. Once approved, model results may not be used to move these boundaries.

## Current decision state

The State label component remains frozen as Candidate A, but State research is `PARKED` after its
development-only probe did not support incremental PPG learnability on the current representation.
No State registered split or model protocol is recommended. Trend is the current frontier, and
final-test performance remains unavailable. The State reserve remains sealed.

### State: fasting range, not diagnosis (label frozen; research parked)

- Use only the 217 participants with a numeric fasting-glucose reference; exclude the 35 missing references.
- Primary label: `NORMAL_RANGE` below 5.6 mmol/L and `ELEVATED_FASTING_RANGE` at or above 5.6 mmol/L, following the audited ADA candidate boundary.
- Audited support: 171 normal-range and 46 elevated-range participants.
- Do not create a low-glucose class: only one participant is below 3.9 mmol/L.
- Keep the three-range ADA result (171 / 32 / 14) as a secondary descriptive analysis, not the primary predictive task.

Why: the binary formulation preserves a clinically sourced fasting-range boundary while avoiding a 14-person primary class. It is a research category and must not be presented as a diabetes diagnosis. The exploratory result does not prove that PPG contains no State information; it means the current representation does not justify proceeding to a registered State split or model.

### Trend: recent direction from past CGM only

- Vocabulary: `FALLING / STABLE / RISING`.
- Candidate primary protocol: 30-minute history, median-of-three CGM smoothing, ordinary least-squares slope, and a 0.5 mg/dL/min direction threshold.
- Audited full-data support: 3,460 falling, 21,086 stable, and 3,367 rising endpoints; every participant supports all three classes.
- Require at least 80% valid CGM support, no future CGM point, continuous BVP history, and the audited gap policies.
- Split each participant chronologically: first 60% train, next 20% validation, final 20% sealed test. Put an embargo of at least 30 minutes at each boundary so no raw history crosses it.
- Use BVP history only at inference. CGM constructs the research label and is never a predictor input.

Why: 30 minutes captures direction beyond a single instant, median smoothing limits isolated CGM noise, OLS is simple and auditable, and the 0.5 threshold retains substantially more minority-class evidence than 1.0. This is a feasibility label, not a device trend-arrow or treatment rule.

## Active decision for the project lead

- Trend: the recommended threshold improves class support but may label small changes as directional; threshold sensitivity must remain visible in validation reporting.
- BIG IDEAs has only 16 independent participants. Millions of signal rows do not change that.
- The final test stays sealed until preprocessing, features, model family, hyperparameters, calibration, OOD policy, and success criteria are frozen.

## Approval choices

1. `APPROVE TREND GATE D PACKAGE` — create the versioned Trend label config and split manifest exactly from this package.
2. `REVISE` — name the boundary or policy to change before anything is frozen.
3. `NO_GO` — stop Trend while retaining the audit artifacts.

Approval is intentionally human for the remaining Trend decisions. State label meaning remains
recorded as `SCI-STATE-LABEL = FROZEN`, but State has no active split or model recommendation.
Registered State modeling and final evaluation may not begin unless the project lead explicitly
reopens State.

APPROVE TREND GATE D PACKAGE - RNA
