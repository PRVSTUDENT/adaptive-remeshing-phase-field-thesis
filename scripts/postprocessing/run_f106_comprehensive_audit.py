#!/usr/bin/env python3
"""
Comprehensive Diagnostic Audit for F106:
Top-boundary equation, runtime displacement, and internal-force reconciliation
between M2STATE_FRACFIX_RESTART2R12 and M2STATE_FRACFIX_RESTART1R1R11.
"""

import json
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
R1R11_NODAL_JSON = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389278.mmaster02/M2STATE_RESTART1R1R11_TERMINAL_NODAL_STATE.json"
R1R11_TRANSFER_JSON = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389278.mmaster02/M2STATE_RESTART1R1R11_RESTART2_SOURCE_TRANSFER_ARTIFACT.json"
R1R11_INP = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R11/M2STATE_FRACFIX_RESTART1R1R11.inp"
R1R11_DAT = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389278.mmaster02/M2STATE_FRACFIX_RESTART1R1R11.dat"

R2R12_INP = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R12/M2STATE_FRACFIX_RESTART2R12.inp"
R2R12_DAT = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R12/M2STATE_FRACFIX_RESTART2R12_STEP1.dat"

def parse_inp_mesh_and_sets(inp_path):
    with open(inp_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    nodes = {}
    elements = {} # eid -> (type, [nids])
    node_sets = {}
    element_sets = {}
    
    current_mode = None
    current_set_name = None
    current_el_type = None
    
    for line in lines:
        line_s = line.strip()
        if not line_s or line_s.startswith('**'):
            continue
        if line_s.startswith('*'):
            current_mode = None
            if line_s.startswith('*NODE'):
                current_mode = 'NODE'
            elif line_s.startswith('*ELEMENT'):
                current_mode = 'ELEMENT'
                parts = [p.strip() for p in line_s.split(',')]
                current_el_type = None
                current_set_name = None
                for p in parts:
                    if p.startswith('TYPE='):
                        current_el_type = p.split('=')[1]
                    elif p.startswith('ELSET='):
                        current_set_name = p.split('=')[1]
                if current_set_name and current_set_name not in element_sets:
                    element_sets[current_set_name] = []
            elif line_s.startswith('*NSET'):
                current_mode = 'NSET'
                parts = [p.strip() for p in line_s.split(',')]
                current_set_name = None
                for p in parts:
                    if p.startswith('NSET='):
                        current_set_name = p.split('=')[1]
                if current_set_name not in node_sets:
                    node_sets[current_set_name] = []
            elif line_s.startswith('*ELSET'):
                current_mode = 'ELSET'
                parts = [p.strip() for p in line_s.split(',')]
                current_set_name = None
                for p in parts:
                    if p.startswith('ELSET='):
                        current_set_name = p.split('=')[1]
                if current_set_name not in element_sets:
                    element_sets[current_set_name] = []
            continue
            
        if current_mode == 'NODE':
            parts = [p.strip() for p in line_s.split(',')]
            if len(parts) >= 3:
                nid = int(parts[0])
                x = float(parts[1])
                y = float(parts[2])
                nodes[nid] = (x, y)
        elif current_mode == 'ELEMENT':
            parts = [p.strip() for p in line_s.split(',')]
            if len(parts) >= 2:
                eid = int(parts[0])
                conn = [int(p) for p in parts[1:] if p]
                elements[eid] = (current_el_type, conn)
                if current_set_name:
                    element_sets[current_set_name].append(eid)
        elif current_mode == 'NSET':
            parts = [p.strip() for p in line_s.split(',')]
            for p in parts:
                if p:
                    try:
                        node_sets[current_set_name].append(int(p))
                    except ValueError:
                        pass
        elif current_mode == 'ELSET':
            parts = [p.strip() for p in line_s.split(',')]
            for p in parts:
                if p:
                    try:
                        element_sets[current_set_name].append(int(p))
                    except ValueError:
                        pass
                        
    return nodes, elements, node_sets, element_sets

def parse_dat_nodes(dat_path):
    with open(dat_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    in_table = False
    nodes_data = {}
    for i, l in enumerate(lines):
        if 'THE FOLLOWING TABLE IS PRINTED FOR ALL NODES' in l:
            in_table = True
            continue
        if in_table:
            if 'THE FOLLOWING TABLE' in l or 'MAXIMUM' in l or 'MINIMUM' in l or 'TOTAL' in l:
                break
            parts = l.strip().split()
            if not parts:
                continue
            try:
                nid = int(parts[0])
                vals = [float(p) for p in parts[1:] if not p.isalpha()]
                if len(vals) == 6:
                    u1, u2, u3, rf1, rf2, rf3 = vals
                elif len(vals) >= 7:
                    u1, u2, u3, rf1, rf2, rf3 = vals[-6:]
                elif len(vals) == 2 and nid == 99999:
                    u1, rf1 = vals[0], vals[1]
                    u2, u3, rf2, rf3 = 0.0, 0.0, 0.0, 0.0
                else:
                    continue
                nodes_data[nid] = {
                    'u1': u1, 'u2': u2, 'u3': u3,
                    'rf1': rf1, 'rf2': rf2, 'rf3': rf3
                }
            except ValueError:
                pass
    return nodes_data

# UEL constitutive matrix
def get_plane_strain_stiffness(E, nu, deg):
    fac = E / ((1.0 + nu) * (1.0 - 2.0 * nu))
    C = np.zeros((3, 3))
    C[0, 0] = fac * (1.0 - nu) * deg
    C[1, 1] = C[0, 0]
    C[0, 1] = fac * nu * deg
    C[1, 0] = C[0, 1]
    C[2, 2] = E / (2.0 * (1.0 + nu)) * deg
    return C

def element_ke_and_fint(coords, eltype, u_elem, d_elem, E=210.0, nu=0.3, k_res=1e-7):
    """
    Compute element tangent Ke (8x8 for quad, 6x6 for tri) and fint
    coords: (nnode, 2)
    u_elem: (nnode*2,) [u1_1, u2_1, u1_2, u2_2, ...]
    d_elem: (nnode,) [d_1, d_2, ...]
    """
    nnode = len(coords)
    if nnode == 4: # Quad
        ngp = 4
        g_pts = np.array([
            [-0.577350269189626, -0.577350269189626],
            [ 0.577350269189626, -0.577350269189626],
            [ 0.577350269189626,  0.577350269189626],
            [-0.577350269189626,  0.577350269189626]
        ])
        g_wts = np.array([1.0, 1.0, 1.0, 1.0])
        Ke = np.zeros((8, 8))
        fe = np.zeros(8)
        ip_deg = []
        ip_d = []
        
        for k in range(ngp):
            xi, eta = g_pts[k]
            wt = g_wts[k]
            
            # Shape functions
            N = 0.25 * np.array([
                (1.0 - xi) * (1.0 - eta),
                (1.0 + xi) * (1.0 - eta),
                (1.0 + xi) * (1.0 + eta),
                (1.0 - xi) * (1.0 + eta)
            ])
            
            # Derivatives wrt xi, eta
            dNdxi = 0.25 * np.array([
                [-(1.0 - eta),  (1.0 - eta),  (1.0 + eta), -(1.0 + eta)],
                [-(1.0 - xi),  -(1.0 + xi),   (1.0 + xi),   (1.0 - xi)]
            ])
            
            # Jacobian
            J = dNdxi @ coords
            detJ = J[0, 0] * J[1, 1] - J[0, 1] * J[1, 0]
            if detJ <= 0:
                raise ValueError("Negative Jacobian")
            invJ = np.array([
                [ J[1, 1], -J[0, 1]],
                [-J[1, 0],  J[0, 0]]
            ]) / detJ
            
            dNdx = invJ @ dNdxi # (2, 4)
            
            # Interpolate phase field
            d_gp = float(np.dot(N, d_elem))
            deg = (1.0 - d_gp)**2 + k_res
            ip_deg.append(deg)
            ip_d.append(d_gp)
            
            # Constitutive matrix
            C = get_plane_strain_stiffness(E, nu, deg)
            
            # B matrix (3, 8)
            B = np.zeros((3, 8))
            for i in range(4):
                B[0, 2*i]   = dNdx[0, i]
                B[1, 2*i+1] = dNdx[1, i]
                B[2, 2*i]   = dNdx[1, i]
                B[2, 2*i+1] = dNdx[0, i]
                
            dV = detJ * wt
            Ke += B.T @ C @ B * dV
            
        fe = Ke @ u_elem
        return Ke, fe, ip_d, ip_deg
        
    elif nnode == 3: # Triangle
        ngp = 1
        xi, eta = 1.0/3.0, 1.0/3.0
        wt = 0.5
        
        N = np.array([xi, eta, 1.0 - xi - eta])
        dNdxi = np.array([
            [ 1.0, 0.0, -1.0],
            [ 0.0, 1.0, -1.0]
        ])
        
        J = dNdxi @ coords
        detJ = J[0, 0] * J[1, 1] - J[0, 1] * J[1, 0]
        if detJ <= 0:
            raise ValueError("Negative Jacobian")
        invJ = np.array([
            [ J[1, 1], -J[0, 1]],
            [-J[1, 0],  J[0, 0]]
        ]) / detJ
        
        dNdx = invJ @ dNdxi # (2, 3)
        
        d_gp = float(np.dot(N, d_elem))
        deg = (1.0 - d_gp)**2 + k_res
        
        C = get_plane_strain_stiffness(E, nu, deg)
        
        B = np.zeros((3, 6))
        for i in range(3):
            B[0, 2*i]   = dNdx[0, i]
            B[1, 2*i+1] = dNdx[1, i]
            B[2, 2*i]   = dNdx[1, i]
            B[2, 2*i+1] = dNdx[0, i]
            
        dV = detJ * wt
        Ke = B.T @ C @ B * dV
        fe = Ke @ u_elem
        return Ke, fe, [d_gp], [deg]
    else:
        raise ValueError(f"Unsupported nnode={nnode}")

def run_audit():
    print("==========================================================================")
    print("F106 COMPREHENSIVE RECONCILIATION AUDIT")
    print("==========================================================================")
    
    # 1. Load R2R12 runtime state from authoritative DAT table
    print("\n--- 1. Parsing Authoritative R2R12 DAT Output Table ---")
    r2_nodes = parse_dat_nodes(R2R12_DAT)
    r2_inp_nodes, r2_inp_elems, r2_inp_nsets, r2_inp_elsets = parse_inp_mesh_and_sets(R2R12_INP)
    
    n_top_ids = sorted(list(set(r2_inp_nsets['N_TOP'])))
    n_bot_ids = sorted(list(set(r2_inp_nsets['N_BOTTOM'])))
    all_node_ids = sorted([nid for nid in r2_inp_nodes.keys() if nid != 99999])
    
    print(f"Total domain nodes: {len(all_node_ids)}, N_TOP: {len(n_top_ids)}, N_BOTTOM: {len(n_bot_ids)}")
    
    # 2. Extract R2R12 top node displacement statistics
    top_u1 = [r2_nodes[nid]['u1'] for nid in n_top_ids]
    top_u2 = [r2_nodes[nid]['u2'] for nid in n_top_ids]
    top_u3 = [r2_nodes[nid]['u3'] for nid in n_top_ids]
    
    bot_u1 = [r2_nodes[nid]['u1'] for nid in n_bot_ids]
    bot_u2 = [r2_nodes[nid]['u2'] for nid in n_bot_ids]
    
    interior_ids = [nid for nid in all_node_ids if nid not in n_top_ids and nid not in n_bot_ids]
    int_u1 = [r2_nodes[nid]['u1'] for nid in interior_ids]
    int_u2 = [r2_nodes[nid]['u2'] for nid in interior_ids]
    
    print("\n--- 2. R2R12 Runtime Nodal Displacement Statistics ---")
    print(f"top_U1_min = {np.min(top_u1):.8f}")
    print(f"top_U1_max = {np.max(top_u1):.8f}")
    print(f"top_U1_mean = {np.mean(top_u1):.8f}")
    print(f"top_U2_min = {np.min(top_u2):.8f}")
    print(f"top_U2_max = {np.max(top_u2):.8f}")
    print(f"top_U2_mean = {np.mean(top_u2):.8f}")
    print(f"top_U2_absmax = {np.max(np.abs(top_u2)):.8f}")
    
    print(f"\nbottom_U1_min = {np.min(bot_u1):.8f}, max = {np.max(bot_u1):.8f}")
    print(f"bottom_U2_min = {np.min(bot_u2):.8f}, max = {np.max(bot_u2):.8f}")
    print(f"interior_U1_min = {np.min(int_u1):.8f}, max = {np.max(int_u1):.8f}")
    print(f"interior_U2_min = {np.min(int_u2):.8f}, max = {np.max(int_u2):.8f}")
    
    # Sample 20 top nodes
    sample_indices = np.linspace(0, len(n_top_ids)-1, 20, dtype=int)
    print("\n--- Sample 20 R2R12 Top Nodes ---")
    print(f"{'NodeID':>8} {'X':>10} {'Y':>10} {'U1':>12} {'U2':>12} {'U3(d)':>12}")
    for idx in sample_indices:
        nid = n_top_ids[idx]
        nd = r2_nodes[nid]
        x, y = r2_inp_nodes[nid]
        print(f"{nid:>8d} {x:>10.4f} {y:>10.4f} {nd['u1']:>12.6f} {nd['u2']:>12.6f} {nd['u3']:>12.6f}")

    # 3. R1R11 terminal state statistics
    print("\n--- 3. Loading R1R11 Terminal State (1389278.mmaster02) ---")
    with open(R1R11_NODAL_JSON) as f:
        r1_state = json.load(f)
    r1_nodes = r1_state['nodes']
    r1_inp_nodes, r1_inp_elems, r1_inp_nsets, r1_inp_elsets = parse_inp_mesh_and_sets(R1R11_INP)
    
    r1_top_ids = sorted(list(set(r1_inp_nsets['N_TOP'])))
    r1_bot_ids = sorted(list(set(r1_inp_nsets['N_BOTTOM'])))
    
    r1_top_u1 = [r1_nodes[str(nid)]['u1'] for nid in r1_top_ids]
    r1_top_u2 = [r1_nodes[str(nid)]['u2'] for nid in r1_top_ids]
    r1_bot_u1 = [r1_nodes[str(nid)]['u1'] for nid in r1_bot_ids]
    r1_bot_u2 = [r1_nodes[str(nid)]['u2'] for nid in r1_bot_ids]
    
    print(f"R1R11_top_U1_min = {np.min(r1_top_u1):.8f}, max = {np.max(r1_top_u1):.8f}, mean = {np.mean(r1_top_u1):.8f}")
    print(f"R1R11_top_U2_min = {np.min(r1_top_u2):.8f}, max = {np.max(r1_top_u2):.8f}, mean = {np.mean(r1_top_u2):.8f}")
    print(f"R1R11_bottom_U1_min = {np.min(r1_bot_u1):.8f}, max = {np.max(r1_bot_u1):.8f}")
    print(f"R1R11_bottom_U2_min = {np.min(r1_bot_u2):.8f}, max = {np.max(r1_bot_u2):.8f}")

    # 4 & 6. Global Mechanical Matrix Assembly & Internal Force Reconstruction
    print("\n--- 4 & 6. Mechanical Stiffness Assembly and Internal Force Reconstruction ---")
    
    # Filter mechanical elements from R2R12
    mech_elements = {}
    for eid, (eltype, conn) in r2_inp_elems.items():
        if eltype in ['U2', 'U4']:
            mech_elements[eid] = (eltype, conn)
            
    print(f"Total R2R12 mechanical elements: {len(mech_elements)}")
    
    # Map node IDs to continuous indices (0 to N-1)
    node_to_idx = {nid: i for i, nid in enumerate(all_node_ids)}
    num_nodes = len(all_node_ids)
    num_dofs = 2 * num_nodes
    
    # Build global vectors: runtime U and phase d
    u_runtime = np.zeros(num_dofs)
    d_runtime = np.zeros(num_nodes)
    
    for nid in all_node_ids:
        idx = node_to_idx[nid]
        nd = r2_nodes[nid]
        u_runtime[2*idx]   = nd['u1']
        u_runtime[2*idx+1] = nd['u2']
        d_runtime[idx]     = nd['u3']
        
    # Assemble global stiffness K_undamaged, K_damaged, and global internal force f_int
    I_list = []
    J_list = []
    V_undam_list = []
    V_dam_list = []
    
    f_int_global = np.zeros(num_dofs)
    
    elem_audit_records = []
    
    for eid, (eltype, conn) in mech_elements.items():
        elem_coords = np.array([r2_inp_nodes[nid] for nid in conn])
        elem_d = np.array([d_runtime[node_to_idx[nid]] for nid in conn])
        elem_u = np.zeros(2 * len(conn))
        for i, nid in enumerate(conn):
            idx = node_to_idx[nid]
            elem_u[2*i]   = u_runtime[2*idx]
            elem_u[2*i+1] = u_runtime[2*idx+1]
            
        # Damaged element solve
        Ke_dam, fe_dam, ip_d, ip_deg = element_ke_and_fint(elem_coords, eltype, elem_u, elem_d)
        
        # Undamaged element solve
        Ke_undam, _, _, _ = element_ke_and_fint(elem_coords, eltype, elem_u, np.zeros_like(elem_d))
        
        # Assemble internal force
        for i, ni in enumerate(conn):
            idi = node_to_idx[ni]
            f_int_global[2*idi]   += fe_dam[2*i]
            f_int_global[2*idi+1] += fe_dam[2*i+1]
            
        # Assemble sparse stiffness
        for i, ni in enumerate(conn):
            idi = node_to_idx[ni]
            for j, nj in enumerate(conn):
                idj = node_to_idx[nj]
                
                I_list.extend([2*idi, 2*idi, 2*idi+1, 2*idi+1])
                J_list.extend([2*idj, 2*idj+1, 2*idj, 2*idj+1])
                
                V_dam_list.extend([
                    Ke_dam[2*i, 2*j], Ke_dam[2*i, 2*j+1],
                    Ke_dam[2*i+1, 2*j], Ke_dam[2*i+1, 2*j+1]
                ])
                V_undam_list.extend([
                    Ke_undam[2*i, 2*j], Ke_undam[2*i, 2*j+1],
                    Ke_undam[2*i+1, 2*j], Ke_undam[2*i+1, 2*j+1]
                ])
                
        elem_audit_records.append({
            'eid': eid,
            'eltype': eltype,
            'conn': conn,
            'coords': elem_coords.tolist(),
            'd_nodes': elem_d.tolist(),
            'ip_d': ip_d,
            'ip_deg': ip_deg,
            'u_nodes': elem_u.tolist(),
            'fe': fe_dam.tolist()
        })

    K_dam = sp.coo_matrix((V_dam_list, (I_list, J_list)), shape=(num_dofs, num_dofs)).tocsr()
    K_undam = sp.coo_matrix((V_undam_list, (I_list, J_list)), shape=(num_dofs, num_dofs)).tocsr()
    
    # Calculate resultant forces from reconstructed f_int
    top_dofs_x = [2*node_to_idx[nid] for nid in n_top_ids]
    top_dofs_y = [2*node_to_idx[nid]+1 for nid in n_top_ids]
    bot_dofs_x = [2*node_to_idx[nid] for nid in n_bot_ids]
    bot_dofs_y = [2*node_to_idx[nid]+1 for nid in n_bot_ids]
    
    rf1_top_reconstructed = np.sum(f_int_global[top_dofs_x])
    rf2_top_reconstructed = np.sum(f_int_global[top_dofs_y])
    rf1_bot_reconstructed = np.sum(f_int_global[bot_dofs_x])
    rf2_bot_reconstructed = np.sum(f_int_global[bot_dofs_y])
    
    # Internal free DOFs residual norm (all DOFs except prescribed top_dofs_x, bot_dofs_x, bot_dofs_y)
    fixed_dofs = set(top_dofs_x + bot_dofs_x + bot_dofs_y)
    free_dofs = [d for d in range(num_dofs) if d not in fixed_dofs]
    
    residual_free = f_int_global[free_dofs]
    residual_norm = np.linalg.norm(residual_free)
    
    print("\n--- 6. Reconstructed Internal Forces from Runtime Displacement Field ---")
    print(f"offline_from_runtime_U_top_resultant_RF1    = {rf1_top_reconstructed:.6f} kN")
    print(f"offline_from_runtime_U_top_resultant_RF2    = {rf2_top_reconstructed:.6f} kN")
    print(f"offline_from_runtime_U_bottom_resultant_RF1 = {rf1_bot_reconstructed:.6f} kN")
    print(f"offline_from_runtime_U_bottom_resultant_RF2 = {rf2_bot_reconstructed:.6f} kN")
    print(f"offline_from_runtime_U_global_residual_norm = {residual_norm:.6e} kN")
    print(f"R2R12 Runtime RP RF1                        = 0.798404 kN")
    print(f"R2R12 Runtime Bottom RF1 Sum                = -0.805496 kN")
    print(f"Discrepancy (Reconstructed Top RF1 vs Runtime RP RF1) = {abs(rf1_top_reconstructed - 0.798404):.6e} kN")

    # 4. Rebuild exact offline R2R12 BVP solve
    # Constraints:
    # 1) Bottom nodes: u1 = 0, u2 = 0
    # 2) Top nodes: u1 = 0.010000 (coupled to single RP DOF), u2 is FREE
    # 3) All other DOFs: FREE
    print("\n--- 4. Solving Exact Offline R2R12 BVP ---")
    
    def solve_bvp(K_mat):
        prescribed_dofs = {}
        for d in top_dofs_x:
            prescribed_dofs[d] = 0.010000
        for d in bot_dofs_x:
            prescribed_dofs[d] = 0.0
        for d in bot_dofs_y:
            prescribed_dofs[d] = 0.0
            
        p_dofs = sorted(list(prescribed_dofs.keys()))
        f_dofs = [d for d in range(num_dofs) if d not in prescribed_dofs]
        
        u_p = np.array([prescribed_dofs[d] for d in p_dofs])
        
        K_ff = K_mat[f_dofs, :][:, f_dofs]
        K_fp = K_mat[f_dofs, :][:, p_dofs]
        
        rhs_f = - K_fp @ u_p
        u_f = spla.spsolve(K_ff, rhs_f)
        
        u_sol = np.zeros(num_dofs)
        for i, d in enumerate(p_dofs):
            u_sol[d] = u_p[i]
        for i, d in enumerate(f_dofs):
            u_sol[d] = u_f[i]
            
        f_react = K_mat @ u_sol
        rf1_top = np.sum(f_react[top_dofs_x])
        rf1_bot = np.sum(f_react[bot_dofs_x])
        return u_sol, rf1_top, rf1_bot
        
    u_sol_undam, rf1_undam, _ = solve_bvp(K_undam)
    u_sol_dam, rf1_dam, _ = solve_bvp(K_dam)
    
    print(f"R2R12_exact_offline_undamaged_RF1 = {rf1_undam:.6f} kN")
    print(f"R2R12_exact_offline_damaged_RF1   = {rf1_dam:.6f} kN")
    print(f"Runtime R2R12 RF1                 = 0.798404 kN")
    rel_err_rf = abs(rf1_dam - 0.798404) / 0.798404
    print(f"Relative error vs runtime RF      = {rel_err_rf:.6e} ({rel_err_rf*100:.4f}%)")

    # 5. Validate offline solution against runtime displacement field
    print("\n--- 5. Offline vs Runtime Displacement Field Error ---")
    u1_runtime = u_runtime[0::2]
    u2_runtime = u_runtime[1::2]
    u1_offline = u_sol_dam[0::2]
    u2_offline = u_sol_dam[1::2]
    
    u1_l2_err = np.linalg.norm(u1_offline - u1_runtime) / np.linalg.norm(u1_runtime)
    u1_max_abs_err = np.max(np.abs(u1_offline - u1_runtime))
    
    u2_l2_err = np.linalg.norm(u2_offline - u2_runtime) / np.linalg.norm(u2_runtime)
    u2_max_abs_err = np.max(np.abs(u2_offline - u2_runtime))
    
    print(f"U1_relative_L2_error = {u1_l2_err:.6e}")
    print(f"U1_max_abs_error     = {u1_max_abs_err:.6e} mm")
    print(f"U2_relative_L2_error = {u2_l2_err:.6e}")
    print(f"U2_max_abs_error     = {u2_max_abs_err:.6e} mm")

    # 7. Element detail samples
    print("\n--- 7. Sample Element Degradation Details ---")
    # Sort elements by max d_nodes
    elem_audit_records.sort(key=lambda r: max(r['d_nodes']), reverse=True)
    print(f"{'ElemID':>8} {'Type':>5} {'Max Nodal d':>12} {'IP d values':>24} {'IP DEG values':>28}")
    for rec in elem_audit_records[:20]:
        ip_d_str = ", ".join([f"{v:.4f}" for v in rec['ip_d']])
        ip_deg_str = ", ".join([f"{v:.4f}" for v in rec['ip_deg']])
        print(f"{rec['eid']:>8d} {rec['eltype']:>5} {max(rec['d_nodes']):>12.4f} [{ip_d_str:>22}] [{ip_deg_str:>26}]")

    # 12. R1R11 Terminal Internal Force Reconstruction
    print("\n--- 12. Reconstructing R1R11 Terminal Internal Force ---")
    with open(R1R11_TRANSFER_JSON) as f:
        r1_transfer = json.load(f)
        
    r1_elem_sdv = r1_transfer['elements']
    r1_all_node_ids = sorted([int(nid) for nid in r1_nodes.keys() if int(nid) != 99999])
    r1_node_to_idx = {nid: i for i, nid in enumerate(r1_all_node_ids)}
    r1_num_dofs = 2 * len(r1_all_node_ids)
    
    r1_u_runtime = np.zeros(r1_num_dofs)
    for nid in r1_all_node_ids:
        idx = r1_node_to_idx[nid]
        r1_u_runtime[2*idx]   = r1_nodes[str(nid)]['u1']
        r1_u_runtime[2*idx+1] = r1_nodes[str(nid)]['u2']
        
    r1_f_int_global = np.zeros(r1_num_dofs)
    sdv14_diffs = []
    
    for eid_s, ip_data in r1_elem_sdv.items():
        eid = int(eid_s)
        eltype, conn = r1_inp_elems[eid]
        elem_coords = np.array([r1_inp_nodes[nid] for nid in conn])
        elem_u = np.zeros(2 * len(conn))
        for i, nid in enumerate(conn):
            idx = r1_node_to_idx[nid]
            elem_u[2*i]   = r1_u_runtime[2*idx]
            elem_u[2*i+1] = r1_u_runtime[2*idx+1]
            
        sdv14_list = [ip_data[ip_key]['SDV14'] for ip_key in sorted(ip_data.keys(), key=lambda x: int(x))]
        d_avg = np.mean(sdv14_list)
        
        for s14 in sdv14_list:
            sdv14_diffs.append(abs(s14 - d_avg))
            
        elem_d_avg = np.full(len(conn), d_avg)
        Ke_r1, fe_r1, _, _ = element_ke_and_fint(elem_coords, eltype, elem_u, elem_d_avg)
        
        for i, ni in enumerate(conn):
            idi = r1_node_to_idx[ni]
            r1_f_int_global[2*idi]   += fe_r1[2*i]
            r1_f_int_global[2*idi+1] += fe_r1[2*i+1]
            
    r1_top_dofs_x = [2*r1_node_to_idx[nid] for nid in r1_top_ids]
    r1_bot_dofs_x = [2*r1_node_to_idx[nid] for nid in r1_bot_ids]
    
    r1_rf1_top = np.sum(r1_f_int_global[r1_top_dofs_x])
    r1_rf1_bot = np.sum(r1_f_int_global[r1_bot_dofs_x])
    
    print(f"R1R11_offline_from_runtime_U_RF1 = {r1_rf1_top:.6f} kN")
    print(f"R1R11_runtime_RF1                = 0.123223 kN")
    r1_rf_rel_err = abs(r1_rf1_top - 0.123223) / 0.123223
    print(f"R1R11 Relative Error             = {r1_rf_rel_err:.6e} ({r1_rf_rel_err*100:.4f}%)")
    print(f"R1R11 Reconstructed Bottom RF1   = {r1_rf1_bot:.6f} kN")

    # 13. SDV14 vs SV_PHASE
    print("\n--- 13. SDV14 vs SV_PHASE Element Average Comparison ---")
    print(f"max_abs(SDV14 - D_AVG)  = {np.max(sdv14_diffs):.6e}")
    print(f"mean_abs(SDV14 - D_AVG) = {np.mean(sdv14_diffs):.6e}")

if __name__ == '__main__':
    run_audit()
