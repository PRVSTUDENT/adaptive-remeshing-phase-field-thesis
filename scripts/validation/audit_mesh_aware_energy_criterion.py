"""
Independent Audit and Formulation of Mesh-Aware Energy Criterion.
Research Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Evaluates Packages 111 R2, 112, 113, 115, 116 R1, 117, 118.

Formulates prospective dimensionless energy residual:
    r_E = (E_target - E_source - Delta_E_mesh_independent) / E_source

Enforces strict non-circularity:
    - Evaluates whether existing evidence can independently calibrate Delta_E_mesh.
    - Prohibits tuning Delta_E_mesh to Package 115 or Package 113 within the same training set.
    - Classifies the proposal strictly as one of:
        - PROSPECTIVE_CRITERION_INDEPENDENTLY_SUPPORTED
        - PROSPECTIVE_CRITERION_REQUIRES_HOLDOUT_VALIDATION
        - MESH_AWARE_CORRECTION_NOT_YET_IDENTIFIABLE
"""

import os
import json
import csv
import math

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

def run_audit():
    # 1. Authoritative Evidence for all 7 Controls (All energies in mJ = kN*mm)
    controls = [
        {
            "package_id": "PACKAGE_111_R2",
            "name": "Stage C1-1 Direct Transfer",
            "physical_state": "Frame 77 (u = 0.0018003 mm, pre-localization)",
            "donor_mesh": "C3 (1600 quads, h = 2.5 um)",
            "target_mesh": "C4 (4422 quads, h_min = 0.61 um)",
            "displacement_mm": 0.0018003,
            "e_source_mJ": 0.20848325,
            "e_target_mJ": 0.20879672,
            "rf2_N": 186.149,
            "d_max": 0.479016,
            "is_inc79_family": False,
            "purpose": "Early transfer reference (Level 3 Gate Passed)"
        },
        {
            "package_id": "PACKAGE_112",
            "name": "Stage C1-2 Forward Step 1",
            "physical_state": "Increment 78 (u = 0.0018214 mm, pre-localization)",
            "donor_mesh": "C3 (1600 quads, h = 2.5 um)",
            "target_mesh": "C4 (4422 quads, h_min = 0.61 um)",
            "displacement_mm": 0.0018214,
            "e_source_mJ": 0.20909247,
            "e_target_mJ": 0.21275149,
            "rf2_N": 186.980,
            "d_max": 0.488406,
            "is_inc79_family": False,
            "purpose": "Intermediate forward step (Level 3 Gate Passed)"
        },
        {
            "package_id": "PACKAGE_113",
            "name": "Stage C1-2 Forward Step 2",
            "physical_state": "Increment 79 (u = 0.0018425 mm, near-localization)",
            "donor_mesh": "C3 (1600 quads, h = 2.5 um)",
            "target_mesh": "C4 (4422 quads, h_min = 0.61 um)",
            "displacement_mm": 0.0018425,
            "e_source_mJ": 0.21244795,
            "e_target_mJ": 0.21671407,
            "rf2_N": 187.391,
            "d_max": 0.499220,
            "is_inc79_family": True,
            "purpose": "Forward continuation step (Level 3 Gate FAILED: +2.0080315%)"
        },
        {
            "package_id": "PACKAGE_115",
            "name": "C4 Direct Transfer Control",
            "physical_state": "Increment 79 (u = 0.0018425 mm, physical hold)",
            "donor_mesh": "C3 (1600 quads, h = 2.5 um, un-reequilibrated)",
            "target_mesh": "C4 (4422 quads, h_min = 0.61 um)",
            "displacement_mm": 0.0018425,
            "e_source_mJ": 0.21244795,
            "e_target_mJ": 0.21675960,
            "rf2_N": 185.789,
            "d_max": 0.523773,
            "is_inc79_family": True,
            "purpose": "Level 4 Explanatory diagnostic: direct hold on C4"
        },
        {
            "package_id": "PACKAGE_116_R1",
            "name": "C3-Int Mesh Sensitivity Control",
            "physical_state": "Increment 79 (u = 0.0018425 mm, intermediate refinement)",
            "donor_mesh": "C3 (1600 quads, h = 2.5 um)",
            "target_mesh": "C3-Int (2500 quads, h = 1.25 um)",
            "displacement_mm": 0.0018425,
            "e_source_mJ": 0.21244800,
            "e_target_mJ": 0.21678093,
            "rf2_N": 185.847,
            "d_max": 0.520228,
            "is_inc79_family": True,
            "purpose": "Level 4 Explanatory diagnostic: spatial discretization plateau"
        },
        {
            "package_id": "PACKAGE_117",
            "name": "C3 Same-Mesh AM Control",
            "physical_state": "Increment 79 (u = 0.0018425 mm, same-mesh re-equilibration)",
            "donor_mesh": "C3 (1600 quads, h = 2.5 um)",
            "target_mesh": "C3 (1600 quads, h = 2.5 um)",
            "displacement_mm": 0.0018425,
            "e_source_mJ": 0.21244800,
            "e_target_mJ": 0.21245454,
            "rf2_N": 185.318,
            "d_max": 0.433395,
            "is_inc79_family": True,
            "purpose": "Level 4 Explanatory diagnostic: pure solver AM relaxation"
        },
        {
            "package_id": "PACKAGE_118",
            "name": "C4 from Re-equilibrated Donor Transfer",
            "physical_state": "Increment 79 (u = 0.0018425 mm, re-equilibrated donor)",
            "donor_mesh": "C3 (1600 quads, re-equilibrated via P117)",
            "target_mesh": "C4 (4422 quads, h_min = 0.61 um)",
            "displacement_mm": 0.0018425,
            "e_source_mJ": 0.21245454,
            "e_target_mJ": 0.21676045,
            "rf2_N": 185.783,
            "d_max": 0.523842,
            "is_inc79_family": True,
            "purpose": "Level 4 Explanatory diagnostic: donor non-equilibrium independence"
        }
    ]

    # Compute raw discrepancies
    for c in controls:
        c["delta_e_raw_mJ"] = c["e_target_mJ"] - c["e_source_mJ"]
        c["pct_discrepancy_raw"] = (c["delta_e_raw_mJ"] / c["e_source_mJ"]) * 100.0

    # 2. Evaluation of Prospective Calibration Models
    # Model 1: Zero correction (standard Level 3 continuity gate, Delta E_mesh = 0)
    # Model 2: Pure fixed-field quadrature integration shift (Delta E_quad = -0.0000508 mJ = -0.1217% of fracture energy)
    # Model 3: Same-mesh re-equilibration shift (Delta E_same = +0.00000654 mJ = +0.00308%)
    # Model 4: Empirical Increment-79 C4 shift (Delta E_P115 = +0.00431165 mJ = +2.0295%)
    # Model 5: Intermediate C3-Int shift (Delta E_P116 = +0.00433293 mJ = +2.0395%)

    # Calculate residuals under each prospective model
    for c in controls:
        # Model 1: Delta E_mesh = 0
        c["r_E_model1_pct"] = c["pct_discrepancy_raw"]

        # Model 2: Pure quadrature shift (-5.08e-5 mJ)
        delta_m2 = -5.08e-5
        c["r_E_model2_pct"] = ((c["delta_e_raw_mJ"] - delta_m2) / c["e_source_mJ"]) * 100.0

        # Model 3: Same-mesh re-equilibration (+6.54e-6 mJ)
        delta_m3 = 6.54e-6
        c["r_E_model3_pct"] = ((c["delta_e_raw_mJ"] - delta_m3) / c["e_source_mJ"]) * 100.0

        # Model 4: Empirical P115 shift (+4.31165e-3 mJ)
        delta_m4 = 0.00431165
        c["r_E_model4_pct"] = ((c["delta_e_raw_mJ"] - delta_m4) / c["e_source_mJ"]) * 100.0

    # 3. Non-Circularity and Correlation Analysis
    # Crucial scientific check:
    # Packages 113, 115, 116 R1, 117, 118 all share Increment 79 (u = 0.0018425 mm).
    # Packages 115, 116 R1, 117, 118 were generated after Package 113 failed to diagnose Package 113.
    # Therefore, calibrating Delta E_mesh on P115 (+2.0295%) and testing on P113 (+2.0080%) yields
    # a residual r_E = -0.0215%, which trivially passes |r_E| <= 2.0% or 0.1%, BUT this is entirely
    # an in-sample training calibration on the exact same physical displacement increment.
    # When Model 4 (+2.0295%) is applied to Package 111 R2 (u = 0.0018003 mm), r_E = -1.917%,
    # and to Package 112 (u = 0.0018214 mm), r_E = -0.312%.
    # This demonstrates that Delta E_mesh is NOT a constant geometric parameter, but strongly
    # state-dependent on crack-tip localization: Delta E_mesh(h, u, d_max).
    # An independent, predictive mesh-aware criterion requires a generalized formulation verified
    # on an out-of-sample holdout (e.g. Increment 85 or post-initiation state).

    # 4. Classification Decision
    classification = "PROSPECTIVE_CRITERION_REQUIRES_HOLDOUT_VALIDATION"
    rationale = (
        "The prospective energy residual r_E = (E_target - E_source - Delta_E_mesh) / E_source is "
        "physically meaningful and well-defined in units of mJ (kN*mm), with r_E > 0 denoting excess "
        "non-physical hardening and r_E < 0 denoting non-physical relaxation. However, within the existing "
        "Abaqus evidence suite, all fine-mesh C4 and intermediate-mesh C3-Int runs (Packages 113, 115, 116 R1, "
        "117, 118) are clustered at a single physical displacement (Increment 79, u = 0.0018425 mm) and were "
        "formulated specifically as diagnostic controls for the Package 113 outcome. Setting Delta_E_mesh to "
        "Package 115's observed +2.0295% offset to evaluate Package 113 constitutes circular in-sample calibration. "
        "Furthermore, applying that calibration to earlier pre-localization increments (Package 111 R2 at Frame 77, "
        "+0.150%) produces large negative residuals (-1.917%), proving that Delta_E_mesh is a state-dependent "
        "function of crack localization Delta_E_mesh(h, u, d_max), not a constant geometric scalar. Therefore, "
        "the criterion cannot be declared independently supported without holdout validation on an uncalibrated "
        "state (such as Increment 85). Per project governance, Gate C1-2 Step 2 remains strictly "
        "C1_2_STEP2_ENERGY_GATE_FAILED (+2.0080315% > 2.000000%)."
    )

    # 5. Export Controls CSV
    csv_path = os.path.join(REPO_ROOT, "results/validation/mesh_aware_controls_comparison.csv")
    fieldnames = [
        "package_id", "name", "displacement_mm", "d_max", "rf2_N",
        "e_source_mJ", "e_target_mJ", "delta_e_raw_mJ", "pct_discrepancy_raw",
        "r_E_model1_pct", "r_E_model4_p115_pct", "is_inc79_family"
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in controls:
            row = {
                "package_id": c["package_id"],
                "name": c["name"],
                "displacement_mm": f"{c['displacement_mm']:.7f}",
                "d_max": f"{c['d_max']:.6f}",
                "rf2_N": f"{c['rf2_N']:.3f}",
                "e_source_mJ": f"{c['e_source_mJ']:.8f}",
                "e_target_mJ": f"{c['e_target_mJ']:.8f}",
                "delta_e_raw_mJ": f"{c['delta_e_raw_mJ']:.8f}",
                "pct_discrepancy_raw": f"{c['pct_discrepancy_raw']:.5f}",
                "r_E_model1_pct": f"{c['r_E_model1_pct']:.5f}",
                "r_E_model4_p115_pct": f"{c['r_E_model4_pct']:.5f}",
                "is_inc79_family": c["is_inc79_family"]
            }
            writer.writerow(row)

    # 6. Export Holdout Specification
    holdout_spec = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "title": "Prospective Holdout Validation Specification for Mesh-Aware Energy Criterion",
        "formulation": {
            "energy_units": "milliJoules (mJ = 10^-3 J = kN*mm)",
            "dimensionless_residual_formula": "r_E = (E_target - E_source - Delta_E_mesh_model) / E_source",
            "residual_sign_convention": {
                "r_E_positive": "Unexplained energy excess beyond predicted discretization sharpening (excess stiffness / history ratcheting)",
                "r_E_negative": "Unexplained energy deficit below predicted discretization sharpening (spurious relaxation / healing / interpolation loss)",
                "r_E_zero": "Exact balance between target energy and independently predicted mesh-sharpened energy"
            }
        },
        "holdout_experiment": {
            "recommended_state": "Increment 85 (post-initiation localized crack tip, u ~ 0.00195 mm)",
            "donor_source": "Authentic coarse C3 donor continued to Inc 85",
            "candidate_receiver": "Candidate C4 mesh (h_min = 0.61 um)",
            "independent_predictor": "Variational energy functional integration using localized asymptotic crack-tip model or multi-mesh scaling extrapolation",
            "predeclared_acceptance_band": "|r_E| <= 0.25% (unexplained residual)",
            "falsification_condition": "|r_E| > 0.50% falsifies the state-dependent scaling model"
        },
        "governance_status": {
            "gate_c1_2_step2_status": "C1_2_STEP2_ENERGY_GATE_FAILED (RETAINED, NOT CLEARED)",
            "c5_remeshing_permitted": False,
            "classification": classification
        }
    }
    holdout_spec_path = os.path.join(REPO_ROOT, "results/validation/mesh_aware_holdout_specification.json")
    with open(holdout_spec_path, "w", encoding="utf-8") as f:
        json.dump(holdout_spec, f, indent=2)

    # 7. Export Comprehensive Audit JSON
    audit_data = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "description": "Independent evaluation of prospective mesh-aware energy transfer criterion",
        "energy_units": "milliJoules (mJ = kN*mm)",
        "residual_sign_convention": {
            "formula": "r_E = (E_target - E_source - Delta_E_mesh_independent) / E_source",
            "positive_residual": "Excess energy beyond expected mesh sharpening (spurious hardening/ratcheting)",
            "negative_residual": "Energy deficit below expected mesh sharpening (spurious relaxation/loss)",
            "zero_residual": "Exact physical/discretization alignment"
        },
        "controls_analyzed": controls,
        "governance_preservation": {
            "level_3_gate_status": "C1_2_STEP2_ENERGY_GATE_FAILED",
            "package_113_status": "FAIL (+2.0080315% > 2.000000%)",
            "retrospective_alteration_permitted": False,
            "autonomous_c5_remeshing_permitted": False
        },
        "circularity_audit": {
            "circular_tuning_identified": True,
            "circular_pair": "Calibrating Delta_E_mesh on Package 115 (+2.0295%) to evaluate Package 113 (+2.0080%)",
            "reason": "Packages 113, 115, 116 R1, 117, and 118 all occupy the exact same physical displacement (Increment 79, u = 0.0018425 mm); Package 115 was specifically synthesized to diagnose Package 113.",
            "state_dependence_demonstrated": "Shift varies from +0.150% at Frame 77 to +1.750% at Inc 78 to +2.026% at Inc 79 as crack localizes."
        },
        "classification": classification,
        "scientific_rationale": rationale
    }
    audit_path = os.path.join(REPO_ROOT, "results/validation/mesh_aware_energy_criterion_audit.json")
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    print("Mesh-Aware Energy Criterion Audit successfully completed.")
    print(f"Classification: {classification}")
    print(f"Artifacts generated:")
    print(f"  - {audit_path}")
    print(f"  - {csv_path}")
    print(f"  - {holdout_spec_path}")

if __name__ == "__main__":
    run_audit()
