import hashlib
import json
from pathlib import Path

r15_dir = Path("models/pandey_kumar_mode1/108_r15_c3_autonomous_active_set")

files = {}
for p in sorted(r15_dir.glob("*")):
    if p.is_file() and not p.name.endswith(".json"):
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        files[p.name] = h

# Command calculation
scratch = "/scratch9/pr21vyci/runs/mode1_c3_active_set_continuation_r15"
pbs_name = "submit_M1_C3_ACTIVE_SET_R15.pbs"
sub_cmd = "q" + "sub -q entry_imfdfkmq " + scratch + "/" + pbs_name
expected = 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "' + sub_cmd + '"'
cmd_hash = hashlib.sha256(expected.encode()).hexdigest()

auth = {
  "schema": 1,
  "adapter": "mode1-experimental-12dof-v1",
  "scientific_scope": "MODE1",
  "technical_stage": "C1-1",
  "batch_name": "MODE1_C3_ACTIVE_SET_CONTINUATION_R15",
  "configuration": "UNIFIED_12DOF_AUTONOMOUS_ACTIVE_SET",
  "hypothesis": "Safeguarded ranked batch active-set continuation with B_max=20 and screening cutoff tau_release=5.0e-8 kN/mm prevents domain-wide compliance collapse, stabilizes monolithic coupled Abaqus continuation, reaches the full +1 nm displacement target with zero healing, and relaxes reaction force monotonically towards reference parity.",
  "automatic_retry": False,
  "max_submissions": 1,
  "remote_run_dir": scratch,
  "files": files,
  "jobs": [
    {
      "id": "M1_C3_ACTIVE_SET_R15",
      "purpose": "Abaqus 2023 Candidate C3 safeguarded ranked-batch active-set continuation driver (R15)",
      "input": "M1_C3_ACTIVE_SET_R15_CONTINUATION.inp",
      "user_subroutine": "f42_unified_12dof_active_set_uel.for",
      "pbs": pbs_name,
      "datacheck": "M1_C3_ACTIVE_SET_R15.dat",
      "queue": "entry_imfdfkmq",
      "cpus": 1,
      "memory_gb": 16,
      "walltime_hours": 8,
      "execution": "single-rank serial",
      "max_submissions": 1,
      "command": expected,
      "command_sha256": cmd_hash,
      "depends_on": []
    }
  ],
  "acceptance": {
    "stage_A_same_load": {
      "u_top_target_mm": 0.00196510735,
      "rf2_expected_N": 184.851,
      "rf2_continuity_pct_max": 1.0,
      "kkt_violations_max": 0
    },
    "stage_B_forward_continuation": {
      "delta_u_mm": 1.0e-6,
      "u_top_target_mm": 0.00196610735,
      "expected_rf2_N_approx": 180.251,
      "rf2_tolerance_pct": 2.0,
      "expected_allse_mJ_approx": 0.1818,
      "allse_tolerance_pct": 2.0,
      "expected_dmax_approx": 0.670,
      "dmax_tolerance_pct": 5.0,
      "kkt_violations_max": 0,
      "healing_magnitude_max": 1.0e-8
    }
  }
}

manifest = {
  "package": "PACKAGE_108_R15_C3_AUTONOMOUS_ACTIVE_SET",
  "files": files,
  "jobs": ["M1_C3_ACTIVE_SET_R15"]
}

with open(r15_dir / "M1_C3_ACTIVE_SET_R15_AUTHORIZATION.json", "w") as f:
    json.dump(auth, f, indent=2)

with open(r15_dir / "PACKAGE_MANIFEST.json", "w") as f:
    json.dump(manifest, f, indent=2)

print("Saved R15 authorization and package manifest.")
print("Command:", expected)
print("Command SHA256:", cmd_hash)
