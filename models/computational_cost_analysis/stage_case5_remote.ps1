$ErrorActionPreference = 'Stop'
$config = "$env:USERPROFILE\.ssh\codex_config"
$dest_norm = 'tu_freiberg:/scratchtemp/pr21vyci/runs/cost_analysis_extended/case5_normal/'
$files_norm = @(
    'models\computational_cost_analysis\case5\normal\PK_COST_CASE5_NORMAL.inp',
    'models\computational_cost_analysis\case5\normal\submit_case5_normal.pbs',
    'models\computational_cost_analysis\case5\normal\f42_mixed_uel.for',
    'models\computational_cost_analysis\case5\normal\job_notifications.sh'
)
foreach ($f in $files_norm) {
    Write-Host "Uploading $f to $dest_norm..."
    scp -O -B -o BatchMode=yes -F $config $f $dest_norm
}
Write-Host "Case 5 Normal files uploaded successfully."

# Next Case 5 Method C
& .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand 'mkdir -p /scratchtemp/pr21vyci/runs/cost_analysis_extended/case5_method_c'
$dest_mc = 'tu_freiberg:/scratchtemp/pr21vyci/runs/cost_analysis_extended/case5_method_c/'
$files_mc = @(
    'models\computational_cost_analysis\case5\method_c\case5_single_job_orchestrator.py',
    'models\computational_cost_analysis\case5\method_c\generate_case5_adaptive_corridor_mesh.py',
    'models\computational_cost_analysis\case5\method_c\f42_mixed_uel.for',
    'models\computational_cost_analysis\case5\method_c\job_notifications.sh',
    'models\computational_cost_analysis\case5\method_c\PK_METHOD_C_CASE5_COARSE_JOB1.inp',
    'models\computational_cost_analysis\case5\method_c\PK_METHOD_C_CASE5_COARSE_PHYS.inp',
    'models\computational_cost_analysis\case5\method_c\PK_METHOD_C_CASE5_ADAPTIVE_PHYS.inp',
    'models\computational_cost_analysis\case5\method_c\submit_case5_method_c.pbs'
)
foreach ($f in $files_mc) {
    Write-Host "Uploading $f to $dest_mc..."
    scp -O -B -o BatchMode=yes -F $config $f $dest_mc
}
Write-Host "Case 5 Method C files uploaded successfully."
