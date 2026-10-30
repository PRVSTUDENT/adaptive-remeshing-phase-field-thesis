function Get-ControllerTraceQualification([string]$Workspace) {
    $relative='models/pandey_kumar_mode1/74_method_c_history_call_trace_absolute_path/QUALIFICATION.json'
    $path=Join-Path $Workspace $relative
    if(-not(Test-Path -LiteralPath $path -PathType Leaf)){throw 'Trace technical qualification evidence missing'}
    $q=Get-Content -LiteralPath $path -Raw|ConvertFrom-Json
    if($q.schema -ne 1 -or $q.operation -ne 'authentic_uel_history_call_trace' -or $q.status -ne 'READY_FOR_TRACE_ANALYSIS' -or
        $q.dispatch_ready -isnot [bool] -or -not $q.dispatch_ready -or $q.pbs_job_id -notmatch '^\d+\.mmaster02$' -or
        $q.datacheck -ne 'PASS' -or $q.login_notifications -ne 'PASS' -or $q.compute_notifications -ne 'PASS' -or $q.parity -ne 'PASS'){throw 'Incomplete trace technical qualification'}
    $root=[IO.Path]::GetFullPath($Workspace).TrimEnd([char[]]'\/')+[IO.Path]::DirectorySeparatorChar
    if(@($q.sources.PSObject.Properties).Count -lt 10){throw 'Trace source/evidence binding incomplete'}
    foreach($item in $q.sources.PSObject.Properties){
        $p=[IO.Path]::GetFullPath((Join-Path $Workspace $item.Name))
        if(-not $p.StartsWith($root,[StringComparison]::OrdinalIgnoreCase) -or -not(Test-Path -LiteralPath $p -PathType Leaf) -or
            (Get-Item -LiteralPath $p).Length -gt 16777216 -or (Get-FileHash -LiteralPath $p).Hash -ne $item.Value){throw ('Trace qualification source/evidence changed: '+$item.Name)}
    }
    $receipts=Get-Content -LiteralPath (Join-Path $Workspace 'project_coordination/MODE1_BATCH_SUBMISSIONS.json') -Raw|ConvertFrom-Json
    $receipt=$receipts.PSObject.Properties[$q.manifest_sha256].Value.PSObject.Properties['M1_F1597_HISTORY_TRACE_R2'].Value
    if($receipt.pbs_job_id -ne $q.pbs_job_id){throw 'Actual governed trace PBS receipt mismatch'}
    $row=@(Import-Csv -LiteralPath (Join-Path $Workspace 'project_coordination/HPC_JOB_LEDGER.csv')|Where-Object {$_.Job_ID -eq $q.pbs_job_id -and $_.Job_Name -eq 'M1_F1597_HISTORY_TRACE_R2'})
    if($row.Count -ne 1 -or $row[0].Status -ne 'COMPLETED' -or [string]$row[0].Exit_Status -ne '0'){throw 'Independent terminal trace accounting missing'}
    $q|Add-Member -NotePropertyName qualification_artifact -NotePropertyValue $relative -Force
    return $q
}

function Get-ControllerDynamicQualification([string]$Workspace, [string]$Path = '', [string]$ArtifactId = '') {
    if(-not $Workspace){throw 'Workspace path is required for dynamic qualification'}
    $root = [IO.Path]::GetFullPath($Workspace).TrimEnd([char[]]'\/') + [IO.Path]::DirectorySeparatorChar

    if($Path -cin @('evaluate_mode1_package148_state_transfer','evaluate_mode1_package148_state_transfer_r2','evaluate_mode1_package148_state_transfer_r3')){
        if(-not $ArtifactId){ $ArtifactId = $Path }
        $Path = 'scripts/validation/execute_package148_state_transfer.py'
    }

    $candidates = @()
    if($ArtifactId){
        $candidates += "scripts/validation/$ArtifactId.qualification.json"
        $candidates += "scripts/validation/$ArtifactId.json"
        $candidates += "project_coordination/qualifications/$ArtifactId.json"
        $candidates += "project_coordination/qualifications/$ArtifactId.qualification.json"
    }
    if($Path){
        $cleanPath = $Path.Replace('\', '/')
        if($cleanPath -match '(?:\.\.[/\\]|[/\\]\.\.)'){ throw "PATH_ESCAPE_REJECTED: Script path escapes workspace: $Path" }
        if($cleanPath.StartsWith('/')){ $cleanPath = $cleanPath.TrimStart('/') }
        $fullScript = [IO.Path]::GetFullPath((Join-Path $Workspace $cleanPath))
        if(-not $fullScript.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)){
            throw "PATH_ESCAPE_REJECTED: Script path escapes workspace: $Path"
        }
        $candidates += [IO.Path]::ChangeExtension($cleanPath, '.qualification.json').Replace('\', '/')
        $candidates += (Join-Path (Split-Path $cleanPath) 'QUALIFICATION.json').Replace('\', '/')
        $scriptBase = [IO.Path]::GetFileNameWithoutExtension($cleanPath)
        $candidates += "project_coordination/qualifications/$scriptBase.json"
        $candidates += "project_coordination/qualifications/$scriptBase.qualification.json"
    }

    $activeTaskPath = Join-Path $Workspace 'project_coordination/ACTIVE_TASK.json'
    if(Test-Path -LiteralPath $activeTaskPath){
        try{
            $at = Get-Content -LiteralPath $activeTaskPath -Raw | ConvertFrom-Json
            if($at.operation_preparation.qualification_artifact){
                $opMatch = (-not $ArtifactId -or $at.operation_preparation.operation_id -eq $ArtifactId)
                $pathMatch = (-not $Path -or $at.operation_preparation.path -eq $Path)
                if($opMatch -and $pathMatch){
                    $candidates += ([string]$at.operation_preparation.qualification_artifact).Replace('\', '/')
                }
            }
        }catch{}
    }

    $qualRel = $null
    $qualFull = $null
    $qObj = $null
    foreach($c in ($candidates | Select-Object -Unique)){
        if(-not $c){continue}
        if($c -match '(?:\.\.[/\\]|[/\\]\.\.)'){ continue }
        $full = [IO.Path]::GetFullPath((Join-Path $Workspace $c))
        if($full.StartsWith($root, [StringComparison]::OrdinalIgnoreCase) -and (Test-Path -LiteralPath $full -PathType Leaf)){
            try {
                $candQ = Get-Content -LiteralPath $full -Raw | ConvertFrom-Json
                $opName = if($candQ.operation){ [string]$candQ.operation } elseif($candQ.canonical_path){ [IO.Path]::GetFileNameWithoutExtension([string]$candQ.canonical_path) } else { '' }
                if($ArtifactId -and $opName -and $opName -ne $ArtifactId){ continue }
                if($Path -and $candQ.canonical_path -and $candQ.canonical_path -ne $Path){ continue }
                $qualRel = $c.Replace('\', '/')
                $qualFull = $full
                $qObj = $candQ
                break
            } catch { continue }
        }
    }

    if(-not $qualRel -or -not $qObj){
        return $null
    }

    $q = $qObj
    if($q.schema -ne 1){
        throw "INVALID_QUALIFICATION_SCHEMA: schema must be 1 in $qualRel"
    }
    if($q.status -notin @('QUALIFIED', 'READY_FOR_EXECUTION', 'READY_FOR_TRACE_ANALYSIS', 'QUALIFIED_FOR_PREFLIGHT')){
        throw "INVALID_QUALIFICATION_STATUS: status '$($q.status)' is not qualified in $qualRel"
    }
    if($q.dispatch_ready -isnot [bool] -or -not $q.dispatch_ready){
        throw "QUALIFICATION_NOT_DISPATCH_READY: dispatch_ready must be true in $qualRel"
    }

    $scriptRel = if($q.canonical_path){ [string]$q.canonical_path } elseif($Path){ $Path } else { throw "QUALIFICATION_MISSING_SCRIPT_PATH: canonical_path required in $qualRel" }
    $scriptRel = $scriptRel.Replace('\', '/')
    if($scriptRel -match '(?:\.\.[/\\]|[/\\]\.\.)'){ throw "PATH_ESCAPE_REJECTED: canonical_path escapes workspace: $scriptRel" }
    $fullScript = [IO.Path]::GetFullPath((Join-Path $Workspace $scriptRel))
    if(-not $fullScript.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)){
        throw "PATH_ESCAPE_REJECTED: canonical_path escapes workspace: $scriptRel"
    }
    if(-not (Test-Path -LiteralPath $fullScript -PathType Leaf)){
        throw "QUALIFIED_SCRIPT_MISSING: script file not found on disk: $scriptRel"
    }
    $scriptHash = (Get-FileHash -LiteralPath $fullScript -Algorithm SHA256).Hash
    if($q.script_sha256 -and $q.script_sha256 -cne $scriptHash){
        throw "SCRIPT_HASH_MISMATCH: script hash changed on disk for $scriptRel"
    }

    $opId = if($q.operation){ [string]$q.operation } else { [IO.Path]::GetFileNameWithoutExtension($scriptRel) }

    if($null -eq $q.tests -or @($q.tests.PSObject.Properties).Count -lt 1){
        throw "QUALIFICATION_TESTS_REQUIRED: at least one passing test binding is required in $qualRel"
    }
    if($q.tests_passed -isnot [bool] -or -not $q.tests_passed){
        throw "QUALIFICATION_TESTS_NOT_PASSED: tests_passed must be true in $qualRel"
    }
    foreach($t in $q.tests.PSObject.Properties){
        if($t.Name -match '(?:\.\.[/\\]|[/\\]\.\.)'){ throw "PATH_ESCAPE_REJECTED: test path escapes workspace: $($t.Name)" }
        $tp = [IO.Path]::GetFullPath((Join-Path $Workspace $t.Name))
        if(-not $tp.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)){
            throw "PATH_ESCAPE_REJECTED: test path escapes workspace: $($t.Name)"
        }
        if(-not (Test-Path -LiteralPath $tp -PathType Leaf)){
            throw "QUALIFICATION_TEST_FILE_MISSING: test file missing: $($t.Name)"
        }
        $th = (Get-FileHash -LiteralPath $tp -Algorithm SHA256).Hash
        if($t.Value -and $t.Value -cne $th){
            throw "TEST_HASH_MISMATCH: test file changed on disk: $($t.Name)"
        }
    }

    if($q.scientific_dependencies){
        foreach($d in $q.scientific_dependencies.PSObject.Properties){
            if($d.Name -match '(?:\.\.[/\\]|[/\\]\.\.)'){ throw "PATH_ESCAPE_REJECTED: dependency path escapes workspace: $($d.Name)" }
            $dp = [IO.Path]::GetFullPath((Join-Path $Workspace $d.Name))
            if(-not $dp.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)){
                throw "PATH_ESCAPE_REJECTED: dependency path escapes workspace: $($d.Name)"
            }
            if(-not (Test-Path -LiteralPath $dp -PathType Leaf)){
                throw "QUALIFICATION_DEPENDENCY_MISSING: dependency file missing: $($d.Name)"
            }
            $dh = (Get-FileHash -LiteralPath $dp -Algorithm SHA256).Hash
            if($d.Value -and $d.Value -cne $dh){
                throw "DEPENDENCY_HASH_MISMATCH: dependency file changed on disk: $($d.Name)"
            }
        }
    }

    if($null -eq $q.verification_criteria -or $null -eq $q.verification_criteria.required_measurements -or @($q.verification_criteria.required_measurements).Count -eq 0){
        throw "QUALIFICATION_CRITERIA_REQUIRED: verification_criteria.required_measurements required in $qualRel"
    }

    if($q.execution_mode -eq 'HPC_PRE_SUBMISSION'){
        $revision=if($opId -ceq 'evaluate_mode1_package148_state_transfer_r3'){3}elseif($opId -ceq 'evaluate_mode1_package148_state_transfer_r2'){2}elseif($opId -ceq 'evaluate_mode1_package148_state_transfer'){1}else{throw 'INVALID_PRESUBMISSION_OPERATION'}
        $expectedJob='M1_C4_P148_R'+$revision
        $expectedManifest='models/pandey_kumar_mode1/148_c4_package148_state_transfer_r'+$revision+'/EXECUTION_MANIFEST.json'
        if($q.manifest -cne $expectedManifest){throw 'PRESUBMISSION_REVISION_MISMATCH'}
        # Registration qualifies a guarded preflight entrypoint, not a completed
        # experiment. A PBS ID is created only by the once-only submission gate.
        if($q.status -ne 'QUALIFIED_FOR_PREFLIGHT' -or $q.pbs_job_id -or
           $scriptRel -cne 'scripts/validation/execute_package148_state_transfer.py' -or
           $q.execution_adapter -cne 'scripts/hpc/Invoke-Mode1Execution.ps1' -or
           $q.production_uel_sha256 -cne 'CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6'){
            throw 'INVALID_PRESUBMISSION_CONTRACT: guarded adapter, frozen UEL and no PBS ID required'
        }
        foreach($binding in @($q.execution_adapter,$q.manifest,$q.independent_review)){
            if(-not $binding -or -not $q.scientific_dependencies.PSObject.Properties[$binding] -or
               $q.scientific_dependencies.PSObject.Properties[$binding].Value -notmatch '^[A-F0-9]{64}$'){
                throw 'PRESUBMISSION_BINDING_REQUIRED: adapter, manifest and independent review must be hash bound'
            }
        }
        $review=Get-Content -LiteralPath (Join-Path $Workspace $q.independent_review) -Raw|ConvertFrom-Json
        if($review.verification_passed -isnot [bool] -or -not $review.verification_passed -or
           (($revision -eq 1 -and $review.review_summary.r1_independent_review -ne 'PASS') -or
            ($revision -eq 2 -and ($review.independent_r2_qualification -ne 'PASS' -or $review.python_36_compatibility -ne 'PASS')) -or
            ($revision -eq 3 -and ($review.independent_r3_qualification -ne 'PASS' -or $review.python_36_compatibility -ne 'PASS')))){
            throw 'PRESUBMISSION_REVIEW_REQUIRED: independent numerical runtime review must pass'
        }
        foreach($source in $review.evidence_sources.PSObject.Properties){
            if($source.Name -match '^scripts/state_transfer/' -or $source.Name -eq 'scripts/validation/extract_package148_iteration.py'){
                if($q.scientific_dependencies.($source.Name) -cne $source.Value){
                    throw 'PRESUBMISSION_REVIEW_STALE: numerical runtime differs from independent review'
                }
            }
        }
        $batch=Get-Content -LiteralPath (Join-Path $Workspace $q.manifest) -Raw|ConvertFrom-Json
        if($batch.scientific_scope -ne 'MODE1' -or $batch.automatic_retry -isnot [bool] -or $batch.automatic_retry -or
           $batch.max_submissions -ne 1 -or @($batch.jobs).Count -ne 1 -or $batch.jobs[0].id -cne $expectedJob){
            throw 'PRESUBMISSION_MANIFEST_REQUIRED: exact once-only reviewed Mode-I job required'
        }
    } elseif($q.status -eq 'QUALIFIED_FOR_PREFLIGHT'){
        throw 'INVALID_PRESUBMISSION_MODE'
    }
    $isHpc = ($q.execution_mode -eq 'HPC') -or ($q.pbs_job_id)
    if($isHpc){
        if($q.pbs_job_id -notmatch '^\d+\.mmaster02$'){
            throw "HPC_QUALIFICATION_FAILED: valid pbs_job_id required in $qualRel"
        }
        if($q.datacheck -ne 'PASS'){
            throw "HPC_QUALIFICATION_FAILED: datacheck must be PASS in $qualRel"
        }
        if($q.login_notifications -ne 'PASS' -or $q.compute_notifications -ne 'PASS'){
            throw "HPC_QUALIFICATION_FAILED: dual channel notifications must be PASS in $qualRel"
        }
        $frozenUelHash = 'CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6'
        if($q.production_uel_sha256 -and $q.production_uel_sha256 -cne $frozenUelHash){
            throw "HPC_QUALIFICATION_FAILED: production UEL is not bitwise frozen in $qualRel"
        }
        $hpcLedger = Join-Path $Workspace 'project_coordination/HPC_JOB_LEDGER.csv'
        if(-not (Test-Path -LiteralPath $hpcLedger)){
            throw "HPC_QUALIFICATION_FAILED: HPC_JOB_LEDGER.csv missing in $Workspace"
        }
        $ledgerRows = @(Import-Csv -LiteralPath $hpcLedger | Where-Object { $_.job_id -eq $q.pbs_job_id -or $_.Job_ID -eq $q.pbs_job_id })
        if($ledgerRows.Count -lt 1){
            throw "HPC_QUALIFICATION_FAILED: job ID $($q.pbs_job_id) not found in HPC_JOB_LEDGER.csv"
        }
    }

    $q | Add-Member -NotePropertyName qualification_artifact -NotePropertyValue $qualRel -Force
    $q | Add-Member -NotePropertyName canonical_path -NotePropertyValue $scriptRel -Force
    $q | Add-Member -NotePropertyName operation -NotePropertyValue $opId -Force
    return $q
}
