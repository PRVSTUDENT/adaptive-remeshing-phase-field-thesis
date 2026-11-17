from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2]
B=ROOT/'models/pandey_kumar_mode1/280_f1850_donor_recovery'

def test_snapshot_fields_topology_and_reconstruction():
    for cid in (1,2,3,5):
        d=json.loads((B/('case%d_donor.json'%cid)).read_text());p=d['mesh_fields']
        assert hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':')).encode()).hexdigest()==d['mesh_fields_sha256']
        labels={e[0] for e in p['elements']};nodes={n[0] for n in p['nodes']}
        assert all(set(e[2])<=nodes for e in p['elements'])
        assert all({v[0] for v in vals}==labels for vals in p['fields'].values())
        a=json.loads((B/('case%d'%cid)/'audit.json').read_text())
        assert a['field_roundtrip_exact'] and a['donor_logical_sha256']==d['mesh_fields_sha256']
        assert a['min_det_j']>0

def test_preserved_controls_and_negative_results():
    d=json.loads((ROOT/'results/validation/f1850_donor_recovery_summary.json').read_text())
    counts={c['case_id']:c['audit']['total_elements'] for c in d['cases']}
    assert counts=={1:20193,2:17280,3:45009,5:4375}
    assert d['new_pbs']==0 and d['master_goal_status']=='OPEN'
    assert all(not c['audit']['qualifies_native_miseseri'] for c in d['cases'])

def test_frozen_framework_and_published_artifacts():
    d=json.loads((ROOT/'results/validation/f1850_donor_recovery_summary.json').read_text())
    assert d['source_sha256']=='694e7ababd739e6f5cbca5597cb39ada500116895b8c4a21ca470b64f9247096'
    for c in d['cases']:
        for path,h in [(c['snapshot'],c['snapshot_sha256']),(c['audit']['physical_mesh'],c['audit']['mesh_sha256'])]:
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h
    for im in d['images']:assert hashlib.sha256((ROOT/im['path']).read_bytes()).hexdigest()==im['sha256']
