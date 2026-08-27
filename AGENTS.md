# GlycoBand — Codex Operating Rules

## Prime directive

Do the minimum work required to produce the next **decision-relevant result**.

Optimize for:

```text
important uncertainty removed
-----------------------------
time + compute + complexity
```

Do not optimize for gate completion, documentation volume, repository cleanliness, or number of checks.

Plans, readiness pages, TODOs, and decision registers describe project state. They are not autonomous work queues.

## Prompt authority

```text
ASK / EXPLAIN / EVALUATE / OPINION
-> non-mutating by default

PLAN / DESIGN / PROPOSE
-> specification only by default

CHECK / VERIFY
-> inspect only what is necessary

IMPLEMENT / FIX / CREATE / UPDATE
-> bounded mutation

RUN / AUDIT / EXECUTE
-> perform the named operation only

APPROVE / FREEZE
-> may change a scientific contract, subject to human-review rules
```

Ambiguous verbs such as `prepare`, `initialize`, `review`, `set up`, and `make ready` default to the minimum sufficient interpretation.

## Three evidence levels

### Level 0 — Audit / descriptive analysis

Use to inspect distributions, support, missingness, gaps, SQI, candidate labels, and feasibility constraints.

No model score is required.

### Level 1 — Exploratory probe

Use when a scientific decision is still unresolved and a cheap development-only experiment can materially reduce uncertainty.

An exploratory probe:

- uses development data only;
- never accesses the sealed final test;
- may compare candidate labels, H/tau values, smoothing, alignment, preprocessing, feature families, or simple baseline learnability;
- should use the cheapest adequate method first, normally Dummy/majority and Logistic Regression;
- may use participant-grouped or chronological development validation as appropriate;
- is not final scientific evidence;
- cannot select a clinical definition solely because it gives a better model score;
- cannot automatically freeze a scientific decision;
- must end with a finding, uncertainty remaining, and recommendation.

### Level 2 — Registered experiment

Use for evidence intended to support the scientific conclusion.

Relevant labels, split contract, preprocessing/evaluation rules, and claim ceiling must already be frozen.

The final test remains sealed until the full pipeline is frozen.

## Mandatory uncertainty loop

Before requesting a project-lead freeze, ask:

> Is there a cheap, non-test exploratory probe that would materially improve this decision?

Use:

```text
uncertainty
-> can existing evidence resolve it?
   -> yes: recommend decision
   -> no: can a cheap exploratory probe resolve it?
      -> yes: run/recommend probe -> interpret -> recommend
      -> no: escalate to project lead
-> freeze if approved
-> registered experiment
```

Do not stop merely because a field is `PENDING` if a safe exploratory probe is the cheapest valid way to learn.

## Final-test protection

The final test must never influence:

- target or label definition;
- category thresholds;
- Trend H/tau/smoothing/alignment/gap policy;
- preprocessing;
- features;
- model family;
- hyperparameters;
- calibration;
- OOD policy;
- success criteria;
- claim wording.

If exploratory model learnability will influence a target/protocol decision, first establish a leakage-safe outer test reserve whose membership/time range is excluded from the probe.

Once reserved, do not change or inspect that reserve to improve development results. Changing it requires explicit project-lead review and must be documented.

## Research path

Escalate reasoning when work affects:

- target or label semantics;
- split validity;
- leakage;
- evaluation design;
- claim language;
- model interpretation;
- Go/No-Go decisions;
- unexpected model performance.

Scientific validity dominates token efficiency, but scientific rigor does not require unnecessary ceremony.

## Context routing

Read only what the task needs.

```text
Agent/01_CONTEXT.md
-> stable scientific framing, architecture, claim boundaries

Agent/02_RESEARCH_PLAN.md
-> research questions, evidence sequence, evaluation, Go/No-Go

Agent/03_BASE_DATA.md
-> dataset facts, versions, schemas, label/data contracts

Agent/04_DEVELOPMENT_PLAN.md
-> repository, code, tests, artifacts, reproducibility

Agent/05_EXPERIMENT_AGENT.md
-> experiment safeguards and scientific execution rules
```

Expand context because evidence requires it, not because more files exist.

## Expensive-work rule

Before full audits, full test suites, broad model searches, repository-wide scans, or subagent fan-out, require at least one:

1. the user explicitly requested it;
2. the task cannot be completed correctly without it;
3. upstream evidence was invalidated;
4. a credible anomaly threatens correctness or scientific validity.

Otherwise use the smallest discriminating operation.

## Validation proportionality

```text
docs-only
-> consistency check

exploratory probe
-> leakage-safe dev split + minimal reproducibility + targeted sanity checks

isolated implementation
-> relevant unit tests

preprocessing / labels / splits
-> deeper pipeline and scientific checks

registered/final evaluation
-> full applicable safeguards
```

Do not automatically run every available check after every change.

## Human review

Human review is required to:

- freeze or revise a scientific target/label contract;
- freeze or deliberately replace the final split contract;
- open the final test;
- change claim ceiling;
- make a major architecture/dataset-scope change.

Human review is **not** required for every reversible development-only exploratory probe that obeys the rules above.

## Readiness and plans

```text
PENDING      != no learning allowed
PENDING      == not frozen for registered/final evidence
NOT_STARTED  != authorized work
PASS         != rerun validation
```

Do not chase gate status. Gates are summaries of evidence state, not the objective.

## Repository-specific scientific rules

GlycoBand is a computational biomedical feasibility-research project for Healthynovation NEST UI 2026. It is not a clinically validated medical device, glucometer, continuous glucose monitor, diagnostic system, or treatment-decision system.

The authoritative source pack is:

1. `Agent/AGENTS.md`
2. `Agent/01_CONTEXT.md`
3. `Agent/02_RESEARCH_PLAN.md`
4. `Agent/03_BASE_DATA.md`
5. `Agent/04_DEVELOPMENT_PLAN.md`
6. `Agent/05_EXPERIMENT_AGENT.md`

The current architecture is fixed unless explicitly reviewed:

- Model 1 uses Hb-PPG for fasting glycemic-state research.
- Model 2 uses BIG IDEAs v1.1.3 for free-living Recent Trend research.
- PhysioCGM is outside the current core training, validation, and synthetic-testing scope.
- Hb-PPG and BIG IDEAs must never be concatenated into one training population.

Additional non-negotiable boundaries:

- PPG/BVP is the core inference input; reference glucose is used only to create or evaluate labels.
- State evaluation is participant-aware. One participant must never cross train/test boundaries.
- Trend evaluation is within-person chronological with sufficient embargo and no overlapping raw history.
- Never fabricate wavelength channels, people, glucose values, or population evidence.
- Keep native predictive validation, native-derived robustness, and software integration results separate.
- The Decision Engine is deterministic and never arithmetically fuses State and Trend into glucose.
- Preserve participant, source-file, timestamp, label, preprocessing, feature, and split provenance.
- Treat `data/raw/` as immutable.

Stop for project-lead review before freezing State labels, Trend label parameters, split manifests, opening a final test set, changing the target or claims, adding a core predictor/dataset, promoting deep learning to primary, or promoting Model 2B to primary scope.

Track preparation evidence and gate status in `docs/research/readiness_contract.md`. Record reviewed scientific decisions in `docs/research/decision_register.md`.

## Development conventions

- Follow `RESEARCH_STANDARDS.md` for experiment evidence, reproducibility, compact records, and environment consistency.
- Target Python 3.11+ and use the checked-in `uv.lock` for reproducibility.
- Put reusable logic in `src/glycoband/`; notebooks are for exploration, not sole-source core logic.
- Use typed interfaces, `pathlib`, deterministic seeds, structured logs, config-driven scientific choices, and versioned artifacts.
- Add tests for split integrity, temporal leakage, label generation, provenance, degradation behavior, and Decision Engine gates as those modules are implemented.
- Do not hardcode unresolved scientific values. Keep them as explicit `TBD_*` config values until their review gate passes.
- Meaningful experiment runners must provide concise live terminal progress and save interpretation-relevant diagnostic figures according to `RESEARCH_STANDARDS.md`; do not replace these with additional planning prose.

## Required verification

Before declaring a change complete, restore the locked environment and run:

```powershell
uv sync --frozen
uv lock --check
uv run --frozen pytest
uv run --frozen ruff check .
uv run --frozen mypy
```

Run additional experiment-specific checks required by `Agent/05_EXPERIMENT_AGENT.md` before reporting scientific results.

## End-of-task output

For analysis/probes:

```text
Question:
Probe or evidence used:
Finding:
What it does not prove:
Confidence:
Recommended next action:
```

For development:

```text
Changed:
Validated:
Result:
Remaining issue:
```

Stop when the next decision-relevant result has been produced.
