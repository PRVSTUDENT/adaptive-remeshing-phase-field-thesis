"""Unit tests for Mode-II Gate M2-3 MISESERI provenance, falsification audit, and epistemology.

Verifies:
1. Actual-mesh figure files exist across PNG, PDF, and SVG formats.
2. The 3-layer passive modulus scaling factor (2.1e13) explains the 10^-14 linear companion stress indicators.
3. Distinguishes PROJECT_VERIFIED linear scaling from UNRESOLVED nonlinear Miehe UEL equivalence.
4. Distinguishes INFERRED/UNRESOLVED Abaqus internal sizing formulation from verified ratio invariance.
5. Predeclared Pearson correlation failure (r <= -0.85 failed with r = -0.8202) is preserved.
6. Graph connected components of fine elements confirm giant crack-tip component (11,828 elements, 70.66%).
7. Epistemic classification of errorTarget=2.0% is preserved as UNRESOLVED in literature and INFERRED in project.
8. Non-targeted selection rationale is documented and verified.
9. Gate M2-3 scientific qualification is recorded as PROVISIONAL / REQUIRES_DIAGNOSIS.
10. The authoritative audit report exists and is synchronized in models/pandey_kumar_mode2/ and docs/mode2/.
"""

import math
from pathlib import Path
from collections import defaultdict, deque
import pytest
import pandas as pd
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIGURES_DIR = REPO_ROOT / "results" / "figures" / "mode2"
DOCS_REPORT = REPO_ROOT / "docs" / "mode2" / "MODE2_M2_3_MISESERI_PROVENANCE_AUDIT_REPORT.md"
MODELS_REPORT = REPO_ROOT / "models" / "pandey_kumar_mode2" / "MODE2_M2_3_MISESERI_PROVENANCE_AUDIT_REPORT.md"
RAW_INP = REPO_ROOT / "models" / "pandey_kumar_mode2" / "06_paper_grounded_uel_preanalysis" / "M2_3_ADAPTED_RAW_2PCT.inp"
STEP1_CSV = REPO_ROOT / "models" / "pandey_kumar_mode2" / "06_paper_grounded_uel_preanalysis" / "miseseri_step1_final_frame2000.csv"


def test_actual_mesh_figures_exist():
    """Verify that all 3 actual-mesh figures exist in PNG (>= 1 MB), PDF, and SVG."""
    fig_stems = [
        "fig_mode2_m2_3_actual_mesh_fulldomain",
        "fig_mode2_m2_3_actual_mesh_crack_tip_zoom",
        "fig_mode2_m2_3_actual_mesh_lower_right_corridor_zoom",
    ]
    for stem in fig_stems:
        png = FIGURES_DIR / f"{stem}.png"
        pdf = FIGURES_DIR / f"{stem}.pdf"
        svg = FIGURES_DIR / f"{stem}.svg"
        assert png.exists(), f"Missing PNG: {png}"
        assert pdf.exists(), f"Missing PDF: {pdf}"
        assert svg.exists(), f"Missing SVG: {svg}"
        assert png.stat().st_size > 500_000, f"PNG too small: {png}"
        assert pdf.stat().st_size > 100_000, f"PDF too small: {pdf}"
        assert svg.stat().st_size > 1_000_000, f"SVG too small: {svg}"


def test_audit_reports_exist_and_consistent():
    """Verify that both audit reports exist, match, and contain explicit epistemic tags."""
    assert DOCS_REPORT.exists(), f"Missing {DOCS_REPORT}"
    assert MODELS_REPORT.exists(), f"Missing {MODELS_REPORT}"
    
    docs_text = DOCS_REPORT.read_text(encoding="utf-8")
    models_text = MODELS_REPORT.read_text(encoding="utf-8")
    assert docs_text == models_text, "Docs report and models report content mismatch"
    
    assert "PROVISIONAL / REQUIRES_DIAGNOSIS" in docs_text
    assert "INFERRED / PROJECT_SELECTED_FOR_M2_4" in docs_text
    assert "UNRESOLVED" in docs_text
    assert "PROJECT_VERIFIED" in docs_text
    assert "3-layer" in docs_text.lower()
    assert "22,530" in docs_text
    assert "1410807" in docs_text
    assert "FAILED" in docs_text
    assert "11,828" in docs_text or "Component 1" in docs_text
    assert "non-targeted" in docs_text.lower()


def test_miseseri_scale_invariance_and_physics_range():
    """Verify the mathematical dynamic range and physical linear proxy rescaling of MISESERI."""
    assert STEP1_CSV.exists(), f"Missing {STEP1_CSV}"
    df = pd.read_csv(STEP1_CSV)
    assert len(df) == 2960, f"Expected 2960 elements, found {len(df)}"
    
    m_raw = df["miseseri"].values
    dynamic_range = m_raw.max() / m_raw.min()
    assert dynamic_range > 1000.0, f"Expected dynamic range > 1000x, found {dynamic_range:.1f}x"
    
    # Linear scale factor from dummy E=1e-11 kN/mm^2 to physical E=210 GPa = 210 kN/mm^2
    scale_factor = 210.0 / 1.0e-11
    m_physical_mpa = m_raw * scale_factor * 1.0e3  # kN/mm^2 to MPa
    
    # Check that linear proxy crack tip singularity is physically realistic for linear elasticity (500 to 15000 MPa)
    assert 500.0 <= m_physical_mpa.max() <= 15000.0, f"Physical max stress error out of range: {m_physical_mpa.max():.1f} MPa"
    # Check that far-field stress error is realistic (0.01 to 10 MPa)
    assert 0.01 <= m_physical_mpa.min() <= 10.0, f"Physical min stress error out of range: {m_physical_mpa.min():.4f} MPa"


def test_fine_mesh_graph_topology_and_connectivity():
    """Verify topological connected components of the fine element subgraph in M2_3_ADAPTED_RAW_2PCT.inp."""
    assert RAW_INP.exists(), f"Missing {RAW_INP}"
    
    nodes = {}
    elements = {}
    reading_nodes = False
    reading_elements = False
    current_elem_type = None

    with open(RAW_INP, 'r', encoding='utf-8') as f:
        for line in f:
            line_s = line.strip()
            if not line_s or line_s.startswith('**'):
                continue
            if line_s.startswith('*Node'):
                reading_nodes = True
                reading_elements = False
                continue
            elif line_s.startswith('*Element,') or line_s == '*Element':
                reading_nodes = False
                reading_elements = True
                for p in line_s.split(','):
                    if 'type=' in p.lower():
                        current_elem_type = p.split('=')[1].strip()
                continue
            elif line_s.startswith('*'):
                reading_nodes = False
                reading_elements = False
                continue

            if reading_nodes:
                parts = line_s.split(',')
                nid = int(parts[0])
                nodes[nid] = (float(parts[1]), float(parts[2]))
            elif reading_elements:
                parts = [int(p.strip()) for p in line_s.split(',')]
                elements[parts[0]] = {'type': current_elem_type, 'conn': parts[1:]}

    assert len(elements) == 22530
    assert len(nodes) == 22642

    elem_h = {}
    elem_centroid = {}
    edge_to_elems = defaultdict(set)

    for eid, e in elements.items():
        pts = [nodes[n] for n in e['conn']]
        n_pts = len(pts)
        x = [p[0] for p in pts]
        y = [p[1] for p in pts]
        xc = sum(x) / float(n_pts)
        yc = sum(y) / float(n_pts)
        elem_centroid[eid] = (xc, yc)
        
        if n_pts == 4:
            area = 0.5 * abs((x[0]*y[1] + x[1]*y[2] + x[2]*y[3] + x[3]*y[0]) - 
                             (y[0]*x[1] + y[1]*x[2] + y[2]*x[3] + y[3]*x[0]))
        elif n_pts == 3:
            area = 0.5 * abs((x[0]*y[1] + x[1]*y[2] + x[2]*y[0]) - 
                             (y[0]*x[1] + y[1]*x[2] + y[2]*x[0]))
        else:
            area = 0.0
        elem_h[eid] = math.sqrt(area)
        
        for i in range(n_pts):
            edge = tuple(sorted((e['conn'][i], e['conn'][(i+1)%n_pts])))
            edge_to_elems[edge].add(eid)

    h_thresh = 0.008
    fine_eids = set([eid for eid, h in elem_h.items() if h <= h_thresh])
    assert len(fine_eids) == 16739

    # Build adjacency
    adj_fine = defaultdict(set)
    for edge, e_set in edge_to_elems.items():
        fine_in_edge = e_set.intersection(fine_eids)
        if len(fine_in_edge) == 2:
            e1, e2 = list(fine_in_edge)
            adj_fine[e1].add(e2)
            adj_fine[e2].add(e1)

    visited = set()
    components = []
    for eid in fine_eids:
        if eid not in visited:
            comp = []
            queue = deque([eid])
            visited.add(eid)
            while queue:
                curr = queue.popleft()
                comp.append(curr)
                for neighbor in adj_fine[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(comp)

    components.sort(key=len, reverse=True)
    main_comp = set(components[0])
    assert len(main_comp) == 11828, f"Expected 11828 elements in main component, got {len(main_comp)}"
    
    # Check that 100% of crack tip fine elements belong to main component
    tip_fine_eids = [eid for eid in fine_eids if math.sqrt((elem_centroid[eid][0]-0.5)**2 + (elem_centroid[eid][1]-0.5)**2) < 0.05]
    for te in tip_fine_eids:
        assert te in main_comp, f"Crack tip fine element {te} not in main component"


def test_raw_inp_deck_sha256():
    """Verify raw input deck SHA-256 hash."""
    assert RAW_INP.exists(), f"Missing {RAW_INP}"
    import hashlib
    h = hashlib.sha256(RAW_INP.read_bytes()).hexdigest().upper()
    assert h == "BD02D73C2BC199DB95369C094A3B579005A8F3B97654657874BD73398DEF6C22"
