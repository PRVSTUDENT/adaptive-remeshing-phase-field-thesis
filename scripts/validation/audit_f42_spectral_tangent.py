"""
Algorithmic Tangent Audit for f42_mixed_uel_spectral.for
Performs component-by-component finite difference Jacobian verification
of the implemented Miehe spectral stress update against the implemented tangent.
"""

import numpy as np
import pandas as pd

# Material constants
E_MOD = 210.0      # kN/mm^2 (210 GPa)
E_NU  = 0.3
E_K   = 1.0e-7     # residual stiffness parameter

# Plane strain elastic moduli
C11_0 = E_MOD * (1.0 - E_NU) / ((1.0 + E_NU) * (1.0 - 2.0 * E_NU))
C12_0 = E_MOD * E_NU / ((1.0 + E_NU) * (1.0 - 2.0 * E_NU))
C22_0 = C11_0
C33_0 = E_MOD / (2.0 * (1.0 + E_NU))

def compute_stress_spectral(strain, d_val):
    """
    Exact reproduction of stress calculation in f42_mixed_uel_spectral.for
    strain = [eps11, eps22, gamma12]
    """
    e11 = strain[0]
    e22 = strain[1]
    e12 = 0.5 * strain[2]
    
    deg = (1.0 - d_val)**2 + E_K
    
    # Trace split
    tr_e = e11 + e22
    if tr_e > 0.0:
        tr_pos = tr_e
        tr_neg = 0.0
    else:
        tr_pos = 0.0
        tr_neg = tr_e
        
    # Mohr circle / principal strains
    e_mean = 0.5 * (e11 + e22)
    r_mohr = np.sqrt((0.5 * (e11 - e22))**2 + e12**2)
    e_pr1 = e_mean + r_mohr
    e_pr2 = e_mean - r_mohr
    
    # Positive / negative principal strains
    if e_pr1 > 0.0:
        e1_pos = e_pr1
        e1_neg = 0.0
    else:
        e1_pos = 0.0
        e1_neg = e_pr1
        
    if e_pr2 > 0.0:
        e2_pos = e_pr2
        e2_neg = 0.0
    else:
        e2_pos = 0.0
        e2_neg = e_pr2
        
    # Spectral projectors
    if r_mohr < 1.0e-14:
        c2 = 1.0
        s2 = 0.0
        cs = 0.0
    else:
        c2 = 0.5 * (1.0 + (e11 - e22) / (2.0 * r_mohr))
        s2 = 0.5 * (1.0 - (e11 - e22) / (2.0 * r_mohr))
        cs = 0.5 * e12 / r_mohr
        
    # Strain tensors
    eps_p11 = e1_pos * c2 + e2_pos * s2
    eps_p22 = e1_pos * s2 + e2_pos * c2
    eps_p12 = (e1_pos - e2_pos) * cs
    
    eps_m11 = e1_neg * c2 + e2_neg * s2
    eps_m22 = e1_neg * s2 + e2_neg * c2
    eps_m12 = (e1_neg - e2_neg) * cs
    
    # Stress tensors
    sig_p11 = C12_0 * tr_pos + 2.0 * C33_0 * eps_p11
    sig_p22 = C12_0 * tr_pos + 2.0 * C33_0 * eps_p22
    sig_p12 = 2.0 * C33_0 * eps_p12
    
    sig_m11 = C12_0 * tr_neg + 2.0 * C33_0 * eps_m11
    sig_m22 = C12_0 * tr_neg + 2.0 * C33_0 * eps_m22
    sig_m12 = 2.0 * C33_0 * eps_m12
    
    # Degraded Cauchy stress
    stress = np.zeros(3)
    stress[0] = deg * sig_p11 + sig_m11
    stress[1] = deg * sig_p22 + sig_m22
    stress[2] = deg * sig_p12 + sig_m12
    
    return stress

def compute_implemented_tangent(strain, d_val):
    """
    Exact reproduction of D_ELAS calculation in f42_mixed_uel_spectral.for
    """
    e11 = strain[0]
    e22 = strain[1]
    e12 = 0.5 * strain[2]
    
    deg = (1.0 - d_val)**2 + E_K
    
    tr_e = e11 + e22
    e_mean = 0.5 * (e11 + e22)
    r_mohr = np.sqrt((0.5 * (e11 - e22))**2 + e12**2)
    e_pr1 = e_mean + r_mohr
    e_pr2 = e_mean - r_mohr
    
    if r_mohr < 1.0e-14:
        c2 = 1.0
        s2 = 0.0
        cs = 0.0
    else:
        c2 = 0.5 * (1.0 + (e11 - e22) / (2.0 * r_mohr))
        s2 = 0.5 * (1.0 - (e11 - e22) / (2.0 * r_mohr))
        cs = 0.5 * e12 / r_mohr
        
    if e_pr1 > 0.0:
        g1 = deg
    else:
        g1 = 1.0
        
    if e_pr2 > 0.0:
        g2 = deg
    else:
        g2 = 1.0
        
    if tr_e > 0.0:
        g_vol = deg
    else:
        g_vol = 1.0
        
    dstar11 = C12_0 * g_vol + 2.0 * C33_0 * g1
    dstar22 = C12_0 * g_vol + 2.0 * C33_0 * g2
    dstar12 = C12_0 * g_vol
    if r_mohr > 1.0e-14:
        dstar33 = C33_0 * (g1 * e_pr1 - g2 * e_pr2) / (2.0 * r_mohr)
    else:
        dstar33 = C33_0 * g1
        
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

def compute_numerical_jacobian(strain, d_val, h=1.0e-7):
    """
    Central finite difference Jacobian: J_ij = d(sigma_i) / d(strain_j)
    """
    j_num = np.zeros((3, 3))
    for j in range(3):
        strain_p = np.copy(strain)
        strain_m = np.copy(strain)
        strain_p[j] += h
        strain_m[j] -= h
        
        sig_p = compute_stress_spectral(strain_p, d_val)
        sig_m = compute_stress_spectral(strain_m, d_val)
        
        j_num[:, j] = (sig_p - sig_m) / (2.0 * h)
    return j_num

def run_perturbation_convergence(strain, d_val):
    """
    Check convergence of numerical Jacobian across perturbation step sizes
    """
    h_list = [1.0e-3, 1.0e-4, 1.0e-5, 1.0e-6, 1.0e-7, 1.0e-8, 1.0e-9, 1.0e-10]
    j_ref = compute_numerical_jacobian(strain, d_val, h=1.0e-7)
    errors = []
    for h in h_list:
        j_h = compute_numerical_jacobian(strain, d_val, h=h)
        err = np.linalg.norm(j_h - j_ref, 'fro')
        errors.append({'h': h, 'err_fro_vs_ref': err})
    return pd.DataFrame(errors)

def audit_state(name, strain, d_val):
    d_impl = compute_implemented_tangent(strain, d_val)
    j_num  = compute_numerical_jacobian(strain, d_val, h=1.0e-7)
    
    diff = d_impl - j_num
    max_abs_err = np.max(np.abs(diff))
    fro_norm_diff = np.linalg.norm(diff, 'fro')
    fro_norm_j = np.linalg.norm(j_num, 'fro')
    rel_err_fro = fro_norm_diff / fro_norm_j * 100.0 if fro_norm_j > 0 else 0.0
    
    # Symmetry checks
    sym_err_impl = np.linalg.norm(d_impl - d_impl.T, 'fro')
    sym_err_num  = np.linalg.norm(j_num - j_num.T, 'fro')
    
    # Condition numbers
    cond_impl = np.linalg.cond(d_impl)
    cond_num  = np.linalg.cond(j_num)
    
    # Eigenvalues
    eig_impl = np.linalg.eigvalsh(0.5 * (d_impl + d_impl.T))
    eig_num  = np.linalg.eigvalsh(0.5 * (j_num + j_num.T))
    
    print(f"\n================================================================================")
    print(f"STATE: {name}")
    print(f"Strain eps: [{strain[0]:.6e}, {strain[1]:.6e}, {strain[2]:.6e}], Damage d: {d_val:.4f}")
    
    e11, e22, e12 = strain[0], strain[1], 0.5*strain[2]
    r_mohr = np.sqrt((0.5*(e11-e22))**2 + e12**2)
    e_mean = 0.5*(e11+e22)
    e_pr1, e_pr2 = e_mean + r_mohr, e_mean - r_mohr
    print(f"Principal Strains: eps_1 = {e_pr1:+.6e}, eps_2 = {e_pr2:+.6e}, Tr(eps) = {e11+e22:+.6e}")
    print(f"--------------------------------------------------------------------------------")
    print("Implemented Tangent D_impl [kN/mm^2]:")
    print(np.array2string(d_impl, precision=4, suppress_small=False))
    print("\nNumerical Jacobian J_num = d(sigma)/d(eps) [kN/mm^2]:")
    print(np.array2string(j_num, precision=4, suppress_small=False))
    print("\nDifference Matrix (D_impl - J_num) [kN/mm^2]:")
    print(np.array2string(diff, precision=4, suppress_small=False))
    print(f"\nMax Absolute Error:          {max_abs_err:.6e} kN/mm^2")
    print(f"Relative Frobenius Error:    {rel_err_fro:.4f}%")
    print(f"Symmetry Norm (D_impl - D^T): {sym_err_impl:.6e}")
    print(f"Symmetry Norm (J_num - J^T):  {sym_err_num:.6e}")
    print(f"Condition Number kappa:      D_impl = {cond_impl:.4e}, J_num = {cond_num:.4e}")
    print(f"Eigenvalues:                 D_impl = {eig_impl}, J_num = {eig_num}")
    
    return {
        'name': name,
        'strain': strain,
        'd_val': d_val,
        'eps_pr1': e_pr1,
        'eps_pr2': e_pr2,
        'max_abs_err': max_abs_err,
        'rel_err_fro': rel_err_fro,
        'sym_err_impl': sym_err_impl,
        'sym_err_num': sym_err_num,
        'cond_impl': cond_impl,
        'cond_num': cond_num,
        'd_impl': d_impl,
        'j_num': j_num,
        'diff': diff
    }

if __name__ == '__main__':
    print("================================================================================")
    print("FINITE-DIFFERENCE AUDIT OF ALGORITHMIC TANGENT IN f42_mixed_uel_spectral.for")
    print("================================================================================")
    
    states = [
        ("Case (i): Pure Biaxial/Uniaxial Tension (eps1>0, eps2>0, d=0.5)", np.array([0.004, 0.008, 0.0]), 0.5),
        ("Case (i-b): Pure Tension with Damage d=0.9", np.array([0.002, 0.007, 0.0]), 0.9),
        ("Case (ii): Pure Compression (eps1<0, eps2<0, d=0.5)", np.array([-0.004, -0.008, 0.0]), 0.5),
        ("Case (ii-b): Pure Compression with Damage d=0.9", np.array([-0.003, -0.006, 0.0]), 0.9),
        ("Case (iii): Mixed-Sign Principal Strains (eps1>0, eps2<0, gamma=0, d=0.5)", np.array([-0.003, 0.007, 0.0]), 0.5),
        ("Case (iv): Shear-Dominated Mixed State (eps11=0.002, eps22=-0.001, gamma=0.008, d=0.5)", np.array([0.002, -0.001, 0.008]), 0.5),
        ("Case (iv-b): Pure Shear (eps11=0, eps22=0, gamma=0.008, d=0.5)", np.array([0.0, 0.0, 0.008]), 0.5),
        ("Case (v): Representative Crack-Tip State Near Peak (eps11=-0.002, eps22=0.012, gamma=0.003, d=0.85)", np.array([-0.002, 0.012, 0.003]), 0.85),
        ("Case (v-b): Crack-Tip Softening State (eps11=-0.004, eps22=0.025, gamma=0.005, d=0.95)", np.array([-0.004, 0.025, 0.005]), 0.95),
    ]
    
    results = []
    for name, strain, d_val in states:
        res = audit_state(name, strain, d_val)
        results.append(res)
        
    print("\n================================================================================")
    print("PERTURBATION STEP-SIZE CONVERGENCE CHECK (Case iv)")
    print("================================================================================")
    df_conv = run_perturbation_convergence(np.array([0.002, -0.001, 0.008]), 0.5)
    print(df_conv.to_string(index=False))
    
    print("\n================================================================================")
    print("SUMMARY OF TANGENT CONSISTENCY AUDIT")
    print("================================================================================")
    summary_data = []
    for r in results:
        summary_data.append({
            'Case': r['name'].split(':')[0],
            'd': r['d_val'],
            'Max |Err| [kN/mm^2]': f"{r['max_abs_err']:.4e}",
            'Rel Fro Err (%)': f"{r['rel_err_fro']:.4f}%",
            'D_impl Symm': f"{r['sym_err_impl']:.2e}",
            'J_num Symm': f"{r['sym_err_num']:.2e}",
            'kappa(D_impl)': f"{r['cond_impl']:.2e}",
            'kappa(J_num)': f"{r['cond_num']:.2e}"
        })
    print(pd.DataFrame(summary_data).to_string(index=False))
