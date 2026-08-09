#!/usr/bin/env python3
"""Offline revalidator for Stage F Mode-II H1 endpoint sweep jobs.

Revalidates evidence bundles without re-running Abaqus or overwriting original evidence files.
Outputs revalidation results to runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/revalidation/<job_id>/REVALIDATION_RESULTS.json.
"""


import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
from scripts.validation.validate_mode_ii_h1_results import validate_results

SWEEP_EVIDENCE_DIR = ROOT / "runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/evidence"
REVAL_BASE_DIR = ROOT / "runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/revalidation"

JOB_TARGETS = {
    "1379481.mmaster02": 0.015,
    "1379482.mmaster02": 0.020,
    "1379483.mmaster02": 0.030,
    "1379484.mmaster02": 0.040,
}


def main() -> int:
    all_passed = True
    summary = {}

    for job_id, target_u1 in JOB_TARGETS.items():
        ev_dir = SWEEP_EVIDENCE_DIR / job_id
        if not ev_dir.is_dir():
            print(f"Error: evidence directory missing for {job_id}: {ev_dir}")
            return 1

        reval_dir = REVAL_BASE_DIR / job_id
        reval_dir.mkdir(parents=True, exist_ok=True)
        reval_json_path = reval_dir / "REVALIDATION_RESULTS.json"

        # Both Abaqus and extractor finished cleanly with exit code 0
        res = validate_results(
            evidence_dir=ev_dir,
            abaqus_return_code=0,
            extractor_return_code=0,
            expected_u1_target=target_u1,
            output_json_path=reval_json_path,
        )

        summary[job_id] = {
            "target_u1_mm": target_u1,
            "technical_pass": res["technical_pass"],
            "validator_return_code": res["validator_return_code"],
            "physical_classification": res["classification"],
            "warnings": res["warnings"],
            "max_sdv15": res["max_sdv15"],
            "min_sdv15": res["min_sdv15"],
            "final_rf1_kn": res["final_rf1_kn"],
            "pct_force_drop": res["percentage_force_drop"],
            "revalidation_json": str(reval_json_path.relative_to(ROOT)),
        }

        print(f"Job {job_id} (u1={target_u1}mm):")
        print(f"  technical_pass = {res['technical_pass']}")
        print(f"  validator_return_code = {res['validator_return_code']}")
        print(f"  physical_classification = {res['classification']}")
        print(f"  warnings = {res['warnings']}")
        print(f"  max_sdv15 = {res['max_sdv15']}")

        if not res["technical_pass"]:
            all_passed = False

    summary_json_path = REVAL_BASE_DIR / "SWEEP_REVALIDATION_SUMMARY.json"
    summary_json_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\nSaved revalidation summary to {summary_json_path.relative_to(ROOT)}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
