# Generate-F1720ReceiptInventory.ps1
$ErrorActionPreference = 'Stop'

$files = [ordered]@{
    "sta_original" = "models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1720_ADAPTED_PFM.sta"
    "msg_original" = "models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1720_ADAPTED_PFM.msg"
    "dat_original" = "models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1720_ADAPTED_PFM.dat"
    "sta_text_copy" = "results/validation/f1720_solver_receipts/PK_F1720_ADAPTED_PFM_sta.txt"
    "dat_text_copy" = "results/validation/f1720_solver_receipts/PK_F1720_ADAPTED_PFM_dat.txt"
    "msg_terminal_copy" = "results/validation/f1720_solver_receipts/PK_F1720_ADAPTED_PFM_msg_terminal.txt"
}

$inventory = [ordered]@{
    "protocol" = "PRIMARY_SOLVER_RECEIPT_QUALIFICATION_V1"
    "task_id" = "F1720-METHOD-A-DIRECT-COUPLING-AND-REMESH-REPRODUCTION"
    "correlation_id" = "HND-F1720-METHOD-A-FINAL-VALIDATION-004"
    "job_name" = "PK_F1720_ADAPTED_PFM"
    "files" = [ordered]@{}
}

foreach ($key in $files.Keys) {
    $path = $files[$key]
    if (Test-Path $path) {
        $item = Get-Item $path
        $hash = (Get-FileHash $path -Algorithm SHA256).Hash
        $inventory["files"][$key] = [ordered]@{
            "exists" = $true
            "path" = $path
            "name" = $item.Name
            "size_bytes" = $item.Length
            "sha256" = $hash
        }
        Write-Host "$key : $($item.Name) -> $($item.Length) bytes, SHA-256: $hash"
    } else {
        $inventory["files"][$key] = [ordered]@{
            "exists" = $false
            "path" = $path
        }
        Write-Warning "$key : $path does not exist"
    }
}

$outPath = "results/validation/f1720_solver_receipts/RECEIPT_INVENTORY.json"
$dir = Split-Path $outPath
if (-not (Test-Path $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

$json = $inventory | ConvertTo-Json -Depth 5
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($outPath, $json, $utf8NoBom)
Write-Host "Saved inventory to $outPath"
