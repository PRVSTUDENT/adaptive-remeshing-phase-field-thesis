"""F1597: Generation and Verification of Candidate h=2.5 um Donor Mesh for Mode-I Phase-Field Fracture.

Constructs a uniform 40x40 quad mesh (h = 0.0025 mm = 2.5 um <= ell/3 = 0.0025 mm) on [0, 0.1]^2
with an exact sharp slit at y = 0.050 mm, a0 = 0.040 mm (17 split nodes).
Outputs an authoritative Abaqus .inp deck compatible with the frozen production UEL (f42_mixed_uel.for).
"""
import hashlib
import json
import math
from pathlib import Path
from typing import Dict, Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_UEL_PATH = REPO_ROOT / "models/pandey_kumar_mode1/reproduction_package_gate6b_energy/f42_mixed_uel.for"
EXPECTED_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def build_uniform_slit_mesh(
    domain_size: float = 0.100,
    h: float = 0.0025,
    slit_y: float = 0.050,
    slit_a0: float = 0.040,
) -> Dict[str, Any]:
    """Generate uniform quad mesh on [0, domain_size]^2 with split nodes along slit."""
    nx = int(round(domain_size / h))
    ny = int(round(domain_size / h))
    x_coords = np.linspace(0.0, domain_size, nx + 1)
    y_coords = np.linspace(0.0, domain_size, ny + 1)

    slit_y_idx = int(round(slit_y / h))
    slit_x_max_idx = int(round(slit_a0 / h))

    nodes = {}
    grid_nid = np.zeros((nx + 1, ny + 1), dtype=int)
    nid_counter = 1

    # 1. Base grid nodes
    for j in range(ny + 1):
        for i in range(nx + 1):
            nodes[nid_counter] = [float(x_coords[i]), float(y_coords[j])]
            grid_nid[i, j] = nid_counter
            nid_counter += 1

    # 2. Duplicate slit nodes on the upper flank (j = slit_y_idx, i <= slit_x_max_idx)
    upper_slit_nid = {}
    for i in range(slit_x_max_idx + 1):
        upper_slit_nid[i] = nid_counter
        nodes[nid_counter] = [float(x_coords[i]), float(slit_y)]
        nid_counter += 1

    rp_nid = 999999
    nodes[rp_nid] = [float(domain_size / 2.0), float(domain_size)]

    # 3. Element connectivity (1..nx*ny)
    elements = {}
    eid_counter = 1
    for j in range(ny):
        for i in range(nx):
            if j == slit_y_idx and i <= slit_x_max_idx:
                n1 = upper_slit_nid[i]
                n2 = upper_slit_nid[i + 1] if (i + 1) <= slit_x_max_idx else grid_nid[i + 1, j]
            else:
                n1 = grid_nid[i, j]
                n2 = grid_nid[i + 1, j]
            n3 = grid_nid[i + 1, j + 1]
            n4 = grid_nid[i, j + 1]
            elements[eid_counter] = [int(n1), int(n2), int(n3), int(n4)]
            eid_counter += 1

    # 4. Check Jacobians
    min_det = 1e30
    max_aspect = 0.0
    for eid, conn in elements.items():
        xy = np.array([nodes[n] for n in conn])
        q = 1.0 / np.sqrt(3.0)
        for xi, eta in ((-q, -q), (q, -q), (q, q), (-q, q)):
            dn = 0.25 * np.array([
                [-(1 - eta), (1 - eta), (1 + eta), -(1 + eta)],
                [-(1 - xi), -(1 + xi), (1 + xi), (1 - xi)]
            ])
            jac = dn @ xy
            det = float(np.linalg.det(jac))
            if det <= 0:
                raise ValueError(f"Non-positive Jacobian in element {eid}: {det}")
            min_det = min(min_det, det)

        dx = max(xy[:, 0]) - min(xy[:, 0])
        dy = max(xy[:, 1]) - min(xy[:, 1])
        aspect = max(dx / dy, dy / dx) if dy > 0 and dx > 0 else 1.0
        max_aspect = max(max_aspect, aspect)

    top_nodes = sorted([n for n, p in nodes.items() if abs(p[1] - domain_size) < 1e-6 and n != rp_nid])
    bottom_nodes = sorted([n for n, p in nodes.items() if abs(p[1]) < 1e-6 and n != rp_nid])
    pin_nodes = [n for n in bottom_nodes if abs(nodes[n][0]) < 1e-6]

    return {
        "nodes": nodes,
        "elements": elements,
        "x_coords": x_coords,
        "y_coords": y_coords,
        "nx": nx,
        "ny": ny,
        "h": h,
        "n_elements": len(elements),
        "n_nodes": len(nodes) - 1,
        "rp_nid": rp_nid,
        "top_nodes": top_nodes,
        "bottom_nodes": bottom_nodes,
        "pin_nodes": pin_nodes,
        "min_det_jac": min_det,
        "max_aspect_ratio": max_aspect,
        "slit_y": slit_y,
        "slit_a0": slit_a0,
        "split_node_count": len(upper_slit_nid),
    }


def write_candidate_donor_deck(
    mesh: Dict[str, Any],
    out_path: Path,
    ell: float = 0.0075,
    gc: float = 0.0027,
    e_mod: float = 210.0,
    nu: float = 0.3,
    k_res: float = 1.0e-7,
    max_disp: float = 0.0050,
) -> None:
    """Write complete, compliant Abaqus input deck for candidate donor simulation."""
    nodes = mesh["nodes"]
    elements = mesh["elements"]
    n_elems = len(elements)
    top_nodes = mesh["top_nodes"]
    bottom_nodes = mesh["bottom_nodes"]
    pin_nodes = mesh["pin_nodes"]
    rp_nid = mesh["rp_nid"]

    lines = [
        "*Heading",
        f"** Candidate High-Resolution Mode-I Donor Model (1600 Quads, h=0.0025 mm <= l0/3 = 0.0025 mm)",
        f"** Geometry: 0.1 x 0.1 mm, sharp slit at y=0.05 mm, a0=0.04 mm",
        f"** Elements: {n_elems} Quads, Nodes: {len(nodes) - 1} physical + RP {rp_nid}",
        f"** Parameters: E={e_mod} kN/mm^2, nu={nu}, Gc={gc} kN/mm, l0={ell} mm, k={k_res}",
        "*Preprint, echo=NO, model=NO, history=NO, contact=NO",
        "** ==========================================================",
        f"** USER ELEMENTS (Phase U1: 1..{n_elems}, Mech U2: {n_elems+1}..{2*n_elems})",
        "** ==========================================================",
        "*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM",
        "3",
        "*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM",
        "1, 2",
        "** ==========================================================",
        f"** NODES ({len(nodes) - 1} physical nodes + RP {rp_nid})",
        "** ==========================================================",
        "*Node",
    ]

    for nid in sorted(nodes.keys()):
        x, y = nodes[nid]
        lines.append(f"{nid}, {x:.10f}, {y:.10f}")

    lines.append("** ==========================================================")
    lines.append(f"** LAYER 1: Phase-Field UEL Elements (U1: DOF 3, 1..{n_elems})")
    lines.append("** ==========================================================")
    lines.append("*Element, type=U1, elset=PHASE_QUADS")
    for eid in sorted(elements.keys()):
        conn = elements[eid]
        lines.append(f"{eid}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}")

    lines.append("** ==========================================================")
    lines.append(f"** LAYER 2: Mechanical UEL Elements (U2: DOFs 1,2, {n_elems+1}..{2*n_elems})")
    lines.append("** ==========================================================")
    lines.append("*Element, type=U2, elset=MECH_QUADS")
    for eid in sorted(elements.keys()):
        conn = elements[eid]
        lines.append(f"{eid + n_elems}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}")

    lines.append("** ==========================================================")
    lines.append(f"** LAYER 3: Visualization Overlay Elements (CPE4, {2*n_elems+1}..{3*n_elems})")
    lines.append("** ==========================================================")
    lines.append("*Element, type=CPE4, elset=umatelem")
    for eid in sorted(elements.keys()):
        conn = elements[eid]
        lines.append(f"{eid + 2*n_elems}, {conn[0]}, {conn[1]}, {conn[2]}, {conn[3]}")

    lines.append("** ==========================================================")
    lines.append("** SOLID SECTION FOR VISUALIZATION OVERLAY")
    lines.append("** ==========================================================")
    lines.append("*Solid Section, elset=umatelem, material=DUMMY_ELASTIC")
    lines.append("1.0,")
    lines.append("*Material, name=DUMMY_ELASTIC")
    lines.append("*Elastic")
    lines.append("1.0e-12, 0.3")

    lines.append("** ==========================================================")
    lines.append("** UEL PROPERTIES")
    lines.append("** ==========================================================")
    lines.append("*UEL PROPERTY, ELSET=PHASE_QUADS")
    lines.append(f"{ell}, {gc}, {e_mod}, {nu}, {k_res}, {n_elems}")
    lines.append("*UEL PROPERTY, ELSET=MECH_QUADS")
    lines.append(f"{ell}, {gc}, {e_mod}, {nu}, {k_res}, {n_elems}")

    lines.append("** ==========================================================")
    lines.append("** NODE SETS & BOUNDARY CONDITIONS")
    lines.append("** ==========================================================")
    lines.append("*Nset, nset=N_BOTTOM")
    for i in range(0, len(bottom_nodes), 16):
        lines.append(", ".join(str(n) for n in bottom_nodes[i:i + 16]))

    lines.append("*Nset, nset=N_PIN")
    lines.append(", ".join(str(n) for n in pin_nodes))

    lines.append("*Nset, nset=N_TOP")
    for i in range(0, len(top_nodes), 16):
        lines.append(", ".join(str(n) for n in top_nodes[i:i + 16]))

    lines.append("*Nset, nset=N_RP")
    lines.append(f"{rp_nid}")

    lines.append("*Boundary")
    lines.append("N_BOTTOM, 2, 2, 0.0")
    lines.append("N_PIN, 1, 1, 0.0")

    lines.append("** Rigid body tie top nodes to RP for Mode-I displacement")
    lines.append("*Equation")
    lines.append("2")
    lines.append(f"** Top node u_y coupled to RP u_y")
    for tn in top_nodes:
        lines.append("2")
        lines.append(f"{tn}, 2, 1.0, {rp_nid}, 2, -1.0")

    lines.append("** ==========================================================")
    lines.append("** STEP 1: Quasi-Static Monotonic Extension")
    lines.append("** ==========================================================")
    lines.append("*Step, name=Step-1, nlgeom=NO, inc=2000")
    lines.append("*Static")
    lines.append("1.0e-3, 1.0, 1.0e-8, 5.0e-3")

    lines.append("*Boundary")
    lines.append(f"N_RP, 2, 2, {max_disp}")
    lines.append("N_RP, 1, 1, 0.0")

    lines.append("** Output requests")
    lines.append("*Output, field, frequency=5")
    lines.append("*Node Output")
    lines.append("U, RF")
    lines.append("*Element Output, elset=umatelem")
    lines.append("S, E")
    lines.append("*Output, history, frequency=1")
    lines.append("*Node Output, nset=N_RP")
    lines.append("U2, RF2")
    lines.append("*Energy Output")
    lines.append("ALLSE, ALLWK, ALLFD, ALLIE")
    lines.append("*End Step")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def generate_candidate_donor_h0025():
    """Build candidate h=0.0025 mm donor mesh and write INP deck."""
    deck_path = REPO_ROOT / "models/pandey_kumar_mode1/candidate_donor_h0025.inp"
    mesh = build_uniform_slit_mesh(
        domain_size=0.100,
        h=0.0025,
        slit_y=0.050,
        slit_a0=0.040,
    )
    write_candidate_donor_deck(mesh, deck_path)
    deck_hash = sha256_file(deck_path)
    uel_hash = sha256_file(PRODUCTION_UEL_PATH)

    return {
        "deck_path": str(deck_path.relative_to(REPO_ROOT)),
        "deck_sha256": deck_hash,
        "uel_path": str(PRODUCTION_UEL_PATH.relative_to(REPO_ROOT)),
        "uel_sha256": uel_hash,
        "n_elements": mesh["n_elements"],
        "n_nodes": mesh["n_nodes"],
        "h_mm": mesh["h"],
        "min_det_jac": mesh["min_det_jac"],
        "max_aspect_ratio": mesh["max_aspect_ratio"],
        "split_nodes": mesh["split_node_count"],
    }
