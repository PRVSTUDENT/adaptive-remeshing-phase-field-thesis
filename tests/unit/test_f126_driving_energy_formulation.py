import pytest

def compute_pos_m(e11, e22, e12, E=210.0, nu=0.3, k=1e-7, d=0.0, degraded=False):
    c11_0 = E*(1.0 - nu)/((1.0 + nu)*(1.0 - 2.0*nu))
    c12_0 = E*nu/((1.0 + nu)*(1.0 - 2.0*nu))
    c33_0 = E/(2.0*(1.0 + nu))
    
    deg = (1.0 - d)**2 + k
    
    if degraded:
        c12 = c12_0 * deg
        c33 = c33_0 * deg
    else:
        c12 = c12_0
        c33 = c33_0
        
    tr_e = e11 + e22
    e_pos = max(0.0, tr_e)
    pos_m = 0.5 * c12 * (e_pos**2) + c33 * (e11**2 + e22**2 + 2.0 * (e12**2))
    return pos_m

def test_driving_energy_undegraded_vs_degraded_bug():
    d_vals = [0.0, 0.25, 0.50, 0.845716, 0.95]
    e11, e22, e12 = 0.01, 0.005, 0.002
    
    for d in d_vals:
        pos_m_corr = compute_pos_m(e11, e22, e12, d=d, degraded=False)
        pos_m_bug  = compute_pos_m(e11, e22, e12, d=d, degraded=True)
        deg = (1.0 - d)**2 + 1e-7
        
        ratio = pos_m_bug / pos_m_corr
        assert abs(ratio - deg) < 1e-6, f"Ratio {ratio} should match DEG {deg} for d={d}"
        
        # Regression assertion: Undegraded driving energy MUST be independent of damage d
        assert abs(pos_m_corr - compute_pos_m(e11, e22, e12, d=0.0, degraded=False)) < 1e-12
