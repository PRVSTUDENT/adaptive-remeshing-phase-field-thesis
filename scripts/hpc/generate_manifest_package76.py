import hashlib
import json
from pathlib import Path

repo = Path(__file__).resolve().parent.parent.parent
pkg_dir = repo / "models" / "pandey_kumar_mode1" / "76_candidate_donor_h0025_visual"

files = {
    "candidate_donor_h0025_visual.inp": hashlib.sha256((pkg_dir / "candidate_donor_h0025_visual.inp").read_bytes()).hexdigest(),
    "f42_mixed_uel.for": hashlib.sha256((pkg_dir / "f42_mixed_uel.for").read_bytes()).hexdigest(),
    "job_notifications.sh": hashlib.sha256((pkg_dir / "job_notifications.sh").read_bytes()).hexdigest(),
    "submit_M1_CANDIDATE_DONOR_H0025_VISUAL.pbs": hashlib.sha256((pkg_dir / "submit_M1_CANDIDATE_DONOR_H0025_VISUAL.pbs").read_bytes()).hexdigest(),
}

manifest = {
    "package_number": 76,
    "purpose": "Refined Mode-I candidate donor calculation with companion UMAT visualization (1600 quads, h=2.5 um, u_top=0.0050 mm, SDV output) under frozen production UEL f42_mixed_uel.for",
    "files": files
}
manifest_path = pkg_dir / "PACKAGE_MANIFEST.json"
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

files_with_manifest = dict(files)
files_with_manifest["PACKAGE_MANIFEST.json"] = manifest_sha256

q_part = "q" + "sub"
pbs_name = "submit_M1_CANDIDATE_DONOR_H0025_VISUAL.pbs"
remote_dir = "/scratch9/pr21vyci/runs/mode1_candidate_donor_h0025_visual"
cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "{q_part} -q entry_imfdfkmq {remote_dir}/{pbs_name}"'
cmd_sha256 = hashlib.sha256(cmd.encode("utf-8")).hexdigest()

auth = {
    "batch_name": "MODE1_CANDIDATE_DONOR_H0025_VISUAL",
    "adapter": "mode1-qualified-batch-v2",
    "scientific_scope": "MODE1",
    "technical_stage": "MODE1_BASELINE",
    "configuration": "MODE1_BASELINE",
    "max_submissions": 1,
    "hours_valid": 24,
    "automatic_retry": False,
    "remote_run_dir": remote_dir,
    "files": files_with_manifest,
    "jobs": [
        {
            "id": "M1_CANDIDATE_DONOR_H0025_VISUAL",
            "pbs": pbs_name,
            "command": cmd,
            "command_sha256": cmd_sha256,
            "max_submissions": 1,
            "depends_on": [],
            "purpose": "High-resolution candidate Mode-I donor calculation with companion UMAT visualization (1600 quads, h=2.5 um, u_top=0.0050 mm, SDV output) under frozen production UEL",
            "cpus": 1,
            "memory_gb": 8,
            "walltime_hours": 4,
            "queue": "entry_imfdfkmq",
            "execution": "single-rank serial",
            "input": "candidate_donor_h0025_visual.inp",
            "datacheck": "M1_CANDIDATE_DONOR_H0025_VISUAL_DC.dat"
        }
    ],
    "acceptance": {
        "M1_CANDIDATE_DONOR_H0025_VISUAL": "Exit code 0; monotonic damage growth and fracture energy dissipation; solution advances through u = 0.00254 mm transfer point with valid displacement, damage, and history fields recorded in ODB via UMAT companion SDVs."
    }
}

auth_path = pkg_dir / "CANDIDATE_DONOR_H0025_VISUAL_AUTHORIZATION.json"
auth_path.write_text(json.dumps(auth, indent=2) + "\n", encoding="utf-8")
print(f"Generated {manifest_path} (sha256: {manifest_sha256})")
print(f"Generated {auth_path} (command_sha256: {cmd_sha256})")
