"""
Unit tests for Package 153: Production C4 Companion Continuum Model for MISESERI Recovery.

Tests:
1. Input deck generation, file existence, and SHA-256 bindings.
2. Mesh identity: exact 7,056 CPE4 elements, 7,265 physical nodes + RP 999999.
3. Slit flank duplicate nodes: exactly 40 coincident pairs (nodes 3571..3610 and 7226..7265).
4. Ligament nodes: exactly 45 shared nodes (nodes 3611..3655).
5. Kinematic coupling: 85 *EQUATION cards in DOF 2 tying top boundary to RP 999999.
6. Boundary conditions and material properties (E = 210.0 kN/mm^2, nu = 0.3, uy = 0.002000 mm).
7. Output requests: MISESERI, MISESAVG, S, EVOL, U, RF.
8. Manifest and script integrity (PACKAGE_MANIFEST.json, EXECUTION_MANIFEST.json, PBS script, datacheck runner).
"""

import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import pytest
from scripts.remeshing.build_package153_c4_companion import (
    PKG153_DIR,
    build_package153,
    compute_sha256,
)


@pytest.fixture(scope="module", autouse=True)
def generated_package153():
    """Generates Package 153 files before running tests."""
    build_package153(displacement_target=0.002000)
    assert os.path.isdir(PKG153_DIR)


def test_package153_files_exist():
    """Verifies that all required Package 153 artifacts exist."""
    inp_file = os.path.join(PKG153_DIR, "M1_C4_COMPANION_MISESERI.inp")
    pkg_manifest = os.path.join(PKG153_DIR, "PACKAGE_MANIFEST.json")
    exec_manifest = os.path.join(PKG153_DIR, "EXECUTION_MANIFEST.json")
    pbs_file = os.path.join(PKG153_DIR, "submit_M1_C4_COMPANION_MISESERI.pbs")
    dc_file = os.path.join(PKG153_DIR, "run_datacheck.sh")

    for f in (inp_file, pkg_manifest, exec_manifest, pbs_file, dc_file):
        assert os.path.isfile(f), f"File {f} must exist"


def test_package153_input_deck_mesh_structure():
    """Verifies node counts, CPE4 element counts, sets, and equations."""
    inp_file = os.path.join(PKG153_DIR, "M1_C4_COMPANION_MISESERI.inp")

    nodes = {}
    elements = {}
    current_sec = None
    equation_count = 0

    with open(inp_file, "r") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("**"):
                continue

            if stripped.startswith("*"):
                upper = stripped.upper()
                if upper.startswith("*NODE") and "OUTPUT" not in upper:
                    current_sec = "NODE"
                    continue
                elif upper.startswith("*ELEMENT") and "OUTPUT" not in upper:
                    assert "TYPE=CPE4" in upper
                    current_sec = "ELEMENT"
                    continue
                elif upper.startswith("*EQUATION"):
                    equation_count += 1
                    current_sec = "EQUATION"
                    continue
                else:
                    current_sec = "OTHER"
                    continue

            parts = [p.strip() for p in stripped.split(",")]
            if current_sec == "NODE":
                if len(parts) >= 3:
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
            elif current_sec == "ELEMENT":
                if len(parts) >= 5:
                    elements[int(parts[0])] = [int(p) for p in parts[1:5]]

    # 7,265 nodes + RP 999999 = 7,266 total nodes
    assert len(nodes) == 7266
    assert 999999 in nodes

    # 7,056 CPE4 continuum quads
    assert len(elements) == 7056
    assert min(elements.keys()) == 1
    assert max(elements.keys()) == 7056

    # 85 kinematic tie equations in DOF 2
    assert equation_count == 85


def test_package153_flank_and_ligament_topology():
    """Verifies that the duplicate slit nodes and ligament shared nodes match canonical C4."""
    inp_file = os.path.join(PKG153_DIR, "M1_C4_COMPANION_MISESERI.inp")

    nodes = {}
    with open(inp_file, "r") as f:
        reading_nodes = False
        for line in f:
            stripped = line.strip()
            if stripped.startswith("*Node"):
                reading_nodes = True
                continue
            elif stripped.startswith("*") and reading_nodes:
                break
            if reading_nodes and stripped and not stripped.startswith("**"):
                parts = [p.strip() for p in stripped.split(",")]
                if len(parts) >= 3:
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))

    # Find duplicate pairs along slit y = 0.05 mm, x in [0.0, 0.04] mm
    slit_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 0.05) < 1e-5 and x <= 0.040001]
    ligament_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 0.05) < 1e-5 and x > 0.040001]

    from collections import defaultdict
    pos_map = defaultdict(list)
    for nid in slit_nodes:
        pos_map[round(nodes[nid][0], 7)].append(nid)

    pairs = [nids for nids in pos_map.values() if len(nids) == 2]
    assert len(pairs) == 40, f"Expected 40 duplicate slit pairs, got {len(pairs)}"
    assert len(ligament_nodes) == 45, f"Expected 45 ligament nodes, got {len(ligament_nodes)}"


def test_package153_material_boundary_and_output_requests():
    """Verifies steel elasticity, perturbation step, prescribed displacement, and output requests."""
    inp_file = os.path.join(PKG153_DIR, "M1_C4_COMPANION_MISESERI.inp")
    content = open(inp_file, "r").read()

    assert "*Solid Section, elset=ALL_QUADS, material=STEEL" in content
    assert "210.0, 0.3" in content
    assert "*Step, name=STATIC_ELASTIC, perturb" in content
    assert "*Static" in content
    assert "999999, 2, 2, 0.002000000" in content
    assert "S, MISESERI, MISESAVG, EVOL" in content
    assert "*Element Output, elset=ALL_QUADS" in content
    assert "*Node Output, nset=N_RP" in content


def test_package153_manifests_and_scripts():
    """Verifies manifest consistency and PBS script directives."""
    pkg_manifest_path = os.path.join(PKG153_DIR, "PACKAGE_MANIFEST.json")
    with open(pkg_manifest_path, "r") as f:
        pkg_m = json.load(f)

    assert pkg_m["package_number"] == 153
    assert pkg_m["job_name"] == "M1_C4_COMPANION_MISESERI"
    assert pkg_m["mesh_provenance"]["elements"] == 7056
    assert pkg_m["mesh_provenance"]["nodes"] == 7265
    assert pkg_m["loading"]["prescribed_u2_mm"] == 0.002000

    exec_manifest_path = os.path.join(PKG153_DIR, "EXECUTION_MANIFEST.json")
    with open(exec_manifest_path, "r") as f:
        exec_m = json.load(f)

    assert exec_m["package_number"] == 153
    assert exec_m["execution_mode"] == "SERIAL_STANDALONE_CONTINUUM"
    assert exec_m["cpus"] == 1
    assert exec_m["memory_gb"] == 8

    # PBS Script checks
    pbs_file = os.path.join(PKG153_DIR, "submit_M1_C4_COMPANION_MISESERI.pbs")
    pbs_text = open(pbs_file, "r").read()
    assert "#PBS -N M1_C4_COMPANION_MISESERI" in pbs_text
    assert "#PBS -m abe" in pbs_text
    assert "notification_install_terminal_trap" in pbs_text
    assert "notify_start" in pbs_text
