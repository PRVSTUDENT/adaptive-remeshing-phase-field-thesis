import numpy as np
import pytest
from scripts.validation.evaluate_f1641_local_size_support import bulk_support, inside, polygon_area, support_distance


def test_bulk_mass_is_area_weighted_and_scale_invariant():
    selected, weights, _ = bulk_support([1, 2, 1], [1, 2, 1], .8)
    assert selected.tolist() == [False, True, False]
    assert weights.tolist() == pytest.approx([.1, .8, .1])
    other, _, _ = bulk_support([1, 2, 1], [10, 20, 10], .8)
    assert np.array_equal(selected, other)


def test_cutoff_ties_do_not_depend_on_element_order():
    selected, weights, _ = bulk_support([1, 1, 1], [1, 1, 1], .5)
    assert selected.all() and weights.sum() == pytest.approx(1)


def test_polygon_and_distance_preserve_odb_three_coordinates():
    p = [[0,0,0],[1,0,0],[1,1,0],[0,1,0]]
    assert polygon_area(p) == pytest.approx(1)
    assert inside((.5,.5), p) and inside((1,.5), p)
    assert not inside((1.1,.5), p)
    q = [[2,0,0],[3,0,0],[3,1,0],[2,1,0]]
    assert support_distance(np.array([[.5,.5],[2.5,.5]]),[p,q],[True,False]).tolist() == pytest.approx([0,1.5])


def test_invalid_indicator_proxy_cannot_create_support():
    with pytest.raises(ValueError):
        bulk_support([1], [0])
    with pytest.raises(ValueError):
        bulk_support([0], [1])
    with pytest.raises(ValueError):
        bulk_support([1], [float('nan')])
