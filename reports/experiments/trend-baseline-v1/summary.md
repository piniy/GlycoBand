# Trend baseline development v1

Status: registered development; validation-only result; final test sealed.

## Contract

- Dataset: big_ideas v1.1.3
- Label protocol: trend-label-v1
- Split manifest: trend-split-v1
- Train rows: 16652
- Validation rows: 5386
- Numeric BVP feature count: 50
- Decision: not_supported_for_classical_followup
- Final-test access: false

## Validation metrics

| Model | Macro-F1 | Balanced accuracy |
|---|---:|---:|
| majority | 0.2869 | 0.3333 |
| always_stable | 0.2869 | 0.3333 |
| logistic_history | 0.2889 | 0.3343 |
| logistic_current_window | 0.2869 | 0.3333 |
| logistic_shifted_control | 0.2869 | 0.3333 |

## Finding

The predeclared decision is **not_supported_for_classical_followup**. The aligned H30 history model reached Macro-F1 0.2889; the current-window and shifted-control variants remained at the constant baseline in this validation run.
Directional recall was FALLING=0.0031 and RISING=0.0000.

Paired participant-bootstrap deltas: {'history_minus_best_constant': {'mean_delta': 0.0012877134824085222, 'ci_lower': -5.553135888501895e-05, 'ci_upper': 0.003945409127055224}, 'history_minus_shifted_control': {'mean_delta': 0.0012877134824085222, 'ci_lower': -8.226867982965777e-05, 'ci_upper': 0.003945409127055224}, 'history_minus_current_window': {'mean_delta': 0.0012877134824085222, 'ci_lower': -8.226867982965777e-05, 'ci_upper': 0.003945409127055224}}

## What this does not prove

No final-test performance was accessed. This result does not establish general-population validity, direct glucose measurement, clinical utility, or physical-device validity.
