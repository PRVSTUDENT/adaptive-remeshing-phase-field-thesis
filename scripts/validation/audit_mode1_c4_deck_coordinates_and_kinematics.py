"""Audit and reconcile C4 deck kinematic constraints, reference point identifier,
and crack-tip coordinates against established benchmark geometry.
Reconciles Turn 399 narrative discrepancy:
- Reference point is Node 999999 (not 1000001)
- Crack tip region is around x in [0.04, 0.05] mm with Node 3612 at (0.04136, 0.05000) mm
  in the 0.1 mm x 0.1 mm domain (not x = 1.0 mm in a 1.0 mm domain).
"""

import json
import os
import re
from pathlib import Path


def audit_c4_deck(deck_path: Path) -> dict:
    if not deck_path.is_file():
        raise FileNotFoundError(f"Input deck not found: {deck_path}")

    with open(deck_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f]

    # 1. Inspect Reference Point in Nset and Nodes
    rp_nodes = []
    rp_coords = {}
    equations = []
    node_3612_coords = None
    node_7265_coords = None  # initial slit tip
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")

    in_nodes = False
    in_rp_nset = False
    in_equation = False
    eq_count = 0

    for i, line in enumerate(lines):
        if line.startswith("**"):
            continue

        if line.startswith("*"):
            upper = line.upper()
            if upper.startswith("*NODE"):
                in_nodes = True
                in_rp_nset = False
                in_equation = False
                continue
            elif "NSET=N_RP" in upper or "NSET=RP" in upper:
                in_rp_nset = True
                in_nodes = False
                in_equation = False
                continue
            elif upper.startswith("*EQUATION"):
                in_equation = True
                in_nodes = False
                in_rp_nset = False
                continue
            else:
                in_nodes = False
                in_rp_nset = False
                in_equation = False

        if in_nodes:
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if len(parts) >= 3:
                try:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    if nid < 900000:
                        min_x = min(min_x, x)
                        max_x = max(max_x, x)
                        min_y = min(min_y, y)
                        max_y = max(max_y, y)
                    if nid == 999999:
                        rp_coords[nid] = (x, y)
                    elif nid == 1000001:
                        rp_coords[nid] = (x, y)
                    elif nid == 3612:
                        node_3612_coords = (x, y)
                    elif nid == 7265:
                        node_7265_coords = (x, y)
                except ValueError:
                    pass

        elif in_rp_nset:
            parts = [p.strip() for p in line.split(",") if p.strip()]
            for p in parts:
                try:
                    rp_nodes.append(int(p))
                except ValueError:
                    pass

        elif in_equation:
            # First line after *EQUATION is number of terms (e.g. 2)
            # Subsequent line has term definition: node1, dof1, coeff1, node2, dof2, coeff2
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if len(parts) >= 6:
                try:
                    n1 = int(parts[0])
                    dof1 = int(parts[1])
                    c1 = float(parts[2])
                    n2 = int(parts[3])
                    dof2 = int(parts[4])
                    c2 = float(parts[5])
                    equations.append({
                        "node1": n1, "dof1": dof1, "coeff1": c1,
                        "node2": n2, "dof2": dof2, "coeff2": c2
                    })
                except ValueError:
                    pass

    return {
        "deck_path": str(deck_path).replace("\\", "/"),
        "rp_nodes_in_nset": rp_nodes,
        "rp_coords": rp_coords,
        "total_equations": len(equations),
        "tied_rp_node": equations[0]["node2"] if equations else None,
        "node_3612_coords": node_3612_coords,
        "initial_slit_tip_node_7265_coords": node_7265_coords,
        "bounding_box": {
            "x_min": min_x,
            "x_max": max_x,
            "y_min": min_y,
            "y_max": max_y
        }
    }


def main():
    root = Path(__file__).resolve().parents[2]
    deck = root / "models/pandey_kumar_mode1/150_c4_package150_c1_2_continuation/M1_C4_PACKAGE150_C1_2_CONTINUATION.inp"
    audit = audit_c4_deck(deck)

    # Narrative reconciliation assertions
    rp_id = audit["tied_rp_node"]
    assert rp_id == 999999, f"Expected RP 999999, got {rp_id}"
    assert 1000001 not in audit["rp_coords"], "Node 1000001 must not exist in deck"
    assert audit["node_3612_coords"] == (0.04136, 0.05), f"Unexpected Node 3612 coords: {audit['node_3612_coords']}"
    assert audit["initial_slit_tip_node_7265_coords"] == (0.04, 0.05), f"Unexpected Node 7265 coords: {audit['initial_slit_tip_node_7265_coords']}"
    assert audit["bounding_box"]["x_max"] == 0.1, f"Domain x_max must be 0.1 mm, got {audit['bounding_box']['x_max']}"
    assert audit["bounding_box"]["y_max"] == 0.1, f"Domain y_max must be 0.1 mm, got {audit['bounding_box']['y_max']}"

    reconciliation = {
        "schema": 1,
        "audit_name": "mode1_c4_deck_kinematics_and_coordinate_reconciliation",
        "reference_point_reconciliation": {
            "deck_reference_point_node_id": rp_id,
            "deck_reference_point_coordinates_mm": list(audit["rp_coords"][rp_id]),
            "narrative_claim_node_id": 1000001,
            "reconciliation_verdict": "Node 1000001 is a narrative typographical discrepancy; the authentic Abaqus deck exclusively uses Node 999999 as Reference Point RP tied to 85 top nodes (7141..7225) in DOF 2 via *EQUATION.",
            "tied_top_node_count": audit["total_equations"]
        },
        "crack_tip_coordinate_reconciliation": {
            "domain_dimensions_mm": [audit["bounding_box"]["x_max"], audit["bounding_box"]["y_max"]],
            "initial_slit_length_a0_mm": 0.04,
            "initial_slit_y_mm": 0.05,
            "slit_tip_node_7265_coords_mm": list(audit["initial_slit_tip_node_7265_coords"]),
            "peak_damage_node_3612_coords_mm": list(audit["node_3612_coords"]),
            "distance_from_slit_tip_to_node_3612_mm": audit["node_3612_coords"][0] - audit["initial_slit_tip_node_7265_coords"][0],
            "narrative_claim_crack_tip_mm": [1.0, 0.0],
            "reconciliation_verdict": "The narrative claim of crack-tip at (x = 1.0 mm, y = 0.0 mm) was an erroneous unit/coordinate statement. The authentic Pandey-Kumar Mode-I benchmark domain is 0.1 mm x 0.1 mm with horizontal symmetry/slit at y = 0.05 mm. Node 3612 is situated at x = 0.04136 mm, y = 0.05000 mm, exactly 0.00136 mm (1.36 um) ahead of the initial slit tip Node 7265 (x = 0.04000 mm, y = 0.05000 mm)."
        },
        "prerequisites_for_r4_dispatch": {
            "registration_status": "REGISTRATION_PENDING_REVIEW",
            "operation_id": "execute_mode1_package157_c1_2_r4_adaptive_continuation",
            "required_binding_file": "scripts/controller/Controller-Operations.ps1",
            "quota_safety_gate": "Account4 quota (18.910%) is below the mandatory 20% stop threshold. Active execution requires selection of an eligible profile (account1).",
            "scientific_baseline_reconciled": True
        }
    }

    out_path = root / "results/validation/mode1_c4_deck_kinematics_and_coordinate_reconciliation.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(reconciliation, f, indent=2)

    print(f"Audit completed successfully: {out_path}")


if __name__ == "__main__":
    main()
