from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[2]
def summary():return json.loads((R/'results/validation/f1851_diagnostics_summary.json').read_text())
def test_actual_mapping_and_missing_volume_are_distinguished():
    for m in summary()['mapping']:
        assert m['maximum_coordinate_difference']==0 and m['connectivity_mismatches']==0
        assert all(v==0 for v in m['scalar_differences'].values())
        assert m['source_EVOL_present'] is False
        assert max(abs(x-1) for x in m['EVOL_to_area_ratio_range'])<1e-6
    c=summary()['comparisons']['case2_original337']
    assert c['status']=='FAILED_SUPPORTED_PATH_TEST' and 'EVOL' in c['error']
def test_original_vs_extracted_native_remesh_identity():
    c=summary()['comparisons']
    for step in ('Step-1','Step-2'):
        a,b=c['f1720_%s_original'%step],c['f1720_%s_extracted'%step]
        assert a['status']==b['status']=='GENERATED'
        assert a['body_sha256']==b['body_sha256']
        assert a['audit']['total_elements']==b['audit']['total_elements']
def test_count_cannot_substitute_for_area_coverage():
    c=summary()['coverage']['F1840']['distal_report']
    assert 91<c['count_pct_half_l0']<92 and 69<c['area_pct_half_l0']<71
    assert summary()['new_pbs']==0 and summary()['master_goal_status']=='OPEN'
def test_frozen_sources_and_original_native_fields():
    assert hashlib.sha256((R/'scripts/remeshing/reusable_2d_adaptive_framework.py').read_bytes()).hexdigest()=='b0857c521ae8e212c74f711cc3373ad57b081167727104905a0f4d2fbbda0129'
    assert hashlib.sha256((R/'scripts/remeshing/generalized_2d_adaptive_framework_damage_envelope_f1849.py').read_bytes()).hexdigest()=='694e7ababd739e6f5cbca5597cb39ada500116895b8c4a21ca470b64f9247096'
    stats=summary()['field_statistics'];f=next(x for x in stats if x['snapshot']=='f1720_step2_178.json')
    assert .52<f['maximum_IP_damage']<.53
def test_triangle_anomaly_is_distinct_from_ip_accounting():
    stats=summary()['field_statistics']
    c=next(x for x in stats if x['snapshot']=='case2_original337.json')['element_type_audit']
    assert c['CPE3']['elements']==c['CPE3']['zero_stress']==c['CPE3']['zero_base']==74
    assert c['CPE4']['zero_stress']==0
    assert 64<c['CPE3']['outside_error_proxy_share_pct']<65
    f=next(x for x in stats if x['snapshot']=='f1720_step2_178.json')
    assert f['missing_stress_elements']==f['missing_damage_elements']==0
    assert f['element_type_audit']['CPE4']['elements']==2663
    assert f['element_type_audit']['CPE3']['elements']==84
