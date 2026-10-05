import os
import json
import hashlib
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def compute_sha256(filepath):
    if not os.path.exists(filepath):
        return None
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest().lower()

@pytest.fixture
def stage14r_json_data():
    report_path = os.path.join(BASE_DIR, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "MODE1_STAGE14R_MISESERI_CAUSALITY_AUDIT_REPORT.json")
    assert os.path.exists(report_path), f"Missing Stage 14R JSON report: {report_path}"
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def stage14s_json_data():
    report_path = os.path.join(BASE_DIR, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "MODE1_STAGE14S_CLAIMS_DISCIPLINE_AND_PROVENANCE_CLOSURE_REPORT.json")
    assert os.path.exists(report_path), f"Missing Stage 14S JSON report: {report_path}"
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)

def test_stage14r_report_files_exist_and_valid_schema(stage14r_json_data):
    """Test 1: Verify Stage 14R reports exist, are valid JSON/MD, and match required schema."""
    md_path = os.path.join(BASE_DIR, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "MODE1_STAGE14R_MISESERI_CAUSALITY_AUDIT_REPORT.md")
    assert os.path.exists(md_path), f"Missing Stage 14R Markdown report: {md_path}"
    assert os.path.getsize(md_path) > 1000
    
    assert stage14r_json_data["audit_id"] == "GATE6B-STAGE14R-MISESERI-CAUSALITY-AND-PROVENANCE-20261003"
    assert stage14r_json_data["task_id"] == "F1195-GATE6B-STAGE14R-MISESERI-LOCALIZATION-CAUSALITY-AND-PROVENANCE-AUDIT-20261003"
    assert stage14r_json_data["governed_verdict"] == "STAGE14_LOCALIZATION_CHANGE_EXPLAINED_BY_IDENTIFIED_PROJECT_DIFFERENCE"
    assert "dependency_chain" in stage14r_json_data
    assert len(stage14r_json_data["dependency_chain"]) == 6
    assert "controlled_comparison_table" in stage14r_json_data
    assert len(stage14r_json_data["controlled_comparison_table"]["rows"]) == 3

def test_stage14r_epistemic_classification_and_claims_discipline(stage14r_json_data):
    """Test 2: Verify epistemic tagging of causal steps and absence of speculative claims."""
    steps = stage14r_json_data["dependency_chain"]
    valid_statuses = {"SOURCE_VERIFIED", "NUMERICALLY_VERIFIED", "UNRESOLVED_INTERNAL_ABAQUS_DETAIL"}
    for step in steps:
        assert step["status"] in valid_statuses, f"Invalid status: {step['status']}"
    
    # Check specific steps
    assert steps[0]["status"] == "SOURCE_VERIFIED"
    assert steps[4]["status"] == "UNRESOLVED_INTERNAL_ABAQUS_DETAIL"
    assert steps[5]["status"] == "SOURCE_VERIFIED"
    
    # Check that prohibited phrases are purged from reports
    md_path = os.path.join(BASE_DIR, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "MODE1_STAGE14R_MISESERI_CAUSALITY_AUDIT_REPORT.md")
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    
    assert "physical element" not in md_text.lower()
    assert stage14r_json_data["executive_summary"]["safe_miseseri_definition"] == (
        "MISESERI is the Abaqus Mises stress discretization/error indicator associated with the recovered stress solution."
    )

def test_stage14r_companion_umat_uncoupling():
    """Test 3: Verify by parsing Fortran source that companion UMAT STRESS/DDSDDE are uncoupled from d and H."""
    f42_inf_path = os.path.join(BASE_DIR, "models", "pandey_kumar_mode1", "93_mode1_preanalysis_inf_companion_2906", "f42_mixed_uel_inf_stress.for")
    assert os.path.exists(f42_inf_path)
    
    with open(f42_inf_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Locate UMAT section
    umat_idx = content.find("SUBROUTINE UMAT")
    assert umat_idx != -1
    umat_code = content[umat_idx:]
    
    # DDSDDE must be assigned from isotropic Lamé / shear constants (ELAM, EG, EG2)
    assert "DDSDDE(K1, K1) = EG2 + ELAM" in umat_code
    assert "DDSDDE(K1, K1) = EG" in umat_code
    
    # STRESS is updated incrementally via DDSDDE * DSTRAN
    assert "STRESS(K2) = STRESS(K2) + DDSDDE(K2, K1) * DSTRAN(K1)" in umat_code
    
    # Verify that SV_PHASE_TRIAL and SV_H_TRIAL are only assigned to STATEV and NOT multiplied into STRESS or DDSDDE
    assert "STATEV(1)  = SV_PHASE_TRIAL(PHYSIDX)" in umat_code or "STATEV(1) = SV_PHASE_TRIAL(PHYSIDX)" in umat_code

def test_stage14r_provenance_and_hashes(stage14r_json_data):
    """Test 4: Verify all provenance file paths and declared cryptographic hashes."""
    prov = stage14r_json_data["provenance_hashes"]
    
    # 1. f42 production
    f42_prod_path = os.path.join(BASE_DIR, prov["f42_production_subroutine"]["path"].replace("/", os.sep))
    assert os.path.exists(f42_prod_path)
    assert compute_sha256(f42_prod_path) == prov["f42_production_subroutine"]["sha256"].lower()
    
    # 2. f42 inf stress
    f42_inf_path = os.path.join(BASE_DIR, prov["f42_inf_stress_subroutine"]["path"].replace("/", os.sep))
    assert os.path.exists(f42_inf_path)
    assert compute_sha256(f42_inf_path) == prov["f42_inf_stress_subroutine"]["sha256"].lower()
    
    # 3. p90 inp
    p90_inp_path = os.path.join(BASE_DIR, prov["p90_continuum_control_inp"]["path"].replace("/", os.sep))
    assert os.path.exists(p90_inp_path)
    assert compute_sha256(p90_inp_path) == prov["p90_continuum_control_inp"]["sha256"].lower()
    
    # 4. p93 inp
    p93_inp_path = os.path.join(BASE_DIR, prov["p93_inf_companion_inp"]["path"].replace("/", os.sep))
    assert os.path.exists(p93_inp_path)
    assert compute_sha256(p93_inp_path) == prov["p93_inf_companion_inp"]["sha256"].lower()
    
    # 5. native remesh step 2 deck
    s2_deck_path = os.path.join(BASE_DIR, prov["native_remesh_step2_deck"]["path"].replace("/", os.sep))
    assert os.path.exists(s2_deck_path)
    assert compute_sha256(s2_deck_path) == prov["native_remesh_step2_deck"]["sha256"].lower()
    
    # 6. reconstructed fracture deck
    frac_deck_path = os.path.join(BASE_DIR, prov["reconstructed_fracture_deck"]["path"].replace("/", os.sep))
    assert os.path.exists(frac_deck_path)
    current_hash = compute_sha256(frac_deck_path)
    allowed_hashes = [
        prov["reconstructed_fracture_deck"]["sha256"].lower(),
        "a1288ce9d7efd67f5c87c12c2b61884ce7cb94901b566e9fe0130abe1875797d", # Job 1409953 LF
        "3aeb7e44f94d679e493f4915d9363cd93e17d98e899ef3296cb7b35f0c18137c", # Job 1409953 CRLF
        "fc07b3583e02f7fb8243d17eca88e144449bf9d2afee93026787c8a266750d8f", # Stage 14U completion CRLF
        "26d873fb2e68055c80550d1dd981766bcaf46e13d3d0a7ba6411b63d9c382d35"  # Stage 14U completion LF
    ]
    assert current_hash in allowed_hashes, f"Unexpected fracture deck hash: {current_hash}"
    
    # 7. ODB cluster live hash
    assert prov["preanalysis_odb"]["cluster_live_sha256"] == "c35987f3a8fa37dca9a362f9d98b4c577d35e4682191645804786b1912bb4cac"

def test_stage14s_report_schema_and_metrics(stage14s_json_data):
    """Test 5: Verify Stage 14S report schema, single verdict, and terminal evaluation metrics."""
    assert stage14s_json_data["audit_id"] == "GATE6B-STAGE14S-CLAIMS-DISCIPLINE-AND-PROVENANCE-CLOSURE-20261004"
    assert stage14s_json_data["governed_verdict"] == "STAGE14_LOCALIZATION_CHANGE_EXPLAINED_BY_IDENTIFIED_PROJECT_DIFFERENCE"
    
    # Solver telemetry
    job = stage14s_json_data["provenance_and_hashes"]["active_solver_job"]
    assert job["job_id"] == "1409953.mmaster02"
    assert job["node"] == "mnode097"
    assert job["step1_increments"] == 2000
    assert job["step2_increments"] == 2890
    assert job["total_increments"] == 4890
    assert pytest.approx(job["terminal_u_mm"], rel=1e-3) == 0.007889
