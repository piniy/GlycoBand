# GlycoBand Scientific Decision Register

## Purpose

Track only scientific decisions that can materially change experiment validity or claim interpretation.

This file is descriptive, not a task queue. `PENDING` does not authorize the agent to complete a
decision automatically.

## Decisions

| ID | Decision | Status | Current value | Evidence required | Blocks |
|---|---|---|---|---|---|
| SCI-STATE-LABEL | State label formulation | `FROZEN` | `state-label-v1`: binary 5.6 mmol/L boundary | `configs/state/label-v1.yaml`; audit support; exploratory decision record | Registered State modeling; confirmatory/final State evaluation |
| SCI-TREND-LABEL | Trend label protocol | `FROZEN` | `trend-label-v1`: H30, median3, OLS, tau0.5 mg/dL/min, >=80% CGM support, continuous BVP history | `configs/trend/label-v1.yaml`; BIG IDEAs candidate and endpoint-stability evidence | Registered Trend modeling; confirmatory/final Trend evaluation |
| SCI-STATE-SPLIT | State participant split | `PENDING` | — | Approved State label + participant-level class support | Confirmatory/final State evaluation |
| SCI-TREND-SPLIT | Trend chronological split | `FROZEN` | `trend-split-v1`: within-person chronological 60/20/20 with 30-minute embargo | `data/manifests/trend_split-v1.json`; split validator and raw-history audit | Confirmatory/final Trend evaluation |
| SCI-FINAL-TEST | Final-test access | `SEALED` | — | Frozen label, split, preprocessing, features, model, hyperparameters, calibration/OOD, success criteria | Final evaluation |
| CLAIM-CEILING | Maximum defensible claim | `FEASIBILITY_ONLY` | Feasibility research only | Native held-out evidence + leakage/negative controls + uncertainty + domain limits | Stronger claims |

## Frozen decision record

```text
ID: SCI-STATE-LABEL
Version: state-label-v1
Value: Candidate A, NORMAL_RANGE < 5.6 mmol/L; ELEVATED_FASTING_RANGE >= 5.6 mmol/L
Evidence: Hb-PPG audit support (171/46 full eligible participants) plus state_exploratory-v1
Date: 2026-08-17
```

This freezes label meaning only. It does not freeze the State model protocol, registered split, or
claim that PPG can infer State. Current scientific status: `incremental PPG learnability not
supported on current representation`.

## Trend frozen record

ID: SCI-TREND-LABEL
Version: trend-label-v1
Value: H30 history, median3 smoothing, OLS slope, tau0.5 mg/dL/min, >=80% CGM support, continuous BVP history
Evidence: BIG IDEAs audit, trend formulation shortlist, exact endpoint stability probe, Gate D approval
Date: 2026-08-25

ID: SCI-TREND-SPLIT
Version: trend-split-v1
Value: Within-person chronological 60% train, 20% validation, 20% sealed test with 30-minute embargo
Evidence: data/manifests/trend_split-v1.json; raw-history separation validator
Date: 2026-08-25

Trend is now frozen for registered development only. This does not establish BVP learnability,
device validity, clinical utility, or permission to open final-test results.

## Exploratory status

While a decision is `PENDING`, bounded development-only exploratory probes are permitted when they
preserve the sealed final test. They do not constitute registered evidence and cannot automatically
freeze the decision.

The `Blocks` column refers to registered or confirmatory/final evidence; it does not block a safe
development-only probe.

## Invariants

### State split

A participant may appear in only one of train, validation, or test.

### Trend split

No raw history may cross a split boundary. Embargo must be at least the selected history window.

### Final test

Final-test results must not be used to select labels, thresholds, preprocessing, features, models,
calibration, OOD policy, or claim wording.

## Approval rule

Only the project lead may change a scientific decision from `PENDING` to `FROZEN`.
