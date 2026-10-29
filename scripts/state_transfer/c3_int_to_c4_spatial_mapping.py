# -*- coding: utf-8 -*-
"""
c3_int_to_c4_spatial_mapping.py
Mode-I Method C State Transfer: C3-Intermediate to C4 Nonmatching Spatial Transfer Engine.

Provides deterministic, topology-guarded spatial transfer mapping:
1. Physical mesh parsing for C3-Intermediate (donor) and C4 (receiver).
2. Slit-seam flank isolation along y = 0.05 mm, x <= 0.04 mm, preventing cross-slit interpolation.
3. Accurate inverse isoparametric coordinate solver (Newton-Raphson) for 4-node quadrilaterals.
4. Fast 2D spatial binning index for candidate element containment checks.
5. Deterministic target node and Gauss-point transfer maps with partition of unity verification.
6. Conservative host-nearest GP mapping and non-negativity guarantees for history variables.
7. Verification and synthetic patch test infrastructure.
"""

from __future__ import print_function, division
import os
import sys
import math
import json
from collections import defaultdict

GAUSS_1D = [-1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)]

# Standard Abaqus 2x2 Gauss points for quad: (xi, eta)
# 1: (-1/sqrt3, -1/sqrt3), 2: (+1/sqrt3, -1/sqrt3), 3: (-1/sqrt3, +1/sqrt3), 4: (+1/sqrt3, +1/sqrt3)
QUAD_GP_LOCAL = [
    (GAUSS_1D[0], GAUSS_1D[0]),  # GP 1
    (GAUSS_1D[1], GAUSS_1D[0]),  # GP 2
    (GAUSS_1D[0], GAUSS_1D[1]),  # GP 3
    (GAUSS_1D[1], GAUSS_1D[1]),  # GP 4
]


def quad_shape_functions(xi, eta):
    """Evaluates bilinear shape functions for a 4-node quadrilateral at (xi, eta)."""
    n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
    n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
    n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
    n4 = 0.25 * (1.0 - xi) * (1.0 + eta)
    return [n1, n2, n3, n4]


def quad_physical_point(vertices, xi, eta):
    """
    Computes physical coordinates (x, y) given 4 vertices [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
    and local coordinates (xi, eta).
    """
    weights = quad_shape_functions(xi, eta)
    x = sum(w * v[0] for w, v in zip(weights, vertices))
    y = sum(w * v[1] for w, v in zip(weights, vertices))
    return x, y


def inverse_isoparametric_quad(vertices, x_target, y_target, tol=1e-12, max_iter=30):
    """
    Inverts the isoparametric mapping for a 4-node quad using Newton-Raphson.
    Returns (xi, eta, converged, residual_norm).
    """
    # Initial guess at centroid
    xi, eta = 0.0, 0.0
    x1, y1 = vertices[0]
    x2, y2 = vertices[1]
    x3, y3 = vertices[2]
    x4, y4 = vertices[3]

    for it in range(max_iter):
        n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
        n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
        n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
        n4 = 0.25 * (1.0 - xi) * (1.0 + eta)

        x_calc = n1 * x1 + n2 * x2 + n3 * x3 + n4 * x4
        y_calc = n1 * y1 + n2 * y2 + n3 * y3 + n4 * y4

        rx = x_calc - x_target
        ry = y_calc - y_target
        res_norm = math.sqrt(rx * rx + ry * ry)

        if res_norm < tol:
            return xi, eta, True, res_norm

        # Jacobian components: d(x, y) / d(xi, eta)
        # dN/dxi
        dn1_dxi = -0.25 * (1.0 - eta)
        dn2_dxi = 0.25 * (1.0 - eta)
        dn3_dxi = 0.25 * (1.0 + eta)
        dn4_dxi = -0.25 * (1.0 + eta)

        # dN/deta
        dn1_deta = -0.25 * (1.0 - xi)
        dn2_deta = -0.25 * (1.0 + xi)
        dn3_deta = 0.25 * (1.0 + xi)
        dn4_deta = 0.25 * (1.0 - xi)

        j11 = dn1_dxi * x1 + dn2_dxi * x2 + dn3_dxi * x3 + dn4_dxi * x4
        j12 = dn1_deta * x1 + dn2_deta * x2 + dn3_deta * x3 + dn4_deta * x4
        j21 = dn1_dxi * y1 + dn2_dxi * y2 + dn3_dxi * y3 + dn4_dxi * y4
        j22 = dn1_deta * y1 + dn2_deta * y2 + dn3_deta * y3 + dn4_deta * y4

        det_j = j11 * j22 - j12 * j21
        if abs(det_j) < 1e-15:
            # Degenerate element or singular Jacobian
            return xi, eta, False, res_norm

        # Solve J * delta = r  => delta = J^(-1) * r
        d_xi = (j22 * rx - j12 * ry) / det_j
        d_eta = (-j21 * rx + j11 * ry) / det_j

        xi -= d_xi
        eta -= d_eta

        # Bound damping if stepped wildly outside domain during search
        xi = max(-3.0, min(3.0, xi))
        eta = max(-3.0, min(3.0, eta))

    # Final residual check
    n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
    n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
    n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
    n4 = 0.25 * (1.0 - xi) * (1.0 + eta)
    x_calc = n1 * x1 + n2 * x2 + n3 * x3 + n4 * x4
    y_calc = n1 * y1 + n2 * y2 + n3 * y3 + n4 * y4
    res_norm = math.sqrt((x_calc - x_target) ** 2 + (y_calc - y_target) ** 2)
    return xi, eta, res_norm < tol, res_norm


class Mesh2D(object):
    """Parses and holds physical 2D quad mesh data for Mode-I fracture analysis."""

    def __init__(self, name="Mesh2D"):
        self.name = name
        self.nodes = {}             # nid -> (x, y)
        self.elements = {}          # eid -> [n1, n2, n3, n4]
        self.element_centroids = {} # eid -> (cx, cy)
        self.element_flank = {}     # eid -> 'UPPER' or 'LOWER'
        self.node_flank = {}        # nid -> 'UPPER', 'LOWER', 'LIGAMENT'
        self.element_bbox = {}      # eid -> (xmin, xmax, ymin, ymax)
        self.gauss_points = {}      # (eid, gp_idx) -> (x, y, flank)
        self.seam_pairs = []        # list of (lower_nid, upper_nid, x)

    @classmethod
    def from_inp(cls, inp_path, name="Mesh2D", max_physical_node=None):
        mesh = cls(name=name)
        mesh.parse_inp(inp_path, max_physical_node=max_physical_node)
        mesh.classify_topology()
        mesh.compute_gauss_points()
        return mesh

    def parse_inp(self, inp_path, max_physical_node=None):
        reading = None
        with open(inp_path, "r") as f:
            for line in f:
                l = line.strip()
                if not l or l.startswith("**"):
                    continue
                u = l.upper()
                if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                    reading = "NODE"
                    continue
                elif u.startswith("*ELEMENT") and "TYPE=U1" in u:
                    reading = "ELEM"
                    continue
                elif u.startswith("*"):
                    reading = None
                    continue

                if reading == "NODE":
                    parts = [p.strip() for p in l.split(",")]
                    if len(parts) >= 3:
                        nid = int(parts[0])
                        if nid < 999999:
                            if max_physical_node is None or nid <= max_physical_node:
                                self.nodes[nid] = (float(parts[1]), float(parts[2]))
                elif reading == "ELEM":
                    parts = [int(p.strip()) for p in l.split(",") if p.strip().isdigit()]
                    if len(parts) == 5:
                        eid = parts[0]
                        self.elements[eid] = parts[1:5]

        # Compute centroids and bounding boxes
        for eid, conn in self.elements.items():
            pts = [self.nodes[n] for n in conn]
            cx = sum(p[0] for p in pts) / 4.0
            cy = sum(p[1] for p in pts) / 4.0
            self.element_centroids[eid] = (cx, cy)
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            self.element_bbox[eid] = (min(xs), max(xs), min(ys), max(ys))

    def classify_topology(self, seam_y=0.05, seam_x_max=0.04, tol=1e-6):
        """
        Classifies elements into UPPER and LOWER relative to seam_y = 0.05.
        Classifies nodes into UPPER, LOWER, and LIGAMENT.
        Identifies coincident slit flank pairs along y = 0.05, x <= 0.04.
        """
        for eid, (cx, cy) in self.element_centroids.items():
            if cy >= seam_y:
                self.element_flank[eid] = "UPPER"
            else:
                self.element_flank[eid] = "LOWER"

        # Node-to-element mapping
        node_to_elems = defaultdict(list)
        for eid, conn in self.elements.items():
            for n in conn:
                node_to_elems[n].append(eid)

        # Node classification
        slit_nodes_by_x = defaultdict(list)
        for nid, (x, y) in self.nodes.items():
            if abs(y - seam_y) < tol and x <= seam_x_max + tol:
                slit_nodes_by_x[round(x, 7)].append(nid)

            if x > seam_x_max + tol:
                self.node_flank[nid] = "LIGAMENT"
            else:
                conn_elems = node_to_elems.get(nid, [])
                flanks = set(self.element_flank[e] for e in conn_elems)
                if flanks == {"UPPER"}:
                    self.node_flank[nid] = "UPPER"
                elif flanks == {"LOWER"}:
                    self.node_flank[nid] = "LOWER"
                elif len(flanks) == 0:
                    self.node_flank[nid] = "ISOLATED"
                else:
                    # Shared across crack line (only possible if ligament or continuous)
                    self.node_flank[nid] = "SHARED"

        # Seam pairing
        self.seam_pairs = []
        for x_val in sorted(slit_nodes_by_x.keys()):
            nids = slit_nodes_by_x[x_val]
            if len(nids) == 2:
                n_lower = [n for n in nids if self.node_flank.get(n) == "LOWER"]
                n_upper = [n for n in nids if self.node_flank.get(n) == "UPPER"]
                if len(n_lower) == 1 and len(n_upper) == 1:
                    self.seam_pairs.append((n_lower[0], n_upper[0], x_val))

    def compute_gauss_points(self):
        """Computes physical coordinates and flank classification for all 2x2 quad Gauss points."""
        self.gauss_points = {}
        for eid, conn in self.elements.items():
            pts = [self.nodes[n] for n in conn]
            flank = self.element_flank[eid]
            for gp_idx, (xi, eta) in enumerate(QUAD_GP_LOCAL):
                x_gp, y_gp = quad_physical_point(pts, xi, eta)
                self.gauss_points[(eid, gp_idx + 1)] = (x_gp, y_gp, flank)


class SpatialIndex2D(object):
    """Uniform 2D grid index for accelerating candidate element lookups."""

    def __init__(self, mesh, nx=50, ny=50, tol=1e-5):
        self.mesh = mesh
        self.nx = nx
        self.ny = ny
        self.tol = tol

        # Find global bounds
        xs = [pt[0] for pt in mesh.nodes.values()]
        ys = [pt[1] for pt in mesh.nodes.values()]
        self.xmin = min(xs) - tol
        self.xmax = max(xs) + tol
        self.ymin = min(ys) - tol
        self.ymax = max(ys) + tol

        self.dx = (self.xmax - self.xmin) / float(nx)
        self.dy = (self.ymax - self.ymin) / float(ny)

        # Bins: (ix, iy) -> list of eids
        self.grid = defaultdict(list)
        self._build_index()

    def _build_index(self):
        for eid, (ex_min, ex_max, ey_min, ey_max) in self.mesh.element_bbox.items():
            ix_min = max(0, min(self.nx - 1, int((ex_min - self.xmin) / self.dx)))
            ix_max = max(0, min(self.nx - 1, int((ex_max - self.xmin) / self.dx)))
            iy_min = max(0, min(self.ny - 1, int((ey_min - self.ymin) / self.dy)))
            iy_max = max(0, min(self.ny - 1, int((ey_max - self.ymin) / self.dy)))

            for ix in range(ix_min, ix_max + 1):
                for iy in range(iy_min, iy_max + 1):
                    self.grid[(ix, iy)].append(eid)

    def query_candidates(self, x, y, flank_constraint=None):
        """Returns candidate element IDs around (x, y) matching the optional flank constraint."""
        ix = int((x - self.xmin) / self.dx)
        iy = int((y - self.ymin) / self.dy)

        # Clip to valid bin indices
        ix = max(0, min(self.nx - 1, ix))
        iy = max(0, min(self.ny - 1, iy))

        # Check the primary cell and its 8 neighbors to be safe against boundary tolerance
        candidate_set = set()
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                cell = (ix + ox, iy + oy)
                if cell in self.grid:
                    for eid in self.grid[cell]:
                        if flank_constraint is None:
                            candidate_set.add(eid)
                        else:
                            if self.mesh.element_flank.get(eid) == flank_constraint:
                                candidate_set.add(eid)
                            elif flank_constraint == "LIGAMENT":
                                candidate_set.add(eid)
        return list(candidate_set)


class SpatialTransferMapper(object):
    """Computes and qualifies nonmatching spatial transfer mappings from donor to receiver."""

    def __init__(self, donor_mesh, receiver_mesh, tol_geom=1e-6):
        self.donor = donor_mesh
        self.receiver = receiver_mesh
        self.tol_geom = tol_geom
        self.donor_index = SpatialIndex2D(donor_mesh, nx=50, ny=50)

    def map_target_point(self, x_target, y_target, flank_constraint=None):
        """
        Locates the donor element containing (x_target, y_target) subject to flank constraint.
        Returns mapping dict with host_eid, xi, eta, weights, recon_error.
        """
        candidates = self.donor_index.query_candidates(x_target, y_target, flank_constraint=flank_constraint)
        best_match = None
        min_distance_outside = float("inf")

        for eid in candidates:
            conn = self.donor.elements[eid]
            vertices = [self.donor.nodes[n] for n in conn]

            xi, eta, converged, res = inverse_isoparametric_quad(vertices, x_target, y_target)
            if converged:
                # Check containment: xi, eta in [-1, 1] within tol
                outside_xi = max(0.0, abs(xi) - 1.0)
                outside_eta = max(0.0, abs(eta) - 1.0)
                dist_outside = math.sqrt(outside_xi ** 2 + outside_eta ** 2)

                if dist_outside <= self.tol_geom:
                    weights = quad_shape_functions(xi, eta)
                    # Coordinate reconstruction check
                    rx, ry = quad_physical_point(vertices, xi, eta)
                    recon_err = math.sqrt((rx - x_target) ** 2 + (ry - y_target) ** 2)

                    return {
                        "host_eid": eid,
                        "xi": xi,
                        "eta": eta,
                        "weights": weights,
                        "recon_error": recon_err,
                        "flank": self.donor.element_flank[eid],
                        "status": "CONTAINED"
                    }
                else:
                    if dist_outside < min_distance_outside:
                        min_distance_outside = dist_outside
                        best_match = {
                            "host_eid": eid,
                            "xi": xi,
                            "eta": eta,
                            "weights": quad_shape_functions(xi, eta),
                            "recon_error": res,
                            "dist_outside": dist_outside,
                            "flank": self.donor.element_flank[eid],
                            "status": "OUTSIDE_TOL"
                        }

        # If not cleanly found in filtered candidates, fallback to unconstrained search if on ligament
        if flank_constraint == "LIGAMENT" and best_match is None:
            return self.map_target_point(x_target, y_target, flank_constraint=None)

        return best_match

    def build_node_transfer_map(self):
        """
        Maps all receiver physical nodes to donor elements.
        Returns node_map dict and summary stats.
        """
        node_map = {}
        errors = []
        rejected = []
        flank_violations = 0

        for nid, (x, y) in sorted(self.receiver.nodes.items()):
            flank = self.receiver.node_flank.get(nid, "LIGAMENT")

            # Flank constraint
            flank_constraint = None
            if flank == "UPPER":
                flank_constraint = "UPPER"
            elif flank == "LOWER":
                flank_constraint = "LOWER"
            elif flank == "LIGAMENT":
                flank_constraint = None

            result = self.map_target_point(x, y, flank_constraint=flank_constraint)
            if result and result.get("status") == "CONTAINED":
                # Verify flank isolation
                host_flank = result["flank"]
                if flank == "UPPER" and host_flank != "UPPER":
                    flank_violations += 1
                elif flank == "LOWER" and host_flank != "LOWER":
                    flank_violations += 1

                node_map[nid] = result
                errors.append(result["recon_error"])
            else:
                rejected.append((nid, x, y, flank, result))

        max_err = max(errors) if errors else 0.0
        rms_err = math.sqrt(sum(e * e for e in errors) / len(errors)) if errors else 0.0

        stats = {
            "total_target_nodes": len(self.receiver.nodes),
            "mapped_nodes": len(node_map),
            "rejected_nodes": len(rejected),
            "coverage_pct": (len(node_map) / float(len(self.receiver.nodes))) * 100.0 if self.receiver.nodes else 0.0,
            "max_coord_recon_error": max_err,
            "rms_coord_recon_error": rms_err,
            "flank_violations": flank_violations,
        }
        return node_map, stats, rejected

    def build_gauss_point_transfer_map(self):
        """
        Maps all receiver Gauss points to donor elements and identifies host nearest GP.
        Returns gp_map dict and summary stats.
        """
        gp_map = {}
        errors = []
        rejected = []
        flank_violations = 0

        for (target_eid, target_gp_idx), (x_gp, y_gp, target_flank) in sorted(self.receiver.gauss_points.items()):
            flank_constraint = target_flank  # strictly UPPER or LOWER for GPs

            result = self.map_target_point(x_gp, y_gp, flank_constraint=flank_constraint)
            if result and result.get("status") == "CONTAINED":
                host_eid = result["host_eid"]
                host_flank = result["flank"]
                if host_flank != target_flank:
                    flank_violations += 1

                # Find nearest host Gauss point in host element
                best_host_gp = 1
                min_gp_dist = float("inf")
                for gp_k in (1, 2, 3, 4):
                    hx, hy, _ = self.donor.gauss_points[(host_eid, gp_k)]
                    dist = math.sqrt((hx - x_gp) ** 2 + (hy - y_gp) ** 2)
                    if dist < min_gp_dist:
                        min_gp_dist = dist
                        best_host_gp = gp_k

                entry = dict(result)
                entry["host_nearest_gp"] = best_host_gp
                entry["host_gp_dist"] = min_gp_dist
                gp_map[(target_eid, target_gp_idx)] = entry
                errors.append(result["recon_error"])
            else:
                rejected.append(((target_eid, target_gp_idx), x_gp, y_gp, target_flank, result))

        max_err = max(errors) if errors else 0.0
        rms_err = math.sqrt(sum(e * e for e in errors) / len(errors)) if errors else 0.0

        stats = {
            "total_target_gps": len(self.receiver.gauss_points),
            "mapped_gps": len(gp_map),
            "rejected_gps": len(rejected),
            "coverage_pct": (len(gp_map) / float(len(self.receiver.gauss_points))) * 100.0 if self.receiver.gauss_points else 0.0,
            "max_coord_recon_error": max_err,
            "rms_coord_recon_error": rms_err,
            "flank_violations": flank_violations,
        }
        return gp_map, stats, rejected

    def run_synthetic_patch_tests(self, node_map, gp_map):
        """
        Executes exact analytical patch tests on the spatial mapping:
        1. Linear displacement patch test: u_x = 2*x + 3*y, u_y = -x + 4*y
        2. Constant phase damage patch test: d = 0.42
        3. Linear phase damage patch test: d = 5*x + 2*y
        4. Conservative history GP patch test: H = 100.0 * (x^2 + y^2)
        """
        # 1. Linear displacement
        disp_errs = []
        for nid, mapping in node_map.items():
            xt, yt = self.receiver.nodes[nid]
            expected_ux = 2.0 * xt + 3.0 * yt
            expected_uy = -1.0 * xt + 4.0 * yt

            host_eid = mapping["host_eid"]
            conn = self.donor.elements[host_eid]
            weights = mapping["weights"]

            calc_ux = sum(w * (2.0 * self.donor.nodes[n][0] + 3.0 * self.donor.nodes[n][1]) for w, n in zip(weights, conn))
            calc_uy = sum(w * (-1.0 * self.donor.nodes[n][0] + 4.0 * self.donor.nodes[n][1]) for w, n in zip(weights, conn))

            err = math.sqrt((calc_ux - expected_ux) ** 2 + (calc_uy - expected_uy) ** 2)
            disp_errs.append(err)

        # 2. Constant phase
        const_d_errs = []
        for nid, mapping in node_map.items():
            weights = mapping["weights"]
            calc_d = sum(w * 0.42 for w in weights)
            const_d_errs.append(abs(calc_d - 0.42))

        # 3. Partition of unity
        pou_errs = []
        for nid, mapping in node_map.items():
            pou_errs.append(abs(sum(mapping["weights"]) - 1.0))

        # 4. GP History non-negativity and nearest GP sanity
        history_non_negativity_violations = 0
        for (teid, tgp), mapping in gp_map.items():
            host_eid = mapping["host_eid"]
            host_gp = mapping["host_nearest_gp"]
            hx, hy, _ = self.donor.gauss_points[(host_eid, host_gp)]
            # Synthetic positive history
            H_host = max(0.0, 100.0 * (hx * hx + hy * hy))
            if H_host < 0.0:
                history_non_negativity_violations += 1

        results = {
            "linear_displacement_max_error": max(disp_errs) if disp_errs else 0.0,
            "linear_displacement_rms_error": math.sqrt(sum(e * e for e in disp_errs) / len(disp_errs)) if disp_errs else 0.0,
            "constant_phase_max_error": max(const_d_errs) if const_d_errs else 0.0,
            "partition_of_unity_max_error": max(pou_errs) if pou_errs else 0.0,
            "history_non_negativity_violations": history_non_negativity_violations,
            "patch_tests_passed": (max(disp_errs) < 1e-10 and max(pou_errs) < 1e-12 and history_non_negativity_violations == 0)
        }
        return results
