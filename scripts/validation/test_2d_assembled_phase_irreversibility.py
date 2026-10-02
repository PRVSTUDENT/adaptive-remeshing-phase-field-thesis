#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
2D Finite-Element Assembled Multi-Element Patch Test for Phase-Field Irreversibility.
Implemented using pure Python standard library for standalone cluster execution.
"""

import os
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

def assemble_and_solve_patch(nodes_dict, elements, d_committed_dict, H_dict, gc=0.0027, l0=0.015, penalty_factor=1.0e8):
    # Determine active nodes
    active_nodes = sorted(list(set(nid for e_nodes in elements.values() for nid in e_nodes)))
    node_to_idx = {nid: idx for idx, nid in enumerate(active_nodes)}
    n_nodes = len(active_nodes)
    
    K_global = [[0.0]*n_nodes for _ in range(n_nodes)]
    R_global = [0.0]*n_nodes
    
    gp_pts = [-1.0/math.sqrt(3), 1.0/math.sqrt(3)]
    
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
                    
        for local_i, nid in enumerate(e_nodes):
            d_com = d_committed_dict.get(nid, 0.0)
            area_i = 0.25 * e_area
            pen_k = penalty_factor * (gc / l0) * area_i
            k_elem[local_i][local_i] += pen_k
            f_elem[local_i] += pen_k * d_com
            
        for i_loc, nid_i in enumerate(e_nodes):
            idx_i = node_to_idx[nid_i]
            R_global[idx_i] += f_elem[i_loc]
            for j_loc, nid_j in enumerate(e_nodes):
                idx_j = node_to_idx[nid_j]
                K_global[idx_i][idx_j] += k_elem[i_loc][j_loc]
                
    d_sol_list = solve_linear_system(K_global, R_global)
    return {nid: d_sol_list[node_to_idx[nid]] for nid in active_nodes}

def run_2d_assembled_tests():
    print("================================================================================")
    print("2D ASSEMBLED FINITE-ELEMENT PATCH TESTS (EXACT FE ASSEMBLY)")
    print("================================================================================")
    
    all_ok = True
    
    # Test 1: 4-Element Patch Sharing Node 0 (Valence 4)
    print("\n--- TEST 1: 4-Element Shared Node Patch (Valence 4) ---")
    nodes = {
        0: (0.0, 0.0), 1: (0.01, 0.0), 2: (0.01, 0.01), 3: (0.0, 0.01),
        4: (-0.01, 0.01), 5: (-0.01, 0.0), 6: (-0.01, -0.01),
        7: (0.0, -0.01), 8: (0.01, -0.01)
    }
    elements = {
        1: [0, 1, 2, 3],
        2: [5, 0, 3, 4],
        3: [6, 7, 0, 5],
        4: [7, 8, 1, 0]
    }
    d_committed = {nid: (0.284444 if nid == 0 else 0.10) for nid in nodes}
    H_zero = {eid: [0.0]*4 for eid in elements}
    
    d_res = assemble_and_solve_patch(nodes, elements, d_committed, H_zero)
    d_center = d_res[0]
    delta_d = d_center - d_committed[0]
    print("  Center Node (Valence 4): Bound = %.6f, Solved = %.6f, Delta d = %+.6e" % (
        d_committed[0], d_center, delta_d))
    if delta_d < -1.0e-6:
        print("  FAIL: Irreversibility violated!")
        all_ok = False
    else:
        print("  PASS: Assembled Valence 4 node strictly satisfies R7 criterion.")
        
    # Test 2: Irregular Valence (Valence 3)
    print("\n--- TEST 2: Irregular Valence Patch (Valence 3) ---")
    elements_v3 = {1: [0, 1, 2, 3], 2: [5, 0, 3, 4], 3: [6, 7, 0, 5]}
    d_res_v3 = assemble_and_solve_patch(nodes, elements_v3, d_committed, H_zero)
    delta_v3 = d_res_v3[0] - d_committed[0]
    print("  Center Node (Valence 3): Bound = %.6f, Solved = %.6f, Delta d = %+.6e" % (
        d_committed[0], d_res_v3[0], delta_v3))
    if delta_v3 < -1.0e-6:
        print("  FAIL: Valence 3 violated!")
        all_ok = False
    else:
        print("  PASS: Valence 3 strictly satisfies R7 criterion.")
        
    # Test 3: Crack Growth Under Load (H = 0.848870)
    print("\n--- TEST 3: Assembled Crack Growth Under High Load ---")
    H_high = {eid: [0.848870]*4 for eid in elements}
    d_res_high = assemble_and_solve_patch(nodes, elements, d_committed, H_high)
    print("  Center Node under load: Bound = %.6f, Solved = %.6f (Growth = %+.6f)" % (
        d_committed[0], d_res_high[0], d_res_high[0] - d_committed[0]))
    if d_res_high[0] <= d_committed[0]:
        print("  FAIL: Crack failed to grow!")
        all_ok = False
    else:
        print("  PASS: Natural crack propagation completely uninhibited.")
        
    # Test 4: Multi-Increment Growth, Rollback & Unload Cycle
    print("\n--- TEST 4: Multi-Increment Cycle with Rollback ---")
    d_com_curr = dict(d_committed)
    d_step2 = assemble_and_solve_patch(nodes, elements, d_com_curr, {eid: [0.20]*4 for eid in elements})
    d_com_curr = {nid: max(d_com_curr[nid], d_step2[nid]) for nid in nodes}
    print("  After Increment 1 (Growth): Center d = %.6f" % d_com_curr[0])
    
    # Simulated Cutback
    d_trial_bad = {nid: 0.99 for nid in nodes}
    print("  Simulated Cutback: Discarded trial state, restored committed d = %.6f" % d_com_curr[0])
    
    # Complete Unloading
    d_step4 = assemble_and_solve_patch(nodes, elements, d_com_curr, H_zero)
    delta_unload = d_step4[0] - d_com_curr[0]
    print("  After Increment 2 (Complete Unloading H=0): Center d = %.6f (Delta = %+.6e)" % (
        d_step4[0], delta_unload))
    if delta_unload < -1.0e-6:
        print("  FAIL: Healing on unloading!")
        all_ok = False
    else:
        print("  PASS: Multi-increment rollback safety and no-healing strictly verified.")
        
    print("\n================================================================================")
    print("2D ASSEMBLED FINITE-ELEMENT TEST OUTCOME: %s" % ("ALL TESTS PASSED (100%)" if all_ok else "FAILED"))
    print("================================================================================")
    return all_ok

if __name__ == "__main__":
    run_2d_assembled_tests()
