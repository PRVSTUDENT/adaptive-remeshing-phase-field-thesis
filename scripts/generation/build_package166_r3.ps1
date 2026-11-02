$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$src = Join-Path $repo 'models\pandey_kumar_mode1\166_c5_package166_r2_c2_0_nonaccumulating_history'
$dst = Join-Path $repo 'models\pandey_kumar_mode1\166_c5_package166_r3_c2_0_nonaccumulating_history'

if (-not (Test-Path $dst)) {
    New-Item -ItemType Directory -Path $dst -Force | Out-Null
}

$filesToCopy = @(
    'active_set_boundary_cards.inc',
    'd_lower_bounds.csv',
    'initial_conditions_solution.inc',
    'nodal_displacements_initial.csv',
    'nodal_phase_field_initial.csv',
    'f42_mixed_uel.for',
    'M1_C5_PACKAGE166_C2_0_REEQUILIBRATION.inp',
    'P166_MECHANICAL_DC.inp',
    'P166_MECHANICAL_DC.dat',
    'P166_PHASE_DC.inp',
    'P166_PHASE_DC.dat',
    'job_notifications.sh',
    'run_datacheck.sh'
)

foreach ($f in $filesToCopy) {
    Copy-Item -Path (Join-Path $src $f) -Destination (Join-Path $dst $f) -Force
}

$pbsContent = @'
#!/bin/bash
#PBS -N M1_C5_P166_R3_C2_0
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_c5_package166_r3_c2_0_nonaccumulating_history/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_c5_package166_r3_c2_0_nonaccumulating_history"
cd "${RUN_DIR}"

export JOB_NAME="M1_C5_P166_R3_C2_0"
export NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-${HOME}/.config/adaptive-remeshing/notifications.env}"
source "${RUN_DIR}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

repo="${RUN_DIR}/runtime"
python3 "${repo}/scripts/state_transfer/driver_package166_r2_c5_nonaccumulating_history.py" \
    --package "${RUN_DIR}" \
    --output "${RUN_DIR}/equilibration_${PBS_JOBID}" \
    --extractor "${repo}/scripts/validation/extract_package148_iteration.py" \
    --memory-gb 16 \
    --timeout 25200 \
    --max-outer 100
EXIT_CODE=$?

echo "Stage C2-0 Re-equilibration (Package 166-R3 Non-Accumulating History) finished with exit code: ${EXIT_CODE}"
exit ${EXIT_CODE}
'@

[IO.File]::WriteAllText((Join-Path $dst 'submit_M1_C5_P166_R3_C2_0.pbs'), $pbsContent.Replace("`r`n", "`n"), [Text.UTF8Encoding]::new($false))

$fileHashes = [ordered]@{}
$packageFiles = @(
    'M1_C5_PACKAGE166_C2_0_REEQUILIBRATION.inp',
    'P166_MECHANICAL_DC.dat',
    'P166_MECHANICAL_DC.inp',
    'P166_PHASE_DC.dat',
    'P166_PHASE_DC.inp',
    'active_set_boundary_cards.inc',
    'd_lower_bounds.csv',
    'f42_mixed_uel.for',
    'initial_conditions_solution.inc',
    'job_notifications.sh',
    'nodal_displacements_initial.csv',
    'nodal_phase_field_initial.csv',
    'run_datacheck.sh',
    'submit_M1_C5_P166_R3_C2_0.pbs'
)

foreach ($fn in $packageFiles) {
    $fp = Join-Path $dst $fn
    $fileHashes[$fn] = (Get-FileHash -Path $fp -Algorithm SHA256).Hash.ToUpper()
}

$pkgManifest = [ordered]@{
    schema = 1
    package_name = 'Package 166-R3 (Non-Accumulating History H* = max(H0, psi+(u*)) with Corrected Manifest & Damage Gate)'
    stage = 'C2-0'
    mesh = 'C5 (12996 quads, 13278 nodes, 51984 GPs)'
    predecessors = @(
        'Package 166 (Job 1419480 rejected for premature false convergence delta_d=3.01e-5 > 1e-5)',
        'Package 166-R2 (Job 1419483 aborted on startup due to missing donor_source in manifest)'
    )
    correction = 'Package 166-R3 restores donor_source and history contract while preserving post-phase damage gate repair from R2 driver'
    donor_source = [ordered]@{
        checkpoint = 'D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\157_c4_package157_c1_2_continuation_r5\converged_checkpoint_01.json'
        target_uy_mm = 0.0018603125442191958
        c4_max_history_MPa = 6868.951434128797
    }
    non_accumulating_history_contract = [ordered]@{
        update_rule = 'H^(k) = max(H0, psi+(u^(k)))'
        immutable_baseline = 'H0 = min(H_trans, H_donor_max)'
        ratcheting_suppression = 'Strictly non-accumulating from predecessor H0; rejected trials cannot corrupt baseline'
        post_convergence_thermo = 'H* >= psi+(u*) at all 51984 GPs'
        post_convergence_monotonicity = 'H* >= H0 at all 51984 GPs'
    }
    file_digests = $fileHashes
}

$pkgManifestJson = ($pkgManifest | ConvertTo-Json -Depth 10).Replace("`r`n", "`n")
[IO.File]::WriteAllText((Join-Path $dst 'PACKAGE_MANIFEST.json'), $pkgManifestJson, [Text.UTF8Encoding]::new($false))

$execFiles = [ordered]@{}
foreach ($k in $fileHashes.Keys) {
    $execFiles[$k] = $fileHashes[$k].ToLower()
}
$execFiles['PACKAGE_MANIFEST.json'] = (Get-FileHash -Path (Join-Path $dst 'PACKAGE_MANIFEST.json') -Algorithm SHA256).Hash.ToLower()

$runtimeSources = [ordered]@{
    'scripts/state_transfer/c4_to_c5_spatial_mapping.py' = 'BD2E115514C8672B07CBD85AEF6135C386B8C70A8044E378C6CCCEC910BD2699'
    'scripts/state_transfer/driver_package146_147_pdas_continuation.py' = '9EDE833668340A41AD590CB2387F8CB72A6C9C63DE9DF6B2185A3CABD1B21265'
    'scripts/state_transfer/driver_package166_r2_c5_nonaccumulating_history.py' = 'A8EC8AD11188AC2D054AB366EB05B489D80EF9F9C8129B73EB21B6582B794513'
    'scripts/validation/extract_package148_iteration.py' = '24C916740F737435612B751B839331131CB30526E6E9C5B31110BB8A463C69CF'
    'scripts/state_transfer/c3_int_to_c4_spatial_mapping.py' = '109B01623F2C24FE1B66C17F62812D575FEFB72AB700F8979B829B85D2DDBBD8'
}

$execManifest = [ordered]@{
    batch_name = 'MODE1_PACKAGE166_R3_M1_C5_P166_R3_C2_0'
    adapter = 'mode1-qualified-batch-v2'
    scientific_scope = 'MODE1'
    technical_stage = 'MODE1_BASELINE'
    configuration = 'MODE1_BASELINE'
    max_submissions = 1
    automatic_retry = $false
    remote_run_dir = '/scratch9/pr21vyci/runs/mode1_c5_package166_r3_c2_0_nonaccumulating_history'
    runtime_root = '/scratch9/pr21vyci/runs/mode1_c5_package166_r3_c2_0_nonaccumulating_history/runtime'
    runtime_source_hashes = $runtimeSources
    files = $execFiles
    scientific_predecessor_review = 'results/validation/package166_authentic_terminal_audit.json'
    jobs = @(
        [ordered]@{
            id = 'M1_C5_P166_R3_C2_0'
            purpose = 'Stage C2-0 coupled re-equilibration on Candidate C5 mesh with restored donor_source manifest schema and verified post-phase damage stopping logic delta_d <= 1e-5.'
            input = 'P166_MECHANICAL_DC.inp'
            datacheck = 'P166_MECHANICAL_DC.dat'
            additional_datachecks = @('P166_PHASE_DC.dat')
            pbs = 'submit_M1_C5_P166_R3_C2_0.pbs'
            queue = 'entry_imfdfkmq'
            cpus = 1
            memory_gb = 16
            walltime_hours = 8
            execution = 'single-rank serial'
            max_submissions = 1
            depends_on = @()
            command = 'powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_c5_package166_r3_c2_0_nonaccumulating_history/submit_M1_C5_P166_R3_C2_0.pbs"'
            command_sha256 = 'placeholder'
        }
    )
    acceptance = [ordered]@{
        M1_C5_P166_R3_C2_0 = 'Stage C2-0 coupled re-equilibration on Candidate C5 mesh (12,996 quads, 13,278 nodes, 51,984 GPs) with restored donor_source manifest schema and verified post-phase damage stopping logic delta_d <= 1e-5.'
    }
}

$execManifestJson = ($execManifest | ConvertTo-Json -Depth 10).Replace("`r`n", "`n")
[IO.File]::WriteAllText((Join-Path $dst 'EXECUTION_MANIFEST.json'), $execManifestJson, [Text.UTF8Encoding]::new($false))

Write-Output "PACKAGE_166_R3_BUILT_SUCCESSFULLY"
