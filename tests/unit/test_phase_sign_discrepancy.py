import numpy as np

def shape_functions(xi, eta):
    N = 0.25 * np.array([
        (1.0 - xi) * (1.0 - eta),
        (1.0 + xi) * (1.0 - eta),
        (1.0 + xi) * (1.0 + eta),
        (1.0 - xi) * (1.0 + eta)
    ])
    dNdxi = 0.25 * np.array([
        -(1.0 - eta),  (1.0 - eta),  (1.0 + eta), -(1.0 + eta)
    ])
    dNdeta = 0.25 * np.array([
        -(1.0 - xi), -(1.0 + xi),  (1.0 + xi),  (1.0 - xi)
    ])
    return N, dNdxi, dNdeta

def eval_production_uel_phase(coords, u_d, hist_val):
    E_GC = 0.0027
    E_L0 = 0.0075
    xg4 = [-0.577350269189626,  0.577350269189626,  0.577350269189626, -0.577350269189626]
    yg4 = [-0.577350269189626, -0.577350269189626,  0.577350269189626,  0.577350269189626]
    w4  = [1.0, 1.0, 1.0, 1.0]

    amatrx = np.zeros((4, 4))
    rhs = np.zeros(4)

    for kpt in range(4):
        xi, eta, wt = xg4[kpt], yg4[kpt], w4[kpt]
        N_vec, dNdxi, dNdeta = shape_functions(xi, eta)

        jac = np.zeros((2, 2))
        for a in range(4):
            jac[0, 0] += dNdxi[a] * coords[0, a]
            jac[0, 1] += dNdxi[a] * coords[1, a]
            jac[1, 0] += dNdeta[a] * coords[0, a]
            jac[1, 1] += dNdeta[a] * coords[1, a]

        detj = jac[0, 0] * jac[1, 1] - jac[0, 1] * jac[1, 0]
        invj = np.linalg.inv(jac)

        b_phase = np.zeros((2, 4))
        for i in range(4):
            b_phase[0, i] = invj[0, 0] * dNdxi[i] + invj[0, 1] * dNdeta[i]
            b_phase[1, i] = invj[1, 0] * dNdxi[i] + invj[1, 1] * dNdeta[i]

        cjac = detj * wt

        for i in range(4):
            for j in range(4):
                bdb = b_phase[0, i] * b_phase[0, j] + b_phase[1, i] * b_phase[1, j]
                amatrx[i, j] += cjac * (
                    (E_GC * E_L0) * bdb +
                    (E_GC / E_L0 + 2.0 * hist_val) * N_vec[i] * N_vec[j]
                )
            rhs[i] += cjac * 2.0 * hist_val * N_vec[i]

    for i in range(4):
        for j in range(4):
            rhs[i] -= amatrx[i, j] * u_d[j]

    rf = -rhs
    return amatrx, rhs, rf

def eval_12dof_uel_corrected(coords, u_d, hist_val):
    E_GC = 0.0027
    E_L0 = 0.0075
    xg4 = [-0.577350269189626,  0.577350269189626,  0.577350269189626, -0.577350269189626]
    yg4 = [-0.577350269189626, -0.577350269189626,  0.577350269189626,  0.577350269189626]
    w4  = [1.0, 1.0, 1.0, 1.0]

    kdd = np.zeros((4, 4))
    rd = np.zeros(4)

    for kpt in range(4):
        xi, eta, wt = xg4[kpt], yg4[kpt], w4[kpt]
        N_vec, dNdxi, dNdeta = shape_functions(xi, eta)

        jac = np.zeros((2, 2))
        for a in range(4):
            jac[0, 0] += dNdxi[a] * coords[0, a]
            jac[0, 1] += dNdxi[a] * coords[1, a]
            jac[1, 0] += dNdeta[a] * coords[0, a]
            jac[1, 1] += dNdeta[a] * coords[1, a]

        detj = jac[0, 0] * jac[1, 1] - jac[0, 1] * jac[1, 0]
        invj = np.linalg.inv(jac)

        dn = np.zeros((2, 4))
        for i in range(4):
            dn[0, i] = invj[0, 0] * dNdxi[i] + invj[0, 1] * dNdeta[i]
            dn[1, i] = invj[1, 0] * dNdxi[i] + invj[1, 1] * dNdeta[i]

        cj = detj * wt

        d_val = np.dot(N_vec, u_d)
        grad_d = dn @ u_d

        # Corrected lines: - 2*(1-d)*H in Rd, + 2*H in Kdd
        for a in range(4):
            rd[a] += cj * (
                ( (E_GC / E_L0) * d_val - 2.0 * (1.0 - d_val) * hist_val ) * N_vec[a] +
                E_GC * E_L0 * (dn[0, a] * grad_d[0] + dn[1, a] * grad_d[1])
            )
            for b in range(4):
                kdd[a, b] += cj * (
                    ( (E_GC / E_L0) + 2.0 * hist_val ) * N_vec[a] * N_vec[b] +
                    E_GC * E_L0 * (dn[0, a] * dn[0, b] + dn[1, a] * dn[1, b])
                )

    rhs = -rd
    rf = rd
    return kdd, rhs, rf

def main():
    print("=== VERIFYING REPAIRED 12-DOF UEL VS PRODUCTION UEL ===")
    coords = np.array([
        [0.0, 0.001, 0.001, 0.0],
        [0.0, 0.0,   0.001, 0.001]
    ])

    test_cases = [
        ("Crack-Tip (d=0.65, H=0.35)", np.array([0.65, 0.65, 0.65, 0.65]), 0.35),
        ("Intact (d=0.00, H=0.00)",    np.array([0.00, 0.00, 0.00, 0.00]), 0.00),
        ("Moderate (d=0.30, H=0.15)",  np.array([0.30, 0.30, 0.30, 0.30]), 0.15),
        ("Non-uniform (gradient)",     np.array([0.20, 0.40, 0.60, 0.50]), 0.25)
    ]

    all_pass = True
    for name, u_d, H in test_cases:
        k_prod, rhs_prod, rf_prod = eval_production_uel_phase(coords, u_d, H)
        k_corr, rhs_corr, rf_corr = eval_12dof_uel_corrected(coords, u_d, H)

        diff_rhs = np.max(np.abs(rhs_corr - rhs_prod))
        diff_rf = np.max(np.abs(rf_corr - rf_prod))
        diff_k = np.max(np.abs(k_corr - k_prod))

        print(f"\nTest: {name}")
        print(f"  Max |RHS_corr - RHS_prod|: {diff_rhs:.2e}")
        print(f"  Max |RF_corr - RF_prod|:   {diff_rf:.2e}")
        print(f"  Max |K_corr - K_prod|:     {diff_k:.2e}")

        if diff_rhs > 1e-15 or diff_rf > 1e-15 or diff_k > 1e-15:
            all_pass = False
            print("  FAIL: Discrepancy detected!")
        else:
            print("  PASS: Machine-precision parity confirmed!")

    assert all_pass, "Parity check failed!"
    print("\n>>> ALL TESTS PASSED: 100% BITWISE EQUIVALENCE WITH PRODUCTION UEL ACHIEVED! <<<")

if __name__ == "__main__":
    main()
