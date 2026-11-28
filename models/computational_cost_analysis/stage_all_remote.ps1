$ErrorActionPreference = 'Stop'
$config = "$env:USERPROFILE\.ssh\codex_config"

$dirs = @(
    'novel_normal', 'novel_method_c',
    'complex1_normal', 'complex1_method_c',
    'complex2_normal', 'complex2_method_c',
    'complex3_normal', 'complex3_method_c'
)

$mkdir_cmds = ($dirs | ForEach-Object { "mkdir -p /scratchtemp/pr21vyci/runs/cost_analysis_extended/$_" }) -join ' ; '
Write-Host "Creating remote directories..."
& .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand $mkdir_cmds

# Novel Normal
Write-Host "Uploading novel_normal..."
scp -O -B -o BatchMode=yes -F $config models\computational_cost_analysis\novel\normal\* tu_freiberg:/scratchtemp/pr21vyci/runs/cost_analysis_extended/novel_normal/

# Novel Method C
Write-Host "Uploading novel_method_c..."
scp -O -B -o BatchMode=yes -F $config models\computational_cost_analysis\novel\method_c\* tu_freiberg:/scratchtemp/pr21vyci/runs/cost_analysis_extended/novel_method_c/

# Complex 1 Normal
Write-Host "Uploading complex1_normal..."
scp -O -B -o BatchMode=yes -F $config models\computational_cost_analysis\complex1\normal\* tu_freiberg:/scratchtemp/pr21vyci/runs/cost_analysis_extended/complex1_normal/

# Complex 1 Method C
Write-Host "Uploading complex1_method_c..."
scp -O -B -o BatchMode=yes -F $config models\computational_cost_analysis\complex1\method_c\* tu_freiberg:/scratchtemp/pr21vyci/runs/cost_analysis_extended/complex1_method_c/

# Complex 2 Normal
Write-Host "Uploading complex2_normal..."
scp -O -B -o BatchMode=yes -F $config models\computational_cost_analysis\complex2\normal\* tu_freiberg:/scratchtemp/pr21vyci/runs/cost_analysis_extended/complex2_normal/

# Complex 2 Method C
Write-Host "Uploading complex2_method_c..."
scp -O -B -o BatchMode=yes -F $config models\computational_cost_analysis\complex2\method_c\* tu_freiberg:/scratchtemp/pr21vyci/runs/cost_analysis_extended/complex2_method_c/

# Complex 3 Normal
Write-Host "Uploading complex3_normal..."
scp -O -B -o BatchMode=yes -F $config models\computational_cost_analysis\complex3\normal\* tu_freiberg:/scratchtemp/pr21vyci/runs/cost_analysis_extended/complex3_normal/

# Complex 3 Method C
Write-Host "Uploading complex3_method_c..."
scp -O -B -o BatchMode=yes -F $config models\computational_cost_analysis\complex3\method_c\* tu_freiberg:/scratchtemp/pr21vyci/runs/cost_analysis_extended/complex3_method_c/

Write-Host "All remote directories pre-staged successfully!"
