import json
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def test_stage_c1_1_summary_classification_and_metrics():
    summary_path = REPO_ROOT / "results" / "validation" / "stage_c1_1_nm_summary.json"
    assert summary_path.exists(), "stage_c1_1_nm_summary.json must exist"
    
    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["overall_verdict"] == "NONMATCHING_GLOBAL_FORCE_ENERGY_PARTIAL_PASS_DAMAGE_CONTINUITY_UNRESOLVED"
    assert data["classification"] == "NONMATCHING_GLOBAL_FORCE_ENERGY_PARTIAL_PASS_DAMAGE_CONTINUITY_UNRESOLVED"
    
    # Check coarse donor vs fine baseline discretization gap
    assert abs(data["coarse_donor"]["rf_N"] - 653.085) < 0.01
    assert abs(data["fine_baseline"]["rf_N"] - 661.725) < 0.01
    assert abs(data["discretization_gap"]["delta_rf_N"] - 8.64039) < 0.01
    assert abs(data["fine_baseline"]["d_max"] - 0.3181416) < 1e-5
    
    # Check mapping accuracy
    assert data["transfer_mapping"]["u_L2_error_pct"] < 0.05
    assert data["transfer_mapping"]["integrated_damage_error_pct"] < 0.05
    assert data["transfer_mapping"]["min_H_kN_per_mm2"] >= 0.0
    
    # Check Step 1 re-equilibration
    assert abs(data["step1_reequilibration"]["rf_N"] - 665.83299) < 0.01
    assert abs(data["step1_reequilibration"]["e_total_mJ"] - 1.693730) < 0.001
    
    # Check damage discrepancy against fine baseline
    d_gap = abs(data["step2_release_and_hold"]["terminal_d_max"] - data["fine_baseline"]["d_max"])
    assert d_gap > 0.0200, "Damage gap against fine baseline exceeds the 0.0200 continuity threshold"
    assert abs(d_gap - 0.045033) < 0.001

def test_package54c_frozen_control_invariance():
    evidence_dir = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_1_nonmatching_frozen_hold" / "evidence_1414766"
    assert evidence_dir.exists(), "Package 54C evidence directory must exist"
    
    fields_file = evidence_dir / "pkg54c_extracted_fields.json"
    assert fields_file.exists(), "pkg54c_extracted_fields.json must exist"
    
    with open(fields_file, "r", encoding="utf-8") as f:
        fields = json.load(f)
        
    step2_frames = fields["steps"]["Step-2-HoldFrozen"]
    assert len(step2_frames) == 11, "Expected 11 frames in Step 2 hold"
    
    ref_rf = 665.832996
    ref_dmax = 0.09040315
    ref_hmax = 0.4557195
    
    for fr in step2_frames:
        assert abs(fr["RF2_N"] - ref_rf) < 1e-4, f"RF2 changed in frame {fr['frame']}: {fr['RF2_N']}"
        assert abs(fr["d_max"] - ref_dmax) < 1e-6, f"d_max changed in frame {fr['frame']}: {fr['d_max']}"
        assert abs(fr["H_max"] - ref_hmax) < 1e-5, f"H_max changed in frame {fr['frame']}: {fr['H_max']}"
        assert fr["H_min"] >= 0.0, "History non-negativity violated"

def test_energy_balance_invariance():
    csv_path = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_1_nonmatching_frozen_hold" / "evidence_1414766" / "uel_energy_balance.csv"
    assert csv_path.exists(), "uel_energy_balance.csv must exist"
    
    with open(csv_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("Step")]
        
    assert len(lines) == 11, "Expected 11 energy balance rows (1 in Step 1, 10 in Step 2)"
    
    ref_etot = 0.16937302e-02
    for line in lines:
        parts = [p.strip() for p in line.split(",")]
        etot = float(parts[6])
        assert abs(etot - ref_etot) < 1e-9, f"Total energy drifted: {etot} vs {ref_etot}"
