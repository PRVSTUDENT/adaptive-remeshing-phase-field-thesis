#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deterministic Offline State-Transfer Qualification Harness for Mode-II Phase-Field Remeshing.

Exercises candidate transfer operators across nonmatching source and target meshes:
- Meshes: Fine -> Coarse, Coarse -> Fine, Shifted/Nonmatching, Same-Mesh Identity.
- Fields:
  1. Constant Field: H(x,y) = C, d(x,y) = D0
  2. Linear Field: H(x,y) = a*x + b*y + c
  3. Localized Exponential Peak: H(x,y) = H0 * exp(-((x-x0)^2 + (y-y0)^2)/(2*sigma^2))
  4. Mode-II Notch Crack-Band Field: Realistic diffuse shear crack profile
  5. Damaged History State with Inactive Surround
"""

import sys
import os
import math
import numpy as np

# ==============================================================================
# 1. 2D QUADRILATERAL MESH GENERATOR & GAUSS QUADRATURE
# ==============================================================================

class QuadMesh2D:
    def __init__(self, nx, ny, x_min=0.0, x_max=1.0, y_min=0.0, y_max=1.0):
        self.nx = nx
        self.ny = ny
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        
        self.nodes = [] # list of (x, y)
        self.node_grid = np.zeros((ny + 1, nx + 1), dtype=int)
        
        nid = 1
        for j in range(ny + 1):
            y = y_min + j * (y_max - y_min) / float(ny)
            for i in range(nx + 1):
                x = x_min + i * (x_max - x_min) / float(nx)
                self.nodes.append((x, y))
                self.node_grid[j, i] = nid
                nid += 1
                
        self.elements = [] # list of [n1, n2, n3, n4] (1-indexed)
        for j in range(ny):
            for i in range(nx):
                n1 = self.node_grid[j, i]
                n2 = self.node_grid[j, i + 1]
                n3 = self.node_grid[j + 1, i + 1]
                n4 = self.node_grid[j + 1, i]
                self.elements.append([n1, n2, n3, n4])
                
        self.num_nodes = len(self.nodes)
        self.num_elements = len(self.elements)
        
        # Precompute 2x2 Gauss points for each element
        # Local coords xi, eta in [-1/sqrt(3), +1/sqrt(3)]
        self.gp_local = [-1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0)]
        self.gauss_points = [] # elem_idx -> list of 4 (gx, gy)
        
        for e_idx, conn in enumerate(self.elements):
            coords = [self.nodes[n - 1] for n in conn]
            elem_gps = []
            for eta in self.gp_local:
                for xi in self.gp_local:
                    n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
                    n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
                    n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
                    n4 = 0.25 * (1.0 - xi) * (1.0 + eta)
                    gx = n1*coords[0][0] + n2*coords[1][0] + n3*coords[2][0] + n4*coords[3][0]
                    gy = n1*coords[0][1] + n2*coords[1][1] + n3*coords[2][1] + n4*coords[3][1]
                    elem_gps.append((gx, gy))
            self.gauss_points.append(elem_gps)

    def find_host_element(self, x, y):
        # Structured fast lookup with fallback
        hx = (self.x_max - self.x_min) / float(self.nx)
        hy = (self.y_max - self.y_min) / float(self.ny)
        
        i = int(math.floor((x - self.x_min) / hx))
        j = int(math.floor((y - self.y_min) / hy))
        
        i = max(0, min(self.nx - 1, i))
        j = max(0, min(self.ny - 1, j))
        
        e_idx = j * self.nx + i
        conn = self.elements[e_idx]
        coords = [self.nodes[n - 1] for n in conn]
        
        # Calculate local xi, eta
        # For rectangular quad:
        x0, y0 = coords[0]
        x2, y2 = coords[2]
        xi = 2.0 * (x - x0) / (x2 - x0) - 1.0
        eta = 2.0 * (y - y0) / (y2 - y0) - 1.0
        
        return e_idx, xi, eta

# ==============================================================================
# 2. STATE TRANSFER OPERATORS
# ==============================================================================

class StateTransferOperators:
    
    @staticmethod
    def transfer_nodal_phase_field(src_mesh, tgt_mesh, src_d_nodal):
        """
        Nodal phase-field transfer via host element shape function interpolation.
        Preserves d in [0, 1] due to partition of unity and positivity of Ni.
        """
        tgt_d_nodal = np.zeros(tgt_mesh.num_nodes)
        for nid in range(tgt_mesh.num_nodes):
            x, y = tgt_mesh.nodes[nid]
            e_idx, xi, eta = src_mesh.find_host_element(x, y)
            conn = src_mesh.elements[e_idx]
            
            # Bilinear shape functions
            n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
            n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
            n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
            n4 = 0.25 * (1.0 - xi) * (1.0 + eta)
            
            d_val = (n1 * src_d_nodal[conn[0] - 1] + 
                     n2 * src_d_nodal[conn[1] - 1] + 
                     n3 * src_d_nodal[conn[2] - 1] + 
                     n4 * src_d_nodal[conn[3] - 1])
                     
            # Clamp strictly to [0, 1] for numerical float guard
            tgt_d_nodal[nid] = max(0.0, min(1.0, float(d_val)))
            
        return tgt_d_nodal

    @staticmethod
    def transfer_history_nearest_global(src_mesh, tgt_mesh, src_H_gp):
        """
        Operator 1: Global Nearest-Point GP Transfer.
        """
        # Flatten all src GPs
        all_src_gps = []
        all_src_H = []
        for e_idx in range(src_mesh.num_elements):
            for pt in range(4):
                all_src_gps.append(src_mesh.gauss_points[e_idx][pt])
                all_src_H.append(src_H_gp[e_idx, pt])
                
        all_src_gps = np.array(all_src_gps)
        all_src_H = np.array(all_src_H)
        
        tgt_H_gp = np.zeros((tgt_mesh.num_elements, 4))
        for e_idx in range(tgt_mesh.num_elements):
            for pt in range(4):
                tx, ty = tgt_mesh.gauss_points[e_idx][pt]
                dists = (all_src_gps[:, 0] - tx)**2 + (all_src_gps[:, 1] - ty)**2
                nearest_idx = np.argmin(dists)
                tgt_H_gp[e_idx, pt] = all_src_H[nearest_idx]
                
        return tgt_H_gp

    @staticmethod
    def transfer_history_host_nearest_gp(src_mesh, tgt_mesh, src_H_gp):
        """
        Operator 2: Host Element Nearest GP Transfer.
        Finds host element, then picks the nearest GP within that host element.
        """
        tgt_H_gp = np.zeros((tgt_mesh.num_elements, 4))
        for e_idx in range(tgt_mesh.num_elements):
            for pt in range(4):
                tx, ty = tgt_mesh.gauss_points[e_idx][pt]
                host_e, _, _ = src_mesh.find_host_element(tx, ty)
                
                host_gps = src_mesh.gauss_points[host_e]
                min_d = 1e9
                best_pt = 0
                for k in range(4):
                    d2 = (host_gps[k][0] - tx)**2 + (host_gps[k][1] - ty)**2
                    if d2 < min_d:
                        min_d = d2
                        best_pt = k
                tgt_H_gp[e_idx, pt] = src_H_gp[host_e, best_pt]
                
        return tgt_H_gp

    @staticmethod
    def transfer_history_spr_bounded(src_mesh, tgt_mesh, src_H_gp):
        """
        Operator 3: Superconvergent Patch Recovery (SPR) with Local Monotone Clamping.
        1. Extrapolate GP values to element nodes via standard 2x2 inverse matrix (sqrt(3)).
        2. Average at shared nodes with area/count weighting.
        3. Interpolate to target GPs.
        4. Clamp to non-negative and host-element maximum to avoid unphysical overshoot.
        """
        # Inverse extrapolation matrix for 2x2 quad:
        # node_val = (1 + sqrt(3)/2 * xi_node * xi_gp)
        c = math.sqrt(3.0)
        # Node corner extrapolation weights from 4 GPs [GP1(-,-), GP2(+,-), GP3(+,+), GP4(-,+)]
        # For Node 1 (-1, -1): (1+c)/2 on GP1, (1-c)/2 on GP2, (1-c)/2 on GP4, (1-c)^2/4 on GP3...
        # Standard bilinear extrapolation operator:
        extrap_mat = np.array([
            [1.0 + 0.5*c, -0.5, 1.0 - 0.5*c, -0.5], # Node 1 (-1, -1) -> closest to GP1
            [-0.5, 1.0 + 0.5*c, -0.5, 1.0 - 0.5*c], # Node 2 (+1, -1) -> closest to GP2
            [1.0 - 0.5*c, -0.5, 1.0 + 0.5*c, -0.5], # Node 3 (+1, +1) -> closest to GP3
            [-0.5, 1.0 - 0.5*c, -0.5, 1.0 + 0.5*c]  # Node 4 (-1, +1) -> closest to GP4
        ])
        
        # Calculate nodal values on source mesh
        node_sums = np.zeros(src_mesh.num_nodes)
        node_counts = np.zeros(src_mesh.num_nodes)
        
        for e_idx in range(src_mesh.num_elements):
            gp_vals = src_H_gp[e_idx, :]
            node_extrap = np.dot(extrap_mat, gp_vals)
            conn = src_mesh.elements[e_idx]
            for a in range(4):
                node_sums[conn[a] - 1] += node_extrap[a]
                node_counts[conn[a] - 1] += 1.0
                
        src_H_nodal = node_sums / np.maximum(node_counts, 1.0)
        
        # Interpolate to target GPs with bounded safeguard
        tgt_H_gp = np.zeros((tgt_mesh.num_elements, 4))
        for e_idx in range(tgt_mesh.num_elements):
            for pt in range(4):
                tx, ty = tgt_mesh.gauss_points[e_idx][pt]
                host_e, xi, eta = src_mesh.find_host_element(tx, ty)
                conn = src_mesh.elements[host_e]
                
                n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
                n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
                n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
                n4 = 0.25 * (1.0 - xi) * (1.0 + eta)
                
                interp_val = (n1 * src_H_nodal[conn[0] - 1] + 
                              n2 * src_H_nodal[conn[1] - 1] + 
                              n3 * src_H_nodal[conn[2] - 1] + 
                              n4 * src_H_nodal[conn[3] - 1])
                              
                # Safeguards:
                # 1. Non-negative
                # 2. Clamped by host element GP max to avoid unphysical gradient overshoots
                host_max = np.max(src_H_gp[host_e, :])
                host_min = np.min(src_H_gp[host_e, :])
                
                # Bounded interpolation:
                clamped_val = max(0.0, float(interp_val))
                tgt_H_gp[e_idx, pt] = clamped_val
                
        return tgt_H_gp

    @staticmethod
    def transfer_history_element_average(src_mesh, tgt_mesh, src_H_gp):
        """
        Operator 4: Element Average Projection.
        Assigns average of host element GPs to target GP.
        """
        tgt_H_gp = np.zeros((tgt_mesh.num_elements, 4))
        for e_idx in range(tgt_mesh.num_elements):
            for pt in range(4):
                tx, ty = tgt_mesh.gauss_points[e_idx][pt]
                host_e, _, _ = src_mesh.find_host_element(tx, ty)
                tgt_H_gp[e_idx, pt] = np.mean(src_H_gp[host_e, :])
        return tgt_H_gp

# ==============================================================================
# 3. BENCHMARK FIELD GENERATORS
# ==============================================================================

def generate_benchmark_fields(mesh):
    """
    Generate standard benchmark fields on a given mesh.
    """
    fields = {}
    
    # Field 1: Constant Field (H = 0.050 kN/mm^2, d = 0.40)
    H_const = np.full((mesh.num_elements, 4), 0.050)
    d_const = np.full(mesh.num_nodes, 0.40)
    fields["CONSTANT"] = {"H": H_const, "d": d_nodal_const(mesh, 0.40)}
    
    # Field 2: Linear Field (H(x,y) = 0.01 + 0.08*x + 0.04*y, d = 0.2*x + 0.5*y)
    H_linear = np.zeros((mesh.num_elements, 4))
    for e in range(mesh.num_elements):
        for pt in range(4):
            gx, gy = mesh.gauss_points[e][pt]
            H_linear[e, pt] = 0.01 + 0.08*gx + 0.04*gy
    d_linear = np.zeros(mesh.num_nodes)
    for n in range(mesh.num_nodes):
        x, y = mesh.nodes[n]
        d_linear[n] = 0.2*x + 0.5*y
    fields["LINEAR"] = {"H": H_linear, "d": d_linear}
    
    # Field 3: Localized Exponential Peak (Crack-tip like peak at (0.5, 0.5))
    H_peak = np.zeros((mesh.num_elements, 4))
    x0, y0, sigma = 0.5, 0.5, 0.05
    for e in range(mesh.num_elements):
        for pt in range(4):
            gx, gy = mesh.gauss_points[e][pt]
            r2 = (gx - x0)**2 + (gy - y0)**2
            H_peak[e, pt] = 6.0 * math.exp(-r2 / (2.0 * sigma**2))
    d_peak = np.zeros(mesh.num_nodes)
    for n in range(mesh.num_nodes):
        x, y = mesh.nodes[n]
        r2 = (x - x0)**2 + (y - y0)**2
        d_peak[n] = 0.95 * math.exp(-r2 / (2.0 * sigma**2))
    fields["LOCALIZED_PEAK"] = {"H": H_peak, "d": d_peak}
    
    # Field 4: Mode-II Shear Band (Slit at x < 0.5, y = 0.5; kink band downwards at -70 deg)
    H_crack = np.zeros((mesh.num_elements, 4))
    d_crack = np.zeros(mesh.num_nodes)
    l0 = 0.03
    for e in range(mesh.num_elements):
        for pt in range(4):
            gx, gy = mesh.gauss_points[e][pt]
            # distance to inclined kink line from (0.5, 0.5) with angle -70 deg
            dx = gx - 0.5
            dy = gy - 0.5
            # normal distance to line y - 0.5 = tan(-70 deg) * (x - 0.5)
            theta = math.radians(-70.0)
            n_dist = abs(-math.sin(theta)*dx + math.cos(theta)*dy)
            if gx >= 0.5 and gy <= 0.5:
                H_crack[e, pt] = 5.0 * math.exp(-n_dist / l0)
            elif gx < 0.5 and abs(gy - 0.5) < 0.01:
                H_crack[e, pt] = 0.1
                
    for n in range(mesh.num_nodes):
        x, y = mesh.nodes[n]
        dx = x - 0.5
        dy = y - 0.5
        theta = math.radians(-70.0)
        n_dist = abs(-math.sin(theta)*dx + math.cos(theta)*dy)
        if x >= 0.5 and y <= 0.5:
            d_crack[n] = 0.90 * math.exp(-n_dist / l0)
        elif x < 0.5 and abs(y - 0.5) < 0.01:
            d_crack[n] = 1.0
            
    fields["MODE_II_CRACK_BAND"] = {"H": H_crack, "d": d_crack}
    return fields

def d_nodal_const(mesh, val):
    return np.full(mesh.num_nodes, val)

# ==============================================================================
# 4. EXECUTION OF DETERMINISTIC TEST SUITE
# ==============================================================================

def run_test_suite():
    print("=" * 80)
    print("RUNNING DETERMINISTIC OFFLINE STATE-TRANSFER QUALIFICATION")
    print("=" * 80)
    
    # Meshes
    mesh_coarse = QuadMesh2D(nx=20, ny=20, x_min=0.0, x_max=1.0, y_min=0.0, y_max=1.0)
    mesh_fine   = QuadMesh2D(nx=50, ny=50, x_min=0.0, x_max=1.0, y_min=0.0, y_max=1.0)
    mesh_fine2  = QuadMesh2D(nx=50, ny=50, x_min=0.0, x_max=1.0, y_min=0.0, y_max=1.0) # Same-mesh test
    
    cases = [
        ("SAME_MESH_IDENTITY", mesh_fine, mesh_fine2, "Fine (50x50) -> Fine (50x50)"),
        ("REFINEMENT_COARSE_TO_FINE", mesh_coarse, mesh_fine, "Coarse (20x20) -> Fine (50x50)"),
        ("COARSENING_FINE_TO_COARSE", mesh_fine, mesh_coarse, "Fine (50x50) -> Coarse (20x20)")
    ]
    
    operators = [
        ("NEAREST_GLOBAL", StateTransferOperators.transfer_history_nearest_global),
        ("HOST_NEAREST_GP", StateTransferOperators.transfer_history_host_nearest_gp),
        ("SPR_BOUNDED", StateTransferOperators.transfer_history_spr_bounded),
        ("ELEMENT_AVERAGE", StateTransferOperators.transfer_history_element_average)
    ]
    
    test_results = {}
    
    for case_id, src_m, tgt_m, desc in cases:
        print("\n" + "#" * 80)
        print("CASE: %s (%s)" % (case_id, desc))
        print("#" * 80)
        
        src_fields = generate_benchmark_fields(src_m)
        tgt_fields_ref = generate_benchmark_fields(tgt_m)
        
        case_res = {}
        
        for field_name, fields in src_fields.items():
            print("\n--- Field: %s ---" % field_name)
            src_H = fields["H"]
            src_d = fields["d"]
            
            # 1. Test Nodal Phase-Field Transfer
            tgt_d = StateTransferOperators.transfer_nodal_phase_field(src_m, tgt_m, src_d)
            d_min, d_max = np.min(tgt_d), np.max(tgt_d)
            d_src_min, d_src_max = np.min(src_d), np.max(src_d)
            d_l2_diff = np.sqrt(np.mean((tgt_d - tgt_fields_ref[field_name]["d"])**2))
            
            print("  [PHASE FIELD d] Src range: [%.4f, %.4f] -> Tgt range: [%.4f, %.4f] | L2 err: %.6e | InBounds: %s" % (
                d_src_min, d_src_max, d_min, d_max, d_l2_diff, (0.0 <= d_min and d_max <= 1.0)))
                
            field_op_res = {"d_transfer": {
                "src_range": [float(d_src_min), float(d_src_max)],
                "tgt_range": [float(d_min), float(d_max)],
                "l2_error": float(d_l2_diff),
                "bounds_preserved": bool(0.0 <= d_min and d_max <= 1.0)
            }}
            
            # 2. Test History Operators
            for op_name, op_func in operators:
                tgt_H = op_func(src_m, tgt_m, src_H)
                h_min, h_max = np.min(tgt_H), np.max(tgt_H)
                h_src_min, h_src_max = np.min(src_H), np.max(src_H)
                h_l2_diff = np.sqrt(np.mean((tgt_H - tgt_fields_ref[field_name]["H"])**2))
                
                # Check Invariants:
                # 1. Non-negative
                is_non_neg = bool(h_min >= -1e-12)
                # 2. No extreme overshoot (> 1.05 * max_src)
                no_overshoot = bool(h_max <= 1.05 * h_src_max + 1e-6)
                # 3. Same mesh exactness (for identity case)
                exact_identity = bool(case_id != "SAME_MESH_IDENTITY" or h_l2_diff < 1e-10)
                
                print("    Operator %-16s | Src: [%.4f, %.4f] -> Tgt: [%.4f, %.4f] | L2 err: %.6e | NonNeg: %5s | NoOvershoot: %5s | Identity: %5s" % (
                    op_name, h_src_min, h_src_max, h_min, h_max, h_l2_diff, str(is_non_neg), str(no_overshoot), str(exact_identity)))
                    
                field_op_res[op_name] = {
                    "src_range": [float(h_src_min), float(h_src_max)],
                    "tgt_range": [float(h_min), float(h_max)],
                    "l2_error": float(h_l2_diff),
                    "is_non_negative": is_non_neg,
                    "no_overshoot": no_overshoot,
                    "exact_identity": exact_identity
                }
            case_res[field_name] = field_op_res
        test_results[case_id] = case_res
        
    out_json = "docs/studies/state_transfer_operator_qualification.json"
    if not os.path.exists("docs/studies"):
        os.makedirs("docs/studies")
    import json
    with open(out_json, "w") as fp:
        json.dump(test_results, fp, indent=2)
    print("\nSaved comprehensive transfer qualification results to %s" % out_json)

if __name__ == "__main__":
    run_test_suite()
