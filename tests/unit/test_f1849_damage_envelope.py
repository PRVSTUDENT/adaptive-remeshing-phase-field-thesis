"""Offline checks of driver isolation, sizing behaviour and numerical artifact integrity."""
from pathlib import Path
import ast
import hashlib
import importlib.util
import json

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'scripts/remeshing/generalized_2d_adaptive_framework_damage_envelope_f1849.py'
spec=importlib.util.spec_from_file_location('f1849',SOURCE)
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)

def test_shared_sizing_is_monotone_and_scaled_by_length():
    fun=f.AdvancingDamageEnvelopeBuilder.analytical_damage_sizing
    values=[fun(d/100.,.01,.04) for d in range(101)]
    assert all(a>=b for a,b in zip(values,values[1:]))
    assert abs(values[-1]-.004)<1e-12
    assert all(abs(fun(d/100.,.02,.08)-2*values[d])<1e-12 for d in range(101))

def test_driver_is_explicit_and_no_region_classifier_in_remesh():
    tree=ast.parse(SOURCE.read_text())
    cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='AbaqusNativeRemeshingEngine')
    fn=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='execute_native_remesh')
    assert not any(isinstance(x,ast.Attribute) and x.attr=='classify_region' for x in ast.walk(fn))
    text=ast.get_source_segment(SOURCE.read_text(),fn)
    assert 'CONSTRUCTED_DAMAGE_ENVELOPE' in text and '9999' in text
    assert 'inspect_donor_fields' not in text

def test_generic_geometry_configuration_changes_domain():
    d={'case_id':'unfamiliar','geometry_type':'GENERIC_2D','geometry':{'plate_width':2,'plate_height':2,'outer_boundary':[[0,0],[2,0],[2,2],[0,2]]},'material':{'length_scale_l0_mm':.01},'remeshing_rule':{'error_target':5,'min_element_size_mm':.001,'max_element_size_mm':.1}}
    cfg=f.AdaptiveConfig(d)
    adapter=f.Generic2DGeometryAdapter(cfg)
    assert adapter.is_inside_domain(.5,.5)
    assert not adapter.is_inside_domain(3,3)

def test_reported_artifacts_have_exact_hashes_and_counts():
    d=json.loads((ROOT/'results/validation/f1849_damage_envelope_summary.json').read_text())
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==d['source']['sha256']
    for c in d['cases']:
        if c['donor']:
            assert hashlib.sha256((ROOT/c['donor']).read_bytes()).hexdigest()==c['donor_sha256']
        if 'audit' in c:
            a=c['audit'];p=ROOT/a['physical_mesh']
            assert hashlib.sha256(p.read_bytes()).hexdigest()==a['mesh_sha256']
            _,q,t=f.MeshQualityAuditEngine.parse_physical_inp(str(p))
            assert len(q)+len(t)==a['total_elements']
    for im in d['images']:
        assert hashlib.sha256((ROOT/im['path']).read_bytes()).hexdigest()==im['sha256']

def test_missing_cases_are_not_replaced_by_old_meshes():
    d=json.loads((ROOT/'results/validation/f1849_damage_envelope_summary.json').read_text())
    for c in d['cases']:
        if not c['donor']:
            assert c['status']=='BLOCKED_MISSING_DONOR' and 'audit' not in c
            assert all(not (ROOT/v).exists() for v in c['expected_donors'])
