#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_fem_penalty_chattering.py
Coupled FE phase-field test of 1D continuum bar with damage lower bounds.
Simulates the exact Abaqus Newton-Raphson iteration on:
  K_phi * d = F_ext
with active-set constraint d >= d_lower.

Compares:
1. Discontinuous step penalty with gamma = 1e8 (Turn 113)
2. Discontinuous step penalty with calibrated gamma = 1e3 .. 1e4
3. Huber C1-smooth penalty
4. Primal-Dual Active Set (PDAS) with multiplier tracking
"""

import numpy as np

def run_fe_experiment():
    # 20-element 1D mesh along x in [0, 0.05]
    n_elem = 20
    nodes_x = np.linspace(0, 0.05, n_elem + 1)
    n_nodes = len(nodes_x)
    dx = nodes_x[1] - nodes_x[0]
    
    # Material parameters matching Mode-I
    Gc = 0.0027   # kN/mm
    l0 = 0.0075   # mm
    
    # Element stiffness matrix
    # K_elem = int (Gc*l0 * B^T B + (Gc/l0 + 2*H) * N^T N) dx
    # Let H be decaying from crack tip at x = 0.035 to x = 0
    # In wake (x < 0.03), H is low, so unconstrained equilibrium wants d to decrease!
    H_wake = 1.0e-5  # small driving force in wake
    H_tip  = 5.0e-2  # large driving force near tip
    
    # Target d_lower represents transferred damage profile
    # d_lower peaks at x = 0.035 with d = 0.65, decays towards 0 at ends
    d_lower = np.zeros(n_nodes)
    for i, x in enumerate(nodes_x):
        d_lower[i] = 0.65 * np.exp(-((x - 0.035) / 0.01)**2)
        
    print("=== 1D FE PHASE FIELD ACTIVE-SET CONSTRAINT BENCHMARK ===")
    print(f"Nodes: {n_nodes}, dx = {dx:.4e} mm")
    print(f"Max d_lower = {np.max(d_lower):.4f} at x = 0.035 mm")
    
    def assemble_system(d_curr, gamma, pen_type="step", delta=1e-4, active_set=None):
        K_global = np.zeros((n_nodes, n_nodes))
        R_global = np.zeros(n_nodes)
        
        for e in range(n_elem):
            x_mid = 0.5 * (nodes_x[e] + nodes_x[e+1])
            # H depends on position
            H_e = H_tip if abs(x_mid - 0.035) < 0.005 else H_wake
            
            # 1D linear shape functions
            k_diff = (Gc * l0 / dx) * np.array([[1.0, -1.0], [-1.0, 1.0]])
            k_mass = ((Gc / l0 + 2.0 * H_e) * dx / 6.0) * np.array([[2.0, 1.0], [1.0, 2.0]])
            k_elem = k_diff + k_mass
            
            f_elem = (2.0 * H_e * dx / 2.0) * np.array([1.0, 1.0])
            
            # assemble
            for i_loc, i_glob in enumerate([e, e+1]):
                R_global[i_glob] += f_elem[i_loc]
                for j_loc, j_glob in enumerate([e, e+1]):
                    K_global[i_glob, j_glob] += k_elem[i_loc, j_loc]
                    
        # Residual = F_ext - K * d
        R_global = R_global - K_global @ d_curr
        
        # Apply constraint penalty / active set
        active_nodes = []
        for i in range(n_nodes):
            diff = d_lower[i] - d_curr[i]
            if pen_type == "step":
                if diff > 0.0:
                    R_global[i] += gamma * diff
                    K_global[i, i] += gamma
                    active_nodes.append(i)
            elif pen_type == "pdas":
                if active_set is not None and active_set[i]:
                    # Dirichlet-type enforcement of active set
                    R_global[i] += gamma * diff
                    K_global[i, i] += gamma
                    active_nodes.append(i)
            elif pen_type == "huber":
                if diff <= 0.0:
                    pass
                elif diff < delta:
                    pen_force = (gamma / (2.0 * delta)) * (diff ** 2)
                    pen_stiff = (gamma / delta) * diff
                    R_global[i] += pen_force
                    K_global[i, i] += pen_stiff
                    active_nodes.append(i)
                else:
                    pen_force = gamma * (diff - 0.5 * delta)
                    pen_stiff = gamma
                    R_global[i] += pen_force
                    K_global[i, i] += pen_stiff
                    active_nodes.append(i)
                    
        return K_global, R_global, active_nodes

    # --- Run 1: Discontinuous Step Penalty gamma = 1e8 ---
    print("\n--- RUN 1: Discontinuous Step Penalty gamma = 1e8 (Turn 113) ---")
    d_step = np.zeros(n_nodes)
    oscillated = False
    history_nodes = []
    for it in range(1, 25):
        K, R, active = assemble_system(d_step, gamma=1.0e8, pen_type="step")
        dd = np.linalg.solve(K, R)
        d_step += dd
        res_norm = np.linalg.norm(R)
        corr_norm = np.linalg.norm(dd)
        history_nodes.append(active)
        print(f"  Iter {it:2d}: |R| = {res_norm:.4e}, |dd| = {corr_norm:.4e}, active nodes = {len(active)}")
        if it > 3 and history_nodes[-1] == history_nodes[-3] and history_nodes[-1] != history_nodes[-2]:
            oscillated = True
            print(f"  --> CONFIRMED 2-CYCLE CHATTERING: active set toggles between {len(history_nodes[-2])} and {len(history_nodes[-1])} nodes!")
            break
            
    # --- Run 2: Discontinuous Step Penalty gamma = 1e3 ---
    print("\n--- RUN 2: Discontinuous Step Penalty with Calibrated gamma = 1e3 ---")
    d_calib = np.zeros(n_nodes)
    conv_calib = False
    for it in range(1, 25):
        K, R, active = assemble_system(d_calib, gamma=1.0e3, pen_type="step")
        dd = np.linalg.solve(K, R)
        d_calib += dd
        res_norm = np.linalg.norm(R)
        corr_norm = np.linalg.norm(dd)
        print(f"  Iter {it:2d}: |R| = {res_norm:.4e}, |dd| = {corr_norm:.4e}, active nodes = {len(active)}")
        if corr_norm < 1.0e-7 and res_norm < 1.0e-5:
            conv_calib = True
            max_viol = np.max(np.maximum(0.0, d_lower - d_calib))
            print(f"  --> CONVERGED in {it} iters! Max violation = {max_viol:.4e}")
            break

    # --- Run 3: Huber C1-Smooth Regularized Penalty ---
    print("\n--- RUN 3: Huber C1-Smooth Penalty (gamma = 1e4, delta = 1e-4) ---")
    d_huber = np.zeros(n_nodes)
    conv_huber = False
    for it in range(1, 25):
        K, R, active = assemble_system(d_huber, gamma=1.0e4, pen_type="huber", delta=1.0e-4)
        dd = np.linalg.solve(K, R)
        d_huber += dd
        res_norm = np.linalg.norm(R)
        corr_norm = np.linalg.norm(dd)
        print(f"  Iter {it:2d}: |R| = {res_norm:.4e}, |dd| = {corr_norm:.4e}, active nodes = {len(active)}")
        if corr_norm < 1.0e-7 and res_norm < 1.0e-5:
            conv_huber = True
            max_viol = np.max(np.maximum(0.0, d_lower - d_huber))
            print(f"  --> CONVERGED in {it} iters! Max violation = {max_viol:.4e}")
            break

    # --- Run 4: Primal-Dual Active Set (PDAS) ---
    print("\n--- RUN 4: Primal-Dual Active Set (PDAS) ---")
    d_pdas = np.zeros(n_nodes)
    lam_pdas = np.zeros(n_nodes)
    active_set = np.zeros(n_nodes, dtype=bool)
    c_pdas = 1.0e3
    conv_pdas = False
    for it in range(1, 25):
        # Update active set: i in A if d_i - lam_i / c < d_lower_i
        active_set = (d_pdas - lam_pdas / c_pdas) < d_lower
        K, R, active = assemble_system(d_pdas, gamma=1.0e4, pen_type="pdas", active_set=active_set)
        dd = np.linalg.solve(K, R)
        d_pdas += dd
        # Update multiplier: lam_i = - gamma * (d_lower - d_pdas) for active nodes
        lam_pdas = np.where(active_set, - 1.0e4 * (d_lower - d_pdas), 0.0)
        res_norm = np.linalg.norm(R)
        corr_norm = np.linalg.norm(dd)
        print(f"  Iter {it:2d}: |R| = {res_norm:.4e}, |dd| = {corr_norm:.4e}, active nodes = {np.sum(active_set)}")
        if corr_norm < 1.0e-7 and res_norm < 1.0e-5:
            conv_pdas = True
            max_viol = np.max(np.maximum(0.0, d_lower - d_pdas))
            print(f"  --> CONVERGED in {it} iters! Max violation = {max_viol:.4e}")
            break

if __name__ == "__main__":
    run_fe_experiment()
