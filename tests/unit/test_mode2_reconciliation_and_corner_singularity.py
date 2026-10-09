"""
Mode-II Scientific Data Reconciliation and Corner Singularity Unit Test Suite
Author: gemini-antigravity
Task: F1350

Validates:
1. Exact corridor selectivity metrics under both geometric definitions:
   - Narrow straight chord box (W = 0.12 mm): 7,309 / 15,771 = 46.34%
   - Curved envelope band (W = 0.24 mm): 12,432 / 15,771 = 78.83%
   - Spatial density contrast: 20.94x higher in corridor than far-field
2. Exact node and element count reconciliation:
   - Physical nodes: 21,042
   - User nodes with RP 999999: 21,043
   - Physical FEs: 21,063 (20,487 quads + 576 tris)
   - Layered solver elements: 63,189
3. Centerline coordinate reconciliation at y = 0.5 mm:
   - Notch tip anchor: x = 0.500 mm
   - Fine element centroid mean: x = 0.5394 mm
4. Bottom-right corner stress singularity and error concentration:
   - Elastic / pre-peak ratio (Corner / Crack Exit): 4.56x to 4.93x
   - Post-fracture ratio: ~1.88x
"""

import os
import json
import pytest
import numpy as np
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BASE_M2_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis")
REMESH_DIR = os.path.join(BASE_M2_DIR, "m2_corrected_remesh")
EXTRACTED_DIR = os.path.join(BASE_M2_DIR, "extracted_corrected_miseseri")

MANIFEST_PATH = os.path.join(REMESH_DIR, "MODE2_CORRECTED_REMESH_MANIFEST.json")
AUDIT_PATH = os.path.join(REMESH_DIR, "mode2_corridor_quantitative_audit.json")
RAW_DECK_PATH = os.path.join(REMESH_DIR, "M2_CORRECTED_ADAPTED_RAW_3PCT.inp")
STAB_DECK_PATH = os.path.join(REMESH_DIR, "M2_CORRECTED_JOB2_ET3PCT_STABILIZED.inp")


def test_corridor_selectivity_reconciliation():
    """Verify exact numerical consistency and definitions of both corridor metrics."""
    assert os.path.exists(MANIFEST_PATH), f"Missing {MANIFEST_PATH}"
    assert os.path.exists(AUDIT_PATH), f"Missing {AUDIT_PATH}"
    
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)
    with open(AUDIT_PATH, "r") as f:
        audit = json.load(f)
    
    m_et3 = manifest["sweep_results"]["ET_3PCT"]
    a_et3 = audit["mesh_selectivity"]["ET_3PCT"]
    
    # 1. Total elements & fine elements identical across both audits
    assert m_et3["total_elements"] == 21063
    assert a_et3["total_elements"] == 21063
    assert m_et3["fine_element_count"] == 15771
    assert a_et3["fine_count"] == 15771
    
    # 2. Narrow chord box definition (F1347): 46.34%
    narrow_fine = m_et3["corridor_fine_count"]
    assert narrow_fine == 7309
    narrow_pct = narrow_fine / m_et3["fine_element_count"] * 100.0
    assert abs(narrow_pct - 46.344556) < 1e-4
    assert abs(m_et3["corridor_fine_fraction_pct"] - 46.344556) < 1e-4
    
    # 3. Curved envelope band definition (F1348): 78.83%
    wide_fine = a_et3["fine_in_corridor_count"]
    assert wide_fine == 12432
    wide_pct = wide_fine / a_et3["fine_count"] * 100.0
    assert abs(wide_pct - 78.828229) < 1e-4
    assert abs(a_et3["fine_in_corridor_pct_of_fine"] - 78.828229) < 1e-4
    
    # 4. Density contrast ratio
    assert abs(a_et3["density_contrast_ratio"] - 20.93887) < 1e-3
    assert a_et3["fine_density_in_corridor_elems_per_mm2"] > 80000.0
    assert a_et3["fine_density_outside_corridor_elems_per_mm2"] < 4000.0


def test_mesh_node_and_element_counts():
    """Verify physical and user node counts in raw and stabilized input decks."""
    assert os.path.exists(RAW_DECK_PATH), f"Missing {RAW_DECK_PATH}"
    assert os.path.exists(STAB_DECK_PATH), f"Missing {STAB_DECK_PATH}"
    
    def parse_deck_counts(path):
        nodes = set()
        quads = set()
        tris = set()
        in_nodes = False
        in_elems = False
        elem_type = None
        with open(path, "r") as f:
            for line in f:
                l = line.strip()
                if not l or l.startswith("**"):
                    continue
                if l.startswith("*"):
                    in_nodes = l.upper().startswith("*NODE")
                    in_elems = l.upper().startswith("*ELEMENT")
                    if in_elems:
                        u = l.upper()
                        if "CPS3" in u or "CPE3" in u or "TRI" in u or "U3" in u or "U4" in u:
                            elem_type = "TRI"
                        else:
                            elem_type = "QUAD"
                    continue
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if in_nodes and len(parts) >= 3:
                    try:
                        nodes.add(int(parts[0]))
                    except ValueError:
                        pass
                if in_elems and len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        if elem_type == "TRI" or len(parts) == 4:
                            tris.add(eid)
                        else:
                            quads.add(eid)
                    except ValueError:
                        pass
        return nodes, quads, tris

    raw_nodes, raw_quads, raw_tris = parse_deck_counts(RAW_DECK_PATH)
    stab_nodes, stab_quads, stab_tris = parse_deck_counts(STAB_DECK_PATH)
    
    # Raw mesh: 21,042 physical nodes, 20,487 quads, 576 tris = 21,063 FEs
    assert len(raw_nodes) == 21042
    assert len(raw_quads) == 20487
    assert len(raw_tris) == 576
    assert len(raw_quads) + len(raw_tris) == 21063
    
    # Stabilized deck: 21,042 physical nodes + RP 999999 = 21,043 nodes
    assert len(stab_nodes) == 21043
    assert 999999 in stab_nodes
    assert (stab_nodes - {999999}) == raw_nodes
    
    # Layered elements: 3 layers * 21,063 = 63,189 elements
    total_stab_elems = len(stab_quads) + len(stab_tris)
    assert total_stab_elems == 63189


def test_centerline_coordinate_reconciliation():
    """Verify centerline station reconciliation at y = 0.5 mm."""
    with open(AUDIT_PATH, "r") as f:
        audit = json.load(f)
    
    c_et3 = audit["centerline_eval"]["ET_3PCT"]
    y_eval = c_et3["y_eval"]
    x_mesh = c_et3["x_mesh"]
    
    # At y = 0.5 mm, fine centroid is 0.5394 mm
    idx_top = y_eval.index(0.5)
    assert abs(x_mesh[idx_top] - 0.5394438) < 1e-4
    
    # At y = 0.0 mm (bottom exit), x_mesh is ~0.9849 mm
    idx_bot = y_eval.index(0.0)
    assert abs(x_mesh[idx_bot] - 0.984867) < 1e-4


def test_bottom_right_corner_singularity_error_ratio():
    """Verify that linear-elastic stress recovery error is concentrated at the bottom-right corner."""
    p_step1_init = os.path.join(EXTRACTED_DIR, "corrected_coarse_fields_ux_0p00500.csv")
    p_step2_peak = os.path.join(EXTRACTED_DIR, "corrected_coarse_fields_ux_0p01343_peak.csv")
    p_step2_final = os.path.join(EXTRACTED_DIR, "corrected_coarse_fields_ux_0p02000_final.csv")
    
    assert os.path.exists(p_step1_init)
    assert os.path.exists(p_step2_peak)
    assert os.path.exists(p_step2_final)
    
    def get_corner_ratio(path):
        df = pd.read_csv(path)
        corner = df[(df['xc'] >= 0.95) & (df['yc'] <= 0.05)]
        crack = df[(df['xc'] >= 0.78) & (df['xc'] <= 0.85) & (df['yc'] <= 0.05)]
        return corner['miseseri'].max() / crack['miseseri'].max()
    
    ratio_init = get_corner_ratio(p_step1_init)
    ratio_peak = get_corner_ratio(p_step2_peak)
    ratio_final = get_corner_ratio(p_step2_final)
    
    # Pre-peak ratios must be between 4.0 and 5.5
    assert 4.0 <= ratio_init <= 5.5
    assert 4.0 <= ratio_peak <= 5.5
    
    # Post-fracture ratio remains elevated (> 1.5)
    assert ratio_final > 1.5
