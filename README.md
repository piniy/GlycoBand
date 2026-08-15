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

The repository and source gate are initialized. The Hb-PPG v6 raw-data audit is complete; BIG
IDEAs acquisition and audit remain in progress. No label freeze, split freeze, training run,
held-out result, synthetic robustness result, or physical-device validation has been completed.

The authoritative research instructions are in [`Agent/00_INDEX.md`](Agent/00_INDEX.md) through [`Agent/05_EXPERIMENT_AGENT.md`](Agent/05_EXPERIMENT_AGENT.md). See [`AGENTS.md`](AGENTS.md) for repository-wide operating rules and [`RESEARCH_STANDARDS.md`](RESEARCH_STANDARDS.md) for the concise research, reproducibility, and environment policy.

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

## Current next gate

Complete the checksum-verified BIG IDEAs acquisition and raw-data audit. Scientific labels and
split manifests require human review before they are frozen.

The preparation sequence is defined in the [Research Start Readiness Plan](docs/superpowers/plans/2026-08-15-glycoband-research-start-readiness.md). The plan must reach its final readiness gate before architecture implementation or model experimentation begins.
