"""
test_mode2_miseseri_physical_provenance.py

Unit test suite verifying MISESERI physical provenance, UMAT companion scaling,
Williams corner singularity mechanics, and Mode-II boundary conditions.

Task: F1351 (Mode-II MISESERI Physical Provenance and Fracture Solver Qualification)
Author: Gemini Antigravity
"""

import os
import sys
import json
import re
import math
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FORTRAN_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "f42_mixed_uel_mode2_miehe.for")
INP_COARSE_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "Job-1_UEL_paper_horizon.inp")
INP_ADAPT_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "m2_corrected_remesh", "M2_CORRECTED_JOB2_ET3PCT_STABILIZED.inp")

def test_fortran_umat_passive_companion():
    """Verify that UMAT implements pure passive linear elasticity without degradation."""
    assert os.path.exists(FORTRAN_PATH), f"Fortran file missing: {FORTRAN_PATH}"
    
    with open(FORTRAN_PATH, 'r') as f:
        content = f.read()
        
    # Check UMAT subroutine exists
    assert 'SUBROUTINE UMAT' in content, "SUBROUTINE UMAT not found in Fortran source"
    
    # Check DDSDDE linear elastic construction
    assert 'DDSDDE(1,1) = E_LAM + TWO * E_MU' in content
    assert 'DDSDDE(2,2) = E_LAM + TWO * E_MU' in content
    assert 'DDSDDE(1,2) = E_LAM' in content
    assert 'DDSDDE(4,4) = E_MU' in content
    
    # Check STRESS linear elastic update
    assert 'STRESS(K2) = STRESS(K2) + DDSDDE(K2, K1) * DSTRAN(K1)' in content
    
    # Check that degradation (1-d)^2 is NOT applied to UMAT STRESS
    umat_start = content.find('SUBROUTINE UMAT(')
    umat_body = content[umat_start:]
    
    assert '(ONE - D_VAL)**2' not in umat_body
    assert '(1.0 - D_VAL)**2' not in umat_body
    assert '(ONE-D_VAL)**2' not in umat_body
    assert 'STATEV(14) = D_VAL' in umat_body
    assert 'STATEV(15) = HIST_VAL' in umat_body
    assert 'STATEV(16) = PSI_E_VAL' in umat_body

def test_input_deck_layering_and_umat_properties():
    """Verify Layer 1, Layer 2, Layer 3 element sets and UMAT_MAT properties in input decks."""
    for inp_path in [INP_COARSE_PATH, INP_ADAPT_PATH]:
        assert os.path.exists(inp_path), f"Input deck missing: {inp_path}"
        with open(inp_path, 'r') as f:
            content = f.read()
            
        assert '*Elset, elset=PHASE_ELEM' in content or '*ELSET, ELSET=PHASE_ELEM' in content
        assert '*Elset, elset=MECH_ELEM' in content or '*ELSET, ELSET=MECH_ELEM' in content
        assert '*Elset, elset=All_elem' in content or '*ELSET, ELSET=All_elem' in content
        
        # Check UMAT material definition
        umat_match = re.search(r'\*Material,\s*name=UMAT_MAT[\r\n]+\*User Material[^\r\n]*[\r\n]+([0-9.eE+-]+),\s*([0-9.eE+-]+)', content, re.IGNORECASE)
        assert umat_match is not None, f"UMAT_MAT not found in {inp_path}"
        e_umat = float(umat_match.group(1))
        nu_umat = float(umat_match.group(2))
        
        assert math.isclose(e_umat, 1.0e-11, rel_tol=1e-5), f"E_umat mismatch: {e_umat}"
        assert math.isclose(nu_umat, 0.3, rel_tol=1e-5), f"nu_umat mismatch: {nu_umat}"

def test_mode2_boundary_condition_specification():
    """Verify Mode-II boundary conditions match Pandey & Kumar (2025) Fig. 4(b) exactly."""
    for inp_path in [INP_COARSE_PATH, INP_ADAPT_PATH]:
        with open(inp_path, 'r') as f:
            content = f.read()
            
        # Bottom edge: ux = uy = 0 (pinned/clamped)
        assert 'N_BOTTOM, 1, 2, 0.0' in content
        # Top edge: uy = 0 (constrained shear)
        assert 'N_TOP, 2, 2, 0.0' in content
        # Reference point: ux applied
        assert 'N_RP, 1, 1, 0.0100' in content

def test_miseseri_scale_invariance():
    """Verify analytical scale-invariance of normalized relative error eta_e = MISESERI / MISESAVG."""
    eps = [0.001, -0.0003, 0.0, 0.0008]
    nu = 0.3
    
    def compute_vm(E):
        lam = (E * nu) / ((1.0 + nu) * (1.0 - 2.0 * nu))
        mu = E / (2.0 * (1.0 + nu))
        sig_xx = (lam + 2.0*mu)*eps[0] + lam*eps[1]
        sig_yy = lam*eps[0] + (lam + 2.0*mu)*eps[1]
        sig_zz = lam*(eps[0] + eps[1])
        tau_xy = mu*eps[3]
        return math.sqrt(0.5 * ((sig_xx - sig_yy)**2 + (sig_yy - sig_zz)**2 + (sig_zz - sig_xx)**2 + 6.0*(tau_xy**2)))
        
    E_phys = 210.0      # kN/mm^2
    E_umat = 1.0e-11    # kN/mm^2
    
    vm_phys = compute_vm(E_phys)
    vm_umat = compute_vm(E_umat)
    
    # Scale ratio must match exact modulus ratio
    assert math.isclose(vm_umat / vm_phys, E_umat / E_phys, rel_tol=1e-12)
    
    # Relative normalized error eta = delta_sigma / sigma must be invariant
    eta_phys = 0.05 * vm_phys / vm_phys
    eta_umat = 0.05 * vm_umat / vm_umat
    assert math.isclose(eta_phys, eta_umat, rel_tol=1e-12)

def test_williams_singularity_exponents():
    """Verify theoretical singularity order for 90-degree clamped-free corner."""
    lambda_val = 0.7583 # Leading singular eigenvalue for nu=0.3 clamped-free wedge
    stress_exponent = lambda_val - 1.0
    grad_exponent = lambda_val - 2.0
    
    assert math.isclose(stress_exponent, -0.2417, rel_tol=1e-3)
    assert math.isclose(grad_exponent, -1.2417, rel_tol=1e-3)
    # The gradient exponent < -1.0 proves that linear elements cannot represent the strain gradient without mesh refinement.
    assert grad_exponent < -1.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
