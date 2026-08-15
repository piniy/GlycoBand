# BIG IDEAs v1.1.3 Raw-Data Audit

## Verdict

All 130 official files passed their published SHA-256 digests. The audit accounted for 16 participants. This report does not freeze a Trend label or chronological split.

## Coverage

- BVP rows: 600698901
- Numeric CGM EGV points: 36898
- Contiguous non-overlapping 30-second BVP windows: 312786
- Total BVP-CGM continuous overlap: 2419.45 hours
- Usable aligned 30-second window-hours: 2399.38 hours
- Participant-level details: `bigideas_participants.csv`

## Explicit anomalies

- BVP duplicate / backward timestamps: 0 / 1
- BVP gaps over policy: 140
- Constant BVP recordings: 0
- Invalid CGM timestamp / glucose rows: 0 / 0
- CGM duplicate / backward timestamps: 0 / 0
- CGM gaps over policy: 24

## Candidate Trend sensitivity

The complete H / threshold / smoothing grid is in `bigideas_trend_candidates.csv`. Counts are
reported by participant and must not be interpreted as independent-human counts. Every candidate
endpoint uses only past and present CGM and requires continuous BVP history.

## Gate consequence

This audit supplies evidence for human review. It does not authorize label freeze, split creation,
architecture selection, model training, or final-test access.
