<#
.SYNOPSIS
    Guarded, non-interactive SSH execution wrapper with stdin isolation,
    safety validation, and bounded per-command timeout.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$RemoteCommand,

    [string]$HostAlias = 'tu_freiberg',

    [string]$ConfigPath = "$env:USERPROFILE\.ssh\codex_config",

    [int]$TimeoutSeconds = 120
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ------------------------------------------------------------
# 1. FAIL-CLOSED PREFLIGHT VALIDATION
# ------------------------------------------------------------
if ($env:ADAPTIVE_REMESHING_OFFLINE_MODE -eq '1' -or $env:OFFLINE_RESEARCH_ONLY -eq '1') {
    [Console]::Error.WriteLine('FAIL_CLOSED_OFFLINE_MODE: Cluster SSH and remote execution are disabled during offline mode.')
    exit 72
}
$trimmedCmd = $RemoteCommand.Trim()
if ([string]::IsNullOrWhiteSpace($trimmedCmd)) {
    [Console]::Error.WriteLine('FAIL_CLOSED_EMPTY_REMOTE_COMMAND: refusing to open interactive SSH session.')
    exit 64
}

if (-not (Test-Path -LiteralPath $ConfigPath)) {
    [Console]::Error.WriteLine("SSH_CONFIG_NOT_FOUND: $ConfigPath")
    exit 66
}

# Rule: Ban nested bash -c / sh -c
if ($trimmedCmd -match '(?i)\b(?:bash|sh)\s+-[a-z]*c\b') {
    [Console]::Error.WriteLine('FAIL_CLOSED_NESTED_BASH_C: Nested bash -c / sh -c is prohibited in SSH commands. Pass the remote command directly.')
    exit 67
}

# Rule: Ban unbounded recursive grep without explicit exclusions
if ($trimmedCmd -match '(?i)\bgrep\b\s+(?:-[a-z]*[rR]\b|--recursive\b)' -and $trimmedCmd -notmatch '(?i)(--exclude|--exclude-dir)') {
    [Console]::Error.WriteLine("FAIL_CLOSED_UNBOUNDED_GREP: Recursive grep across cluster paths must explicitly exclude binary artifacts (e.g. --exclude='*.odb' --exclude-dir='runs').")
    exit 69
}

# Rule: Ban whole-tree find/sha256sum over cluster project directories
if ($trimmedCmd -match '(?i)\bfind\s+(?:/home/pr21vyci/projects/adaptive-remeshing|~|/home/pr21vyci)[^;|&]*\s+-exec\s+sha256sum' -or 
    $trimmedCmd -match '(?i)\bsha256sum\s+(?:/home/pr21vyci/projects/adaptive-remeshing/|\./|\*)\*\s*') {
    [Console]::Error.WriteLine("FAIL_CLOSED_UNBOUNDED_HASH_SEARCH: Whole-tree find/sha256sum over cluster storage (1.3 TB) is prohibited. Target specific files or check ARTIFACT_REGISTRY.csv.")
    exit 70
}

# Rule: Ban bare stdin consumers without explicit arguments
if ($trimmedCmd -match '(?i)\b(?<prog>tail|cat|head)\b(?<rest>[^;&|]*)') {
    $prog = $Matches['prog'].ToLower()
    $rest = $Matches['rest'].Trim().TrimEnd("'", '"')
    $tokens = @($rest -split '\s+' | Where-Object { $_ -ne "" })
    
    $sawDoubleDash = $false
    $hasFileArg = $false
    for ($i = 0; $i -lt $tokens.Count; $i++) {
        $tok = [string]$tokens[$i]
        if ($tok -eq '--') {
            $sawDoubleDash = $true
            continue
        }
        if ($sawDoubleDash) {
            $hasFileArg = $true
            break
        }
        if ($tok -like '-*') {
            if ($tok -match '^-[nc]' -and ($i + 1 -lt $tokens.Count) -and ($tokens[$i+1] -match '^[0-9]+$')) {
                $i++
            }
            continue
        }
        $hasFileArg = $true
        break
    }
    if (-not $hasFileArg) {
        [Console]::Error.WriteLine("FAIL_CLOSED_BARE_STDIN_CONSUMER: Program '$prog' has no file argument and would wait on stdin indefinitely.")
        exit 68
    }
}

# ------------------------------------------------------------
# 2. RESOLVE SSH EXECUTABLE
# ------------------------------------------------------------
$sshCommand = Get-Command ssh.exe -ErrorAction Stop
$sshPath = $sshCommand.Source

# ------------------------------------------------------------
# 3. BUILD ARGUMENTS (Enforcing -n -T, BatchMode, and remote timeout)
# ------------------------------------------------------------
$remoteWrappedCmd = "timeout --preserve-status ${TimeoutSeconds}s $trimmedCmd"
$argStr = "-n -T -o BatchMode=yes -o ConnectTimeout=20 -o ServerAliveInterval=30 -o ServerAliveCountMax=2 -F `"$ConfigPath`" $HostAlias `"$remoteWrappedCmd`""

$psi = [System.Diagnostics.ProcessStartInfo]::new($sshPath, $argStr)
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.CreateNoWindow = $true

# ------------------------------------------------------------
# 4. EXECUTE WITH BOUNDED TIMEOUT
# ------------------------------------------------------------
try {
    $proc = [System.Diagnostics.Process]::Start($psi)
} catch {
    [Console]::Error.WriteLine("SSH_SPAWN_FAILED: $($_.Exception.Message)")
    exit 71
}

# Read streams asynchronously or via ReadToEnd
$stdoutTask = $proc.StandardOutput.ReadToEndAsync()
$stderrTask = $proc.StandardError.ReadToEndAsync()

$timeoutMs = $TimeoutSeconds * 1000
$finished = $proc.WaitForExit($timeoutMs)

if (-not $finished) {
    # Timed out! Terminate ONLY this spawned SSH process
    try {
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    } catch {}
    [Console]::Error.WriteLine("SSH_COMMAND_TIMEOUT: Remote command timed out after $TimeoutSeconds seconds (PID $($proc.Id)). Terminated process.")
    exit 124
}

[System.Threading.Tasks.Task]::WaitAll($stdoutTask, $stderrTask)

$stdout = $stdoutTask.Result
$stderr = $stderrTask.Result

# Filter out harmless SSH notices
if (-not [string]::IsNullOrEmpty($stdout)) {
    [Console]::Out.Write($stdout)
}

if (-not [string]::IsNullOrEmpty($stderr)) {
    $filteredErr = ($stderr -split "`r?`n" | Where-Object { 
        $_ -notmatch 'post-quantum key exchange' -and $_.Trim() -ne ''
    }) -join "`r`n"
    if ($filteredErr.Trim().Length -gt 0) {
        [Console]::Error.WriteLine($filteredErr.Trim())
    }
}

exit $proc.ExitCode
