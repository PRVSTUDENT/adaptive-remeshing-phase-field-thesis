import json
import hashlib
import re
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R7"

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def test_package_files_exist():
    assert CANDIDATE_DIR.exists(), f"Candidate dir {CANDIDATE_DIR} does not exist"
    required = [
        "M2STATE_FRACFIX_RESTART1R1R7.inp",
        "f42_mixed_uel.for",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "job_notifications.sh",
        "validate_package_manifest.py",
        "M2STATE_FRACFIX_RESTART1R1R7.pbs",
        "submit_m2state_fracfix_restart1r1r7.sh",
        "PACKAGE_MANIFEST.json"
    ]
    for rf in required:
        p = CANDIDATE_DIR / rf
        assert p.exists(), f"Missing required package file: {rf}"

def test_package_manifest_verification():
    man_path = CANDIDATE_DIR / "PACKAGE_MANIFEST.json"
    m = json.loads(man_path.read_text(encoding="utf-8"))
    assert "files" in m
    for fname, exp_hash in m["files"].items():
        fp = CANDIDATE_DIR / fname
        assert fp.exists(), f"Manifest file missing on disk: {fname}"
        actual = sha256_file(fp)
        assert actual.lower() == exp_hash.lower(), f"Hash mismatch for {fname}"

def test_property_abi_6_slots_in_deck():
    inp_path = CANDIDATE_DIR / "M2STATE_FRACFIX_RESTART1R1R7.inp"
    text = inp_path.read_text(encoding="utf-8")
    
    # Check UEL declarations have PROPERTIES=6
    for u_type in ["TYPE=U1", "TYPE=U2", "TYPE=U3", "TYPE=U4"]:
        pattern = rf"\*USER ELEMENT,\s+{u_type}[^\n]*PROPERTIES=6"
        assert re.search(pattern, text, re.IGNORECASE), f"PROPERTIES=6 missing in {u_type}"
        
    # Check UEL PROPERTY cards have 6 values with NPHYS=4894.0 in slot 6 and k=1e-7 in slot 5
    for elset in ["ELSET=E_U1", "ELSET=E_U2", "ELSET=E_U3", "ELSET=E_U4"]:
        pattern = rf"\*UEL PROPERTY,\s+{elset}\s*\n\s*0\.015000,\s*0\.002700,\s*210\.000000,\s*0\.300000,\s*1\.0000e-07,\s*4894\.0"
        assert re.search(pattern, text), f"Property card mismatch for {elset}"

def test_uel_subroutine_6_property_abi_and_consistent_residual():
    for_path = CANDIDATE_DIR / "f42_mixed_uel.for"
    code = for_path.read_text(encoding="utf-8")
    
    # Check PROPS assignments
    assert "E_L0   = PROPS(1)" in code
    assert "E_GC   = PROPS(2)" in code
    assert "E_MOD  = PROPS(3)" in code
    assert "E_NU   = PROPS(4)" in code
    assert "E_K    = PROPS(5)" in code
    assert "N_PHYS = INT(PROPS(6))" in code
    
    # Check DEG = (ONE - D_VAL)**2 + E_K
    assert "DEG   = (ONE - D_VAL)**2 + E_K" in code
    
    # Check consistent Newton phase residual
    assert "RHS(I,1) = RHS(I,1) - AMATRX(I,J)*U(J)" in code
    assert "AMATRX(I,J) = AMATRX(I,J) + CJAC * (" in code
    assert "RHS(I,1) = RHS(I,1) + CJAC * TWO * HIST * N_VEC(I)" in code

def test_source_ingestion_from_valid_1386469():
    stat_path = CANDIDATE_DIR / "STATE_TRANSFER_ARTIFACT.json"
    stat = json.loads(stat_path.read_text(encoding="utf-8"))
    assert stat["source_job_id"] == "1386469.mmaster02"
    assert stat["source_u1_mm"] == 0.005
    assert stat["target_physical_elements"] == 4894
    assert stat["target_nodes"] == 4998

def test_mesh_topology_and_boundary():
    inp_path = CANDIDATE_DIR / "M2STATE_FRACFIX_RESTART1R1R7.inp"
    text = inp_path.read_text(encoding="utf-8")
    
    # Check Equation
    assert "*EQUATION" in text
    assert "N_TOP, 1, 1.0, 99999, 1, -1.0" in text
    
    # Check Steps
    assert "*STEP, NAME=Step-1-PhaseInit" in text
    assert "*STEP, NAME=Step-2-Continuation" in text
    assert "99999, 1, 1, 0.005000" in text # Step 1
    assert "99999, 1, 1, 0.010000" in text # Step 2
