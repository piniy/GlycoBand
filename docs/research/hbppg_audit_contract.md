# Hb-PPG v6 Raw-Data Audit Contract

## Purpose and boundary

This audit determines whether Hb-PPG v6 can support a participant-aware fasting-state study. It describes the source data; it does not select a label, split participants, train a model, or establish clinical validity.

## Inputs

- Immutable archive: `data/raw/hbppg/Hb_PPG_Dataset.zip`
- Extracted source: `data/raw/hbppg/v6/Hb_PPG_Dataset/`
- Metadata key: `ID`
- Signal files: one `<ID>.csv` per participant
- Required ordered channels: `660nm`, `730nm`, `850nm`, `940nm`
- Declared native rate: 200 Hz
- Reference field: `Blood glucose (mmol/L)`

The CSV representation is authoritative for this audit. MAT files are checked for one-to-one presence but are not used as a second copy of the participant.

## Required participant-level output

- metadata/file identity and duplicate checks;
- raw and numeric glucose value, with non-numeric tokens treated as missing;
- declared duration, observed sample count, and implied sampling rate;
- exact channel order and equal lengths;
- NaN/Inf, standard deviation, unique-value fraction, consecutive-flat fraction, and extrema occupancy per channel;
- descriptive pulse-band frequency and spectral-power ratio per channel;
- explicit exclusion reasons, without silently removing records.

The initial signal-quality fields are descriptive screening indicators. Their thresholds are not a frozen model SQI policy.

## Aggregate output

- exact participant and file counts;
- glucose missingness, minimum, maximum, mean, standard deviation, quantiles, and ECDF-ready values;
- counts under clearly named candidate clinical threshold schemes;
- participant support for every candidate category;
- duration, implied-rate, channel-integrity, non-finite, flatline, extrema, and pulse-screen summaries;
- all exclusions and unresolved anomalies.

Candidate category counts are sensitivity evidence only. The project lead must review their source, participant support, and claim consequences before any State label is frozen.

## Exit gate

The audit passes only when all 252 metadata IDs are accounted for, identifier joins are unambiguous, every participant has four real channels, corrupt or missing records are listed, glucose support is quantified, and the generated report is reproducible from the verified archive.

## Artifacts

- `reports/audits/hbppg_participants.csv`
- `reports/audits/hbppg_audit.json`
- `reports/audits/hbppg_audit.md`

