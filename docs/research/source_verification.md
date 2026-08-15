# GlycoBand Source Verification

## Decision

Only these sources are approved for the current core research scope:

| Task | Dataset | Exact version | Official identifier | Access and license |
|---|---|---|---|---|
| Fasting State | Hb-PPG | Figshare v6 | `10.6084/m9.figshare.22256143.v6` | Public; CC BY 4.0 |
| Recent Trend | BIG IDEAs | PhysioNet v1.1.3 | `10.13026/aw6y-fc44` | Open access; ODC Attribution v1.0 |

PhysioCGM remains outside core training, validation, and synthetic-testing scope.

## Verified inventory

### Hb-PPG v6

- Official metadata: `https://api.figshare.com/v2/articles/22256143/versions/6`
- Archive: `Hb_PPG_Dataset.zip`
- Archive bytes: `46,787,781`
- Official MD5: `59bd26271695e5e9ada8e42c841568b5`
- Project-observed ZIP contents: 506 files and 164,727,880 uncompressed bytes.
- Project-observed structure: 252 CSV signals, 252 MAT signals, one README, and one subject-information workbook.
- CSV channel header: `660nm,730nm,850nm,940nm`.

The downloaded archive matched both the official byte size and MD5 on 2026-08-15.

### BIG IDEAs v1.1.3

- Official page: `https://physionet.org/content/big-ideas-glycemic-wearable/1.1.3/`
- ZIP bytes from the official endpoint: `5,015,250,233`.
- Reported uncompressed size: 34.1 GB.
- Participants: folders `001` through `016`.
- Core files: one BVP CSV and one Dexcom CSV per participant.
- Official file-level checksums: `SHA256SUMS.txt` at the versioned PhysioNet file path.
- License: Open Data Commons Attribution License v1.0.

PhysioNet does not publish an archive-level checksum on the dataset page. After extraction, every file must match the official file-level SHA-256 manifest before Gate C auditing begins.

## Storage budget

The Gate B budget retains both source ZIP files, extracted sources, and a 10,000,000,000-byte working reserve:

```text
source archives                       5,062,038,014 bytes
reported/verified extracted sources 34,264,727,880 bytes
working reserve                      10,000,000,000 bytes
--------------------------------------------------------
total planned footprint             49,326,765,894 bytes
```

The reserve covers extraction recovery, audit tables, and temporary processing. Synthetic robustness datasets are outside this readiness-stage budget and require a later storage review.

## Download authority

The project lead authorized downloading all datasets required by the current scope on 2026-08-15. This covers Hb-PPG v6 and BIG IDEAs v1.1.3 only; it does not authorize adding a new dataset or changing the scientific architecture.

## Reproduction

Run:

```powershell
uv run --frozen python scripts/verify_sources.py
```

The command verifies live metadata, the local Hb-PPG archive, the BIG IDEAs ZIP endpoint, the official checksum manifest, the license file, and current storage headroom. It writes `data/manifests/source_manifest.json`.
