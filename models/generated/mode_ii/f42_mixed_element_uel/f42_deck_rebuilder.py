#!/usr/bin/env python3
"""
F42 Offline Mixed-Element Input Deck Parser and Rebuilder

Parses remeshed connectivity from Abaqus (Job-2.inp), classifies physical elements
by node count (CPE4 vs CPE3), and generates the corresponding 3-node and 4-node
layered UEL input deck (Job-2_UEL.inp).
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
        self.nodes = {}       # node_id -> (x, y)
        self.quad_elems = {}  # elem_id -> [n1, n2, n3, n4]
        self.tri_elems = {}   # elem_id -> [n1, n2, n3]
        self.rejected = []    # list of rejection reason strings

    def parse(self):
        """Parse raw Abaqus input file for nodes and elements."""
        if not os.path.exists(self.input_deck_path):
            raise FileNotFoundError(f"Input deck not found: {self.input_deck_path}")

        with open(self.input_deck_path, 'r') as f:
            lines = f.readlines()

        current_mode = None
        current_elem_type = None

        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.startswith('**'):
                continue

            if line_str.lower().startswith('*node'):
                current_mode = 'NODE'
                continue
            elif line_str.lower().startswith('*element'):
                current_mode = 'ELEMENT'
                # Parse element type if present
                m = re.search(r'type\s*=\s*([A-Za-z0-9]+)', line_str, re.IGNORECASE)
                if m:
                    current_elem_type = m.group(1).upper()
                else:
                    current_elem_type = None
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
                    elem_id = int(tokens[0])
                    node_ids = [int(t) for t in tokens[1:] if t]

                    # Validate connectivity length and physical type
                    if len(node_ids) == 4:
                        # Check duplicate node IDs in same element
                        if len(set(node_ids)) != 4:
                            self.rejected.append(f"Element {elem_id}: duplicate node IDs in connectivity {node_ids}")
                            continue
                        coords = [self.nodes[nid] for nid in node_ids if nid in self.nodes]
                        if len(coords) != 4:
                            self.rejected.append(f"Element {elem_id}: missing node coordinates for {node_ids}")
                            continue
                        area = compute_element_area_2d(coords)
                        if area <= 0.0:
                            self.rejected.append(f"Element {elem_id}: non-positive area {area:.6e}")
                            continue
                        self.quad_elems[elem_id] = node_ids

                    elif len(node_ids) == 3:
                        if len(set(node_ids)) != 3:
                            self.rejected.append(f"Element {elem_id}: duplicate node IDs in connectivity {node_ids}")
                            continue
                        coords = [self.nodes[nid] for nid in node_ids if nid in self.nodes]
                        if len(coords) != 3:
                            self.rejected.append(f"Element {elem_id}: missing node coordinates for {node_ids}")
                            continue
                        area = compute_element_area_2d(coords)
                        if area <= 0.0:
                            self.rejected.append(f"Element {elem_id}: non-positive area {area:.6e}")
                            continue
                        self.tri_elems[elem_id] = node_ids

                    else:
                        self.rejected.append(f"Element {elem_id}: unsupported node count {len(node_ids)}")

    def build_mixed_uel_deck(self, output_path):
        """Generate Job-2_UEL.inp with separate U11, U12, U21, U22 declarations."""
        if self.rejected:
            print(f"Rebuilder encountered {len(self.rejected)} rejected elements:")
            for r in self.rejected:
                print(f"  REJECTED: {r}")

        lines = []
        lines.append("** ==========================================================")
        lines.append("** Job-2_UEL.inp: Mixed 3-Node/4-Node Layered Phase-Field Deck")
        lines.append("** ==========================================================")
        lines.append("*Heading")
        lines.append(" Mixed Element UEL Model")

        # 1. User Element Declarations
        lines.append("** User Element Cards")
        lines.append("*User Element, nodes=4, type=U11, properties=3, coordinates=2, VARIABLES=8")
        lines.append(" 3")
        lines.append("*User Element, nodes=4, type=U12, properties=4, coordinates=2, VARIABLES=56")
        lines.append(" 1, 2")
        lines.append("*User Element, nodes=3, type=U21, properties=3, coordinates=2, VARIABLES=8")
        lines.append(" 3")
        lines.append("*User Element, nodes=3, type=U22, properties=4, coordinates=2, VARIABLES=56")
        lines.append(" 1, 2")

        # 2. Nodes
        lines.append("*Node")
        for nid, (x, y) in sorted(self.nodes.items()):
            lines.append(f" {nid}, {x:.6f}, {y:.6f}")

        # 3. Layer 1: Quad Phase UEL (U11)
        if self.quad_elems:
            lines.append("*Element, type=U11, elset=Phase_Quad")
            for eid, nids in sorted(self.quad_elems.items()):
                lines.append(f" {eid}, " + ", ".join(str(n) for n in nids))

        # 4. Layer 2: Tri Phase UEL (U21)
        if self.tri_elems:
            lines.append("*Element, type=U21, elset=Phase_Tri")
            for eid, nids in sorted(self.tri_elems.items()):
                lines.append(f" {eid}, " + ", ".join(str(n) for n in nids))

        # 5. Layer 3: Quad Facsimile (CPE4)
        if self.quad_elems:
            lines.append("*Element, type=CPE4, elset=All_elem_quad")
            for eid, nids in sorted(self.quad_elems.items()):
                lines.append(f" {eid}, " + ", ".join(str(n) for n in nids))

        # 6. Layer 4: Tri Facsimile (CPE3)
        if self.tri_elems:
            lines.append("*Element, type=CPE3, elset=All_elem_tri")
            for eid, nids in sorted(self.tri_elems.items()):
                lines.append(f" {eid}, " + ", ".join(str(n) for n in nids))

        # Combine all facsimile elements into All_elem and umatelem
        lines.append("*Elset, elset=All_elem")
        if self.quad_elems:
            lines.append(" Phase_Quad")
        if self.tri_elems:
            lines.append(" Phase_Tri")
        lines.append("*Elset, elset=umatelem")
        if self.quad_elems:
            lines.append(" Phase_Quad")
        if self.tri_elems:
            lines.append(" Phase_Tri")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write("\n".join(lines) + "\n")

        return len(self.quad_elems), len(self.tri_elems), len(self.rejected)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: f42_deck_rebuilder.py <input_deck.inp> <output_uel_deck.inp>")
        sys.exit(1)
    rebuilder = MixedDeckRebuilder(sys.argv[1])
    rebuilder.parse()
    nq, nt, nr = rebuilder.build_mixed_uel_deck(sys.argv[2])
    print(f"Successfully rebuilt mixed UEL deck: {nq} Quads, {nt} Triangles, {nr} Rejected")
