# BIG IDEAs v1.1.3 Raw-Data Audit Contract

## Purpose and boundary

This audit determines whether BIG IDEAs v1.1.3 can support a within-person chronological Recent Trend study. It does not freeze a Trend protocol, create train/test periods, train a model, or claim population-level validation.

## Inputs

- Immutable archive: `data/raw/bigideas/big-ideas-glycemic-wearable-1.1.3.zip`
- Extracted source: `data/raw/bigideas/v1.1.3/`
- Official file checksums: `data/raw/bigideas/SHA256SUMS.txt`
- Participants: `001` through `016`
- Native input: one `BVP_<ID>.csv` stream with `datetime,bvp`
- Reference: `Dexcom_<ID>.csv`, EGV rows only
- Declared BVP rate: 64 Hz

No other wearable modality is a core predictor. BVP is one native stream and must never be treated as wavelength-resolved data.

## Required source-integrity output

- ZIP integrity;
- exact archive membership;
- SHA-256 verification of every extracted file against the official manifest;
- participant/file inventory and explicit missing or unexpected paths.

Because PhysioNet does not publish an archive-level digest, extraction is accepted only after every listed file passes its official file digest.

## Required participant-level output

- BVP and CGM start/end/duration;
- exact overlap duration;
- BVP rows, finite values, timestamp order, duplicates, gaps, implied rate, flat runs, and extrema occupancy;
- CGM EGV count, numeric glucose support, timestamp order, duplicates, and gap distribution;
- usable aligned duration under explicitly recorded audit policies;
- counts of contiguous 30-second BVP windows and descriptive quality indicators;
- glucose distribution;
- candidate `FALLING / STABLE / RISING` counts for each audited history/threshold protocol;
- class support by both windows and participants, never windows alone.

## Candidate Trend study

Every candidate label uses only CGM history at or before time `t`. The audit varies history length, slope threshold, smoothing, minimum support, and gap policy from config. These combinations are exploratory evidence, not approved labels. No candidate may inspect a future CGM value.

## Memory and execution rules

BVP is read participant-wise and in chunks. The audit must not load the full dataset into memory. Intermediate tables contain provenance and are written only outside `data/raw/`.

## Exit gate

The audit passes only when all official files verify, all 16 participants are accounted for, BVP-CGM overlap and gaps are measured, candidate label support is reported per participant, anomalies and exclusions are explicit, and outputs reproduce from the verified source.

## Artifacts

- `reports/audits/bigideas_participants.csv`
- `reports/audits/bigideas_trend_candidates.csv`
- `reports/audits/bigideas_audit.json`
- `reports/audits/bigideas_audit.md`

