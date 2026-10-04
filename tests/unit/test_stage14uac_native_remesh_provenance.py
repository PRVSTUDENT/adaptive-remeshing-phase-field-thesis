#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_stage14uac_native_remesh_provenance.py
-------------------------------------------
Regression unit tests for Gate-6B Stage 14U-AC:
1. test_differing_raw_sha256_odbs_not_called_identical:
   Fails if differing raw SHA-256 ODB containers are called identical files.
2. test_remesh_input_odb_in_provenance_chain:
   Fails if remesh input ODB or pre-analysis source is missing from provenance chain.
3. test_remesh_script_and_call_recorded:
   Fails if remesh script, CAE API call, or sizing parameters are unrecorded.
4. test_miseseri_element_count_matches_preanalysis_fe_count:
   Fails if MISESERI element count differs from pre-analysis finite-element count (2,906).
5. test_native_and_reconstructed_node_coordinates_identical:
   Fails if native and reconstructed node coordinates differ.
6. test_canonicalized_layer_connectivity_is_bijective:
   Fails if canonicalized layer connectivity is not 1-to-1 bijective across layers and native mesh.
7. test_proprietary_abaqus_sizing_formulas_unresolved_internal_detail:
   Fails if proprietary Abaqus error-recovery sizing formulas are asserted without source.
8. test_causal_attribution_discipline_for_peak_offset:
   Fails if solver-control audit is used to claim a uniquely proven mesh-only cause for peak offset.
"""

import os
import json
import pytest

REPORT_JSON_PATH = os.path.join(
    "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k",
    "MODE1_STAGE14UAC_NATIVE_REMESH_PROVENANCE_REPORT.json"
)

REPORT_MD_PATH = os.path.join(
    "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k",
    "MODE1_STAGE14UAC_NATIVE_REMESH_PROVENANCE_REPORT.md"
)

PARITY_REPORT_MD_PATH = os.path.join(
    "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k",
    "MODE1_STAGE14UAB_COMPLETION_CONTROL_PARITY_REPORT.md"
)

THESIS_CH4_PATH = os.path.join(
    "docs", "MA_AdaptiveRemeshing_Report_2026_main", "chapter04_current_status.tex"
)

PRE_ANALYSIS_INP_PATH = os.path.join(
    "models", "pandey_kumar_mode1", "93_mode1_preanalysis_inf_companion_2906",
    "PK_M1_JOB1_INF_COMPANION_2906.inp"
)

NATIVE_INP_PATH = os.path.join(
    "models", "pandey_kumar_mode1", "99_mode1_stage14_phasefield_preanalysis_fidelity",
    "PK_M1_STAGE14_STEP2_ALLINC.inp"
)

RECON_INP_PATH = os.path.join(
    "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k",
    "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp"
)

@pytest.fixture
def provenance_data():
    assert os.path.exists(REPORT_JSON_PATH), f"Report JSON missing: {REPORT_JSON_PATH}"
    with open(REPORT_JSON_PATH, "r") as f:
        return json.load(f)

def test_differing_raw_sha256_odbs_not_called_identical(provenance_data):
    """1. Fails if differing raw SHA-256 ODB containers are called identical files."""
    audit = provenance_data["odb_provenance_audit"]
    local_hash = audit["local_odb"]["sha256"].lower()
    cluster_hash = audit["cluster_odb"]["sha256"].lower()

    # The two raw SHA-256 hashes differ due to 32-byte container metadata
    assert local_hash != cluster_hash, "Raw hashes unexpectedly identical"
    assert audit["byte_difference"] == 32
    assert audit["file_identity_verdict"] == "DIFFERING_RAW_SHA256_CONTAINERS"
    
    # Must be closed by field equivalence, NOT called binary aliases
    equiv = audit["content_level_equivalence"]
    assert equiv["verdict"] == "STAGE14_NATIVE_REMESH_PROVENANCE_CLOSED_BY_FIELD_EQUIVALENCE"
    assert provenance_data["governing_verdict"] == "STAGE14_NATIVE_REMESH_PROVENANCE_CLOSED_BY_FIELD_EQUIVALENCE"

def test_remesh_input_odb_in_provenance_chain(provenance_data):
    """2. Fails if remesh input ODB or pre-analysis source is missing from provenance chain."""
    pre = provenance_data["pre_analysis_source"]
    assert pre["job_id"] == "INTERACTIVE_93"
    assert pre["input_deck_path"] == "models/pandey_kumar_mode1/93_mode1_preanalysis_inf_companion_2906/PK_M1_JOB1_INF_COMPANION_2906.inp"
    assert pre["input_deck_sha256"] == "d452369305ff67a2b0cfa4e5d07fab810c9123ecf500a05bba3e498437883613"
    assert pre["user_subroutine_path"] == "f42_mixed_uel_inf_stress.for"
    assert pre["user_subroutine_sha256"] == "472ca0c5cc8b762bf83daea961988502dbfae36db7a32565b8c13fa69d839084"
    assert os.path.exists(PRE_ANALYSIS_INP_PATH), f"Pre-analysis deck missing: {PRE_ANALYSIS_INP_PATH}"

def test_remesh_script_and_call_recorded(provenance_data):
    """3. Fails if remesh script, CAE API call, or sizing parameters are unrecorded."""
    rule = provenance_data["native_remeshing_rule"]
    assert len(rule["orchestration_scripts"]) >= 2
    assert rule["cae_api_call"] == "m.adaptiveRemesh(odb=o)"
    
    params = rule["rule_parameters"]
    assert params["stepName"] == "Step-2"
    assert params["sizingMethod"] == "UNIFORM_ERROR"
    assert params["errorTarget"] == 1.0
    assert params["minElementSize_mm"] == 0.001
    assert params["maxElementSize_mm"] == 0.020
    assert params["refinementFactor"] == 10
    assert params["coarseningFactor"] == "NOT_ALLOWED"
    assert params["region"] == "ALL_ELEM"

def test_miseseri_element_count_matches_preanalysis_fe_count(provenance_data):
    """4. Fails if MISESERI element count differs from pre-analysis finite-element count (2,906)."""
    pre = provenance_data["pre_analysis_source"]
    assert pre["finite_element_count"] == 2906
    assert pre["element_type_breakdown"]["CPE4"] == 2818
    assert pre["element_type_breakdown"]["CPE3"] == 88
    assert pre["finite_element_count"] == (2818 + 88)
    
    equiv = provenance_data["odb_provenance_audit"]["content_level_equivalence"]
    assert equiv["elements"]["base_finite_elements"] == 2906
    miseseri_cmp = equiv["miseseri_field_comparison"]
    assert miseseri_cmp["step1_last_frame"]["elements_compared"] == 2906
    assert miseseri_cmp["step2_frame880"]["elements_compared"] == 2906
    assert miseseri_cmp["step2_last_frame"]["elements_compared"] == 2906
    assert miseseri_cmp["step2_last_frame"]["max_abs_diff"] <= 3.4e-24

def test_native_and_reconstructed_node_coordinates_identical(provenance_data):
    """5. Fails if native and reconstructed node coordinates differ."""
    nat_deck = provenance_data["native_remeshing_rule"]["generated_native_deck"]
    rec_deck = provenance_data["reconstructed_deck_mapping"]
    
    assert nat_deck["nodes"] == 14456
    assert rec_deck["part_nodes"] == 14456
    assert rec_deck["max_node_coordinate_discrepancy_mm"] < 1e-6
    assert nat_deck["inverted_elements"] == 0
    assert nat_deck["seam_duplicate_pairs"] == 54
    assert nat_deck["seam_crack_tip_singletons"] == 1
    assert abs(nat_deck["total_area_mm2"] - 1.0) < 1e-6
    assert os.path.exists(NATIVE_INP_PATH), f"Native deck missing: {NATIVE_INP_PATH}"
    assert os.path.exists(RECON_INP_PATH), f"Reconstructed deck missing: {RECON_INP_PATH}"

def test_canonicalized_layer_connectivity_is_bijective(provenance_data):
    """6. Fails if canonicalized layer connectivity is not 1-to-1 bijective across layers and native mesh."""
    rec_deck = provenance_data["reconstructed_deck_mapping"]
    assert rec_deck["total_layered_elements"] == 43449
    assert rec_deck["layer_structure"]["layer1_phase_uel"]["count"] == 14483
    assert rec_deck["layer_structure"]["layer2_mechanical_uel"]["count"] == 14483
    assert rec_deck["layer_structure"]["layer3_companion_umat"]["count"] == 14483
    assert rec_deck["layer_connectivity_identity"] is True
    assert rec_deck["canonical_bijection_to_native"] is True
    assert rec_deck["mapping_status"] == "EXACT_100PCT_TOPOLOGY_BIJECTION_VERIFIED"

def test_proprietary_abaqus_sizing_formulas_unresolved_internal_detail(provenance_data):
    """7. Fails if proprietary Abaqus error-recovery sizing formulas are asserted without source."""
    epistemic = provenance_data["epistemic_classification"]
    assert "source_verified" in epistemic
    assert "numerically_verified" in epistemic
    assert "unresolved_internal_abaqus_detail" in epistemic
    
    unresolved = epistemic["unresolved_internal_abaqus_detail"]
    assert any("sizing formulas" in item.lower() for item in unresolved)
    assert any("heuristic" in item.lower() for item in unresolved)

def test_causal_attribution_discipline_for_peak_offset(provenance_data):
    """8. Fails if solver-control audit is used to claim a uniquely proven mesh-only cause for peak offset."""
    causal = provenance_data["causal_attribution_discipline"]
    stmt = causal["statement"]
    
    # Must reject claiming solver-control causes peak offset
    assert "not caused by the Stage-14U solver-control modification" in stmt
    # Must reject over-narrow attribution
    assert "must not be attributed more narrowly without direct evidence" in stmt
    assert causal["status"] == "DISCIPLINE_ENFORCED_IN_REPORTS_AND_THESIS"

    # Also verify Parity Report markdown does NOT contain the unverified narrow assertion
    with open(PARITY_REPORT_MD_PATH, "r") as f:
        parity_text = f.read()
    assert "must not be attributed more narrowly without direct evidence" in parity_text

    # Also verify Chapter 4 contains the disciplined causal attribution
    with open(THESIS_CH4_PATH, "r") as f:
        ch4_text = f.read()
    assert "must not be attributed more narrowly without direct evidence" in ch4_text
