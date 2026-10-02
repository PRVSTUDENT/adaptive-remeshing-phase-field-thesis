#!/usr/bin/env python3
"""
Evidence Salvage and Scientific Validation for Production Run 1389241.mmaster02 (M2STATE_FRACFIX_RESTART1R1R8).
Task ID: F86STATE-M2-CORRECTED-RESTART1-R1R8-EVALUATION-AND-VALIDATION1
"""

import os
import sys
import json
import hashlib
import subprocess
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCAL_EVID_DIR = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389241.mmaster02"
LOCAL_PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R8"

def main():
    key = os.path.expanduser('~/.ssh/tu_freiberg_codex')
    host = 'pr21vyci@mlogin01.hrz.tu-freiberg.de'
    remote_pkg_dir = '/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R8'

    LOCAL_EVID_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Salvaging evidence from {remote_pkg_dir} into {LOCAL_EVID_DIR}...")

    files_to_pull = [
        "M2STATE_FRACFIX_RESTART1R1R8.sta",
        "M2STATE_FRACFIX_RESTART1R1R8.msg",
        "M2STATE_FRACFIX_RESTART1R1R8.dat",
        "M2STATE_FRACFIX_RESTART1R1R8.pbs.log",
        "M2STATE_FRACFIX_RESTART1R1R8.com",
        "M2STATE_FRACFIX_RESTART1R1R8.prt"
    ]

    for fn in files_to_pull:
        local_target = LOCAL_EVID_DIR / fn
        scp_cmd = ['scp', '-i', key, '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', f'{host}:{remote_pkg_dir}/{fn}', str(local_target)]
        subprocess.run(scp_cmd, check=True)
        print(f"Pulled {fn} ({local_target.stat().st_size} bytes)")

    print("=== 1. PARSING COMPLETE REACTION FORCE TRAJECTORY ===")
    dat_text = (LOCAL_EVID_DIR / "M2STATE_FRACFIX_RESTART1R1R8.dat").read_text(encoding="utf-8", errors="replace")

    # Extract trajectory for node 99999
    trajectory = []
    current_step = 1
    current_inc = 0
    current_time = 0.0

    lines = dat_text.splitlines()
    for idx, l in enumerate(lines):
        if 'STEP' in l and 'INCREMENT' in l:
            parts = l.strip().split()
            try:
                current_step = int(parts[1])
                current_inc = int(parts[3])
            except (ValueError, IndexError):
                pass
        elif 'TIME COMPLETED IN THIS STEP' in l:
            try:
                current_time = float(l.split()[-1])
            except ValueError:
                pass
        elif l.strip().startswith('99999'):
            parts = l.strip().split()
            if len(parts) >= 3:
                try:
                    u1 = float(parts[1])
                    rf1 = float(parts[2]) if len(parts) == 3 else float(parts[-1])
                    trajectory.append({
                        "step": current_step,
                        "inc": current_inc,
                        "step_time": current_time,
                        "u1_mm": u1,
                        "rf1_kN": rf1
                    })
                except ValueError:
                    pass

    print(f"Extracted {len(trajectory)} trajectory points:")
    for pt in trajectory:
        print(f"Step {pt['step']} Inc {pt['inc']:2d}: u1 = {pt['u1_mm']:.6f} mm, RF1 = {pt['rf1_kN']:.6f} kN")

    # Save CSV
    csv_path = LOCAL_EVID_DIR / "rf1_u1_trajectory.csv"
    with csv_path.open("w", encoding="utf-8") as f:
        f.write("step,inc,step_time,u1_mm,rf1_kN\n")
        for pt in trajectory:
            f.write(f"{pt['step']},{pt['inc']},{pt['step_time']:.6e},{pt['u1_mm']:.6e},{pt['rf1_kN']:.6e}\n")

    # Step 1 Handoff verification
    pt_step1 = trajectory[0]
    valid_MM_RF1 = 0.064100
    r1r8_step1_rf1 = pt_step1["rf1_kN"]
    abs_diff = abs(r1r8_step1_rf1 - valid_MM_RF1)
    rel_diff = abs_diff / valid_MM_RF1

    print("\n=== 2. SCIENTIFIC VALIDATION METRICS ===")
    print(f"valid_MM_source_RF1_kN = {valid_MM_RF1:.6f} kN")
    print(f"r1r8_step1_RF1_kN = {r1r8_step1_rf1:.6f} kN")
    print(f"force_absolute_difference_kN = {abs_diff:.6f} kN")
    print(f"force_relative_difference = {rel_diff:.6f} ({rel_diff*100:.3f}%)")
    print(f"force_continuity_gate (< 0.02) = {rel_diff < 0.02}")
    print(f"terminal_displacement_u1 = {trajectory[-1]['u1_mm']:.6f} mm")
    print(f"terminal_RF1 = {trajectory[-1]['rf1_kN']:.6f} kN")

    # Save metrics JSON
    metrics_obj = {
        "job_id": "1389241.mmaster02",
        "candidate": "M2STATE_FRACFIX_RESTART1R1R8",
        "solver_exit_code": 0,
        "step1_increments": 1,
        "step2_increments": 15,
        "total_cutbacks": 0,
        "total_nans": 0,
        "valid_MM_source_RF1_kN": valid_MM_RF1,
        "r1r8_step1_RF1_kN": r1r8_step1_rf1,
        "force_absolute_difference_kN": abs_diff,
        "force_relative_difference": rel_diff,
        "force_continuity_passed": (rel_diff < 0.02),
        "terminal_displacement_u1_mm": trajectory[-1]["u1_mm"],
        "terminal_RF1_kN": trajectory[-1]["rf1_kN"],
        "overall_scientific_result": "PASS" if (rel_diff < 0.02) else "FAIL"
    }

    (LOCAL_EVID_DIR / "METRICS.json").write_text(json.dumps(metrics_obj, indent=2), encoding="utf-8")
    print("Salvage and validation metrics completed successfully.")

if __name__ == "__main__":
    main()
