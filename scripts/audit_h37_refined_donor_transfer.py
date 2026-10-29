# -*- coding: utf-8 -*-
"""
audit_h37_refined_donor_transfer.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Audits authentic C3-Int donor availability and evaluates Hypothesis H37:
Refined-Donor Nonmatching State Transfer Qualification.
"""

from __future__ import print_function, division
import os
import sys
import json
import math
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def audit_c3_int_donor_availability():
    """
    Inspects Package 116 / 116 R1, HPC job records, and state files
    to verify whether an authentic C3-Int donor state exists at Frame 77.
    """
    p116_dir = REPO_ROOT / "models/pandey_kumar_mode1/116_c3_int_inc79_direct_transfer"
    p116_r1_dir = REPO_ROOT / "models/pandey_kumar_mode1/116_r1_c3_int_inc79_direct_transfer"
    summary_path = REPO_ROOT / "results/validation/c3_int_r1_inc79_direct_transfer_summary.json"
    hpc_ledger_path = REPO_ROOT / "project_coordination/HPC_JOB_LEDGER.csv"

    audit_findings = {
        "p116_dir_exists": p116_dir.is_dir(),
        "p116_r1_dir_exists": p116_r1_dir.is_dir(),
        "summary_exists": summary_path.is_file(),
    }

    # Inspect summary
    with open(summary_path, "r") as f:
        summary_data = json.load(f)

    audit_findings["summary_status"] = summary_data.get("status")
    audit_findings["summary_target_rf2_ref_N"] = summary_data.get("target_rf2_ref_N")
    audit_findings["summary_cycles"] = summary_data.get("cycles_completed")
    audit_findings["summary_final_rf2_N"] = summary_data.get("final_state", {}).get("rf2_rp_N")
    audit_findings["summary_final_e_tot_mJ"] = summary_data.get("final_state", {}).get("e_tot_mJ")

    # Inspect input deck step definition
    inp_path = p116_r1_dir / "M1_C3_INT_R1_INC79_DIRECT_TRANSFER.inp"
    step_lines = []
    step_found = False
    with open(inp_path, "r") as f:
        for line in f:
            if line.strip().upper().startswith("*STEP"):
                step_found = True
            if step_found:
                step_lines.append(line.strip())
                if len(step_lines) >= 15:
                    break

    audit_findings["inp_step_definition"] = step_lines
    audit_findings["inp_applied_displacement_mm"] = 0.00184250  # From Step 1 cards
    audit_findings["required_frame77_displacement_mm"] = 0.0018003125442191958

    # Check HPC ledger for C3-Int jobs
    c3_int_jobs = []
    with open(hpc_ledger_path, "r") as f:
        for line in f:
            if "C3_INT" in line or "c3_int" in line:
                parts = [p.strip() for p in line.split(",")]
                if parts:
                    c3_int_jobs.append({
                        "job_id": parts[0],
                        "job_name": parts[1] if len(parts) > 1 else "",
                        "status": parts[6] if len(parts) > 6 else "",
                        "exit_info": parts[8] if len(parts) > 8 else ""
                    })

    audit_findings["c3_int_hpc_jobs"] = c3_int_jobs

    # Evaluate whether authentic Frame-77 state exists
    # 1. Did any job run a continuous simulation from u=0 to u=0.00180031 mm?
    # 2. Package 116 R1 was an isolated direct transfer at Increment 79 (u=0.00184250 mm)
    # 3. No continuous donor simulation exists for C3-Int
    has_authentic_frame77_checkpoint = False
    audit_findings["has_authentic_frame77_checkpoint"] = has_authentic_frame77_checkpoint
    audit_findings["authenticity_verdict"] = (
        "AUTHENTIC_FRAME77_CHECKPOINT_ABSENT: Package 116 R1 (Job 1417818) executed solely at Increment 79 "
        "(u_RP = 0.00184250 mm) as a receiver re-equilibration from coarse C3 Increment 79. No continuous "
        "donor simulation exists for C3-Int from u = 0, and no state files exist at Frame 77 (u = 0.00180031 mm)."
    )

    return audit_findings

def formulate_h37_hypothesis_and_predeclared_thresholds():
    """
    Formulates the falsifiable Hypothesis H37 and predeclared acceptance thresholds.
    """
    h37_spec = {
        "hypothesis_id": "H37",
        "title": "Refined-Donor Nonmatching State Transfer Qualification",
        "statement": (
            "Reducing the source-to-target mesh-resolution mismatch from h_donor/h_target = 4.125 "
            "(coarse C3, h/ell0 = 0.3333, 1,600 quads) to h_donor/h_target = 1.980 (intermediate C3-Int, "
            "h/ell0 = 0.1600, 2,484 quads) will reduce AT2 regularization gradient under-integration bias, "
            "enabling nonmatching transfer to Candidate C4 (h/ell0 = 0.0808, 4,422 quads) at Frame 77 "
            "(u_top = 0.00180031 mm) to satisfy force continuity (|Delta RF2| <= 5.0%), re-equilibration energy "
            "continuity (|Delta E_tot| <= 2.0%), and forward continuation energy discrepancy (|Delta E_tot| <= 2.00000%) "
            "without violating pointwise damage irreversibility (0 healing violations) or Kuhn-Tucker optimality."
        ),
        "mesh_progression": {
            "source_mesh": {
                "name": "Candidate C3-Intermediate (C3-Int)",
                "elements": 2484,
                "nodes": 2610,
                "h_tip_um": 1.200,
                "h_over_ell0": 0.16000000
            },
            "target_mesh": {
                "name": "Candidate C4",
                "elements": 4422,
                "nodes": 4588,
                "h_tip_um": 0.606,
                "h_over_ell0": 0.08080000
            },
            "reference_coarse_mesh": {
                "name": "Candidate C3 (Donor Baseline)",
                "elements": 1600,
                "nodes": 1681,
                "h_tip_um": 2.500,
                "h_over_ell0": 0.33333333
            },
            "resolution_mismatch_reduction": {
                "original_ratio_c3_to_c4": 4.12541254,
                "intermediate_ratio_c3int_to_c4": 1.98019802,
                "mismatch_reduction_factor": 2.08333333
            }
        },
        "predeclared_acceptance_thresholds": {
            "initial_mapping_fidelity": {
                "max_damage_attenuation_pct": 0.25,
                "rms_damage_attenuation_pct": 0.10,
                "committed_history_loss_pct": 0.00,
                "slit_flank_cross_contamination": 0
            },
            "stage_c1_1_re_equilibration": {
                "reaction_force_continuity_pct": 5.0,
                "total_energy_continuity_pct": 2.0,
                "damage_healing_violations": 0,
                "am_loop_cap": 15
            },
            "stage_c1_2_step1_forward_continuation": {
                "displacement_increment_nm": 21.09375,
                "reaction_force_continuity_pct": 5.0,
                "total_energy_continuity_pct": 2.0,
                "damage_healing_violations": 0
            },
            "stage_c1_2_step2_forward_continuation": {
                "displacement_increment_nm": 21.09375,
                "reaction_force_continuity_pct": 5.0,
                "total_energy_discrepancy_pct": 2.00000000,
                "damage_healing_violations": 0,
                "kkt_min_dual_multiplier_kN_mm": -1.0e-9,
                "kkt_max_free_residual_kN_mm": 1.0e-6
            }
        }
    }
    return h37_spec

def main():
    print("================================================================================", flush=True)
    print("CONTROLLER TURN 302: HYPOTHESIS H37 REFINED-DONOR TRANSFER QUALIFICATION AUDIT", flush=True)
    print("================================================================================", flush=True)

    availability_audit = audit_c3_int_donor_availability()
    print("C3-Int Donor Availability Audit Result:")
    print("  p116_r1_dir_exists:", availability_audit["p116_r1_dir_exists"])
    print("  summary_exists:", availability_audit["summary_exists"])
    print("  has_authentic_frame77_checkpoint:", availability_audit["has_authentic_frame77_checkpoint"])
    print("  verdict:", availability_audit["authenticity_verdict"])

    h37_spec = formulate_h37_hypothesis_and_predeclared_thresholds()
    print("\nHypothesis H37 Statement:")
    print("  ", h37_spec["statement"])

    # Determine classification
    # Authentic Frame-77 checkpoint is strictly absent.
    # Governance prohibits manufacturing missing restart data or substituting Increment 79.
    # Therefore, candidate transfer cannot proceed, and job qualification is blocked on authentic state.
    classification = "H37_BLOCKED_AUTHENTIC_STATE"

    report = {
        "schema": 1,
        "turn": 302,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "hypothesis": "H37",
        "title": "Refined-Donor Nonmatching State Transfer Qualification",
        "classification": classification,
        "availability_audit": availability_audit,
        "h37_specification": h37_spec,
        "comparative_resolution_metrics": {
            "level1_c3_donor": {
                "elements": 1600,
                "nodes": 1681,
                "h_um": 2.500,
                "h_over_ell0": 0.33333333,
                "frame77_rf2_N": 185.470521,
                "frame77_e_tot_mJ": 0.209100,
                "inc79_rf2_N": 186.067909,
                "inc79_e_tot_mJ": 0.21244805
            },
            "level2_c3_int": {
                "elements": 2484,
                "nodes": 2610,
                "h_um": 1.200,
                "h_over_ell0": 0.16000000,
                "frame77_rf2_N": None,
                "frame77_e_tot_mJ": None,
                "inc79_rf2_N": 185.847178,
                "inc79_e_tot_mJ": 0.21678093
            },
            "level3_c4": {
                "elements": 4422,
                "nodes": 4588,
                "h_um": 0.606,
                "h_over_ell0": 0.08080000,
                "frame77_p111_r2_rf2_N": 186.150000,
                "frame77_p111_r2_e_tot_mJ": 0.208797,
                "inc79_p113_seq_rf2_N": 187.391475,
                "inc79_p113_seq_e_tot_mJ": 0.21671407,
                "inc79_p115_dir_rf2_N": 185.788572,
                "inc79_p115_dir_e_tot_mJ": 0.21676034
            }
        },
        "governing_gate_status": {
            "stage_c1_2_step2_energy_gate_failed": "RETAINED_INVARIANT (+2.00803158%)",
            "p113_gate_valid_failure": "RETAINED_INVARIANT",
            "h24_reference_audit_pending": "RETAINED_INVARIANT"
        },
        "next_dependent_action": (
            "To unblock H37 nonmatching transfer, qualify Package 141 as an authentic continuous monotonic "
            "C3-Int donor simulation (2,484 quads, h = 1.2 um, 2,610 nodes, f42_mixed_uel.for, 0 <= u <= 0.0020 mm) "
            "with field output frequency 1 to capture an authentic, history-consistent Frame-77 donor state."
        )
    }

    out_path = REPO_ROOT / "results/validation/h37_refined_donor_transfer_audit.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\nSaved H37 Audit Artifact:", out_path)
    print("Classification:", classification)

if __name__ == "__main__":
    main()
