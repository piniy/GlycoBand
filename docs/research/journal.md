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

## 2026-08-17 — Trend formulation shortlist

Question:
Which BIG IDEAs Recent Trend label formulations are worth a small development-only comparison before any chronological split or registered model?

Evidence / experiment:
The existing 81-protocol audit was reused without rereading raw BVP files: 16 participants, causal CGM-at-or-before-endpoint labels, continuous BVP coverage, and the configured CGM support/gap rules. We compared eligible endpoints, class fractions, all-participant class support, and participant-level class-composition shift versus H30 / 0.5 / median3 / OLS. Three diagnostic figures were saved.

Finding:
H30 / 0.5 / median3 / OLS retains 27,913 eligible endpoints with a 12.1% smaller directional class and all three classes supported in every participant. H15 gives 13.6% minority support but fewer eligible endpoints; H60 gives 8.2% and a larger composition shift. Tau 1.0 remains supported but falls to 4.0%; tau 1.5 is too sparse. Theil–Sen is compositionally close to OLS.

Interpretation:
The audit supports one primary formulation plus four targeted sensitivities, not an 81-protocol search. Stability is currently a participant-composition proxy, not endpoint-level agreement.

Decision / next direction:
Use the five-formulation development-only shortlist, with H30 / 0.5 / median3 / OLS as working primary. Before registration, quantify shared-endpoint label agreement; keep the chronological reserve unopened.

Evidence refs:
- `reports/experiments/trend_formulation-v0/summary.md`
- `reports/experiments/trend_formulation-v0/figures/`
- `reports/audits/bigideas_trend_candidates.csv`

## 2026-08-17 — Trend exact endpoint stability

Question:
Across the five shortlisted BIG IDEAs Recent Trend formulations, do the same participant-timestamp
endpoints remain eligible and receive the same direction label before any chronological split or
model selection?

Evidence / experiment:
The immutable BIG IDEAs v1.1.3 BVP files were re-streamed once for each of 16 participants to
reconstruct continuous-coverage eligibility. Only the five shortlisted causal CGM-history label
formulations were regenerated. Each candidate was compared with H30 / 0.5 / median3 / OLS on the
exact `(participant_id, timestamp)` key; no chronological split, final reserve, model, or final-test
data was created or accessed.

Finding:
The Theil-Sen sensitivity retained exactly the same 27,913 endpoints as the primary and agreed on
97.99% of labels (Cohen's kappa 0.950). The 1.0 mg/dL/min threshold also retained the same
endpoints but agreed on 84.44% (kappa 0.483), reflecting its intentionally more conservative
direction boundary. H15 shared 22,929 endpoints with the primary (Jaccard 0.811; agreement 83.52%;
kappa 0.610); H60 shared 27,010 (Jaccard 0.968; agreement 80.20%; kappa 0.435). For the Theil-Sen
sensitivity, disagreements concentrated much nearer the primary 0.5 mg/dL/min boundary than
agreements (median primary-margin 0.029 versus 0.364 mg/dL/min).

Interpretation:
The OLS estimator choice is highly stable under the retained robust-estimator sensitivity. Changing
history length or the direction threshold changes label meaning materially enough that these remain
visible sensitivities rather than interchangeable formulations. This evidence supports retaining
H30 / 0.5 / median3 / OLS as the working primary; it does not automatically freeze it or establish
predictive learnability.

Decision / next direction:
The endpoint-stability uncertainty is now reduced. Present the existing Trend Gate D package with
this evidence for project-lead approval or revision. Do not create the chronological split, version
the Trend label, start a model, or open a final test until that human decision.

Evidence refs:
- `reports/experiments/trend_endpoint_stability-v1/summary.md`
- `reports/experiments/trend_endpoint_stability-v1/pooled_pairwise.csv`
- `reports/experiments/trend_endpoint_stability-v1/per_participant_pairwise.csv`
- `reports/experiments/trend_endpoint_stability-v1/figures/`
