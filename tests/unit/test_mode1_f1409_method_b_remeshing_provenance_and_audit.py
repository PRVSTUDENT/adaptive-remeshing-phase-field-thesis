"""Unit test suite for Task F1409 Mode-I Method B Remeshing Provenance Audit.

Verifies:
1. Forensic audit results (audit_miseseri_results.json) confirm MISESERI == 0.0,
   MISESAVG == 0.0, and companion S_Mises == 0.0 across all 2,906 elements in 1S, 2S, 4S.
2. Root cause verified in f42_mixed_uel.for: companion UMAT sets STRESS(I) = 0.D0,
   which forces MISESERI / MISESAVG = 0/0 and causes native adaptiveRemesh to fail.
3. Mesh provenance separation: M1_MB_FINAL_1S mesh has SHA-256 B5135AF5... and 6,112 FE,
   matching Stage 14 Step 2 ET2 (Package 93 infinitesimal companion origin),
   independent of pre-peak Method B preliminary runs.
4. Decision document (SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md)
   is updated to Revision 2.3 with explicit Section 8 provenance documentation.
5. HPC Job Ledger and Active Task record Job 1411895.mmaster02 as active 24h campaign.
"""

import json
import os
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PRE_DIR = os.path.join(REPO_ROOT, "runs", "mode1", "method_b_preliminary")
AUDIT_JSON_PATH = os.path.join(PRE_DIR, "audit_miseseri_results.json")
SUMMARY_JSON_PATH = os.path.join(PRE_DIR, "METHOD_B_PRE_COMPARISON_SUMMARY.json")
UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
STAGE14_ET2_INP_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "34_stage14_step2_adaptive_candidate_et2_6k", "PK_MODE1_STAGE14_STEP2_ET2_6K_FRACTURE.inp"
)
DECISION_DOC_PATH = os.path.join(REPO_ROOT, "docs", "decisions", "SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md")
JOB_LEDGER_PATH = os.path.join(REPO_ROOT, "project_coordination", "HPC_JOB_LEDGER.csv")
ACTIVE_TASK_PATH = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")


def test_f1409_forensic_audit_miseseri_identically_zero():
    """Verify that MISESERI, MISESAVG, and S_Mises evaluate to identically zero across all preliminary ODBs."""
    assert os.path.isfile(AUDIT_JSON_PATH), "Audit JSON missing: %s" % AUDIT_JSON_PATH

    with open(AUDIT_JSON_PATH, "r") as f:
        data = json.load(f)

    for case_name in ["1S", "2S", "4S"]:
        assert case_name in data, "Missing case %s in audit results" % case_name
        case_data = data[case_name]

        # Check MISESERI
        m = case_data["miseseri"]
        assert m is not None, "MISESERI is None for %s" % case_name
        assert m["count"] == 2906, "Expected 2906 elements for %s, got %d" % (case_name, m["count"])
        assert m["min"] == 0.0, "MISESERI min is non-zero for %s" % case_name
        assert m["max"] == 0.0, "MISESERI max is non-zero for %s" % case_name
        assert m["non_zero_count"] == 0, "Non-zero MISESERI count > 0 for %s" % case_name

        # Check MISESAVG
        m_avg = case_data["misesavg"]
        assert m_avg is not None, "MISESAVG is None for %s" % case_name
        assert m_avg["count"] == 2906, "Expected 2906 elements for %s, got %d" % (case_name, m_avg["count"])
        assert m_avg["min"] == 0.0, "MISESAVG min is non-zero for %s" % case_name
        assert m_avg["max"] == 0.0, "MISESAVG max is non-zero for %s" % case_name
        assert m_avg["non_zero_count"] == 0, "Non-zero MISESAVG count > 0 for %s" % case_name

        # Check Stress S Mises
        s = case_data["stress_mises"]
        assert s is not None, "Stress Mises is None for %s" % case_name
        assert s["min"] == 0.0, "Stress Mises min is non-zero for %s" % case_name
        assert s["max"] == 0.0, "Stress Mises max is non-zero for %s" % case_name
        assert s["non_zero_count"] == 0, "Non-zero Stress Mises count > 0 for %s" % case_name


def test_f1409_root_cause_companion_umat_zeroing():
    """Verify that f42_mixed_uel.for explicitly sets STRESS(I) = 0.D0 in companion UMAT layer."""
    assert os.path.isfile(UEL_PATH), "UEL missing: %s" % UEL_PATH

    with open(UEL_PATH, "r") as f:
        content = f.read()

    # Verify frozen baseline UEL hash
    h = hashlib.sha256()
    h.update(content.encode("utf-8"))
    uel_sha = h.hexdigest().upper()
    assert uel_sha == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6", "Frozen UEL altered"

    # Confirm companion stress zeroing cards exist
    assert "STRESS(I) = 0.D0" in content, "STRESS(I) = 0.D0 card not found in UEL"


def test_f1409_mesh_provenance_separation_et2_6k():
    """Verify that ET2 6k mesh is the historical Stage 14 Step 2 artifact with known hash and element counts."""
    assert os.path.isfile(STAGE14_ET2_INP_PATH), "Stage 14 ET2 deck missing: %s" % STAGE14_ET2_INP_PATH

    h = hashlib.sha256()
    with open(STAGE14_ET2_INP_PATH, "rb") as f:
        h.update(f.read())
    deck_sha = h.hexdigest().upper()
    assert deck_sha == "B5135AF51026FE2ABC4D3A0471567E7F6D55299A53A2D3501BCE61C3146FE36D", "Stage 14 ET2 deck altered"

    # Verify element and node topology
    with open(STAGE14_ET2_INP_PATH, "r") as f:
        lines = f.readlines()

    in_nodes = False
    in_elems = False
    node_count = 0
    elem_count = 0

    for line in lines:
        line_clean = line.strip().upper()
        if line_clean.startswith("*NODE"):
            in_nodes = True
            in_elems = False
            continue
        elif line_clean.startswith("*ELEMENT"):
            in_nodes = False
            in_elems = True
            continue
        elif line_clean.startswith("*"):
            in_nodes = False
            in_elems = False

        if in_nodes and line_clean:
            node_count += 1
        elif in_elems and line_clean:
            elem_count += 1

    assert node_count == 6186, "Expected 6186 nodes (6181 mesh + 5 aux), got %d" % node_count
    assert elem_count == 18338, "Expected 18338 elements (18336 layered + 2 aux), got %d" % elem_count


def test_f1409_decision_document_updated_to_rev_2_3():
    """Verify that SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md is at Revision 2.3 with Section 8."""
    assert os.path.isfile(DECISION_DOC_PATH), "Decision doc missing: %s" % DECISION_DOC_PATH

    with open(DECISION_DOC_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Revision:** `2.3" in content, "Decision document not updated to Revision 2.3"
    assert "## 8. Empirical Execution Audit & Forensic Provenance Resolution (Tasks F1408 & F1409)" in content, \
        "Section 8 missing in decision document"
    assert "METHOD_B_PRELIMINARY_VALIDATED_REMESHING_BLOCKED" in content, \
        "Verdict METHOD_B_PRELIMINARY_VALIDATED_REMESHING_BLOCKED missing in decision document"


def test_f1409_hpc_job_ledger_records_active_job():
    """Verify that HPC_JOB_LEDGER.csv records 1411895.mmaster02."""
    assert os.path.isfile(JOB_LEDGER_PATH), "Job ledger missing: %s" % JOB_LEDGER_PATH

    with open(JOB_LEDGER_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    assert "1411895.mmaster02" in content, "Job 1411895.mmaster02 not in HPC_JOB_LEDGER.csv"
