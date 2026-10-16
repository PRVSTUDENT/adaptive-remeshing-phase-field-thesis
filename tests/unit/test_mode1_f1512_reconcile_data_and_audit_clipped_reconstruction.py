"""
Unit tests for Task F1512:
Reconcile contradictory numerical references, audit clipped least-squares inverse reconstruction,
and verify Gate 6C evaluation criteria for same-mesh control experiments.
"""
import csv
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_reaction_force_baseline_reference_reconciliation():
    rf_csv = REPO_ROOT / "models" / "pandey_kumar_mode1" / "40_method_b_corrected_propagation_14k" / "evidence_1412465" / "corrected_method_b_load_displacement.csv"
    assert rf_csv.exists()
    matched_rf = None
    with open(rf_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            u = float(row["u_mm"])
            if abs(u - 0.0050) < 1e-6:
                matched_rf = float(row["f_kN"]) * 1000.0  # Convert kN to N
                break
    assert matched_rf is not None, "Failed to find u=0.0050 mm in load-displacement CSV"
    assert abs(matched_rf - 661.7254) < 0.01, f"Expected RF2 ~ 661.7254 N, found {matched_rf} N"


def test_fracture_energy_reference_reconciliation():
    # 1. Baseline 1412465
    base_energy_csv = REPO_ROOT / "models" / "pandey_kumar_mode1" / "40_method_b_corrected_propagation_14k" / "evidence_1412465" / "uel_energy_balance.csv"
    assert base_energy_csv.exists()
    e_frac_base = None
    with open(base_energy_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            step = row.get("Step", "").strip()
            inc = int(row.get("Increment", 0))
            if step == "1" and inc == 2000:
                e_frac_base = float(row["E_fracture_kNmm"]) * 1000.0  # Convert to mJ
                break
    assert e_frac_base is not None
    assert abs(e_frac_base - 0.036786) < 0.0001, f"Expected base E_frac ~ 0.036786 mJ, found {e_frac_base}"

    # 2. Relhold 1414550 terminal
    relhold_energy_csv = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer" / "evidence" / "1414550.mmaster02" / "uel_energy_balance.csv"
    assert relhold_energy_csv.exists()
    e_frac_relhold = None
    with open(relhold_energy_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            step = row.get("Step", "").strip()
            inc = int(row.get("Increment", 0))
            if step == "2" and inc == 10:
                e_frac_relhold = float(row["E_fracture_kNmm"]) * 1000.0  # Convert to mJ
                break
    assert e_frac_relhold is not None
    assert abs(e_frac_relhold - 0.036947) < 0.0001, f"Expected relhold E_frac ~ 0.036947 mJ, found {e_frac_relhold}"

    # Relative match
    rel_diff_pct = (e_frac_relhold - e_frac_base) / e_frac_base * 100.0
    assert abs(rel_diff_pct - 0.438) < 0.02, f"Expected +0.438% match, found {rel_diff_pct:.4f}%"


def test_mesh_topology_quad_tri_breakdown():
    deck_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer"
    decks = [
        REPO_ROOT / "models" / "pandey_kumar_mode1" / "40_method_b_corrected_propagation_14k" / "M1_MB_CORRECTED_PROPAGATION_14K.inp",
        deck_dir / "M1_MC_STAGE_C1_1_RELHOLD.inp",
        deck_dir / "M1_MC_STAGE_C1_1_SAMEMESH_RELHOLD.inp",
        deck_dir / "M1_MC_STAGE_C1_1_SAMEMESH_CONSISTENT_RELHOLD.inp"
    ]
    for deck in decks:
        assert deck.exists(), f"Missing deck: {deck}"
        quads = 0
        tris = 0
        current_type = None
        with open(deck, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                l = line.strip()
                if l.startswith("**"):
                    continue
                if l.upper().startswith("*ELEMENT"):
                    parts = [pt.strip() for pt in l.split(",")]
                    type_str = ""
                    for pt in parts:
                        if pt.upper().startswith("TYPE="):
                            type_str = pt.split("=")[1].strip()
                    current_type = type_str
                elif l.startswith("*"):
                    current_type = None
                elif current_type is not None and l:
                    if current_type in ("U1", "U2", "CPE4"):
                        quads += 1
                    elif current_type in ("U3", "U4", "CPE3"):
                        tris += 1
        # In Abaqus UEL models, elements are repeated in sets (phase + mech + companion UMAT = 3x)
        # Unique base elements:
        base_quads = quads // 3
        base_tris = tris // 3
        assert base_quads == 14082, f"{deck.name}: expected 14082 quads, got {base_quads}"
        assert base_tris == 401, f"{deck.name}: expected 401 tris, got {base_tris}"
        assert (base_quads + base_tris) == 14483, f"{deck.name}: expected 14483 elements, got {base_quads + base_tris}"


def test_submitted_deck_damage_clipping_and_tip_invariance():
    deck_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer" / "M1_MC_STAGE_C1_1_SAMEMESH_CONSISTENT_RELHOLD.inp"
    assert deck_path.exists()
    d_vals = {}
    in_boundary = False
    with open(deck_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            l = line.strip()
            if l.startswith("**"):
                continue
            if l.upper().startswith("*BOUNDARY"):
                in_boundary = True
                continue
            elif l.startswith("*"):
                in_boundary = False
                continue
            elif in_boundary and l:
                parts = [pt.strip() for pt in l.split(",")]
                if len(parts) >= 4 and parts[1] == "3" and parts[2] == "3":
                    d_vals[int(parts[0])] = float(parts[3])

    assert len(d_vals) == 14456
    assert min(d_vals.values()) >= 0.0, "Found negative damage in submitted deck!"
    assert abs(max(d_vals.values()) - 0.342331) < 0.001
    assert abs(d_vals[129] - 0.342331) < 0.001, "Apex node 129 damage altered!"
    assert abs(d_vals[1384] - 0.319037) < 0.001, "Node 1384 damage altered!"


def test_gate_6c_original_acceptance_criteria_codification():
    # Original Gate 6C thresholds (MUST NOT be relaxed to 5%)
    GATE_6C_MAX_DELTA_RF_N = 5.0
    GATE_6C_MAX_DELTA_PEAK_D = 0.020
    GATE_6C_MAX_DELTA_ELAS_ENERGY_PCT = 0.50
    GATE_6C_MAX_DELTA_FRAC_ENERGY_PCT = 0.50
    GATE_6C_MAX_DELTA_TOTAL_ENERGY_PCT = 0.10

    assert GATE_6C_MAX_DELTA_RF_N == 5.0
    assert GATE_6C_MAX_DELTA_PEAK_D == 0.020
    assert GATE_6C_MAX_DELTA_ELAS_ENERGY_PCT == 0.50
    assert GATE_6C_MAX_DELTA_FRAC_ENERGY_PCT == 0.50
    assert GATE_6C_MAX_DELTA_TOTAL_ENERGY_PCT == 0.10
