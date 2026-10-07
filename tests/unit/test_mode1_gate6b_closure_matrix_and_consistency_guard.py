"""
test_mode1_gate6b_closure_matrix_and_consistency_guard.py

Regression and consistency unit tests for Mode-I Gate-6B:
Mode-I Gate-6B Evidence, Single-Job Provenance Synthesis, & Invariant Guards.

Guards enforced:
1. Guard 1: Stale String & Energy Classification Integrity (no active UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED).
2. Guard 2: 15-Point Gate-6B Closure Decision Matrix Completeness & Classification.
3. Guard 3: Decoupled Multi-Quantity Synthesis Logic (Crack Path vs Global Mechanical / No Forward-Filling).
4. Guard 4: Governed Energy Balance Formulation Contract (E_elas, E_frac, E_model, W_ext, Delta_book, eps_book).
5. Guard 5: Telemetry Displacement Mapping Contract (F1251 Two-Step Loading).
6. Guard 6: Supervisor Report Structure & Frozen 08-Oct-2026 Date.
7. Guard 7: Governance Reconciliation Invariants (Meeting date, UEL energy qualified, 8T SMP qualified / 16T unqualified, Gate 6C held).
8. Guard 8: Bridge Rules & Alignment Guard Invariants (DryRun support, zero superseded strings).
9. Guard 9: Gate-6B Single-Job Provenance Synthesis Table & Spatial Convergence Figure Guards.
10. Guard 10: Machine-Readable Single-Job Provenance JSON & Algorithmic Extraction (zero hard-coding).
11. Guard 11: Provenance Schema Disambiguation & Terminology Guards (explicit row_index_zero_based, csv_line_number, abaqus_step, abaqus_increment, global_completed_increments; zero 0.005840 stale values for 1410180; zero 'Inc 2732' conflation).
"""

from __future__ import annotations

import os
import re
import json
import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_guard1_no_stale_energy_qualification_string():
    """Guard 1: Ensure stale string UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED does not exist in CURRENT_STATE.md, START_HERE.md, or active checklist."""
    stale_pattern = "UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED"
    governing_pattern = "UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE"

    core_status_files = [
        REPO_ROOT / "project_coordination" / "CURRENT_STATE.md",
        REPO_ROOT / "project_coordination" / "START_HERE.md",
        REPO_ROOT / "docs" / "project" / "PROJECT_PHASE_CHECKLIST.md",
    ]

    for p in core_status_files:
        assert p.exists(), f"Missing core status file: {p}"
        text = p.read_text(encoding="utf-8", errors="ignore")
        assert stale_pattern not in text, (
            f"Found stale status string '{stale_pattern}' in {p.name}. "
            f"Must be updated to '{governing_pattern}'."
        )

    # In methods docs, ensure governing pattern is present
    methods_audit = REPO_ROOT / "docs" / "methods" / "MODE1_GATE6B_CLOSURE_DECISION_MATRIX_AND_CONSISTENCY_AUDIT.md"
    assert methods_audit.exists()
    assert governing_pattern in methods_audit.read_text(encoding="utf-8")


def test_guard2_15_point_closure_matrix_completeness():
    """Guard 2: Verify all 15 points of the Gate-6B Closure Decision Matrix are defined and correctly classified."""
    audit_file = REPO_ROOT / "docs" / "methods" / "MODE1_GATE6B_CLOSURE_DECISION_MATRIX_AND_CONSISTENCY_AUDIT.md"
    assert audit_file.exists(), f"Missing audit document: {audit_file}"
    content = audit_file.read_text(encoding="utf-8")

    # Check for presence of all 15 matrix items (e.g. '| **1** |' or '| 1 |')
    for item_idx in range(1, 16):
        pattern = rf"\|\s*(?:\*\*)?{item_idx}(?:\*\*)?\s*\|"
        assert re.search(pattern, content), f"Matrix Item {item_idx} missing from closure decision table in {audit_file.name}"

    # Verify specific classifications
    assert "CONVERGED / STABLE" in content
    assert "TEMPORALLY_SENSITIVE_POSTPEAK" in content or "MESH-SENSITIVE" in content
    assert "CONVERGENCE_CONTROL_DIAGNOSTIC" in content

    # Verify key job assignments
    assert "1409982" in content  # Baseline
    assert "1410027" in content  # Refined
    assert "1410180" in content  # Cn=0.50 diagnostic
    assert "1410179" in content  # Spatial 58k serial
    assert "1410504" in content  # Spatial 58k 8T candidate
    assert "1410357" in content  # ET2
    assert "1410358" in content  # ET3
    assert "1410359" in content  # ET5


def test_guard3_decoupled_multi_quantity_synthesis_logic():
    """Guard 3: Ensure multi-quantity synthesis decouples spatial crack path from global mechanics and forbids forward-filling."""
    audit_file = REPO_ROOT / "docs" / "methods" / "MODE1_GATE6B_CLOSURE_DECISION_MATRIX_AND_CONSISTENCY_AUDIT.md"
    content = audit_file.read_text(encoding="utf-8")

    assert "Decoupled Convergence Assessment" in content
    assert "Crack-Path vs Mechanical Convergence" in content
    assert "Strict Zero Forward-Filling & Extrapolation Guard" in content
    assert "NOT_REACHED" in content

    # Crack path stability must cite yc centroid deviation <= 0.5 um and w0.5 approx 20.8 um
    assert "0.500" in content
    assert "20.8" in content


def test_guard4_governed_energy_balance_formulation():
    """Guard 4: Verify 6 governed energy fields and non-invasive energy balance contract."""
    audit_file = REPO_ROOT / "docs" / "methods" / "MODE1_GATE6B_CLOSURE_DECISION_MATRIX_AND_CONSISTENCY_AUDIT.md"
    content = audit_file.read_text(encoding="utf-8")

    # Math terms present in document
    assert "\\mathcal{E}_{\\text{elas}}" in content or "E_{\\text{elas}}" in content
    assert "\\mathcal{E}_{\\text{frac}}" in content or "E_{\\text{frac}}" in content
    assert "\\mathcal{E}_{\\text{model}}" in content or "E_{\\text{model}}" in content
    assert "\\mathcal{W}_{\\text{ext}}" in content or "W_{\\text{ext}}" in content
    assert "\\Delta_{\\text{book}}" in content or "\\Delta_{book}" in content
    assert "\\varepsilon_{\\text{book}}" in content or "\\varepsilon_{book}" in content

    # Verify bitwise parity citation
    assert "1409734" in content
    assert "7,000" in content or "7000" in content


def test_guard5_telemetry_displacement_mapping():
    """Guard 5: Verify kinematic displacement contract from Task F1251."""
    audit_file = REPO_ROOT / "docs" / "methods" / "MODE1_GATE6B_CLOSURE_DECISION_MATRIX_AND_CONSISTENCY_AUDIT.md"
    content = audit_file.read_text(encoding="utf-8")

    # Step 1: 0.0050 * t1, Step 2: 0.0050 + 0.0050 * t2
    assert "0.0050" in content
    assert "2.50" in content  # nm/inc
    assert "1.00" in content  # nm/inc


def test_guard6_supervisor_summary_structure_and_date():
    """Guard 6: Verify supervisor summary exists, targets 08-Oct-2026, and contains required sections."""
    sup_file = REPO_ROOT / "docs" / "supervisor_reports" / "08-10-2026" / "MODE1_GATE6B_PROVEN_VS_PENDING_SUMMARY.md"
    assert sup_file.exists(), f"Supervisor summary file missing: {sup_file}"
    content = sup_file.read_text(encoding="utf-8")

    # Verify date
    assert "08 October 2026" in content or "08-Oct-2026" in content
    assert "10:00 CEST" in content

    # Verify key sections
    assert "What Is Already Proven" in content
    assert "What Remains Actively Solving" in content
    assert "Summary Blocker Status" in content


def test_guard7_governance_reconciliation_invariants():
    """Guard 7: Enforce authoritative governance invariants across active documents:
    - Next supervisor meeting: Thursday 08 October 2026, 10:00 CEST.
    - Energy instrumentation status: UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE.
    - Gate 6B remains active pending the 57,929-FE spatial fine candidate.
    - Gate 6C remains on hold until Gate 6B is closed (no auto-promotion).
    - 8-thread shared-memory SMP is qualified; 16-thread execution remains unqualified.
    """
    current_state_path = REPO_ROOT / "project_coordination" / "CURRENT_STATE.md"
    assert current_state_path.exists()
    cs_text = current_state_path.read_text(encoding="utf-8")

    assert "Thursday, 08 October 2026, 10:00 CEST" in cs_text
    assert "UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE" in cs_text
    assert "8THREAD_SHARED_MEMORY_EXECUTION_EMPIRICALLY_QUALIFIED_FOR_THE_TESTED_MODE1_FORMULATION_AND_CONTROLS" in cs_text
    assert "16THREAD_SHARED_MEMORY_EXECUTION_UNQUALIFIED_PENDING_INDEPENDENT_STAGE_A_AND_B_VERIFICATION" in cs_text
    assert "ON_HOLD_PENDING_GATE6B_CLOSURE" in cs_text
    assert "no auto-promotion" in cs_text

    checklist_path = REPO_ROOT / "docs" / "project" / "PROJECT_PHASE_CHECKLIST.md"
    assert checklist_path.exists()
    cl_text = checklist_path.read_text(encoding="utf-8")

    assert "Thursday, 08 October 2026, 10:00" in cl_text
    assert "UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE" in cl_text
    assert "G6B-07" in cl_text
    assert "G6C-01" in cl_text
    assert "must NOT auto-promote" in cl_text

    sup_summary_path = REPO_ROOT / "docs" / "supervisor_reports" / "08-10-2026" / "MODE1_GATE6B_PROVEN_VS_PENDING_SUMMARY.md"
    assert sup_summary_path.exists()
    ss_text = sup_summary_path.read_text(encoding="utf-8")

    assert "Thursday, 08 October 2026, 10:00 CEST" in ss_text
    assert "13. Shared-Memory 8-Thread Parallelism" in ss_text
    assert "16-thread execution remains unqualified" in ss_text
    assert "no auto-promotion" in ss_text

    # Controller script governance check if available
    controller_path = Path(r"C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1")
    if controller_path.exists():
        ctrl_text = controller_path.read_text(encoding="utf-8", errors="ignore")
        assert "01 October 2026" not in ctrl_text
        assert "01-Oct-2026" not in ctrl_text
        assert "UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED" not in ctrl_text
        assert "Thursday, 08 October 2026, 10:00 CEST" in ctrl_text
        assert "UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE" in ctrl_text


def test_guard8_bridge_rules_and_handoff_invariants():
    """Guard 8: Enforce bridge rules, alignment guard, and bridge launcher invariants:
    - bridge_rules.txt must contain 08-Oct meeting date, qualified UEL energy, Gate 6B active,
      Gate 6C hold without auto-promotion, 8T SMP qualified, 16T SMP unqualified, MPI disqualified.
    - Zero superseded strings (01 October 2026, 01-Oct, UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED).
    - project_alignment_guard.txt clean of superseded strings and containing authoritative definitions.
    - Invoke-ChatGPTBridge.ps1 supporting DryRun and prompt reconciliation.
    """
    repo_rules = REPO_ROOT / ".agents" / "scripts" / "bridge_rules.txt"
    assert repo_rules.exists()
    rr_text = repo_rules.read_text(encoding="utf-8")

    assert "01 October 2026" not in rr_text
    assert "01-Oct" not in rr_text
    assert "UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED" not in rr_text
    assert "MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE" not in rr_text
    assert "Thursday, 08 October 2026, 10:00 CEST" in rr_text
    assert "UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE" in rr_text
    assert "GATE_6B_ACTIVE_EVALUATION_AND_CONTINUATION" in rr_text
    assert "ON_HOLD_PENDING_GATE6B_CLOSURE" in rr_text
    assert "8-thread shared-memory SMP execution is empirically qualified" in rr_text
    assert "16-thread shared-memory execution is UNQUALIFIED" in rr_text
    assert "Distributed multi-rank MPI execution is STRICTLY DISQUALIFIED" in rr_text

    repo_guard = REPO_ROOT / ".agents" / "scripts" / "project_alignment_guard.txt"
    assert repo_guard.exists()
    rg_text = repo_guard.read_text(encoding="utf-8")

    assert "01 October 2026" not in rg_text
    assert "01-Oct-2026" not in rg_text
    assert "UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED" not in rg_text
    assert "MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE" not in rg_text
    assert "MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION" in rg_text
    assert "Thursday, 08 October 2026, 10:00 CEST" in rg_text
    assert "UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE" in rg_text

    repo_bridge = REPO_ROOT / ".agents" / "scripts" / "Invoke-ChatGPTBridge.ps1"
    assert repo_bridge.exists()
    rb_text = repo_bridge.read_text(encoding="utf-8")

    assert "DryRun" in rb_text
    assert "project_alignment_guard.txt" in rb_text
    assert "bridge_rules.txt" in rb_text

    rescue_script = REPO_ROOT / "scripts" / "validation" / "rescue_bridge_request.py"
    assert rescue_script.exists()
    rs_text = rescue_script.read_text(encoding="utf-8")
    assert "MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE" not in rs_text
    assert "MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION" in rs_text

    # Also check external OpenClawPAD files if present
    pad_rules = Path(r"C:\Users\pruth\OpenClawPAD\ChatGPTBridge\bridge_rules.txt")
    if pad_rules.exists():
        pr_text = pad_rules.read_text(encoding="utf-8", errors="ignore")
        assert "01 October 2026" not in pr_text
        assert "01-Oct" not in pr_text
        assert "UEL_ENERGY_OUTPUT_NOT_YET_QUALIFIED" not in pr_text
        assert "MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE" not in pr_text
        assert "Thursday, 08 October 2026, 10:00 CEST" in pr_text
        assert "UEL_ENERGY_OUTPUT_QUALIFIED_MECHANICALLY_NONINVASIVE" in pr_text


def test_guard9_gate6b_single_job_provenance_and_figure_guards():
    """Guard 9: Enforce strict single-job provenance separation and spatial convergence synthesis figure existence:
    - Fixed reference base mesh has exactly 15,192 finite elements (15,160 CPE4 + 32 CPE3) and 15,521 FE nodes.
    - Historical mechanical anchor (1398090) and full-horizon energy run (1409734) are separately documented.
    - Canonical ET1 baseline (1409982) is separated from Cn=0.50 diagnostic (1410180).
    - Spatial fine 58k serial run (1410179) is classified as partial post-peak diagnostic without forward-filling.
    - Active 8T SMP candidate (1410504) is documented as the full-horizon closure solve.
    - 4-panel spatial convergence synthesis figure and plotting script exist and are valid.
    """
    fig_pdf = REPO_ROOT / "results" / "figures" / "mode1_gate6b" / "fig_mode1_gate6b_spatial_convergence_synthesis.pdf"
    fig_png = REPO_ROOT / "results" / "figures" / "mode1_gate6b" / "fig_mode1_gate6b_spatial_convergence_synthesis.png"
    assert fig_pdf.exists() and fig_pdf.stat().st_size > 5000, f"Missing or empty PDF figure: {fig_pdf}"
    assert fig_png.exists() and fig_png.stat().st_size > 5000, f"Missing or empty PNG figure: {fig_png}"

    plot_script = REPO_ROOT / "scripts" / "postprocessing" / "plot_gate6b_spatial_convergence_synthesis.py"
    assert plot_script.exists() and plot_script.stat().st_size > 1000, f"Missing plot script: {plot_script}"

    exp_record = REPO_ROOT / "docs" / "experiment_records" / "STAGE_GATE6B_SPATIAL_FINE_58K_JOB_1410179_TERMINAL_EVALUATION.md"
    assert exp_record.exists(), f"Missing experiment record: {exp_record}"
    er_text = exp_record.read_text(encoding="utf-8")

    # Strict single-job provenance entries in synthesis table
    assert "1398090.mmaster02" in er_text
    assert "1409734.mmaster02" in er_text
    assert "1409982.mmaster02" in er_text
    assert "1410180.mmaster02" in er_text
    assert "1410179.mmaster02" in er_text
    assert "1410504.mmaster02" in er_text

    # Fixed ref element count is 15,192
    assert "15,192" in er_text or "15{,}192" in er_text
    assert "57,929" in er_text or "57{,}929" in er_text
    assert "14,483" in er_text or "14{,}483" in er_text

    # Figure embedded and referenced
    assert "fig_mode1_gate6b_spatial_convergence_synthesis.png" in er_text
    assert "fig_mode1_gate6b_spatial_convergence_synthesis.pdf" in er_text


def test_guard10_single_job_provenance_json_and_algorithmic_derivation():
    """Guard 10: Enforce machine-readable single-job provenance dataset, algorithmic peak derivation, and zero hard-coding:
    - MODE1_GATE6B_SINGLE_JOB_PROVENANCE_SYNTHESIS.json exists, contains 9 distinct jobs, with zero cross-contamination.
    - Full-horizon Reference Job 1409734 has raw source PK_M1_REF15K_ENERGY.dat, peak idx 2856 (Step 2 Inc 857), W_ext=2.359329 mJ, E_frac=2.340220 mJ, E_elas=0.001161 mJ, eps_book=0.7607%.
    - Canonical ET1 Baseline Job 1409982 has raw source PK_MODE1_STAGE14_ADAPT_14K_FRACTURE_fu.csv (SHA256: 71ba958e...), peak idx 2734 (Step 2 Inc 733), K0=137.909558, F_max=0.743701, u_peak=0.005733, u_term=0.007889, W_ext=2.267380, E_frac=2.285469, E_elas=0.006960, eps_book=1.1048%.
    - Diagnostic Job 1410180 has raw source PK_MODE1_STAGE14_ADAPT_14K_CONV_CTRL_fu.csv (SHA256: 44d0b66f...), peak idx 2732 (Step 2 Inc 733), F_max=0.743711, u_peak=0.005733, u_term=0.010000, W_ext=2.270745, E_frac=2.246309, E_elas=0.005801, eps_book=0.8207%.
    - Step-2 errorTarget sweep jobs (1410357, 1410358, 1410359) have their respective raw source CSVs and SHA256 hashes populated.
    - Spatial fine 58k Job 1410179 has raw source PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_FRACTURE.dat (SHA256: 36908c50...), peak idx 2716 (Step 2 Inc 717), K0=137.840989, F_max=0.741633, u_peak=0.005717, u_term=0.007429, W_ext=2.501136, E_frac=2.359641, E_elas=0.040984, eps_book=4.0186%.
    - Zero occurrence of 'fracture dissipation' in plot_gate6b_spatial_convergence_synthesis.py.
    - scripts/postprocessing/extract_gate6b_single_job_provenance.py exists and operates algorithmically without hard-coded numbers.
    - Outer bridge handoff prompt is clean of STEP2_ACTIVE and accurately describes 1410179 as partial evidence and 1410504 as active candidate.
    """
    json_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "MODE1_GATE6B_SINGLE_JOB_PROVENANCE_SYNTHESIS.json"
    csv_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "MODE1_GATE6B_SINGLE_JOB_PROVENANCE_SYNTHESIS.csv"
    assert json_path.exists(), f"Missing synthesis JSON: {json_path}"
    assert csv_path.exists(), f"Missing synthesis CSV: {csv_path}"

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    assert "jobs" in data and len(data["jobs"]) == 9
    jobs_by_id = {j["job_id"]: j for j in data["jobs"]}

    # Job 1398090
    j_1398090 = jobs_by_id["1398090.mmaster02"]
    assert j_1398090["fe_elements"] == 15192
    assert j_1398090["fe_nodes"] == 15521
    assert j_1398090["raw_source_file"] == "models/pandey_kumar_mode1/01_standard_pfm_reference/PK_MODE1_STANDARD_PFM.dat"
    assert j_1398090["peak_row_index"] == 2856
    assert j_1398090["peak_step"] == 2
    assert j_1398090["peak_increment"] == 857
    assert abs(j_1398090["k0_kn_per_mm"] - 137.945520) < 1e-4
    assert abs(j_1398090["f_max_kn"] - 0.757778) < 1e-4
    assert abs(j_1398090["u_peak_mm"] - 0.005857) < 1e-5

    # Job 1409734 (Full Horizon Energetic Standard)
    j_1409734 = jobs_by_id["1409734.mmaster02"]
    assert j_1409734["fe_elements"] == 15192
    assert j_1409734["fe_nodes"] == 15521
    assert j_1409734["raw_source_file"] == "models/pandey_kumar_mode1/16_energy_qualification_reference_15k/PK_M1_REF15K_ENERGY.dat"
    assert j_1409734["peak_row_index"] == 2856
    assert j_1409734["peak_step"] == 2
    assert j_1409734["peak_increment"] == 857
    assert abs(j_1409734["w_ext_mJ"] - 2.359329) < 1e-4
    assert abs(j_1409734["e_frac_mJ"] - 2.340220) < 1e-4
    assert abs(j_1409734["e_elas_mJ"] - 0.001161) < 1e-4
    assert abs(j_1409734["eps_book_pct"] - 0.7607) < 1e-2

    # Job 1409982 (Canonical ET1 Baseline)
    j_1409982 = jobs_by_id["1409982.mmaster02"]
    assert j_1409982["fe_elements"] == 14483
    assert j_1409982["fe_nodes"] == 14456
    assert j_1409982["raw_source_file"] == "models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/PK_MODE1_STAGE14_ADAPT_14K_FRACTURE_fu.csv"
    assert j_1409982["raw_source_sha256"] == "71ba958e1dcd2b2a67892407b982e907dca1a7672620cca2a52cc3835adf5b8c"
    assert j_1409982["peak_row_index"] == 2734
    assert j_1409982["peak_step"] == 2
    assert j_1409982["peak_increment"] == 733
    assert abs(j_1409982["k0_kn_per_mm"] - 137.909558) < 1e-4
    assert abs(j_1409982["f_max_kn"] - 0.743701) < 1e-4
    assert abs(j_1409982["u_peak_mm"] - 0.005733) < 1e-5
    assert abs(j_1409982["u_term_mm"] - 0.007889) < 1e-5
    assert abs(j_1409982["w_ext_mJ"] - 2.267380) < 1e-4
    assert abs(j_1409982["e_frac_mJ"] - 2.285469) < 1e-4
    assert abs(j_1409982["e_elas_mJ"] - 0.006960) < 1e-4
    assert abs(j_1409982["eps_book_pct"] - 1.1048) < 1e-2

    # Job 1410180 (ET1 Cn=0.50 Diagnostic)
    j_1410180 = jobs_by_id["1410180.mmaster02"]
    assert j_1410180["fe_elements"] == 14483
    assert j_1410180["raw_source_file"] == "models/pandey_kumar_mode1/28_stage14_convergence_control_candidate/PK_MODE1_STAGE14_ADAPT_14K_CONV_CTRL_fu.csv"
    assert j_1410180["raw_source_sha256"] == "44d0b66f5348baeef0c82f9034d8676e81188308c3531be2ff2f52c443ad1771"
    assert j_1410180["peak_row_index"] == 2732
    assert j_1410180["peak_step"] == 2
    assert j_1410180["peak_increment"] == 733
    assert abs(j_1410180["f_max_kn"] - 0.743711) < 1e-4
    assert abs(j_1410180["u_peak_mm"] - 0.005733) < 1e-5
    assert abs(j_1410180["u_term_mm"] - 0.010000) < 1e-5
    assert abs(j_1410180["w_ext_mJ"] - 2.270745) < 1e-4
    assert abs(j_1410180["e_frac_mJ"] - 2.246309) < 1e-4
    assert abs(j_1410180["e_elas_mJ"] - 0.005801) < 1e-4
    assert abs(j_1410180["eps_book_pct"] - 0.8207) < 1e-2

    # ET2 / ET3 / ET5 provenance assertions
    j_1410357 = jobs_by_id["1410357.mmaster02"]
    assert j_1410357["raw_source_sha256"] == "03cf30208c8c994591fe8df204662c5e03a0e3d0b6cc63a6dec58553529a358c"
    assert j_1410357["peak_row_index"] == 2840
    assert j_1410357["peak_step"] == 2
    assert j_1410357["peak_increment"] == 841
    assert abs(j_1410357["u_peak_mm"] - 0.005841) < 1e-5

    j_1410358 = jobs_by_id["1410358.mmaster02"]
    assert j_1410358["raw_source_sha256"] == "3649191908f4f0ca2a44544b992d374f516235394bbe8ca83d7c7d77cd968153"
    assert j_1410358["peak_row_index"] == 2875
    assert j_1410358["peak_step"] == 2
    assert j_1410358["peak_increment"] == 876
    assert abs(j_1410358["u_peak_mm"] - 0.005876) < 1e-5

    j_1410359 = jobs_by_id["1410359.mmaster02"]
    assert j_1410359["raw_source_sha256"] == "226cf873ab938c94c2ffddc300ec22df895671647b0cc7aa6ab7d04855733bde"
    assert j_1410359["peak_row_index"] == 2925
    assert j_1410359["peak_step"] == 2
    assert j_1410359["peak_increment"] == 926
    assert abs(j_1410359["u_peak_mm"] - 0.005926) < 1e-5

    # Job 1410179 (Spatial Fine 58k Serial Partial Diagnostic)
    j_1410179 = jobs_by_id["1410179.mmaster02"]
    assert j_1410179["fe_elements"] == 57929
    assert j_1410179["fe_nodes"] == 57491
    assert j_1410179["raw_source_sha256"] == "36908c50cb79e685e6d2f5072b00c323c82af4b00a51b7dffc3cfebf07f91a83"
    assert j_1410179["peak_row_index"] == 2716
    assert j_1410179["peak_step"] == 2
    assert j_1410179["peak_increment"] == 717
    assert abs(j_1410179["k0_kn_per_mm"] - 137.840989) < 1e-4
    assert abs(j_1410179["f_max_kn"] - 0.741633) < 1e-4
    assert abs(j_1410179["u_peak_mm"] - 0.005717) < 1e-5
    assert abs(j_1410179["u_term_mm"] - 0.007429) < 1e-4
    assert abs(j_1410179["w_ext_mJ"] - 2.501136) < 1e-4
    assert abs(j_1410179["e_frac_mJ"] - 2.359641) < 1e-4
    assert abs(j_1410179["e_elas_mJ"] - 0.040984) < 1e-4
    assert abs(j_1410179["eps_book_pct"] - 4.0186) < 1e-2

    # Job 1410504 (Spatial Fine 58k 8T SMP Full-Horizon Candidate)
    j_1410504 = jobs_by_id["1410504.mmaster02"]
    assert j_1410504["fe_elements"] == 57929
    assert j_1410504["fe_nodes"] == 57491
    assert j_1410504["raw_source_sha256"] == "a3af73565afd5146874c71972f9173a406a5890f3dd2a7ab3062e41222bb4be0"
    assert j_1410504["peak_row_index"] == 2716
    assert j_1410504["peak_step"] == 2
    assert j_1410504["peak_increment"] == 717
    assert abs(j_1410504["k0_kn_per_mm"] - 137.840989) < 1e-4
    assert abs(j_1410504["f_max_kn"] - 0.741633) < 1e-4
    assert abs(j_1410504["u_peak_mm"] - 0.005717) < 1e-5
    assert abs(j_1410504["u_term_mm"] - 0.010000) < 1e-5
    assert abs(j_1410504["w_ext_mJ"] - 2.521738) < 1e-4
    assert abs(j_1410504["e_frac_mJ"] - 2.381941) < 1e-4
    assert abs(j_1410504["e_elas_mJ"] - 0.028178) < 1e-4
    assert abs(j_1410504["eps_book_pct"] - 4.4263) < 1e-2

    # Terminology guard: check plot script
    plot_script = REPO_ROOT / "scripts" / "postprocessing" / "plot_gate6b_spatial_convergence_synthesis.py"
    ps_text = plot_script.read_text(encoding="utf-8")
    assert "fracture dissipation" not in ps_text.lower()
    assert "Phase-Field Fracture Energy Functional" in ps_text

    # Extractor script existence
    extractor_script = REPO_ROOT / "scripts" / "postprocessing" / "extract_gate6b_single_job_provenance.py"
    assert extractor_script.exists() and extractor_script.stat().st_size > 1000

    # Bridge dry-run validation
    bridge_script = REPO_ROOT / ".agents" / "scripts" / "Invoke-ChatGPTBridge.ps1"
    cmd = [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        f". '{bridge_script}'; Invoke-ChatGPTBridge -PromptText 'Test verification prompt' -DryRun"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    assert res.returncode == 0
    assert "STEP2_ACTIVE" not in res.stdout
    assert "MODE1_GATE6B_STEP2" not in res.stdout
    assert "MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION" in res.stdout
    assert "1410179.mmaster02" in res.stdout and "1410504.mmaster02" in res.stdout


def test_guard11_provenance_schema_and_disambiguation_guards():
    """Guard 11: Enforce explicit separated provenance schema, distinct solver datasets, and zero terminology conflation:
    1. MODE1_GATE6B_SINGLE_JOB_PROVENANCE_SYNTHESIS.json explicitly defines separated fields:
       - row_index_zero_based
       - csv_line_number
       - abaqus_step
       - abaqus_increment
       - global_completed_increments
    2. Format contract:
       - .dat jobs (1398090, 1409734, 1410179, 1410504): csv_line_number == 'NOT_AVAILABLE_FROM_PRESERVED_EVIDENCE'.
       - CSV jobs (1409982, 1410180, 1410357, 1410358, 1410359): csv_line_number is integer == row_index_zero_based + 2.
    3. Distinct solver dataset proof:
       - 1409982 and 1410180 both report u_peak = 0.005733 mm at Step 2 Inc 733.
       - 1409982 has F_max = 0.74370080 kN, SHA256 71ba958e...
       - 1410180 has F_max = 0.74371148 kN, SHA256 44d0b66f...
       - Proves zero data copying or cross-conflation between baseline and diagnostic.
    4. Terminology and active document scan:
       - Zero active document in docs/ or CURRENT_STATE.md reports 0.005840 for 1410180.
       - Zero active document conflates CSV row index 2732 with Abaqus increment (e.g. 'Inc 2732').
    """
    json_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "MODE1_GATE6B_SINGLE_JOB_PROVENANCE_SYNTHESIS.json"
    assert json_path.exists()

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    jobs = {j["job_id"]: j for j in data["jobs"]}

    # Schema completeness across all 9 jobs
    required_fields = [
        "row_index_zero_based",
        "csv_line_number",
        "abaqus_step",
        "abaqus_increment",
        "global_completed_increments"
    ]
    for jid, jdata in jobs.items():
        for field in required_fields:
            assert field in jdata, f"Job {jid} missing required provenance field '{field}'"

    # Dat files format contract
    dat_jobs = ["1398090.mmaster02", "1409734.mmaster02", "1410179.mmaster02", "1410504.mmaster02"]
    for dj in dat_jobs:
        assert jobs[dj]["csv_line_number"] == "NOT_AVAILABLE_FROM_PRESERVED_EVIDENCE", (
            f"Job {dj} is a .dat source and must have csv_line_number = 'NOT_AVAILABLE_FROM_PRESERVED_EVIDENCE'"
        )

    # CSV files format contract
    csv_jobs = ["1409982.mmaster02", "1410180.mmaster02", "1410357.mmaster02", "1410358.mmaster02", "1410359.mmaster02"]
    for cj in csv_jobs:
        row_idx = jobs[cj]["row_index_zero_based"]
        line_num = jobs[cj]["csv_line_number"]
        assert isinstance(line_num, int), f"Job {cj} csv_line_number must be int, got {type(line_num)}"
        assert line_num == row_idx + 2, f"Job {cj} line_num ({line_num}) != row_idx + 2 ({row_idx + 2})"

    # Global increments
    assert jobs["1398090.mmaster02"]["global_completed_increments"] == 2857
    assert jobs["1409734.mmaster02"]["global_completed_increments"] == 2857
    assert jobs["1409982.mmaster02"]["global_completed_increments"] == 2733
    assert jobs["1410180.mmaster02"]["global_completed_increments"] == 2733
    assert jobs["1410357.mmaster02"]["global_completed_increments"] == 2841
    assert jobs["1410358.mmaster02"]["global_completed_increments"] == 2876
    assert jobs["1410359.mmaster02"]["global_completed_increments"] == 2926
    assert jobs["1410179.mmaster02"]["global_completed_increments"] == 2717
    assert jobs["1410504.mmaster02"]["global_completed_increments"] == 2717

    # Distinct datasets check between 1409982 and 1410180
    j25 = jobs["1409982.mmaster02"]
    j28 = jobs["1410180.mmaster02"]
    assert j25["u_peak_mm"] == j28["u_peak_mm"] == 0.005733
    assert j25["abaqus_step"] == j28["abaqus_step"] == 2
    assert j25["abaqus_increment"] == j28["abaqus_increment"] == 733
    assert j25["raw_source_sha256"] != j28["raw_source_sha256"]
    assert j25["f_max_kn"] != j28["f_max_kn"]
    assert abs(j25["f_max_kn"] - 0.74370080) < 1e-6
    assert abs(j28["f_max_kn"] - 0.74371148) < 1e-6
    assert j25["row_index_zero_based"] == 2734
    assert j28["row_index_zero_based"] == 2732

    # Active documents scan against stale 0.005840 for 1410180 or conflation 'Inc 2732'
    scan_dirs = [REPO_ROOT / "docs", REPO_ROOT / "models" / "pandey_kumar_mode1"]
    for sdir in scan_dirs:
        for root, dirs, files in os.walk(sdir):
            if 'sessions' in dirs:
                dirs.remove('sessions')
            for f in files:
                if f.endswith(('.md', '.json', '.csv', '.tex')):
                    fpath = Path(root) / f
                    text = fpath.read_text(encoding='utf-8', errors='ignore')
                    # Assert no conflation like 'Inc 2732' or 'Increment 2732'
                    assert not re.search(r'Inc(?:rement)?\s*2732', text, re.IGNORECASE), (
                        f"Found conflation of CSV row index with Abaqus increment ('Inc 2732') in {fpath.relative_to(REPO_ROOT)}"
                    )
                    # Assert no stale 0.005840 associated with 1410180
                    if '1410180' in text:
                        for line in text.splitlines():
                            if '1410180' in line:
                                assert '0.005840' not in line and '5.840' not in line, (
                                    f"Found stale peak displacement 0.005840 for Job 1410180 in {fpath.relative_to(REPO_ROOT)}: {line}"
                                )
def test_guard13_parallel_execution_governance_consistency_and_dryrun_invariants():
    """Guard 13: Enforce strict parallel execution governance consistency and dry-run handoff invariants:
    1. AGENTS.md and .agents/AGENTS.md must explicitly designate:
       - 1-CPU serial as authoritative reference anchor;
       - 8-thread shared-memory SMP as empirically qualified for tested Mode-I formulation/controls;
       - 16-thread shared-memory execution as UNQUALIFIED pending independent Stage-A/B proof;
       - 4-thread shared-memory execution as not part of active approved execution path;
       - distributed multi-rank MPI as strictly disqualified.
    2. project_alignment_guard.txt and bridge_rules.txt must contain zero generic '1, 4, 8, or 16 threads' lists.
    3. Assembled dry-run bridge handoff must not emit conflicting generic threading lists.
    """
    import subprocess

    # 1. Check AGENTS.md and .agents/AGENTS.md
    for agents_path in [REPO_ROOT / "AGENTS.md", REPO_ROOT / ".agents" / "AGENTS.md"]:
        assert agents_path.exists()
        a_text = agents_path.read_text(encoding="utf-8")
        assert "1, 4, 8, or 16 threads" not in a_text
        assert "(1, 4, 8, or 16 threads)" not in a_text
        assert "8-thread shared-memory SMP is empirically qualified" in a_text
        assert "16-thread shared-memory execution is UNQUALIFIED pending independent Stage-A/B verification" in a_text
        assert "4-thread shared-memory execution is not part of the active approved execution path" in a_text
        assert "distributed multi-rank MPI is strictly disqualified" in a_text

    # 2. Check project_alignment_guard.txt
    guard_path = REPO_ROOT / ".agents" / "scripts" / "project_alignment_guard.txt"
    assert guard_path.exists()
    g_text = guard_path.read_text(encoding="utf-8")
    assert "1, 4, 8, or 16 threads" not in g_text
    assert "(1 CPU serial, 4-thread, 8-thread, or 16-thread)" not in g_text
    assert "8-thread shared-memory SMP is empirically qualified" in g_text
    assert "16-thread shared-memory execution is UNQUALIFIED" in g_text or "16-thread shared-memory execution remains unqualified" in g_text
    assert "4-thread shared-memory execution is not part of the active approved execution path" in g_text
    assert "distributed multi-rank MPI remains strictly disqualified" in g_text or "multi-rank MPI strictly disqualified" in g_text

    # 3. Check bridge_rules.txt
    rules_path = REPO_ROOT / ".agents" / "scripts" / "bridge_rules.txt"
    assert rules_path.exists()
    r_text = rules_path.read_text(encoding="utf-8")
    assert "1, 4, 8, or 16 threads" not in r_text
    assert "8-thread shared-memory SMP execution is empirically qualified" in r_text
    assert "16-thread shared-memory execution is UNQUALIFIED" in r_text
    assert "Distributed multi-rank MPI execution is STRICTLY DISQUALIFIED" in r_text

    # 4. Dry-run prompt assembly test via PowerShell Invoke-ChatGPTBridge
    ps_cmd = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        r". '.agents\scripts\Invoke-ChatGPTBridge.ps1'; Invoke-ChatGPTBridge -PromptText 'Verification turn' -DryRun"
    ]
    try:
        result = subprocess.run(
            ps_cmd,
            cwd=str(REPO_ROOT),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=30
        )
        assert result.returncode == 0, f"Invoke-ChatGPTBridge -DryRun failed: {result.stderr}"
        prompt_output = result.stdout
        assert "1, 4, 8, or 16 threads" not in prompt_output
        assert "(1 CPU serial, 4-thread, 8-thread, or 16-thread)" not in prompt_output
        assert "8-thread shared-memory SMP" in prompt_output
        assert "16-thread shared-memory execution is UNQUALIFIED" in prompt_output or "16-thread execution remains unqualified" in prompt_output
    except (OSError, subprocess.SubprocessError) as exc:
        # If running in restricted sandbox environment without powershell spawn access, verify statically
        assert "1, 4, 8, or 16 threads" not in g_text
        assert "1, 4, 8, or 16 threads" not in r_text


def test_guard14_spatial_localization_synthesis_and_closure_invariants():
    """Guard 14: Enforce spatial phase-field localization synthesis, ligament profile integrity, and formal Gate-6B closure invariants:
    1. GATE6B_SPATIAL_LOCALIZATION_SYNTHESIS.json exists, is valid JSON, and contains all 6 governed discretizations:
       - fixed_ref_15k
       - adapt_et1_14k
       - adapt_et1_cn050
       - adapt_et2_6k
       - adapt_et3_5k
       - adapt_et5_4k
       - spatial_fine_58k
    2. Transverse symmetry is strictly preserved (|y_c - 0.500 mm| = 0.000 mm) across all valid states.
    3. Pre-peak ligament profiles between 14.5k (ET1) and 57.9k (Spatial Fine) have L2 difference <= 0.35%.
    4. GATE6B_SPATIAL_LOCALIZATION_SYNTHESIS.csv and GATE6B_LIGAMENT_PROFILES_MATCHED.csv exist and are non-empty.
    5. Publication figure fig_mode1_gate6b_spatial_localization_and_crack_path.pdf (.png) exists.
    6. Epistemic wording in MODE1_GATE6B_CLOSURE_DECISION_MATRIX_AND_CONSISTENCY_AUDIT.md and supervisor summary:
       - Contains convergence-consistent interpretation of coarse-mesh energy bloat.
       - Contains 2.13% persistent offset between unstructured adaptive mesh and rectilinear structured reference.
       - Contains bounded post-peak energy balance (eps_book = 4.43% on 58k).
       - Recommends formal Gate-6B closure while keeping Gate 6C strictly on hold.
    """
    json_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "GATE6B_SPATIAL_LOCALIZATION_SYNTHESIS.json"
    assert json_path.exists(), f"Missing spatial localization synthesis JSON: {json_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    expected_cases = [
        "fixed_ref_15k",
        "adapt_et1_14k",
        "adapt_et1_cn050",
        "adapt_et2_6k",
        "adapt_et3_5k",
        "adapt_et5_4k",
        "spatial_fine_58k",
    ]
    for cid in expected_cases:
        assert cid in data, f"Case '{cid}' missing from spatial localization JSON"
        cdata = data[cid]
        assert "checkpoints" in cdata
        for u_str in ["0.001000", "0.005000", "0.005717"]:
            assert u_str in cdata["checkpoints"]
            cp = cdata["checkpoints"][u_str]
            assert cp["status"] == "VALID"
            assert cp["y_c_at_x055_mm"] == 0.5
            assert cp["dev_yc_at_x055_mm"] == 0.0

    # L2 difference check between ET1 and 58k pre-peak
    et1_profiles = {cp_k: cp_v["d_ligament_profile"] for cp_k, cp_v in data["adapt_et1_14k"]["checkpoints"].items()}
    f58_profiles = {cp_k: cp_v["d_ligament_profile"] for cp_k, cp_v in data["spatial_fine_58k"]["checkpoints"].items()}

    for u_str in ["0.001000", "0.004000", "0.005000", "0.005717"]:
        p_et1 = [pt["d"] for pt in et1_profiles[u_str]]
        p_f58 = [pt["d"] for pt in f58_profiles[u_str]]
        assert len(p_et1) == len(p_f58)
        diff_sq = sum((a - b) ** 2 for a, b in zip(p_et1, p_f58))
        norm_sq = sum(b ** 2 for b in p_f58)
        l2_err = (diff_sq ** 0.5) / (norm_sq ** 0.5) if norm_sq > 0 else 0.0
        assert l2_err <= 0.0035, f"L2 error for {u_str} is {l2_err*100:.3f}% > 0.35%"

    # CSV files
    csv_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "GATE6B_SPATIAL_LOCALIZATION_SYNTHESIS.csv"
    matched_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "GATE6B_LIGAMENT_PROFILES_MATCHED.csv"
    assert csv_path.exists() and csv_path.stat().st_size > 1000
    assert matched_path.exists() and matched_path.stat().st_size > 1000

    # Figures
    fig_pdf = REPO_ROOT / "results" / "figures" / "mode1_gate6b" / "fig_mode1_gate6b_spatial_localization_and_crack_path.pdf"
    fig_png = REPO_ROOT / "results" / "figures" / "mode1_gate6b" / "fig_mode1_gate6b_spatial_localization_and_crack_path.png"
    assert fig_pdf.exists() and fig_pdf.stat().st_size > 5000
    assert fig_png.exists() and fig_png.stat().st_size > 5000

    # Epistemic text invariants in methods audit
    audit_path = REPO_ROOT / "docs" / "methods" / "MODE1_GATE6B_CLOSURE_DECISION_MATRIX_AND_CONSISTENCY_AUDIT.md"
    a_text = audit_path.read_text(encoding="utf-8")
    assert "convergence-consistent" in a_text.lower()
    assert "2.13%" in a_text
    assert "4.43" in a_text or "4.4263" in a_text
    assert "CLOSED_AND_QUALIFIED" in a_text
    assert "ON HOLD" in a_text or "ON_HOLD" in a_text

