from abaqus import *
from abaqusConstants import *
import os, sys, shutil

sys.path.append('scripts/remeshing')
from test_stage_b_selective_aggregation import build_base_cad_model

repo_root = os.path.abspath('.')
odb_path = os.path.join(repo_root, 'runs', 'f1684_multistep_recovery', 'PK_HOLE_MULTISTEP_RECOVERY.odb')
cand_dir = os.path.join(repo_root, 'models', 'pandey_kumar_mode1', '176_method_a_plate_with_hole', 'candidates')
odb = session.openOdb(name=odb_path)

for e_sec in [8.0, 12.0]:
    model_name = 'MODEL_SEL_E%02d' % int(e_sec)
    Mdb()
    m = build_base_cad_model(model_name)
    p = m.parts['PlateWithHole']
    reg = m.rootAssembly.sets['All_elem']

    m.RemeshingRule(name='Rule_CandC_5pct', stepName='RECOVERY_C', region=reg,
                    variables=('MISESERI',), sizingMethod=UNIFORM_ERROR, errorTarget=5.0,
                    specifyMinSize=True, specifyMaxSize=True, minElementSize=0.0015, maxElementSize=0.0200,
                    coarseningFactor=NOT_ALLOWED, refinementFactor=10)
    m.RemeshingRule(name='Rule_Terminal_Selective', stepName='RECOVERY_TERMINAL', region=reg,
                    variables=('MISESERI',), sizingMethod=UNIFORM_ERROR, errorTarget=e_sec,
                    specifyMinSize=True, specifyMaxSize=True, minElementSize=0.0015, maxElementSize=0.0200,
                    coarseningFactor=NOT_ALLOWED, refinementFactor=10)
    m.adaptiveRemesh(odb=odb)
    job_name = 'PK_HOLE_SEL_E%02d_PHYS' % int(e_sec)
    j = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)
    dest_inp = os.path.join(cand_dir, '%s.inp' % job_name)
    shutil.copyfile('%s.inp' % job_name, dest_inp)
    print('Generated %s: %d elements' % (job_name, len(p.elements)))
odb.close()
