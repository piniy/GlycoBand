"""Run the config-driven Hb-PPG v6 raw-data audit."""

from __future__ import annotations

from pathlib import Path

from glycoband.datasets.hbppg import audit_hbppg, load_config, write_hbppg_artifacts


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    config = load_config(repo_root / "configs/audits/hbppg.yaml")
    dataset_root = repo_root / "data/raw/hbppg/v6/Hb_PPG_Dataset"
    participants, summary = audit_hbppg(dataset_root, config)
    write_hbppg_artifacts(dataset_root, participants, summary, repo_root / "reports")
    print(
        "Hb-PPG audit complete: "
        f"{summary['participant_inventory']['metadata']} participants, "
        f"{summary['glucose_mmol_l']['valid']} numeric glucose references"
    )


if __name__ == "__main__":
    main()

