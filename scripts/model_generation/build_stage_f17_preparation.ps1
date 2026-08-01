param([string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path)
$ErrorActionPreference = 'Stop'

$f16Probe = Join-Path $Root 'models/generated/mode_ii/f16_controlled_rollback_control_r3'
$f16Region = Join-Path $Root 'models/generated/mode_ii/f16_native_adaptive_region_resolution_r3'
$probe = Join-Path $Root 'models/generated/mode_ii/f17_penalty_activation_probe'
$region = Join-Path $Root 'models/generated/mode_ii/f17_native_adaptive_region_repair'

New-Item -ItemType Directory -Force -Path (Join-Path $probe 'runtime'),(Join-Path $region 'runtime') | Out-Null
Copy-Item (Join-Path $f16Probe 'runtime/M2IRR_F16.inp') (Join-Path $probe 'runtime/M2IRRPENACT1.inp')
Copy-Item (Join-Path $f16Probe 'runtime/M2IRR_F16.for') (Join-Path $probe 'runtime/M2IRRPENACT1.for')
Copy-Item (Join-Path $f16Probe 'runtime/extract_stage_f11_instrumented_pair.py') (Join-Path $probe 'runtime/extract_stage_f17_penalty_probe.py')
Copy-Item (Join-Path $f16Probe 'runtime/job_notifications.sh') (Join-Path $probe 'runtime/job_notifications.sh')
Copy-Item (Join-Path $f16Probe 'runtime/notification_evidence.py') (Join-Path $probe 'runtime/notification_evidence.py')
Copy-Item (Join-Path $f16Region 'runtime/source_deck.inp') (Join-Path $region 'runtime/source_deck.inp')
Copy-Item (Join-Path $f16Region 'runtime/job_notifications.sh') (Join-Path $region 'runtime/job_notifications.sh')
Copy-Item (Join-Path $f16Region 'runtime/notification_evidence.py') (Join-Path $region 'runtime/notification_evidence.py')
Copy-Item (Join-Path $Root 'scripts/validation/analyze_stage_f17_penalty_probe.py') (Join-Path $probe 'runtime/analyze_stage_f17_penalty_probe.py')
Copy-Item (Join-Path $Root 'scripts/validation/f17_abaqus_python_compatibility.py') (Join-Path $region 'runtime/f17_abaqus_python_compatibility.py')
Set-Content (Join-Path $probe 'runtime/.gitignore') '__pycache__/'
Set-Content (Join-Path $region 'runtime/.gitignore') '__pycache__/'

$forPath = Join-Path $probe 'runtime/M2IRRPENACT1.for'
$src = Get-Content $forPath -Raw
$src = $src -replace "        IF \(F16FORCE\.EQ\.'1'\.AND\.KSTEP\.EQ\.2\.AND\.[\s\S]*?\n     3   PNEWDT=HALF", "C       F17 penalty scout: forced cutback is unconditionally disabled."
$src = $src -replace "        F16FLAG=F16OUT\(1:F16LO\)//'/'//F16JOB\(1:F16LJ\)//[\s\S]*?        IF \(F16IOS\.NE\.0\) CALL XIT", "        F16FORCE='0'"
$src = $src -replace "        F16FORCE='0'\r?\n        READ\(97,'\(A1\)',IOSTAT=F16IOS\) F16FORCE\r?\n        CLOSE\(97\)\r?\n        IF \(F16IOS\.NE\.0\) CALL XIT", "        F16FORCE='0'"
$src = $src -replace "_f16_rollback_calls\.log", "_f17_penalty_calls.log"
$src = $src -replace "     5    GAP,PENEDEN", "     5    GAP,PENEDEN,PENRES,PENTAN"
Set-Content -NoNewline -Path $forPath -Value $src

$pbsProbe = @'
#!/bin/bash
#PBS -N M2IRRPENACT1
#PBS -q entry_imfdfkmq
#PBS -l select=1:ncpus=1:mem=8gb
#PBS -l walltime=01:00:00
#PBS -j oe
#PBS -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de
#PBS -m abe
set -uo pipefail
set +x
PACKAGE_DIR="${F17_PACKAGE_DIR:?F17_PACKAGE_DIR required}"
EVIDENCE_DIR="${F17_EVIDENCE_DIR:?F17_EVIDENCE_DIR required}"
WORK_ROOT="${SCRATCH:?SCRATCH required}/M2IRRPENACT1_${PBS_JOBID:-unknown}"
mkdir -p "$WORK_ROOT" "$EVIDENCE_DIR" && cp -p "$PACKAGE_DIR"/runtime/* "$WORK_ROOT/" || exit 6
cd "$WORK_ROOT" || exit 6
export NOTIFICATION_EVIDENCE_DIR="$EVIDENCE_DIR"
export NOTIFICATION_CONFIG="$HOME/.config/adaptive-remeshing/notifications.env" NOTIFICATION_EMAIL_MODE=native_pbs NOTIFICATION_STAGE=F17 NOTIFICATION_RUN_ID="${PBS_JOBID:-unknown}"
export PBS_JOBNAME="${PBS_JOBNAME:-M2IRRPENACT1}"
. ./job_notifications.sh
notification_load_config || exit 4
notification_install_terminal_trap
notify_start || exit 5
module purge && module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 || exit 8
abaqus job=M2IRRPENACT1 input=M2IRRPENACT1.inp user=M2IRRPENACT1.for interactive
solver_rc=$?
for ext in sta msg dat log; do test -f "M2IRRPENACT1.$ext" && cp -p "M2IRRPENACT1.$ext" "$EVIDENCE_DIR/"; done
test $solver_rc -eq 0 || exit $solver_rc
abaqus python extract_stage_f17_penalty_probe.py --odb M2IRRPENACT1.odb --output-dir extracted --role candidate || exit 10
cp extracted/rf_u_work_history.csv extracted/response_curve.csv
cp extracted/fixed_point_history.csv extracted/phase_history.csv
cp extracted/diagnostic_energy_history.csv extracted/energy_history.csv
cp extracted/fixed_point_history.csv extracted/accepted_increments.csv
python3 analyze_stage_f17_penalty_probe.py --log M2IRRPENACT1_f17_penalty_calls.log --extracted extracted --output STATUS.json || exit 11
required="response_curve.csv phase_history.csv energy_history.csv accepted_increments.csv"
for f in $required; do test -s "extracted/$f" || exit 12; cp -p "extracted/$f" "$EVIDENCE_DIR/"; done
cp -p STATUS.json M2IRRPENACT1_f17_penalty_calls.log "$EVIDENCE_DIR/" || exit 13
(cd "$EVIDENCE_DIR" && sha256sum STATUS.json M2IRRPENACT1_f17_penalty_calls.log $required > EXTRACTION_MANIFEST.sha256) || exit 14
exit 0
'@
Set-Content -NoNewline -Path (Join-Path $probe 'M2IRRPENACT1.pbs') -Value $pbsProbe

$regionScript = Get-Content (Join-Path $f16Region 'runtime/qualify_f16_adaptive_region.py') -Raw
$regionScript = $regionScript -replace "finite=sum\(1 for v in vals if not math\.isnan\(float\(v\.data\)\) and not math\.isinf\(float\(v\.data\)\)\)", "finite=0`n for value in vals:`n  datum=float(value.data)`n  if not math.isnan(datum) and not math.isinf(datum):`n   finite += 1"
$regionScript = $regionScript -replace 'F16_', 'F17_'
$regionScript = $regionScript -replace 'F16_OUTPUT_DIR', 'F17_OUTPUT_DIR'
$regionScript = $regionScript -replace 'F16_SOURCE_ODB', 'F17_SOURCE_ODB'
Set-Content -NoNewline -Path (Join-Path $region 'runtime/qualify_f17_adaptive_region.py') -Value $regionScript

$pbsRegion = @'
#!/bin/bash
#PBS -N M2RMREG4
#PBS -q entry_imfdfkmq
#PBS -l select=1:ncpus=1:mem=8gb
#PBS -l walltime=00:30:00
#PBS -j oe
#PBS -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de
#PBS -m abe
set -uo pipefail
set +x
PACKAGE_DIR="${F17_PACKAGE_DIR:?F17_PACKAGE_DIR required}"
EVIDENCE_DIR="${F17_EVIDENCE_DIR:?F17_EVIDENCE_DIR required}"
WORK_ROOT="${SCRATCH:?SCRATCH required}/M2RMREG4_${PBS_JOBID:-unknown}"
mkdir -p "$WORK_ROOT" "$EVIDENCE_DIR" && cp -p "$PACKAGE_DIR"/runtime/* "$WORK_ROOT/" || exit 6
cd "$WORK_ROOT" || exit 6
export NOTIFICATION_EVIDENCE_DIR="$EVIDENCE_DIR" F17_OUTPUT_DIR="$EVIDENCE_DIR"
export NOTIFICATION_CONFIG="$HOME/.config/adaptive-remeshing/notifications.env" NOTIFICATION_EMAIL_MODE=native_pbs NOTIFICATION_STAGE=F17 NOTIFICATION_RUN_ID="${PBS_JOBID:-unknown}"
export PBS_JOBNAME="${PBS_JOBNAME:-M2RMREG4}"
. ./job_notifications.sh
notification_load_config || exit 4
notification_install_terminal_trap
notify_start || exit 5
module purge && module load abaqus/2023 || exit 8
abaqus python f17_abaqus_python_compatibility.py || exit 9
abaqus cae noGUI=qualify_f17_adaptive_region.py
rc=$?
exit $rc
'@
Set-Content -NoNewline -Path (Join-Path $region 'M2RMREG4.pbs') -Value $pbsRegion

foreach($pair in @(@($probe,'M2IRRPENACT1'),@($region,'M2RMREG4'))){
 $dir=$pair[0]; $job=$pair[1]
 $manifest=[ordered]@{job=$job;classification='prepared_not_authorized';queue='entry_imfdfkmq';expected_execution_queue='normal_imfdfkmq';cpus=1;memory_gb=8;execution_authorized=$false;submission_approved=$false;qsub_attempts=0;retry_authorized=$false;replacement_authorized=$false;telegram_mandatory=$true;pbs_email='best_effort'}
 $manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $dir 'PACKAGE_MANIFEST.json')
 [ordered]@{job=$job;immutable=$true;runtime_files=(Get-ChildItem (Join-Path $dir 'runtime') -File | Select-Object -ExpandProperty Name)} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $dir 'F17_RUNTIME_MANIFEST.json')
 [ordered]@{solver_calls=0;datacheck_calls=0;adaptivity_process_submissions=0;model_adaptiveRemesh_calls=0;native_remesh_calls=0;candidates_generated=0;refined_analyses=0;execution_authorized=$false} | ConvertTo-Json | Set-Content (Join-Path $dir 'F17_NO_EXECUTION_AUDIT.json')
 [ordered]@{job=$job;classification='prepared_not_authorized';execution_authorized=$false;submission_approved=$false;maximum_jobs_now=0} | ConvertTo-Json | Set-Content (Join-Path $dir 'STATUS.json')
 Get-ChildItem $dir -Recurse -File | Where-Object { $_.Name -notin @('SHA256SUMS','F17_SHA256SUMS') -and $_.FullName -notmatch '[\\/]__pycache__[\\/]' } | ForEach-Object { $h=(Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower(); "$h  $($_.FullName.Substring($dir.Length+1).Replace('\','/'))" } | Set-Content (Join-Path $dir 'F17_SHA256SUMS')
 Copy-Item (Join-Path $dir 'F17_SHA256SUMS') (Join-Path $dir 'SHA256SUMS')
}

$runDir=Join-Path $Root 'runs/hpc/stage_f/f17_penalty_activation_and_adaptive_region_repair'
Get-ChildItem $runDir -File | Where-Object Name -ne 'F17_SHA256SUMS' | ForEach-Object { $h=(Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower(); "$h  $($_.Name)" } | Set-Content (Join-Path $runDir 'F17_SHA256SUMS')
