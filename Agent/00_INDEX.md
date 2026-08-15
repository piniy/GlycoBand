# GlycoBand Agent Pack — Index

**Status:** current working source pack  
**Project:** GlycoBand — Healthynovation NEST UI 2026, Diagnostic Intelligence  
**Updated:** 2026-08-15

This pack is intended for coding, data-engineering, research, modeling, experiment, and reviewer agents.

## Files

- `01_CONTEXT.md` — stable scientific context, terminology, architecture, claim boundaries.
- `02_RESEARCH_PLAN.md` — current RQs, experiment sequence, validation, Go/No-Go rules.
- `03_BASE_DATA.md` — dataset facts, versions, data contracts, audit requirements, label rules.
- `04_DEVELOPMENT_PLAN.md` — repository structure, modules, tests, artifacts, reproducibility.
- `05_EXPERIMENT_AGENT.md` — operating instructions for an AI experiment agent.

## Current architecture

```text
Hb-PPG
4-wave fingertip PPG + fasting venous glucose
        |
        v
MODEL 1 — FASTING STATE EXPERT
        |
        v
Fasting glycemic state

BIG IDEAs
wrist BVP 64 Hz + longitudinal Dexcom G6 CGM
        |
        v
MODEL 2 — FREE-LIVING DYNAMIC EXPERT
        |
        +--> Recent Trend [PRIMARY]
        |    FALLING / STABLE / RISING
        |
        +--> Free-Living Excursion State [OPTIONAL]
```

The two datasets answer different scientific questions and must **not** be merged row-wise into one training population.

## Priority order

```text
1. Verify source versions + checksums + manifests
2. Full Hb-PPG audit
3. Full BIG IDEAs audit
4. Freeze target/label definitions
5. Freeze split manifests
6. Baselines
7. Classical models
8. Negative controls + leakage checks
9. Calibration + SQI + OOD
10. Frozen held-out evaluation
11. Synthetic robustness
12. Candidate engineering envelope
13. Optional Model 2B
14. Optional deep sequence models
15. Decision Engine / integration demo
```

## Source-of-truth rule

If old documents conflict with this pack, use this pack unless the project lead explicitly changes the science after a human review gate.
