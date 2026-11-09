import hashlib
import json
import os

repo = r'D:\Master thesis\Adaptive remeshing'
model_dir = os.path.join(repo, 'models', 'pandey_kumar_mode1', '196_pk_sec43_standard_element_job1')

inp_file = 'PK_SEC43_STANDARD_JOB1.inp'
dc_file = 'PK_SEC43_STANDARD_JOB1_DC.dat'
pbs_file = 'submit_M1_PK_SEC43_STANDARD_JOB1.pbs'
notif_file = 'job_notifications.sh'

def file_sha256(fname):
    p = os.path.join(model_dir, fname)
    with open(p, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest().lower()

inp_sha = file_sha256(inp_file)
dc_sha = file_sha256(dc_file)
pbs_sha = file_sha256(pbs_file)
notif_sha = file_sha256(notif_file)

cmd = r'powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_pk_sec43_standard_job1/submit_M1_PK_SEC43_STANDARD_JOB1.pbs"'
cmd_sha = hashlib.sha256(cmd.encode('utf-8')).hexdigest().lower()

manifest = {
    "batch_name": "MODE1_METHOD_A_PK_SEC43_STANDARD",
    "max_submissions": 1,
    "hours_valid": 24,
    "automatic_retry": False,
    "files": {
        inp_file: inp_sha,
        pbs_file: pbs_sha,
        notif_file: notif_sha,
        dc_file: dc_sha
    },
    "jobs": [
        {
            "id": "pk_sec43_standard_job1",
            "pbs": pbs_file,
            "command": cmd,
            "command_sha256": cmd_sha,
            "max_submissions": 1,
            "depends_on": [],
            "purpose": "Method A Pandey-Kumar Section 4.3 Job-1 Standard-Element Formulation Test: Plane-stress linear elastic pre-analysis (*STATIC, DIRECT) on 3,923 physical elements (3,814 CPS4R quads, 109 CPS3 tris, 4,040 nodes), 1-CPU serial, 2-step loading to u_y = 1.5 mm, generating authentic standard-element donor ODB for native MISESERI error evaluation and comparison against Fig. 15b.",
            "cpus": 1,
            "memory_gb": 16,
            "walltime_hours": 8,
            "queue": "entry_imfdfkmq",
            "execution": "single-rank serial",
            "input": inp_file,
            "datacheck": dc_file
        }
    ],
    "acceptance": {
        "pk_sec43_standard_job1": "Abaqus 2023 single-rank serial solve completes Stage B Job-1 standard plane-stress element simulation on 3,923 elements to u_y = 1.5 mm, producing donor ODB with native MISESERI across load increments for evaluation against Fig. 15b."
    },
    "adapter": "mode1-continuum-preanalysis-v1",
    "configuration": "STANDARD_PLANE_STRESS_JOB1",
    "hypothesis": "A standard plane-stress element formulation (CPS4R/CPS3) produces a dual-branch elevated-error MISESERI band along both the notch-to-hole path and the secondary flank-to-edge path in the Section 4.3 holed plate.",
    "scientific_scope": "MODE1",
    "technical_stage": "CONTINUUM_PREANALYSIS",
    "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_pk_sec43_standard_job1",
    "required_state_checks": [
        "nodal_displacement_verified",
        "miseseri_recovery_verified",
        "linear_elastic_equilibrium_verified"
    ]
}

out_path = os.path.join(model_dir, 'METHOD_A_PK_SEC43_STANDARD_AUTHORIZATION.json')
with open(out_path, 'w') as f:
    json.dump(manifest, f, indent=2)

print('Wrote manifest to:', out_path)
print('Inp SHA:', inp_sha)
print('PBS SHA:', pbs_sha)
print('Cmd SHA:', cmd_sha)
