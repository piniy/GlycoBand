# Hb-PPG v6 Raw-Data Audit

## Verdict

The audit accounted for 252 metadata participants, 252 CSV files, and 252 MAT files. 217 participants have numeric fasting-glucose references; 35 do not. This report does not freeze a State label or split.

## Inventory and joins

- Metadata without CSV: `[]`
- CSV without metadata: `[]`
- Metadata without MAT: `[]`
- MAT without metadata: `[]`
- Four-channel schema valid: 252
- Passed descriptive signal screens: 252
- Eligible reference + signal records for State review: 217
- Flagged for explicit review: 35

## Glucose support

- Numeric: 217
- Missing/non-numeric: 35
- Mean: 5.336 mmol/L
- Minimum / median / maximum: 3.890 / 5.070 / 13.540 mmol/L

## Candidate category sensitivity

- `ada_fpg_ranges`: NORMAL_RANGE=171, PREDIABETES_RANGE=32, DIABETES_RANGE=14 (sensitivity only; source in config)
- `who_fpg_ranges`: BELOW_IFG_THRESHOLD=193, DIABETES_RANGE=14, IFG_RANGE=10 (sensitivity only; source in config)
- `low_glucose_screen`: AT_OR_ABOVE_3_9=216, BELOW_3_9=1 (sensitivity only; source in config)

These are descriptive counts under external threshold schemes. They are not diagnoses and are
not an approved project label. Repeat-testing and clinical-context requirements are outside this
dataset.

## Signal observations

- Declared duration counts: `{'60.0': 201, '40.0': 12, '35.0': 11, '50.0': 9, '45.0': 9, '30.0': 6, '55.0': 4}`
- Implied rate min / median / max: 200.000 / 200.000 / 200.000 Hz
- Participant-level flags and channel metrics: `hbppg_participants.csv`

## Gate consequence

This audit supplies evidence for human review. It does not authorize label freeze, split creation,
architecture selection, model training, or final-test access.
