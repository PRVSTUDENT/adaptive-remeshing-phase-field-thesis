# -*- coding: utf-8 -*-
# scripts/hpc/Collect-F1739-Case1-Fracture-R1.ps1
# Collects and Evaluates Task F1739 Case 1 Corrected Adapted Fracture Receipts from HPC Cluster

$ErrorActionPreference = 'Stop'
$repo = 'D:\Master thesis\Adaptive remeshing'
$activeTaskJson = Join-Path $repo 'project_coordination/ACTIVE_TASK.json'
$remoteDir = "/scratch9/pr21vyci/runs/mode1_pk_f1739_case1_fracture_r1"
$evidenceDir = Join-Path $repo 'results/validation/f1739_case1_adapted_fracture_evidence'
$cfg = "$env:USERPROFILE\.ssh\codex_config"

function Download-File($remote, $local) {
    & scp -F $cfg -B -o BatchMode=yes "tu_freiberg:$remote" $local
    if ($LASTEXITCODE -ne 0) { throw "SCP failed for $remote to $local" }
}

Write-Output "=== TASK F1739: COLLECTING CASE 1 ADAPTED FRACTURE RECEIPTS (R1) ==="

if (-not (Test-Path $evidenceDir)) {
    New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null
}

$task = Get-Content $activeTaskJson -Raw | ConvertFrom-Json
$jobId = $task.active_pbs_job_id
Write-Output "Active PBS Job ID: $jobId"

# 1. Download evidence files (text and tabular receipts only; exclude bulky ODB)
$filesToDownload = @(
    "pbs_execution.log",
    "PK_F1739_CASE_1_FRAC.sta",
    "PK_F1739_CASE_1_FRAC.msg",
    "PK_F1739_CASE_1_FRAC.dat",
    "PK_F1739_CASE_1_FRAC.prt",
    "PK_F1739_CASE_1_FRAC.com",
    "uel_energy_balance.csv",
    "uel_svars_out.txt",
    "f1739_case1_odb_audit.json"
)

foreach ($f in $filesToDownload) {
    $remote = "$remoteDir/$f"
    $local = Join-Path $evidenceDir $f
    try {
        Download-File $remote $local
        Write-Output "  Downloaded $f ($(Get-Item $local | Select-Object -ExpandProperty Length) bytes)"
    } catch {
        Write-Warning "Could not download ${f}: $_"
    }
}

Write-Output "Collection complete."
