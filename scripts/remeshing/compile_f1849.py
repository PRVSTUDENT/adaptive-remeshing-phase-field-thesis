"""Compile measured F1849 evidence; unavailable cases stay explicitly blocked."""
from pathlib import Path
import sys,json,hashlib,ast,subprocess
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.remeshing.generalized_2d_adaptive_framework_damage_envelope_f1849 import MeshQualityAuditEngine
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

BASE=ROOT/'models/pandey_kumar_mode1/279_f1849_damage_envelope'
SOURCE=ROOT/'scripts/remeshing/generalized_2d_adaptive_framework_damage_envelope_f1849.py'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def plot(ax,c):
    cid=c['case_id']
    if c['status'].startswith('BLOCKED'):
        ax.text(.5,.55,'Case %d: BLOCKED\nRequired damage Job-1/envelope donor absent'%cid,
                ha='center',va='center',transform=ax.transAxes,fontsize=12)
        ax.text(.5,.35,'No historical mesh substituted',ha='center',transform=ax.transAxes)
        ax.set_axis_off();return
    a=c['audit'];n,q,t=MeshQualityAuditEngine.parse_physical_inp(str(ROOT/a['physical_mesh']))
    polygons=[[n[i] for i in conn] for conn in list(q.values())+list(t.values())]
    ax.add_collection(PolyCollection(polygons,facecolors='white',edgecolors='#233044',linewidths=.12))
    ax.autoscale();ax.set_aspect('equal');ax.set_xlabel('x [mm]');ax.set_ylabel('y [mm]')
    ratio=a['refinement_ratio_far_to_core']
    ax.set_title('Case %d: %s elements | %.2f%% quads\nGate 06: %.3fx %s\nCONSTRUCTED_DAMAGE_ENVELOPE'%(
        cid,format(a['total_elements'],','),a['quad_fraction_pct'],ratio,'PASS' if ratio>=2 else 'FAIL'),fontsize=10,pad=12)

def main():
    d=json.loads((BASE/'inventory.json').read_text())
    d['source']={'path':SOURCE.relative_to(ROOT).as_posix(),'bytes':SOURCE.stat().st_size,'sha256':sha(SOURCE),'lines':len(SOURCE.read_text().splitlines())}
    d['frozen_preservation']={}
    for name in ['scripts/remeshing/reusable_2d_adaptive_framework.py','scripts/remeshing/generalized_2d_adaptive_framework_f1846.py']:
        p=ROOT/name;d['frozen_preservation'][name]=sha(p)
    for c in d['cases']:
        ap=BASE/('case%d'%c['case_id'])/'audit.json'
        if ap.exists():
            a=json.loads(ap.read_text());assert a['source_sha256']==d['source']['sha256'];assert sha(ROOT/a['physical_mesh'])==a['mesh_sha256']
            c.update(status='GENERATED_COMPARISON_NOT_ACCEPTED',audit=a)
            # Independently compute area and count resolution over the entire mesh.
            n,q,t=MeshQualityAuditEngine.parse_physical_inp(str(ROOT/a['physical_mesh']))
            areas=[]
            for conn in list(q.values())+list(t.values()):
                pts=[n[i] for i in conn]
                ar=abs(sum(pts[j][0]*pts[(j+1)%len(pts)][1]-pts[(j+1)%len(pts)][0]*pts[j][1] for j in range(len(pts))))/2
                areas.append(ar)
            cfg=json.loads((ROOT/c['config']).read_text());l0=cfg['material']['length_scale_l0_mm']
            c['global_resolution']={'area_mm2':sum(areas),'area_pct_h_le_l0':100*sum(x for x in areas if x<=l0*l0)/sum(areas),'area_pct_h_le_half_l0':100*sum(x for x in areas if x<=(l0/2)**2)/sum(areas)}
    d['images']=[]
    dest=ROOT/'results/figures';dest.mkdir(exist_ok=True)
    for c in d['cases']:
        if 'audit' not in c:continue
        fig,ax=plt.subplots(figsize=(7,8));plot(ax,c);fig.tight_layout()
        for ext in ['png','pdf']:
            p=dest/('fig_f1849_case_%d_mesh.%s'%(c['case_id'],ext));fig.savefig(p,dpi=300)
            d['images'].append({'case_id':c['case_id'],'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size,'mesh_sha256':c['audit']['mesh_sha256'],'source_sha256':d['source']['sha256']})
        plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(14,14),layout='constrained')
    for ax,c in zip(axes.flat,d['cases']):plot(ax,c)
    fig.suptitle('F1849: constructed damage-envelope comparison\nTwo generated cases; two missing-donor blocks — not a complete regression',fontsize=15)
    for ext in ['png','pdf']:
        p=dest/('fig_f1849_partial_composite.'+ext);fig.savefig(p,dpi=300)
        d['images'].append({'case_id':'composite','path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size,'source_sha256':d['source']['sha256']})
    plt.close(fig)
    out=ROOT/'results/validation/f1849_damage_envelope_summary.json';out.write_text(json.dumps(d,indent=2)+'\n')
    lines=SOURCE.read_text().splitlines();loc={name:next(i+1 for i,x in enumerate(lines) if name in x) for name in ['class Generic2DGeometryAdapter','def analytical_damage_sizing','def build_envelope_odb','def prepare_damage_donor']}
    report=['# F1849 constructed damage-envelope framework — partial numerical result','',
    'Status: PARTIAL / MASTER_GOAL_OPEN. Zero new PBS; cumulative submission accounting remains 36.',
    'This is CONSTRUCTED_DAMAGE_ENVELOPE sizing, SEPARATE_COMPARISON, qualifies_native_miseseri=false. Full sampled history is used offline; this is not a causal online prediction.',
    '', '## Numerical finding',
    'Case 2 reproduces the F1779 element count. Case 5 does not; F1779 used native stress-error sizing for Case 5, whereas this experiment constructs a damage-sizing envelope. Cases 1 and 3 lack required local source Job-1 or damage-envelope ODBs. Existing recovery ODBs were not substituted.',
    'The Case 2 supplied envelope is frame ID 9999, description `Calibrated Advancing Crack Envelope v2`, SHA 0aa96015... . Its prior calibration is not reconstructed or relabeled as unmodified F1779.',
    '', '|Case|F1779 count|Fresh count|Delta %|Quads %|min detJ|max AR|Gate06|Status|','|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for c in d['cases']:
        if 'audit' in c:
            a=c['audit'];linestr='|%d|%d|%d|%+.2f|%.2f|%.5g|%.3f|%.3f|COMPARISON ONLY|'%(c['case_id'],c['target_F1779'],a['total_elements'],a['delta_F1779_pct'],a['quad_fraction_pct'],a['min_det_j'],a['max_aspect_ratio'],a['refinement_ratio_far_to_core']);report.append(linestr)
        else:report.append('|%d|%d|—|—|—|—|—|—|BLOCKED_MISSING_DONOR|'%(c['case_id'],c['target_F1779']))
    report+=['','## Frozen candidate and scope',
    'Derived from Git revision c8d8588fb: frozen F1779 sizing, audits and remesh execution. Generic configuration, adapters and CAD construction are ported from the preserved F1846 file. Native-first routing is not inherited. No frozen production source or UEL was edited.',
    'Candidate: `%s`; %d bytes; %d lines; SHA256 `%s`.'%(d['source']['path'],d['source']['bytes'],d['source']['lines'],d['source']['sha256']),
    'Code locations: '+json.dumps(loc),
    'Shared damage thresholds remain 0.5 / 0.1 / 0.01, factors 2.5 / 1.2, stride 5, s_base 100, frame ID 9999. Percentage target is converted to a dimensionless sizing encoding. Existing envelopes are reused without rewriting.',
    '', '## Donor inventory']
    for c in d['cases']:
        report.append('- Case %d: %s'%(c['case_id'],c['status']))
        if c['donor']:report.append('  `%s`: %d bytes, SHA256 `%s`.'%(c['donor'],c['donor_bytes'],c['donor_sha256']))
        else:report.extend('  Missing: `%s`.'%v for v in c['expected_donors'])
    report+=['','## Verification and limitations',
    'Actual mesh counts, source/donor/mesh hashes and FE audits were computed. Global area-weighted resolution is retained in results/validation/f1849_damage_envelope_summary.json. Historical critical-region gates are not replaced by global percentages. No claim of scientific acceptance or complete four-case regression is made.',
    'Original implementation failures preserved: initial CAE entry failed because __file__ is absent in its noGUI namespace; fixed by explicit F1849_ROOT. Existing Case 2 envelope was initially rejected by an overly narrow description check; read-only inspection proved its calibrated-envelope frame ID 9999 before allowing envelope provenance. No source donor was edited.',
    'Candidate source guards reject absent damage steps, empty histories, nonfinite damage and incomplete selected-element damage coverage. New geometries still require compatible donor topology and loading; no universal accuracy claim.',
    '', '## Images and committed artifact manifest',
    'Fresh standalone images exist only for generated Cases 2 and 5. The 2x2 composite displays explicit blocked panels for Cases 1 and 3. No old mesh or image is presented as fresh.',
    'Commit-pinned manifest is recorded after artifact commit in results/validation/f1849_image_manifest.json.']
    (ROOT/'docs/validation/F1849_DAMAGE_ENVELOPE_FRAMEWORK_REPORT.md').write_text('\n\n'.join(report)+'\n',encoding='utf-8')
    print([(c['case_id'],c['status'],c.get('audit',{}).get('total_elements')) for c in d['cases']])

if __name__=='__main__':main()
