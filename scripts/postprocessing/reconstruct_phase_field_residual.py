"""
Pure-Python script to reconstruct and evaluate term-by-term finite element phase-field residual
matrices on crack-tip elements for H1 (1389686) and PK10R2 (1390056).
"""

import math

def mat_add(A, B):
    return [[A[i][j] + B[i][j] for j in range(len(A[0]))] for i in range(len(A))]

def mat_scalar(A, c):
    return [[A[i][j] * c for j in range(len(A[0]))] for i in range(len(A))]

def mat_norm(A):
    return math.sqrt(sum([sum([x**2 for x in row]) for row in A]))

def vec_norm(v):
    return math.sqrt(sum([x**2 for x in v]))

def compute_element_phase_matrices(node_coords, H_values, Gc=0.0027, l0=0.015):
    g_local = [-0.577350269189626, 0.577350269189626]
    W = 1.0

    K_grad = [[0.0]*4 for _ in range(4)]
    K_mass = [[0.0]*4 for _ in range(4)]
    K_hist = [[0.0]*4 for _ in range(4)]
    f_ext = [0.0]*4

    gp_idx = 0
    for eta in g_local:
        for xi in g_local:
            N = [
                0.25 * (1.0 - xi) * (1.0 - eta),
                0.25 * (1.0 + xi) * (1.0 - eta),
                0.25 * (1.0 + xi) * (1.0 + eta),
                0.25 * (1.0 - xi) * (1.0 + eta)
            ]

            dN_dxi = [
                [-0.25 * (1.0 - eta), 0.25 * (1.0 - eta), 0.25 * (1.0 + eta), -0.25 * (1.0 + eta)],
                [-0.25 * (1.0 - xi), -0.25 * (1.0 + xi), 0.25 * (1.0 + xi), 0.25 * (1.0 - xi)]
            ]

            # Jacobian J
            J00 = sum([dN_dxi[0][k] * node_coords[k][0] for k in range(4)])
            J01 = sum([dN_dxi[0][k] * node_coords[k][1] for k in range(4)])
            J10 = sum([dN_dxi[1][k] * node_coords[k][0] for k in range(4)])
            J11 = sum([dN_dxi[1][k] * node_coords[k][1] for k in range(4)])

            detJ = J00 * J11 - J01 * J10
            invJ00 = J11 / detJ
            invJ01 = -J01 / detJ
            invJ10 = -J10 / detJ
            invJ11 = J00 / detJ

            # B matrix: 2x4 (dN/dx, dN/dy)
            B = [[0.0]*4 for _ in range(2)]
            for k in range(4):
                B[0][k] = invJ00 * dN_dxi[0][k] + invJ01 * dN_dxi[1][k]
                B[1][k] = invJ10 * dN_dxi[0][k] + invJ11 * dN_dxi[1][k]

            cjac = detJ * W * W
            H_gp = H_values[gp_idx] if gp_idx < len(H_values) else H_values[0]

            for i in range(4):
                f_ext[i] += cjac * (2.0 * H_gp) * N[i]
                for j in range(4):
                    bdb = B[0][i] * B[0][j] + B[1][i] * B[1][j]
                    K_grad[i][j] += cjac * (Gc * l0) * bdb
                    K_mass[i][j] += cjac * (Gc / l0) * N[i] * N[j]
                    K_hist[i][j] += cjac * (2.0 * H_gp) * N[i] * N[j]

            gp_idx += 1

    K_total = mat_add(mat_add(K_grad, K_mass), K_hist)
    return {
        "K_grad": K_grad,
        "K_mass": K_mass,
        "K_hist": K_hist,
        "K_total": K_total,
        "f_ext": f_ext,
        "norm_K_grad": mat_norm(K_grad),
        "norm_K_mass": mat_norm(K_mass),
        "norm_K_hist": mat_norm(K_hist),
        "norm_f_ext": vec_norm(f_ext)
    }

def main():
    print("================================================================================")
    print("TERM-BY-TERM PHASE-FIELD FINITE ELEMENT RESIDUAL AUDIT")
    print("================================================================================")

    # 1. H1 Reference Tip Element (h = 0.0025 mm)
    h1_coords = [(0.0, 0.0), (0.0025, 0.0), (0.0025, 0.0025), (0.0, 0.0025)]
    h1_H = [0.0924, 0.0450, 0.0300, 0.0450] # Peak near tip GP = 0.0924 kN/mm^2
    res_h1 = compute_element_phase_matrices(h1_coords, h1_H)

    # 2. PK10R2 Control Tip Element (h = 0.0050 mm)
    pk10_coords = [(0.0, 0.0), (0.0050, 0.0), (0.0050, 0.0050), (0.0, 0.0050)]
    pk10_H = [0.0112, 0.0060, 0.0040, 0.0060] # Peak near tip GP = 0.0112 kN/mm^2
    res_pk10 = compute_element_phase_matrices(pk10_coords, pk10_H)

    print("--- H1 Reference Tip Element (h = 0.0025 mm, l0 = 0.015 mm) ---")
    print("  ||K_grad|| (Gradient Stiffness Gc*l0*B^T*B):  {0:.6e} kN".format(res_h1["norm_K_grad"]))
    print("  ||K_mass|| (Mass Matrix Gc/l0*N^T*N):        {0:.6e} kN".format(res_h1["norm_K_mass"]))
    print("  ||K_hist|| (Crack-Driving Matrix 2H*N^T*N):   {0:.6e} kN".format(res_h1["norm_K_hist"]))
    print("  ||f_ext||  (RHS Excitation Force 2H*N):      {0:.6e} kN".format(res_h1["norm_f_ext"]))
    print("  Ratio ||K_grad|| / ||K_mass||:                 {0:.2f} (Theoretical l0^2 / h^2 = 36.0)".format(res_h1["norm_K_grad"] / res_h1["norm_K_mass"]))
    print("  Ratio ||K_hist|| / ||K_mass||:                 {0:.2f} (H / H0 = 0.0924 / 0.090 = 1.03)".format(res_h1["norm_K_hist"] / res_h1["norm_K_mass"]))

    print("\n--- PK10R2 Control Tip Element (h = 0.0050 mm, l0 = 0.015 mm) ---")
    print("  ||K_grad|| (Gradient Stiffness Gc*l0*B^T*B):  {0:.6e} kN".format(res_pk10["norm_K_grad"]))
    print("  ||K_mass|| (Mass Matrix Gc/l0*N^T*N):        {0:.6e} kN".format(res_pk10["norm_K_mass"]))
    print("  ||K_hist|| (Crack-Driving Matrix 2H*N^T*N):   {0:.6e} kN".format(res_pk10["norm_K_hist"]))
    print("  ||f_ext||  (RHS Excitation Force 2H*N):      {0:.6e} kN".format(res_pk10["norm_f_ext"]))
    print("  Ratio ||K_grad|| / ||K_mass||:                 {0:.2f} (Theoretical l0^2 / h^2 = 9.0)".format(res_pk10["norm_K_grad"] / res_pk10["norm_K_mass"]))
    print("  Ratio ||K_hist|| / ||K_mass||:                 {0:.2f} (H / H0 = 0.0112 / 0.090 = 0.12)".format(res_pk10["norm_K_hist"] / res_pk10["norm_K_mass"]))
    print("================================================================================")

if __name__ == "__main__":
    main()
