# GlycoBand Scientific Decision Register

## Rules

Every entry requires evidence, a reviewer, and a version before its status becomes `APPROVED`. Reversals create a new version and name the superseded decision. Final-test performance cannot justify changing an earlier scientific decision.

## SCI-STATE-LABEL-001

- **Version:** 0
- **Approval status:** `NOT_STARTED`
- **Approval date:** Not applicable before approval.
- **Decision:** No State formulation has been selected.
- **Evidence considered:** Hb-PPG v6 raw-data audit completed and independently accepted; no label review has opened.
- **Required evidence:** Project-lead review of the audited glucose distribution, candidate clinical definitions, participant support per class, and claim consequences.
- **Alternatives rejected:** None; decision review has not opened.
- **Reviewer:** Project lead.
- **Supersedes:** None.
- **Superseded by:** None.
- **Blocks:** State split freeze and State modeling.

## SCI-TREND-LABEL-001

- **Version:** 0
- **Approval status:** `NOT_STARTED`
- **Approval date:** Not applicable before approval.
- **Decision:** No Trend history, slope, threshold, smoothing, support, alignment, gap, or stride policy has been selected.
- **Evidence considered:** BIG IDEAs v1.1.3 integrity, coverage, anomaly, and 81-protocol sensitivity audit completed and independently accepted; no Trend protocol review has opened.
- **Required evidence:** Project-lead review of candidate history, threshold, smoothing, slope, alignment, gap, and chronological split policies before any version is approved.
- **Alternatives rejected:** None; decision review has not opened.
- **Reviewer:** Project lead.
- **Supersedes:** None.
- **Superseded by:** None.
- **Blocks:** Trend label freeze and Trend modeling.

## SCI-STATE-SPLIT-001

- **Version:** 0
- **Approval status:** `NOT_STARTED`
- **Approval date:** Not applicable before approval.
- **Decision:** No participant split has been frozen.
- **Evidence considered:** None; the State label decision and participant-support audit are incomplete.
- **Required evidence:** Approved State label definition and participant-level class support.
- **Alternatives rejected:** None; decision review has not opened.
- **Reviewer:** Project lead.
- **Supersedes:** None.
- **Superseded by:** None.
- **Invariant:** A participant appears in exactly one of train, validation, or test.

## SCI-TREND-SPLIT-001

- **Version:** 0
- **Approval status:** `NOT_STARTED`
- **Approval date:** Not applicable before approval.
- **Decision:** No chronological split has been frozen.
- **Evidence considered:** Per-participant coverage, gap, anomaly, and candidate-history support are audited; no split policy has been approved.
- **Required evidence:** Approved Trend label definition plus a chronological split proposal whose embargo is at least the selected history.
- **Alternatives rejected:** None; decision review has not opened.
- **Reviewer:** Project lead.
- **Supersedes:** None.
- **Superseded by:** None.
- **Invariant:** No raw history overlaps a split boundary; embargo is at least the selected history.

## SCI-FINAL-TEST-001

- **Version:** 0
- **Approval status:** `NOT_STARTED`
- **Approval date:** Not applicable before approval.
- **Decision:** Final-test access is not authorized.
- **Evidence considered:** Current project status and unresolved label, split, preprocessing, and model decisions.
- **Required evidence:** Frozen task config, label version, split version, preprocessing, features, model family, hyperparameters, calibration, OOD policy, and success criteria.
- **Alternatives rejected:** Opening the final test during development is rejected because it invalidates the held-out evaluation.
- **Reviewer:** Project lead.
- **Supersedes:** None.
- **Superseded by:** None.
- **Blocks:** Any final-test evaluation.

## ARCH-PIPELINE-001

- **Version:** 0
- **Approval status:** `NOT_STARTED`
- **Approval date:** Not applicable before approval.
- **Decision:** No implementation architecture has been approved beyond the repository scaffold.
- **Evidence considered:** Both raw datasets, schema, signal rates, file integrity, timestamp anomalies, alignment, and candidate support have been measured; task contracts remain unfrozen.
- **Required evidence:** Project-lead-approved State and Trend labels/splits, followed by a bounded architecture and experiment-readiness review.
- **Alternatives rejected:** Premature microservices, orchestration platforms, and deep-learning infrastructure are rejected without measured need.
- **Reviewer:** Project lead.
- **Supersedes:** None.
- **Superseded by:** None.

## CLAIM-CEILING-001

- **Version:** 0
- **Approval status:** `NOT_STARTED`
- **Approval date:** Not applicable before approval.
- **Decision:** Current claims remain limited to feasibility questions; no predictive result has been established.
- **Evidence considered:** Source-level dataset facts and the absence of project audit or experiment results.
- **Required evidence:** Native held-out evaluation, leakage controls, negative controls, support, uncertainty, and domain limitations.
- **Alternatives rejected:** Device validation, glucose measurement, diagnosis, and general-population claims are rejected at the current evidence level.
- **Reviewer:** Project lead.
- **Supersedes:** None.
- **Superseded by:** None.
