#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mode-I Method C State Transfer Engine & Spatial Projection Prototype.

Implements topology-guarded, nonmatching state projection for the
Pandey-Kumar (2025) Mode-I phase-field fracture benchmark:
1. Parses donor and recipient Abaqus input decks (*.inp) with 3-layer co-located elements.
2. Identifies the crack seam discontinuity (y = 0.5, 0 <= x <= 0.5) and isolates upper
   and lower slit flanks so non-matching nodes/Gauss-points never cross-interpolate.
3. Projects primary nodal displacements (u_x: DOF 1, u_y: DOF 2) and phase-field (d: DOF 3)
   using bilinear/isoparametric shape functions with physical bounding [0, 1].
4. Projects integration-point history variables H (SVARS 9..12 for quads, 7..9 for tris)
   using the qualified HOST_NEAREST_GP operator with non-negativity bounding (H >= 0).
5. Assembles complete, runnable Abaqus continuation decks with:
   - *INITIAL CONDITIONS, TYPE=DISPLACEMENT (DOFs 1, 2, 3)
   - *INITIAL CONDITIONS, TYPE=SOLUTION (SVARS 1..18)
   - Wrapped N_BOTTOM cards (16-entry limit guard)
   - Seamless Step-1 displacement continuation ramping from u_handoff to u_final.
"""

import os
import sys
import math
import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Set, Any


class Mode1Mesh:
    """Represents a 2D planar finite element mesh for the Mode-I benchmark."""

    def __init__(self, name: str = "Mode1Mesh"):
        self.name = name
        self.nodes: Dict[int, Tuple[float, float]] = {}  # nid -> (x, y)
        self.elements_u1: Dict[int, List[int]] = {}      # Layer 1 Phase UEL: eid -> [n1..n4]
        self.elements_u2: Dict[int, List[int]] = {}      # Layer 2 Mech UEL: eid -> [n1..n4]
        self.elements_cpe: Dict[int, List[int]] = {}     # Layer 3 Companion: eid -> [n1..n4]
        self.n_bottom: List[int] = []                    # Nodes on y = 0
        self.n_top: List[int] = []                       # Nodes on y = 1
        self.rp_node_id: int = 999999                    # Reference point node ID
        self.rp_coords: Tuple[float, float] = (0.5, 1.0)
        self.node_to_elements: Dict[int, List[int]] = {} # Node connectivity
        self.element_centroids: Dict[int, Tuple[float, float]] = {}
        self.element_flank: Dict[int, str] = {}          # 'UPPER' or 'LOWER'
        self.node_flank: Dict[int, str] = {}             # 'UPPER', 'LOWER', or 'LIGAMENT'

    @property
    def num_nodes(self) -> int:
        return len(self.nodes)

    @property
    def num_elements(self) -> int:
        return len(self.elements_u1)

    def classify_topology(self, seam_y: float = 0.5, seam_x_max: float = 0.5, tol: float = 1e-6):
        """
        Classifies elements and nodes relative to the zero-gap crack slit:
        - Slit: y = 0.5 mm for x in [0.0, 0.5] mm.
        - Elements with centroid y > 0.5 are UPPER.
        - Elements with centroid y < 0.5 are LOWER.
        - Nodes with x > 0.5 are in intact LIGAMENT (continuous across y = 0.5).
        - Nodes with x <= 0.5 are UPPER or LOWER based on connected elements.
        """
        # 1. Element classification
        for eid, conn in self.elements_u1.items():
            coords = [self.nodes[n] for n in conn]
            cx = sum(c[0] for c in coords) / float(len(coords))
            cy = sum(c[1] for c in coords) / float(len(coords))
            self.element_centroids[eid] = (cx, cy)
            if cy >= seam_y - tol:
                self.element_flank[eid] = "UPPER"
            else:
                self.element_flank[eid] = "LOWER"

        # 2. Build node-to-element connectivity
        self.node_to_elements = {nid: [] for nid in self.nodes}
        for eid, conn in self.elements_u1.items():
            for nid in conn:
                self.node_to_elements[nid].append(eid)

        # 3. Node classification
        for nid, (x, y) in self.nodes.items():
            if x > seam_x_max + tol:
                self.node_flank[nid] = "LIGAMENT"
            else:
                # Along slit x <= 0.5: classify based on connected elements
                conn_elems = self.node_to_elements.get(nid, [])
                flanks = set(self.element_flank[e] for e in conn_elems)
                if "UPPER" in flanks and "LOWER" not in flanks:
                    self.node_flank[nid] = "UPPER"
                elif "LOWER" in flanks and "UPPER" not in flanks:
                    self.node_flank[nid] = "LOWER"
                elif y > seam_y:
                    self.node_flank[nid] = "UPPER"
                elif y < seam_y:
                    self.node_flank[nid] = "LOWER"
                else:
                    # Node at crack tip (x approx 0.5, y approx 0.5) shared by both flanks
                    self.node_flank[nid] = "LIGAMENT"


class Mode1SpatialIndex:
    """Accelerated spatial bounding-box hash for topology-guarded host element lookup."""

    def __init__(self, mesh: Mode1Mesh, grid_size: int = 50):
        self.mesh = mesh
        self.grid_size = grid_size
        self.upper_buckets: Dict[Tuple[int, int], List[int]] = {}
        self.lower_buckets: Dict[Tuple[int, int], List[int]] = {}
        self.elem_bboxes: Dict[int, Tuple[float, float, float, float]] = {}
        self._build_index()

    def _build_index(self):
        for eid, conn in self.mesh.elements_u1.items():
            coords = [self.mesh.nodes[n] for n in conn]
            min_x = min(c[0] for c in coords)
            max_x = max(c[0] for c in coords)
            min_y = min(c[1] for c in coords)
            max_y = max(c[1] for c in coords)
            self.elem_bboxes[eid] = (min_x, max_x, min_y, max_y)

            # Determine grid buckets covering the bounding box
            flank = self.mesh.element_flank[eid]
            bucket_dict = self.upper_buckets if flank == "UPPER" else self.lower_buckets

            i_min = max(0, min(self.grid_size - 1, int(min_x * self.grid_size)))
            i_max = max(0, min(self.grid_size - 1, int(max_x * self.grid_size)))
            j_min = max(0, min(self.grid_size - 1, int(min_y * self.grid_size)))
            j_max = max(0, min(self.grid_size - 1, int(max_y * self.grid_size)))

            for i in range(i_min, i_max + 1):
                for j in range(j_min, j_max + 1):
                    key = (i, j)
                    if key not in bucket_dict:
                        bucket_dict[key] = []
                    bucket_dict[key].append(eid)

    def find_host_element(self, x: float, y: float, flank: str, tol: float = 1e-5) -> Tuple[int, float, float]:
        """
        Finds containing host element in the specified flank partition.
        Returns: (element_id, xi, eta) where xi, eta in [-1, 1].
        """
        # Determine which bucket dictionary to search
        if flank == "UPPER":
            target_dicts = [self.upper_buckets]
        elif flank == "LOWER":
            target_dicts = [self.lower_buckets]
        else:  # LIGAMENT: can search both
            target_dicts = [self.upper_buckets, self.lower_buckets]

        i = max(0, min(self.grid_size - 1, int(x * self.grid_size)))
        j = max(0, min(self.grid_size - 1, int(y * self.grid_size)))

        # Candidate element set
        candidates: Set[int] = set()
        # Search surrounding cells for safety
        for di in [-1, 0, 1]:
            for dj in [-1, 0, 1]:
                ci, cj = i + di, j + dj
                if 0 <= ci < self.grid_size and 0 <= cj < self.grid_size:
                    for bdict in target_dicts:
                        candidates.update(bdict.get((ci, cj), []))

        # Test containment via inverse isoparametric mapping
        best_eid = -1
        best_xi, best_eta = 0.0, 0.0
        best_residual = 1e9

        for eid in candidates:
            min_x, max_x, min_y, max_y = self.elem_bboxes[eid]
            if min_x - tol <= x <= max_x + tol and min_y - tol <= y <= max_y + tol:
                conn = self.mesh.elements_u1[eid]
                coords = [self.mesh.nodes[n] for n in conn]
                xi, eta, res = self._inverse_map_quad(coords, x, y)
                if abs(xi) <= 1.0 + tol and abs(eta) <= 1.0 + tol:
                    return eid, max(-1.0, min(1.0, xi)), max(-1.0, min(1.0, eta))
                if res < best_residual:
                    best_residual = res
                    best_eid = eid
                    best_xi, best_eta = xi, eta

        # Fallback: closest candidate in the requested flank
        if best_eid != -1:
            return best_eid, max(-1.0, min(1.0, best_xi)), max(-1.0, min(1.0, best_eta))

        # Global fallback within flank
        flank_elems = [e for e, f in self.mesh.element_flank.items() if flank == "LIGAMENT" or f == flank]
        best_eid = min(flank_elems, key=lambda e: (self.mesh.element_centroids[e][0] - x)**2 + (self.mesh.element_centroids[e][1] - y)**2)
        conn = self.mesh.elements_u1[best_eid]
        coords = [self.mesh.nodes[n] for n in conn]
        xi, eta, _ = self._inverse_map_quad(coords, x, y)
        return best_eid, max(-1.0, min(1.0, xi)), max(-1.0, min(1.0, eta))

    @staticmethod
    def _inverse_map_quad(coords: List[Tuple[float, float]], x: float, y: float, max_iter: int = 10, tol: float = 1e-12) -> Tuple[float, float, float]:
        """Newton-Raphson inverse isoparametric mapping for a 4-node quad."""
        # Initial guess: element center
        xi, eta = 0.0, 0.0
        for _ in range(max_iter):
            n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
            n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
            n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
            n4 = 0.25 * (1.0 - xi) * (1.0 + eta)

            fx = n1 * coords[0][0] + n2 * coords[1][0] + n3 * coords[2][0] + n4 * coords[3][0] - x
            fy = n1 * coords[0][1] + n2 * coords[1][1] + n3 * coords[2][1] + n4 * coords[3][1] - y

            res = fx * fx + fy * fy
            if res < tol * tol:
                break

            dn1_dxi  = -0.25 * (1.0 - eta); dn1_deta = -0.25 * (1.0 - xi)
            dn2_dxi  =  0.25 * (1.0 - eta); dn2_deta = -0.25 * (1.0 + xi)
            dn3_dxi  =  0.25 * (1.0 + eta); dn3_deta =  0.25 * (1.0 + xi)
            dn4_dxi  = -0.25 * (1.0 + eta); dn4_deta =  0.25 * (1.0 - xi)

            j11 = dn1_dxi * coords[0][0] + dn2_dxi * coords[1][0] + dn3_dxi * coords[2][0] + dn4_dxi * coords[3][0]
            j12 = dn1_deta * coords[0][0] + dn2_deta * coords[1][0] + dn3_deta * coords[2][0] + dn4_deta * coords[3][0]
            j21 = dn1_dxi * coords[0][1] + dn2_dxi * coords[1][1] + dn3_dxi * coords[2][1] + dn4_dxi * coords[3][1]
            j22 = dn1_deta * coords[0][1] + dn2_deta * coords[1][1] + dn3_deta * coords[2][1] + dn4_deta * coords[3][1]

            detJ = j11 * j22 - j12 * j21
            if abs(detJ) < 1e-15:
                break

            dxi  = -(j22 * fx - j12 * fy) / detJ
            deta = -(-j21 * fx + j11 * fy) / detJ

            xi  += dxi
            eta += deta

        res_final = math.sqrt(max(0.0, (xi - max(-1.0, min(1.0, xi)))**2 + (eta - max(-1.0, min(1.0, eta)))**2))
        return xi, eta, res_final


class Mode1State:
    """Holds field data on a mesh: displacements, phase-field, and history."""

    def __init__(self):
        self.u_nodal: Dict[int, Tuple[float, float]] = {}  # nid -> (ux, uy)
        self.d_nodal: Dict[int, float] = {}                # nid -> d in [0, 1]
        self.H_gp: Dict[int, List[float]] = {}             # eid -> list of 4 H values (quads) or 3 (tris)
        self.u_rp: Tuple[float, float] = (0.0, 0.0)        # RP displacement (ux, uy)


def parse_mode1_input_deck(inp_path: str) -> Mode1Mesh:
    """Parses an Abaqus input deck for Mode-I and extracts 3-layer mesh structure."""
    if not os.path.exists(inp_path):
        raise FileNotFoundError("Input deck not found: %s" % inp_path)

    mesh = Mode1Mesh(name=os.path.basename(inp_path))

    with open(inp_path, "r", encoding="utf-8") as f:
        reading_nodes = False
        reading_elem = False
        reading_nset = False
        elem_layer = None
        active_nset = None

        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("**"):
                continue

            if line.startswith("*"):
                upper_line = line.upper()
                reading_nodes = False
                reading_elem = False
                reading_nset = False

                if "*NODE" in upper_line and "*OUTPUT" not in upper_line and "*PRINT" not in upper_line:
                    reading_nodes = True
                elif "*ELEMENT" in upper_line:
                    reading_elem = True
                    if "TYPE=U1" in upper_line or "TYPE=U3" in upper_line:
                        elem_layer = "U1"
                    elif "TYPE=U2" in upper_line or "TYPE=U4" in upper_line:
                        elem_layer = "U2"
                    elif "TYPE=CPE4" in upper_line or "TYPE=CPE3" in upper_line:
                        elem_layer = "CPE"
                    else:
                        elem_layer = "OTHER"
                elif "*NSET" in upper_line:
                    reading_nset = True
                    if "NSET=N_BOTTOM" in upper_line:
                        active_nset = "N_BOTTOM"
                    elif "NSET=N_TOP" in upper_line:
                        active_nset = "N_TOP"
                    elif "NSET=N_RP" in upper_line or "NSET=RP" in upper_line:
                        active_nset = "N_RP"
                    else:
                        active_nset = "OTHER"
                continue

            # Parse node lines: id, x, y
            if reading_nodes:
                parts = [p.strip() for p in line.split(",") if p.strip()]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        if nid == 999999 or nid == 99999:
                            mesh.rp_node_id = nid
                            mesh.rp_coords = (x, y)
                        else:
                            mesh.nodes[nid] = (x, y)
                    except ValueError:
                        pass

            # Parse element lines: id, n1, n2, n3, n4 (or n1..n3)
            elif reading_elem and elem_layer in ["U1", "U2", "CPE"]:
                parts = [p.strip() for p in line.split(",") if p.strip()]
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        conn = [int(p) for p in parts[1:]]
                        if elem_layer == "U1":
                            mesh.elements_u1[eid] = conn
                        elif elem_layer == "U2":
                            mesh.elements_u2[eid] = conn
                        elif elem_layer == "CPE":
                            mesh.elements_cpe[eid] = conn
                    except ValueError:
                        pass

            # Parse nset lines: list of node IDs
            elif reading_nset and active_nset in ["N_BOTTOM", "N_TOP", "N_RP"]:
                parts = [p.strip() for p in line.split(",") if p.strip()]
                for p in parts:
                    try:
                        nid = int(p)
                        if active_nset == "N_BOTTOM":
                            mesh.n_bottom.append(nid)
                        elif active_nset == "N_TOP":
                            mesh.n_top.append(nid)
                        elif active_nset == "N_RP":
                            mesh.rp_node_id = nid
                    except ValueError:
                        pass

    # Classify mesh topology and slit flanks
    mesh.classify_topology()
    return mesh


def compute_quad_gauss_points(coords: List[Tuple[float, float]]) -> List[Tuple[float, float, float]]:
    """
    Computes 2x2 Gauss integration points for a 4-node quadrilateral.
    Returns: list of 4 tuples (gx, gy, detJ * weight).
    """
    g_pt = 1.0 / math.sqrt(3.0)
    local_gps = [
        (-g_pt, -g_pt),
        ( g_pt, -g_pt),
        ( g_pt,  g_pt),
        (-g_pt,  g_pt),
    ]
    results = []
    for xi, eta in local_gps:
        n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
        n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
        n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
        n4 = 0.25 * (1.0 - xi) * (1.0 + eta)

        gx = n1 * coords[0][0] + n2 * coords[1][0] + n3 * coords[2][0] + n4 * coords[3][0]
        gy = n1 * coords[0][1] + n2 * coords[1][1] + n3 * coords[2][1] + n4 * coords[3][1]

        dn1_dxi  = -0.25 * (1.0 - eta); dn1_deta = -0.25 * (1.0 - xi)
        dn2_dxi  =  0.25 * (1.0 - eta); dn2_deta = -0.25 * (1.0 + xi)
        dn3_dxi  =  0.25 * (1.0 + eta); dn3_deta =  0.25 * (1.0 + xi)
        dn4_dxi  = -0.25 * (1.0 + eta); dn4_deta =  0.25 * (1.0 - xi)

        j11 = dn1_dxi * coords[0][0] + dn2_dxi * coords[1][0] + dn3_dxi * coords[2][0] + dn4_dxi * coords[3][0]
        j12 = dn1_deta * coords[0][0] + dn2_deta * coords[1][0] + dn3_deta * coords[2][0] + dn4_deta * coords[3][0]
        j21 = dn1_dxi * coords[0][1] + dn2_dxi * coords[1][1] + dn3_dxi * coords[2][1] + dn4_dxi * coords[3][1]
        j22 = dn1_deta * coords[0][1] + dn2_deta * coords[1][1] + dn3_deta * coords[2][1] + dn4_deta * coords[3][1]

        detJ = j11 * j22 - j12 * j21
        results.append((gx, gy, abs(detJ)))
    return results


class Mode1StateTransferEngine:
    """
    Main projection engine that maps state from donor Mode1Mesh to recipient Mode1Mesh.
    """

    def __init__(self, donor_mesh: Mode1Mesh):
        self.donor_mesh = donor_mesh
        self.spatial_index = Mode1SpatialIndex(donor_mesh)

        # Precompute donor element Gauss points
        self.donor_gps: Dict[int, List[Tuple[float, float, float]]] = {}
        for eid, conn in self.donor_mesh.elements_u1.items():
            coords = [self.donor_mesh.nodes[n] for n in conn]
            if len(coords) == 4:
                self.donor_gps[eid] = compute_quad_gauss_points(coords)
            else:
                # 3-node tri: centroid
                cx = sum(c[0] for c in coords) / 3.0
                cy = sum(c[1] for c in coords) / 3.0
                area = 0.5 * abs((coords[1][0]-coords[0][0])*(coords[2][1]-coords[0][1]) - (coords[2][0]-coords[0][0])*(coords[1][1]-coords[0][1]))
                self.donor_gps[eid] = [(cx, cy, area)]

    def project_state(self, recipient_mesh: Mode1Mesh, donor_state: Mode1State) -> Mode1State:
        """
        Executes topology-guarded transfer of displacements, phase-field, and history.
        """
        target_state = Mode1State()
        target_state.u_rp = donor_state.u_rp

        # 1. Project primary nodal fields: (ux, uy, d)
        for nid, (tx, ty) in recipient_mesh.nodes.items():
            flank = recipient_mesh.node_flank.get(nid, "LIGAMENT")

            # Find host element in donor mesh respecting flank isolation
            host_eid, xi, eta = self.spatial_index.find_host_element(tx, ty, flank)
            conn = self.donor_mesh.elements_u1[host_eid]

            # Shape function weights
            if len(conn) == 4:
                n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
                n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
                n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
                n4 = 0.25 * (1.0 - xi) * (1.0 + eta)
                weights = [n1, n2, n3, n4]
            else:
                # Tri: area coordinates
                weights = [1.0/3.0, 1.0/3.0, 1.0/3.0]

            # Interpolate ux, uy
            ux_val = sum(w * donor_state.u_nodal[conn[a]][0] for a, w in enumerate(weights))
            uy_val = sum(w * donor_state.u_nodal[conn[a]][1] for a, w in enumerate(weights))

            # Interpolate phase field d
            d_val = sum(w * donor_state.d_nodal[conn[a]] for a, w in enumerate(weights))
            # Clamp strictly to physical damage bounds [0, 1]
            d_clamped = max(0.0, min(1.0, float(d_val)))

            # Preserve exact boundary constraints on recipient nodes:
            # Bottom roller: y = 0 -> uy = 0
            if abs(ty) < 1e-6:
                uy_val = 0.0
                if abs(tx) < 1e-6:  # Pinned node (0, 0) -> ux = 0
                    ux_val = 0.0

            target_state.u_nodal[nid] = (ux_val, uy_val)
            target_state.d_nodal[nid] = d_clamped

        # 2. Project integration-point history H via HOST_NEAREST_GP
        for eid, conn in recipient_mesh.elements_u1.items():
            coords = [recipient_mesh.nodes[n] for n in conn]
            flank = recipient_mesh.element_flank.get(eid, "UPPER")

            if len(coords) == 4:
                elem_gps = compute_quad_gauss_points(coords)
            else:
                cx = sum(c[0] for c in coords) / 3.0
                cy = sum(c[1] for c in coords) / 3.0
                elem_gps = [(cx, cy, 1.0)]

            transferred_H = []
            for gx, gy, _ in elem_gps:
                host_eid, _, _ = self.spatial_index.find_host_element(gx, gy, flank)
                donor_gp_list = self.donor_gps[host_eid]
                donor_H_list = donor_state.H_gp[host_eid]

                # Nearest donor GP in host element
                best_k = 0
                min_dist2 = 1e9
                for k, (dgx, dgy, _) in enumerate(donor_gp_list):
                    dist2 = (dgx - gx)**2 + (dgy - gy)**2
                    if dist2 < min_dist2:
                        min_dist2 = dist2
                        best_k = k

                h_val = max(0.0, float(donor_H_list[best_k]))
                transferred_H.append(h_val)

            target_state.H_gp[eid] = transferred_H

        return target_state

    def assemble_continuation_deck(
        self,
        recipient_mesh: Mode1Mesh,
        target_state: Mode1State,
        output_inp_path: str,
        u_handoff: float,
        u_final: float = 0.0100,
        num_increments: int = 5000,
        E_mod: float = 210.0,
        nu: float = 0.3,
        Gc: float = 2.7e-3,
        l0: float = 0.0075,
        k_stab: float = 1e-7,
    ) -> str:
        """
        Assembles a complete, runnable Abaqus input deck (.inp) embedding:
        - *INITIAL CONDITIONS, TYPE=DISPLACEMENT
        - *INITIAL CONDITIONS, TYPE=SOLUTION
        - Wrapped N_BOTTOM cards (avoiding 16-entry limit)
        - Step-1 continuation ramping from u_handoff to u_final.
        """
        n_phys = recipient_mesh.num_elements
        n_nodes = recipient_mesh.num_nodes

        lines = []
        lines.append("*HEADING")
        lines.append("MODE1_METHOD_C_RESTART - Sequential Adaptive Continuation Solve")
        lines.append("** Generated by Mode1StateTransferEngine")
        lines.append("** Handoff Displacement: %.6e mm | Target: %.6e mm" % (u_handoff, u_final))
        lines.append("** Physical Mesh: %d elements, %d nodes" % (n_phys, n_nodes))
        lines.append("**")
        lines.append("*PREPRINT, ECHO=NO, MODEL=NO, HISTORY=NO, CONTACT=NO")

        # 1. User Element Type Definitions
        lines.append("** ==========================================================")
        lines.append("** LAYER 1: PHASE-FIELD UEL (U1: Quad, U3: Tri, DOF 3)")
        lines.append("** ==========================================================")
        lines.append("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=6, VARIABLES=18, UNSYMM")
        lines.append("3")
        lines.append("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, I PROPERTIES=0, PROPERTIES=6, VARIABLES=18, UNSYMM")
        lines.append("3")
        lines.append("** ==========================================================")
        lines.append("** LAYER 2: MECHANICAL UEL (U2: Quad, U4: Tri, DOFs 1, 2)")
        lines.append("** ==========================================================")
        lines.append("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=6, VARIABLES=18, UNSYMM")
        lines.append("1, 2")
        lines.append("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, I PROPERTIES=0, PROPERTIES=6, VARIABLES=18, UNSYMM")
        lines.append("1, 2")

        # 2. Nodes
        lines.append("** ==========================================================")
        lines.append("** NODES")
        lines.append("** ==========================================================")
        lines.append("*NODE")
        for nid, (x, y) in sorted(recipient_mesh.nodes.items()):
            lines.append("%8d, %16.10e, %16.10e" % (nid, x, y))
        lines.append("%8d, %16.10e, %16.10e" % (recipient_mesh.rp_node_id, recipient_mesh.rp_coords[0], recipient_mesh.rp_coords[1]))

        # 3. Elements Layer 1 (U1/U3)
        lines.append("** ==========================================================")
        lines.append("** LAYER 1: PHASE UEL ELEMENTS (1..N_PHYS)")
        lines.append("** ==========================================================")
        quad_eids = [e for e, c in recipient_mesh.elements_u1.items() if len(c) == 4]
        tri_eids  = [e for e, c in recipient_mesh.elements_u1.items() if len(c) == 3]

        if quad_eids:
            lines.append("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD")
            for eid in sorted(quad_eids):
                c = recipient_mesh.elements_u1[eid]
                lines.append("%8d, %8d, %8d, %8d, %8d" % (eid, c[0], c[1], c[2], c[3]))
        if tri_eids:
            lines.append("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI")
            for eid in sorted(tri_eids):
                c = recipient_mesh.elements_u1[eid]
                lines.append("%8d, %8d, %8d, %8d" % (eid, c[0], c[1], c[2]))

        # 4. Elements Layer 2 (U2/U4)
        lines.append("** ==========================================================")
        lines.append("** LAYER 2: MECHANICAL UEL ELEMENTS (N_PHYS+1..2*N_PHYS)")
        lines.append("** ==========================================================")
        if quad_eids:
            lines.append("*ELEMENT, TYPE=U2, ELSET=MECH_QUAD")
            for eid in sorted(quad_eids):
                c = recipient_mesh.elements_u1[eid]
                lines.append("%8d, %8d, %8d, %8d, %8d" % (eid + n_phys, c[0], c[1], c[2], c[3]))
        if tri_eids:
            lines.append("*ELEMENT, TYPE=U4, ELSET=MECH_TRI")
            for eid in sorted(tri_eids):
                c = recipient_mesh.elements_u1[eid]
                lines.append("%8d, %8d, %8d, %8d" % (eid + n_phys, c[0], c[1], c[2]))

        # 5. Elements Layer 3 (CPE4/CPE3 Companion)
        lines.append("** ==========================================================")
        lines.append("** LAYER 3: COMPANION FACSIMILE (2*N_PHYS+1..3*N_PHYS)")
        lines.append("** ==========================================================")
        if quad_eids:
            lines.append("*ELEMENT, TYPE=CPE4, ELSET=All_elem_quad")
            for eid in sorted(quad_eids):
                c = recipient_mesh.elements_u1[eid]
                lines.append("%8d, %8d, %8d, %8d, %8d" % (eid + 2 * n_phys, c[0], c[1], c[2], c[3]))
        if tri_eids:
            lines.append("*ELEMENT, TYPE=CPE3, ELSET=All_elem_tri")
            for eid in sorted(tri_eids):
                c = recipient_mesh.elements_u1[eid]
                lines.append("%8d, %8d, %8d, %8d" % (eid + 2 * n_phys, c[0], c[1], c[2]))

        # Composite Element Sets
        lines.append("*ELSET, ELSET=All_elem")
        if quad_eids and tri_eids:
            lines.append("All_elem_quad, All_elem_tri")
        elif quad_eids:
            lines.append("All_elem_quad")
        else:
            lines.append("All_elem_tri")

        # 6. Node Sets: N_BOTTOM, N_TOP, N_RP
        lines.append("** ==========================================================")
        lines.append("** NODE SETS (SAFELY WRAPPED ACROSS VALID DATA LINES)")
        lines.append("** ==========================================================")
        # N_BOTTOM wrapped
        lines.append("*NSET, NSET=N_BOTTOM")
        for chunk in [recipient_mesh.n_bottom[i:i+16] for i in range(0, len(recipient_mesh.n_bottom), 16)]:
            lines.append(", ".join(str(n) for n in chunk))

        # N_TOP wrapped
        lines.append("*NSET, NSET=N_TOP")
        for chunk in [recipient_mesh.n_top[i:i+16] for i in range(0, len(recipient_mesh.n_top), 16)]:
            lines.append(", ".join(str(n) for n in chunk))

        # N_RP
        lines.append("*NSET, NSET=N_RP")
        lines.append("%d" % recipient_mesh.rp_node_id)

        # 7. Rigid Kinematic Coupling: N_TOP tied to RP 999999
        lines.append("** ==========================================================")
        lines.append("** RIGID LINEAR COUPLING ON N_TOP")
        lines.append("** ==========================================================")
        lines.append("*EQUATION")
        lines.append("2")
        lines.append("N_TOP, 2, 1.0, N_RP, 2, -1.0")

        # 8. UEL Properties & Materials
        lines.append("** ==========================================================")
        lines.append("** UEL PROPERTIES & COMPANION MATERIAL")
        lines.append("** ==========================================================")
        # Properties: E, nu, Gc, l0, k, thickness
        uel_prop_str = "%.10e, %.10e, %.10e, %.10e, %.10e, 1.0" % (E_mod, nu, Gc, l0, k_stab)
        if quad_eids:
            lines.append("*UEL PROPERTY, ELSET=PHASE_QUAD")
            lines.append(uel_prop_str)
            lines.append("*UEL PROPERTY, ELSET=MECH_QUAD")
            lines.append(uel_prop_str)
        if tri_eids:
            lines.append("*UEL PROPERTY, ELSET=PHASE_TRI")
            lines.append(uel_prop_str)
            lines.append("*UEL PROPERTY, ELSET=MECH_TRI")
            lines.append(uel_prop_str)

        lines.append("*SOLID SECTION, ELSET=All_elem, MATERIAL=COMPANION_MAT")
        lines.append("1.0")
        lines.append("*MATERIAL, NAME=COMPANION_MAT")
        lines.append("*USER MATERIAL, CONSTANTS=1")
        lines.append("1.0e-11")  # Infinitesimal non-invasive tangent E_dummy
        lines.append("*DEPVAR")
        lines.append("18")

        # 9. INITIAL CONDITIONS: TYPE=DISPLACEMENT
        lines.append("** ==========================================================")
        lines.append("** INITIAL CONDITIONS: TYPE=DISPLACEMENT (DOFs 1, 2, 3)")
        lines.append("** ==========================================================")
        lines.append("*INITIAL CONDITIONS, TYPE=DISPLACEMENT")
        for nid in sorted(recipient_mesh.nodes.keys()):
            ux, uy = target_state.u_nodal[nid]
            d_val = target_state.d_nodal[nid]
            lines.append("%8d, 1, 1, %16.10e" % (nid, ux))
            lines.append("%8d, 2, 2, %16.10e" % (nid, uy))
            lines.append("%8d, 3, 3, %16.10e" % (nid, d_val))
        # RP initial displacement
        lines.append("%8d, 1, 1, 0.0" % recipient_mesh.rp_node_id)
        lines.append("%8d, 2, 2, %16.10e" % (recipient_mesh.rp_node_id, u_handoff))

        # 10. INITIAL CONDITIONS: TYPE=SOLUTION (History SVARS 9..12)
        lines.append("** ==========================================================")
        lines.append("** INITIAL CONDITIONS: TYPE=SOLUTION (SVARS 1..18 for UEL)")
        lines.append("** ==========================================================")
        lines.append("*INITIAL CONDITIONS, TYPE=SOLUTION")
        for eid in sorted(recipient_mesh.elements_u1.keys()):
            conn = recipient_mesh.elements_u1[eid]
            h_vals = target_state.H_gp[eid]
            d_avg = sum(target_state.d_nodal[n] for n in conn) / float(len(conn))
            deg = (1.0 - d_avg)**2 + k_stab

            if len(conn) == 4:
                # 4-node quad: 4 Gauss points
                h1, h2, h3, h4 = h_vals[0], h_vals[1], h_vals[2], h_vals[3]
                # SVARS:
                # 1..4: d at GPs (approx d_avg)
                # 5..8: H at GPs
                # 9..12: SV_H_COMMITTED at GPs (critical for UEL lines 252-253!)
                # 13..14: d_avg
                # 15: deg
                # 16: H(1)
                # 17..18: energy (0.0)
                sv = [
                    d_avg, d_avg, d_avg, d_avg,
                    h1, h2, h3, h4,
                    h1, h2, h3, h4,
                    d_avg, d_avg, deg, h1, 0.0, 0.0
                ]
            else:
                # 3-node tri: 3 Gauss points
                h1, h2, h3 = h_vals[0], h_vals[1], h_vals[2]
                sv = [
                    d_avg, d_avg, d_avg, 0.0,
                    h1, h2, h3, 0.0,
                    h1, h2, h3, 0.0,
                    d_avg, d_avg, deg, h1, 0.0, 0.0
                ]

            # Format 18 SVAR values across lines (8 per line)
            lines.append("%8d, " % eid + ", ".join("%14.7e" % v for v in sv[:8]))
            lines.append("  " + ", ".join("%14.7e" % v for v in sv[8:16]))
            lines.append("  " + ", ".join("%14.7e" % v for v in sv[16:]))

        # 11. STEP 1: CONTINUATION SOLVE
        lines.append("** ==========================================================")
        lines.append("** STEP 1: NONLINEAR STATIC CONTINUATION SOLVE")
        lines.append("** ==========================================================")
        dt_init = 1.0 / float(num_increments)
        lines.append("*STEP, NAME=Step-1, NLGEOM=YES, INC=%d" % (num_increments * 2))
        lines.append("*STATIC")
        lines.append("%.8e, 1.0, 1.0e-12, %.8e" % (dt_init, dt_init))

        lines.append("** Boundary conditions:")
        lines.append("*BOUNDARY")
        lines.append("N_BOTTOM, 2, 2, 0.0")
        lines.append("1, 1, 1, 0.0")  # Pin origin node
        # Ramp RP from u_handoff to u_final
        lines.append("N_RP, 2, 2, %.10e" % u_final)

        lines.append("*RESTART, WRITE, FREQUENCY=0")
        lines.append("*OUTPUT, FIELD, FREQUENCY=10")
        lines.append("*NODE OUTPUT, NSET=N_RP")
        lines.append("U, RF")
        lines.append("*ELEMENT OUTPUT, ELSET=All_elem")
        lines.append("SDV")
        lines.append("*NODE PRINT, FREQ=1, NSET=N_RP")
        lines.append("U2, RF2")
        lines.append("*END STEP")

        # Write deck
        deck_content = "\n".join(lines) + "\n"
        ensure_dir = os.path.dirname(output_inp_path)
        if ensure_dir and not os.path.exists(ensure_dir):
            os.makedirs(ensure_dir)

        with open(output_inp_path, "w", encoding="utf-8") as fp:
            fp.write(deck_content)

        return output_inp_path
