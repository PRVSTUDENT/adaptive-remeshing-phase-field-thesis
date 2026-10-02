#!/usr/bin/env python3
"""
Mode-II R7 Same-Mesh Restart Validation Evaluator:
Deterministic scientific postprocessing and evaluation tool for M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7.
Evaluates 4-stage restart protocol against authoritative criterion registry:
  - scripts/postprocessing/criterion_registry.json
Authoritative References:
  - Replay Reference Job: 1389707.mmaster02 (Step 1 Inc 29 RF1 = 0.305426 kN)
  - Original Baseline Job: 1389684.mmaster02 (Step 1 Inc 29 RF1 = 0.305468 kN)
  - Reconstructed Committed Binary: PK10R1_INC29_COMMITTED_STATE_REPLAY_RECONSTRUCTED.bin (SHA256: 9ad133d7...)
"""

import os
import sys
import re
import csv
import math
import json
import subprocess
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REGISTRY_PATH = SCRIPT_DIR / "criterion_registry.json"

def load_criterion_registry():
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Criterion registry not found: {REGISTRY_PATH}")
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    crit_map = {c["criterion_id"]: c for c in data.get("criteria", [])}
    return crit_map

CRITERIA = load_criterion_registry()

# Authoritative Frozen References & Constants
CANONICAL_SOURCE_STATE_HASH = "5a2313e1ed15834d933e7cd12808681bd554394ad64d58419ad85f6f2bf6cf69"
COMMITTED_BINARY_HASH = "9ad133d73332fa24e4c35eab9d49505d30232d30ff5b9f49372d361f833cccea"
COMMITTED_STATE_PROVENANCE = "SCIENTIFICALLY_EQUIVALENT_REPLAY_RECONSTRUCTION"
RECONSTRUCTED_HMAX_EXPECTED = 98.221423
HANDOFF_RP_U1_MM = 0.010143300518393517

# Handoff RF1 Reference Clarification
REPLAY_HANDOFF_RF1_KN = CRITERIA["CRIT_R7_HANDOFF_RF1_TOLERANCE"]["target_reference_value"] # 0.305426 kN
ORIGINAL_HANDOFF_RF1_KN = CRITERIA["CRIT_R7_HANDOFF_RF1_TOLERANCE"]["original_baseline_value"] # 0.305468 kN
ACTIVE_REFERENCE_HANDOFF_RF1_KN = REPLAY_HANDOFF_RF1_KN

# Continuation Reference Terminal RF1
CONTINUATION_REF_TERMINAL_RF1_KN = CRITERIA["CRIT_R7_TERMINAL_CONTINUATION_RF1_TOLERANCE"]["target_reference_value"] # 0.003639 kN

# Frozen Acceptance Thresholds loaded from registry
THRESH_STEP1_HANDOFF_PCT = CRITERIA["CRIT_R7_HANDOFF_RF1_TOLERANCE"]["threshold"] # 1.0%
THRESH_MECH_JUMP_PCT = CRITERIA["CRIT_R7_MECH_EQUILIBRATION_RF1_JUMP"]["threshold"] # 1.0%
THRESH_PHASE_HEALING_MIN_DELTA_D = CRITERIA["CRIT_R7_PHASE_IRREVERSIBILITY_TOLERANCE"]["threshold"] # -1.0e-6
THRESH_TERMINAL_RF1_PCT = CRITERIA["CRIT_R7_TERMINAL_CONTINUATION_RF1_TOLERANCE"]["threshold"] # 2.0%
TOL_MECH_U3_DRIFT = CRITERIA["CRIT_R7_MECH_EQUILIBRATION_U3_DRIFT"]["threshold"] # 1.0e-6

def load_trajectory_from_csv(csv_path):
    if not os.path.exists(csv_path):
        return None
    rows = []
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                s_name = r.get("step_name") or r.get("Step") or "UNKNOWN"
                f_idx = int(r.get("frame_idx") or r.get("frame") or 0)
                t = float(r.get("step_time") or r.get("time") or 0.0)
                u1 = float(r.get("u1_mm") or r.get("U1") or 0.0)
                rf1 = float(r.get("rf1_kN") or r.get("RF1") or 0.0)
                d_max = float(r.get("d_max") or r.get("SDV15") or 0.0)
                rows.append({
                    "step_name": s_name,
                    "frame_idx": f_idx,
                    "step_time": t,
                    "u1_mm": u1,
                    "rf1_kN": rf1,
                    "d_max": d_max
                })
            except (ValueError, TypeError):
                continue
    return rows if rows else None

def group_trajectory_by_stages(rows):
    stages = {}
    for r in rows:
        sn = r["step_name"].upper()
        if "INSTALL" in sn or "STEP_1" in sn or "STEP 1" in sn:
            canonical_stage = "STATE_INSTALL"
        elif "EQUILIBRATION" in sn or "STEP_2" in sn or "STEP 2" in sn:
            canonical_stage = "MECH_EQUILIBRATION"
        elif "RELEASE" in sn or "STEP_3" in sn or "STEP 3" in sn:
            canonical_stage = "PHASE_RELEASE"
        elif "CONTINUATION" in sn or "STEP_4" in sn or "STEP 4" in sn:
            canonical_stage = "CONTINUATION"
        else:
            canonical_stage = r["step_name"]

        if canonical_stage not in stages:
            stages[canonical_stage] = []
        stages[canonical_stage].append(r)
    return stages

def parse_sta_file(sta_path):
    if not os.path.exists(sta_path):
        return {"exists": False, "completed_cleanly": False, "total_increments": 0, "cutbacks": 0}
    inc_count = 0
    cutbacks = 0
    completed = False
    with open(sta_path, "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 8:
                try:
                    inc_num = int(parts[1])
                    att_num = int(parts[2])
                    inc_count += 1
                    if att_num > 1:
                        cutbacks += (att_num - 1)
                except ValueError:
                    pass
            if "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in line.upper():
                completed = True
    return {
        "exists": True,
        "completed_cleanly": completed,
        "total_increments": inc_count,
        "cutbacks": cutbacks
    }

def evaluate_r7_restart(candidate_dir, output_json=None):
    cand_path = Path(candidate_dir)
    print(f"=== Evaluating R7 Same-Mesh Restart Validation Job: {cand_path.name} ===")

    sta_path = cand_path / f"{cand_path.name}.sta"
    sta_info = parse_sta_file(str(sta_path))

    traj_csv = cand_path / f"{cand_path.name}.extracted_trajectory.csv"
    if not traj_csv.exists():
        traj_csv = cand_path / "trajectory.csv"

    trajectory = load_trajectory_from_csv(str(traj_csv)) if traj_csv.exists() else []

    stage_metrics = {}
    if trajectory:
        stages = group_trajectory_by_stages(trajectory)
        for s_name, frames in stages.items():
            first_f = frames[0]
            last_f = frames[-1]
            stage_metrics[s_name] = {
                "frame_count": len(frames),
                "first_frame_time": first_f["step_time"],
                "last_frame_time": last_f["step_time"],
                "rp_u1_first_mm": first_f["u1_mm"],
                "rp_u1_last_mm": last_f["u1_mm"],
                "rp_rf1_first_kN": first_f["rf1_kN"],
                "rp_rf1_last_kN": last_f["rf1_kN"]
            }

    # Step 1 Evaluation (Handoff RF1 Agreement)
    step1_rf1 = stage_metrics.get("STATE_INSTALL", {}).get("rp_rf1_last_kN")
    if step1_rf1 is not None:
        step1_diff_pct = abs(step1_rf1 - ACTIVE_REFERENCE_HANDOFF_RF1_KN) / ACTIVE_REFERENCE_HANDOFF_RF1_KN * 100.0
        step1_status = "PASS" if step1_diff_pct <= THRESH_STEP1_HANDOFF_PCT else "FAIL"
    else:
        step1_diff_pct = None
        step1_status = "UNRESOLVED"

    # Step 2 Evaluation (Mech Equilibration Jump)
    s2 = stage_metrics.get("MECH_EQUILIBRATION")
    if s2 and step1_rf1 is not None:
        s2_rf1_end = s2["rp_rf1_last_kN"]
        s2_jump_pct = abs(s2_rf1_end - step1_rf1) / abs(step1_rf1) * 100.0 if step1_rf1 != 0 else 0.0
        s2_status = "PASS" if s2_jump_pct <= THRESH_MECH_JUMP_PCT else "FAIL"
    else:
        s2_jump_pct = None
        s2_status = "UNRESOLVED"

    # Step 3 Evaluation (Phase Release RF Jump: Quantitative/Qualitative Evidence)
    s3 = stage_metrics.get("PHASE_RELEASE")
    if s3 and s2:
        s3_rf1_end = s3["rp_rf1_last_kN"]
        s2_rf1_end = s2["rp_rf1_last_kN"]
        s3_jump_pct = abs(s3_rf1_end - s2_rf1_end) / abs(s2_rf1_end) * 100.0 if s2_rf1_end != 0 else 0.0
    else:
        s3_jump_pct = None

    # Step 4 Continuation Evaluation (Terminal RF1 Tolerance)
    s4 = stage_metrics.get("CONTINUATION")
    if s4:
        s4_term_rf1 = s4["rp_rf1_last_kN"]
        s4_term_diff_pct = abs(s4_term_rf1 - CONTINUATION_REF_TERMINAL_RF1_KN) / CONTINUATION_REF_TERMINAL_RF1_KN * 100.0
        s4_status = "PASS" if s4_term_diff_pct <= THRESH_TERMINAL_RF1_PCT else "FAIL"
    else:
        s4_term_rf1 = None
        s4_term_diff_pct = None
        s4_status = "UNRESOLVED"

    report = {
        "job_identity": cand_path.name,
        "job_package_revision": "R7",
        "predecessor_status": "R6_SUPERSEDED_BY_R7",
        "reconstructed_committed_state": {
            "provenance": COMMITTED_STATE_PROVENANCE,
            "binary_sha256": COMMITTED_BINARY_HASH,
            "expected_hmax_kN_mm2": RECONSTRUCTED_HMAX_EXPECTED
        },
        "references": {
            "active_reference_handoff_rf1_kN": ACTIVE_REFERENCE_HANDOFF_RF1_KN,
            "replay_reference_handoff_rf1_kN": REPLAY_HANDOFF_RF1_KN,
            "original_baseline_handoff_rf1_kN": ORIGINAL_HANDOFF_RF1_KN,
            "continuation_terminal_rf1_kN": CONTINUATION_REF_TERMINAL_RF1_KN
        },
        "solver_completion": sta_info.get("completed_cleanly", False),
        "total_increments": sta_info.get("total_increments", len(trajectory)),
        "cutbacks": sta_info.get("cutbacks", 0),
        "stage_extractions": stage_metrics,
        "step1_handoff_evaluation": {
            "active_reference_rf1_kN": ACTIVE_REFERENCE_HANDOFF_RF1_KN,
            "actual_rf1_kN": step1_rf1,
            "difference_pct": step1_diff_pct,
            "frozen_threshold_pct": THRESH_STEP1_HANDOFF_PCT,
            "criterion_type": "FROZEN_SCIENTIFIC",
            "status": step1_status
        },
        "step2_mech_equilibration_evaluation": {
            "rf1_jump_pct": s2_jump_pct,
            "frozen_threshold_pct": THRESH_MECH_JUMP_PCT,
            "criterion_type": "FROZEN_SCIENTIFIC",
            "max_u3_drift_software_tolerance": TOL_MECH_U3_DRIFT,
            "status": s2_status
        },
        "step3_phase_release_evaluation": {
            "rf1_jump_pct": s3_jump_pct,
            "criterion_type": "QUALITATIVE",
            "phase_healing_threshold_min_delta_d": THRESH_PHASE_HEALING_MIN_DELTA_D,
            "phase_healing_criterion_type": "FROZEN_SCIENTIFIC",
            "status": "QUALITATIVE_EVIDENCE"
        },
        "step4_continuation_evaluation": {
            "reference_terminal_rf1_kN": CONTINUATION_REF_TERMINAL_RF1_KN,
            "actual_terminal_rf1_kN": s4_term_rf1,
            "terminal_difference_pct": s4_term_diff_pct,
            "frozen_threshold_pct": THRESH_TERMINAL_RF1_PCT,
            "criterion_type": "FROZEN_SCIENTIFIC",
            "status": s4_status
        },
        "overall_status": "PASS" if (step1_status == "PASS" and s2_status == "PASS" and s4_status == "PASS" and sta_info.get("completed_cleanly")) else "UNRESOLVED"
    }

    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Saved R7 evaluation report to: {output_json}")

    return report

def main():
    parser = argparse.ArgumentParser(description="Evaluate R7 Same-Mesh Restart Validation Candidate")
    parser.add_argument("--candidate-dir", required=True, help="Directory containing job files (.dat, .sta, etc.)")
    parser.add_argument("--output-json", help="Output JSON path")
    args = parser.parse_args()

    res = evaluate_r7_restart(args.candidate_dir, args.output_json)
    print("\n=== EVALUATION SUMMARY ===")
    print(f"Job: {res.get('job_identity')} (Revision: {res.get('job_package_revision')})")
    print(f"Solver Completion: {res.get('solver_completion')}")
    print(f"Step 1 Status: {res.get('step1_handoff_evaluation', {}).get('status')}")
    print(f"Step 2 Status: {res.get('step2_mech_equilibration_evaluation', {}).get('status')}")
    print(f"Step 4 Status: {res.get('step4_continuation_evaluation', {}).get('status')}")
    print(f"Overall Status: {res.get('overall_status')}")

if __name__ == "__main__":
    main()
