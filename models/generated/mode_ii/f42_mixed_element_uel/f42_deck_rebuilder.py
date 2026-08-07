#!/usr/bin/env python3
"""
F42-R1 Offline Mixed-Element Input Deck Parser and Rebuilder

Parses remeshed connectivity from Abaqus (Job-2.inp), classifies physical elements
by node count (CPE4 vs CPE3), and generates the corresponding 3-node and 4-node
layered UEL input deck (Job-2_UEL.inp) with unique element labels across layers.
"""

import sys
import os
import re

def compute_element_area_2d(coords):
    """
    Compute signed 2D area of a polygon defined by ordered node coordinates.
    coords: list of (x, y) tuples.
    Returns signed area.
    """
    n = len(coords)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += coords[i][0] * coords[j][1] - coords[j][0] * coords[i][1]
    return 0.5 * area

class MixedDeckRebuilder:
    def __init__(self, input_deck_path):
        self.input_deck_path = input_deck_path
        self.nodes = {}           # node_id -> (x, y)
        self.physical_elems = {}  # phys_index (1..Nphys) -> {'type': 'QUAD'/'TRI', 'nodes': [nids], 'orig_id': orig_id}
        self.rejected = []        # list of rejection reason strings

    def parse(self):
        """Parse raw Abaqus input file for nodes and elements."""
        if not os.path.exists(self.input_deck_path):
            raise FileNotFoundError(f"Input deck not found: {self.input_deck_path}")

        with open(self.input_deck_path, 'r') as f:
            lines = f.readlines()

        current_mode = None
        phys_index = 0

        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.startswith('**'):
                continue

            if line_str.lower().startswith('*node'):
                current_mode = 'NODE'
                continue
            elif line_str.lower().startswith('*element'):
                current_mode = 'ELEMENT'
                continue
            elif line_str.startswith('*'):
                current_mode = None
                continue

            if current_mode == 'NODE':
                tokens = [t.strip() for t in line_str.split(',')]
                if len(tokens) >= 3:
                    node_id = int(tokens[0])
                    x = float(tokens[1])
                    y = float(tokens[2])
                    self.nodes[node_id] = (x, y)

            elif current_mode == 'ELEMENT':
                tokens = [t.strip() for t in line_str.split(',')]
                if len(tokens) >= 4:
                    orig_id = int(tokens[0])
                    node_ids = [int(t) for t in tokens[1:] if t]

                    if len(node_ids) == 4:
                        if len(set(node_ids)) != 4:
                            self.rejected.append(f"Element {orig_id}: duplicate node IDs {node_ids}")
                            continue
                        coords = [self.nodes[nid] for nid in node_ids if nid in self.nodes]
                        if len(coords) != 4:
                            self.rejected.append(f"Element {orig_id}: missing node coordinates for {node_ids}")
                            continue
                        area = compute_element_area_2d(coords)
                        if area <= 0.0:
                            self.rejected.append(f"Element {orig_id}: non-positive area {area:.6e}")
                            continue
                        phys_index += 1
                        self.physical_elems[phys_index] = {'type': 'QUAD', 'nodes': node_ids, 'orig_id': orig_id}

                    elif len(node_ids) == 3:
                        if len(set(node_ids)) != 3:
                            self.rejected.append(f"Element {orig_id}: duplicate node IDs {node_ids}")
                            continue
                        coords = [self.nodes[nid] for nid in node_ids if nid in self.nodes]
                        if len(coords) != 3:
                            self.rejected.append(f"Element {orig_id}: missing node coordinates for {node_ids}")
                            continue
                        area = compute_element_area_2d(coords)
                        if area <= 0.0:
                            self.rejected.append(f"Element {orig_id}: non-positive area {area:.6e}")
                            continue
                        phys_index += 1
                        self.physical_elems[phys_index] = {'type': 'TRI', 'nodes': node_ids, 'orig_id': orig_id}

                    else:
                        self.rejected.append(f"Element {orig_id}: unsupported node count {len(node_ids)}")

    def build_mixed_uel_deck(self, output_path):
        """Generate Job-2_UEL.inp with unique element labels across U1, U2, U3, U4 and CPE4/CPE3 layers."""
        nphys = len(self.physical_elems)
        if self.rejected:
            print(f"Rebuilder encountered {len(self.rejected)} rejected elements:")
            for r in self.rejected:
                print(f"  REJECTED: {r}")

        lines = []
        lines.append("** ==========================================================")
        lines.append("** Job-2_UEL.inp: F42-R1 Mixed 3-Node/4-Node Layered Phase Deck")
        lines.append("** ==========================================================")
        lines.append("*Heading")
        lines.append(" F42-R1 Corrected Mixed Element UEL Model")

        # 1. User Element Cards
        lines.append("** User Element Declarations")
        lines.append("*User Element, nodes=4, type=U1, properties=3, coordinates=2, VARIABLES=8")
        lines.append(" 3")
        lines.append("*User Element, nodes=4, type=U2, properties=4, coordinates=2, VARIABLES=56")
        lines.append(" 1, 2")
        lines.append("*User Element, nodes=3, type=U3, properties=3, coordinates=2, VARIABLES=6")
        lines.append(" 3")
        lines.append("*User Element, nodes=3, type=U4, properties=4, coordinates=2, VARIABLES=42")
        lines.append(" 1, 2")

        # 2. Nodes
        lines.append("*Node")
        for nid, (x, y) in sorted(self.nodes.items()):
            lines.append(f" {nid}, {x:.6f}, {y:.6f}")

        # Classify element IDs by layer
        phase_quad_labels = []
        phase_tri_labels = []
        disp_quad_labels = []
        disp_tri_labels = []
        umat_quad_labels = []
        umat_tri_labels = []

        # Layer 1: Phase Elements (labels 1 .. Nphys)
        lines.append("** Layer 1: Phase Elements")
        for p, info in sorted(self.physical_elems.items()):
            label = p
            nids_str = ", ".join(str(n) for n in info['nodes'])
            if info['type'] == 'QUAD':
                lines.append(f" {label}, {nids_str}")
                phase_quad_labels.append(label)
            else:
                lines.append(f" {label}, {nids_str}")
                phase_tri_labels.append(label)

        # Wrap Phase Element blocks under element types
        # Note: In Abaqus deck format, element blocks specify type
        # Re-organize Phase layer output cleanly by type:
        lines_clean = lines[:lines.index("** Layer 1: Phase Elements")]
        lines_clean.append("** Layer 1: Phase Elements")

        quad_phase = {p: info for p, info in self.physical_elems.items() if info['type'] == 'QUAD'}
        tri_phase = {p: info for p, info in self.physical_elems.items() if info['type'] == 'TRI'}

        if quad_phase:
            lines_clean.append("*Element, type=U1, elset=PHASE_QUAD")
            for p, info in sorted(quad_phase.items()):
                lines_clean.append(f" {p}, " + ", ".join(str(n) for n in info['nodes']))
        if tri_phase:
            lines_clean.append("*Element, type=U3, elset=PHASE_TRI")
            for p, info in sorted(tri_phase.items()):
                lines_clean.append(f" {p}, " + ", ".join(str(n) for n in info['nodes']))

        # Layer 2: Displacement Elements (labels Nphys + 1 .. 2*Nphys)
        lines_clean.append("** Layer 2: Displacement Elements")
        if quad_phase:
            lines_clean.append("*Element, type=U2, elset=DISP_QUAD")
            for p, info in sorted(quad_phase.items()):
                label = nphys + p
                lines_clean.append(f" {label}, " + ", ".join(str(n) for n in info['nodes']))
                disp_quad_labels.append(label)

        if tri_phase:
            lines_clean.append("*Element, type=U4, elset=DISP_TRI")
            for p, info in sorted(tri_phase.items()):
                label = nphys + p
                lines_clean.append(f" {label}, " + ", ".join(str(n) for n in info['nodes']))
                disp_tri_labels.append(label)

        # Layer 3: Facsimile Elements (labels 2*Nphys + 1 .. 3*Nphys)
        lines_clean.append("** Layer 3: Facsimile Output Elements")
        if quad_phase:
            lines_clean.append("*Element, type=CPE4, elset=UMAT_QUAD")
            for p, info in sorted(quad_phase.items()):
                label = 2 * nphys + p
                lines_clean.append(f" {label}, " + ", ".join(str(n) for n in info['nodes']))
                umat_quad_labels.append(label)

        if tri_phase:
            lines_clean.append("*Element, type=CPE3, elset=UMAT_TRI")
            for p, info in sorted(tri_phase.items()):
                label = 2 * nphys + p
                lines_clean.append(f" {label}, " + ", ".join(str(n) for n in info['nodes']))
                umat_tri_labels.append(label)

        # Element Sets
        lines_clean.append("** Aggregate Element Sets")
        lines_clean.append("*Elset, elset=PHASE")
        if quad_phase:
            lines_clean.append(" PHASE_QUAD")
        if tri_phase:
            lines_clean.append(" PHASE_TRI")

        lines_clean.append("*Elset, elset=DISP")
        if quad_phase:
            lines_clean.append(" DISP_QUAD")
        if tri_phase:
            lines_clean.append(" DISP_TRI")

        lines_clean.append("*Elset, elset=UMATELEM")
        if quad_phase:
            lines_clean.append(" UMAT_QUAD")
        if tri_phase:
            lines_clean.append(" UMAT_TRI")

        lines_clean.append("*Elset, elset=All_elem")
        lines_clean.append(" UMATELEM")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write("\n".join(lines_clean) + "\n")

        return len(quad_phase), len(tri_phase), len(self.rejected)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: f42_deck_rebuilder.py <input_deck.inp> <output_uel_deck.inp>")
        sys.exit(1)
    rebuilder = MixedDeckRebuilder(sys.argv[1])
    rebuilder.parse()
    nq, nt, nr = rebuilder.build_mixed_uel_deck(sys.argv[2])
    print(f"Successfully rebuilt mixed UEL deck: {nq} Quads, {nt} Triangles, {nr} Rejected")
