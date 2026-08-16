# GlycoBand Research Readiness Contract

## Purpose

This is the single status page for preparation evidence and scientific freeze. A gate passes only
when its evidence exists and the required reviewer has accepted it.

## Status vocabulary

- `NOT_STARTED`: no qualifying evidence yet.
- `IN_PROGRESS`: evidence is being collected but the gate is not satisfied.
- `PASS`: every exit condition is satisfied.
- `DATA_REQUIRED`: required source data or metadata is unavailable.
- `NO_GO`: evidence shows the proposed task is not defensible.
- `SUPERSEDED`: a newer version replaces this decision or artifact.

## Gates

| Gate | Required outcome | Owner | Current status | Evidence | Current blocker | Approval |
|---|---|---|---:|---|---|---|
| A — Repository and environment | Committed Git baseline, clean evidence capture, locked environment restores, tests/lint/types pass | Repository maintainer | `PASS` | `reports/audits/environment_preflight.json` | None when the report records a commit, `dirty=false`, successful sync, and all checks passing | Automated checks |
| B — Source and storage | Exact sources, access, license, sizes, checksums, and storage budget verified | Data preparation owner | `PASS` | `configs/data_sources.yaml`; `data/manifests/source_manifest.json`; `docs/research/source_verification.md` | None; both authorized archives are locally complete | Project lead authorized required downloads on 2026-08-15 |
| C — Raw-data audits | Hb-PPG and BIG IDEAs audits complete with exclusions and support evidence | Audit owner | `PASS` | `reports/audits/hbppg_audit.md`; `reports/audits/bigideas_audit.md`; `data/manifests/bigideas_extraction_integrity.json` | None; both audits and the regenerated BIG artifacts passed independent review | Independent review completed on 2026-08-15 |
| D-State — Scientific freeze | State label and participant-disjoint split approved and versioned | Project lead | `IN_PROGRESS` | `configs/state/label-v1.yaml`; `reports/probes/state_exploratory-v1/decision_record.md` | Label is frozen; registered participant split and model protocol remain unfrozen | Label-only freeze recorded; split/model approval required |
| D-Trend — Scientific freeze | Trend protocol and chronological split approved and versioned | Project lead | `NOT_STARTED` | `configs/trend/label-v1.yaml`; `data/manifests/trend_split-v1.json` | Candidate protocol and split are not frozen | Project lead required |

## Stop rules

- Before Gate D-State, exploratory development-only State probes are permitted; registered State
  experiments and final evaluation are prohibited.
- Before Gate D-Trend, exploratory development-only Trend probes are permitted; registered Trend
  experiments and final evaluation are prohibited.
- Do not run registered State modeling before Gates A-C and D-State pass.
- Do not run registered Trend modeling before Gates A-C and D-Trend pass.
- Baseline development uses only training and validation partitions after its task-specific scientific freeze.
- Do not open final-test data before the `SCI-FINAL-TEST` decision is frozen.
- State and Trend receive separate label and split outcomes; one does not rescue the other.
- Missing evidence produces `DATA_REQUIRED`, not an assumed pass.
- Failed class support, isolation, or alignment may produce a task-level `NO_GO`.

## Update rule

Update this file only when an evidence artifact changes a gate status. Activity notes and terminal
transcripts do not belong here.
