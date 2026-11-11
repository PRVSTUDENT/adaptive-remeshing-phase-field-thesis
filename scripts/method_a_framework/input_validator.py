# -*- coding: utf-8 -*-
"""
scripts/method_a_framework/input_validator.py
=============================================
Input validation and geometry/topology parsing for the Reusable Method A Framework.

Validates that coarse input decks contain supported 2D continuum topologies,
checks boundary condition node sets, verifies positive Jacobians, and extracts
geometric features without hardcoded geometry priors.
"""

import os
import re
import math


SUPPORTED_2D_ELEMENTS = {
    "CPE4": 4, "CPE4R": 4, "CPS4": 4, "CPS4R": 4,
    "CPE3": 3, "CPS3": 3,
    "U1": 4, "U2": 4, "U3": 3, "U4": 3
}

UNSUPPORTED_ELEMENTS = [
    "C3D8", "C3D8R", "C3D4", "C3D10", "C3D20",
    "B21", "B31", "T2D2", "T3D2", "S4R", "S3"
]


class InputModelValidator(object):
    """
    Validates and extracts geometric, topological, and boundary condition data
    from an Abaqus .inp file.
    """

    def __init__(self, inp_path):
        if not os.path.isfile(inp_path):
            raise IOError("Input deck not found: %s" % inp_path)
        self.inp_path = inp_path
        self.nodes = {}        # nid -> (x, y)
        self.elements = {}     # eid -> {"type": ..., "nodes": [...]}
        self.nsets = {}        # set_name -> [nid, ...]
        self.elsets = {}       # set_name -> [eid, ...]
        self.quad_count = 0
        self.tri_count = 0
        self.bbox = [0.0, 0.0, 0.0, 0.0]  # [xmin, xmax, ymin, ymax]

    def parse(self):
        """
        Parses nodes, elements, and sets from the input deck.
        """
        with open(self.inp_path, "r") as f:
            lines = f.readlines()

        current_section = None
        current_elem_type = None
        current_set_name = None

        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.startswith("**"):
                continue

            if line_str.startswith("*"):
                upper_line = line_str.upper()
                if upper_line.startswith("*NODE"):
                    current_section = "NODE"
                    continue
                elif upper_line.startswith("*ELEMENT"):
                    current_section = "ELEMENT"
                    type_match = re.search(r"TYPE=([A-Za-z0-9]+)", upper_line)
                    current_elem_type = type_match.group(1) if type_match else "UNKNOWN"
                    # Check for unsupported 3D or 1D elements
                    for unsup in UNSUPPORTED_ELEMENTS:
                        if current_elem_type.startswith(unsup):
                            raise ValueError(
                                "Unsupported element type '%s' in deck. Method A only supports 2D planar elements."
                                % current_elem_type
                            )
                    continue
                elif upper_line.startswith("*NSET"):
                    current_section = "NSET"
                    set_match = re.search(r"NSET=([A-Za-z0-9_\-]+)", line_str, re.IGNORECASE)
                    current_set_name = set_match.group(1) if set_match else "UNKNOWN"
                    if current_set_name not in self.nsets:
                        self.nsets[current_set_name] = []
                    continue
                elif upper_line.startswith("*ELSET"):
                    current_section = "ELSET"
                    set_match = re.search(r"ELSET=([A-Za-z0-9_\-]+)", line_str, re.IGNORECASE)
                    current_set_name = set_match.group(1) if set_match else "UNKNOWN"
                    if current_set_name not in self.elsets:
                        self.elsets[current_set_name] = []
                    continue
                else:
                    current_section = "OTHER"
                    continue

            # Parse data lines
            if current_section == "NODE":
                parts = [p.strip() for p in line_str.split(",") if p.strip()]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        self.nodes[nid] = (x, y)
                    except ValueError:
                        pass

            elif current_section == "ELEMENT":
                parts = [p.strip() for p in line_str.split(",") if p.strip()]
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        enodes = [int(p) for p in parts[1:]]
                        self.elements[eid] = {
                            "type": current_elem_type,
                            "nodes": enodes
                        }
                        if len(enodes) == 4:
                            self.quad_count += 1
                        elif len(enodes) == 3:
                            self.tri_count += 1
                    except ValueError:
                        pass

            elif current_section == "NSET" and current_set_name:
                parts = [p.strip() for p in line_str.split(",") if p.strip()]
                for p in parts:
                    try:
                        self.nsets[current_set_name].append(int(p))
                    except ValueError:
                        pass

            elif current_section == "ELSET" and current_set_name:
                parts = [p.strip() for p in line_str.split(",") if p.strip()]
                for p in parts:
                    try:
                        self.elsets[current_set_name].append(int(p))
                    except ValueError:
                        pass

        # Compute bounding box
        if self.nodes:
            xs = [pt[0] for pt in self.nodes.values()]
            ys = [pt[1] for pt in self.nodes.values()]
            self.bbox = [min(xs), max(xs), min(ys), max(ys)]

        return self.get_summary()

    def audit_mesh_quality(self):
        """
        Audits Jacobian determinants and aspect ratios for all 2D elements.
        Returns dict with min/mean/max aspect ratio and Jacobian status.
        """
        aspect_ratios = []
        positive_jacobians = True
        inverted_elements = []

        for eid, edata in self.elements.items():
            enodes = edata["nodes"]
            coords = [self.nodes[nid] for nid in enodes if nid in self.nodes]
            if len(coords) < 3:
                continue

            if len(coords) == 3:
                # Triangle area / Jacobian determinant
                (x1, y1), (x2, y2), (x3, y3) = coords
                area = 0.5 * ((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1))
                if area <= 0.0:
                    positive_jacobians = False
                    inverted_elements.append(eid)
                # Aspect ratio
                d12 = math.hypot(x2 - x1, y2 - y1)
                d23 = math.hypot(x3 - x2, y3 - y2)
                d31 = math.hypot(x1 - x3, y1 - y3)
                max_side = max(d12, d23, d31)
                h_eff = (2.0 * area) / max_side if max_side > 0 else 1.0
                ar = max_side / h_eff if h_eff > 0 else 1.0
                aspect_ratios.append(ar)

            elif len(coords) == 4:
                # Quad element: check cross products at all 4 corners
                (x1, y1), (x2, y2), (x3, y3), (x4, y4) = coords
                det1 = (x2 - x1) * (y4 - y1) - (x4 - x1) * (y2 - y1)
                det2 = (x3 - x2) * (y1 - y2) - (x1 - x2) * (y3 - y2)
                det3 = (x4 - x3) * (y2 - y3) - (x2 - x3) * (y4 - y3)
                det4 = (x1 - x4) * (y3 - y4) - (x3 - x4) * (y1 - y4)
                if min(det1, det2, det3, det4) <= 0.0:
                    positive_jacobians = False
                    inverted_elements.append(eid)
                # Aspect ratio
                d12 = math.hypot(x2 - x1, y2 - y1)
                d23 = math.hypot(x3 - x2, y3 - y2)
                d34 = math.hypot(x4 - x3, y4 - y3)
                d41 = math.hypot(x1 - x4, y1 - y4)
                max_d = max(d12, d23, d34, d41)
                min_d = min(d12, d23, d34, d41)
                ar = max_d / min_d if min_d > 0 else 1.0
                aspect_ratios.append(ar)

        return {
            "all_jacobians_positive": positive_jacobians,
            "inverted_element_count": len(inverted_elements),
            "inverted_element_ids": inverted_elements[:10],
            "aspect_ratio_min": round(min(aspect_ratios), 3) if aspect_ratios else 0.0,
            "aspect_ratio_mean": round(sum(aspect_ratios) / len(aspect_ratios), 3) if aspect_ratios else 0.0,
            "aspect_ratio_max": round(max(aspect_ratios), 3) if aspect_ratios else 0.0
        }

    def get_summary(self):
        quality = self.audit_mesh_quality()
        return {
            "inp_path": self.inp_path,
            "node_count": len(self.nodes),
            "element_count": len(self.elements),
            "quad_count": self.quad_count,
            "tri_count": self.tri_count,
            "bbox": self.bbox,
            "nsets": list(self.nsets.keys()),
            "elsets": list(self.elsets.keys()),
            "quality": quality
        }
