"""
Unit tests for Miehe (2010) spectral strain energy split formulation.
Governing reference: Miehe, Hofacker, Welschinger (2010) CMAME; Pandey & Kumar (2025) CMES Section 4.2.
"""
import pytest
import numpy as np

def compute_miehe_split_2d(eps_voigt, E=210000.0, nu=0.3, d=0.0, k_dam=1e-7):
    """
    Compute 2D plane strain Miehe spectral split:
    eps_voigt = [eps11, eps22, gamma12] (engineering shear gamma12 = 2*eps12)
    """
    lam = (E * nu) / ((1.0 + nu) * (1.0 - 2.0 * nu))
    mu = E / (2.0 * (1.0 + nu))
    
    eps11 = eps_voigt[0]
    eps22 = eps_voigt[1]
    eps12 = 0.5 * eps_voigt[2]
    
    tr_eps = eps11 + eps22
    tr_pos = max(tr_eps, 0.0)
    tr_neg = min(tr_eps, 0.0)
    
    # Eigenvalues
    eps_bar = 0.5 * (eps11 + eps22)
    R = np.sqrt((0.5 * (eps11 - eps22))**2 + eps12**2)
    eps1 = eps_bar + R
    eps2 = eps_bar - R
    
    eps1_pos = max(eps1, 0.0)
    eps1_neg = min(eps1, 0.0)
    eps2_pos = max(eps2, 0.0)
    eps2_neg = min(eps2, 0.0)
    
    # Strain energies
    psi_pos = 0.5 * lam * (tr_pos**2) + mu * (eps1_pos**2 + eps2_pos**2)
    psi_neg = 0.5 * lam * (tr_neg**2) + mu * (eps1_neg**2 + eps2_neg**2)
    
    # Eigenvectors / Projection tensors
    if R > 1e-14:
        cos2t = 0.5 * (eps11 - eps22) / R
        sin2t = eps12 / R
    else:
        cos2t = 1.0
        sin2t = 0.0
        
    v1 = np.array([0.5 * (1.0 + cos2t), 0.5 * (1.0 - cos2t), 0.5 * sin2t])
    v2 = np.array([0.5 * (1.0 - cos2t), 0.5 * (1.0 + cos2t), -0.5 * sin2t])
    v12 = np.array([-sin2t, sin2t, cos2t])
    
    # Stresses
    sigma_pos = lam * tr_pos * np.array([1.0, 1.0, 0.0]) + 2.0 * mu * (eps1_pos * v1 + eps2_pos * v2)
    sigma_neg = lam * tr_neg * np.array([1.0, 1.0, 0.0]) + 2.0 * mu * (eps1_neg * v1 + eps2_neg * v2)
    
    deg = (1.0 - d)**2 + k_dam
    sigma_deg = deg * sigma_pos + sigma_neg
    
    # Tangents
    h_vol_pos = 1.0 if tr_eps > 0.0 else 0.0
    h_vol_neg = 1.0 if tr_eps < 0.0 else 0.0
    h1_pos = 1.0 if eps1 > 0.0 else 0.0
    h1_neg = 1.0 if eps1 < 0.0 else 0.0
    h2_pos = 1.0 if eps2 > 0.0 else 0.0
    h2_neg = 1.0 if eps2 < 0.0 else 0.0
    
    if R > 1e-14:
        theta_pos = (eps1_pos - eps2_pos) / (2.0 * R)
        theta_neg = (eps1_neg - eps2_neg) / (2.0 * R)
    else:
        theta_pos = 0.5 * (h1_pos + h2_pos)
        theta_neg = 0.5 * (h1_neg + h2_neg)
        
    I_vol = np.array([[1.0, 1.0, 0.0], [1.0, 1.0, 0.0], [0.0, 0.0, 0.0]])
    
    D_pos = (lam * h_vol_pos * I_vol + 
             2.0 * mu * (h1_pos * np.outer(v1, v1) + h2_pos * np.outer(v2, v2)) + 
             2.0 * mu * theta_pos * 0.5 * np.outer(v12, v12))
             
    D_neg = (lam * h_vol_neg * I_vol + 
             2.0 * mu * (h1_neg * np.outer(v1, v1) + h2_neg * np.outer(v2, v2)) + 
             2.0 * mu * theta_neg * 0.5 * np.outer(v12, v12))
             
    D_mech = deg * D_pos + D_neg
    
    return {
        'psi_pos': psi_pos,
        'psi_neg': psi_neg,
        'sigma_pos': sigma_pos,
        'sigma_neg': sigma_neg,
        'sigma_deg': sigma_deg,
        'D_mech': D_mech,
        'eps1': eps1,
        'eps2': eps2
    }

def test_pure_tension():
    eps = np.array([0.001, 0.0, 0.0])
    res_intact = compute_miehe_split_2d(eps, d=0.0)
    res_broken = compute_miehe_split_2d(eps, d=1.0)
    
    assert res_intact['psi_pos'] > 0.0
    assert res_intact['psi_neg'] == 0.0
    # Fully degraded stress is proportional to k_dam
    assert np.allclose(res_broken['sigma_deg'], 0.0, atol=1e-4)
    assert np.allclose(res_broken['D_mech'], 0.0, atol=1e-1)

def test_pure_compression():
    eps = np.array([-0.001, 0.0, 0.0])
    res_intact = compute_miehe_split_2d(eps, d=0.0)
    res_broken = compute_miehe_split_2d(eps, d=1.0)
    
    assert res_intact['psi_pos'] == 0.0
    assert res_intact['psi_neg'] > 0.0
    # Compression stress and tangent must remain completely intact despite d=1!
    assert np.allclose(res_broken['sigma_deg'], res_intact['sigma_deg'], rtol=1e-5)
    assert np.allclose(res_broken['D_mech'], res_intact['D_mech'], rtol=1e-5)

def test_pure_shear():
    gamma = 0.002
    eps = np.array([0.0, 0.0, gamma])
    res_intact = compute_miehe_split_2d(eps, d=0.0)
    res_broken = compute_miehe_split_2d(eps, d=1.0)
    
    mu = 210000.0 / (2.0 * 1.3)
    expected_psi = mu * (0.5 * gamma)**2
    assert np.isclose(res_intact['psi_pos'], expected_psi, rtol=1e-5)
    assert np.isclose(res_intact['psi_neg'], expected_psi, rtol=1e-5)
    
    # Under shear, broken material retains compressive half of stiffness!
    assert res_broken['D_mech'][2, 2] > 0.0
    assert np.isclose(res_broken['D_mech'][2, 2], 0.5 * mu, rtol=1e-4)

def test_tangent_consistency():
    eps0 = np.array([0.001, -0.0005, 0.0015])
    d_val = 0.4
    res0 = compute_miehe_split_2d(eps0, d=d_val)
    D_ana = res0['D_mech']
    
    # Numerical tangent
    D_num = np.zeros((3, 3))
    h = 1e-8
    for j in range(3):
        eps_p = eps0.copy()
        eps_m = eps0.copy()
        eps_p[j] += h
        eps_m[j] -= h
        sp = compute_miehe_split_2d(eps_p, d=d_val)['sigma_deg']
        sm = compute_miehe_split_2d(eps_m, d=d_val)['sigma_deg']
        D_num[:, j] = (sp - sm) / (2.0 * h)
        
    assert np.allclose(D_ana, D_num, rtol=1e-4, atol=1e-4)
    # Check symmetry of analytical tangent
    assert np.allclose(D_ana, D_ana.T, rtol=1e-6)
