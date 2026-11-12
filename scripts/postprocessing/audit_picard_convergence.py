"""
Audit Picard Iteration Contraction Factor and Spectral Radius
Evaluates the mathematical stability of the pseudo-monolithic (block-diagonal)
iterative coupling between mechanical displacement and phase-field damage
under the Amor et al. (2009) volumetric-deviatoric split.

NOTE ON SCOPE & APPLICABILITY:
The scalar derivation rho = 4*d represents a restricted 1D scalar slice under
unconstrained stress-controlled loading. In a multidimensional finite-element
specimen with displacement boundary conditions, structural compliance, and
strain-gradient regularization (Gc*l0*(grad d)^2), the exact block-iteration
error propagation matrix is M = E^2 = [K_uu^-1 K_ud K_dd^-1 K_du, 0; 0, K_dd^-1 K_du K_uu^-1 K_ud].
The condition rho(M) > 1 is the theoretical mechanism under investigation for
Newton divergence during localized ligament softening, not an independently
computed numerical eigenvalue for the full mesh.
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
    C_plus = 0.5 * k_bulk + (2.0 / 3.0) * mu
    C_elas = k_bulk + (4.0 / 3.0) * mu
    
    print("=" * 80)
    print("RESTRICTED 1D SCALAR ANALYSIS OF INTRA-INCREMENT PICARD ITERATION STABILITY")
    print("=" * 80)
    print(f"Material: E = {E} kN/mm^2, nu = {nu}, Gc = {Gc} kN/mm, l0 = {l0} mm")
    print(f"Bulk modulus K = {k_bulk:.4f} kN/mm^2, Shear modulus mu = {mu:.4f} kN/mm^2")
    print(f"Effective tensile modulus C_elas = {C_elas:.4f} kN/mm^2")
    print(f"Crack driving factor C_plus = {C_plus:.4f} kN/mm^2")
    print(f"Phase-field intrinsic scale Gc / l0 = {Gc/l0:.4f} kN/mm^2")
    print("-" * 80)
    
    # In an uncoupled Picard iteration under 1D stress control:
    # 1. At fixed strain eps:
    #    H = psi_plus = C_plus * eps^2
    #    d = (2 * H) / (Gc/l0 + 2*H)
    #    dd / dH = (2 * Gc/l0) / (Gc/l0 + 2*H)^2
    #    dH / deps = 2 * C_plus * eps
    #    dd / deps = [4 * C_plus * (Gc/l0) * eps] / (Gc/l0 + 2*H)^2
    #
    # 2. In the mechanical equation under unconstrained load control:
    #    Residual: R_u = F_ext - (1-d)^2 * C_elas * eps = 0
    #    eps = F / [ (1-d)^2 * C_elas ]
    #    deps / dd = 2 * eps / (1-d)
    #
    # 3. Therefore, the 1D scalar Picard amplification factor is:
    #    rho_1D = (deps / dd) * (dd / deps) = 4 * d
    #
    # Note: In a multidimensional specimen, displacement constraints and gradient terms
    # alter the effective compliance. This 1D scalar model illustrates how local compliance
    # increases the amplification factor toward and beyond unity as damage develops.
    
    print("Damage d | (1-d) | 2*H / (Gc/l0) | 1D Scalar Factor rho = 4*d | 1D Model Classification")
    print("-" * 80)
    for d in [0.05, 0.10, 0.20, 0.24, 0.25, 0.30, 0.40, 0.4676, 0.50, 0.60, 0.70, 0.7167, 0.75, 0.80, 0.90]:
        rho = 4.0 * d
        status = "CONTRACTIVE (rho < 1)" if rho < 1.0 else ("NEUTRAL (rho = 1)" if abs(rho-1.0)<1e-3 else "EXPANSIVE (rho > 1)")
        two_H_ratio = d / (1.0 - d) if d < 1.0 else 999.0
        print(f" {d:7.4f} | {1-d:5.3f} | {two_H_ratio:13.4f} | {rho:26.4f} | {status}")
    
    print("-" * 80)
    print("THEORETICAL INTERPRETATION & SCOPE BOUNDARY:")
    print("1. The 1D scalar relation rho = 4*d is a conceptual illustration under unconstrained")
    print("   stress control, NOT an assertion that multidimensional FE models diverge at d = 0.25.")
    print("2. In the authentic F1720 adapted simulation, peak load converged successfully at d = 0.4676,")
    print("   proving that multidimensional constraint and gradient regularization delay divergence.")
    print("3. When damage localized heavily in Ligament 3 (d = 0.56 -> 0.7167), local softening reduced")
    print("   the effective ligament stiffness, making rho(M) > 1 the hypothesized mechanism for the")
    print("   alternating Newton divergence observed in PK_F1720_ADAPTED_PFM.msg.")
    print("=" * 80)

if __name__ == "__main__":
    compute_picard_stability()
