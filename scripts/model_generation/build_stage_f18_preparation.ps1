param([string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path)
$ErrorActionPreference='Stop'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
function Put($p,$s){ [IO.File]::WriteAllText($p,($s.TrimEnd("`r","`n")+"`n"),$utf8NoBom) }
function CopyText($a,$b){ Put $b ([IO.File]::ReadAllText($a)) }
$ctl=Join-Path $Root 'models/generated/mode_ii/f18_penalty_active_rollback_control'
$frc=Join-Path $Root 'models/generated/mode_ii/f18_penalty_active_rollback_forced'
$reg=Join-Path $Root 'models/generated/mode_ii/f18_native_adaptive_region_repair'
$f17p=Join-Path $Root 'models/generated/mode_ii/f17_penalty_activation_probe'
$f17r=Join-Path $Root 'models/generated/mode_ii/f17_native_adaptive_region_repair'
foreach($d in @($ctl,$frc,$reg)){ New-Item -ItemType Directory -Force (Join-Path $d runtime)|Out-Null }
foreach($d in @($ctl,$frc)){
 CopyText (Join-Path $f17p 'runtime/M2IRRPENACT1.inp') (Join-Path $d 'runtime/M2IRR_F18.inp')
 CopyText (Join-Path $f17p 'runtime/M2IRRPENACT1.for') (Join-Path $d 'runtime/M2IRR_F18.for')
 CopyText (Join-Path $f17p 'runtime/extract_stage_f17_penalty_probe.py') (Join-Path $d 'runtime/extract_stage_f18_rollback.py')
 CopyText (Join-Path $f17p 'runtime/analyze_stage_f17_penalty_probe.py') (Join-Path $d 'runtime/analyze_stage_f18_rollback.py')
 CopyText (Join-Path $f17p 'runtime/job_notifications.sh') (Join-Path $d 'runtime/job_notifications.sh')
 CopyText (Join-Path $f17p 'runtime/notification_evidence.py') (Join-Path $d 'runtime/notification_evidence.py')
 Put (Join-Path $d 'runtime/.gitignore') '__pycache__/'
}
$src=[IO.File]::ReadAllText((Join-Path $ctl 'runtime/M2IRR_F18.for'))
$block=@'
C       F18 one-shot cutback only at qualified penalty-active state.
        CALL GETOUTDIR(F16OUT,F16LO)
        CALL GETJOBNAME(F16JOB,F16LJ)
        F16FLAG=F16OUT(1:F16LO)//'/'//F16JOB(1:F16LJ)//
     1   '_f18_force_enabled.flag'
        OPEN(UNIT=97,FILE=F16FLAG,STATUS='OLD',IOSTAT=F16IOS)
        IF (F16IOS.EQ.0) THEN
         F16FORCE='1'
         CLOSE(97)
        ENDIF
        F16FLAG=F16OUT(1:F16LO)//'/'//F16JOB(1:F16LJ)//
     1   '_f18_cutback_once.flag'
        OPEN(UNIT=97,FILE=F16FLAG,STATUS='OLD',IOSTAT=F16IOS)
        IF (F16IOS.EQ.0) THEN
         F16FORCE='0'
         CLOSE(97)
        ENDIF
        IF (F16FORCE.EQ.'1'.AND.F16IOS.NE.0.AND.KSTEP.EQ.2.AND.
     1   KINC.EQ.4.AND.JELEM.EQ.6.AND.INPT.EQ.1.AND.
     2   DABS(TIME(1)-0.08D0).LE.1.0D-10.AND.
     3   DABS(TIME(2)-1.08D0).LE.1.0D-10.AND.
     4   GAP.LT.-1.0D-8.AND.PENRES.NE.ZERO.AND.
     5   PENEDEN.GT.ZERO.AND.PENTAN.LT.1.0D300) THEN
         PNEWDT=HALF
         OPEN(UNIT=97,FILE=F16FLAG,STATUS='NEW',IOSTAT=F16IOS)
         IF (F16IOS.EQ.0) THEN
          WRITE(97,*) 'F18 CUTBACK LATCH OUTSIDE SVARS'
          CLOSE(97)
         ENDIF
        ENDIF
'@
$src=$src.Replace('C       F17 penalty scout: forced cutback is unconditionally disabled.',$block.TrimEnd())
$src=$src.Replace('_f17_penalty_calls.log','_f18_rollback_calls.log')
foreach($d in @($ctl,$frc)){ Put (Join-Path $d 'runtime/M2IRR_F18.for') $src }
function RollPbs($job,$toggle){ @"
#!/bin/bash
#PBS -N $job
#PBS -q entry_imfdfkmq
#PBS -l select=1:ncpus=1:mem=8gb
#PBS -l walltime=01:00:00
#PBS -j oe
#PBS -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de
#PBS -m abe
set -uo pipefail; set +x
PACKAGE_DIR="`${F18_PACKAGE_DIR:?F18_PACKAGE_DIR required}"; EVIDENCE_DIR="`${F18_EVIDENCE_DIR:?F18_EVIDENCE_DIR required}"
WORK_ROOT="`${SCRATCH:?SCRATCH required}/$job`_`${PBS_JOBID:-unknown}"
mkdir -p "`$WORK_ROOT" "`$EVIDENCE_DIR" && cp -p "`$PACKAGE_DIR"/runtime/* "`$WORK_ROOT/" || exit 6
cd "`$WORK_ROOT" || exit 6
export F18_FORCE_CUTBACK=$toggle NOTIFICATION_EVIDENCE_DIR="`$EVIDENCE_DIR" NOTIFICATION_CONFIG="`$HOME/.config/adaptive-remeshing/notifications.env" NOTIFICATION_EMAIL_MODE=native_pbs NOTIFICATION_STAGE=F18 NOTIFICATION_RUN_ID="`${PBS_JOBID:-unknown}" PBS_JOBNAME="`${PBS_JOBNAME:-$job}"
. ./job_notifications.sh; notification_load_config || exit 4; notification_install_terminal_trap; notify_start || exit 5
if [ "`$F18_FORCE_CUTBACK" = 1 ]; then : > "`${PBS_JOBNAME}_f18_force_enabled.flag"; fi
module purge && module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 || exit 8
abaqus job=$job input=M2IRR_F18.inp user=M2IRR_F18.for interactive; rc=`$?
for ext in sta msg dat log; do test -s "$job.`$ext" && cp -p "$job.`$ext" "`$EVIDENCE_DIR/"; done
test `$rc -eq 0 || exit `$rc
abaqus python extract_stage_f18_rollback.py --odb $job.odb --output-dir extracted --role candidate || exit 10
python3 analyze_stage_f18_rollback.py --log ${job}_f18_rollback_calls.log --extracted extracted --output STATUS.json || exit 11
for f in response_curve.csv phase_history.csv energy_history.csv accepted_increments.csv cutback_attempts.csv; do test -s "extracted/`$f" || exit 12; cp -p "extracted/`$f" "`$EVIDENCE_DIR/"; done
cp -p STATUS.json ${job}_f18_rollback_calls.log "`$EVIDENCE_DIR/" || exit 13
(cd "`$EVIDENCE_DIR" && sha256sum STATUS.json ${job}_f18_rollback_calls.log response_curve.csv phase_history.csv energy_history.csv accepted_increments.csv cutback_attempts.csv > EXTRACTION_MANIFEST.sha256 && sha256sum -c EXTRACTION_MANIFEST.sha256) || exit 14
exit 0
"@ }
Put (Join-Path $ctl 'M2IRRROLLCTL4.pbs') (RollPbs 'M2IRRROLLCTL4' 0)
Put (Join-Path $frc 'M2IRRROLLFORCE4.pbs') (RollPbs 'M2IRRROLLFORCE4' 1)
foreach($f in @('source_deck.inp','job_notifications.sh','notification_evidence.py','f17_abaqus_python_compatibility.py')){ CopyText (Join-Path $f17r "runtime/$f") (Join-Path $reg "runtime/$($f.Replace('f17_','f18_'))") }
Put (Join-Path $reg 'runtime/.gitignore') '__pycache__/'
$py=@'
from __future__ import print_function
import json,math,os,sys,traceback
from abaqus import mdb
from abaqusConstants import MODEL,NOT_ALLOWED,ON,UNIFORM_ERROR
from odbAccess import openOdb
out=os.environ['F18_OUTPUT_DIR']; odbp=os.environ['F18_SOURCE_ODB']; deck=os.path.join(os.getcwd(),'source_deck.inp')
def wr(n,d): open(os.path.join(out,n),'wb').write((json.dumps(d,indent=2,sort_keys=True)+'\n').encode('utf-8'))
zero={'solver_executions':0,'datacheck_executions':0,'adaptivity_process_submissions':0,'model_adaptiveRemesh_calls':0,'native_remesh_calls':0,'candidates_generated':0,'refined_analyses':0}
odb=None
try:
 m=mdb.ModelFromInputFile(name='F18_SOURCE',inputFileName=deck); p=m.parts[m.parts.keys()[0]]
 orphan=bool(getattr(p,'isMeshPart',False)); methods=[x for x in dir(m) if 'adapt' in x.lower() or 'remesh' in x.lower()]
 gp=m.Part2DGeomFrom2DMesh(name='F18_GEOMETRY_BACKED',part=p,featureAngle=20.0) if orphan and hasattr(m,'Part2DGeomFrom2DMesh') else None
 target=gp or p; geometry_backed=not bool(getattr(target,'isMeshPart',False))
 m.RemeshingRule(name='F18_MISESERI_RULE',stepName='Step-1',variables=(str('MISESERI'),),region=MODEL,sizingMethod=UNIFORM_ERROR,errorTarget=1.0,specifyMinSize=ON,minElementSize=0.001,specifyMaxSize=ON,maxElementSize=0.010,coarseningFactor=NOT_ALLOWED,refinementFactor=10)
 odb=openOdb(path=odbp,readOnly=True); step_names=odb.steps.keys()
 if not step_names: raise ValueError('source ODB has no steps')
 frames=odb.steps[step_names[-1]].frames
 if not frames: raise ValueError('source ODB final step has no frames')
 fields=frames[-1].fieldOutputs
 if 'MISESERI' not in fields: raise KeyError('MISESERI')
 values=fields['MISESERI'].values
 if not values: raise ValueError('MISESERI values empty')
 finite=0
 for value in values:
  datum=float(value.data)
  if not math.isnan(datum) and not math.isinf(datum): finite+=1
 physical=sum(len(x.elements) for x in m.parts.values())
 sets=sorted(m.rootAssembly.sets.keys()); materials=sorted(m.materials.keys()); sections=sorted(m.sections.keys())
 loads=sorted(m.loads.keys()); bcs=sorted(m.boundaryConditions.keys())
 associated='F18_MISESERI_RULE' in m.remeshingRules and m.remeshingRules['F18_MISESERI_RULE'].region is not None
 ok=geometry_backed and finite==3930 and physical==3930 and associated
 cls='native_adaptive_region_contract_qualified' if ok else ('native_adaptive_geometry_reconstruction_required' if orphan and not geometry_backed else 'native_adaptive_region_rule_association_failed' if not associated else 'native_adaptive_region_api_unresolved')
 wr('ADAPTIVE_REGION_API_AUDIT.json',{'classification':cls,'orphan_mesh':orphan,'geometry_backed':geometry_backed,'rule_region_associated':associated,'installed_methods':methods})
 wr('SOURCE_MODEL_INTEGRITY.json',{'deck_sha256':'a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2','odb_sha256':'bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac','physical_elements':physical,'miseseri_finite':finite,'materials':materials,'sections':sections,'sets':sets,'loads':loads,'boundary_conditions':bcs,'true_slit_coincident_pairs_expected':15,'disconnected_slit_required':True,'opposite_face_bridge_prohibited':True})
 wr('REMESH_RULE_MANIFEST.json',{'name':'F18_MISESERI_RULE','step':'Step-1','variables':['MISESERI'],'region_associated':associated})
 zero['classification']=cls
except Exception:
 zero['classification']='native_adaptive_region_construction_failed'; zero['traceback_redacted']=traceback.format_exc()
finally:
 if odb is not None: odb.close()
wr('NO_EXECUTION_AUDIT.json',zero); wr('STATUS.json',zero)
assert all(zero[k]==0 for k in ('solver_executions','datacheck_executions','adaptivity_process_submissions','model_adaptiveRemesh_calls','native_remesh_calls','candidates_generated','refined_analyses'))
sys.exit(0 if zero['classification']!='native_adaptive_region_construction_failed' else 1)
'@
Put (Join-Path $reg 'runtime/qualify_f18_adaptive_region.py') $py
$rp=@'
#!/bin/bash
#PBS -N M2RMREG5
#PBS -q entry_imfdfkmq
#PBS -l select=1:ncpus=1:mem=8gb
#PBS -l walltime=00:30:00
#PBS -j oe
#PBS -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de
#PBS -m abe
set -uo pipefail; set +x
PACKAGE_DIR="${F18_PACKAGE_DIR:?F18_PACKAGE_DIR required}"; EVIDENCE_DIR="${F18_EVIDENCE_DIR:?F18_EVIDENCE_DIR required}"
export F18_SOURCE_ODB=/scratch/pr21vyci/adaptive-remeshing/runs/stage_f4/F4R1_20260730_065138_86ec6c79/miseseri_corrected/M2MISER1.odb F18_OUTPUT_DIR="$EVIDENCE_DIR"
test "${F18_SOURCE_ODB#/}" != "$F18_SOURCE_ODB" && test -r "$F18_SOURCE_ODB" && test -d "$F18_OUTPUT_DIR" && test -w "$F18_OUTPUT_DIR" || exit 6
actual=$(sha256sum "$F18_SOURCE_ODB"|awk '{print $1}'); test "$actual" = bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac || exit 7
printf '{"path":"%s","readable":true,"sha256":"%s","output_writable":true}\n' "$F18_SOURCE_ODB" "$actual" > "$EVIDENCE_DIR/ENVIRONMENT_CONTRACT_AUDIT.json"
WORK_ROOT="${SCRATCH:?SCRATCH required}/M2RMREG5_${PBS_JOBID:-unknown}"; mkdir -p "$WORK_ROOT" && cp -p "$PACKAGE_DIR"/runtime/* "$WORK_ROOT/" || exit 8; cd "$WORK_ROOT" || exit 8
export NOTIFICATION_EVIDENCE_DIR="$EVIDENCE_DIR" NOTIFICATION_CONFIG="$HOME/.config/adaptive-remeshing/notifications.env" NOTIFICATION_EMAIL_MODE=native_pbs NOTIFICATION_STAGE=F18 NOTIFICATION_RUN_ID="${PBS_JOBID:-unknown}" PBS_JOBNAME="${PBS_JOBNAME:-M2RMREG5}"
. ./job_notifications.sh; notification_load_config || exit 4; notification_install_terminal_trap; notify_start || exit 5
module purge && module load abaqus/2023 || exit 9
abaqus python f18_abaqus_python_compatibility.py || exit 10
abaqus cae noGUI=qualify_f18_adaptive_region.py > "$EVIDENCE_DIR/CAE.stdout" 2> "$EVIDENCE_DIR/CAE.stderr"; rc=$?
(cd "$EVIDENCE_DIR" && sha256sum ENVIRONMENT_CONTRACT_AUDIT.json ABAQUS_PYTHON_COMPATIBILITY.json ADAPTIVE_REGION_API_AUDIT.json SOURCE_MODEL_INTEGRITY.json REMESH_RULE_MANIFEST.json NO_EXECUTION_AUDIT.json STATUS.json CAE.stdout CAE.stderr > EVIDENCE_MANIFEST.sha256 && sha256sum -c EVIDENCE_MANIFEST.sha256) || exit 11
exit $rc
'@
Put (Join-Path $reg 'M2RMREG5.pbs') $rp
foreach($x in @(@($ctl,'M2IRRROLLCTL4','control'),@($frc,'M2IRRROLLFORCE4','forced'),@($reg,'M2RMREG5','adaptive'))){
 $d=$x[0];$job=$x[1];$kind=$x[2]
 $allow=(Get-ChildItem (Join-Path $d runtime) -File|% Name|Sort-Object)
 Put (Join-Path $d 'F18_MANIFEST_ALLOWLIST.json') ([ordered]@{runtime_files=$allow}|ConvertTo-Json -Depth 5)
 Put (Join-Path $d 'PACKAGE_MANIFEST.json') ([ordered]@{job=$job;kind=$kind;classification='prepared_not_authorized';queue='entry_imfdfkmq';execution_authorized=$false;submission_approved=$false;cpus=1;memory_gb=8;walltime=($(if($kind-eq'adaptive'){'00:30:00'}else{'01:00:00'}))}|ConvertTo-Json)
 Put (Join-Path $d 'F18_RUNTIME_MANIFEST.json') ([ordered]@{job=$job;runtime_files=$allow}|ConvertTo-Json -Depth 5)
 Put (Join-Path $d 'F18_NO_EXECUTION_AUDIT.json') ([ordered]@{qsub_attempts=0;solver_executions=0;datacheck_executions=0;adaptivity_process_submissions=0;model_adaptiveRemesh_calls=0;native_remesh_calls=0;candidates_generated=0;refined_analyses=0}|ConvertTo-Json)
 Put (Join-Path $d 'STATUS.json') ([ordered]@{job=$job;classification='prepared_not_authorized';execution_authorized=$false;maximum_jobs_now=0}|ConvertTo-Json)
 $lines=Get-ChildItem $d -Recurse -File|? Name -notin @('F18_SHA256SUMS','SHA256SUMS')|%{((Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()+'  '+$_.FullName.Substring($d.Length+1).Replace('\','/'))}|Sort-Object
 Put (Join-Path $d 'F18_SHA256SUMS') ($lines-join"`n"); CopyText (Join-Path $d 'F18_SHA256SUMS') (Join-Path $d 'SHA256SUMS')
}
$run=Join-Path $Root 'runs/hpc/stage_f/f18_rollback_pair_and_adaptive_region_r5_preparation'; New-Item -ItemType Directory -Force $run|Out-Null
Put (Join-Path $run 'F18_THREE_JOB_BATCH_PLAN.json') ([ordered]@{jobs=@('M2IRRROLLCTL4','M2IRRROLLFORCE4','M2RMREG5');submission_order=@('M2IRRROLLCTL4','M2IRRROLLFORCE4','M2RMREG5');maximum_qsub_invocations=3;maximum_successful_submissions=3;maximum_simultaneously_running=2;prepared_not_authorized=$true}|ConvertTo-Json -Depth 5)
Put (Join-Path $run 'F18_DEPENDENCIES.json') ([ordered]@{M2IRRROLLCTL4=@{scientific_dependency='F17 penalty activation passed'};M2IRRROLLFORCE4=@{scientific_dependency='F17 penalty activation passed'};M2RMREG5=@{scientific_dependency='none';scheduler_concurrency_dependency='afterany:M2IRRROLLCTL4'}}|ConvertTo-Json -Depth 5)
Put (Join-Path $run 'F18_RESOURCES.json') ([ordered]@{queue='entry_imfdfkmq';expected_execution_queue='normal_imfdfkmq';cpus_each=1;memory_gb_each=8;rollback_walltime='01:00:00';adaptive_walltime='00:30:00'}|ConvertTo-Json)
Put (Join-Path $run 'F18_ROLLBACK_TRIGGER_CONTRACT.json') ([ordered]@{toggle='F18_FORCE_CUTBACK';control=0;forced=1;state=@{KSTEP=2;KINC=4;JELEM=6;integration_point=1;step_time=0.08;total_time=1.08;time_tolerance=1e-10;healing_tolerance=1e-8};requires=@('trial phase below committed phase','penalty residual nonzero','penalty energy positive','penalty tangent finite','bounds inactive');PNEWDT=0.5;request_count=1;latch='flag file outside SVARS'}|ConvertTo-Json -Depth 5)
Put (Join-Path $run 'F18_ROLLBACK_ACCEPTANCE.json') ([ordered]@{required_classification='penalty_rollback_qualified_controlled_cutback';endpoint_displacement_mm=1e-10;matched_phase=1e-7;final_phase=1e-6;maximum_RF_difference_at_common_peak=1e-4;RF_U_NRMSE=1e-4;relative_energy_difference=1e-4;sta_msg_independent_evidence_required=$true}|ConvertTo-Json)
Put (Join-Path $run 'F18_ADAPTIVE_SOURCE_ODB_CONTRACT.json') ([ordered]@{path='/scratch/pr21vyci/adaptive-remeshing/runs/stage_f4/F4R1_20260730_065138_86ec6c79/miseseri_corrected/M2MISER1.odb';sha256='bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac';readable_verified=$true;verified_at='2026-08-02';mutation_performed=$false}|ConvertTo-Json)
Put (Join-Path $run 'F18_ADAPTIVE_ACCEPTANCE.json') ([ordered]@{required_classification='native_adaptive_region_contract_qualified';physical_elements=3930;finite_MISESERI=3930;true_slit_coincident_pairs=15;disconnected_slit=$true;opposite_face_bridge=$false;zero_execution_required=$true}|ConvertTo-Json)
Put (Join-Path $run 'F18_NOTIFICATION_CONTRACT.json') ([ordered]@{telegram='mandatory_start_and_terminal';pbs_email='best_effort';redaction_required=$true}|ConvertTo-Json)
Put (Join-Path $run 'F18_RUNTIME_MANIFEST.json') ([ordered]@{packages=@($ctl.Substring($Root.Length+1).Replace('\','/'),$frc.Substring($Root.Length+1).Replace('\','/'),$reg.Substring($Root.Length+1).Replace('\','/'));orchestrator='scripts/hpc/stage_f/submit_stage_f18_three_job_batch.sh'}|ConvertTo-Json -Depth 5)
Put (Join-Path $run 'F18_NO_EXECUTION_AUDIT.json') ([ordered]@{qsub_attempts=0;successful_submissions=0;failed_qsub_attempts=0;PBS_jobs=@();solver_executions=0;CAE_executions=0;native_remesh_calls=0;execution_authorized=$false;submission_approved=$false;maximum_jobs_now=0}|ConvertTo-Json)
