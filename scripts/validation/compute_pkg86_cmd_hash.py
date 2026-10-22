import hashlib

cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_package86_donor_sameprocess_staggered/submit_M1_DONOR_SAMEPROCESS_STAGGERED.pbs"'
print(hashlib.sha256(cmd.encode("utf-8")).hexdigest())
