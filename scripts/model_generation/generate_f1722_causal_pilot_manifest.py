#!/usr/bin/env python3
"""Generate F1722 execution authorization manifest for Mode-I Five-Hole Causal Pilot."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / 'models/pandey_kumar_mode1/214_f1720_adapted_mesh'
RUN_DIR = '/scratch9/pr21vyci/runs/mode1_pk_f1722_causal_pilot'
JOB_PBS = 'submit_M1_PK_F1722_CAUSAL_PILOT.pbs'

# Exact files required in the batch
FILES_TO_HASH = [
    'PK_F1721_CAUSAL_PILOT.inp',
    'f1721_proposed_staggered_coupling_uel.for',
    JOB_PBS,
    'job_notifications.sh',
    'M1_PK_F1722_DATACHECK.dat',
]

file_hashes = {}
for filename in FILES_TO_HASH:
    filepath = MODEL_DIR / filename
    if not filepath.is_file():
        raise FileNotFoundError(f"Missing required file: {filepath}")
    file_hashes[filename] = hashlib.sha256(filepath.read_bytes()).hexdigest().lower()

command = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq {RUN_DIR}/{JOB_PBS}"'
command_canonical = ' '.join(command.strip().split())
command_sha256 = hashlib.sha256(command_canonical.encode()).hexdigest().lower()

manifest = {
    "batch_name": "FIVE_HOLE_PK_F1722_CAUSAL_PILOT",
    "max_submissions": 1,
    "hours_valid": 24,
    "automatic_retry": False,
    "files": file_hashes,
    "jobs": [
        {
            "id": "f1722_five_hole_causal_pilot",
            "pbs": JOB_PBS,
            "command": command,
            "command_sha256": command_sha256,
            "max_submissions": 1,
            "depends_on": [],
            "purpose": "Pandey & Kumar (2025) Section 4.5 Five-Hole Adaptive Phase-Field Causal-Isolation Pilot on 13,163 physical elements (39,489 layered elements) under versioned committed-state staggered operator-split UEL f1721_proposed_staggered_coupling_uel.for to test post-peak convergence through uy = 0.00580 mm with matched loading rate and 1 CPU single-rank serial execution (F1720 serial baseline parity, eliminating multi-threading confounding variables)",
            "cpus": 1,
            "memory_gb": 16,
            "walltime_hours": 8,
            "queue": "entry_imfdfkmq",
            "execution": "single-rank serial",
            "input": "PK_F1721_CAUSAL_PILOT.inp",
            "datacheck": "M1_PK_F1722_DATACHECK.dat",
            "subroutine": "f1721_proposed_staggered_coupling_uel.for"
        }
    ],
    "acceptance": {
        "f1722_five_hole_causal_pilot": "Abaqus 2023 single-rank serial solve executes causal-isolation pilot to uy = 0.00580 mm; advancement past uy = 0.0056645 mm without cutback exhaustion supports hypothesis F1721-H1-R1 (committed-state staggered operator-split coupling improves continuation in the tested configuration); repeated stalling at uy = 0.0056645 mm indicates modification alone was insufficient in this configuration; reaction force equilibrium verified via bottom-boundary summation and damage bounds d in [0, 1] verified via UMAT overlay STATEV (SDV1)."
    },
    "adapter": "mode1-five-hole-staggered-v1",
    "scientific_scope": "FIVE_HOLE",
    "technical_stage": "FIVE_HOLE_CAUSAL_PILOT",
    "configuration": "FIVE_HOLE_STAGGERED",
    "remote_run_dir": RUN_DIR,
    "required_state_checks": [
        "nodal_displacement_verified",
        "damage_irreversibility_verified",
        "committed_history_verified",
        "state_restoration_verified"
    ]
}

manifest_path = MODEL_DIR / 'F1722_PK_FIVE_HOLE_CAUSAL_PILOT_AUTHORIZATION.json'
with open(manifest_path, 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=2)
    f.write('\n')

print(f"Manifest written successfully to: {manifest_path}")
print(f"Manifest SHA-256: {hashlib.sha256(manifest_path.read_bytes()).hexdigest()}")
print(f"Command SHA-256:  {command_sha256}")
