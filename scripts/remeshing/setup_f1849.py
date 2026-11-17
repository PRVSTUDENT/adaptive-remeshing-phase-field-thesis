"""Assemble the separately versioned F1849 comparison from preserved sources."""
from pathlib import Path
import subprocess
import json
import hashlib

r = Path(__file__).resolve().parents[2]
frozen = subprocess.check_output(['git', 'show', 'c8d8588fb:scripts/remeshing/reusable_2d_adaptive_framework.py'], cwd=r).decode('utf-8')
generic = (r/'scripts/remeshing/generalized_2d_adaptive_framework_f1846.py').read_text(encoding='utf-8-sig')
s = frozen
a = s.index('class AdaptiveConfig(object):')
b = s.index('class MeshQualityAuditEngine(object):')
s = s[:a] + generic[generic.index('class AdaptiveConfig(object):'):generic.index('class MeshQualityAuditEngine(object):')] + s[b:]
a = s.index('    @classmethod\n    def build_cae_geometry', s.index('class AbaqusNativeRemeshingEngine'))
b = s.index('    @classmethod\n    def execute_native_remesh', a)
ga = generic.index('    @classmethod\n    def build_cae_geometry', generic.index('class AbaqusNativeRemeshingEngine'))
gb = generic.index('    @classmethod\n    def inspect_donor_fields', ga)
s = s[:a] + generic[ga:gb] + s[b:]
s = s.replace('        if step_name not in odb_src.steps:\n            step_name = list(odb_src.steps.keys())[-1]', "        if step_name not in odb_src.steps:\n            odb_src.close()\n            raise ValueError('Requested damage step missing: ' + step_name)")
s = s.replace('        n_frames = len(step_src.frames)\n', "        n_frames = len(step_src.frames)\n        if n_frames == 0:\n            raise ValueError('Empty damage step')\n        seen_damage = set()\n")
s = s.replace('                    if el in d_max_env:\n', "                    if el in d_max_env:\n                        if math.isnan(float(v.data)) or math.isinf(float(v.data)):\n                            raise ValueError('Nonfinite damage')\n                        seen_damage.add(el)\n")
s = s.replace('        odb_src.close()\n\n        eri_vals', "        odb_src.close()\n        if seen_damage != set(elem_labels):\n            raise ValueError('Incomplete damage mapping')\n\n        eri_vals")
s = s.replace('description="Advancing Crack Temporal Damage Envelope"', 'description="CONSTRUCTED_DAMAGE_ENVELOPE; max SDV1; not native stress error"')
s = s.replace("description='Temporal Error Envelope from Advancing Crack Front'", "description='CONSTRUCTED_DAMAGE_ENVELOPE sizing encoding; not native stress error'")
pos = s.index('        donor_list = ', s.index('class AbaqusNativeRemeshingEngine'))
s = s[:pos] + "        if getattr(config, 'sizing_driver', None) != 'CONSTRUCTED_DAMAGE_ENVELOPE':\n            raise ValueError('Explicit CONSTRUCTED_DAMAGE_ENVELOPE driver required')\n" + s[pos:]
pos = s.index('            # Explicitly ensure CAE model has the target step', s.index('class AbaqusNativeRemeshingEngine'))
s = s[:pos] + '''            final = odb_donor.steps[step_target].frames[-1]
            if 'envelope' not in str(final.description).lower():
                odb_donor.close()
                raise ValueError('Constructed donor must declare damage-envelope provenance')
            if final.frameId != 9999 or 'MISESERI' not in final.fieldOutputs or 'MISESAVG' not in final.fieldOutputs:
                odb_donor.close()
                raise ValueError('Expected synthetic frame ID 9999 and sizing fields')
''' + s[pos:]
s = s[:s.index('def run_method_a_case(')]
s = s.replace('from __future__ import print_function', '''# F1849: CONSTRUCTED_DAMAGE_ENVELOPE primary sizing driver.
# Base: frozen F1779 c8d8588fb; config/adapters/CAD ported from preserved F1846.
# Full-history offline comparison; never qualifies native MISESERI.
from __future__ import print_function''', 1)
s += '''
def prepare_damage_donor(config, source, target, existing_envelope=False):
    """Explicit construction/reuse; no native-first detection or fallback."""
    config.sizing_driver = 'CONSTRUCTED_DAMAGE_ENVELOPE'
    if existing_envelope:
        return source
    return AdvancingDamageEnvelopeBuilder.build_envelope_odb(
        source, target, config.l0, config.max_h, config.error_target / 100.0,
        step_name=config.step_name, damage_variable='SDV1', frame_stride=5, s_base=100.0)
'''
p = r/'scripts/remeshing/generalized_2d_adaptive_framework_damage_envelope_f1849.py'
assert not p.exists(), 'Preserve existing candidate'
compile(s, str(p), 'exec')
p.write_text(s, encoding='utf-8')
base = r/'models/pandey_kumar_mode1/279_f1849_damage_envelope'
base.mkdir(exist_ok=False)
manifest = {'task_id':'F1849-DAMAGE-ENVELOPE-FRAMEWORK','driver':'CONSTRUCTED_DAMAGE_ENVELOPE','qualifies_native_miseseri':False,'base_commit':'c8d8588fb','max_new_pbs':0,'cases':[]}
paths = {
 1: ['models/pandey_kumar_mode1/239_f1772_case1_remesh/PK_F1772_CASE1_ENVELOPE.odb','models/pandey_kumar_mode1/237_f1768_case1_donor/PK_F1769_C1_DONOR.odb'],
 2: ['models/pandey_kumar_mode1/224_f1734_case2_distal_refinement/PK_F1779_CASE2_ENVELOPE.odb','models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb'],
 3: ['models/pandey_kumar_mode1/192_pk_sec43_staggered_job1/PK_SEC43_STAGGERED_JOB1.odb'],
 5: ['models/pandey_kumar_mode1/218_f1726_seven_hole_study/PK_F1726_SEVEN_HOLE_COARSE.odb']}
for cid, target, stem in [(1,20232,'mode1_edge_crack'),(2,17280,'off_axis_hole'),(3,9975,'notched_plate_pins'),(5,15330,'seven_hole')]:
    rel = 'configs/remeshing/f1728_case%d_%s.json' % (cid,stem)
    cfg = json.loads(subprocess.check_output(['git','show','c8d8588fb:'+rel], cwd=r, text=True))
    cfg['sizing_driver'] = 'CONSTRUCTED_DAMAGE_ENVELOPE'
    cfgp = base/('case%d_config.json'%cid)
    cfgp.write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8')
    found = next((v for v in paths[cid] if (r/v).is_file()), None)
    item = {'case_id':cid,'target_F1779':target,'config':cfgp.relative_to(r).as_posix(),'expected_donors':paths[cid],'status':'READY' if found else 'BLOCKED_MISSING_DONOR','donor':found,'existing_envelope':bool(found and 'ENVELOPE' in found),'historical_note':'F1779 cases 3/5 used stress-error donors; all-damage sizing is a different experiment.'}
    if found:
        item.update(donor_bytes=(r/found).stat().st_size, donor_sha256=hashlib.sha256((r/found).read_bytes()).hexdigest())
    manifest['cases'].append(item)
(base/'inventory.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print([(c['case_id'],c['status']) for c in manifest['cases']])
