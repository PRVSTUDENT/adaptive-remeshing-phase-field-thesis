# PowerShell remote qualification runner for M2STATE_FRACFIX_RESTART2R3
$ErrorActionPreference = "Stop"

$SSH_CONFIG = "$env:USERPROFILE\.ssh\codex_config"
$SSH_HOST = "tu_freiberg"
$LOCAL_DIR = "models\generated\mode_ii\production_state_transfer_batch\M2STATE_FRACFIX_RESTART2R3"
$REMOTE_BASE = "/home/pr21vyci/projects/adaptive-remeshing"
$REMOTE_DIR = "$REMOTE_BASE/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R3"
$REMOTE_TEST_DIR = "$REMOTE_BASE/tests/unit"

Write-Host "=== Step 1: Create remote directories ==="
ssh -F $SSH_CONFIG $SSH_HOST "mkdir -p $REMOTE_DIR $REMOTE_TEST_DIR"

Write-Host "=== Step 2: Copy package files to cluster ==="
$files = Get-ChildItem -Path $LOCAL_DIR
foreach ($f in $files) {
    Write-Host "  Copying $($f.Name)..."
    scp -F $SSH_CONFIG "$($f.FullName)" "${SSH_HOST}:${REMOTE_DIR}/$($f.Name)"
}

Write-Host "  Copying test_m2state_fracfix_restart2r3.py..."
scp -F $SSH_CONFIG "tests\unit\test_m2state_fracfix_restart2r3.py" "${SSH_HOST}:${REMOTE_TEST_DIR}/test_m2state_fracfix_restart2r3.py"

ssh -F $SSH_CONFIG $SSH_HOST "chmod +x ${REMOTE_DIR}/submit_m2state_fracfix_restart2r3.sh"

Write-Host "=== Step 3: Remote Manifest Validation ==="
ssh -F $SSH_CONFIG $SSH_HOST "cd $REMOTE_DIR && python3 validate_package_manifest.py"

Write-Host "=== Step 4: Remote Unit Regression Suite ==="
ssh -F $SSH_CONFIG $SSH_HOST "cd $REMOTE_BASE && python3 -m unittest tests/unit/test_m2state_fracfix_restart2r3.py"

Write-Host "=== Step 5: Fresh Non-Interactive Environment Test ==="
$envCmd = 'bash -c "source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true; module purge; module load gcc/11.4.0; module load intel/2024.2.0; module load abaqus/2023; module load python/gcc/11.4.0/3.11.7; echo LOADED_MODULES:; module list; echo IFORT_PATH: \$(which ifort); ifort --version | head -n 2; echo ABAQUS_PATH: \$(which abaqus); abaqus information=release | head -n 3; echo ENVIRONMENT_TEST_PASS"'
ssh -F $SSH_CONFIG $SSH_HOST $envCmd

Write-Host "=== Step 6: Abaqus 2023 Syntaxcheck with f42_mixed_uel.for ==="
$syntaxCmd = "cd $REMOTE_DIR && bash -c 'source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true; module purge; module load gcc/11.4.0; module load intel/2024.2.0; module load abaqus/2023; export XDG_RUNTIME_DIR=/tmp/runtime-pr21vyci; mkdir -p /tmp/runtime-pr21vyci; abaqus syntaxcheck job=M2STATE_FRACFIX_RESTART2R3 user=f42_mixed_uel.for interactive > syntaxcheck.log 2>&1; cat syntaxcheck.log'"
ssh -F $SSH_CONFIG $SSH_HOST $syntaxCmd

Write-Host "=== Step 7: Guarded Wrapper Dry-Run ==="
ssh -F $SSH_CONFIG $SSH_HOST "cd $REMOTE_DIR && bash submit_m2state_fracfix_restart2r3.sh --dry-run"

Write-Host "=== Step 8: Remote SHA256 Manifest Verification ==="
$hashCmd = "cd $REMOTE_DIR && python3 -c ""import hashlib, json; files = ['M2STATE_FRACFIX_RESTART2R3.inp', 'f42_mixed_uel.for', 'STATE_TRANSFER_ARTIFACT.json', 'TRANSFER_MANIFEST.json', 'RESTART_ACCEPTANCE_CONTRACT.json', 'M2STATE_FRACFIX_RESTART2R3.pbs', 'submit_m2state_fracfix_restart2r3.sh', 'validate_package_manifest.py', 'job_notifications.sh', 'extract_restart2r3_odb.py', 'verify_restart2r3_science.py', 'compare_restart1_restart2_matched_state.py', 'PACKAGE_MANIFEST.json']; res = {f: hashlib.sha256(open(f, 'rb').read()).hexdigest() for f in files}; print(json.dumps(res, indent=2))"""
ssh -F $SSH_CONFIG $SSH_HOST $hashCmd

Write-Host "=== ALL REMOTE QUALIFICATION STEPS FINISHED ==="
