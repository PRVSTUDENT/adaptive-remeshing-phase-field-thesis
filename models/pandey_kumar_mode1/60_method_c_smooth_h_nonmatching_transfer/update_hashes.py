import hashlib
import json
from pathlib import Path

brain_scratch = Path(r"C:\Users\pruth\.gemini\antigravity-cli\brain\18c98474-bc37-40f5-9dc7-1369029e4645\scratch\package60_staging")

def sha256_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().lower()

files_dict = {
    "M1_EXP_NONMATCHING_SMOOTH_H_650.inp": sha256_file(brain_scratch / "M1_EXP_NONMATCHING_SMOOTH_H_650.inp"),
    "f42_experimental_offset_uel.for": sha256_file(brain_scratch / "f42_experimental_offset_uel.for"),
    "job_notifications.sh": sha256_file(brain_scratch / "job_notifications.sh"),
    "offset_state_table.csv": sha256_file(brain_scratch / "offset_state_table.csv"),
    "submit_M1_EXP_NONMATCHING_SMOOTH_H_650.pbs": sha256_file(brain_scratch / "submit_M1_EXP_NONMATCHING_SMOOTH_H_650.pbs"),
}

pkg_manifest = {
    "package_name": "package60_method_c_smooth_h_nonmatching_transfer",
    "version": "1.0",
    "model": "pandey_kumar_mode1",
    "configuration": "EXPERIMENTAL_OFFSET_SMOOTH_H",
    "adapter": "mode1-experimental-offset-v1",
    "created_at": "2026-10-19T12:00:00+02:00",
    "files": files_dict
}
manifest_candidate = brain_scratch / "PACKAGE_MANIFEST.json"
with open(manifest_candidate, "w") as f:
    json.dump(pkg_manifest, f, indent=2)

files_dict["PACKAGE_MANIFEST.json"] = sha256_file(manifest_candidate)

auth_manifest = {
    "batch_name": "MODE1_EXP_NONMATCHING_SMOOTH_H_650",
    "adapter": "mode1-experimental-offset-v1",
    "scientific_scope": "MODE1",
    "technical_stage": "EXPERIMENTAL_OFFSET",
    "configuration": "EXPERIMENTAL_OFFSET",
    "hypothesis": "Continuous bilinear shape-function projection of Gauss-point history H combined with discrete equilibrium phase-field initialization eliminates the -0.0810 damage healing violation and restores zero-increment variational equilibrium on nonmatching meshes.",
    "max_submissions": 1,
    "hours_valid": 24,
    "automatic_retry": False,
    "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_package60_smooth_h_nonmatching_transfer",
    "files": files_dict,
    "jobs": [
        {
            "id": "M1_EXP_NONMATCHING_SMOOTH_H_650",
            "pbs": "submit_M1_EXP_NONMATCHING_SMOOTH_H_650.pbs",
            "command": "powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_package60_smooth_h_nonmatching_transfer/submit_M1_EXP_NONMATCHING_SMOOTH_H_650.pbs\"",
            "command_sha256": hashlib.sha256(b"powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand \"qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_package60_smooth_h_nonmatching_transfer/submit_M1_EXP_NONMATCHING_SMOOTH_H_650.pbs\"").hexdigest().lower(),
            "max_submissions": 1,
            "depends_on": [],
            "purpose": "Continuous bilinear H nonmatching mesh state transfer diagnostic (400 -> 650 quads, a0=0.040 mm) under offset UEL",
            "cpus": 1,
            "memory_gb": 16,
            "walltime_hours": 4,
            "queue": "entry_imfdfkmq",
            "execution": "single-rank serial",
            "input": "M1_EXP_NONMATCHING_SMOOTH_H_650.inp",
            "datacheck": "M1_EXP_NONMATCHING_SMOOTH_H_650_DC.dat"
        }
    ],
    "acceptance": {
        "M1_EXP_NONMATCHING_SMOOTH_H_650": "Exit code 0; zero-increment healing violation min(delta_d) > -0.010 (90%+ reduction from -0.0810); rapid Newton convergence in <= 5 iterations on Step 1."
    }
}
auth_candidate = brain_scratch / "NONMATCHING_SMOOTH_H_AUTHORIZATION.json"
with open(auth_candidate, "w") as f:
    json.dump(auth_manifest, f, indent=2)

print("Updated hashes successfully:")
for k, v in files_dict.items():
    print(f"  {k}: {v}")
