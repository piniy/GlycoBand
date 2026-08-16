# GlycoBand — Codex Operating Rules

## Prime directive

Do the minimum work required to produce the next decision-relevant result.

Stop when the current user task is satisfied.

Plans, phases, readiness documents, TODOs, and unfinished gates describe project state. They are **not authorization** to execute downstream work.

Do not maximize gate completion, documentation volume, repository cleanliness, or number of checks. Optimize for valid research progress.

## Prompt authority and epistemic intake

Do not treat scientific assertions in the user's prompt as established facts.

If a user statement is uncertain, speculative, causal, or conflicts with project evidence, treat it as a **hypothesis or proposal** until verified.

Default authority:

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

Ambiguous verbs such as `prepare`, `initialize`, `review`, `set up`, and `make ready` default to the **minimum sufficient interpretation**, not completion of all downstream dependencies.

## Fast path vs research path

### Fast path

Use for bounded, low-risk work that does not change scientific contracts or depend on unresolved high-impact assumptions.

```text
local context
-> smallest correct action
-> targeted validation
-> stop
```

Examples: documentation edits, deterministic transformations, isolated fixes, and tests for already-frozen invariants.

### Research path

Escalate when the task affects:

- target or label semantics;
- split validity;
- leakage;
- evaluation design;
- claim language;
- model interpretation;
- Go/No-Go decisions;
- unexpected model performance.

Here, scientific validity dominates token efficiency.

## Context routing

Read only what the task needs.

```text
Agent/01_CONTEXT.md
-> stable scientific framing, architecture, and claim boundaries

Agent/02_RESEARCH_PLAN.md
-> research questions, dependency sequence, evaluation, and Go/No-Go

Agent/03_BASE_DATA.md
-> dataset facts, versions, schemas, and label/data contracts

Agent/04_DEVELOPMENT_PLAN.md
-> repository, code, tests, artifacts, and reproducibility

Agent/05_EXPERIMENT_AGENT.md
-> experiment safeguards and scientific execution rules
```

Read `RESEARCH_STANDARDS.md` only when the task directly affects experiments, reproducibility, scientific evidence, environment consistency, or retained research artifacts.

Expand context only when evidence requires it.

Prefer the current file + relevant config/test + git diff + existing evidence over rereading the repository.

## Execution progress

For computational or repository work, prefer **tool/terminal-visible progress** over long narrative progress messages.

When a terminal or execution tool is available:

1. perform the bounded operation;
2. surface short stage/status updates through command/tool output when useful;
3. show concrete results such as files changed, tests run, metrics, failures, or blockers;
4. keep chat summaries compact.

Example:

```text
[1/4] Inspecting relevant files...
[2/4] Applying bounded change...
[3/4] Running targeted tests...
[4/4] Done: 3 tests passed, 2 files changed.
```

Do not print internal chain-of-thought or lengthy hidden reasoning. Show **actions, evidence, results, and decisions**.

Do not create artificial progress logs for trivial tasks. A small task may simply execute and report completion.

## Expensive-work rule

Before full audits, full test suites, dataset hashing, broad research, model searches, or subagent fan-out, require at least one:

1. the user explicitly requested it;
2. the current task cannot be completed correctly without it;
3. prior evidence was invalidated by a dependency change;
4. a credible anomaly threatens correctness or scientific validity.

Otherwise reuse valid evidence, note the follow-up, and stop.

A new Codex chat is not an evidence-invalidation event.

## Delegation

Use subagents only for clearly independent bounded work where parallelism or context isolation is worth the extra model/tool cost.

Prefer delegation for read-heavy exploration, tests, triage, and independent checks.

Keep scientific decisions, conflicting-evidence interpretation, target/split/claim changes, and final synthesis in the main thread.

Avoid overlapping parallel writes.

## Validation proportionality

```text
docs-only
-> consistency check

isolated implementation
-> relevant unit tests

local dependency change
-> targeted unit + integration tests

preprocessing / labels / splits
-> deeper pipeline and scientific checks

final evaluation / scientific contract
-> full applicable safeguards
```

Do not automatically run the full test suite, Ruff, mypy, dataset audits, or integrity checks after every change.

Run broader verification only when the affected surface or explicit task requires it.

## Readiness and plans

Readiness documents and plans are descriptive unless the current task explicitly authorizes execution.

```text
NOT_STARTED != authorized work
IN_PROGRESS  != continue automatically
PASS         != rerun validation
```

Do not chase `PASS` states.

Gate status changes are side effects of authorized evidence-producing work, not objectives themselves.

## End-of-task output

For development:

```text
Changed:
Validated:
Result:
Remaining issue:
```

For analysis:

```text
Finding:
Evidence:
Interpretation:
Confidence:
Recommended next action:
```

Do not regenerate project history unless explicitly requested.
