# Hb-PPG State Exploratory Figures

These figures render the completed `state_exploratory-v1` development-only artifacts. They do not
open, score, or visualize the sealed 44-participant outer reserve.

- `fig01_cohort_and_label_support` shows the audited cohort, protected development/reserve split,
  and support for the frozen Candidate A research label.
- `fig02_repeated_cv_metric_distributions` shows the 100 participant-safe development-CV fold
  scores for PPG-only, context-only, and PPG-plus-context Logistic Regression pipelines.
- `fig03_paired_incremental_ppg_effect` shows the paired fold-level change from adding PPG to the
  age/sex/BMI comparator. Zero means no paired incremental change.
- `fig04_permutation_null_incremental_ppg` compares the observed mean Macro-F1 change against the
  500 participant-level label-permutation control. Its upper-tail proportion is exploratory and is
  not a confirmatory p-value.

Figures are exported only as 300 dpi PNG. Their appropriate claim ceiling is the one in
`../decision_record.md`: the current PPG representation did not support incremental State
learnability; this is not a clinical-validation or final-test result.
