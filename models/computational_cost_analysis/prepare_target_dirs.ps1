$ErrorActionPreference = 'Stop'
$src_uel = 'models\pandey_kumar_mode1\f42_mixed_uel.for'
$src_notif = 'scripts\hpc\notifications\job_notifications.sh'
$target_dirs = @(
    'models\computational_cost_analysis\novel\normal',
    'models\computational_cost_analysis\novel\method_c',
    'models\computational_cost_analysis\complex1\normal',
    'models\computational_cost_analysis\complex1\method_c',
    'models\computational_cost_analysis\complex2\normal',
    'models\computational_cost_analysis\complex2\method_c',
    'models\computational_cost_analysis\complex3\normal',
    'models\computational_cost_analysis\complex3\method_c'
)
foreach ($d in $target_dirs) {
    Copy-Item $src_uel -Destination $d -Force
    Copy-Item $src_notif -Destination $d -Force
}

$hash = (Get-FileHash $src_uel -Algorithm SHA256).Hash
Write-Host "Subroutine hash: $hash"
if ($hash -ne 'CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6') {
    throw 'Hash mismatch!'
} else {
    Write-Host 'Frozen UEL bitwise verified in all directories.'
}
