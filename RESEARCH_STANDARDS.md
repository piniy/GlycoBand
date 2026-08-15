# GlycoBand Research, Reproducibility, and Environment Standard

## Purpose

This file defines the minimum standard for trustworthy GlycoBand experiments. It converts the scientific rules in `Agent/` into a compact operating policy. It is not a lab journal, activity log, or substitute for an experiment report.

## 1. Research standard

Every experiment must answer one frozen research question with one declared evidence level:

- **Native predictive validation:** real held-out data tests predictive information in the source domain.
- **Native-derived robustness:** controlled degradation of real held-out signals tests model sensitivity.
- **Integration demonstration:** fixtures test software behavior only.
- **Engineering inference:** results motivate candidate hardware requirements without validating a device.

Never combine these evidence levels in one metric or claim.

Before training, record the following in a versioned config or experiment summary:

```text
objective and research question
dataset and exact version
independent unit
inference input
reference and label version
split-manifest version
baseline and negative control
model and primary metric
Go / No-Go rule
claim ceiling
```

If any required field is unresolved, the run is exploratory and cannot open the final test set.

### Required validity controls

- Hb-PPG State splits are participant-disjoint.
- BIG IDEAs Trend splits are chronological within each participant, with an embargo at least as long as the model history.
- Overlapping raw samples never cross split boundaries.
- Reference glucose never enters core inference features.
- Preprocessing, imputation, feature selection, calibration, and OOD fitting use only their allowed training or validation partitions.
- Baselines, leakage checks, and the task-specific negative control run before a result is treated as evidence.
- Poor class support, unresolved alignment, or ambiguous participant identity blocks confirmatory training.

Final-test results never select labels, thresholds, filters, features, hyperparameters, calibration, or claim wording. A change after final-test inspection creates a new exploratory cycle and must be disclosed.

## 2. Reproducibility standard

A result is reproducible when another clean checkout can use the recorded code, lockfile, manifests, config, and command to regenerate the same samples and splits and obtain materially equivalent metrics. Bit-for-bit equality is required for deterministic derived artifacts where practical; floating-point model results may use declared tolerances.

### Data identity and provenance

- Keep `data/raw/` immutable and outside Git.
- Record dataset name, version, source, file checksum, exclusion reason, and acquisition metadata in a manifest.
- Preserve participant ID, source recording, window timestamps, label source/version, preprocessing version, feature version, and split on every derived sample.
- Never overwrite a frozen manifest, config, prediction table, or model bundle. Create a new version.

### Minimum experiment artifact set

Store each completed run under `reports/experiments/<experiment_id>/` with:

```text
config.yaml
environment.txt
dataset_manifest.json
split_manifest.json
metrics.json
per_participant.csv
predictions.parquet
summary.md
model_bundle/          # when a fitted model is retained
logs.txt               # warnings, errors, and major lifecycle events only
```

`summary.md` must state the result, baseline comparison, negative-control result, leakage checks, limitations, claim ceiling, and whether the conclusion is `supported`, `partially supported`, `not supported`, or `insufficient evidence`.

### Compact records, not journals

Record decisions and evidence, not a transcript of activity.

Do record:

- the final command, config, seed, manifests, metrics, and failure reason;
- exclusions and protocol deviations that could change interpretation;
- a concise explanation when a rerun differs.

Do not record:

- terminal dumps, chat transcripts, daily diaries, or repeated progress notes;
- one log line per sample or window;
- duplicate dependency listings when `uv.lock` already defines them;
- secrets, credentials, or raw sensitive participant data in logs.

Use structured tables such as Parquet or CSV for sample-level outputs. Keep text logs small and diagnostic.

## 3. Environment consistency standard

The canonical development environment is defined by:

- `.python-version` for the Python line;
- `pyproject.toml` for declared dependencies and tools;
- `uv.lock` for exact resolved packages;
- the Git commit and experiment config for code and scientific choices.

Create or restore the environment with:

```powershell
uv sync --frozen
uv lock --check
uv run --frozen pytest
uv run --frozen ruff check .
uv run --frozen mypy
```

Do not manually install packages into `.venv`. Change `pyproject.toml`, regenerate `uv.lock`, and review the lockfile change instead. Do not use a local `pip freeze` dump as the project dependency source.

Each `environment.txt` should contain only information needed to rerun or explain a result:

```text
UTC run timestamp
Git commit and dirty/clean state
Python version
operating system and architecture
uv.lock checksum
experiment command and seed
dataset, config, and split-manifest identifiers
CPU/GPU details only when they affect execution or determinism
```

Never include secret values. Record the name of a required environment variable, not its contents.

## 4. Execution gates

### Before a confirmatory run

- Dataset version and checksums are verified.
- Audit findings support the selected task and classes.
- Labels and splits passed their human review gates.
- The final test remains sealed.
- Leakage assertions and unit tests pass.
- The environment restores with `uv sync --frozen`.

### Before reporting a result

- Required artifacts exist and reference one another consistently.
- Baselines and negative controls are included.
- Per-class and per-participant support is visible.
- The recorded command reruns successfully from the locked environment.
- Conclusions stay within the dataset, population, sensor, placement, and evidence-level boundaries.

Failure of a gate means the result is exploratory, blocked, or insufficient evidence. It must not be promoted by changing the target or claim after inspection.

## Related instructions

- `Agent/03_BASE_DATA.md` defines dataset contracts and provenance.
- `Agent/04_DEVELOPMENT_PLAN.md` defines repository and artifact structure.
- `Agent/05_EXPERIMENT_AGENT.md` defines experiment gates and required controls.
- `AGENTS.md` defines repository-wide precedence and human review gates.
