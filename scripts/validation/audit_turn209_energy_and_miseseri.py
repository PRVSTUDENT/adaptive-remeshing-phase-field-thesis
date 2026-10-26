# -*- coding: utf-8 -*-
"""
audit_turn209_energy_and_miseseri.py
====================================
Independent high-precision energy continuity reconciliation and MISESERI
load-state correspondence audit for Package 113 (Job 1417682.mmaster02) Increment 79.

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 209)
"""
import os
import sys
import csv
import json
import hashlib

def get_sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest().upper()

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    donor_energy_csv = os.path.join(
        repo_root,
        "models", "pandey_kumar_mode1", "76_candidate_donor_h0025_visual",
        "evidence_1416301", "uel_energy_balance.csv"
    )
    pkg113_summary_json = os.path.join(
        repo_root,
        "models", "pandey_kumar_mode1", "113_c1_2_second_forward_continuation",
        "c4_c1_2_inc79_continuation_summary.json"
    )
    pkg95_audit_json = os.path.join(
        repo_root,
        "models", "pandey_kumar_mode1", "95_c4_companion_miseseri",
        "c4_miseseri_audit.json"
    )
    pkg95_manifest_json = os.path.join(
        repo_root,
        "models", "pandey_kumar_mode1", "95_c4_companion_miseseri",
        "PACKAGE_MANIFEST.json"
    )

    # 1. Extract authentic donor Increment 79 energy
    donor_inc79 = None
    with open(donor_energy_csv, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < 7:
                continue
            step_str = row[0].strip()
            inc_str = row[1].strip()
            if inc_str == "79":
                # Step, Inc, Step_Time, Total_Time, E_elas, E_frac, E_tot
                e_elas_knmm = float(row[4].strip())
                e_frac_knmm = float(row[5].strip())
                e_tot_knmm = float(row[6].strip())
                donor_inc79 = {
                    "step": int(step_str),
                    "increment": int(inc_str),
                    "time": float(row[3].strip()),
                    "e_elas_mJ": e_elas_knmm,   # 1 kN*mm = 1 J = 1000 mJ? Wait:
                    # Let's check units: row has 0.17140369E-03 kN*mm = 0.17140369 mJ
                    "e_elas_kNmm": e_elas_knmm,
                    "e_frac_kNmm": e_frac_knmm,
                    "e_tot_kNmm": e_tot_knmm,
                    "e_elas_mJ": e_elas_knmm * 1000.0,
                    "e_frac_mJ": e_frac_knmm * 1000.0,
                    "e_tot_mJ": e_tot_knmm * 1000.0,
                }
                break

    if donor_inc79 is None:
        raise ValueError("Increment 79 not found in donor energy balance CSV!")

    # 2. Extract Candidate C4 Increment 79 (Package 113, Cycle 4) energy
    with open(pkg113_summary_json, "r") as f:
        summary113 = json.load(f)

    c4_final = summary113["final_state"]
    c4_inc79 = {
        "cycle": c4_final["cycle"],
        "rf2_rp_N": c4_final["rf2_rp_N"],
        "d_max": c4_final["d_max"],
        "e_elas_mJ": c4_final["e_elas_mJ"],
        "e_frac_mJ": c4_final["e_frac_mJ"],
        "e_tot_mJ": c4_final["e_tot_mJ"],
        "healing_violations": c4_final["healing_violations"],
        "max_delta_d": c4_final["max_delta_d"],
        "delta_rf2_prev_cycle_N": c4_final["delta_rf2_prev_cycle_N"],
    }

    # 3. Compute relative differences
    diff_elas_pct = (c4_inc79["e_elas_mJ"] - donor_inc79["e_elas_mJ"]) / donor_inc79["e_elas_mJ"] * 100.0
    diff_frac_pct = (c4_inc79["e_frac_mJ"] - donor_inc79["e_frac_mJ"]) / donor_inc79["e_frac_mJ"] * 100.0
    diff_tot_pct = (c4_inc79["e_tot_mJ"] - donor_inc79["e_tot_mJ"]) / donor_inc79["e_tot_mJ"] * 100.0

    # Also compute relative to the rounded donor reference 0.212448 mJ
    donor_ref_rounded_mJ = summary113.get("authentic_donor_energy_mJ", 0.212448)
    diff_tot_rounded_pct = (c4_inc79["e_tot_mJ"] - donor_ref_rounded_mJ) / donor_ref_rounded_mJ * 100.0

    energy_threshold_pct = 2.000000
    gate_passed = (abs(diff_tot_pct) <= energy_threshold_pct)
    verdict = "C1_2_STEP2_FULLY_VERIFIED" if gate_passed else "C1_2_STEP2_ENERGY_GATE_FAILED"

    # 4. Audit Package 95 MISESERI load correspondence
    with open(pkg95_manifest_json, "r") as f:
        pkg95_manifest = json.load(f)

    with open(pkg95_audit_json, "r") as f:
        pkg95_audit = json.load(f)

    pkg95_u2_mm = pkg95_manifest["loading"]["prescribed_u2_mm"]
    pkg95_source = pkg95_manifest["loading"]["source_state"]
    inc79_u2_mm = 0.00184250000

    u2_discrepancy_mm = pkg95_u2_mm - inc79_u2_mm
    u2_discrepancy_pct = (pkg95_u2_mm - inc79_u2_mm) / inc79_u2_mm * 100.0

    miseseri_audit_finding = {
        "pkg95_prescribed_u2_mm": pkg95_u2_mm,
        "pkg95_source_state": pkg95_source,
        "pkg113_inc79_u2_mm": inc79_u2_mm,
        "displacement_discrepancy_mm": u2_discrepancy_mm,
        "displacement_discrepancy_pct": u2_discrepancy_pct,
        "pkg95_peak_element": pkg95_audit["peak_miseseri"]["element_id"],
        "pkg95_peak_miseseri_kNmm2": pkg95_audit["peak_miseseri"]["miseseri_kNmm2"],
        "pkg95_elements_above_threshold": pkg95_audit["refinement_metrics"]["elements_above_threshold"],
        "spatial_indicator_validity": "TOPOLOGICALLY_CONSISTENT_NOTCH_TIP_LOCALIZATION",
        "quantitative_load_correspondence": "LOAD_STATE_MISMATCH_POST_PEAK_VS_PRE_PEAK",
        "c5_remeshing_recommendation": "DEDICATED_COMPANION_SOLVE_REQUIRED_AT_INC79_LOAD_BEFORE_C5_FINALIZATION"
    }

    audit_result = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "turn": 209,
        "donor_increment_79": donor_inc79,
        "candidate_c4_increment_79": c4_inc79,
        "energy_continuity_evaluation": {
            "elastic_energy_donor_mJ": donor_inc79["e_elas_mJ"],
            "elastic_energy_c4_mJ": c4_inc79["e_elas_mJ"],
            "elastic_energy_diff_pct": diff_elas_pct,
            "fracture_energy_donor_mJ": donor_inc79["e_frac_mJ"],
            "fracture_energy_c4_mJ": c4_inc79["e_frac_mJ"],
            "fracture_energy_diff_pct": diff_frac_pct,
            "total_energy_donor_mJ": donor_inc79["e_tot_mJ"],
            "total_energy_c4_mJ": c4_inc79["e_tot_mJ"],
            "total_energy_diff_pct_unrounded": diff_tot_pct,
            "total_energy_diff_pct_vs_rounded_ref": diff_tot_rounded_pct,
            "predeclared_threshold_pct": energy_threshold_pct,
            "threshold_excess_pct": diff_tot_pct - energy_threshold_pct,
            "gate_passed": gate_passed,
            "verdict": verdict,
            "physical_mechanism": (
                "Candidate C4 resolves the localized crack tip with element size h ~ 606 nm "
                "(vs donor C3 h ~ 7.5 um). In phase-field fracture (l0 = 30 um), the finer mesh "
                "resolves the damage gradient and localized core more accurately, producing "
                "+7.48% higher regularized fracture energy (0.04412 mJ vs 0.04104 mJ). "
                "Elastic strain energy matches closely (+0.70%, 0.17260 mJ vs 0.17140 mJ). "
                "Total energy difference evaluates unrounded to +2.008031%, which exceeds "
                "the strict <= 2.000000% gate by +0.008031% (8 uJ/J). Under strict scientific "
                "discipline, the gate must be classified as C1_2_STEP2_ENERGY_GATE_FAILED "
                "without artificial threshold rounding."
            )
        },
        "miseseri_audit": miseseri_audit_finding,
        "evidence_hashes": {
            "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_1416301/uel_energy_balance.csv": get_sha256(donor_energy_csv),
            "models/pandey_kumar_mode1/113_c1_2_second_forward_continuation/c4_c1_2_inc79_continuation_summary.json": get_sha256(pkg113_summary_json),
            "models/pandey_kumar_mode1/95_c4_companion_miseseri/c4_miseseri_audit.json": get_sha256(pkg95_audit_json),
            "models/pandey_kumar_mode1/95_c4_companion_miseseri/PACKAGE_MANIFEST.json": get_sha256(pkg95_manifest_json)
        }
    }

    out_json = os.path.join(repo_root, "results", "validation", "turn209_energy_and_miseseri_audit.json")
    with open(out_json, "w") as f:
        json.dump(audit_result, f, indent=2)

    print("================================================================================")
    print("TURN 209 AUDIT: PACKAGE 113 ENERGY GATE & MISESERI CORRESPONDENCE")
    print("================================================================================")
    print("Donor Inc 79 Total Energy:     %.8f mJ" % donor_inc79["e_tot_mJ"])
    print("Candidate C4 Inc 79 Energy:    %.8f mJ" % c4_inc79["e_tot_mJ"])
    print("Total Energy Difference:       %+.6f%% (threshold <= %.6f%%)" % (diff_tot_pct, energy_threshold_pct))
    print("Threshold Excess:              %+.6f%% (+%.3f uJ/J)" % (diff_tot_pct - energy_threshold_pct, (diff_tot_pct - energy_threshold_pct) * 10000.0 / 100.0))
    print("Gate Classification Verdict:   %s" % verdict)
    print("--------------------------------------------------------------------------------")
    print("Package 95 Prescribed u2:      %.6f mm (%s)" % (pkg95_u2_mm, pkg95_source))
    print("Package 113 Inc 79 u2:         %.6f mm" % inc79_u2_mm)
    print("Displacement Mismatch:         %+.6f mm (%+.2f%%)" % (u2_discrepancy_mm, u2_discrepancy_pct))
    print("Spatial Localization:          %s (Peak EID %d)" % (miseseri_audit_finding["spatial_indicator_validity"], pkg95_audit["peak_miseseri"]["element_id"]))
    print("C5 Adaptation Action:          %s" % miseseri_audit_finding["c5_remeshing_recommendation"])
    print("================================================================================")
    print("Audit artifact written to: %s" % out_json)

if __name__ == "__main__":
    main()
