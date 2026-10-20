import numpy as np
import pytest
from scripts.validation.probe_mode1_f1597_kkt import phase_element


def test_constant_solution_and_lower_bound_sign():
    xy = np.array([[0.,0.], [1.,0.], [1.,1.], [0.,1.]])
    ell, gc, h = .1, .2, .3
    equilibrium = 2*h/(gc/ell+2*h)
    a, b, g = phase_element(xy, np.full(4,equilibrium), np.full(4,h), ell,gc)
    assert np.max(np.abs(g)) < 1e-14
    assert np.linalg.eigvalsh(a).min() > 0
    assert np.max(phase_element(xy,np.zeros(4),np.full(4,h),ell,gc)[2]) < 0
    assert np.min(phase_element(xy,np.ones(4),np.full(4,h),ell,gc)[2]) > 0


def test_gradient_matches_energy_derivative():
    xy = np.array([[0.,0.], [2.,0.], [2.,1.], [0.,1.]])
    d = np.array([.1,.2,.3,.4]); h=np.array([.2,.3,.4,.5])
    a,b,g=phase_element(xy,d,h,.1,.2)
    energy=lambda v:.5*v@a@v-b@v
    for i in range(4):
        e=np.eye(4)[i]*1e-5
        assert ((energy(d+e)-energy(d-e))/(2e-5)) == pytest.approx(g[i],abs=1e-10)


def test_nonpositive_jacobian_rejected():
    with pytest.raises(ValueError,match='Jacobian'):
        phase_element(np.zeros((4,2)),np.zeros(4),np.zeros(4),.1,.2)
