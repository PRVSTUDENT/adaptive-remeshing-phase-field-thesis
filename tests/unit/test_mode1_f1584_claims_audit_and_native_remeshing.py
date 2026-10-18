import os
import json
import hashlib
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FROZEN_PRODUCTION_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
FROZEN_EXPERIMENTAL_OFFSET_UEL_SHA256 = "ef92ed58dbe3ea921b48cb328128ab950ba2cafd698e05381e2b29f61412514d"

class TestMode1F1584ClaimsAuditAndNativeRemeshing:
    
    def test_01_subroutine_freeze_and_invariance(self):
        prod_uel_path = os.path.join(ROOT, "models", "pandey_kumar_mode1", "15_energy_qualification_small", "f42_mixed_uel.for")
        with open(prod_uel_path, "rb") as f:
            prod_sha = hashlib.sha256(f.read()).hexdigest().lower()
        assert prod_sha == FROZEN_PRODUCTION_UEL_SHA256, "Production UEL hash altered!"

        exp_uel_path = os.path.join(ROOT, "models", "pandey_kumar_mode1", "experimental_offset_uel", "f42_experimental_offset_uel.for")
        with open(exp_uel_path, "rb") as f:
            exp_sha = hashlib.sha256(f.read()).hexdigest().lower()
        assert exp_sha == FROZEN_EXPERIMENTAL_OFFSET_UEL_SHA256, "Experimental offset UEL hash altered!"

    def test_02_reconciled_package_53_54_energies(self):
        pkg53_eval = os.path.join(ROOT, "models", "pandey_kumar_mode1", "53_method_c_corrected_nonmatching_transfer", "evidence_1415063", "JOB_1415063_EVALUATION.json")
        pkg54_eval = os.path.join(ROOT, "models", "pandey_kumar_mode1", "54_continuous_650_element_corrected_reference", "evidence_1415065", "JOB_1415065_EVALUATION.json")
        
        with open(pkg53_eval) as f:
            d53 = json.load(f)
        with open(pkg54_eval) as f:
            d54 = json.load(f)
            
        e_frac_53 = d53["solver_metrics"]["step2_inc3_e_fracture_knmm"]
        e_tot_53 = d53["solver_metrics"]["step2_inc3_e_total_knmm"]
        
        e_frac_54 = d54["solver_metrics"]["continuation_endpoint_u00270"]["e_fracture_knmm"]
        e_tot_54 = d54["solver_metrics"]["continuation_endpoint_u00270"]["e_total_knmm"]
        
        # Verify values are in authentic ~3.05e-4 kN*mm range
        assert 3.0e-4 < e_frac_53 < 3.1e-4
        assert 3.0e-4 < e_frac_54 < 3.1e-4
        
        delta_frac = (e_frac_53 - e_frac_54) / e_frac_54 * 100.0
        delta_tot = (e_tot_53 - e_tot_54) / e_tot_54 * 100.0
        
        # Verify exact discrepancies
        assert abs(delta_frac - 0.3375) < 0.01, f"Expected +0.338% fracture error, got {delta_frac}%"
        assert abs(delta_tot - (-0.5271)) < 0.01, f"Expected -0.527% total error, got {delta_tot}%"

    def test_03_same_mesh_package_55_56_continuation_parity(self):
        pkg56_eval = os.path.join(ROOT, "models", "pandey_kumar_mode1", "56_method_c_samemesh_reconstruction", "evidence_1415069", "JOB_1415069_EVALUATION.json")
        with open(pkg56_eval) as f:
            d56 = json.load(f)
            
        cp = d56["continuation_parity_u00290"]
        assert abs(cp["delta_rf2_n"]) < 1e-6, "Reaction force discrepancy exceeds tolerance!"
        assert cp["delta_e_frac_pct"] == 0.0, "Fracture energy discrepancy non-zero!"
        assert cp["delta_e_tot_pct"] == 0.0, "Total energy discrepancy non-zero!"
        
        # Step 1 re-equilibration adjustment
        rp = d56["reconstruction_parity_u00270"]
        assert -1.5e-4 < rp["min_delta_d"] < 0.0, "Step 1 damage adjustment outside [-1.5e-4, 0]"
        assert rp["delta_e_tot_pct"] < 0.02, "Step 1 total energy discrepancy exceeds 0.02%"

    def test_04_native_miseseri_remeshing_qualification(self):
        summary_path = os.path.join(ROOT, "models", "pandey_kumar_mode1", "46_mode1_coarse_preanalysis_density_sensitivity", "evidence_1415074", "NATIVE_REMESH_QUALIFICATION_SUMMARY_2PCT.json")
        assert os.path.exists(summary_path), "Remesh qualification summary missing!"
        
        with open(summary_path) as f:
            remesh = json.load(f)
            
        assert remesh["status"] == "NATIVE_ADAPTIVE_REMESH_QUALIFIED"
        assert remesh["error_target_pct"] == 2.0
        assert remesh["sizing_method"] == "UNIFORM_ERROR"
        
        # Check element growth
        coarse_e = remesh["coarse_mesh"]["elements"]
        adapted_e = remesh["adapted_mesh"]["elements"]
        assert adapted_e > coarse_e, f"Adapted elements ({adapted_e}) must exceed coarse ({coarse_e})"
        assert adapted_e == 12369, f"Expected 12,369 elements, got {adapted_e}"
        assert remesh["adapted_mesh"]["nodes"] == 12410
        
        # Check seam topology preservation
        seam = remesh["seam_topology"]
        assert seam["seam_verified"] is True
        assert seam["coincident_node_pairs"] == 67
        assert seam["tip_node_shared"] is True
        
        # Check raw deck exists
        deck_path = os.path.join(ROOT, "models", "pandey_kumar_mode1", "46_mode1_coarse_preanalysis_density_sensitivity", "evidence_1415074", "PK_M1_ADAPTED_RAW_2PCT.inp")
        assert os.path.exists(deck_path), "Adapted raw input deck missing!"
        assert os.path.getsize(deck_path) > 800000, "Adapted deck suspiciously small!"
