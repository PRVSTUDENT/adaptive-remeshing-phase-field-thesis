# Regression tests for controller startup auth recovery stale PID handling and live worker verification
$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
. "$repo/scripts/controller/Controller-AuthRecovery.ps1"

$n = 0
function Check($x, $why) {
    if (-not $x) { throw "FAIL: $why" }
    $script:n++
    Write-Host "PASS $why"
}

# -----------------------------------------------------------------------------
# TEST 1: Stale worker PID from completed predecessor turn is accepted
# -----------------------------------------------------------------------------
& {
    function Read-ControllerCheckpoint { param($path) [pscustomobject]@{ workspace = $repo; process_id = 999999; state = 'COMPLETED' } }
    function Get-Content { param($LiteralPath, [switch]$Raw) '{"active":false}' }
    $script:exePath = (Join-Path $env:USERPROFILE '.gemini/bin/agy.exe')
    $script:hubCommand = 'agy.exe --hub --hub-port=123'
    $script:ownerMatches = $true

    function Get-CimInstance {
        param($ClassName, $Filter, $ErrorAction)
        if ($Filter -eq "Name = 'agy.exe'") {
            return @([pscustomobject]@{ ProcessId = 456; ExecutablePath = $script:exePath; CommandLine = $script:hubCommand; ParentProcessId = 123; CreationDate = [datetime]'2026-11-03' })
        }
        if ($Filter -eq "ProcessId = 999999") {
            # Stale PID does not exist on system
            return $null
        }
        return [pscustomobject]@{ ProcessId = 123; Name = 'Code.exe'; CreationDate = [datetime]'2026-11-02' }
    }
    function Invoke-CimMethod {
        param($InputObject, $MethodName, $ErrorAction)
        [pscustomobject]@{ ReturnValue = 0; Sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value }
    }

    $threw = $false
    try {
        Assert-ControllerBackgroundHubsOnly "fixture-checkpoint"
    } catch {
        $threw = $true
        $msg = $_.Exception.Message
    }
    Check (-not $threw) "Stale PID from exited worker does not trigger AUTH_RECOVERY_LIVE_AGY"
}

# -----------------------------------------------------------------------------
# TEST 2: Active live controlled worker process is rejected
# -----------------------------------------------------------------------------
& {
    function Read-ControllerCheckpoint { param($path) [pscustomobject]@{ workspace = $repo; process_id = 777; state = 'RUNNING' } }
    function Get-Content { param($LiteralPath, [switch]$Raw) '{"active":false}' }
    $script:exePath = (Join-Path $env:USERPROFILE '.gemini/bin/agy.exe')
    $script:workerCommand = '"C:\Users\pruth\AppData\Local\agy\bin\agy.exe" --model gemini-3.8-flash-high --input-format text --output-format stream-json --print-timeout 2280s'

    function Get-CimInstance {
        param($ClassName, $Filter, $ErrorAction)
        if ($Filter -eq "Name = 'agy.exe'") {
            return @([pscustomobject]@{ ProcessId = 777; ExecutablePath = $script:exePath; CommandLine = $script:workerCommand; ParentProcessId = 123; CreationDate = [datetime]'2026-11-04' })
        }
        if ($Filter -eq "ProcessId = 777") {
            return [pscustomobject]@{ ProcessId = 777; Name = 'agy.exe'; ExecutablePath = $script:exePath; CommandLine = $script:workerCommand; CreationDate = [datetime]'2026-11-04' }
        }
        return [pscustomobject]@{ ProcessId = 123; Name = 'powershell.exe'; CreationDate = [datetime]'2026-11-02' }
    }
    function Invoke-CimMethod {
        param($InputObject, $MethodName, $ErrorAction)
        [pscustomobject]@{ ReturnValue = 0; Sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value }
    }

    $threw = $false
    try {
        Assert-ControllerBackgroundHubsOnly "fixture-checkpoint"
    } catch {
        $threw = ($_.Exception.Message -match 'AUTH_RECOVERY_LIVE_AGY')
    }
    Check $threw "Active live controlled worker throws AUTH_RECOVERY_LIVE_AGY"
}

# -----------------------------------------------------------------------------
# TEST 3: Recycled PID assigned to non-agy process is not mistaken for worker
# -----------------------------------------------------------------------------
& {
    function Read-ControllerCheckpoint { param($path) [pscustomobject]@{ workspace = $repo; process_id = 888; state = 'COMPLETED' } }
    function Get-Content { param($LiteralPath, [switch]$Raw) '{"active":false}' }
    $script:exePath = (Join-Path $env:USERPROFILE '.gemini/bin/agy.exe')
    $script:hubCommand = 'agy.exe --hub --hub-port=123'

    function Get-CimInstance {
        param($ClassName, $Filter, $ErrorAction)
        if ($Filter -eq "Name = 'agy.exe'") {
            return @([pscustomobject]@{ ProcessId = 456; ExecutablePath = $script:exePath; CommandLine = $script:hubCommand; ParentProcessId = 123; CreationDate = [datetime]'2026-11-03' })
        }
        if ($Filter -eq "ProcessId = 888") {
            # PID recycled by OS to svchost.exe
            return [pscustomobject]@{ ProcessId = 888; Name = 'svchost.exe'; ExecutablePath = 'C:\Windows\System32\svchost.exe'; CommandLine = 'svchost.exe -k netsvcs'; CreationDate = [datetime]'2026-11-04' }
        }
        return [pscustomobject]@{ ProcessId = 123; Name = 'Code.exe'; CreationDate = [datetime]'2026-11-02' }
    }
    function Invoke-CimMethod {
        param($InputObject, $MethodName, $ErrorAction)
        [pscustomobject]@{ ReturnValue = 0; Sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value }
    }

    $threw = $false
    try {
        Assert-ControllerBackgroundHubsOnly "fixture-checkpoint"
    } catch {
        $threw = $true
    }
    Check (-not $threw) "Recycled PID assigned to non-agy process is recognized as stale and allowed"
}

# -----------------------------------------------------------------------------
# TEST 4: Active session always blocks auth recovery regardless of worker PID
# -----------------------------------------------------------------------------
& {
    function Read-ControllerCheckpoint { param($path) [pscustomobject]@{ workspace = $repo; process_id = 0; state = 'PENDING' } }
    function Get-Content { param($LiteralPath, [switch]$Raw) '{"active":true}' }

    $threw = $false
    try {
        Assert-ControllerBackgroundHubsOnly "fixture-checkpoint"
    } catch {
        $threw = ($_.Exception.Message -match 'AUTH_RECOVERY_LIVE_AGY')
    }
    Check $threw "Active repository session blocks auth recovery"
}

# -----------------------------------------------------------------------------
# TEST 5: Idle background hub without worker processes is permitted
# -----------------------------------------------------------------------------
& {
    function Read-ControllerCheckpoint { param($path) [pscustomobject]@{ workspace = $repo; process_id = 0; state = 'PENDING' } }
    function Get-Content { param($LiteralPath, [switch]$Raw) '{"active":false}' }
    $script:exePath = (Join-Path $env:USERPROFILE '.gemini/bin/agy.exe')
    $script:hubCommand = 'agy.exe --hub --hub-port=123'

    function Get-CimInstance {
        param($ClassName, $Filter, $ErrorAction)
        if ($Filter -eq "Name = 'agy.exe'") {
            return @([pscustomobject]@{ ProcessId = 456; ExecutablePath = $script:exePath; CommandLine = $script:hubCommand; ParentProcessId = 123; CreationDate = [datetime]'2026-11-03' })
        }
        return [pscustomobject]@{ ProcessId = 123; Name = 'Code.exe'; CreationDate = [datetime]'2026-11-02' }
    }
    function Invoke-CimMethod {
        param($InputObject, $MethodName, $ErrorAction)
        [pscustomobject]@{ ReturnValue = 0; Sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value }
    }

    $threw = $false
    try {
        Assert-ControllerBackgroundHubsOnly "fixture-checkpoint"
    } catch {
        $threw = $true
    }
    Check (-not $threw) "Idle background hub is permitted when session is inactive and no worker is live"
}

Write-Host "`nALL $n STALE PID REGRESSION CHECKS PASSED."
