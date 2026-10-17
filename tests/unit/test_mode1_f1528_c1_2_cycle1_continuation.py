import os
import json
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle1_continuation" / "evidence_1414775"
FROZEN_UEL_HASH = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"


def load_extracted_results():
    p = EVIDENCE_DIR / "stage_c1_2_cycle1_extracted_results.json"
    assert p.is_file(), f"Missing extracted results: {p}"
    return json.loads(p.read_text(encoding="utf-8"))


def test_job_1414775_exit_status():
    sta_path = EVIDENCE_DIR / "M1_MC_STAGE_C1_2_CYCLE1_CONT.sta"
    assert sta_path.is_file(), "Missing .sta file"
    text = sta_path.read_text(encoding="utf-8")
    assert "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in text
    
    # Verify 200 increments in Step 2
    step2_incs = [line for line in text.splitlines() if line.strip().startswith("2 ") or line.strip().startswith("2  ")]
    assert len(step2_incs) == 200, f"Expected 200 increments in Step 2, got {len(step2_incs)}"


def test_step1_reequilibration_gate_6c_acceptance():
    results = load_extracted_results()
    s1 = results["step1_equilibration"]
    
    # 1. Force continuity
    assert s1["delta_RF2_pass"] is True
    assert s1["delta_RF2_N"] <= 5.0, f"Force jump {s1['delta_RF2_N']} N exceeds 5.0 N"
    
    # 2. Damage continuity
    assert s1["delta_dmax_pass"] is True
    assert s1["delta_dmax"] <= 0.0200, f"Damage delta {s1['delta_dmax']} exceeds 0.0200"
    
    # 3. Total energy error
    assert s1["delta_etot_pass"] is True
    assert s1["delta_etot_pct"] <= 0.10, f"Energy error {s1['delta_etot_pct']}% exceeds 0.10%"


def test_step2_continuation_gate_6c_acceptance():
    results = load_extracted_results()
    s2 = results["step2_terminal_continuation"]
    
    # 1. Terminal force discrepancy
    assert s2["delta_RF2_pass"] is True
    assert s2["delta_RF2_N"] <= 5.0, f"Terminal force discrepancy {s2['delta_RF2_N']} N exceeds 5.0 N"
    
    # 2. Terminal damage discrepancy
    assert s2["delta_dmax_pass"] is True
    assert s2["delta_dmax"] <= 0.0200, f"Terminal damage discrepancy {s2['delta_dmax']} exceeds 0.0200"
    
    # 3. Terminal total energy discrepancy
    assert s2["delta_etot_pass"] is True
    assert s2["delta_etot_pct"] <= 0.50, f"Terminal energy error {s2['delta_etot_pct']}% exceeds 0.50%"


def test_energy_evolution_monotonicity():
    results = load_extracted_results()
    energies = results["energies_history"]
    
    e_frac_vals = [e["e_frac_mJ"] for e in energies]
    e_tot_vals = [e["e_tot_mJ"] for e in energies]
    
    # Fracture energy must be strictly monotonically non-decreasing
    for i in range(1, len(e_frac_vals)):
        assert e_frac_vals[i] >= e_frac_vals[i-1] - 1e-12, f"Fracture dissipation decreased at inc {i}: {e_frac_vals[i]} < {e_frac_vals[i-1]}"
        
    # Total energy must increase as tensile displacement is applied
    s2_e_tot = [e["e_tot_mJ"] for e in energies if e["step"] == 2]
    for i in range(1, len(s2_e_tot)):
        assert s2_e_tot[i] > s2_e_tot[i-1], f"Total energy did not increase at step 2 inc {i}"


def test_frozen_uel_source_integrity():
    import hashlib
    pkg_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "57_method_c_stage_c1_2_cycle1_continuation"
    uel_path = pkg_dir / "f42_mixed_uel.for"
    assert uel_path.is_file()
    h = hashlib.sha256(uel_path.read_bytes()).hexdigest().lower()
    assert h == FROZEN_UEL_HASH
