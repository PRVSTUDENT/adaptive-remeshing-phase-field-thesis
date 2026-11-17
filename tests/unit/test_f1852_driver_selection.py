from pathlib import Path
import json,hashlib,pytest
from scripts.remeshing.generalized_2d_adaptive_framework_driver_selection_f1852 import select_driver
R=Path(__file__).resolve().parents[2]
def summary():return json.loads((R/'results/validation/f1852_driver_selection_summary.json').read_text())
def test_measured_selection_and_fail_closed_native_gate():
    strong={'max_damage':.5,'fraction_ge_core':.01,'d_core':.5}
    assert select_driver(strong,{})=='CONSTRUCTED_DAMAGE_ENVELOPE'
    assert select_driver(dict(strong,max_damage=1.0022),{})=='CONSTRUCTED_DAMAGE_ENVELOPE'
    weak=dict(strong,max_damage=.476,fraction_ge_core=0)
    assert select_driver(weak,{'accepted':True})=='NATIVE_ABAQUS_STRESS_RECOVERY_ERROR'
    with pytest.raises(ValueError,match='BLOCKED'):select_driver(weak,{'accepted':False})
    with pytest.raises(ValueError):select_driver(dict(weak,max_damage=float('nan')),{'accepted':True})
def test_four_fresh_meshes_preserve_strong_damage_controls():
    s=summary();assert len(s['cases'])==4
    for c in s['cases']:
        a=c['audit'];assert a['framework_sha256']==s['source_sha256']
        assert hashlib.sha256((R/a['physical_mesh']).read_bytes()).hexdigest()==a['mesh_sha256']
        assert a['min_det_j']>0 and a['max_aspect_ratio']<4
        if c['case_id']!=5:assert c['body_identical_F1850'] and a['driver']=='CONSTRUCTED_DAMAGE_ENVELOPE'
def test_native_signal_is_audited_and_case5_failure_retained():
    s=summary();g=s['native_gate'];assert g['accepted']
    assert g['element_type_audit']['CPE3']['elements']==101
    assert g['element_type_audit']['CPE3']['zero_stress_tensors']==0
    assert g['triangle_total_error_proxy_pct']<1
    c=next(c for c in s['cases'] if c['case_id']==5)
    assert c['audit']['total_elements']==15411 and c['previous_F1850']['count']==4375
    assert c['audit']['driver']=='NATIVE_ABAQUS_STRESS_RECOVERY_ERROR'
    assert c['audit']['refinement_ratio_far_to_core']<2
    assert not c['audit']['qualifies_native_miseseri']
def test_frozen_assets_and_genuine_image_hashes():
    s=summary();assert s['new_pbs']==0 and s['master_goal_status']=='OPEN'
    for rel,h in s['frozen_sources'].items():assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==h
    for im in s['images']:assert hashlib.sha256((R/im['path']).read_bytes()).hexdigest()==im['sha256']
