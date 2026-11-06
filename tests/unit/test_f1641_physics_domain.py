import math
import numpy as np
import pytest
from scripts.validation.evaluate_f1641_physics_domain import driver, homogeneous_damage, kinematics, weighted_stats


def test_homogeneous_phase_equation_has_no_positive_initiation_threshold():
    assert homogeneous_damage(0) == 0
    assert 0 < homogeneous_damage(1e-15) < homogeneous_damage(.01) < 1
    h = .12
    d = homogeneous_damage(h)
    assert (.0027/.0075+2*h)*d == pytest.approx(2*h)
    with pytest.raises(ValueError):
        homogeneous_damage(-1)


def test_driver_matches_frozen_trace_split_in_shear_and_compression():
    mu = 210/(2*1.3)
    assert driver([0,0,.02]) == pytest.approx(mu*.02**2/2)
    # The frozen law retains the strain-norm term even with negative trace.
    assert driver([-.01,-.01,0]) == pytest.approx(mu*2*.01**2)
    assert driver([0,0,0]) == 0


@pytest.mark.parametrize('points',[
    [[0,0],[2,0],[2.5,1],[.5,1]],
    [[0,0],[2,0],[.5,1]],
])
def test_affine_kinematics_on_skew_quad_and_triangle(points):
    xy = np.array(points)
    # u_x=.003*x+.005*y; u_y=-.002*x+.004*y
    u = xy@np.array([[.003,-.002],[.005,.004]])
    e,j = kinematics(xy,u,.2,-.3)
    assert j > 0
    assert e == pytest.approx([.003,.004,.003])


def test_energy_weighted_size_summary():
    s = weighted_stats([.1,.2,.3],[1,1,8])
    assert s['median'] == .3 and s['min'] == .1 and s['max'] == .3
