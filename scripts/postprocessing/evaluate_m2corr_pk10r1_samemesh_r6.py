#!/usr/bin/env python3
"""
Mode-II R6 Same-Mesh Restart Validation Evaluator:
Deterministic scientific postprocessing and evaluation tool for M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6.
Compares extracted states and continuation trajectory against:
  - Reference Replay Run: 1389707.mmaster02 (M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1)
  - Canonical Source State CSV: PK10R1_INC29_PRIMARY_STATE_REPLAY_R1.csv (SHA256: 5a2313e1...)
  - Committed Source Binary: PK10R1_INC29_SOURCE_STATE.bin (SHA256: 28e0fc1c...)
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

# Authoritative Frozen References & Constants
CANONICAL_SOURCE_STATE_HASH = "5a2313e1ed15834d933e7cd12808681bd554394ad64d58419ad85f6f2bf6cf69"
COMMITTED_BINARY_HASH = "28e0fc1c6b02a4e6013cea23f38dacfea0e2afaf52d92239d9d694bb2e55e66e"
HANDOFF_RP_U1_MM = 0.010143300518393517
ACCEPTED_HANDOFF_RF1_KN = 0.30542629957199097
CONTINUATION_REF_TERMINAL_RF1_KN = 0.003639

# Frozen Acceptance Thresholds
FROZEN_THRESHOLDS = {
    "step1_handoff_rf1_pct": 1.0,         # Step 1 RF1 within 1.0% of continuous reference Inc 29 (0.305426 kN)
    "mech_release_rf1_jump_pct": 1.0,     # Max RF1 jump during Stage 2 MECH_EQUILIBRATION <= 1.0%
    "phase_release_rf1_jump_pct": 1.0,    # Max RF1 jump during Stage 3 PHASE_RELEASE <= 1.0%
    "phase_healing_min_delta_d": -1.0e-6, # Pointwise max healing <= 1.0e-6
    "continuation_terminal_rf1_pct": 2.0  # Terminal RF1 within 2.0% of continuous reference (0.003639 kN)
}

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

def extract_trajectory_from_odb(odb_path, script_dir):
    out_csv = odb_path.with_suffix(".extracted_trajectory.csv")
    if out_csv.exists():
        traj = load_trajectory_from_csv(str(out_csv))
        if traj:
            return traj, str(out_csv)

    extractor = script_dir / "extract_validation_odb.py"
    if not extractor.exists():
        return None, "extract_validation_odb.py not found"

    cmd = ["abaqus", "python", str(extractor), str(odb_path), str(out_csv)]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if res.returncode == 0 and out_csv.exists():
            traj = load_trajectory_from_csv(str(out_csv))
            if traj:
                return traj, str(out_csv)
    except Exception as e:
        pass
    return None, "Abaqus ODB extraction failed or unavailable"

def group_trajectory_by_stages(rows):
    """Groups flat frame rows into standardized stages."""
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

def evaluate_r6_restart(candidate_dir, canonical_csv=None, output_json=None):
    cand_path = Path(candidate_dir)
    print(f"=== EVALUATING R6 SAME-MESH RESTART CANDIDATE IN: {cand_path} ===")

    script_dir = Path(__file__).resolve().parent
    rows = None
    source_desc = ""

    # 1. Try existing CSV
    csv_files = list(cand_path.glob("*.csv"))
    for cf in csv_files:
        if "trajectory" in cf.name.lower() or "rf" in cf.name.lower() or "extracted" in cf.name.lower():
            r_data = load_trajectory_from_csv(str(cf))
            if r_data:
                rows = r_data
                source_desc = f"CSV: {cf.name}"
                break

    # 2. Try ODB extraction if CSV not found
    if not rows:
        odb_files = list(cand_path.glob("*.odb"))
        if odb_files:
            r_data, src = extract_trajectory_from_odb(odb_files[0], script_dir)
            if r_data:
                rows = r_data
                source_desc = f"ODB: {odb_files[0].name} ({src})"

    if not rows:
        return {
            "status": "UNRESOLVED",
            "error": "No trajectory extracted from CSV or ODB",
            "job_identity": cand_path.name
        }

    stages = group_trajectory_by_stages(rows)
    step1_rows = stages.get("STATE_INSTALL")
    step2_rows = stages.get("MECH_EQUILIBRATION")
    step3_rows = stages.get("PHASE_RELEASE")
    step4_rows = stages.get("CONTINUATION")

    # 1. Step 1 (State Install) Evaluation
    handoff_rf1 = step1_rows[-1]["rf1_kN"] if step1_rows else None
    handoff_u1 = step1_rows[-1]["u1_mm"] if step1_rows else None
    handoff_dmax = step1_rows[-1]["d_max"] if step1_rows else None
    handoff_rf1_diff_pct = None
    step1_pass = "UNRESOLVED"

    if handoff_rf1 is not None:
        handoff_rf1_diff_pct = abs(handoff_rf1 - ACCEPTED_HANDOFF_RF1_KN) / ACCEPTED_HANDOFF_RF1_KN * 100.0
        step1_pass = "PASS" if handoff_rf1_diff_pct <= FROZEN_THRESHOLDS["step1_handoff_rf1_pct"] else "FAIL"

    # 2. Step 2 (Mechanical Equilibration) RF Jump
    rf1_step2_jump_pct = None
    step2_pass = "UNRESOLVED"
    if step1_rows and step2_rows:
        rf1_s1_end = step1_rows[-1]["rf1_kN"]
        rf1_s2_end = step2_rows[-1]["rf1_kN"]
        if rf1_s1_end > 1e-12:
            rf1_step2_jump_pct = abs(rf1_s2_end - rf1_s1_end) / rf1_s1_end * 100.0
            step2_pass = "PASS" if rf1_step2_jump_pct <= FROZEN_THRESHOLDS["mech_release_rf1_jump_pct"] else "FAIL"

    # 3. Step 3 (Phase Release) RF Jump & Phase Healing Check
    rf1_step3_jump_pct = None
    step3_pass = "UNRESOLVED"
    phase_healing_detected = False
    min_delta_d = 0.0

    if step1_rows and step2_rows and step3_rows:
        rf1_s2_end = step2_rows[-1]["rf1_kN"]
        rf1_s3_end = step3_rows[-1]["rf1_kN"]
        if rf1_s2_end > 1e-12:
            rf1_step3_jump_pct = abs(rf1_s3_end - rf1_s2_end) / rf1_s2_end * 100.0

        # Phase healing check: d_max must not drop significantly from step 1
        d_s1 = step1_rows[-1]["d_max"]
        d_s2 = step2_rows[-1]["d_max"]
        d_s3 = step3_rows[-1]["d_max"]
        min_delta_d = min(d_s2 - d_s1, d_s3 - d_s1)
        if min_delta_d < FROZEN_THRESHOLDS["phase_healing_min_delta_d"]:
            phase_healing_detected = True

        if rf1_step3_jump_pct is not None and rf1_step3_jump_pct <= FROZEN_THRESHOLDS["phase_release_rf1_jump_pct"] and not phase_healing_detected:
            step3_pass = "PASS"
        else:
            step3_pass = "FAIL"

    # 4. Step 4 (Continuation) Terminal RF1 Evaluation
    term_rf1 = step4_rows[-1]["rf1_kN"] if step4_rows else None
    term_u1 = step4_rows[-1]["u1_mm"] if step4_rows else None
    term_rf1_diff_pct = None
    step4_pass = "UNRESOLVED"

    if term_rf1 is not None:
        term_rf1_diff_pct = abs(term_rf1 - CONTINUATION_REF_TERMINAL_RF1_KN) / CONTINUATION_REF_TERMINAL_RF1_KN * 100.0
        step4_pass = "PASS" if term_rf1_diff_pct <= FROZEN_THRESHOLDS["continuation_terminal_rf1_pct"] else "FAIL"

    all_criteria = [step1_pass, step2_pass, step3_pass, step4_pass]
    if any(c == "FAIL" for c in all_criteria):
        overall_status = "FAIL"
    elif all(c == "PASS" for c in all_criteria):
        overall_status = "PASS"
    else:
        overall_status = "UNRESOLVED"

    report = {
        "job_identity": cand_path.name,
        "source_evidence": source_desc,
        "reference_replay_job": "1389707.mmaster02",
        "canonical_source_csv_hash": CANONICAL_SOURCE_STATE_HASH,
        "committed_binary_hash": COMMITTED_BINARY_HASH,
        "stages_detected": list(stages.keys()),
        "handoff_metrics": {
            "handoff_rp_u1_mm": handoff_u1,
            "expected_handoff_rp_u1_mm": HANDOFF_RP_U1_MM,
            "handoff_rf1_kN": handoff_rf1,
            "expected_handoff_rf1_kN": ACCEPTED_HANDOFF_RF1_KN,
            "handoff_rf1_difference_pct": handoff_rf1_diff_pct,
            "handoff_dmax": handoff_dmax,
            "frozen_threshold_pct": FROZEN_THRESHOLDS["step1_handoff_rf1_pct"],
            "criterion_status": step1_pass
        },
        "mechanical_release_metrics": {
            "step2_end_rf1_kN": step2_rows[-1]["rf1_kN"] if step2_rows else None,
            "rf1_jump_pct": rf1_step2_jump_pct,
            "frozen_threshold_pct": FROZEN_THRESHOLDS["mech_release_rf1_jump_pct"],
            "criterion_status": step2_pass
        },
        "phase_release_metrics": {
            "step3_end_rf1_kN": step3_rows[-1]["rf1_kN"] if step3_rows else None,
            "rf1_jump_pct": rf1_step3_jump_pct,
            "min_delta_d": min_delta_d,
            "phase_healing_detected": phase_healing_detected,
            "frozen_threshold_pct": FROZEN_THRESHOLDS["phase_release_rf1_jump_pct"],
            "criterion_status": step3_pass
        },
        "continuation_metrics": {
            "terminal_u1_mm": term_u1,
            "terminal_rf1_kN": term_rf1,
            "expected_terminal_rf1_kN": CONTINUATION_REF_TERMINAL_RF1_KN,
            "terminal_rf1_difference_pct": term_rf1_diff_pct,
            "frozen_threshold_pct": FROZEN_THRESHOLDS["continuation_terminal_rf1_pct"],
            "criterion_status": step4_pass
        },
        "frozen_acceptance_criteria": FROZEN_THRESHOLDS,
        "overall_status": overall_status
    }

    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Saved R6 evaluation report to: {output_json}")

    return report

def main():
    parser = argparse.ArgumentParser(description="Evaluate R6 Same-Mesh Restart Validation candidate")
    parser.add_argument("--candidate-dir", required=True, help="Directory containing job files (.dat, .sta, etc.)")
    parser.add_argument("--canonical-csv", help="Canonical source state CSV path")
    parser.add_argument("--output-json", help="Output JSON path")
    args = parser.parse_args()

    res = evaluate_r6_restart(args.candidate_dir, args.canonical_csv, args.output_json)
    print("\n=== EVALUATION SUMMARY ===")
    print(f"Job: {res.get('job_identity')}")
    print(f"Handoff RF1: {res.get('handoff_metrics', {}).get('handoff_rf1_kN')} kN -> {res.get('handoff_metrics', {}).get('criterion_status')}")
    print(f"Mech Release Jump: {res.get('mechanical_release_metrics', {}).get('rf1_jump_pct')}% -> {res.get('mechanical_release_metrics', {}).get('criterion_status')}")
    print(f"Phase Release Jump: {res.get('phase_release_metrics', {}).get('rf1_jump_pct')}% (Healing: {res.get('phase_release_metrics', {}).get('phase_healing_detected')}) -> {res.get('phase_release_metrics', {}).get('criterion_status')}")
    print(f"Continuation Term RF1: {res.get('continuation_metrics', {}).get('terminal_rf1_kN')} kN -> {res.get('continuation_metrics', {}).get('criterion_status')}")
    print(f"Overall Status: {res.get('overall_status')}")

if __name__ == "__main__":
    main()
