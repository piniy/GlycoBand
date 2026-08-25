# GlycoBand

GlycoBand is a reproducible PPG/BVP feasibility-research codebase for two separate questions:

1. Can four-wavelength fingertip PPG classify fasting glycemic state across unseen participants in Hb-PPG?
2. Can longitudinal wrist BVP classify recent CGM-derived glucose direction within a person in BIG IDEAs v1.1.3?

The project does **not** currently claim to measure glucose, replace a glucometer/CGM, diagnose diabetes, or validate a physical wearable.

## Scientific architecture

```text
Hb-PPG v6                         BIG IDEAs v1.1.3
4-wave fingertip PPG             wrist BVP + CGM reference
        |                                  |
        v                                  v
Fasting State Expert             Recent Trend Expert
        |                                  |
        +----------> Decision Engine <-----+
                    deterministic
```

The datasets remain separate because their sensors, placement, reference modalities, populations, protocols, and temporal structures differ.

## Repository status

Readiness Gates A-C are complete: the environment, source identity/storage, and raw-data audits
for Hb-PPG v6 and BIG IDEAs v1.1.3 have passed. The State label definition remains frozen as
Candidate A (binary 5.6 mmol/L boundary), but State research is `PARKED`: its development-only
probe did not support incremental PPG learnability on the current representation, so no State
split or model protocol is active. No registered model, held-out result, synthetic robustness
result, or physical-device validation has been completed.

The authoritative research instructions are [`Agent/AGENTS.md`](Agent/AGENTS.md) and
[`Agent/01_CONTEXT.md`](Agent/01_CONTEXT.md) through
[`Agent/05_EXPERIMENT_AGENT.md`](Agent/05_EXPERIMENT_AGENT.md). See [`AGENTS.md`](AGENTS.md)
for repository-wide operating rules and [`RESEARCH_STANDARDS.md`](RESEARCH_STANDARDS.md) for the
concise research, reproducibility, and environment policy.

## Setup

Requirements: Python 3.11 and [uv](https://docs.astral.sh/uv/).

```powershell
uv sync
uv run pytest
uv run ruff check .
```

## Data placement

Downloaded source data is intentionally excluded from Git:

```text
data/raw/hbppg/
data/raw/bigideas/
```

Do not modify raw files. Store checksums and source/version records in `data/manifests/`; write aligned native-derived data to `data/interim/` and model-ready data to `data/processed/`.

## Current frontier: Trend conditioning gate

The BIG IDEAs Trend label protocol and chronological split are now versioned for registered
development: trend-label-v1 and trend-split-v1. The generated endpoint artifact contains
27,913 causal endpoints from 16 participants; 27,529 remain usable after 384 embargo exclusions.
The State decision record is
[`docs/research/decision_register.md`](docs/research/decision_register.md), and its final
development-only resolution is in
[`reports/probes/state_exploratory-v1/decision_record.md`](reports/probes/state_exploratory-v1/decision_record.md).
The 44-person State reserve remains sealed; reopening State requires an explicit project-lead
decision.

The completed preparation sequence is retained in the [Research Start Readiness Plan](docs/superpowers/plans/2026-08-15-glycoband-research-start-readiness.md). Phase 0 diagnostics and the Phase 1 conditioning/SQI probe used training and validation partitions only. The final frontier is `NOT_SUPPORTED_BY_CONDITIONING`: the selected conditioned candidate reached validation Macro-F1 `0.2879` versus the raw anchor `0.2889`; hard SQI exclusion retained `91.8%` of validation endpoints without recovering directional recall. See [`reports/probes/trend-signal-conditioning-v1/summary.md`](reports/probes/trend-signal-conditioning-v1/summary.md). Phase 2+, deep learning, and final-test evaluation remain closed; the final test is sealed.
