"""
Audit Picard Iteration Contraction Factor and Spectral Radius
Evaluates the mathematical stability of the pseudo-monolithic (block-diagonal)
iterative coupling between mechanical displacement and phase-field damage
under the Amor et al. (2009) volumetric-deviatoric split.
"""

import numpy as np

def compute_picard_stability():
    # Material parameters (Pandey & Kumar 2025 Five-Hole Benchmark)
    E = 210.0          # kN/mm^2 (210 GPa)
    nu = 0.30
    Gc = 2.7e-3        # kN/mm (2.7 N/mm)
    l0 = 0.008         # mm (8 um)
    k_res = 1.0e-7
    
    # Plane strain elastic constants
    mu = E / (2.0 * (1.0 + nu))
    lam = (E * nu) / ((1.0 + nu) * (1.0 - 2.0 * nu))
    k_bulk = E / (3.0 * (1.0 - 2.0 * nu))
    
    # Uniaxial tensile strain in plane strain: eps_22 = eps, eps_11 = 0, eps_12 = 0
    # tr(eps) = eps > 0
    # eps_dev_11 = -eps/3, eps_dev_22 = 2*eps/3, eps_dev_33 = -eps/3
    # eps_dev_sq = (2/3)*eps^2
    # psi_plus = 0.5 * k_bulk * eps^2 + mu * (2/3) * eps^2
    # Let C_plus = 0.5 * k_bulk + (2.0/3.0) * mu
    C_plus = 0.5 * k_bulk + (2.0 / 3.0) * mu
    # sigma_22_0 = (k_bulk + 4/3*mu) * eps = 2 * C_plus * eps
    C_elas = k_bulk + (4.0 / 3.0) * mu
    
    print("=" * 80)
    print("MATHEMATICAL ANALYSIS OF INTRA-INCREMENT PICARD ITERATION STABILITY")
    print("=" * 80)
    print(f"Material: E = {E} kN/mm^2, nu = {nu}, Gc = {Gc} kN/mm, l0 = {l0} mm")
    print(f"Bulk modulus K = {k_bulk:.4f} kN/mm^2, Shear modulus mu = {mu:.4f} kN/mm^2")
    print(f"Effective tensile modulus C_elas = {C_elas:.4f} kN/mm^2")
    print(f"Crack driving factor C_plus = {C_plus:.4f} kN/mm^2")
    print(f"Phase-field intrinsic scale Gc / l0 = {Gc/l0:.4f} kN/mm^2")
    print("-" * 80)
    
    # In an uncoupled Picard iteration at fixed applied tensile force or boundary displacement:
    # 1. At fixed displacement u (strain eps):
    #    H = psi_plus = C_plus * eps^2
    #    Phase field equation (at element center, ignoring grad d for homogeneous state):
    #    d = (2 * H) / (Gc/l0 + 2*H)
    #    dd / dH = (2 * Gc/l0) / (Gc/l0 + 2*H)^2
    #    dH / deps = 2 * C_plus * eps
    #    dd / deps = [4 * C_plus * (Gc/l0) * eps] / (Gc/l0 + 2*H)^2
    #
    # 2. In the mechanical equation:
    #    Residual: R_u = F_ext - (1-d)^2 * C_elas * eps = 0
    #    If displacement is uncoupled, the change in strain induced by a change in damage:
    #    Under load control / elastic compliance from surrounding body:
    #    eps = F / [ (1-d)^2 * C_elas ]
    #    deps / dd = 2 * eps / (1-d)
    #
    # 3. Therefore, the Picard fixed-point amplification factor is:
    #    rho = (deps / dd) * (dd / deps)
    #        = [ 2 * eps / (1-d) ] * [ 4 * C_plus * (Gc/l0) * eps / (Gc/l0 + 2*H)^2 ]
    #        = [ 8 * C_plus * (Gc/l0) * eps^2 ] / [ (1-d) * (Gc/l0 + 2*H)^2 ]
    #    Note that 2*H = 2 * C_plus * eps^2, so:
    #    rho = [ 4 * (Gc/l0) * (2*H) ] / [ (1-d) * (Gc/l0 + 2*H)^2 ]
    #    Since d = 2*H / (Gc/l0 + 2*H), we have 1 - d = (Gc/l0) / (Gc/l0 + 2*H)!
    #    Substitute (Gc/l0 + 2*H) = (Gc/l0) / (1-d):
    #    rho = [ 4 * (Gc/l0) * (2*H) ] / [ (1-d) * (Gc/l0 / (1-d))^2 ]
    #        = [ 4 * (2*H) * (1-d) ] / (Gc/l0)
    #    And 2*H = (Gc/l0) * d / (1-d)!
    #    Therefore:
    #    rho = 4 * [ (Gc/l0) * d / (1-d) ] * (1-d) / (Gc/l0) = 4 * d !
    
    print("Damage d | (1-d) | 2*H / (Gc/l0) | Picard Amplification rho = 4*d | Convergence Status")
    print("-" * 80)
    for d in [0.05, 0.10, 0.20, 0.24, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70, 0.7167, 0.75, 0.80, 0.90]:
        rho = 4.0 * d
        status = "CONVERGENT (rho < 1)" if rho < 1.0 else ("MARGINAL (rho = 1)" if abs(rho-1.0)<1e-3 else "DIVERGENT (rho > 1)")
        two_H_ratio = d / (1.0 - d) if d < 1.0 else 999.0
        print(f" {d:7.4f} | {1-d:5.3f} | {two_H_ratio:13.4f} | {rho:29.4f} | {status}")
    
    print("-" * 80)
    print("CRITICAL FINDING:")
    print("Under uncoupled block-diagonal (Picard) coupling:")
    print("  - For d < 0.25: rho = 4*d < 1 -> Picard iterations are contractive and converge.")
    print("  - At d = 0.25: rho = 1.0 -> Limit of contractivity.")
    print("  - For d > 0.25: rho = 4*d > 1 -> Picard iterations are strictly EXPANSIVE / DIVERGENT!")
    print(f"  - At F1720 terminal state (d = 0.7167): rho = 4 * 0.7167 = {4*0.7167:.4f} >> 1.0!")
    print("  - Each Picard iteration amplifies the error by ~2.87x, causing flip-flop divergence!")
    print("=" * 80)

if __name__ == "__main__":
    compute_picard_stability()
