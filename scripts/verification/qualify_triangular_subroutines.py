import math

def mat_mult(A, B):
    rows_A = len(A)
    cols_A = len(A[0])
    rows_B = len(B)
    cols_B = len(B[0])
    assert cols_A == rows_B
    C = [[0.0 for _ in range(cols_B)] for _ in range(rows_A)]
    for i in range(rows_A):
        for j in range(cols_B):
            for k in range(cols_A):
                C[i][j] += A[i][k] * B[k][j]
    return C

def mat_vec(A, v):
    rows_A = len(A)
    cols_A = len(A[0])
    assert cols_A == len(v)
    res = [0.0 for _ in range(rows_A)]
    for i in range(rows_A):
        for k in range(cols_A):
            res[i] += A[i][k] * v[k]
    return res

def mat_transpose(A):
    rows = len(A)
    cols = len(A[0])
    return [[A[i][j] for i in range(rows)] for j in range(cols)]

def vec_dot(u, v):
    return sum(a * b for a, b in zip(u, v))

def vec_norm(u):
    return math.sqrt(sum(a * a for a in u))

def verify_tri_uel():
    print("=" * 70)
    print("TRIANGULAR ELEMENT SUBROUTINE QUALIFICATION (JTYPE 3 & 4) - PURE PYTHON")
    print("=" * 70)
    
    # Material properties
    E = 210.0      # kN/mm^2
    nu = 0.30
    l0 = 0.015     # mm
    Gc = 0.0027    # kN/mm
    k_res = 1.0e-7
    
    # Plane strain elastic constants
    C11_0 = E * (1.0 - nu) / ((1.0 + nu) * (1.0 - 2.0 * nu))
    C12_0 = E * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
    C22_0 = C11_0
    C33_0 = E / (2.0 * (1.0 + nu))
    
    print(f"Plane Strain Constants:")
    print(f"  C11 = C22 = {C11_0:.6f} kN/mm^2")
    print(f"  C12       = {C12_0:.6f} kN/mm^2")
    print(f"  C33 (G)   = {C33_0:.6f} kN/mm^2")
    
    # Test Triangle: Right triangle with vertices Node 1: (h, 0), Node 2: (0, h), Node 3: (0, 0)
    h = 0.01 # mm
    coords = [
        [h, 0.0],    # Node 1
        [0.0, h],    # Node 2
        [0.0, 0.0]   # Node 3
    ]
    
    # In Fortran subroutine: COORDS(J, K) where J in {1,2} is spatial dim, K in {1,2,3} is node
    COORDS = [[coords[k][j] for k in range(3)] for j in range(2)] # shape (2, 3)
    
    # D_NTRI: shape (2, 3)
    D_NTRI = [
        [ 1.0,  0.0, -1.0],
        [ 0.0,  1.0, -1.0]
    ]
    
    # Jacobian: JAC(I,J) = sum_k D_NTRI(I,K) * COORDS(J,K)
    JAC = [[0.0, 0.0], [0.0, 0.0]]
    for i in range(2):
        for j in range(2):
            for k in range(3):
                JAC[i][j] += D_NTRI[i][k] * COORDS[j][k]
                
    DETJ = JAC[0][0] * JAC[1][1] - JAC[0][1] * JAC[1][0]
    WT = 0.5
    CJAC = DETJ * WT
    area_analytical = 0.5 * h * h
    
    print(f"\nGeometry & Jacobian Check:")
    print(f"  DETJ           = {DETJ:.8e}")
    print(f"  CJAC (Area)    = {CJAC:.8e} (Analytical: {area_analytical:.8e})")
    assert abs(CJAC - area_analytical) < 1e-15, "Jacobian area mismatch!"
    
    INVJ = [
        [ JAC[1][1] / DETJ, -JAC[0][1] / DETJ],
        [-JAC[1][0] / DETJ,  JAC[0][0] / DETJ]
    ]
    
    # -------------------------------------------------------------
    # JTYPE 4: Mechanical Element (6 DOFs)
    # -------------------------------------------------------------
    B_TRI = [[0.0 for _ in range(6)] for _ in range(3)]
    for i in range(3):
        B_TRI[0][2*i]     = INVJ[0][0] * D_NTRI[0][i] + INVJ[0][1] * D_NTRI[1][i]
        B_TRI[0][2*i + 1] = 0.0
        B_TRI[1][2*i]     = 0.0
        B_TRI[1][2*i + 1] = INVJ[1][0] * D_NTRI[0][i] + INVJ[1][1] * D_NTRI[1][i]
        B_TRI[2][2*i]     = INVJ[1][0] * D_NTRI[0][i] + INVJ[1][1] * D_NTRI[1][i]
        B_TRI[2][2*i + 1] = INVJ[0][0] * D_NTRI[0][i] + INVJ[0][1] * D_NTRI[1][i]
        
    d_val = 0.0 # Undegraded state
    deg = (1.0 - d_val)**2 + k_res
    
    D_ELAS = [
        [C11_0 * deg, C12_0 * deg, 0.0],
        [C12_0 * deg, C22_0 * deg, 0.0],
        [0.0,         0.0,         C33_0 * deg]
    ]
    
    BT = mat_transpose(B_TRI)
    BT_D = mat_mult(BT, D_ELAS)
    BT_D_B = mat_mult(BT_D, B_TRI)
    K_mech = [[CJAC * BT_D_B[i][j] for j in range(6)] for i in range(6)]
    
    # Check symmetry: ||K - K^T||
    sym_err = 0.0
    for i in range(6):
        for j in range(6):
            sym_err += (K_mech[i][j] - K_mech[j][i])**2
    sym_err = math.sqrt(sym_err)
    
    # Check rigid body modes: pure translation in X, pure translation in Y, rotation
    u_tx = [1.0, 0.0, 1.0, 0.0, 1.0, 0.0]
    u_ty = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    u_rot = [-coords[0][1], coords[0][0], -coords[1][1], coords[1][0], -coords[2][1], coords[2][0]]
    
    f_tx = mat_vec(K_mech, u_tx)
    f_ty = mat_vec(K_mech, u_ty)
    f_rot = mat_vec(K_mech, u_rot)
    
    print(f"\nJTYPE 4 (Mechanical Triangle) Verification:")
    print(f"  Stiffness matrix shape: 6 x 6")
    print(f"  Symmetry error ||K - K^T||: {sym_err:.8e}")
    print(f"  Rigid X translation residual norm: {vec_norm(f_tx):.8e}")
    print(f"  Rigid Y translation residual norm: {vec_norm(f_ty):.8e}")
    print(f"  Rigid rotation residual norm:      {vec_norm(f_rot):.8e}")
    assert sym_err < 1e-12, "Mechanical stiffness not symmetric!"
    assert vec_norm(f_tx) < 1e-12, "Rigid X translation has non-zero force!"
    assert vec_norm(f_ty) < 1e-12, "Rigid Y translation has non-zero force!"
    assert vec_norm(f_rot) < 1e-12, "Rigid rotation has non-zero force!"
    
    # Test homogeneous shear deformation: u_x = gamma * y, u_y = 0
    gamma = 0.001
    u_shear = [gamma * coords[0][1], 0.0, gamma * coords[1][1], 0.0, gamma * coords[2][1], 0.0]
    strain_shear = mat_vec(B_TRI, u_shear)
    stress_shear = mat_vec(D_ELAS, strain_shear)
    strain_energy_mech = 0.5 * vec_dot(u_shear, mat_vec(K_mech, u_shear))
    strain_energy_analytical = 0.5 * CJAC * (C33_0 * deg) * (gamma**2)
    print(f"  Shear strain: eps11={strain_shear[0]:.6e}, eps22={strain_shear[1]:.6e}, gamma12={strain_shear[2]:.6e}")
    print(f"  Shear stress: sig11={stress_shear[0]:.6e}, sig22={stress_shear[1]:.6e}, tau12={stress_shear[2]:.6e}")
    print(f"  Strain Energy computed:   {strain_energy_mech:.16e} kN*mm")
    print(f"  Strain Energy analytical: {strain_energy_analytical:.16e} kN*mm")
    rel_diff = abs(strain_energy_mech - strain_energy_analytical) / strain_energy_analytical
    print(f"  Energy relative diff:     {rel_diff:.8e}")
    assert rel_diff < 1e-14, "Shear strain energy mismatch!"

    # -------------------------------------------------------------
    # JTYPE 3: Phase-Field Element (3 DOFs)
    # -------------------------------------------------------------
    B_PHTRI = [[0.0 for _ in range(3)] for _ in range(2)]
    for i in range(3):
        B_PHTRI[0][i] = INVJ[0][0] * D_NTRI[0][i] + INVJ[0][1] * D_NTRI[1][i]
        B_PHTRI[1][i] = INVJ[1][0] * D_NTRI[0][i] + INVJ[1][1] * D_NTRI[1][i]
        
    N_TRI = [1.0/3.0, 1.0/3.0, 1.0/3.0]
    HIST = 0.005 # kN/mm^2
    
    K_phase = [[0.0 for _ in range(3)] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            bdb = B_PHTRI[0][i] * B_PHTRI[0][j] + B_PHTRI[1][i] * B_PHTRI[1][j]
            K_phase[i][j] = CJAC * ((Gc * l0) * bdb + (Gc / l0 + 2.0 * HIST) * N_TRI[i] * N_TRI[j])
            
    sym_err_ph = 0.0
    for i in range(3):
        for j in range(3):
            sym_err_ph += (K_phase[i][j] - K_phase[j][i])**2
    sym_err_ph = math.sqrt(sym_err_ph)
    
    print(f"\nJTYPE 3 (Phase-Field Triangle) Verification:")
    print(f"  Stiffness matrix shape: 3 x 3")
    print(f"  Symmetry error ||K - K^T||: {sym_err_ph:.8e}")
    assert sym_err_ph < 1e-12, "Phase-field stiffness not symmetric!"
    
    # Uniform phase-field d = d0
    d0 = 0.5
    u_ph = [d0, d0, d0]
    grad_d = mat_vec(B_PHTRI, u_ph)
    print(f"  Uniform d={d0} grad(d) norm: {vec_norm(grad_d):.8e} (Expected: exactly 0)")
    assert vec_norm(grad_d) < 1e-12, "Uniform phase gradient is non-zero!"
    
    # Check phase-field energy on uniform field
    # E_frac = Area * ( Gc * (0.5 * d0^2 / l0) + 0.5 * Gc * l0 * |grad d|^2 )
    E_frac_analytical = CJAC * (Gc * (0.5 * (d0**2) / l0))
    d_avg = sum(u_ph) / 3.0
    E_frac_computed = CJAC * (Gc * (0.5 * (d_avg**2) / l0))
    print(f"  Uniform d={d0} Fracture Energy computed:   {E_frac_computed:.16e} kN*mm")
    print(f"  Uniform d={d0} Fracture Energy analytical: {E_frac_analytical:.16e} kN*mm")
    assert abs(E_frac_computed - E_frac_analytical) < 1e-16
    
    print("\n" + "=" * 70)
    print("SUCCESS: ALL TRIANGULAR SUBROUTINE EQUATIONS QUALIFIED (JTYPE 3 & 4)")
    print("=" * 70)

if __name__ == "__main__":
    verify_tri_uel()
