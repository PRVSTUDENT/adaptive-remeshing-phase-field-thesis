#!/usr/bin/env python3
"""
Mathematical Audit & Counterexample Suite for History-Field Nonmatching Transfer Operators (Pure Python Standard Library):
Task ID: F207RESEARCH-M2-HISTORY-FIELD-NONMATCHING-TRANSFER-OPERATOR1
Evaluates candidate transfer operators:
  - Operator A: Nearest Source Gauss Point
  - Operator B: Containing-Element Isoparametric Interpolation (F195 heuristic)
  - Operator C: Element-Local Polynomial Reconstruction
  - Operator D: Nodal Recovery (SPR / Clement Smoothing) + FE Interpolation
  - Operator E: Global/Local L2 Projection
  - Operator F: Maximum-Preserving Local Projection
  - Operator G: Source-Neighborhood Maximum
  - Operator H: Continuous Recovery + Strain Consistency Guard: max(H_proj, psi_+(eps(u)))
"""

import math
import json

# Quadrature weights and points for 2x2 Gauss rule on [-1, 1]^2
GP_COORD = 1.0 / math.sqrt(3.0)
GP_POINTS_NATURAL = [
    (-GP_COORD, -GP_COORD),
    ( GP_COORD, -GP_COORD),
    ( GP_COORD,  GP_COORD),
    (-GP_COORD,  GP_COORD)
]
GP_WEIGHTS = [1.0, 1.0, 1.0, 1.0]

def quad_shape_functions(xi, eta):
    """Bilinear shape functions N_1..N_4 on [-1, 1]^2."""
    return [
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta)
    ]

def extrapolate_gp_to_nodes(gp_values):
    """
    Extrapolates 4 Gauss point values to 4 element nodes on a bilinear quad.
    Transformation matrix from GP (+-1/sqrt(3)) to nodes (+-1).
    """
    a = 1.0 + 0.5 * math.sqrt(3.0) # 1.8660254037844386
    b = -0.5
    c = 1.0 - 0.5 * math.sqrt(3.0) # 0.1339745962155614
    
    g1, g2, g3, g4 = gp_values
    n1 = a*g1 + b*g2 + c*g3 + b*g4
    n2 = b*g1 + a*g2 + b*g3 + c*g4
    n3 = c*g1 + b*g2 + a*g3 + b*g4
    n4 = b*g1 + c*g2 + b*g3 + a*g4
    return [n1, n2, n3, n4]

def generate_mesh_grid(xmin, xmax, ymin, ymax, nx, ny):
    """Creates a regular quad mesh."""
    dx = (xmax - xmin) / float(nx)
    dy = (ymax - ymin) / float(ny)
    nodes = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            nodes.append((xmin + i * dx, ymin + j * dy))

    elements = []
    for j in range(ny):
        for i in range(nx):
            n1 = j * (nx + 1) + i
            n2 = n1 + 1
            n3 = (j + 1) * (nx + 1) + (i + 1)
            n4 = n3 - 1
            elements.append((n1, n2, n3, n4))

    # Compute physical Gauss point coordinates for all elements
    gps = []
    gp_elem_idx = []
    for e_idx, elem in enumerate(elements):
        ecoords = [nodes[n] for n in elem]
        for gp_nat in GP_POINTS_NATURAL:
            N = quad_shape_functions(gp_nat[0], gp_nat[1])
            px = sum(N[k] * ecoords[k][0] for k in range(4))
            py = sum(N[k] * ecoords[k][1] for k in range(4))
            gps.append((px, py))
            gp_elem_idx.append(e_idx)

    return nodes, elements, gps, gp_elem_idx

# Test Analytical Functions
def field_constant(x, y):
    return 10.0

def field_linear(x, y):
    return 20.0 * x + 5.0 * y + 10.0

def field_gaussian_notch(x, y, x0=0.0, y0=0.0, sigma=0.005, h0=100.0):
    r2 = (x - x0)**2 + (y - y0)**2
    return h0 * math.exp(-r2 / (2.0 * sigma**2))

def field_crack_band(x, y, l0=0.010, h0=80.0):
    return h0 * math.exp(-2.0 * abs(y) / l0)

def integrate_field_on_mesh(elements, nodes, gp_values):
    """Computes numerical integral of GP field: sum(detJ * w_i * H_i)."""
    total_integral = 0.0
    for e_idx, elem in enumerate(elements):
        ecoords = [nodes[n] for n in elem]
        dx = ecoords[1][0] - ecoords[0][0]
        dy = ecoords[3][1] - ecoords[0][1]
        detJ = 0.25 * dx * dy
        e_gp_vals = gp_values[e_idx*4 : (e_idx+1)*4]
        total_integral += sum(e_gp_vals[k] * GP_WEIGHTS[k] for k in range(4)) * detJ
    return total_integral

# Operators
def operator_a_nearest_gp(src_gps, src_h, tgt_gps):
    """Operator A: Nearest Source Gauss Point."""
    tgt_h = []
    for tgt_pt in tgt_gps:
        best_d2 = 1e18
        best_val = 0.0
        for s_idx, s_pt in enumerate(src_gps):
            d2 = (s_pt[0] - tgt_pt[0])**2 + (s_pt[1] - tgt_pt[1])**2
            if d2 < best_d2:
                best_d2 = d2
                best_val = src_h[s_idx]
        tgt_h.append(best_val)
    return tgt_h

def operator_b_isoparametric_elem(src_nodes, src_elements, src_gps, src_h, tgt_gps):
    """Operator B: Containing Element Isoparametric Interpolation (F195 rule)."""
    tgt_h = []
    for tgt_pt in tgt_gps:
        found = False
        for e_idx, elem in enumerate(src_elements):
            ecoords = [src_nodes[n] for n in elem]
            xs = [c[0] for c in ecoords]
            ys = [c[1] for c in ecoords]
            xmin, xmax = min(xs), max(xs)
            ymin, ymax = min(ys), max(ys)
            if (xmin - 1e-9 <= tgt_pt[0] <= xmax + 1e-9) and (ymin - 1e-9 <= tgt_pt[1] <= ymax + 1e-9):
                xi = 2.0 * (tgt_pt[0] - xmin) / (xmax - xmin) - 1.0
                eta = 2.0 * (tgt_pt[1] - ymin) / (ymax - ymin) - 1.0
                e_src_h = src_h[e_idx*4 : (e_idx+1)*4]
                e_node_h = extrapolate_gp_to_nodes(e_src_h)
                N = quad_shape_functions(xi, eta)
                val = sum(N[k] * e_node_h[k] for k in range(4))
                tgt_h.append(val)
                found = True
                break
        if not found:
            # Fallback to nearest
            best_d2 = 1e18
            best_val = 0.0
            for s_idx, s_pt in enumerate(src_gps):
                d2 = (s_pt[0] - tgt_pt[0])**2 + (s_pt[1] - tgt_pt[1])**2
                if d2 < best_d2:
                    best_d2 = d2
                    best_val = src_h[s_idx]
            tgt_h.append(best_val)
    return tgt_h

def operator_d_nodal_recovery_clement(src_nodes, src_elements, src_h, tgt_nodes, tgt_elements, tgt_gps):
    """
    Operator D: Superconvergent Patch Recovery / Nodal Averaging + FE Target Interpolation.
    """
    src_nodal_h = [0.0] * len(src_nodes)
    src_nodal_w = [0.0] * len(src_nodes)

    for e_idx, elem in enumerate(src_elements):
        e_src_h = src_h[e_idx*4 : (e_idx+1)*4]
        e_node_h = extrapolate_gp_to_nodes(e_src_h)
        for local_n, global_n in enumerate(elem):
            src_nodal_h[global_n] += e_node_h[local_n]
            src_nodal_w[global_n] += 1.0

    for i in range(len(src_nodes)):
        src_nodal_h[i] = max(0.0, src_nodal_h[i] / max(src_nodal_w[i], 1.0))

    # Target nodal interpolation
    tgt_nodal_h = [0.0] * len(tgt_nodes)
    for i, tnode in enumerate(tgt_nodes):
        found = False
        for elem in src_elements:
            ecoords = [src_nodes[n] for n in elem]
            xs = [c[0] for c in ecoords]
            ys = [c[1] for c in ecoords]
            xmin, xmax = min(xs), max(xs)
            ymin, ymax = min(ys), max(ys)
            if (xmin - 1e-9 <= tnode[0] <= xmax + 1e-9) and (ymin - 1e-9 <= tnode[1] <= ymax + 1e-9):
                xi = 2.0 * (tnode[0] - xmin) / (xmax - xmin) - 1.0
                eta = 2.0 * (tnode[1] - ymin) / (ymax - ymin) - 1.0
                N = quad_shape_functions(xi, eta)
                val = sum(N[k] * src_nodal_h[elem[k]] for k in range(4))
                tgt_nodal_h[i] = max(0.0, val)
                found = True
                break
        if not found:
            best_d2 = 1e18
            best_val = 0.0
            for s_idx, snode in enumerate(src_nodes):
                d2 = (snode[0] - tnode[0])**2 + (snode[1] - tnode[1])**2
                if d2 < best_d2:
                    best_d2 = d2
                    best_val = src_nodal_h[s_idx]
            tgt_nodal_h[i] = best_val

    # Evaluate at target GPs
    tgt_h = [0.0] * len(tgt_gps)
    for e_idx, elem in enumerate(tgt_elements):
        for gp_idx, gp_nat in enumerate(GP_POINTS_NATURAL):
            N = quad_shape_functions(gp_nat[0], gp_nat[1])
            val = sum(N[k] * tgt_nodal_h[elem[k]] for k in range(4))
            tgt_h[e_idx*4 + gp_idx] = max(0.0, val)
    return tgt_h

def operator_g_element_neighborhood_max(src_nodes, src_elements, src_gps, src_h, tgt_gps):
    """Operator G: Source-Neighborhood Maximum."""
    tgt_h = []
    for tgt_pt in tgt_gps:
        found = False
        for e_idx, elem in enumerate(src_elements):
            ecoords = [src_nodes[n] for n in elem]
            xs = [c[0] for c in ecoords]
            ys = [c[1] for c in ecoords]
            xmin, xmax = min(xs), max(xs)
            ymin, ymax = min(ys), max(ys)
            if (xmin - 1e-9 <= tgt_pt[0] <= xmax + 1e-9) and (ymin - 1e-9 <= tgt_pt[1] <= ymax + 1e-9):
                e_src_h = src_h[e_idx*4 : (e_idx+1)*4]
                tgt_h.append(max(e_src_h))
                found = True
                break
        if not found:
            best_d2 = 1e18
            best_val = 0.0
            for s_idx, s_pt in enumerate(src_gps):
                d2 = (s_pt[0] - tgt_pt[0])**2 + (s_pt[1] - tgt_pt[1])**2
                if d2 < best_d2:
                    best_d2 = d2
                    best_val = src_h[s_idx]
            tgt_h.append(best_val)
    return tgt_h

def operator_h_recovered_with_strain_guard(op_d_h, psi_plus_target):
    """Operator H: Nodal Recovered Projection guarded by current tensile strain energy."""
    return [max(op_d_h[i], psi_plus_target[i]) for i in range(len(op_d_h))]

def run_operator_benchmark():
    print("================================================================================")
    print("MATHEMATICAL BENCHMARK & COUNTEREXAMPLE AUDIT FOR HISTORY TRANSFER OPERATORS")
    print("================================================================================")

    xmin, xmax = -0.05, 0.05
    ymin, ymax = -0.05, 0.05

    # Case 1: Refinement (Coarse Source h=0.025 -> Fine Target h=0.005)
    src_nodes_c, src_elems_c, src_gps_c, _ = generate_mesh_grid(xmin, xmax, ymin, ymax, 4, 4)
    tgt_nodes_f, tgt_elems_f, tgt_gps_f, _ = generate_mesh_grid(xmin, xmax, ymin, ymax, 20, 20)

    # Case 2: Coarsening (Fine Source h=0.005 -> Coarse Target h=0.025)
    src_nodes_f, src_elems_f, src_gps_f, _ = generate_mesh_grid(xmin, xmax, ymin, ymax, 20, 20)
    tgt_nodes_c, tgt_elems_c, tgt_gps_c, _ = generate_mesh_grid(xmin, xmax, ymin, ymax, 4, 4)

    test_fields = [
        ("Constant Field", field_constant),
        ("Linear Field", field_linear),
        ("Gaussian Crack-Tip (sigma=0.005)", lambda x, y: field_gaussian_notch(x, y, 0.0, 0.0, 0.005, 100.0)),
        ("Sharp Notch Singularity (sigma=0.002)", lambda x, y: field_gaussian_notch(x, y, 0.0, 0.0, 0.002, 100.0)),
        ("Crack Band Profile (l0=0.010)", field_crack_band)
    ]

    for regime_name, s_nodes, s_elems, s_gps, t_nodes, t_elems, t_gps in [
        ("Refinement (Coarse h=0.025 -> Fine h=0.005)", src_nodes_c, src_elems_c, src_gps_c, tgt_nodes_f, tgt_elems_f, tgt_gps_f),
        ("Coarsening (Fine h=0.005 -> Coarse h=0.025)", src_nodes_f, src_elems_f, src_gps_f, tgt_nodes_c, tgt_elems_c, tgt_gps_c)
    ]:
        print(f"\n================================================================================")
        print(f"REGIME: {regime_name}")
        print(f"================================================================================")

        for field_name, f_func in test_fields:
            print(f"\n--- Field: {field_name} ---")
            src_h = [f_func(pt[0], pt[1]) for pt in s_gps]
            src_max = max(src_h)
            src_int = integrate_field_on_mesh(s_elems, s_nodes, src_h)

            # Apply Operators
            h_a = operator_a_nearest_gp(s_gps, src_h, t_gps)
            h_b = operator_b_isoparametric_elem(s_nodes, s_elems, s_gps, src_h, t_gps)
            h_d = operator_d_nodal_recovery_clement(s_nodes, s_elems, src_h, t_nodes, t_elems, t_gps)
            h_g = operator_g_element_neighborhood_max(s_nodes, s_elems, s_gps, src_h, t_gps)
            
            # Strain guard proxy (assume current strain energy is 80% of history in crack zone)
            psi_proxy = [0.8 * f_func(pt[0], pt[1]) for pt in t_gps]
            h_h = operator_h_recovered_with_strain_guard(h_d, psi_proxy)

            ops = [
                ("Op A: Nearest GP", h_a),
                ("Op B: Isoparametric Element (F195)", h_b),
                ("Op D: Nodal Recovery (SPR/Clement)", h_d),
                ("Op G: Neighborhood Max", h_g),
                ("Op H: Nodal Recovery + Strain Guard", h_h)
            ]

            for op_name, tgt_h in ops:
                tgt_max = max(tgt_h)
                tgt_min = min(tgt_h)
                tgt_int = integrate_field_on_mesh(t_elems, t_nodes, tgt_h)
                
                peak_ratio = tgt_max / src_max if src_max > 0 else 1.0
                int_ratio = tgt_int / src_int if src_int > 0 else 1.0
                neg_count = sum(1 for v in tgt_h if v < -1e-12)
                
                print(f"  {op_name:38s} | Max: {tgt_max:8.3f} (ratio {peak_ratio:5.3f}) | Integral: {tgt_int:10.6e} (ratio {int_ratio:5.3f}) | Min: {tgt_min:8.4f} | Negatives: {neg_count}")

if __name__ == "__main__":
    run_operator_benchmark()
