"""
Full UEL Residual and Jacobian Structure Audit for f42_mixed_uel_spectral.for
Audits:
1. JTYPE 1: R_d(d), K_dd = -d(R_d)/d(d) (4x4)
2. JTYPE 2: R_u(u), K_uu = -d(R_u)/d(u) (8x8)
3. Off-diagonal coupled blocks: K_ud = -d(R_u)/d(d) (8x4), K_du = -d(R_d)/d(u) (4x8)
4. Evaluates representative near-peak and early-softening crack-tip element states.
"""

import numpy as np
import pandas as pd

# Benchmark Material Parameters
E_MOD = 210.0          # kN/mm^2 (210 GPa)
E_NU  = 0.3
E_GC  = 2.7e-3         # kN/mm (2.7 N/mm)
E_L0  = 0.0075         # mm (7.5 um)
E_K   = 1.0e-7         # residual stiffness parameter

# Plane strain elastic moduli
C11_0 = E_MOD * (1.0 - E_NU) / ((1.0 + E_NU) * (1.0 - 2.0 * E_NU))
C12_0 = E_MOD * E_NU / ((1.0 + E_NU) * (1.0 - 2.0 * E_NU))
C22_0 = C11_0
C33_0 = E_MOD / (2.0 * (1.0 + E_NU))

# Gauss quadrature (2x2)
XG4 = np.array([-1.0/np.sqrt(3.0),  1.0/np.sqrt(3.0), 1.0/np.sqrt(3.0), -1.0/np.sqrt(3.0)])
YG4 = np.array([-1.0/np.sqrt(3.0), -1.0/np.sqrt(3.0), 1.0/np.sqrt(3.0),  1.0/np.sqrt(3.0)])
W4  = np.array([1.0, 1.0, 1.0, 1.0])

def shape_functions(xi, eta):
    N = 0.25 * np.array([
        (1.0 - xi) * (1.0 - eta),
        (1.0 + xi) * (1.0 - eta),
        (1.0 + xi) * (1.0 + eta),
        (1.0 - xi) * (1.0 + eta)
    ])
    dN_dxi = 0.25 * np.array([
        [-(1.0 - eta),  (1.0 - eta),  (1.0 + eta), -(1.0 + eta)],
        [-(1.0 - xi),  -(1.0 + xi),   (1.0 + xi),   (1.0 - xi)]
    ])
    return N, dN_dxi

def compute_element_geometry(coords):
    gp_geom = []
    for kpt in range(4):
        xi, eta, wt = XG4[kpt], YG4[kpt], W4[kpt]
        N, dN_local = shape_functions(xi, eta)
        
        jac = dN_local @ coords.T
        detj = np.linalg.det(jac)
        invj = np.linalg.inv(jac)
        cjac = detj * wt
        
        dN_global = invj @ dN_local
        
        B_u = np.zeros((3, 8))
        for i in range(4):
            B_u[0, 2*i]   = dN_global[0, i]
            B_u[1, 2*i+1] = dN_global[1, i]
            B_u[2, 2*i]   = dN_global[1, i]
            B_u[2, 2*i+1] = dN_global[0, i]
            
        B_d = dN_global
        
        gp_geom.append({
            'N': N,
            'B_u': B_u,
            'B_d': B_d,
            'cjac': cjac
        })
    return gp_geom

def compute_stress_spectral_pt(strain, d_val):
    e11, e22, e12 = strain[0], strain[1], 0.5 * strain[2]
    deg = (1.0 - d_val)**2 + E_K
    
    tr_e = e11 + e22
    tr_pos = max(tr_e, 0.0)
    tr_neg = min(tr_e, 0.0)
    
    e_mean = 0.5 * (e11 + e22)
    r_mohr = np.sqrt((0.5 * (e11 - e22))**2 + e12**2)
    e_pr1 = e_mean + r_mohr
    e_pr2 = e_mean - r_mohr
    
    e1_pos = max(e_pr1, 0.0)
    e1_neg = min(e_pr1, 0.0)
    e2_pos = max(e_pr2, 0.0)
    e2_neg = min(e_pr2, 0.0)
    
    if r_mohr < 1.0e-14:
        c2, s2, cs = 1.0, 0.0, 0.0
    else:
        c2 = 0.5 * (1.0 + (e11 - e22) / (2.0 * r_mohr))
        s2 = 0.5 * (1.0 - (e11 - e22) / (2.0 * r_mohr))
        cs = 0.5 * e12 / r_mohr
        
    eps_p11 = e1_pos * c2 + e2_pos * s2
    eps_p22 = e1_pos * s2 + e2_pos * c2
    eps_p12 = (e1_pos - e2_pos) * cs
    
    eps_m11 = e1_neg * c2 + e2_neg * s2
    eps_m22 = e1_neg * s2 + e2_neg * c2
    eps_m12 = (e1_neg - e2_neg) * cs
    
    sig_p11 = C12_0 * tr_pos + 2.0 * C33_0 * eps_p11
    sig_p22 = C12_0 * tr_pos + 2.0 * C33_0 * eps_p22
    sig_p12 = 2.0 * C33_0 * eps_p12
    
    sig_m11 = C12_0 * tr_neg + 2.0 * C33_0 * eps_m11
    sig_m22 = C12_0 * tr_neg + 2.0 * C33_0 * eps_m22
    sig_m12 = 2.0 * C33_0 * eps_m12
    
    stress = np.zeros(3)
    stress[0] = deg * sig_p11 + sig_m11
    stress[1] = deg * sig_p22 + sig_m22
    stress[2] = deg * sig_p12 + sig_m12
    
    psi_plus = 0.5 * C12_0 * (tr_pos**2) + C33_0 * (e1_pos**2 + e2_pos**2)
    return stress, psi_plus

def compute_tangent_d_elas(strain, d_val):
    e11, e22, e12 = strain[0], strain[1], 0.5 * strain[2]
    deg = (1.0 - d_val)**2 + E_K
    
    tr_e = e11 + e22
    e_mean = 0.5 * (e11 + e22)
    r_mohr = np.sqrt((0.5 * (e11 - e22))**2 + e12**2)
    e_pr1 = e_mean + r_mohr
    e_pr2 = e_mean - r_mohr
    
    if r_mohr < 1.0e-14:
        c2, s2, cs = 1.0, 0.0, 0.0
    else:
        c2 = 0.5 * (1.0 + (e11 - e22) / (2.0 * r_mohr))
        s2 = 0.5 * (1.0 - (e11 - e22) / (2.0 * r_mohr))
        cs = 0.5 * e12 / r_mohr
        
    g1 = deg if e_pr1 > 0.0 else 1.0
    g2 = deg if e_pr2 > 0.0 else 1.0
    g_vol = deg if tr_e > 0.0 else 1.0
    
    dstar11 = C12_0 * g_vol + 2.0 * C33_0 * g1
    dstar22 = C12_0 * g_vol + 2.0 * C33_0 * g2
    dstar12 = C12_0 * g_vol
    dstar33 = C33_0 * (g1 * e_pr1 - g2 * e_pr2) / (2.0 * r_mohr) if r_mohr > 1.0e-14 else C33_0 * g1
    
    a11 = dstar11 * c2 + dstar12 * s2
    a12 = dstar11 * s2 + dstar12 * c2
    a13 = (dstar11 - dstar12) * cs
    a21 = dstar12 * c2 + dstar22 * s2
    a22 = dstar12 * s2 + dstar22 * c2
    a23 = (dstar12 - dstar22) * cs
    a31 = -2.0 * dstar33 * cs
    a32 =  2.0 * dstar33 * cs
    a33 = dstar33 * (c2 - s2)
    
    d_elas = np.zeros((3, 3))
    d_elas[0, 0] = c2 * a11 + s2 * a21 - 2.0 * cs * a31
    d_elas[0, 1] = c2 * a12 + s2 * a22 - 2.0 * cs * a32
    d_elas[0, 2] = c2 * a13 + s2 * a23 - 2.0 * cs * a33
    d_elas[1, 0] = d_elas[0, 1]
    d_elas[1, 1] = s2 * a12 + c2 * a22 + 2.0 * cs * a32
    d_elas[1, 2] = s2 * a13 + c2 * a23 + 2.0 * cs * a33
    d_elas[2, 0] = d_elas[0, 2]
    d_elas[2, 1] = d_elas[1, 2]
    d_elas[2, 2] = cs * a13 - cs * a23 + (c2 - s2) * a33
    return d_elas

def evaluate_jtype1_phase_element(gp_geom, d_vec, hist_gp):
    amatrx_dd = np.zeros((4, 4))
    rhs_d = np.zeros(4)
    
    for kpt in range(4):
        g = gp_geom[kpt]
        N = g['N']
        B_d = g['B_d']
        cjac = g['cjac']
        hist = hist_gp[kpt]
        
        bdb = B_d.T @ B_d
        amatrx_dd += cjac * (
            (E_GC * E_L0) * bdb +
            (E_GC / E_L0 + 2.0 * hist) * np.outer(N, N)
        )
        rhs_d += cjac * 2.0 * hist * N
        
    rhs_d -= amatrx_dd @ d_vec
    return rhs_d, amatrx_dd

def evaluate_jtype2_mech_element(gp_geom, u_vec, d_avg):
    amatrx_uu = np.zeros((8, 8))
    f_int = np.zeros(8)
    
    for kpt in range(4):
        g = gp_geom[kpt]
        B_u = g['B_u']
        cjac = g['cjac']
        
        strain = B_u @ u_vec
        stress, _ = compute_stress_spectral_pt(strain, d_avg)
        d_elas = compute_tangent_d_elas(strain, d_avg)
        
        f_int += cjac * (B_u.T @ stress)
        amatrx_uu += cjac * (B_u.T @ d_elas @ B_u)
        
    rhs_u = -f_int
    return rhs_u, amatrx_uu

def build_kinematic_nodal_displacements(coords, e11, e22, gamma12):
    x0 = np.mean(coords[0, :])
    y0 = np.mean(coords[1, :])
    u_vec = np.zeros(8)
    for i in range(4):
        dx = coords[0, i] - x0
        dy = coords[1, i] - y0
        u_vec[2*i]   = e11 * dx + 0.5 * gamma12 * dy
        u_vec[2*i+1] = e22 * dy + 0.5 * gamma12 * dx
    return u_vec

def audit_element_level_jacobians(coords, u_vec, d_vec, h_eps=1.0e-7):
    gp_geom = compute_element_geometry(coords)
    d_avg = np.mean(d_vec)
    
    # Compute GP history from current u_vec
    hist_gp = np.zeros(4)
    for kpt in range(4):
        g = gp_geom[kpt]
        strain = g['B_u'] @ u_vec
        _, psi_plus = compute_stress_spectral_pt(strain, d_avg)
        hist_gp[kpt] = psi_plus
        
    # 1. JTYPE 1 Phase element audit (K_dd = -d(RHS_d)/d(d))
    rhs_d, amatrx_dd = evaluate_jtype1_phase_element(gp_geom, d_vec, hist_gp)
    k_dd_num = np.zeros((4, 4))
    for j in range(4):
        d_p = np.copy(d_vec)
        d_m = np.copy(d_vec)
        d_p[j] += h_eps
        d_m[j] -= h_eps
        rhs_p, _ = evaluate_jtype1_phase_element(gp_geom, d_p, hist_gp)
        rhs_m, _ = evaluate_jtype1_phase_element(gp_geom, d_m, hist_gp)
        k_dd_num[:, j] = -(rhs_p - rhs_m) / (2.0 * h_eps)
        
    diff_dd = amatrx_dd - k_dd_num
    max_err_dd = np.max(np.abs(diff_dd))
    rel_err_dd = np.linalg.norm(diff_dd, 'fro') / np.linalg.norm(k_dd_num, 'fro') * 100.0
    
    # 2. JTYPE 2 Mechanical element audit (K_uu = -d(RHS_u)/d(u))
    rhs_u, amatrx_uu = evaluate_jtype2_mech_element(gp_geom, u_vec, d_avg)
    k_uu_num = np.zeros((8, 8))
    for j in range(8):
        u_p = np.copy(u_vec)
        u_m = np.copy(u_vec)
        u_p[j] += h_eps
        u_m[j] -= h_eps
        rhs_p, _ = evaluate_jtype2_mech_element(gp_geom, u_p, d_avg)
        rhs_m, _ = evaluate_jtype2_mech_element(gp_geom, u_m, d_avg)
        k_uu_num[:, j] = -(rhs_p - rhs_m) / (2.0 * h_eps)
        
    diff_uu = amatrx_uu - k_uu_num
    max_err_uu = np.max(np.abs(diff_uu))
    rel_err_uu = np.linalg.norm(diff_uu, 'fro') / np.linalg.norm(k_uu_num, 'fro') * 100.0
    
    # 3. Off-diagonal coupled block K_ud = -d(RHS_u)/d(d) (8x4)
    k_ud_num = np.zeros((8, 4))
    for j in range(4):
        d_p = np.copy(d_vec)
        d_m = np.copy(d_vec)
        d_p[j] += h_eps
        d_m[j] -= h_eps
        d_avg_p = np.mean(d_p)
        d_avg_m = np.mean(d_m)
        rhs_p, _ = evaluate_jtype2_mech_element(gp_geom, u_vec, d_avg_p)
        rhs_m, _ = evaluate_jtype2_mech_element(gp_geom, u_vec, d_avg_m)
        k_ud_num[:, j] = -(rhs_p - rhs_m) / (2.0 * h_eps)
        
    # 4. Off-diagonal coupled block K_du = -d(RHS_d)/d(u) (4x8) [when H is active]
    k_du_num = np.zeros((4, 8))
    for j in range(8):
        u_p = np.copy(u_vec)
        u_m = np.copy(u_vec)
        u_p[j] += h_eps
        u_m[j] -= h_eps
        
        hist_p = np.zeros(4)
        hist_m = np.zeros(4)
        for kpt in range(4):
            g = gp_geom[kpt]
            s_p = g['B_u'] @ u_p
            s_m = g['B_u'] @ u_m
            _, psi_p = compute_stress_spectral_pt(s_p, d_avg)
            _, psi_m = compute_stress_spectral_pt(s_m, d_avg)
            hist_p[kpt] = psi_p
            hist_m[kpt] = psi_m
            
        rhs_p, _ = evaluate_jtype1_phase_element(gp_geom, d_vec, hist_p)
        rhs_m, _ = evaluate_jtype1_phase_element(gp_geom, d_vec, hist_m)
        k_du_num[:, j] = -(rhs_p - rhs_m) / (2.0 * h_eps)
        
    return {
        'max_err_dd': max_err_dd,
        'rel_err_dd': rel_err_dd,
        'max_err_uu': max_err_uu,
        'rel_err_uu': rel_err_uu,
        'amatrx_dd': amatrx_dd,
        'k_dd_num': k_dd_num,
        'amatrx_uu': amatrx_uu,
        'k_uu_num': k_uu_num,
        'k_ud_num': k_ud_num,
        'k_du_num': k_du_num,
        'norm_k_ud': np.linalg.norm(k_ud_num, 'fro'),
        'norm_k_du': np.linalg.norm(k_du_num, 'fro'),
        'norm_k_uu': np.linalg.norm(amatrx_uu, 'fro'),
        'norm_k_dd': np.linalg.norm(amatrx_dd, 'fro')
    }

if __name__ == '__main__':
    print("================================================================================")
    print("FULL UEL RESIDUAL & JACOBIAN STRUCTURE AUDIT: f42_mixed_uel_spectral.for")
    print("================================================================================")
    
    h_elem = 0.0030
    coords = np.array([
        [0.5000, 0.5030, 0.5030, 0.5000],
        [0.5000, 0.5000, 0.5030, 0.5030]
    ])
    
    # State 1: Elastic Pre-damage (eps11=-0.0015, eps22=0.0050, gamma=0.0005, d=0.05)
    u_elastic = build_kinematic_nodal_displacements(coords, -0.0015, 0.0050, 0.0005)
    d_elastic = np.array([0.05, 0.05, 0.05, 0.05])
    
    # State 2: Near Peak Crack-Tip State (eps11=-0.0020, eps22=0.0120, gamma=0.0030, d=0.85)
    u_peak = build_kinematic_nodal_displacements(coords, -0.0020, 0.0120, 0.0030)
    d_peak = np.array([0.88, 0.82, 0.82, 0.88])
    
    # State 3: Post-Peak Softening Localization State (eps11=-0.0040, eps22=0.0250, gamma=0.0050, d=0.95)
    u_soft = build_kinematic_nodal_displacements(coords, -0.0040, 0.0250, 0.0050)
    d_soft = np.array([0.98, 0.94, 0.94, 0.98])
    
    test_cases = [
        ("State 1: Elastic Pre-Damage (d ~ 0.05)", u_elastic, d_elastic),
        ("State 2: Near-Peak Localization (d ~ 0.85)", u_peak, d_peak),
        ("State 3: Post-Peak Softening (d ~ 0.95)", u_soft, d_soft)
    ]
    
    results = []
    for name, u_v, d_v in test_cases:
        res = audit_element_level_jacobians(coords, u_v, d_v)
        results.append((name, res))
        
        print(f"\n--------------------------------------------------------------------------------")
        print(f"CASE: {name}")
        print(f"--------------------------------------------------------------------------------")
        print(f"JTYPE 1 Phase Jacobian K_dd (4x4):")
        print(f"  Max Absolute Error vs -d(R_d)/d(d): {res['max_err_dd']:.4e} kN/mm")
        print(f"  Relative Frobenius Error:           {res['rel_err_dd']:.6f}%")
        print(f"  Frobenius Norm ||K_dd||_F:          {res['norm_k_dd']:.4e}")
        
        print(f"\nJTYPE 2 Mechanical Jacobian K_uu (8x8):")
        print(f"  Max Absolute Error vs -d(R_u)/d(u): {res['max_err_uu']:.4e} kN/mm")
        print(f"  Relative Frobenius Error:           {res['rel_err_uu']:.6f}%")
        print(f"  Frobenius Norm ||K_uu||_F:          {res['norm_k_uu']:.4e}")
        
        print(f"\nCoupled Off-Diagonal Matrix Norms (Mathematically non-zero vs Implemented Zero):")
        print(f"  Mechanical-Phase Coupling ||K_ud||_F: {res['norm_k_ud']:.4e} kN/mm")
        print(f"  Phase-Mechanical Coupling ||K_du||_F: {res['norm_k_du']:.4e} kN/mm")

    print("\n================================================================================")
    print("SUMMARY COMPARISON TABLE")
    print("================================================================================")
    rows = []
    for name, r in results:
        rows.append({
            'State': name.split(':')[0],
            'Max |Err(K_dd)|': f"{r['max_err_dd']:.2e}",
            'Rel Err(K_dd)': f"{r['rel_err_dd']:.6f}%",
            'Max |Err(K_uu)|': f"{r['max_err_uu']:.2e}",
            'Rel Err(K_uu)': f"{r['rel_err_uu']:.6f}%",
            '||K_ud||_F': f"{r['norm_k_ud']:.2e}",
            '||K_du||_F': f"{r['norm_k_du']:.2e}"
        })
    print(pd.DataFrame(rows).to_string(index=False))
