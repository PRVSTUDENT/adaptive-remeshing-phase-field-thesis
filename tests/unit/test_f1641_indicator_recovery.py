"""Validate authentic recovered field coverage and source immutability pins."""
import hashlib
import json
import math
from pathlib import Path
import pytest
from scripts.remeshing.generate_plate_with_hole_method_a import validate_reused_preanalysis
from scripts.validation.validate_f1641_native_mesh import element_metrics

ROOT = Path(__file__).resolve().parents[2]


def recovered():
    return json.loads((ROOT / 'results/validation/f1641_hole_indicator_provenance.json').read_text())


def test_authentic_source_identity_and_final_frame():
    data = recovered()
    assert data['source_sha256'] == '0A108C6A8404F1AF9D8F5DDC03223E9D8D051AB08587F841D9F5799970AE93B1'
    assert data['step'] == 'Step-1' and data['frame_value'] == 1.0
    assert data['frame_count'] == 11 and data['output_positions'] == ['WHOLE_ELEMENT']
    assert data['solver_runs'] == 0 and data['odb_modified'] is False


def test_complete_unambiguous_indicator_coverage():
    data = recovered()
    rows = data['records']
    assert len(rows) == 2906
    assert len({(r['instance'], r['element']) for r in rows}) == 2906
    assert {r['instance'] for r in rows} == {'PLATE-1'}
    assert sum(r['samples'] for r in rows) == 5812
    for r in rows:
        assert r['samples'] == 2
        assert math.isfinite(r['miseseri_max']) and r['miseseri_max'] >= 0
        assert r['miseseri_min'] == r['miseseri_max']
        assert r['edge_min_mm'] > 0


def test_frozen_local_uel_unchanged():
    path = ROOT / 'models/pandey_kumar_mode1/176_method_a_plate_with_hole/f42_mixed_uel.for'
    assert hashlib.sha256(path.read_bytes()).hexdigest().upper() == 'CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6'


def test_reused_odb_hash_gate(tmp_path):
    p = tmp_path / 'existing.odb'
    p.write_bytes(b'opaque test artifact')
    expected = hashlib.sha256(p.read_bytes()).hexdigest()
    validate_reused_preanalysis(str(p), expected)
    with pytest.raises(ValueError, match='mismatch'):
        validate_reused_preanalysis(str(p), '0' * 64)
    with pytest.raises(ValueError, match='existing exact path'):
        validate_reused_preanalysis(str(p), None)
    with pytest.raises(ValueError, match='existing exact path'):
        validate_reused_preanalysis(str(tmp_path / 'absent.odb'), expected)


def test_square_gauss_jacobians_and_angles():
    m = element_metrics([(0, 0), (2, 0), (2, 2), (0, 2)])
    assert m['area'] == pytest.approx(4)
    assert m['min_jac'] == pytest.approx(1)
    assert m['min_angle'] == pytest.approx(90)
    assert m['quality'] == pytest.approx(1)


def test_triangle_and_inverted_quad_detection():
    tri = element_metrics([(0, 0), (1, 0), (0, 1)])
    assert tri['area'] == pytest.approx(.5)
    assert tri['min_jac'] == pytest.approx(1)
    assert tri['min_angle'] == pytest.approx(45)
    inverted = element_metrics([(0, 0), (0, 1), (1, 1), (1, 0)])
    assert inverted['min_jac'] < 0 and inverted['area'] < 0
