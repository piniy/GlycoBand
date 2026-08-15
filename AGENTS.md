# AGENTS.md — GlycoBand Repository Instructions

## Project status

GlycoBand is a computational biomedical feasibility-research project for Healthynovation NEST UI 2026. It is not a clinically validated medical device, glucometer, continuous glucose monitor, diagnostic system, or treatment-decision system.

## Source-of-truth order

Read the project pack before changing scientific behavior:

1. `Agent/00_INDEX.md`
2. `Agent/01_CONTEXT.md`
3. `Agent/02_RESEARCH_PLAN.md`
4. `Agent/03_BASE_DATA.md`
5. `Agent/04_DEVELOPMENT_PLAN.md`
6. `Agent/05_EXPERIMENT_AGENT.md`

`Agent/GLYCOBAND_AGENT-1.md` is retained as legacy research context. When it conflicts with the current pack above, the current pack wins. In particular:

- Model 1 uses Hb-PPG for fasting glycemic-state research.
- Model 2 uses BIG IDEAs v1.1.3 for free-living Recent Trend research.
- PhysioCGM is outside the current core training, validation, and synthetic-testing scope.
- Hb-PPG and BIG IDEAs must never be concatenated into one training population.

## Non-negotiable scientific boundaries

- PPG/BVP is the core inference input; reference glucose is used only to create or evaluate labels.
- State evaluation is participant-aware. One participant must never cross train/test boundaries.
- Trend evaluation is within-person chronological with sufficient embargo and no overlapping raw history.
- Never use the final test set to select labels, thresholds, preprocessing, features, models, calibration, or OOD policy.
- Never fabricate wavelength channels, people, glucose values, or population evidence.
- Keep native predictive validation, native-derived robustness, and software integration results separate.
- The Decision Engine is deterministic and never arithmetically fuses State and Trend into glucose.
- Preserve participant, source-file, timestamp, label, preprocessing, feature, and split provenance.
- Treat `data/raw/` as immutable.

## Human review gates

Stop for project-lead review before freezing State labels, Trend label parameters, split manifests, opening a final test set, changing the target or claims, adding a core predictor/dataset, promoting deep learning to primary, or promoting Model 2B to primary scope.

## Development conventions

- Follow `RESEARCH_STANDARDS.md` for experiment evidence, reproducibility, compact records, and environment consistency.
- Target Python 3.11+ and use the checked-in `uv.lock` for reproducibility.
- Put reusable logic in `src/glycoband/`; notebooks are for exploration, not sole-source core logic.
- Use typed interfaces, `pathlib`, deterministic seeds, structured logs, config-driven scientific choices, and versioned artifacts.
- Add tests for split integrity, temporal leakage, label generation, provenance, degradation behavior, and Decision Engine gates as those modules are implemented.
- Do not hardcode unresolved scientific values. Keep them as explicit `TBD_*` config values until their review gate passes.

## Required verification

Before declaring a change complete, run:

```powershell
uv run pytest
uv run ruff check .
```

Run additional experiment-specific checks required by `Agent/05_EXPERIMENT_AGENT.md` before reporting scientific results.
