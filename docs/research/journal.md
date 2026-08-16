# GlycoBand Research Journal

## 2026-08-17 — State label freeze, learnability stop

Question:
Can Hb-PPG support a defensible fasting State definition, and does native PPG add value beyond age/sex/BMI on the current representation?

Evidence / experiment:
Candidate A (binary 5.6 mmol/L boundary) was evaluated on 173 development participants using 20×5 repeated participant-safe CV, class-wise sensitivity/specificity/PR-AUC, paired context versus PPG+context deltas, and 500 participant-level label permutations. The 44-person outer reserve remained sealed. Imputation and scaling were fit inside each training fold; no feature selection was used.

Finding:
Candidate A is adequately supported as a research label. Incremental PPG learnability is not supported on the current representation: observed Macro-F1 Δ was 0.0492, while the permutation-null Δ was 0.0534 ± 0.0418; PPG+context had lower Macro PR-AUC than context-only.

Interpretation:
This is not evidence that State is impossible. It is evidence that the current global/simple statistical, spectral, pulse, and cross-wavelength features do not justify a robust PPG State claim.

Decision / next direction:
Freeze Candidate A as the label definition only. Do not freeze the model, create the registered split, or open the final reserve. No single biologically motivated representation hypothesis is currently strong enough to justify targeted feature fishing; park State development and move primary effort to Trend.

Evidence refs:
- `reports/probes/state_exploratory-v1/decision_record.md`
- `configs/state/label-v1.yaml`
- `data/manifests/state_test_reserve-v0.json`
