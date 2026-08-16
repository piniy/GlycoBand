# State Exploratory Probe

Question: does Hb-PPG contain enough participant-level predictive information to justify freezing a State formulation?

Probe: Hb-PPG v6; one feature row per participant; deterministic outer reserve; participant-safe stratified development CV; Dummy and Logistic Regression; one participant-level label permutation control.

Reserve rule: `data/manifests/state_test_reserve-v0.json`; reserved participants were excluded from feature extraction, fitting, and scoring.

- Development participants: `173`
- Seed: `20260817`
- Final-test performance accessed: **NO**

## candidate_a_binary

Scientific rationale: binary 5.6 mmol/L boundary
Development support: `{'NORMAL_RANGE': 136, 'ELEVATED_FASTING_RANGE': 37}`
Provisional probe verdict: **VIABLE**

- ppg_only: Logistic Macro-F1 `0.5506493506493506`, balanced accuracy `0.5480922098569158`, fold Macro-F1 range `0.480-0.676`
- context_only: Logistic Macro-F1 `0.5018826135105205`, balanced accuracy `0.522158187599364`, fold Macro-F1 range `0.417-0.681`
- ppg_plus_context: Logistic Macro-F1 `0.6107884685815936`, balanced accuracy `0.6058227344992051`, fold Macro-F1 range `0.572-0.669`
- permutation control: Macro-F1 `0.4673645320197044`, balanced accuracy `0.48171701112877585`

Main weakness: exploratory development performance is not confirmatory evidence; support and clinical meaning still require project-lead review.

## candidate_b_ada_3class

Scientific rationale: ADA-inspired three-range formulation
Development support: `{'NORMAL_RANGE': 136, 'PREDIABETES_RANGE': 26, 'DIABETES_RANGE': 11}`
Provisional probe verdict: **WEAK**

- ppg_only: Logistic Macro-F1 `0.35144927536231885`, balanced accuracy `0.3489819004524887`, fold Macro-F1 range `0.282-0.464`
- context_only: Logistic Macro-F1 `0.35732948294829486`, balanced accuracy `0.3668929110105581`, fold Macro-F1 range `0.289-0.466`
- ppg_plus_context: Logistic Macro-F1 `0.3361111111111111`, balanced accuracy `0.333710407239819`, fold Macro-F1 range `0.276-0.471`

Main weakness: exploratory development performance is not confirmatory evidence; support and clinical meaning still require project-lead review.

## candidate_c_who_3class

Scientific rationale: WHO-inspired three-range formulation
Development support: `{'BELOW_IFG_THRESHOLD': 154, 'DIABETES_RANGE': 11, 'IFG_RANGE': 8}`
Provisional probe verdict: **WEAK**

- ppg_only: Logistic Macro-F1 `0.4206773618538324`, balanced accuracy `0.42803030303030304`, fold Macro-F1 range `0.295-0.468`
- context_only: Logistic Macro-F1 `0.31396534148827726`, balanced accuracy `0.3333333333333333`, fold Macro-F1 range `0.312-0.318`
- ppg_plus_context: Logistic Macro-F1 `0.35182616736014793`, balanced accuracy `0.3468614718614719`, fold Macro-F1 range `0.301-0.398`

Main weakness: exploratory development performance is not confirmatory evidence; support and clinical meaning still require project-lead review.

## Leading recommendation (not a freeze)

Candidate A (binary 5.6 mmol/L boundary) is the only formulation with comfortable development participant support (136/37 after the outer reserve; 171/46 in the full eligible audit) and a clinically documented interpretation. Candidate B and C retain minority classes of 11 and 8 development participants, respectively, so they are weak primary prediction candidates despite their exploratory scores.

The learnability finding is weak: PPG-only Logistic Regression is only slightly above the majority baseline for Candidate A and is essentially similar to context-only; the PPG-plus-context gain is not evidence that PPG alone recovers fasting State. The permutation control is chance-like and the continuous Ridge sanity check does not beat the dummy regressor.

Recommended State-v1 for project-lead review: Candidate A as the defensible formulation to freeze and test, with a deliberately low claim ceiling and no automatic approval. A registered experiment should proceed only after explicit project-lead freeze.

## Continuous sanity check

PPG-only Dummy/Ridge metrics: `{'dummy': {'mae_mmol_l': 0.6812218463480033, 'rmse_mmol_l': 1.1500524740213112, 'r2': -0.006147451990114794}, 'ridge': {'mae_mmol_l': 1.0789453216404268, 'rmse_mmol_l': 1.7786276918332689, 'r2': -1.4065584703094194}}`
This does not redefine the primary State task.

## Recommendation status

These provisional verdicts are decision support only. Do not freeze State-v1 automatically; the project lead must approve the formulation and registered split.
