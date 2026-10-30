# Offline integration replay of the authentic R4 receipt in an isolated workspace.
# Never launches the controller, adapter, notification transport or scheduler.
$ErrorActionPreference='Stop'
$repo=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
. (Join-Path $repo 'scripts/controller/Controller-Recovery.ps1')
$root=Join-Path $env:TEMP ('r4-submission-closeout-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $root|Out-Null
$qp='scripts/validation/evaluate_mode1_package148_state_transfer_r4.qualification.json'
$receipt='results/validation/package148_r4_submission_validation.json'
$q=Get-Content (Join-Path $repo $qp) -Raw|ConvertFrom-Json
$payload=Get-Content (Join-Path $repo $receipt) -Raw|ConvertFrom-Json
foreach($d in $q.scientific_dependencies.PSObject.Properties){
    if($d.Name.Contains('\') -or $payload.sources.($d.Name) -cne $d.Value){throw 'Noncanonical/missing source binding'}
}
'PASS: canonical qualification keys match every receipt source'
$files=@($payload.sources.PSObject.Properties.Name)+@($q.tests.PSObject.Properties.Name)
foreach($rel in ($files|Select-Object -Unique)){
    $source=Join-Path $repo $rel
    if(-not(Test-Path -LiteralPath $source -PathType Leaf)){throw "Missing replay source $rel"}
    $dest=Join-Path $root $rel
    New-Item -ItemType Directory (Split-Path $dest) -Force|Out-Null
    Copy-Item -LiteralPath $source -Destination $dest
}
function Put([string]$Rel,$Data){
    $p=Join-Path $root $Rel
    New-Item -ItemType Directory (Split-Path $p) -Force|Out-Null
    [IO.File]::WriteAllText($p,($Data|ConvertTo-Json -Depth 40),[Text.UTF8Encoding]::new($false))
}
# Use real ledger receipt, but no scheduler/engine command is invoked.
Copy-Item (Join-Path $repo 'project_coordination/MODE1_BATCH_SUBMISSIONS.json') (Join-Path $root 'batch.json')
New-Item -ItemType Directory (Join-Path $root 'project_coordination') -Force|Out-Null
Copy-Item (Join-Path $root 'batch.json') (Join-Path $root 'project_coordination/MODE1_BATCH_SUBMISSIONS.json')
$run=[guid]::NewGuid().ToString()
$artifact="results/validation/mode1_f1597/$run.json"
Put $artifact $payload
$record=[pscustomobject]@{controller_run_id=$run;task_id='fixture';bootstrap_status='COMPLETE';operation_id=$q.operation;operation_path=$q.canonical_path;scientific_checkpoint=[pscustomobject]@{kind='HPC_SUBMISSION';exit_code=0;operation=$q.operation;artifact=$artifact;sha256=(Get-FileHash (Join-Path $root $artifact)).Hash}}
Put 'record.json' $record
$state=[pscustomobject]@{bootstrap_record_path=(Join-Path $root 'record.json');run_id=$run;task_id='fixture';scientific_operation=$q.canonical_path;sources=$payload.sources}
if(-not(Test-ControllerScientificCheckpoint $root $state)){throw 'Authentic R4 closeout replay rejected'}
'PASS: full controller HPC_SUBMISSION validation accepts revalidated authentic receipt'
$payload.sources.($q.manifest)='0'*64
Put $artifact $payload
$record.scientific_checkpoint.sha256=(Get-FileHash (Join-Path $root $artifact)).Hash
Put 'record.json' $record
if(Test-ControllerScientificCheckpoint $root $state){throw 'Tampered source accepted'}
'PASS: changed manifest source still fails closed even with fresh artifact checksum'
'PASS: 3 R4 source-map/closeout cases; all writes isolated in TEMP.'
