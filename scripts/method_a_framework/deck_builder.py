# -*- coding: utf-8 -*-
"""
scripts/method_a_framework/deck_builder.py
==========================================
Reconstructs compatible 3-layer UEL + UMAT production input decks for
the Reusable Method A Adaptive-Remeshing Framework.

Layers generated:
- Layer 1 (Phase Field): Element types U1 (4-node quads) and U3 (3-node tris), DOF 3.
- Layer 2 (Mechanical): Element types U2 (4-node quads) and U4 (3-node tris), DOFs 1, 2.
- Layer 3 (Visualizer): Element types CPE4 (quads) and CPE3 (tris) with UMAT material.
- Wrapped *NSET cards (<= 16 entries/line).
- Coupled top-edge kinematics via *EQUATION and bottom-edge Dirichlet reactions.
"""

import os
import re


def wrap_nset_line(node_list, max_per_line=16):
    """
    Formats a list of integers into comma-separated lines with at most max_per_line entries.
    """
    lines = []
    for i in range(0, len(node_list), max_per_line):
        chunk = node_list[i:i + max_per_line]
        lines.append(", ".join(str(n) for n in chunk))
    return lines


class ProductionDeckBuilder(object):
    """
    Builds a 3-layer production phase-field input deck from a physical adapted mesh.
    """

    def __init__(self, physical_inp_path, config):
        if not os.path.isfile(physical_inp_path):
            raise IOError("Physical mesh file not found: %s" % physical_inp_path)
        self.physical_inp_path = physical_inp_path
        self.config = config
        self.nodes = {}       # nid -> (x, y)
        self.quads = {}       # eid -> [n1, n2, n3, n4]
        self.tris = {}        # eid -> [n1, n2, n3]
        self.n_phys = 0

    def parse_physical_mesh(self):
        """
        Parses nodes and elements from the physical mesh input deck.
        """
        with open(self.physical_inp_path, "r") as f:
            lines = f.readlines()

        current_section = None
        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.startswith("**"):
                continue

            if line_str.startswith("*"):
                upper = line_str.upper()
                if upper.startswith("*NODE"):
                    current_section = "NODE"
                    continue
                elif upper.startswith("*ELEMENT"):
                    current_section = "ELEMENT"
                    continue
                else:
                    current_section = "OTHER"
                    continue

            if current_section == "NODE":
                parts = [p.strip() for p in line_str.split(",") if p.strip()]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        self.nodes[nid] = (float(parts[1]), float(parts[2]))
                    except ValueError:
                        pass

            elif current_section == "ELEMENT":
                parts = [p.strip() for p in line_str.split(",") if p.strip()]
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        enodes = [int(p) for p in parts[1:]]
                        if len(enodes) == 4:
                            self.quads[eid] = enodes
                        elif len(enodes) == 3:
                            self.tris[eid] = enodes
                    except ValueError:
                        pass

        self.n_phys = len(self.quads) + len(self.tris)
        return self.n_phys

    def detect_boundary_nodes(self, tol=1.0e-5):
        """
        Detects top and bottom boundary nodes based on bounding box extrema.
        """
        ys = [pt[1] for pt in self.nodes.values()]
        xs = [pt[0] for pt in self.nodes.values()]
        ymin, ymax = min(ys), max(ys)
        xmin, xmax = min(xs), max(xs)

        bottom_nodes = []
        top_nodes = []
        pin_node = None
        min_x_dist = 1.0e9

        for nid, (x, y) in sorted(self.nodes.items()):
            if abs(y - ymin) <= tol:
                bottom_nodes.append(nid)
                if abs(x - xmin) < min_x_dist:
                    min_x_dist = abs(x - xmin)
                    pin_node = nid
            elif abs(y - ymax) <= tol:
                top_nodes.append(nid)

        if not pin_node and bottom_nodes:
            pin_node = bottom_nodes[0]

        return {
            "bottom_nodes": bottom_nodes,
            "top_nodes": top_nodes,
            "pin_node": pin_node,
            "bbox": (xmin, xmax, ymin, ymax)
        }

    def build_deck(self, output_inp_path):
        """
        Constructs the complete 3-layer production input deck and writes to output_inp_path.
        """
        if self.n_phys == 0:
            self.parse_physical_mesh()

        bdata = self.detect_boundary_nodes()
        bottom_nodes = bdata["bottom_nodes"]
        top_nodes = bdata["top_nodes"]
        pin_node = bdata["pin_node"]
        xmin, xmax, ymin, ymax = bdata["bbox"]

        # Reference node ID is max node ID + 1
        max_nid = max(self.nodes.keys())
        rp_node = max_nid + 1
        rp_x = 0.5 * (xmin + xmax)
        rp_y = ymax

        mat = self.config.material
        loading = self.config.loading
        n_phys = self.n_phys

        out = []
        out.append("** ==========================================================")
        out.append("** REUSABLE METHOD A PRODUCTION PHASE-FIELD INPUT DECK")
        out.append("** Generated by scripts/method_a_framework/deck_builder.py")
        out.append("** Physical Elements: %d (Quads: %d, Tris: %d)" % (n_phys, len(self.quads), len(self.tris)))
        out.append("** Layered Elements: %d, Total Nodes: %d" % (3 * n_phys, len(self.nodes) + 1))
        out.append("** ==========================================================")
        out.append("*HEADING")
        out.append("Method A Adaptive Remeshing Phase-Field Production Analysis")

        # User Element Type Definitions
        out.append("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
        out.append("3")
        out.append("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
        out.append("1, 2")
        out.append("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
        out.append("3")
        out.append("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
        out.append("1, 2")

        # Nodal Coordinates
        out.append("*NODE")
        for nid, (x, y) in sorted(self.nodes.items()):
            out.append("%d, %.8e, %.8e" % (nid, x, y))
        out.append("%d, %.8e, %.8e" % (rp_node, rp_x, rp_y))

        # Re-numbering elements sequentially into tris and quads:
        # All tris get physical indices 1..N_tri
        # All quads get physical indices (N_tri + 1)..N_phys
        ordered_tris = sorted(self.tris.items())
        ordered_quads = sorted(self.quads.items())
        n_tri = len(ordered_tris)

        # ---------------------------------------------------------------------
        # LAYER 1: Phase Field (U1 quads, U3 tris)
        # ---------------------------------------------------------------------
        if ordered_tris:
            out.append("*ELEMENT, TYPE=U3, ELSET=PHASE_TRIS")
            for idx, (old_eid, enodes) in enumerate(ordered_tris):
                eid = idx + 1
                out.append("%d, %s" % (eid, ", ".join(str(n) for n in enodes)))

        if ordered_quads:
            out.append("*ELEMENT, TYPE=U1, ELSET=PHASE_QUADS")
            for idx, (old_eid, enodes) in enumerate(ordered_quads):
                eid = n_tri + idx + 1
                out.append("%d, %s" % (eid, ", ".join(str(n) for n in enodes)))

        # ---------------------------------------------------------------------
        # LAYER 2: Mechanical Displacements (U2 quads, U4 tris)
        # ---------------------------------------------------------------------
        if ordered_tris:
            out.append("*ELEMENT, TYPE=U4, ELSET=MECH_TRIS")
            for idx, (old_eid, enodes) in enumerate(ordered_tris):
                eid = n_phys + idx + 1
                out.append("%d, %s" % (eid, ", ".join(str(n) for n in enodes)))

        if ordered_quads:
            out.append("*ELEMENT, TYPE=U2, ELSET=MECH_QUADS")
            for idx, (old_eid, enodes) in enumerate(ordered_quads):
                eid = n_phys + n_tri + idx + 1
                out.append("%d, %s" % (eid, ", ".join(str(n) for n in enodes)))

        # ---------------------------------------------------------------------
        # LAYER 3: Visualizer Companion Elements (CPE4 quads, CPE3 tris)
        # ---------------------------------------------------------------------
        if ordered_tris:
            out.append("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS")
            for idx, (old_eid, enodes) in enumerate(ordered_tris):
                eid = 2 * n_phys + idx + 1
                out.append("%d, %s" % (eid, ", ".join(str(n) for n in enodes)))

        if ordered_quads:
            out.append("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS")
            for idx, (old_eid, enodes) in enumerate(ordered_quads):
                eid = 2 * n_phys + n_tri + idx + 1
                out.append("%d, %s" % (eid, ", ".join(str(n) for n in enodes)))

        # Element Sets
        out.append("*ELSET, ELSET=PHASE_ELEM")
        if ordered_tris:
            out.append("PHASE_TRIS")
        if ordered_quads:
            out.append("PHASE_QUADS")

        out.append("*ELSET, ELSET=MECH_ELEM")
        if ordered_tris:
            out.append("MECH_TRIS")
        if ordered_quads:
            out.append("MECH_QUADS")

        out.append("*ELSET, ELSET=umatelem")
        if ordered_tris:
            out.append("UMAT_TRIS")
        if ordered_quads:
            out.append("UMAT_QUADS")

        out.append("*ELSET, ELSET=All_elem")
        out.append("umatelem")

        # Boundary Node Sets (Wrapped to <= 16 per line)
        out.append("*NSET, NSET=N_BOTTOM")
        for line in wrap_nset_line(bottom_nodes):
            out.append(line)

        out.append("*NSET, NSET=N_TOP")
        for line in wrap_nset_line(top_nodes):
            out.append(line)

        out.append("*NSET, NSET=N_RP")
        out.append("%d" % rp_node)

        out.append("*NSET, NSET=N_PIN")
        out.append("%d" % pin_node)

        # UEL Properties
        # Constants: l0, Gc, E, nu, k_residual, N_PHYS
        uel_props = "%.6f, %.6f, %.2f, %.2f, %.1e, %d.0" % (
            mat["l0"], mat["Gc"], mat["E"], mat["nu"], mat["k_residual"], n_phys
        )
        out.append("*UEL PROPERTY, ELSET=PHASE_ELEM")
        out.append(uel_props)
        out.append("*UEL PROPERTY, ELSET=MECH_ELEM")
        out.append(uel_props)

        # Solid Section & Material
        out.append("*SOLID SECTION, ELSET=umatelem, MATERIAL=UMAT_MAT")
        out.append("1.0")
        out.append("*MATERIAL, NAME=UMAT_MAT")
        out.append("*USER MATERIAL, CONSTANTS=3")
        out.append("%.2f, %.2f, %d.0" % (mat["E"], mat["nu"], n_phys))
        out.append("*DEPVAR")
        out.append("20")

        # Top Boundary MPC Equations linking top surface to Reference Node
        out.append("*EQUATION")
        for top_nid in top_nodes:
            out.append("2")
            out.append("%d, 2, 1.0, %d, 2, -1.0" % (top_nid, rp_node))

        # STEP 1: Pre-Critical Loading
        out.append("** ----------------------------------------------------------")
        out.append("** STEP 1: Pre-Critical Loading to u = %.4f mm" % loading["step1_disp"])
        out.append("** ----------------------------------------------------------")
        out.append("*STEP, NAME=Step-1, NLGEOM=NO, INC=2500")
        out.append("*STATIC")
        out.append("%.1E, 1.0, %.1E, %.1E" % (loading["step1_dt"], loading["dt_min"], loading["step1_dt"]))
        out.append("*BOUNDARY")
        out.append("N_BOTTOM, 2, 2, 0.0")
        out.append("N_PIN, 1, 1, 0.0")
        out.append("N_RP, 2, 2, %.4f" % loading["step1_disp"])
        out.append("*RESTART, WRITE, FREQUENCY=0")
        out.append("*OUTPUT, FIELD, FREQUENCY=1")
        out.append("*NODE OUTPUT, NSET=N_RP")
        out.append("U, RF")
        out.append("*NODE OUTPUT, NSET=N_BOTTOM")
        out.append("RF")
        out.append("*ELEMENT OUTPUT, ELSET=All_elem")
        out.append("SDV")
        out.append("*END STEP")

        # STEP 2: Fracture Propagation
        out.append("** ----------------------------------------------------------")
        out.append("** STEP 2: Fracture Propagation to u = %.4f mm" % loading["step2_disp"])
        out.append("** ----------------------------------------------------------")
        out.append("*STEP, NAME=Step-2, NLGEOM=NO, INC=6000")
        out.append("*STATIC")
        out.append("%.1E, 1.0, %.1E, %.1E" % (loading["step2_dt"], loading["dt_min"], loading["step2_dt"]))
        out.append("*CONTROLS, PARAMETERS=TIME INCREMENTATION")
        out.append("4, 10, 9, 20, 10, 4, 0, 10")
        out.append("*BOUNDARY")
        out.append("N_RP, 2, 2, %.4f" % loading["step2_disp"])
        out.append("*RESTART, WRITE, FREQUENCY=0")
        out.append("*OUTPUT, FIELD, FREQUENCY=1")
        out.append("*NODE OUTPUT, NSET=N_RP")
        out.append("U, RF")
        out.append("*NODE OUTPUT, NSET=N_BOTTOM")
        out.append("RF")
        out.append("*ELEMENT OUTPUT, ELSET=All_elem")
        out.append("SDV")
        out.append("*END STEP")

        # Write file
        with open(output_inp_path, "w") as f:
            f.write("\n".join(out) + "\n")

        return {
            "output_inp_path": output_inp_path,
            "physical_elements": n_phys,
            "layered_elements": 3 * n_phys,
            "nodes": len(self.nodes) + 1,
            "bottom_nodes_count": len(bottom_nodes),
            "top_nodes_count": len(top_nodes)
        }
