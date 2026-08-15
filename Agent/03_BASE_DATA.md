# GlycoBand — Base Data and Data Contracts

## Purpose

This file records source-level dataset facts, versions, data contracts, allowed/forbidden use, audit requirements, and label provenance.

It is not a substitute for raw-data audit results. Anything marked `TBD_AUDIT` must be calculated from downloaded files.

## Dataset A — Hb-PPG

### Role

Primary dataset for Model 1 — Fasting State Expert.

### Source

Paper: **A Four-Wavelength Photoplethysmography dataset for non-invasive hemoglobin assessment**, Scientific Data, 2026.  
DOI: `10.1038/s41597-026-06945-6`

Dataset: Figshare v6.  
DOI: `10.6084/m9.figshare.22256143.v6`

### Verified source-level facts

- 252 retained adult participants.
- Approximate age range 21–90 years.
- Reflection fingertip PPG.
- Four wavelengths: 660, 730, 850, 940 nm.
- Per-participant PPG files.
- Metadata includes age, gender, height, weight, Hb, blood glucose, SBP, DBP, signal length.
- Signal durations include roughly 45–60 s.
- Fasting blood glucose information is recorded.
- The source paper is primarily a data descriptor; it does not itself establish GlycoBand's fasting-glucose model performance.

### Native contract

```text
StateInput
- participant_id
- ppg_660
- ppg_730
- ppg_850
- ppg_940
- sampling_rate
- signal_length
- acquisition_metadata
```

Reference: fasting venous blood glucose.

Core predictor: PPG-derived information.

Optional declared context comparator: age, sex/gender, BMI if legitimately derived from real height/weight.

Do not silently use glucose reference, Hb, SBP, or DBP as core predictors.

### Required audit (`TBD_AUDIT`)

- exact glucose distribution/quantiles,
- candidate class counts,
- participant support per class,
- missingness,
- actual rate/length consistency,
- corrupt files,
- flatline/clipping,
- usability per wavelength,
- pulse quality/SQI,
- representative signals.

## Dataset B — BIG IDEAs

### Role

Primary dataset for Model 2 — Recent Trend. Optional secondary dataset for Model 2B.

### Current version

PhysioNet **v1.1.3**, published 13 Apr 2026.  
DOI: `10.13026/aw6y-fc44`

Use the same exact version in manifests, reports, and citations unless explicitly changed.

### Verified source-level facts

- 16 participants.
- Inclusion age approximately 35–65.
- Point-of-care A1C inclusion approximately 5.2–6.4%.
- Monitoring approximately 8–10 days.
- Empatica E4 wrist wearable.
- Dexcom G6 CGM.
- CGM measures interstitial glucose about every 5 min.
- BVP/PPG sampled ~64 Hz.
- Additional modalities include ACC, EDA, temperature, HR, IBI, food logs, demographics.
- Total uncompressed size about 34.1 GB.
- Individual BVP files can be around ~1 GB or more.

### Critical sensor rule

Treat `BVP.csv` as one native BVP signal. It is not wavelength-resolved raw optical data.

Forbidden:

```text
BVP -> fake green/red
BVP -> fake 660/730/850/940 channels
```

### Native contract

```text
DynamicInput
- participant_id
- bvp
- sampling_rate
- start_timestamp
- end_timestamp
- optional quality metadata
- optional motion metadata
```

Reference contract: CGM trajectory.

Core inference:

```text
BVP history -> predicted Trend
```

CGM is used for ground-truth generation/evaluation, not as a core inference feature.

### Required audit (`TBD_AUDIT`)

Per participant:

```text
participant_id
bvp_start/end/duration
cgm_start/end/duration
overlap_duration
cgm_points
cgm_gap_stats
bvp_gap_stats
usable_aligned_hours
valid_short_windows
sqi_stats
glucose_stats
trend_label_counts_by_candidate_protocol
```

Also compute support by both **windows** and **participants**.

## Separation matrix

| Property | Hb-PPG | BIG IDEAs |
|---|---|---|
| Primary task | Fasting State | Recent Trend |
| Participants | 252 | 16 |
| Placement | fingertip | wrist |
| Optical form | 4 wavelength channels | 1 BVP stream |
| Sampling | ~200 Hz | ~64 Hz |
| Temporal structure | ~45–60 s snapshot | ~8–10 day longitudinal |
| Reference | fasting venous glucose | interstitial CGM |
| Primary split | participant-aware | within-person chronological |
| Row-wise merge | forbidden | forbidden |

## State-label contract

Clinical/conceptual categories may be declared before modeling, provided boundaries are defensible. Example vocabulary may be `LOW / NORMAL / ELEVATED`.

But the raw-data audit must determine whether each class has enough participant support to be evaluated as a primary ML class.

Correct:

```text
audit -> clinical candidate definitions -> support review -> freeze labels -> model -> final test
```

Incorrect:

```text
final test -> change cutoff -> retest
```

After performance audit, the operational layer may suppress unreliable outputs without redefining ground truth.

## Trend-label contract

Vocabulary:

```text
FALLING / STABLE / RISING
```

Candidate generator:

```text
CGM history ending at t -> slope -> thresholded direction
```

Parameters to freeze before final test:

- H,
- slope method,
- smoothing,
- tau,
- minimum valid CGM points,
- alignment tolerance,
- gap policy.

Candidate H: 15 / 30 / 60 min.

## Manifest schema

### Hb-PPG

```text
dataset
dataset_version
participant_id
source_path
checksum
sampling_rate
signal_length_seconds
has_660/730/850/940
glucose_reference
reference_type
missing_fraction
exclusion_reason
split
processing_version
```

### BIG IDEAs

```text
dataset
dataset_version
participant_id
source_file
modality
checksum
sampling_rate
start_time
end_time
duration
overlap_with_cgm
missing_fraction
exclusion_reason
split_policy
processing_version
```

## Derived-sample provenance

Every feature row should retain:

```text
dataset + version
participant_id
recording/source_file
window_start/end
label + label_version + label_source
preprocess_version
feature_version
split
```

Never lose participant/temporal identity.

## Storage policy

`data/raw/` is immutable.  
`data/interim/` holds aligned/cleaned native-derived data.  
`data/processed/` holds model-ready data.  
`data/manifests/` holds versions, checksums, splits, exclusions, provenance.

For BIG IDEAs process participant-wise/chunk-wise and prefer Parquet for compact derived tables.

## Current status

| Item | Status |
|---|---|
| Hb-PPG source/schema | source-level verified |
| Hb-PPG exact glucose/class audit | `TBD_AUDIT` |
| Hb-PPG model performance | not established |
| BIG IDEAs v1.1.3 source/version | verified |
| BIG IDEAs source/schema | source-level verified |
| BIG IDEAs exact BVP-CGM overlap | `TBD_AUDIT` |
| BIG IDEAs Trend class distribution | `TBD_AUDIT` |
| BIG IDEAs PPG-only Trend performance | not established |
| Model 2B feasibility | secondary / not established |
| synthetic robustness | not yet run |
| physical wearable validity | not established |

## External references

- `https://doi.org/10.1038/s41597-026-06945-6`
- `https://doi.org/10.6084/m9.figshare.22256143.v6`
- `https://physionet.org/content/big-ideas-glycemic-wearable/1.1.3/`
- `https://doi.org/10.13026/aw6y-fc44`
