# State Decisive Exploratory Experiment — Decision Record

Status: **development-only; Candidate A label FROZEN, State model and split remain PENDING**

## Question

Does native Hb-PPG add reproducible participant-level information beyond age/sex/BMI for Candidate A (the binary 5.6 mmol/L fasting boundary)?

## Protection and protocol

- Development participants: `173`; reserved participants: `44`.
- Reserved participants were not loaded for feature extraction, fitting, or scoring.
- Observation CV: `20` repeats × `5` stratified folds.
- Null control: `500` participant-level label permutations × `5` participant-safe folds.
- Every classifier is a fresh Pipeline per training fold: median imputation → standard scaling → Logistic Regression. Feature selection: none.
- Final-test performance accessed: **NO**.

## Repeated-CV pooled metrics

| Predictor set | Macro-F1 | Balanced accuracy | Macro PR-AUC |
|---|---:|---:|---:|
| PPG-only | 0.5350 | 0.5339 | 0.5759 |
| Context-only | 0.5398 | 0.5454 | 0.6720 |
| PPG + context | 0.5874 | 0.5817 | 0.6098 |

Fold-distribution summaries (mean ± SD; 2.5–97.5% fold quantiles):
- `ppg_only` Macro-F1 `0.5297 ± 0.0817` ([0.3946, 0.6964]); Macro PR-AUC `0.6215 ± 0.0633`.
- `context_only` Macro-F1 `0.5322 ± 0.0836` ([0.4167, 0.7062]); Macro PR-AUC `0.7137 ± 0.0751`.
- `ppg_plus_context` Macro-F1 `0.5814 ± 0.0834` ([0.4143, 0.7304]); Macro PR-AUC `0.6624 ± 0.0748`.

## Class-wise pooled metrics

| Predictor set / class | Sensitivity | Specificity | PR-AUC |
|---|---:|---:|---:|
| ppg_only / ELEVATED_FASTING_RANGE | 0.2068 | 0.8610 | 0.2766 |
| ppg_only / NORMAL_RANGE | 0.8610 | 0.2068 | 0.8753 |
| context_only / ELEVATED_FASTING_RANGE | 0.1324 | 0.9585 | 0.4139 |
| context_only / NORMAL_RANGE | 0.9585 | 0.1324 | 0.9302 |
| ppg_plus_context / ELEVATED_FASTING_RANGE | 0.2946 | 0.8688 | 0.3279 |
| ppg_plus_context / NORMAL_RANGE | 0.8688 | 0.2946 | 0.8918 |

## Paired context → PPG + context

- Macro-F1 Δ mean: `0.0492` (SD `0.1042`); positive in `69.0%` of paired folds.
- Balanced-accuracy Δ mean: `0.0365`; positive in `68.0%` of folds.
- Macro PR-AUC Δ mean: `-0.0513`; positive in `30.0%` of folds.

## Permutation control

- Null Macro-F1 Δ mean/SD: `0.0534` / `0.0418`.
- Empirical upper-tail proportion for observed Macro-F1 Δ: `0.5409` (exploratory, not a confirmatory p-value).
- Null PPG+context Macro-F1: `0.4946` ± `0.0424`.

## Finding

The binary Candidate A remains the only adequately supported State formulation. The decision-relevant question is whether its PPG contribution is stable beyond context; this record reports that result without using the reserved participants.

## Freeze recommendation

Exploratory decision: **the incremental PPG contribution is not supported**. The paired gain is no larger than the permutation null, and the combined model has lower macro PR-AUC than context-only. Candidate A remains a label-support candidate, not a learnability-supported State claim.

Do not register or freeze the modeling protocol automatically. Project-lead review must decide whether the observed paired gain, class-wise behavior, and permutation result are strong enough to freeze Candidate A and proceed to a registered State experiment. The claim ceiling remains feasibility-only until that registered experiment and one-time reserved-test evaluation are complete.
