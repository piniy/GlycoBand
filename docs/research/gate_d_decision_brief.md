# Gate D Decision Brief

## What this decision does

Gate D locks the meaning of each answer and the rules for separating development data from final-test data. Once approved, model results may not be used to move these boundaries.

## Current decision state

The State label component is frozen as Candidate A only. The State registered split and model
protocol are not frozen, Trend remains a leading hypothesis, and final-test performance remains
unavailable. Bounded development-only probes may be used for any still-open decision while the
reserve remains sealed.

### State: fasting range, not diagnosis (label frozen; split/model not frozen)

- Use only the 217 participants with a numeric fasting-glucose reference; exclude the 35 missing references.
- Primary label: `NORMAL_RANGE` below 5.6 mmol/L and `ELEVATED_FASTING_RANGE` at or above 5.6 mmol/L, following the audited ADA candidate boundary.
- Audited support: 171 normal-range and 46 elevated-range participants.
- Do not create a low-glucose class: only one participant is below 3.9 mmol/L.
- Keep the three-range ADA result (171 / 32 / 14) as a secondary descriptive analysis, not the primary predictive task.
- Split once by participant, approximately 70% train / 15% validation / 15% sealed test, stratified by the binary label. No participant may occur in more than one split.

Why: the binary formulation preserves a clinically sourced fasting-range boundary while avoiding a 14-person primary class. It is a research category and must not be presented as a diabetes diagnosis.

### Trend: recent direction from past CGM only

- Vocabulary: `FALLING / STABLE / RISING`.
- Candidate primary protocol: 30-minute history, median-of-three CGM smoothing, ordinary least-squares slope, and a 0.5 mg/dL/min direction threshold.
- Audited full-data support: 3,460 falling, 21,086 stable, and 3,367 rising endpoints; every participant supports all three classes.
- Require at least 80% valid CGM support, no future CGM point, continuous BVP history, and the audited gap policies.
- Split each participant chronologically: first 60% train, next 20% validation, final 20% sealed test. Put an embargo of at least 30 minutes at each boundary so no raw history crosses it.
- Use BVP history only at inference. CGM constructs the research label and is never a predictor input.

Why: 30 minutes captures direction beyond a single instant, median smoothing limits isolated CGM noise, OLS is simple and auditable, and the 0.5 threshold retains substantially more minority-class evidence than 1.0. This is a feasibility label, not a device trend-arrow or treatment rule.

## Trade-offs the project lead must accept

- State: combining prediabetes-range and diabetes-range references improves evaluability but gives up a three-level primary claim.
- Trend: the recommended threshold improves class support but may label small changes as directional; threshold sensitivity must remain visible in validation reporting.
- Both datasets are small in independent-human count: 217 State participants and 16 Trend participants. Millions of signal rows do not change that.
- The final test stays sealed until preprocessing, features, model family, hyperparameters, calibration, OOD policy, and success criteria are frozen.

## Approval choices

1. `APPROVE RECOMMENDED GATE D PACKAGE` — create versioned label configs and split manifests exactly from this package.
2. `REVISE` — name the boundary or policy to change before anything is frozen.
3. `NO_GO` — stop one or both predictive tasks while retaining the audit artifacts.

Approval is intentionally human for the remaining split and Trend decisions. State label meaning is
already recorded as `SCI-STATE-LABEL = FROZEN`; registered State modeling and final evaluation may
not begin until the State split and model protocol are separately approved. A safe development-only
probe may proceed under the project rules above.
