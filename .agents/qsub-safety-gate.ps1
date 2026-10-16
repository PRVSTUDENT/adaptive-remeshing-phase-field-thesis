[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

function ConvertTo-GuardCompressedBase64([byte[]]$Bytes) {
    $buffer=New-Object IO.MemoryStream
    $stream=New-Object IO.Compression.GZipStream($buffer,[IO.Compression.CompressionMode]::Compress,$true)
    try{$stream.Write($Bytes,0,$Bytes.Length)}finally{$stream.Dispose()}
    $result=[Convert]::ToBase64String($buffer.ToArray())
    $buffer.Dispose()
    return $result
}

try {
    # -------------------------------------------------------------
    # 1. Fail-Closed on Empty or Missing Input
    # -------------------------------------------------------------
    $rawInput = ($input | Out-String)
    if ([string]::IsNullOrWhiteSpace($rawInput)) {
        $rawInput = [Console]::In.ReadToEnd()
    }
    $rawInput = $rawInput.Trim()

    if ([string]::IsNullOrWhiteSpace($rawInput)) {
        Write-Output '{"decision":"deny","reason":"SAFETY GATE: Empty hook payload (fail closed)."}'
        exit 0
    }

    # -------------------------------------------------------------
    # 2. Fail-Closed on Malformed JSON or Missing CommandLine
    # -------------------------------------------------------------
    try {
        $payload = $rawInput | ConvertFrom-Json
    } catch {
        Write-Output '{"decision":"deny","reason":"SAFETY GATE: Malformed JSON payload (fail closed)."}'
        exit 0
    }

    $cmd = ""
    if ($payload.toolCall -and $payload.toolCall.args -and $payload.toolCall.args.CommandLine) {
        $cmd = [string]$payload.toolCall.args.CommandLine
    }

    if ([string]::IsNullOrWhiteSpace($cmd)) {
        Write-Output '{"decision":"deny","reason":"SAFETY GATE: Missing CommandLine in toolCall args (fail closed)."}'
        exit 0
    }

    # -------------------------------------------------------------
    # 3. Unconditional Hard Denial for qdel and qmove
    # -------------------------------------------------------------
    if ($cmd -match '(?i)\b(qdel|qmove)\b') {
        Write-Output '{"decision":"deny","reason":"SAFETY GATE: qdel and qmove are strictly prohibited without separate explicit human authorization."}'
        exit 0
    }

    # -------------------------------------------------------------
    # 3b. Fail-Closed SSH Noninteractive Safety & Stdin Isolation Gate
    # -------------------------------------------------------------
    if ($cmd -match '(?i)\bssh(?:\.exe)?\b' -and $cmd -notmatch '(?i)\bInvoke-GuardedSsh\.ps1\b') {
        # Check for nested bash -c, sh -c, bash -lc
        if ($cmd -match '(?i)\b(?:bash|sh)\s+-[a-z]*c\b') {
            Write-Output '{"decision":"deny","reason":"SAFETY GATE DENIAL: Nested bash -c / sh -c is prohibited in SSH commands. Pass the remote command directly to ssh (e.g. ssh -n -T tu_freiberg \"tail -n 25 ...\") or use .\\.agents\\scripts\\Invoke-GuardedSsh.ps1."}'
            exit 0
        }

        # Check for bare stdin consumers without arguments
        if ($cmd -match '(?i)\b(?<prog>tail|cat|head)\b(?<rest>[^;&|]*)') {
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
                Write-Output ("{`"decision`":`"deny`",`"reason`":`"SAFETY GATE DENIAL: Bare stdin consumer detected ('$prog' without explicit file argument). Commands must specify target files/arguments explicitly and cannot consume stdin.`"}")
                exit 0
            }
        }

        # Check for missing -n flag on non-interactive SSH reads/queries
        if ($cmd -match '(?i)\b(tail|cat|head|grep|find|stat|qstat|sha256sum|ps|ls)\b') {
            $sshPrefix = $cmd
            if ($cmd -match '(?i)\bssh(?:\.exe)?\b(?<args>[^"'']*?)(?:["''\r\n;&|]|$)') {
                $sshPrefix = $Matches['args']
            }
            if ($sshPrefix -match '(?i)\b(tail|cat|head|grep|find|stat|qstat|sha256sum|ps|ls)\b') {
                $sshPrefix = $sshPrefix.Substring(0, $sshPrefix.IndexOf($Matches[0]))
            }
            $hasDashN = ($sshPrefix -match '(?i)\s-[a-zA-Z0-9]*n\b')
            if (-not $hasDashN) {
                Write-Output '{"decision":"deny","reason":"SAFETY GATE DENIAL: Noninteractive SSH reads/queries must include -n -T (e.g. ssh -n -T -F <config> <host> \"<cmd>\") to disconnect stdin from null and prevent remote processes from hanging indefinitely. Or use .\\.agents\\scripts\\Invoke-GuardedSsh.ps1."}'
                exit 0
            }
        }
    }


    # -------------------------------------------------------------
    # 4. Filter for qsub HPC Submissions
    # -------------------------------------------------------------
    # Detect the executable token even inside a guarded RemoteCommand and
    # regardless of qsub options. The former pattern missed "qsub -q ...".
    $isSubmissionCmd = ($cmd -match '(?i)(?:^|[\s"'';&|])qsub(?:\.exe)?(?=\s|$)')

    if (-not $isSubmissionCmd) {
        # Non-cluster, non-qsub command -> Allowed
        Write-Output '{"decision":"allow"}'
        exit 0
    }

    # Technical execution validation only. Human approval, grant pins and
    # machine permit issuance were removed by explicit user directive.
    $repoRoot=Split-Path -Parent $PSScriptRoot
    . (Join-Path $repoRoot 'scripts/hpc/Invoke-Mode1Engine.ps1')
    $command64=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($cmd))
    $decision=Invoke-Mode1Engine -Arguments @('--command64',$command64)
    if($decision.decision -notin @('allow','deny')){throw 'Invalid technical gate response'}
    Write-Output ($decision|ConvertTo-Json -Compress)
} catch {
    Write-Output (@{decision='deny';reason=('TECHNICAL EXECUTION CHECK: '+$_.Exception.Message)}|ConvertTo-Json -Compress)
}
