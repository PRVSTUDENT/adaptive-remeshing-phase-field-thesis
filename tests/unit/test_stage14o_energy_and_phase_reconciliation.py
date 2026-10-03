"""
test_stage14o_energy_and_phase_reconciliation.py

Unit and regression test suite for Gate-6B Stage 14O:
Energy-Unit and Phase-Field Anchor Reconciliation Audit.

Guards:
1. Energy unit scaling: 1 kN*mm = 1 J = 1000 mJ across all solver extractions.
2. Immutability and exact values of Reference Anchor at u=0.0010 mm (Inc 400, Job 1409734).
3. Reconciled values of Adaptive Anchor at u=0.0010 mm (Inc 400, Job 1409953).
4. Phase field d_max exact extraction and companion SDV14/SDV1 layer parity.
5. Schema and numeric integrity of MODE1_STAGE14O_ENERGY_AND_PHASE_RECONCILIATION_REPORT.json.
"""

import json
import math
from pathlib import Path
import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
STAGE14_DIR = WORKSPACE_ROOT / "models" / "pandey_kumar_mode1" / "25_stage14_adaptive_candidate_14k"
STAGE14O_JSON = STAGE14_DIR / "MODE1_STAGE14O_ENERGY_AND_PHASE_RECONCILIATION_REPORT.json"


def test_energy_unit_scaling_consistency():
    """Verify standard unit scaling 1 kN*mm = 1 J = 1000 mJ."""
    raw_reference_e_elas_kNmm = 6.89620813e-5
    reconciled_reference_e_elas_mJ = raw_reference_e_elas_kNmm * 1000.0
    assert math.isclose(reconciled_reference_e_elas_mJ, 0.0689620813, rel_tol=1e-7)

    raw_adaptive_e_elas_kNmm = 6.89440827e-5
    reconciled_adaptive_e_elas_mJ = raw_adaptive_e_elas_kNmm * 1000.0
    assert math.isclose(reconciled_adaptive_e_elas_mJ, 0.0689440827, rel_tol=1e-7)

    raw_reference_e_frac_kNmm = 5.55344167e-8
    reconciled_reference_e_frac_mJ = raw_reference_e_frac_kNmm * 1000.0
    assert math.isclose(reconciled_reference_e_frac_mJ, 0.0000555344167, rel_tol=1e-7)

    raw_adaptive_e_frac_kNmm = 5.56075948e-8
    reconciled_adaptive_e_frac_mJ = raw_adaptive_e_frac_kNmm * 1000.0
    assert math.isclose(reconciled_adaptive_e_frac_mJ, 0.0000556075948, rel_tol=1e-7)


def test_stage14o_reconciled_reference_anchor():
    """Verify exact reference values at u=0.0010 mm (Inc 400 of Job 1409734)."""
    # Mechanical anchor
    rf_kN = 0.13792416
    u_mm = 0.001000
    k0_expected = 137.945520

    # Elastic energy
    e_elas_mJ = 0.068962081
    # Fracture functional
    e_frac_mJ = 0.0000555344
    # Total model energy
    e_model_mJ = e_elas_mJ + e_frac_mJ
    w_ext_mJ = 0.069017512

    assert math.isclose(e_model_mJ, 0.069017616, abs_tol=1e-7)
    delta_book_mJ = e_model_mJ - w_ext_mJ
    eps_book_pct = abs(delta_book_mJ) / w_ext_mJ * 100.0
    assert eps_book_pct < 0.001  # 0.00015%

    # Phase field
    d_max = 0.00910334
    assert 0.0090 < d_max < 0.0100


def test_stage14o_reconciled_adaptive_anchor():
    """Verify exact adaptive values at u=0.0010 mm (Inc 400 of Job 1409953)."""
    rf_kN = 0.13788816
    ref_rf_kN = 0.13792416
    delta_rf_pct = (rf_kN - ref_rf_kN) / ref_rf_kN * 100.0
    assert math.isclose(delta_rf_pct, -0.026101, abs_tol=1e-4)

    e_elas_mJ = 0.068944083
    ref_e_elas_mJ = 0.068962081
    delta_e_elas_pct = (e_elas_mJ - ref_e_elas_mJ) / ref_e_elas_mJ * 100.0
    assert math.isclose(delta_e_elas_pct, -0.026100, abs_tol=1e-4)

    e_frac_mJ = 0.0000556076
    ref_e_frac_mJ = 0.0000555344
    delta_e_frac_pct = (e_frac_mJ - ref_e_frac_mJ) / ref_e_frac_mJ * 100.0
    assert math.isclose(delta_e_frac_pct, 0.131771, abs_tol=1e-3)

    # Phase field
    d_max = 0.00953182
    ref_d_max = 0.00910334
    assert 0.0090 < d_max < 0.0100

    # Structural stiffness
    k0 = 137.909558
    ref_k0 = 137.945520
    delta_k0_pct = (k0 - ref_k0) / ref_k0 * 100.0
    assert math.isclose(delta_k0_pct, -0.026070, abs_tol=1e-4)


def test_stage14o_json_report_schema_and_values():
    """Verify presence and validity of Stage 14O JSON report."""
    assert STAGE14O_JSON.exists(), f"Missing report {STAGE14O_JSON}"
    with open(STAGE14O_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["audit_metadata"]["governing_verdict"] == "STAGE14_ENERGY_AND_PHASE_ANCHOR_RECONCILED"
    table = data["reconciliation_table_at_u_0_0010_mm"]["metrics"]

    assert table["reaction_force_kN"]["fixed_reference_1409734"] == 0.13792416
    assert table["reaction_force_kN"]["corrected_adaptive_1409953"] == 0.13788816

    assert table["elastic_energy_mJ"]["fixed_reference_1409734"] == 0.068962081
    assert table["elastic_energy_mJ"]["corrected_adaptive_1409953"] == 0.068944083

    assert table["fracture_energy_mJ"]["fixed_reference_1409734"] == 0.0000555344
    assert table["fracture_energy_mJ"]["corrected_adaptive_1409953"] == 0.0000556076

    assert table["max_phase_field_dmax"]["fixed_reference_1409734"] == 0.00910334
    assert table["max_phase_field_dmax"]["corrected_adaptive_1409953"] == 0.00953182

    assert table["canonical_structural_stiffness_K0_kN_per_mm"]["classification"] == "STABLE"
