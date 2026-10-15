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

    # -------------------------------------------------------------
    # 5. Atomic WSL Verification & Consumption
    # -------------------------------------------------------------
    $pyCheck = @"
import json, os, sys, hashlib, fcntl, re
from datetime import datetime, timezone

state_file = '/home/openclaw/.openclaw/workspace-antigravity-controller/controller-state.json'
lock_file = state_file + '.lock'

if not os.path.exists(state_file):
    print('DENY: Controller state file missing.')
    sys.exit(1)

incoming_cmd = sys.argv[1] if len(sys.argv) > 1 else ''

def canonicalize_cmd(c):
    return ' '.join(c.strip().split())

def sha256_text(t):
    return hashlib.sha256(t.encode('utf-8')).hexdigest()

incoming_canonical = canonicalize_cmd(incoming_cmd)
incoming_hash = sha256_text(incoming_canonical)

with open(lock_file, 'w') as lf:
    fcntl.flock(lf, fcntl.LOCK_EX)
    try:
        with open(state_file, 'r', encoding='utf-8') as sf:
            state = json.load(sf)

        delegation = state.get('daily_chatgpt_delegation', {})
        auth = state.get('submission_authorization', {})
        jobs = state.get('jobs', {})

        # A. Validate Daily Delegation & Expiry
        if not delegation.get('active', False):
            print('DENY: Daily ChatGPT delegation is inactive.')
            sys.exit(1)

        exp_str = delegation.get('expires_at', '')
        try:
            expiry = datetime.fromisoformat(exp_str.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) >= expiry:
                print('DENY: Daily ChatGPT delegation has expired.')
                sys.exit(1)
        except Exception as e:
            print(f'DENY: Invalid expiry format ({e}).')
            sys.exit(1)

        # B. Validate Single-Use Permit Activity
        if not auth.get('active', False):
            print('DENY: No active submission permit in state.')
            sys.exit(1)

        if auth.get('consumed', 0) >= auth.get('max_submissions', 1):
            print('DENY: Single-use submission permit is already consumed.')
            sys.exit(1)

        # C. Validate Command SHA-256 Binding
        auth_hash = auth.get('authorized_command_sha256')
        auth_cmd_raw = auth.get('authorized_command')
        auth_cmds = auth.get('authorized_commands', [])
        auth_hashes = auth.get('authorized_command_hashes', [])

        cmd_matched = False
        if auth_hash and incoming_hash == auth_hash:
            cmd_matched = True
        elif auth_cmd_raw and sha256_text(canonicalize_cmd(auth_cmd_raw)) == incoming_hash:
            cmd_matched = True
        elif incoming_hash in auth_hashes:
            cmd_matched = True
        elif any(sha256_text(canonicalize_cmd(c)) == incoming_hash for c in auth_cmds):
            cmd_matched = True

        if not cmd_matched:
            print(f'DENY: Command content mismatch with authorized command. Actual: {incoming_hash}')
            sys.exit(1)

        # D. Validate Candidate Manifest SHA-256 Binding
        permit_manifest = auth.get('candidate_manifest_sha256')
        preflight = auth.get('notification_preflight', {})
        preflight_manifest = preflight.get('candidate_manifest_sha256')

        if not permit_manifest:
            print('DENY: Submission permit missing candidate manifest SHA-256 hash.')
            sys.exit(1)

        if not preflight_manifest or preflight_manifest != permit_manifest:
            print('DENY: Notification preflight manifest hash does not match authorized permit manifest.')
            sys.exit(1)

        # Bounded Method C batch: immutable files, once per exact command,
        # and scientific checkpoint review before any dependent submission.
        batch_job = None
        if str(auth.get('batch_name', '')).startswith('MODE1_PACKAGE48') and preflight.get('file_hashes'):
            import base64, gzip
            live = json.loads(gzip.decompress(base64.b64decode(sys.argv[2])))
            if any(live.get('file_hashes', {}).get(name) != expected
                   for name, expected in preflight['file_hashes'].items()):
                print('DENY: Previously approved Package 48 files changed; fresh human batch approval required.')
                sys.exit(1)
        if auth.get('batch_manifest_path'):
            try:
                if datetime.now(timezone.utc) >= datetime.fromisoformat(auth['expires_at']):
                    raise ValueError('Batch permit expired')
                import base64, gzip
                context = json.loads(gzip.decompress(base64.b64decode(sys.argv[2])))
                batch_bytes = base64.b64decode(context['manifest_bytes_b64'], validate=True)
                if hashlib.sha256(batch_bytes).hexdigest() != permit_manifest:
                    raise ValueError('Batch manifest changed')
                batch = json.loads(batch_bytes)
                if batch['max_submissions'] != auth['max_submissions'] or batch['max_submissions'] != 3:
                    raise ValueError('Batch submission budget mismatch')
                for name, expected in batch['files'].items():
                    if os.path.basename(name) != name:
                        raise ValueError('Unsafe batch file path')
                    if context.get('file_hashes', {}).get(name) != expected:
                        raise ValueError('Batch candidate file changed: ' + name)
                    if preflight.get('file_hashes', {}).get(name) != expected:
                        raise ValueError('Batch file was not verified by human preflight')
                matches = [j for j in batch['jobs'] if j['command_sha256'] == incoming_hash and
                           sha256_text(canonicalize_cmd(j['command'])) == incoming_hash]
                if len(matches) != 1:
                    raise ValueError('Command absent or ambiguous in immutable batch')
                batch_job = matches[0]
                counts = auth.get('command_consumption', {})
                if counts.get(incoming_hash, 0) >= batch_job['max_submissions']:
                    raise ValueError('This exact batch command is already consumed')
                if batch_job.get('depends_on'):
                    donor = next(j for j in batch['jobs'] if j['id'] == 'donor')
                    if counts.get(donor['command_sha256'], 0) != 1:
                        raise ValueError('Donor has not been submitted under this batch')
                    review = context.get('dependency_review', {})
                    if not (review.get('batch_manifest_sha256') == permit_manifest and
                            review.get('donor_terminal_exit_status') == 0 and
                            review.get('checkpoint_verified') is True and
                            review.get('scientific_review') == 'PASS' and
                            review.get('handoff_displacement_mm') == 0.005 and
                            review.get('checkpoint_hashes') and
                            re.fullmatch(r'\d+\.mmaster02', review.get('donor_pbs_job_id', '')) and
                            review.get('donor_pbs_job_id') != '1413808.mmaster02' and
                            review.get('reviewed_by') and review.get('evidence_report')):
                        raise ValueError('Authentic donor checkpoint scientific review not passed')
                    for checkpoint, digest in review['checkpoint_hashes'].items():
                        if not re.fullmatch(r'[0-9a-fA-F]{64}', digest):
                            raise ValueError('Checkpoint hash invalid')
            except Exception as e:
                print('DENY: Batch verification: ' + str(e))
                sys.exit(1)

        # E. Validate Notification Preflight Delivery Verification
        if not (preflight.get('passed', False) and 
                preflight.get('pbs_email_verified', False) and 
                preflight.get('telegram_verified', False)):
            print('DENY: Dual-channel notification preflight (email + Telegram) not verified.')
            sys.exit(1)

        # F. Strict Concurrency Check (SUBMITTED + QUEUED + RUNNING <= max_concurrent_jobs)
        active_jobs = [j for j, d in jobs.items() if d.get('status') in ['SUBMITTED', 'QUEUED', 'RUNNING']]
        max_active = delegation.get('max_concurrent_jobs', 2)
        if len(active_jobs) >= max_active:
            print(f'DENY: Strict concurrency limit reached ({len(active_jobs)}/{max_active} active jobs in PBS).')
            sys.exit(1)

        # -------------------------------------------------------------
        # ATOMIC CONSUMPTION: Mutate permit on disk while lock is held
        # -------------------------------------------------------------
        auth['consumed'] = auth.get('consumed', 0) + 1
        if batch_job is not None:
            auth.setdefault('command_consumption', {})[incoming_hash] = auth.get('command_consumption', {}).get(incoming_hash, 0) + 1
            auth.setdefault('consumption_audit', []).append({'job': batch_job['id'], 'command_sha256': incoming_hash, 'at': datetime.now(timezone.utc).isoformat()})
        if auth['consumed'] >= auth.get('max_submissions', 1):
            auth['active'] = False
        auth['consumed_at'] = datetime.now(timezone.utc).isoformat()
        auth['consumed_by_command_sha256'] = incoming_hash
        state['submission_authorization'] = auth
        state['workflow_status'] = 'PERMIT_CONSUMED_SUBMITTING'

        tmp_file = state_file + '.tmp'
        with open(tmp_file, 'w', encoding='utf-8') as tf:
            json.dump(state, tf, indent=2)
            tf.flush()
            os.fsync(tf.fileno())

        os.replace(tmp_file, state_file)
        sys.exit(0) # ALLOWED

    finally:
        fcntl.flock(lf, fcntl.LOCK_UN)
"@

    $b64Code = ConvertTo-GuardCompressedBase64 ([System.Text.Encoding]::UTF8.GetBytes($pyCheck))
    $b64Cmd  = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($cmd))
    # This WSL distro intentionally disables Windows drive automounts.
    # Read the live immutable package from trusted PowerShell, not tool args.
    $repoRoot = Split-Path -Parent $PSScriptRoot
    $packageRoot = Join-Path $repoRoot 'models/pandey_kumar_mode1/48_method_c_stage_c1_0_restart_positive_control'
    $batchPath = Join-Path $packageRoot 'METHOD_C_BATCH_AUTHORIZATION.json'
    $context = @{}
    if(Test-Path -LiteralPath $batchPath){
        $batchBytes=[IO.File]::ReadAllBytes($batchPath)
        $batchData=[Text.Encoding]::UTF8.GetString($batchBytes)|ConvertFrom-Json
        $actualHashes=@{}
        foreach($property in $batchData.files.PSObject.Properties){
            if([IO.Path]::GetFileName($property.Name) -cne $property.Name){throw 'Unsafe candidate filename'}
            $actualHashes[$property.Name]=(Get-FileHash -LiteralPath (Join-Path $packageRoot $property.Name)).Hash.ToLowerInvariant()
        }
        $context=@{manifest_bytes_b64=[Convert]::ToBase64String($batchBytes);file_hashes=$actualHashes}
        $reviewPath=Join-Path $repoRoot 'project_coordination/METHOD_C_DONOR_CHECKPOINT_REVIEW.json'
        if(Test-Path -LiteralPath $reviewPath){$context.dependency_review=Get-Content -LiteralPath $reviewPath -Raw|ConvertFrom-Json}
    }
    $b64Context=ConvertTo-GuardCompressedBase64 ([Text.Encoding]::UTF8.GetBytes(($context|ConvertTo-Json -Depth 16 -Compress)))

    $checkOutput = wsl.exe -d OpenClawGateway -u openclaw -- python3 -c "import sys, base64,gzip; incoming_raw = base64.b64decode(sys.argv[1]).decode('utf-8'); sys.argv[1] = incoming_raw; exec(gzip.decompress(base64.b64decode('$b64Code')).decode('utf-8'))" "$b64Cmd" "$b64Context" 2>&1
    $checkExit = $LASTEXITCODE

    if ($checkExit -eq 0) {
        Write-Output '{"decision":"allow"}'
    } else {
        $reasonMsg = ($checkOutput | Out-String).Trim()
        if ([string]::IsNullOrWhiteSpace($reasonMsg)) {
            $reasonMsg = "UNAUTHORIZED CLUSTER SUBMISSION BLOCKED."
        }
        $res = [PSCustomObject]@{
            decision = "deny"
            reason   = "SAFETY GATE DENIAL: $reasonMsg"
        } | ConvertTo-Json -Compress
        Write-Output $res
    }
} catch {
    $err = $_.Exception.Message
    $res = [PSCustomObject]@{
        decision = "deny"
        reason   = "SAFETY GATE ERROR: Evaluation crashed (fail closed): $err"
    } | ConvertTo-Json -Compress
    Write-Output $res
}
