# Background .NET readers keep anonymous-pipe I/O off the PowerShell watchdog thread.
if(-not ('AgyProcessPumpV3' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Text;
using System.Threading;
using System.Diagnostics;
using System.Collections.Concurrent;

public sealed class AgyProcessPumpV3 {
    public readonly ConcurrentQueue<string> Out = new ConcurrentQueue<string>();
    public readonly ConcurrentQueue<string> Err = new ConcurrentQueue<string>();
    public volatile bool OutDone, ErrDone, InputDone;
    public Exception InputError, ReadError;
    Thread output, error, input;

    void Read(Stream stream, ConcurrentQueue<string> queue, bool isError) {
        try {
            var bytes = new byte[4096];
            var chars = new char[8192];
            var decoder = new UTF8Encoding(false, false).GetDecoder();
            int n;
            while((n = stream.Read(bytes, 0, bytes.Length)) > 0) {
                int count = decoder.GetChars(bytes, 0, n, chars, 0, false);
                if(count > 0) queue.Enqueue(new string(chars, 0, count));
            }
            int remaining = decoder.GetChars(bytes, 0, 0, chars, 0, true);
            if(remaining > 0) queue.Enqueue(new string(chars, 0, remaining));
        } catch(Exception ex) { ReadError = ex; }
        finally { if(isError) ErrDone = true; else OutDone = true; }
    }

    public void Start(Process process, string text) {
        output = new Thread(() => Read(process.StandardOutput.BaseStream, Out, false));
        error = new Thread(() => Read(process.StandardError.BaseStream, Err, true));
        input = new Thread(() => {
            try {
                if(!string.IsNullOrEmpty(text)) {
                    byte[] utf8Bytes = new UTF8Encoding(false, false).GetBytes(text + "\n");
                    process.StandardInput.BaseStream.Write(utf8Bytes, 0, utf8Bytes.Length);
                    process.StandardInput.BaseStream.Flush();
                }
                process.StandardInput.Close();
            } catch(Exception ex) { InputError = ex; }
            finally { InputDone = true; }
        });
        output.IsBackground = true; error.IsBackground = true; input.IsBackground = true;
        output.Start(); error.Start(); input.Start();
    }
    public void Join() { output.Join(1000); error.Join(1000); input.Join(1000); }
}
'@
}
function Invoke-BoundedAgyProcess {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [string[]]$ArgumentList=@(), [string]$InputText='',
        [ValidateRange(1,86400)][int]$TimeoutSeconds=2460,
        [string]$WorkingDirectory=(Get-Location).Path,
        [scriptblock]$Checkpoint={}, [scriptblock]$OnStarted={},
        [int]$CheckpointIntervalSeconds=15,
        [scriptblock]$ProgressProbe={ $false },
        [int]$NoProgressSeconds=0, [int]$StatusIntervalSeconds=30,
        [string]$OutputLogPath='', [scriptblock]$OnOutput={param($Chunk)}
    )
    $quoted=foreach($arg in $ArgumentList){ '"'+([regex]::Replace(([regex]::Replace($arg,'(\\*)"','$1$1\"')),'(\\+)$','$1$1'))+'"' }
    $info=[Diagnostics.ProcessStartInfo]::new()
    $info.FileName=$FilePath; $info.Arguments=$quoted -join ' '; $info.WorkingDirectory=$WorkingDirectory
    $info.UseShellExecute=$false; $info.CreateNoWindow=$true
    $info.RedirectStandardInput=$true; $info.RedirectStandardOutput=$true; $info.RedirectStandardError=$true
    $info.StandardOutputEncoding=[Text.UTF8Encoding]::new($false)
    $info.StandardErrorEncoding=[Text.UTF8Encoding]::new($false)
    $proc=[Diagnostics.Process]::new(); $proc.StartInfo=$info
    $clock=[Diagnostics.Stopwatch]::StartNew(); $started=$false
    $out=[Text.StringBuilder]::new(); $err=[Text.StringBuilder]::new()
    $reason=''; $nextCheckpoint=0.0; $nextStatus=[double]$StatusIntervalSeconds; $lastProgress=0.0
    $pump=$null; $failure=$null
    try {
        [void]$proc.Start(); $started=$true
        & $OnStarted $proc.Id | Out-Null
        $pump=[AgyProcessPumpV3]::new(); $pump.Start($proc,$InputText)
        while($true) {
            foreach($queue in @($pump.Out,$pump.Err)) {
                $chunk=$null
                while($queue.TryDequeue([ref]$chunk)) {
                    if([object]::ReferenceEquals($queue,$pump.Out)){[void]$out.Append($chunk)}else{[void]$err.Append($chunk)}
                    if($OutputLogPath){[IO.File]::AppendAllText($OutputLogPath,$chunk,[Text.UTF8Encoding]::new($false))}
                    & $OnOutput $chunk | Out-Null
                    $chunk=$null
                }
            }
            if($clock.Elapsed.TotalSeconds -ge $nextCheckpoint) {
                & $Checkpoint | Out-Null
                if(& $ProgressProbe){$lastProgress=$clock.Elapsed.TotalSeconds}
                $nextCheckpoint=$clock.Elapsed.TotalSeconds+$CheckpointIntervalSeconds
            }
            if($clock.Elapsed.TotalSeconds -ge $nextStatus) {
                Write-Host ('[PROGRESS] elapsed={0:N0}s; no saved result for {1:N0}s; captured={2} chars; PID={3}' -f $clock.Elapsed.TotalSeconds,($clock.Elapsed.TotalSeconds-$lastProgress),($out.Length+$err.Length),$proc.Id)
                $nextStatus=$clock.Elapsed.TotalSeconds+$StatusIntervalSeconds
            }
            if($proc.HasExited -and $pump.OutDone -and $pump.ErrDone -and $pump.Out.IsEmpty -and $pump.Err.IsEmpty){break}
            if($clock.Elapsed.TotalSeconds -ge $TimeoutSeconds){$reason='WORK_DEADLINE';break}
            if($NoProgressSeconds -gt 0 -and ($clock.Elapsed.TotalSeconds-$lastProgress) -ge $NoProgressSeconds){$reason='NO_DURABLE_PROGRESS';break}
            [Threading.Thread]::Sleep(50)
        }
    } catch { $failure=$_ }
    finally {
        if($started -and -not $proc.HasExited) {
            $killer=Start-Process -FilePath "$env:SystemRoot/System32/taskkill.exe" -ArgumentList @('/PID',$proc.Id,'/T','/F') -WindowStyle Hidden -PassThru
            if(-not $killer.WaitForExit(5000)){$killer.Kill()}
            $killer.Dispose()
            if(-not $proc.WaitForExit(2000)){$failure='Cannot terminate owned CLI process'}
        }
        # Drain bytes queued before termination, including incomplete JSON lines.
        if($null -ne $pump){
            $pump.Join()
            foreach($queue in @($pump.Out,$pump.Err)){
                $chunk=$null
                while($queue.TryDequeue([ref]$chunk)){
                    if([object]::ReferenceEquals($queue,$pump.Out)){[void]$out.Append($chunk)}else{[void]$err.Append($chunk)}
                    if($OutputLogPath){[IO.File]::AppendAllText($OutputLogPath,$chunk,[Text.UTF8Encoding]::new($false))}
                    $chunk=$null
                }
            }
        }
        $exitCode=if($reason){124}elseif($failure){1}elseif($started){$proc.ExitCode}else{1}
        $proc.Dispose()
    }
    if($failure){throw $failure}
    [pscustomobject]@{ExitCode=$exitCode;TimedOut=[bool]$reason;StopReason=$reason;Output=($out.ToString()+"`r`n"+$err.ToString());DurationSeconds=$clock.Elapsed.TotalSeconds}
}
