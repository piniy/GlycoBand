# Trend signal conditioning probe v1

Status: exploratory development-only evidence; final test sealed.

Selected conditioning candidate by train-only chronological resampling: **bp_0p5_8_zscore__report_only**.
Validation metrics are ordinary unweighted metrics; soft SQI weights affect training only.

Decision: **NOT_SUPPORTED_BY_CONDITIONING**. The selected candidate reached Macro-F1 0.2879 versus the raw anchor 0.2889; hard SQI exclusion reached 0.2911 but retained 91.8% of validation rows and did not recover RISING recall. No Phase 2 physiological-feature expansion is justified by this gate. The strongest absolute pooled conditioned-feature/slope correlation was 0.0400, without a predeclared coherent-family criterion.

Final-test performance accessed: NO
