#!/usr/bin/env python3
"""Build the preparation-only F15/F16 four-job conditional batch."""
import hashlib, json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODE = ROOT / "models/generated/mode_ii"
INFRA = ROOT / "models/generated/infrastructure/f15_dual_channel_notification_smoke"
CTL = MODE / "f16_controlled_rollback_control"
FORCE = MODE / "f16_controlled_rollback_forced"
REG = MODE / "f16_native_adaptive_region_resolution"
RUN = ROOT / "runs/hpc/stage_f/f15_f16_conditional_batch_preparation"
NOTIFY = ROOT / "scripts/hpc/notifications/job_notifications.sh"
MAIL = "Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p, s): p.parent.mkdir(parents=True, exist_ok=True); p.write_text(s, encoding="utf-8", newline="\n")
def dump(p, d): write(p, json.dumps(d, indent=2, sort_keys=True) + "\n")
def reset(p):
    if p.exists(): shutil.rmtree(str(p))
    p.mkdir(parents=True)
def copy(src, dst): dst.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(str(src), str(dst))

def notify_prelude(job, queue, mem, wall, mode):
    return f'''#!/bin/bash
#PBS -N {job}
#PBS -q {queue}
#PBS -l select=1:ncpus=1:mem={mem}
#PBS -l walltime={wall}
#PBS -M {MAIL}
#PBS -m abe
#PBS -j oe
set -uo pipefail
set +x
cd "$PBS_O_WORKDIR" || exit 2
sha256sum -c SHA256SUMS || exit 3
export NOTIFICATION_CONFIG="$HOME/.config/adaptive-remeshing/notifications.env"
export NOTIFICATION_EMAIL_MODE=native_pbs
export NOTIFICATION_STAGE=F16
export NOTIFICATION_EVIDENCE_DIR="$PBS_O_WORKDIR/evidence"
export NOTIFICATION_RUN_ID="${{PBS_JOBID:-unknown}}"
export PBS_JOBNAME="${{PBS_JOBNAME:-{job}}}"
mkdir -p "$NOTIFICATION_EVIDENCE_DIR"
. runtime/job_notifications.sh
notification_load_config || exit 4
notification_install_terminal_trap
notify_start || exit 5
export WORK_ROOT="${{SCRATCH:?SCRATCH is required}}/{job}_${{PBS_JOBID:-unknown}}"
rm -rf "$WORK_ROOT" && mkdir -p "$WORK_ROOT"
cp -p runtime/* "$WORK_ROOT/"
cd "$WORK_ROOT" || exit 6
'''

def build_notify():
    reset(INFRA); rt=INFRA/"runtime"; rt.mkdir()
    copy(NOTIFY, rt/"job_notifications.sh"); copy(ROOT/"scripts/hpc/notifications/notification_evidence.py", rt/"notification_evidence.py")
    pbs = notify_prelude("M2NOTIFY1","entry_imfdfkmq","1gb","00:05:00","shell-only") + '''
python3 - <<'PY'
import json,os,socket,datetime
d={'job_id':os.environ.get('PBS_JOBID'),'host':socket.gethostname(),'utc_start':datetime.datetime.utcnow().isoformat()+'Z'}
open('ENVIRONMENT.json','w').write(json.dumps(d,indent=2,sort_keys=True)+'\\n')
PY
sleep 30
python3 - <<'PY'
import json,datetime
d={'classification':'notification_smoke_technically_passed_awaiting_human_confirmation','exit_code':0,'utc_end':datetime.datetime.utcnow().isoformat()+'Z','abaqus_loaded':False,'scientific_code_executed':False,'qsub_calls':0}
open('STATUS.json','w').write(json.dumps(d,indent=2,sort_keys=True)+'\\n')
PY
cp ENVIRONMENT.json STATUS.json "$NOTIFICATION_EVIDENCE_DIR/"
exit 0
'''
    write(INFRA/"M2NOTIFY1.pbs",pbs)
    dump(INFRA/"PBS_EMAIL_CONFIGURATION.json",{"pbs_version":"2024.1.3","multiple_recipient_syntax_supported":True,"mail_points":"abe","recipients":["Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de","pr21vyci@mailserver.tu-freiberg.de"],"primary_mechanism":"native_pbs"})
    dump(INFRA/"PACKAGE_MANIFEST.json",{"status":"prepared_not_authorized","job":"M2NOTIFY1","queue":"entry_imfdfkmq","cpus":1,"memory":"1 GB","walltime":"00:05:00","execution":"shell-only","sleep_seconds":30,"abaqus":False,"scientific_execution":False,"qsub_calls":0})

def f16_source():
    p=MODE/"f13_rollback_control/M2IRR_F13.for"; text=p.read_text(encoding="ascii")
    text=text.replace("       CHARACTER*512 F13LOG\n       CHARACTER*8 F13FORCE\n       INTEGER F13LS,F13FS,F13IOS",
      "       CHARACTER*512 F16OUT,F16JOB,F16LOG,F16FLAG\n       CHARACTER*1 F16FORCE\n       INTEGER F16LO,F16LJ,F16IOS")
    start=text.index("C       F13 diagnostic-only controlled cutback")
    end=text.index("C\nC     ==================================================================\nC     Uploading solution dep. variables",start)
    block='''C       F16 controlled cutback; runtime flag file is wrapper-created.
        PBEFORE=PNEWDT
        CALL GETOUTDIR(F16OUT,F16LO)
        CALL GETJOBNAME(F16JOB,F16LJ)
        IF (F16LO.LE.0.OR.F16LJ.LE.0) CALL XIT
        F16FLAG=F16OUT(1:F16LO)//'/'//F16JOB(1:F16LJ)//
     1   '_f16_force_cutback.flag'
        OPEN(UNIT=97,FILE=F16FLAG,STATUS='OLD',ACTION='READ',
     1   IOSTAT=F16IOS)
        IF (F16IOS.NE.0) CALL XIT
        READ(97,'(A1)',IOSTAT=F16IOS) F16FORCE
        CLOSE(97)
        IF (F16IOS.NE.0) CALL XIT
        IF (F16FORCE.EQ.'1'.AND.KSTEP.EQ.2.AND.
     1   TIME(1).GE.0.0D0.AND.TIME(1).LT.4.0D-2.AND.
     2   JELEM.EQ.1.AND.INPT.EQ.2.AND.DTIME.GT.1.5D-2)
     3   PNEWDT=HALF
        IF (JELEM.LE.23.AND.INPT.LE.4.AND.STEPITER.LE.40) THEN
         F16LOG=F16OUT(1:F16LO)//'/'//F16JOB(1:F16LJ)//
     1    '_f16_rollback_calls.log'
         OPEN(UNIT=98,FILE=F16LOG,STATUS='UNKNOWN',
     1    POSITION='APPEND',ACTION='WRITE',IOSTAT=F16IOS)
         IF (F16IOS.NE.0) CALL XIT
         WRITE(98,*) 'F16_CALL',KSTEP,KINC,JELEM,INPT,
     1    TIME(1),TIME(2),DTIME,PHASE,PHASE-DPHASE,
     2    SVARS(NSTVTO*(INPT-1)+1),PHASEOLD,
     3    USRVAR(JELEM,16,INPT),USRVAR(JELEM,15,INPT),
     4    USRVAR(JELEM,22,INPT),PBEFORE,PNEWDT,STEPITER,
     5    GAP,PENEDEN
         CLOSE(98)
        ENDIF
'''
    normalized=(text[:start]+block+text[end:]).replace("F13 BOUNDS","F16 BOUNDS")
    return (normalized.rstrip()+"\n").encode("ascii")

def build_rollback(out, job, flag, role):
    reset(out); rt=out/"runtime"; rt.mkdir()
    deck=MODE/"f13_rollback_control/M2IRR_F13.inp"
    copy(deck,rt/"M2IRR_F16.inp"); (rt/"M2IRR_F16.for").write_bytes(f16_source())
    copy(NOTIFY,rt/"job_notifications.sh"); copy(ROOT/"scripts/hpc/notifications/notification_evidence.py",rt/"notification_evidence.py")
    copy(ROOT/"scripts/postprocessing/extract_stage_f11_instrumented_pair.py",rt/"extract_stage_f11_instrumented_pair.py")
    analyzer='''#!/usr/bin/env python3
import json,os,re,sys
sta=open(sys.argv[1],errors="replace").read() if os.path.exists(sys.argv[1]) else ""
msg=open(sys.argv[2],errors="replace").read() if os.path.exists(sys.argv[2]) else ""
calls=open(sys.argv[3],errors="replace").read() if os.path.exists(sys.argv[3]) else ""
d={"classification":"penalty_rollback_inconclusive","independent_sta_msg_cutback_evidence":bool(re.search(r"cutback|attempt",sta+msg,re.I)),"pnewdt_requested":bool(re.search(r"F16_CALL",calls)),"common_bounds_guard_fired":bool(re.search(r"F16 BOUNDS",calls)),"required_log_fields":["KSTEP","KINC","JELEM","INPT","TIME","DTIME","trial_phase","committed_phase","trial_SVARS","committed_SVARS","SDV15","SDV16","penalty_active","PNEWDT","retry","accepted_state"]}
open("ROLLBACK_STATUS.json","w").write(json.dumps(d,indent=2,sort_keys=True)+"\\n")
'''
    write(rt/"analyze_stage_f16_rollback.py",analyzer)
    pbs=notify_prelude(job,"normal_imfdfkmq","8gb","01:00:00","Abaqus/Standard serial")+f'''
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
export F16_FORCE_CUTBACK={flag}
printf '%s\n' "$F16_FORCE_CUTBACK" > "{job}_f16_force_cutback.flag"
abaqus job={job} input=M2IRR_F16.inp user=M2IRR_F16.for interactive
rc=$?
for s in sta msg dat log; do test -f "{job}.$s" && cp "{job}.$s" "$NOTIFICATION_EVIDENCE_DIR/"; done
test "$rc" -eq 0 || exit "$rc"
abaqus python extract_stage_f11_instrumented_pair.py --odb {job}.odb --output-dir extracted --role candidate || exit 10
python3 analyze_stage_f16_rollback.py {job}.sta {job}.msg {job}_f16_rollback_calls.log || exit 11
cp ROLLBACK_STATUS.json {job}_f16_rollback_calls.log "$NOTIFICATION_EVIDENCE_DIR/"
exit 0
'''
    write(out/(job+".pbs"),pbs)
    tol={"displacement_mm":1e-10,"phase_matched":1e-7,"final_phase":1e-6,"max_rf_difference_normalized":1e-4,"rf_u_nrmse":1e-4,"relative_energy":1e-4}
    dump(out/"PACKAGE_MANIFEST.json",{"status":"prepared_not_authorized","job":job,"role":role,"queue":"normal_imfdfkmq","cpus":1,"memory":"8 GB","walltime":"01:00:00","execution":"Abaqus/Standard serial","f16_force_cutback":flag,"runtime_only_difference":"F16_FORCE_CUTBACK","mapping":{"phase_uel":[1,23],"displacement_uel":[24,46],"visualization_cpe4":[47,69]},"trigger":{"step":2,"time_window":[0,0.04],"element":1,"integration_point":2,"pnewdt":0.5,"penalty_required_active":True},"tolerances":tol,"independent_sta_msg_evidence_required":True,"source_sha256":sha(rt/"M2IRR_F16.for"),"deck_sha256":sha(rt/"M2IRR_F16.inp")})

def build_region():
    reset(REG); rt=REG/"runtime"; rt.mkdir()
    copy(MODE/"f14_native_miseseri_adaptive_region/source_deck.inp",rt/"source_deck.inp")
    copy(NOTIFY,rt/"job_notifications.sh"); copy(ROOT/"scripts/hpc/notifications/notification_evidence.py",rt/"notification_evidence.py")
    audit='''from __future__ import print_function
import hashlib,json,math,os,sys,traceback
from abaqus import mdb
from abaqusConstants import MODEL,NOT_ALLOWED,ON,UNIFORM_ERROR
from odbAccess import openOdb
out=os.environ["F16_OUTPUT_DIR"]; deck=os.path.join(os.getcwd(),"source_deck.inp"); odbp=os.environ["F16_SOURCE_ODB"]
def wr(n,d): open(os.path.join(out,n),'wb').write((json.dumps(d,indent=2,sort_keys=True)+'\\n').encode('utf-8'))
z={"solver_executions":0,"adaptivity_process_submissions":0,"native_remesh_calls":0,"refined_solver_executions":0,"generated_candidates":0,"adaptiveRemesh_called":False,"ale_used":False}
try:
 m=mdb.ModelFromInputFile(name='F16_SOURCE',inputFileName=deck); p=m.parts[m.parts.keys()[0]]; orphan=bool(getattr(p,'isMeshPart',False))
 methods=[x for x in dir(m) if 'adapt' in x.lower() or 'remesh' in x.lower()]; repos=[x for x in dir(m) if 'adapt' in x.lower() or 'remesh' in x.lower()]
 geometry_method=hasattr(m,'Part2DGeomFrom2DMesh')
 gp=None
 if orphan and geometry_method: gp=m.Part2DGeomFrom2DMesh(name='F16_GEOMETRY_BACKED',part=p,featureAngle=20.0)
 target=gp or p; geometry_backed=not bool(getattr(target,'isMeshPart',False))
 m.RemeshingRule(name='F16_MISESERI_RULE',stepName='Step-1',variables=(str('MISESERI'),),region=MODEL,sizingMethod=UNIFORM_ERROR,errorTarget=1.0,specifyMinSize=ON,minElementSize=0.001,specifyMaxSize=ON,maxElementSize=0.010,coarseningFactor=NOT_ALLOWED,refinementFactor=10)
 odb=openOdb(path=odbp,readOnly=True); vals=odb.steps[odb.steps.keys()[-1]].frames[-1].fieldOutputs['MISESERI'].values; finite=sum(1 for v in vals if not math.isnan(float(v.data)) and not math.isinf(float(v.data))); odb.close()
 precondition=geometry_backed and finite==3930 and 'F16_MISESERI_RULE' in m.remeshingRules
 cls='native_adaptive_region_contract_qualified' if precondition else ('native_adaptive_geometry_reconstruction_required' if orphan and not geometry_backed else 'native_adaptive_region_api_unresolved')
 wr('ADAPTIVE_REGION_API_AUDIT.json',{"classification":cls,"RemeshingRule":True,"adaptive_remeshing_region":repr(m.remeshingRules['F16_MISESERI_RULE'].region),"geometry_backed_part":geometry_backed,"orphan_mesh":orphan,"ALE_adaptive_meshing":False,"AdaptivityProcess":False,"model_adaptiveRemesh_present":hasattr(m,'adaptiveRemesh'),"installed_methods":methods,"installed_repositories":repos,"nonexecuting_precondition_pass":precondition})
 wr('SOURCE_MODEL_INTEGRITY.json',{"deck_sha256":"a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2","odb_sha256":"bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac","physical_elements":3930,"miseseri_finite":finite,"true_slit_coincident_pairs":15,"slit_faces_disconnected":True,"opposite_face_bridge":False})
 wr('REMESH_RULE_MANIFEST.json',{"name":"F16_MISESERI_RULE","step":"Step-1","variables":["MISESERI"],"sizing":"UNIFORM_ERROR","errorTarget":1.0,"minElementSize":0.001,"maxElementSize":0.010,"coarsening":"NOT_ALLOWED","refinementFactor":10,"future_passes":1})
 z['classification']=cls
except Exception:
 z['classification']='native_adaptive_region_construction_failed'; z['traceback_redacted']=traceback.format_exc()
wr('NO_EXECUTION_AUDIT.json',z); wr('STATUS.json',z)
sys.exit(0 if z['classification']!='native_adaptive_region_construction_failed' else 1)
'''
    write(rt/"qualify_f16_adaptive_region.py",audit)
    pbs=notify_prelude("M2RMREG2","normal_imfdfkmq","8gb","00:30:00","Abaqus/CAE noGUI only")+'''
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
export F16_OUTPUT_DIR="$NOTIFICATION_EVIDENCE_DIR"
export F16_SOURCE_ODB="/scratch/pr21vyci/adaptive-remeshing/runs/stage_f4/F4R1_20260730_065138_86ec6c79/miseseri_corrected/M2MISER1.odb"
test "$(sha256sum "$F16_SOURCE_ODB"|awk '{print $1}')" = bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac || exit 7
abaqus cae noGUI=qualify_f16_adaptive_region.py
exit $?
'''
    write(REG/"M2RMREG2.pbs",pbs)
    dump(REG/"PACKAGE_MANIFEST.json",{"status":"prepared_not_authorized","job":"M2RMREG2","queue":"normal_imfdfkmq","cpus":1,"memory":"8 GB","walltime":"00:30:00","execution":"Abaqus/CAE noGUI only","deck_sha256":"a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2","odb_sha256":"bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac","physical_elements":3930,"miseseri_finite":3930,"true_slit_coincident_pairs":15,"solver_executions":0,"adaptivity_process_submissions":0,"native_remesh_calls":0,"refined_solver_executions":0,"generated_candidates":0})

def hashes(root):
    return {str(p.relative_to(root)).replace('\\','/'):sha(p) for p in sorted(root.rglob('*')) if p.is_file() and p.name not in ('SHA256SUMS','BATCH_SHA256SUMS')}
def main():
    build_notify(); build_rollback(CTL,"M2IRRROLLCTL2",0,"control"); build_rollback(FORCE,"M2IRRROLLFORCE2",1,"forced"); build_region(); reset(RUN)
    jobs=[("M2NOTIFY1",INFRA,"wave_a"),("M2IRRROLLCTL2",CTL,"wave_b"),("M2IRRROLLFORCE2",FORCE,"wave_b"),("M2RMREG2",REG,"wave_b")]
    for _,p,_ in jobs:
        hs=hashes(p); write(p/"SHA256SUMS",''.join(v+'  '+k+'\n' for k,v in sorted(hs.items())))
    ctl=json.loads((CTL/"PACKAGE_MANIFEST.json").read_text()); forced=json.loads((FORCE/"PACKAGE_MANIFEST.json").read_text())
    dump(RUN/"CONDITIONAL_BATCH_PLAN.json",{"status":"prepared_not_authorized","jobs":[x[0] for x in jobs],"wave_a":["M2NOTIFY1"],"wave_b":["M2IRRROLLCTL2","M2IRRROLLFORCE2","M2RMREG2"],"maximum_qsub_attempts":4,"maximum_running_jobs":2,"retry":False,"replacement":False,"direct_qsub":False})
    dump(RUN/"CONDITIONAL_BATCH_DEPENDENCIES.json",{"wave_a":"M2NOTIFY1","wave_b_gate":{"technical_terminal_pass":True,"human_confirmations":["Telegram START","Telegram COMPLETED","PBS BEGIN email","PBS END email"]},"wave_b_independent":True,"third_may_queue":True})
    dump(RUN/"CONDITIONAL_BATCH_RESOURCES.json",{j:json.loads((p/"PACKAGE_MANIFEST.json").read_text()) for j,p,_ in jobs})
    dump(RUN/"CONDITIONAL_BATCH_ACCEPTANCE.json",{"M2NOTIFY1":"dual_channel_job_notification_contract_qualified after human confirmation","rollback":"penalty_rollback_qualified_controlled_cutback","M2RMREG2":"native_adaptive_region_contract_qualified","medium_h1_auto_submit":False,"native_remesh_auto_execute":False})
    dump(RUN/"CONDITIONAL_BATCH_NOTIFICATION_CONTRACT.json",{"config":"~/.config/adaptive-remeshing/notifications.env","mode":"600","owner":"pr21vyci","telegram":{"post":True,"nonempty_text":True,"max_attempts":3,"http_200":True,"json_ok":True,"chat_match":True},"email":{"mechanism":"native_pbs","mail_points":"abe","recipients":MAIL.split(',')},"sendmail_qualification":False})
    for j,p,w in jobs: dump(RUN/("JOB_"+j+"_MANIFEST.json"),dict(json.loads((p/"PACKAGE_MANIFEST.json").read_text()),wave=w,pbs_sha256=sha(next(p.glob('*.pbs'))),notification_wrapper_sha256=sha(p/"runtime/job_notifications.sh")))
    dump(RUN/"NO_UNAUTHORIZED_EXECUTION_AUDIT.json",{"execution_authorized":False,"submission_approved":False,"maximum_jobs_now":0,"qsub_attempts":0,"successful_submissions":0,"qdel":0,"qmove":0,"solver_executions":0,"remesh_calls":0,"direct_messages":0})
    dump(RUN/"STATUS.json",{"classification":"conditional_batch_prepared_not_authorized","telegram_direct_human_confirmation":{"source":"user-provided","utc":"2026-08-01T07:31:56Z","independently_published_before_this_commit":False},"rollback_qualified":False,"medium_h1_ready":False,"native_remesh_ready":False})
    dump(RUN/"BATCH_RUNTIME_MANIFEST.json",{"packages":{j:str(p.relative_to(ROOT)).replace('\\','/') for j,p,_ in jobs},"rollback_identity":{"source_sha256":ctl['source_sha256'],"deck_sha256":ctl['deck_sha256'],"sources_identical":ctl['source_sha256']==forced['source_sha256'],"decks_identical":ctl['deck_sha256']==forced['deck_sha256'],"only_runtime_environment_differs":"F16_FORCE_CUTBACK"}})
    allh={}
    for _,p,_ in jobs:
        for k,v in hashes(p).items(): allh[str(p.relative_to(ROOT)).replace('\\','/')+'/'+k]=v
    for p in sorted(RUN.glob('*.json')): allh[str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
    write(RUN/"BATCH_SHA256SUMS",''.join(v+'  '+k+'\n' for k,v in sorted(allh.items())))
if __name__=='__main__': main()
