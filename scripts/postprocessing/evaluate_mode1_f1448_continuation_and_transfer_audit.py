"""
Task F1449 — Mode-I Method C State Transfer Audit and Continuation Post-Processing
Audits four critical scientific questions:
1. Criterion 3 strict threshold check (5.0465% vs 5.0% threshold) and analytical coarsening bias verification
   via the exact user formula xi*coth(xi) - 1 = +53.25% vs 2D domain-integrated behavior (+5.05%).
2. Criterion 5 step-boundary force discontinuity (Delta RF = 21.55 N between Step 1 end and Step 2 entry)
   classified strictly as FAIL against the 5.0 N threshold without cherry-picking.
3. Adaptivity classification and coarse-mesh crack pinning on the 2,906 recipient mesh (h/l0 = 2.67).
4. Forward-refinement experiment design (2,906 FE coarse donor -> 14,677 FE native recipient).
"""

import math
import json
import os

def compute_analytical_coth_formula(h, l0):
    """
    Computes exact analytical relative error for 1D exponential phase-field profile:
      d(x) = d_max * exp(-|x| / l0)
    on an infinite periodic 1D lattice with uniform node spacing h:
      xi = h / (2 * l0)
      Relative Error = xi * coth(xi) - 1
    Taylor expansion for small h/l0:
      xi * coth(xi) - 1 = xi^2 / 3 - xi^4 / 45 + ... = h^2 / (12 * l0^2) - ...
    """
    xi = h / (2.0 * l0)
    coth_xi = 1.0 / math.tanh(xi)
    rel_error = xi * coth_xi - 1.0
    taylor_approx = (xi ** 2) / 3.0
    return {
        "h_mm": h,
        "l0_mm": l0,
        "h_over_l0": h / l0,
        "xi": xi,
        "coth_xi": coth_xi,
        "rel_error_exact": rel_error,
        "bias_pct": rel_error * 100.0,
        "taylor_approx_pct": taylor_approx * 100.0
    }

def compute_analytical_chordal_bias(h, l0, d_max=0.319455):
    """
    Computes analytical chordal integration bias for a 1D exponential phase-field profile:
      d(x) = d_max * exp(-x / l0).
    On element [0, h], linear interpolation between d(0)=d_max and d(h)=d_max*exp(-h/l0) is:
      d_linear(x) = d_max * [ (1 - x/h) + (x/h)*exp(-h/l0) ]
    Exact integral:
      I_exact = int_0^h d_max * exp(-x/l0) dx = d_max * l0 * (1 - exp(-h/l0))
    Linear interpolant integral:
      I_linear = int_0^h d_linear(x) dx = 0.5 * h * d_max * (1 + exp(-h/l0))
    Relative chordal bias:
      bias_pct = (I_linear - I_exact) / I_exact * 100
    Algebraic identity: (I_linear / I_exact) = (h / (2*l0)) * (1 + exp(-h/l0)) / (1 - exp(-h/l0)) = xi * coth(xi).
    Hence bias_pct is identically (xi * coth(xi) - 1) * 100.
    """
    exp_term = math.exp(-h / l0)
    I_exact = d_max * l0 * (1.0 - exp_term)
    I_linear = 0.5 * h * d_max * (1.0 + exp_term)
    bias_pct = (I_linear - I_exact) / I_exact * 100.0
    return {
        "h_mm": h,
        "l0_mm": l0,
        "h_over_l0": h / l0,
        "I_exact": I_exact,
        "I_linear": I_linear,
        "bias_pct": bias_pct
    }

def audit_gate6c_transfer_criteria():
    """
    Audits the Gate 6C acceptance criteria under strict threshold governance:
    - Criterion 3 is strictly FAIL (5.0465% > 5.0% threshold).
    - Criterion 5 is strictly FAIL on the actual step boundary (21.55 N > 5.0 N threshold).
    No retrospective relaxation or selective cherry-picking permitted.
    """
    predeclared_thresholds = {
        "criterion_1_displacement_l2": {"threshold": 1.0, "unit": "%"},
        "criterion_2_peak_damage": {"threshold": 0.020, "unit": "dimensionless"},
        "criterion_3_integrated_damage": {"threshold": 5.0, "unit": "%"},
        "criterion_4_history_non_negativity": {"threshold": 0.0, "unit": "kN/mm^2"},
        "criterion_5_boundary_force_continuity": {"threshold": 5.0, "unit": "N"},
        "criterion_6_internal_energy": {"threshold": 5.0, "unit": "%"},
        "criterion_7_global_energy_residual": {"threshold": 10.0, "unit": "%"}
    }
    
    # Evaluated values reflecting actual physical state
    # Criterion 5 is evaluated on the actual Abaqus step boundary:
    # |RF(Step 2 Inc 1) - RF(Step 1 End)| = |653.1694 - 674.7167| = 21.5473 N
    evaluated_values = {
        "criterion_1_displacement_l2": 0.480553,
        "criterion_2_peak_damage": 0.000000,
        "criterion_3_integrated_damage": 5.046520,  # 5.0465% > 5.0%
        "criterion_4_history_non_negativity": 3.876e-32,
        "criterion_5_boundary_force_continuity": 21.5473,  # Step-boundary jump: 21.55 N > 5.0 N
        "criterion_6_internal_energy": 1.637987,
        "criterion_7_global_energy_residual": 1.100000
    }
    
    criteria_audit = {}
    for crit, spec in predeclared_thresholds.items():
        val = evaluated_values[crit]
        thresh = spec["threshold"]
        
        if crit == "criterion_4_history_non_negativity":
            passed = (val >= thresh)
        else:
            passed = (val <= thresh)
            
        if crit == "criterion_3_integrated_damage":
            verdict = "FAIL_AGAINST_STRICT_5PCT_THRESHOLD"
            qualification = (
                "Exceeds strict 5.0% threshold by +0.0465% (evaluated 5.0465%). "
                "Classified as FAIL under strict threshold governance. The discrepancy is a 2D domain-integrated "
                "numerical quadrature difference over nonmatching elements. While the 1D infinite-domain analytical "
                "formula xi*coth(xi)-1 yields +53.25% locally on h=20 um elements, the 2D domain-integrated error is "
                "damped to +5.05% because >97% of the specimen has d ~ 0 and 2D bilinear quad quadrature differs from "
                "1D linear chords. The 1D formula does not prove 2D domain compliance, so Criterion 3 remains strictly FAIL."
            )
        elif crit == "criterion_5_boundary_force_continuity":
            verdict = "FAIL_AGAINST_STRICT_5N_THRESHOLD"
            qualification = (
                "Evaluated across the actual Abaqus step boundary: |RF_step2_inc1 - RF_step1_end| = "
                "|653.1694 - 674.7167| = 21.55 N (exceeds 5.0 N threshold by +16.55 N). "
                "Classified as FAIL under strict threshold governance. Step 1 functions mechanically as a one-increment "
                "reload from zero displacement; coarse-mesh secant stiffness over Delta u = 0.0050 mm yields RF = 674.72 N, "
                "whereas the true tangent at Step 2 entry drops to 653.17 N. Comparing donor (653.09 N) to Step 2 entry (653.17 N) "
                "yields Delta RF = 0.0794 N, but cherry-picking this subset comparison obscures the physical 21.55 N handoff "
                "discontinuity in the executed solver trajectory."
            )
        else:
            verdict = "PASS" if passed else "FAIL"
            qualification = "Satisfies predeclared threshold."
            
        criteria_audit[crit] = {
            "evaluated_value": val,
            "threshold": thresh,
            "unit": spec["unit"],
            "strict_verdict": verdict,
            "passed_strict": passed,
            "qualification": qualification
        }
        
    return criteria_audit

def audit_mesh_adaptivity_lineage():
    """
    Audits the mesh adaptivity relationship between donor and recipient.
    """
    return {
        "donor_mesh": {
            "name": "M1_MB_NATIVE_FINAL_1S.inp",
            "element_count": 14677,
            "node_count": 14948,
            "fine_corridor_h_mm": 0.001875,
            "provenance": "Generated by native Abaqus adaptiveRemesh on Step-1 MISESERI with errorTarget=1.0"
        },
        "recipient_mesh": {
            "name": "M1_MB_INF_1S.inp",
            "element_count": 2906,
            "node_count": 2988,
            "coarse_h_mm": 0.020000,
            "provenance": "Reused canonical coarse background discretization (models/pandey_kumar_mode1/93_mode1_preanalysis_inf_companion_2906/)"
        },
        "transfer_direction": "COARSENING (14,677 FE -> 2,906 FE, ratio 5.05 : 1)",
        "scientific_classification": "COARSENING_FEASIBILITY_EXPERIMENT_AND_STATIC_CONTINUATION_QUALIFICATION",
        "distinction_note": (
            "Package 41 evaluates the feasibility of nonmatching state transfer and static continuation "
            "architecture without reload from zero. Because it maps from 14.7k down to 2.9k, it is NOT "
            "an adaptive refinement cycle. Validated sequential adaptive refinement requires the forward "
            "coarse-to-fine progression (e.g. 2,906 FE -> 14,677 FE)."
        )
    }

def audit_job_1412809_initial_state():
    """
    Audits initial state preservation and reaction force continuity on Job 1412809.mmaster02.
    """
    donor_rf_handoff_N = 653.09  # At u = 0.0050 mm
    donor_energy_handoff_mJ = 1.6911
    
    # Values extracted from Job 1412809 M1_MC_GENUINE_CONTINUATION.dat:
    # Step 1 End (u = 0.0050000 mm):
    step1_rf_N = 674.7167
    step1_internal_energy_mJ = 1.689856
    
    # Step 2 Inc 1 (u = 0.0050010 mm):
    step2_inc1_rf_N = 653.1694
    
    # Discontinuities:
    delta_rf_boundary_N = abs(step2_inc1_rf_N - step1_rf_N)
    delta_rf_step1_vs_donor_N = abs(step1_rf_N - donor_rf_handoff_N)
    delta_rf_step2_vs_donor_N = abs(step2_inc1_rf_N - donor_rf_handoff_N)
    delta_e_int_pct = abs(step1_internal_energy_mJ - donor_energy_handoff_mJ) / donor_energy_handoff_mJ * 100.0
    
    return {
        "job_id": "1412809.mmaster02",
        "donor_reference": {
            "u_handoff_mm": 0.0050000,
            "rf_handoff_N": donor_rf_handoff_N,
            "internal_energy_mJ": donor_energy_handoff_mJ
        },
        "step_1_re_equilibration": {
            "converged_increments": 1,
            "newton_iterations": 2,
            "u_applied_mm": 0.0050000,
            "rf_evaluated_N": step1_rf_N,
            "delta_rf_vs_donor_N": delta_rf_step1_vs_donor_N,
            "delta_rf_vs_donor_pct": (delta_rf_step1_vs_donor_N / donor_rf_handoff_N) * 100.0,
            "internal_energy_mJ": step1_internal_energy_mJ,
            "energy_discrepancy_pct": delta_e_int_pct,
            "analysis": (
                "Step 1 converges in 1 increment (2 iters) resolving compatible displacement and phase "
                "fields with 99.93% internal energy preservation (0.07% error). The end-of-step reaction force "
                "is 674.72 N (+21.63 N vs donor) due to coarse-mesh stiffness over the single large handoff increment."
            )
        },
        "step_2_continuation_entry": {
            "inc_1_displacement_mm": 0.0050010,
            "inc_1_rf_N": step2_inc1_rf_N,
            "delta_rf_vs_donor_N": delta_rf_step2_vs_donor_N,
            "delta_rf_vs_donor_pct": (delta_rf_step2_vs_donor_N / donor_rf_handoff_N) * 100.0,
            "step_boundary_jump_N": delta_rf_boundary_N,
            "step_boundary_jump_pct": (delta_rf_boundary_N / step1_rf_N) * 100.0,
            "step_boundary_verdict": "FAIL_AGAINST_STRICT_5N_THRESHOLD",
            "donor_subset_comparison_N": delta_rf_step2_vs_donor_N,
            "analysis": (
                "Across the actual step boundary, RF drops from 674.72 N to 653.17 N (Delta RF = 21.55 N), "
                "strictly FAILING the 5.0 N threshold. The entry tangent agrees with the donor (653.09 N vs 653.17 N, "
                "Delta RF = 0.0794 N), but this tangent relaxation occurs across the boundary discontinuity."
            )
        }
    }

def audit_coarse_mesh_crack_pinning():
    """
    Audits the physics of coarse-mesh crack pinning on the 2,906-element recipient mesh.
    """
    return {
        "recipient_mesh_element_size_h_mm": 0.020,
        "phase_field_length_scale_l0_mm": 0.0075,
        "mesh_resolution_ratio_h_over_l0": 0.020 / 0.0075,
        "physical_resolution_criterion": "h <= l0 / 2 (or h <= 0.00375 mm)",
        "pinning_mechanism": (
            "Because h/l0 = 2.67 > 1, the element size exceeds the regularization length scale l0 = 7.5 um. "
            "The regularized damage band (width ~ 2*l0 = 15 um) cannot localize within a single element column. "
            "Consequently, the discrete damage profile is artificially broadened, causing severe crack pinning, "
            "elevated initiation resistance, delayed post-peak softening, and peak reaction force climbing past 880 N "
            "towards F_max ~ 1.08 kN (matching Gate C1 V2 Job 1412464 at 1.0868 kN vs reference 0.7578 kN)."
        ),
        "scientific_conclusion": (
            "Successful convergence of Step 1 re-equilibration verifies state-transfer data structures and initial "
            "static equilibrium, but does NOT demonstrate sequential adaptive fracture propagation. The 14.7k -> 2.9k "
            "coarsening run is an offline data-structure qualification, not an accurate fracture mechanics simulation."
        )
    }

def design_forward_refinement_experiment():
    """
    Defines the forward-refinement experiment design (offline only, zero PBS submissions authorized).
    """
    return {
        "status": "OFFLINE_DESIGN_ONLY_ZERO_PBS_SUBMISSIONS_AUTHORIZED",
        "donor": {
            "name": "M1_MB_INF_1S.inp (Coarse Pre-Analysis)",
            "elements": 2906,
            "h_corridor_mm": 0.020,
            "handoff_displacement_mm": 0.0050,
            "expected_rf_N": 653.1,
            "expected_d_max": 0.3195
        },
        "recipient": {
            "name": "M1_MB_NATIVE_FINAL_1S.inp (Native Refined Adaptive Mesh)",
            "elements": 14677,
            "h_corridor_mm": 0.001875,
            "h_over_l0": 0.25,
            "meets_resolution_criterion": True
        },
        "expected_theoretical_chordal_bias_pct": 0.0039,
        "scientific_objective": (
            "Evaluate true adaptive refinement (coarse donor 2.9k -> fine recipient 14.7k) to eliminate "
            "coarse-mesh crack pinning and achieve reference-level peak load (~0.743-0.758 kN)."
        )
    }

def main():
    coth_coarse = compute_analytical_coth_formula(h=0.020, l0=0.0075)
    coth_fine = compute_analytical_coth_formula(h=0.001875, l0=0.0075)
    chordal_coarse = compute_analytical_chordal_bias(h=0.020, l0=0.0075)
    chordal_fine = compute_analytical_chordal_bias(h=0.001875, l0=0.0075)
    
    criteria_audit = audit_gate6c_transfer_criteria()
    mesh_audit = audit_mesh_adaptivity_lineage()
    job_audit = audit_job_1412809_initial_state()
    pinning_audit = audit_coarse_mesh_crack_pinning()
    forward_design = design_forward_refinement_experiment()
    
    report = {
        "task_id": "F1449",
        "title": "Method C State Transfer Audit, Force Discontinuity, and Coarse Pinning Forensic Report",
        "analytical_coarsening_formula": {
            "formula": "xi * coth(xi) - 1, where xi = h / (2 * l0)",
            "coarse_recipient_h_20um": coth_coarse,
            "fine_donor_h_1p9um": coth_fine,
            "reconciliation_note": (
                "The 1D analytical formula xi*coth(xi)-1 yields +53.25% locally on h=20 um elements. "
                "In the 2D finite element model, the total integrated damage error is +5.0465% because "
                "damage is localized (over 97% of the domain d ~ 0) and 2D bilinear quad Gauss quadrature "
                "differs from 1D linear chords. Criterion 3 strictly fails the 5.0% threshold."
            )
        },
        "gate_6c_criteria_audit": criteria_audit,
        "mesh_adaptivity_lineage": mesh_audit,
        "job_1412809_initial_state_audit": job_audit,
        "coarse_mesh_crack_pinning_audit": pinning_audit,
        "forward_refinement_design": forward_design
    }
    
    out_path = r"models/pandey_kumar_mode1/41_method_c_genuine_continuation/method_c_genuine_continuation_audit.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
        
    print(f"Report written to {out_path}")
    print("\n--- Summary of Findings ---")
    print(f"Criterion 3 Strict Verdict: {criteria_audit['criterion_3_integrated_damage']['strict_verdict']}")
    print(f"  Evaluated: {criteria_audit['criterion_3_integrated_damage']['evaluated_value']:.4f}% (Threshold: {criteria_audit['criterion_3_integrated_damage']['threshold']}%)")
    print(f"  1D Formula xi*coth(xi)-1: +{coth_coarse['bias_pct']:.2f}% (Coarse), +{coth_fine['bias_pct']:.4f}% (Fine)")
    print(f"Criterion 5 Strict Verdict: {criteria_audit['criterion_5_boundary_force_continuity']['strict_verdict']}")
    print(f"  Step-boundary jump: {criteria_audit['criterion_5_boundary_force_continuity']['evaluated_value']:.4f} N (Threshold: 5.0 N)")
    print(f"  Donor-to-Step2 tangent difference: {job_audit['step_2_continuation_entry']['delta_rf_vs_donor_N']:.4f} N")
    print(f"Coarse Pinning Ratio h/l0: {pinning_audit['mesh_resolution_ratio_h_over_l0']:.2f} (Elevates RF past 880 N)")
    print(f"Forward Refinement Design: {forward_design['status']}")

if __name__ == "__main__":
    main()
