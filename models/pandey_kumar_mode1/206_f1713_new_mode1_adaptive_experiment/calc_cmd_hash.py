import hashlib

cmd = 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_pk_f1713_job2_adapted/submit_M1_PK_F1713_JOB2_ADAPTED.pbs"'
h = hashlib.sha256(cmd.encode('utf-8')).hexdigest()
print("Command SHA-256:", h)
