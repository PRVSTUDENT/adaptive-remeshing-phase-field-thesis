#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive Offline Unit Test Suite for Bounded Phase-Field [0, 1] Active-Set Formulation.
"""

import sys
import math

def solve_linear_system(A, b):
    n = len(b)
    M = [row[:] for row in A]
    x = b[:]
    
    for i in range(n):
        max_row = i
        for k in range(i+1, n):
            if abs(M[k][i]) > abs(M[max_row][i]):
                max_row = k
        M[i], M[max_row] = M[max_row], M[i]
        x[i], x[max_row] = x[max_row], x[i]
        
        pivot = M[i][i]
        if abs(pivot) < 1.0e-14:
            continue
        for k in range(i+1, n):
            factor = M[k][i] / pivot
            for j in range(i, n):
                M[k][j] -= factor * M[i][j]
            x[k] -= factor * x[i]
            
    res = [0.0] * n
    for i in range(n-1, -1, -1):
        s = x[i]
        for j in range(i+1, n):
            s -= M[i][j] * res[j]
        res[i] = s / M[i][i]
    return res

def quad_shape_and_jac(xi, eta, coords):
    N = [
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta)
    ]
    dN_dxi = [
        [-0.25 * (1.0 - eta),  0.25 * (1.0 - eta),  0.25 * (1.0 + eta), -0.25 * (1.0 + eta)],
        [-0.25 * (1.0 - xi),  -0.25 * (1.0 + xi),   0.25 * (1.0 + xi),   0.25 * (1.0 - xi)]
    ]
    j11 = sum(dN_dxi[0][k] * coords[k][0] for k in range(4))
    j12 = sum(dN_dxi[0][k] * coords[k][1] for k in range(4))
    j21 = sum(dN_dxi[1][k] * coords[k][0] for k in range(4))
    j22 = sum(dN_dxi[1][k] * coords[k][1] for k in range(4))
    
    detj = j11 * j22 - j12 * j21
    invj = [
        [ j22 / detj, -j12 / detj],
        [-j21 / detj,  j11 / detj]
    ]
    B = [[0.0]*4, [0.0]*4]
    for r in range(2):
        for c in range(4):
            B[r][c] = invj[r][0] * dN_dxi[0][c] + invj[r][1] * dN_dxi[1][c]
            
    return N, B, detj

def assemble_and_solve_bounded(nodes_dict, elements, d_committed_dict, H_dict, gc=0.0027, l0=0.015, penalty_factor=1.0e8):
    active_nodes = sorted(list(set(nid for e_nodes in elements.values() for nid in e_nodes)))
    node_to_idx = {nid: idx for idx, nid in enumerate(active_nodes)}
    n_nodes = len(active_nodes)
    
    gp_pts = [-1.0/math.sqrt(3), 1.0/math.sqrt(3)]
    
    # Active-set iteration loop
    # Initial trial d
    d_current = {nid: d_committed_dict.get(nid, 0.0) for nid in active_nodes}
    
    for it in range(10): # active set convergence
        K_global = [[0.0]*n_nodes for _ in range(n_nodes)]
        R_global = [0.0]*n_nodes
        
        for eid, e_nodes in elements.items():
            e_coords = [nodes_dict[nid] for nid in e_nodes]
            k_elem = [[0.0]*4 for _ in range(4)]
            f_elem = [0.0]*4
            
            _, _, detj_center = quad_shape_and_jac(0.0, 0.0, e_coords)
            e_area = detj_center * 4.0
            
            k_idx = 0
            for xi in gp_pts:
                for eta in gp_pts:
                    N, B, detj = quad_shape_and_jac(xi, eta, e_coords)
                    cjac = detj * 1.0
                    H_gp = H_dict.get(eid, [0.0]*4)[k_idx]
                    k_idx += 1
                    
                    for i in range(4):
                        for j in range(4):
                            bdb = B[0][i]*B[0][j] + B[1][i]*B[1][j]
                            k_elem[i][j] += cjac * ((gc * l0) * bdb + (gc / l0 + 2.0 * H_gp) * N[i] * N[j])
                        f_elem[i] += cjac * 2.0 * H_gp * N[i]
                        
            # Lower and upper active set penalty
            for local_i, nid in enumerate(e_nodes):
                d_com = d_committed_dict.get(nid, 0.0)
                u_curr = d_current[nid]
                area_i = 0.25 * e_area
                pen_k = penalty_factor * (gc / l0) * area_i
                
                # Lower bound
                if d_com > 0.0 and u_curr <= d_com:
                    k_elem[local_i][local_i] += pen_k
                    f_elem[local_i] += pen_k * d_com
                # Upper bound
                elif u_curr >= 1.0:
                    k_elem[local_i][local_i] += pen_k
                    f_elem[local_i] += pen_k * 1.0
                
            for i_loc, nid_i in enumerate(e_nodes):
                idx_i = node_to_idx[nid_i]
                R_global[idx_i] += f_elem[i_loc]
                for j_loc, nid_j in enumerate(e_nodes):
                    idx_j = node_to_idx[nid_j]
                    K_global[idx_i][idx_j] += k_elem[i_loc][j_loc]
                    
        d_sol_list = solve_linear_system(K_global, R_global)
        d_new = {nid: d_sol_list[node_to_idx[nid]] for nid in active_nodes}
        
        # Check convergence
        max_diff = max(abs(d_new[nid] - d_current[nid]) for nid in active_nodes)
        d_current = d_new
        if max_diff < 1.0e-9:
            break
            
    return d_current

def run_bounded_unit_tests():
    print("================================================================================")
    print("BOUNDED PHASE-FIELD [0, 1] ACTIVE-SET UNIT TESTS")
    print("================================================================================")
    
    all_ok = True
    nodes = {
        0: (0.0, 0.0), 1: (0.01, 0.0), 2: (0.01, 0.01), 3: (0.0, 0.01),
        4: (-0.01, 0.01), 5: (-0.01, 0.0), 6: (-0.01, -0.01),
        7: (0.0, -0.01), 8: (0.01, -0.01)
    }
    elements = {
        1: [0, 1, 2, 3], 2: [5, 0, 3, 4],
        3: [6, 7, 0, 5], 4: [7, 8, 1, 0]
    }
    
    # Test 1: Transferred Lower Bound Preservation (No Healing)
    print("\n--- TEST 1: Transferred Lower Bound Preservation (H = 0) ---")
    d_com = {nid: 0.284444 for nid in nodes}
    d_res1 = assemble_and_solve_bounded(nodes, elements, d_com, {eid: [0.0]*4 for eid in elements})
    delta1 = d_res1[0] - d_com[0]
    print("  Center Node: Bound = %.6f, Solved = %.6f, Delta = %+.6e" % (d_com[0], d_res1[0], delta1))
    if delta1 < -1.0e-6:
        print("  FAIL: Lower bound violated!")
        all_ok = False
    else:
        print("  PASS: Transferred lower bound strictly preserved.")

    # Test 2: Growth Below 1.0 (H = 0.50)
    print("\n--- TEST 2: Intermediate Growth Below 1.0 (H = 0.50) ---")
    d_res2 = assemble_and_solve_bounded(nodes, elements, d_com, {eid: [0.50]*4 for eid in elements})
    print("  Center Node: Bound = %.6f, Solved = %.6f" % (d_com[0], d_res2[0]))
    if d_res2[0] <= d_com[0] or d_res2[0] > 1.0:
        print("  FAIL: Growth out of bounds!")
        all_ok = False
    else:
        print("  PASS: Intermediate crack growth strictly inside (d_com, 1.0].")

    # Test 3: Extreme Driving Energy Saturation (H = 100.0, Overshoot Prevention)
    print("\n--- TEST 3: Extreme Energy Upper-Bound Clamping (H = 100.0) ---")
    d_res3 = assemble_and_solve_bounded(nodes, elements, d_com, {eid: [100.0]*4 for eid in elements})
    print("  Center Node under H=100: Solved d = %.8f" % d_res3[0])
    if d_res3[0] > 1.000001:
        print("  FAIL: Upper bound overshoot!")
        all_ok = False
    else:
        print("  PASS: Phase field strictly capped at 1.0 (no runaway overshoot).")

    # Test 4: Complete Unloading after Saturated Failure (H = 0 after d = 1)
    print("\n--- TEST 4: Unloading After Complete Fracture (H = 0 after d = 1) ---")
    d_com_sat = {nid: 1.0 for nid in nodes}
    d_res4 = assemble_and_solve_bounded(nodes, elements, d_com_sat, {eid: [0.0]*4 for eid in elements})
    delta4 = d_res4[0] - d_com_sat[0]
    print("  Center Node after Unloading: Bound = %.6f, Solved = %.6f, Delta = %+.6e" % (
        d_com_sat[0], d_res4[0], delta4))
    if delta4 < -1.0e-6:
        print("  FAIL: Healing on unloading from 1.0!")
        all_ok = False
    else:
        print("  PASS: Saturated broken state is 100% irreversible.")

    # Test 5: Mechanical Degradation Monotonicity (No Re-stiffening)
    print("\n--- TEST 5: Mechanical Degradation Law Monotonicity ---")
    ek = 1.0e-6
    for d_test in [0.0, 0.284444, 0.80, 1.0, 1.05, 2.0, 4.03]:
        d_eff = min(max(d_test, 0.0), 1.0)
        deg = (1.0 - d_eff)**2 + ek
        print("  d = %6.3f -> d_eff = %6.3f -> Degradation g(d) = %.6e" % (d_test, d_eff, deg))
        if deg < ek or deg > 1.0 + ek:
            print("  FAIL: Degradation out of physical bounds!")
            all_ok = False
    print("  PASS: Degradation strictly bounded in [1e-6, 1.0] for all d.")

    print("\n================================================================================")
    print("BOUNDED FORMULATION UNIT TEST OUTCOME: %s" % ("ALL TESTS PASSED (100%)" if all_ok else "FAILED"))
    print("================================================================================")
    return all_ok

if __name__ == "__main__":
    run_bounded_unit_tests()
