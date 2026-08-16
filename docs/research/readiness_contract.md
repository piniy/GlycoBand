# GlycoBand Research Readiness Contract

## Purpose

This is the single status page for preparation before architecture implementation or model experimentation. A gate passes only when its evidence exists and the required reviewer has accepted it.

## Status vocabulary

- `NOT_STARTED`: no qualifying evidence yet.
- `IN_PROGRESS`: evidence is being collected but the gate is not satisfied.
- `PASS`: every exit condition is satisfied.
- `DATA_REQUIRED`:bisa  required source data or metadata is unavailable.
- `NO_GO`: evidence shows the proposed task is not defensible.
- `SUPERSEDED`: a newer version replaces this decision or artifact.

## Gates

| Gate | Required outcome | Owner | Current status | Evidence | Current blocker | Approval |
|---|---|---|---:|---|---|---|
| A — Repository and environment | Committed Git baseline, clean evidence capture, locked environment restores, tests/lint/types pass | Repository maintainer | `PASS` | `reports/audits/environment_preflight.json` | None when the report records a commit, `dirty=false`, successful sync, and all checks passing | Automated checks |
| B — Source and storage | Exact sources, access, license, sizes, checksums, and storage budget verified | Data preparation owner | `PASS` | `configs/data_sources.yaml`; `data/manifests/source_manifest.json`; `docs/research/source_verification.md` | None; both authorized archives are locally complete | Project lead authorized required downloads on 2026-08-15 |
| C — Raw-data audits | Hb-PPG and BIG IDEAs audits complete with exclusions and support evidence | Audit owner | `PASS` | `reports/audits/hbppg_audit.md`; `reports/audits/bigideas_audit.md`; `data/manifests/bigideas_extraction_integrity.json` | None; both audits and the regenerated BIG artifacts passed independent review | Independent review completed on 2026-08-15 |
| D — Scientific freeze | Supported labels and leakage-safe splits approved and versioned | Project lead | `NOT_STARTED` | `configs/state/label-v1.yaml`; `configs/trend/label-v1.yaml`; split manifests | Gate C must pass | Project lead required |
| E — Architecture and experiment readiness | Evidence-based architecture constraints and experiment contract approved | Project lead | `NOT_STARTED` | `docs/architecture/readiness_brief.md`; `docs/research/experiment_contract.md`; `reports/audits/model_readiness.md` | Gate D must pass for the relevant task | Project lead required |

## Stop rules

- Do not design or train predictive models before Gates A-D pass for the relevant task.
- Do not open final-test data before the `SCI-FINAL-TEST-001` decision is approved.
- State and Trend receive separate readiness outcomes; one does not rescue the other.
- Missing evidence produces `DATA_REQUIRED`, not an assumed pass.
- Failed class support, isolation, or alignment may produce a task-level `NO_GO`.

## Update rule

Update this file only when an evidence artifact changes a gate status. Activity notes and terminal transcripts do not belong here.
