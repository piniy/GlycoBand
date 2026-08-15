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
- **Evidence considered:** None; the BIG IDEAs audit has not been completed.
- **Required evidence:** BIG IDEAs coverage audit and candidate-protocol results restricted to train/validation periods.
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
- **Evidence considered:** None; coverage, history, and gap evidence are incomplete.
- **Required evidence:** Per-participant coverage, selected history window, and gap statistics.
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
- **Evidence considered:** Hb-PPG raw schema and signal behavior are measured; BIG IDEAs acquisition and full audit remain incomplete.
- **Required evidence:** Completed BIG IDEAs file verification and audit, measured memory/timestamp/alignment behavior, audit failure modes, and frozen task contracts.
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
