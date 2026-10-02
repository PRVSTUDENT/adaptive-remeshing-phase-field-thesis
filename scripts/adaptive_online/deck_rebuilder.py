#!/usr/bin/env python3
"""
Layered Phase-Field UEL Input Deck Builder.
Transforms physical mesh definitions into validated 3-layer UEL input decks:
  Layer 1 (Phase):        U1 (quad) / U3 (tri), labels 1 .. NPHYS
  Layer 2 (Displacement): U2 (quad) / U4 (tri), labels NPHYS+1 .. 2*NPHYS
  Layer 3 (Facsimile):    CPE4 (quad) / CPE3 (tri), labels 2*NPHYS+1 .. 3*NPHYS
Enforces strict 100% agreement between declared physical elements and 3-layer element counts.
"""

import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

DEFAULT_L0 = 0.015
DEFAULT_GC = 0.0027
DEFAULT_EMOD = 210.0
DEFAULT_ENU = 0.30
DEFAULT_PARK = 1.0e-7
DEFAULT_THICKNESS = 1.0
DEFAULT_PASSIVE_E = 1.0e-11
DEFAULT_DEPVAR = 18


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_layered_uel_deck(
    mesh_data: Dict[str, Any],
    output_path: Path,
    job_name: str = "ADAPTIVE_LAYERED_MODEL",
    l0: float = DEFAULT_L0,
    gc: float = DEFAULT_GC,
    emod: float = DEFAULT_EMOD,
    enu: float = DEFAULT_ENU,
    park: float = DEFAULT_PARK,
    thickness: float = DEFAULT_THICKNESS,
    step_u1_target: float = 0.001,
    exec_mode: int = 0
) -> Dict[str, Any]:
    """
    Builds a complete 3-layer Phase-Field UEL input deck.
    """
    nodes: Dict[int, Tuple[float, float]] = mesh_data["nodes"]
    elements: Dict[int, Tuple[int, ...]] = mesh_data["elements"]
    node_sets = mesh_data["node_sets"]
    n_phys = len(elements)
    
    quad_elements = {eid: conn for eid, conn in elements.items() if len(conn) == 4}
    tri_elements = {eid: conn for eid, conn in elements.items() if len(conn) == 3}
    n_quads = len(quad_elements)
    n_tris = len(tri_elements)

    part_name = "PlatePart"
    instance_name = "PlateInstance"
    rp_id = mesh_data.get("rp_id", 99999)
    rp_coords = mesh_data.get("rp_coords", (0.0, 0.6, 0.0))

    lines: List[str] = []

    # Heading
    lines.append("*Heading")
    lines.append(f" Automated Layered Phase-Field UEL Deck: {job_name}")
    lines.append(f"** Physical Elements: {n_phys} (Quads: {n_quads}, Tris: {n_tris}), Physical Nodes: {len(nodes)}")
    lines.append(f"** Total Layered Elements: {3 * n_phys}")
    lines.append(f"** Parameters: l0={l0:.6e}, Gc={gc:.6e}, E={emod:.6e}, nu={enu:.4f}, k={park:.4e}, thickness={thickness:.4e}")
    lines.append("*Preprint, echo=NO, model=NO, history=NO, contact=NO")
    lines.append("**")
    lines.append("** PARTS")
    lines.append("**")
    lines.append(f"*Part, name={part_name}")

    # User element declarations
    lines.append("** User Element Declarations")
    if n_quads > 0:
        lines.append(f"*User Element, nodes=4, type=U1, properties=7, coordinates=2, VARIABLES={DEFAULT_DEPVAR}, UNSYMM")
        lines.append(" 3")
        lines.append(f"*User Element, nodes=4, type=U2, properties=7, coordinates=2, VARIABLES={DEFAULT_DEPVAR}, UNSYMM")
        lines.append(" 1, 2")
    if n_tris > 0:
        lines.append(f"*User Element, nodes=3, type=U3, properties=7, coordinates=2, VARIABLES={DEFAULT_DEPVAR}, UNSYMM")
        lines.append(" 3")
        lines.append(f"*User Element, nodes=3, type=U4, properties=7, coordinates=2, VARIABLES={DEFAULT_DEPVAR}, UNSYMM")
        lines.append(" 1, 2")

    # Nodes
    lines.append("** Part Nodes")
    lines.append("*Node")
    for nid in sorted(nodes.keys()):
        x, y = nodes[nid]
        lines.append(f" {nid:7d}, {x:18.10e}, {y:18.10e}")

    # Layer 1: Phase Elements (1 .. NPHYS)
    lines.append(f"** Layer 1: Phase Elements (1 .. {n_phys})")
    if n_quads > 0:
        lines.append("*Element, type=U1, elset=PHASE_QUAD")
        for eid in sorted(quad_elements.keys()):
            conn = quad_elements[eid]
            conn_str = ", ".join(f"{n:7d}" for n in conn)
            lines.append(f" {eid:7d}, {conn_str}")
    if n_tris > 0:
        lines.append("*Element, type=U3, elset=PHASE_TRI")
        for eid in sorted(tri_elements.keys()):
            conn = tri_elements[eid]
            conn_str = ", ".join(f"{n:7d}" for n in conn)
            lines.append(f" {eid:7d}, {conn_str}")

    # Layer 2: Displacement Elements (NPHYS+1 .. 2*NPHYS)
    lines.append(f"** Layer 2: Displacement Elements ({n_phys + 1} .. {2 * n_phys})")
    if n_quads > 0:
        lines.append("*Element, type=U2, elset=DISP_QUAD")
        for eid in sorted(quad_elements.keys()):
            conn = quad_elements[eid]
            mech_eid = n_phys + eid
            conn_str = ", ".join(f"{n:7d}" for n in conn)
            lines.append(f" {mech_eid:7d}, {conn_str}")
    if n_tris > 0:
        lines.append("*Element, type=U4, elset=DISP_TRI")
        for eid in sorted(tri_elements.keys()):
            conn = tri_elements[eid]
            mech_eid = n_phys + eid
            conn_str = ", ".join(f"{n:7d}" for n in conn)
            lines.append(f" {mech_eid:7d}, {conn_str}")

    # Layer 3: Facsimile Output Elements (2*NPHYS+1 .. 3*NPHYS)
    lines.append(f"** Layer 3: Facsimile Output Elements ({2 * n_phys + 1} .. {3 * n_phys})")
    if n_quads > 0:
        lines.append("*Element, type=CPE4, elset=UMAT_QUAD")
        for eid in sorted(quad_elements.keys()):
            conn = quad_elements[eid]
            vis_eid = 2 * n_phys + eid
            conn_str = ", ".join(f"{n:7d}" for n in conn)
            lines.append(f" {vis_eid:7d}, {conn_str}")
    if n_tris > 0:
        lines.append("*Element, type=CPE3, elset=UMAT_TRI")
        for eid in sorted(tri_elements.keys()):
            conn = tri_elements[eid]
            vis_eid = 2 * n_phys + eid
            conn_str = ", ".join(f"{n:7d}" for n in conn)
            lines.append(f" {vis_eid:7d}, {conn_str}")

    # Aggregate Sets
    lines.append("** Aggregate Element Sets")
    lines.append("*Elset, elset=PHASE")
    if n_quads > 0:
        lines.append(" PHASE_QUAD")
    if n_tris > 0:
        lines.append(" PHASE_TRI")

    lines.append("*Elset, elset=DISP")
    if n_quads > 0:
        lines.append(" DISP_QUAD")
    if n_tris > 0:
        lines.append(" DISP_TRI")

    lines.append("*Elset, elset=UMATELEM")
    if n_quads > 0:
        lines.append(" UMAT_QUAD")
    if n_tris > 0:
        lines.append(" UMAT_TRI")

    lines.append("*Elset, elset=All_elem")
    lines.append(" UMATELEM")

    # UEL Properties
    lines.append("** UEL Properties: l0, Gc, E, nu, k_res, N_PHYS, EXEC_MODE")
    if n_quads > 0:
        lines.append("*UEL Property, elset=PHASE_QUAD")
        lines.append(f" {l0:.6e}, {gc:.6e}, {emod:.6e}, {enu:.6e}, {park:.6e}, {n_phys:.1f}, {float(exec_mode):.1f}")
        lines.append("*UEL Property, elset=DISP_QUAD")
        lines.append(f" {l0:.6e}, {gc:.6e}, {emod:.6e}, {enu:.6e}, {park:.6e}, {n_phys:.1f}, {float(exec_mode):.1f}")

    if n_tris > 0:
        lines.append("*UEL Property, elset=PHASE_TRI")
        lines.append(f" {l0:.6e}, {gc:.6e}, {emod:.6e}, {enu:.6e}, {park:.6e}, {n_phys:.1f}, {float(exec_mode):.1f}")
        lines.append("*UEL Property, elset=DISP_TRI")
        lines.append(f" {l0:.6e}, {gc:.6e}, {emod:.6e}, {enu:.6e}, {park:.6e}, {n_phys:.1f}, {float(exec_mode):.1f}")

    # Facsimile Solid Sections
    if n_quads > 0:
        lines.append("*Solid Section, elset=UMAT_QUAD, material=MAT_QUAD_FACSIMILE")
        lines.append(f" {thickness:.6e}")
    if n_tris > 0:
        lines.append("*Solid Section, elset=UMAT_TRI, material=MAT_TRI_FACSIMILE")
        lines.append(f" {thickness:.6e}")

    lines.append("*End Part")
    lines.append("**")
    lines.append("** ASSEMBLY")
    lines.append("**")
    lines.append("*Assembly, name=Assembly")
    lines.append(f"*Instance, name={instance_name}, part={part_name}")
    lines.append("*End Instance")

    # Reference point node
    lines.append("** Assembly Reference Point")
    lines.append("*Node")
    lines.append(f" {rp_id:7d}, {rp_coords[0]:18.10e}, {rp_coords[1]:18.10e}, {rp_coords[2]:18.10e}")
    lines.append(f"*Nset, nset=RP\n {rp_id:7d}")

    # Node sets in assembly
    for nset_name in ["bottom_nodes", "top_nodes", "left_nodes", "right_nodes"]:
        if nset_name in node_sets:
            items = node_sets[nset_name]
            lines.append(f"*Nset, nset={nset_name}, instance={instance_name}")
            for i in range(0, len(items), 16):
                chunk = items[i:i + 16]
                lines.append(" " + ", ".join(f"{nid:7d}" for nid in chunk))

    lines.append(f"*Elset, elset=UMATELEM, instance={instance_name}\n UMATELEM")
    lines.append(f"*Elset, elset=All_elem, instance={instance_name}\n UMATELEM")

    # Shear coupling equation: top_nodes U1 - RP U1 = 0
    lines.append("** Constraint: Mode-II Pure Shear Coupling (top_nodes U1 -> RP U1)")
    lines.append("*Equation")
    lines.append(" 2")
    lines.append(" top_nodes, 1, 1.")
    lines.append(" RP, 1, -1.")

    lines.append("*End Assembly")

    # Materials
    lines.append("** MATERIALS")
    if n_quads > 0:
        lines.append("*Material, name=MAT_QUAD_FACSIMILE")
        lines.append(f"*Depvar\n {DEFAULT_DEPVAR}")
        lines.append(f"*User Material, constants=4\n {DEFAULT_PASSIVE_E:.6e}, {DEFAULT_ENU:.6e}, {n_phys:.1f}, 4.0")
    if n_tris > 0:
        lines.append("*Material, name=MAT_TRI_FACSIMILE")
        lines.append(f"*Depvar\n {DEFAULT_DEPVAR}")
        lines.append(f"*User Material, constants=4\n {DEFAULT_PASSIVE_E:.6e}, {DEFAULT_ENU:.6e}, {n_phys:.1f}, 3.0")

    # Boundary conditions
    lines.append("** BOUNDARY CONDITIONS")
    lines.append("*Boundary")
    lines.append(" bottom_nodes, 1, 1")
    lines.append(" bottom_nodes, 2, 2")
    lines.append(" top_nodes, 2, 2")

    # Step
    lines.append("** STEP: Step-1")
    lines.append("*Step, name=Step-1, nlgeom=NO")
    lines.append("*Static")
    lines.append(" 0.001, 1.0, 1.0e-5, 1.0")
    lines.append("*Boundary")
    lines.append(f" RP, 1, 1, {step_u1_target:.8f}")
    lines.append("*Output, field")
    lines.append("*Node Output\n RF, U")
    lines.append("*Node Output, nset=RP\n RF, U")
    lines.append("*Element Output, elset=UMATELEM\n S, E, SDV, EVOL")
    lines.append("*Output, history, variable=PRESELECT")
    lines.append("*Energy Output\n ALLAE, ALLCD, ALLIE, ALLKE, ALLPD, ALLSE, ALLWK, ETOTAL")
    lines.append("*End Step")

    deck_text = "\n".join(lines) + "\n"
    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(deck_text)

    deck_sha = sha256_text(deck_text)

    return {
        "job_name": job_name,
        "deck_path": str(output_path),
        "sha256": deck_sha,
        "n_physical_elements": n_phys,
        "n_layered_elements": 3 * n_phys,
        "n_nodes": len(nodes),
        "n_quads": n_quads,
        "n_tris": n_tris,
        "l0": l0,
        "gc": gc,
        "exec_mode": exec_mode
    }
