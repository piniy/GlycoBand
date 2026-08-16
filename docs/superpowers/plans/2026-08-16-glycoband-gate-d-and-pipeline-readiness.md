# GlycoBand Gate D — Exploratory-to-Freeze Plan

## Purpose

Resolve the remaining State and Trend scientific choices with the **minimum work needed to make an informed freeze decision**, while keeping the final test uncontaminated.

This plan does not require documentation ceremony before useful scientific learning.

## Core rule

```text
PENDING
!= no experimentation allowed

PENDING
= not yet frozen for registered/final evidence
```

Development-only exploratory probes are allowed before Gate D freeze when they are the cheapest valid way to reduce material uncertainty.

## Non-negotiable protections

- Hb-PPG and BIG IDEAs remain separate experiments.
- `data/raw/` is immutable.
- Reference glucose/CGM never enters core inference features.
- Final-test data never influences label/protocol, preprocessing, features, model, calibration, OOD, success criteria, or claim wording.
- State final test is participant-disjoint.
- Trend final test is chronological with no raw-history leakage.
- Project lead freezes scientific decisions and authorizes final-test opening.

## Gate D is now a decision process, not a paperwork gate

For each unresolved scientific decision:

```text
1. inspect existing audit evidence
2. ask whether evidence is sufficient
3. if not, run the cheapest safe exploratory probe
4. summarize what was learned
5. recommend a freeze / revision / no-go
6. project lead decides
```

Do not create extra readiness documents merely to prove that these six steps happened.

---

## Task 1 — Establish or verify the sealed outer test reserve

### State

Create/verify a participant-disjoint final-test reserve that is excluded from candidate-label learnability probes.

The development pool may use participant-grouped CV or train/validation splits.

### Trend

Create/verify a future chronological reserve for each participant.

Any probe using history H must keep required raw BVP/CGM history inside the development region and away from the final reserve.

If candidate H values differ, protect the boundary using the largest H under active consideration or otherwise ensure no candidate can borrow history across the reserve boundary.

### Rule

Once a reserve is used to protect exploratory selection, do not replace it because development results are inconvenient.

**Exit condition:** exploratory work cannot inspect the final reserve.

---

## Task 2 — State formulation study

Current recommendation `<5.6 / >=5.6 mmol/L` is a **candidate**, not an automatic freeze.

### Compare scientifically plausible formulations

Use audit evidence first:

- clinical/research interpretation;
- participants per class;
- samples per class;
- imbalance;
- threshold sensitivity;
- likely measurement/label noise.

### If uncertainty remains, run a cheap probe

Development participants only:

```text
majority baseline
Logistic Regression using simple PPG features
optional context-only comparator
participant-grouped validation
```

Compare candidate formulations only enough to answer whether they are obviously unsupported, viable, or materially different in learnability.

Do not do broad hyperparameter search.

Do not conclude that the best-scoring threshold is the clinically correct threshold.

### Output

```text
Candidate A:
Support:
Probe result:
Scientific strengths/weaknesses:

Candidate B:
...

Recommendation:
Freeze / revise / no-go
Reason:
Remaining uncertainty:
```

**Exit condition:** project lead has enough evidence to freeze or reject State v1.

---

## Task 3 — Trend protocol study

The current package:

```text
H = 30 min
median-of-three smoothing
OLS slope
tau = 0.5 mg/dL/min
>=80% CGM support
continuous BVP history
max CGM gap = 10 min
```

is a candidate package, not an automatic freeze.

### Candidate analysis

Compare only plausible alternatives, for example:

- H: 15 / 30 / 60 min;
- smoothing: none / median3;
- tau: small defensible grid;
- support/gap rules required by data quality.

Measure:

- valid endpoints retained;
- class distribution;
- support by participant;
- label stability;
- effect of small parameter changes.

### If uncertainty remains, run a cheap probe

Development periods only:

```text
majority / always-STABLE
Logistic Regression
chronological development validation
current-window-only vs history-H if needed
```

No final reserve access.

No broad model search.

### Output

Same structure as State: evidence, probe result, interpretation, recommendation.

**Exit condition:** project lead has enough evidence to freeze or reject Trend v1.

---

## Task 4 — Freeze only the decisions that are now justified

After explicit project-lead approval:

- write/update `configs/state/label-v1.yaml` if State is approved;
- write/update `configs/trend/label-v1.yaml` if Trend is approved;
- formalize the relevant split manifest from the sealed reserve/development scheme;
- update the scientific decision register once;
- validate participant/time isolation.

Do not create additional readiness/architecture documents unless another task actually needs them.

**Exit condition:** the approved track has a versioned target + split contract.

---

## Task 5 — Registered baseline development

A track may begin registered baseline development once its own target and split are frozen.

### State

```text
majority
Logistic Regression
context-only comparator
PPG signal baseline
```

### Trend

```text
majority
always-STABLE
Logistic Regression
current-window-only vs history-H
```

Use train/validation only for development choices.

Random Forest/XGBoost follow only if simple evidence justifies more complexity.

**Exit condition:** a reproducible baseline result answers whether the track deserves further modeling.

---

## Task 6 — Final test remains a separate operation

Do not open the final test until all of the following are frozen for that track:

- label/protocol;
- split;
- preprocessing;
- features;
- model family;
- hyperparameters;
- calibration if used;
- OOD/SQI policy if used in scoring;
- primary metric;
- success/No-Go interpretation.

Final-test performance cannot justify going backward and changing those choices while still calling the test pristine.

---

## Completion condition

Gate D is complete for a track when:

```text
candidate uncertainty reduced
-> project lead freezes target/protocol
-> split finalized
-> final reserve remains untouched
```

The purpose of Gate D is **not** to maximize documents or approvals. Its purpose is to enter registered modeling with a defensible scientific target while preserving an independent final test.
