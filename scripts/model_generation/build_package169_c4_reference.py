"""Builder script for Package 169: Continuous C4 Two-Checkpoint Reference Experiment.

This package generates an authentic, continuous, monotonic Abaqus/Standard simulation
on the Candidate C4 mesh (7,056 quads, 7,265 nodes) using the frozen production UEL
f42_mixed_uel.for (SHA-256: CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6).

Loading Schedule (Monotonic, rate = 0.005 mm/s):
  Step 1: Monotonic loading to Frame 77 (uy = 0.0018003125442192 mm, t = 0.36006251 s)
  Step 2: Monotonic continuation to Checkpoint 01 (uy = 0.0018603125442191958 mm, t = 0.01200000 s)
  Step 3: Monotonic continuation to Reference A (uy = 0.0018653125442191958 mm, +5 nm, t = 0.00100000 s)
  Step 4: Monotonic continuation to Reference B (uy = 0.0018703125442191958 mm, +5 nm, t = 0.00100000 s)
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil

REPO_ROOT = Path(__file__).resolve().parents[2]
P160_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "160_c4_exact_load_reference"
P169_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "169_c4_two_checkpoint_reference"
FROZEN_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def build_package_169() -> dict:
    P169_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Building Package 169 in {P169_DIR}...")

    # 1. Copy f42_mixed_uel.for and verify hash
    src_uel = P160_DIR / "f42_mixed_uel.for"
    dst_uel = P169_DIR / "f42_mixed_uel.for"
    shutil.copy2(src_uel, dst_uel)
    actual_uel_hash = sha256_file(dst_uel)
    if actual_uel_hash != FROZEN_UEL_SHA256:
        raise ValueError(f"UEL SHA-256 mismatch: {actual_uel_hash} != {FROZEN_UEL_SHA256}")
    print(f"Verified frozen production UEL: {actual_uel_hash}")

    # 2. Copy job_notifications.sh
    shutil.copy2(P160_DIR / "job_notifications.sh", P169_DIR / "job_notifications.sh")

    # 3. Read base input deck up to end of Step 1 from P160
    base_inp = (P160_DIR / "M1_C4_EXACT_LOAD_REF.inp").read_text(encoding="utf-8")
    end_step1_idx = base_inp.find("** STEP 2: Monotonic Continuation")
    if end_step1_idx == -1:
        raise ValueError("Could not find Step 2 boundary in base P160 inp")

    prefix = base_inp[:end_step1_idx]

    # Update header in prefix
    prefix = prefix.replace(
        "** Continuous C4 Exact-Load Reference Simulation (Package 160)\n"
        "** Target Displacement: uy = 0.0018603125442191958 mm",
        "** Continuous C4 Two-Checkpoint Reference Simulation (Package 169)\n"
        "** Target Displacements: Reference A uy = 0.0018653125442191958 mm, Reference B uy = 0.0018703125442191958 mm"
    )
    prefix = prefix.replace(
        "** Two-step continuous loading: Step 1 lands on Frame 77 (u = 0.0018003125 mm), Step 2 terminates exactly at u = 0.0018603125442191958 mm",
        "** Four-step continuous loading: Step 1 (Frame 77, 0.0018003125 mm), Step 2 (Checkpoint 01, 0.001860312544 mm),\n"
        "** Step 3 (Reference A, 0.001865312544 mm), Step 4 (Reference B, 0.001870312544 mm)"
    )

    # 4. Construct Steps 2, 3, and 4
    steps_suffix = (
        "** ==========================================================\n"
        "** STEP 2: Monotonic Continuation to Checkpoint 01\n"
        "** Target Displacement: uy = 0.0018603125442191958 mm (delta_u = +60 nm)\n"
        "** ==========================================================\n"
        "*Step, name=Step-2, nlgeom=NO, inc=1000\n"
        "*Static\n"
        "1.0e-3, 0.0120000000, 1.0e-8, 5.0e-3\n"
        "*Boundary\n"
        "N_RP, 2, 2, 0.0018603125442191958\n"
        "** Output requests\n"
        "*Output, field, frequency=1\n"
        "*Node Output\n"
        "U, RF\n"
        "*Element Output, elset=umatelem\n"
        "SDV, S, E\n"
        "*Node Print, frequency=1000\n"
        "U, RF\n"
        "*Output, history, frequency=1\n"
        "*Node Output, nset=N_RP\n"
        "U2, RF2\n"
        "*Energy Output\n"
        "ALLSE, ALLWK\n"
        "*Restart, write, frequency=1\n"
        "*End Step\n"
        "** ==========================================================\n"
        "** STEP 3: Monotonic Continuation to Reference A (C5-R3 Comparator)\n"
        "** Target Displacement: uy = 0.0018653125442191958 mm (delta_u = +5 nm)\n"
        "** ==========================================================\n"
        "*Step, name=Step-3, nlgeom=NO, inc=1000\n"
        "*Static\n"
        "1.0e-4, 0.0010000000, 1.0e-8, 1.0e-3\n"
        "*Boundary\n"
        "N_RP, 2, 2, 0.0018653125442191958\n"
        "** Output requests\n"
        "*Output, field, frequency=1\n"
        "*Node Output\n"
        "U, RF\n"
        "*Element Output, elset=umatelem\n"
        "SDV, S, E\n"
        "*Node Print, frequency=1000\n"
        "U, RF\n"
        "*Output, history, frequency=1\n"
        "*Node Output, nset=N_RP\n"
        "U2, RF2\n"
        "*Energy Output\n"
        "ALLSE, ALLWK\n"
        "*Restart, write, frequency=1\n"
        "*End Step\n"
        "** ==========================================================\n"
        "** STEP 4: Monotonic Continuation to Reference B (C4-R8 & P167 Comparator)\n"
        "** Target Displacement: uy = 0.0018703125442191958 mm (delta_u = +5 nm)\n"
        "** ==========================================================\n"
        "*Step, name=Step-4, nlgeom=NO, inc=1000\n"
        "*Static\n"
        "1.0e-4, 0.0010000000, 1.0e-8, 1.0e-3\n"
        "*Boundary\n"
        "N_RP, 2, 2, 0.0018703125442191958\n"
        "** Output requests\n"
        "*Output, field, frequency=1\n"
        "*Node Output\n"
        "U, RF\n"
        "*Element Output, elset=umatelem\n"
        "SDV, S, E\n"
        "*Node Print, frequency=1000\n"
        "U, RF\n"
        "*Output, history, frequency=1\n"
        "*Node Output, nset=N_RP\n"
        "U2, RF2\n"
        "*Energy Output\n"
        "ALLSE, ALLWK\n"
        "*Restart, write, frequency=1\n"
        "*End Step\n"
    )

    full_inp = prefix + steps_suffix
    inp_path = P169_DIR / "M1_C4_TWO_CHECKPOINT_REF.inp"
    inp_path.write_bytes(full_inp.replace("\r\n", "\n").encode("utf-8"))
    print(f"Generated input deck: {inp_path.name} ({len(full_inp.splitlines())} lines)")

    # 5. Datacheck decks
    shutil.copy2(P160_DIR / "P160_MECHANICAL_DC.inp", P169_DIR / "P169_MECHANICAL_DC.inp")
    shutil.copy2(P160_DIR / "P160_PHASE_DC.inp", P169_DIR / "P169_PHASE_DC.inp")

    # 6. run_datacheck.sh
    dc_sh = f"""#!/bin/bash
set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_c4_two_checkpoint_reference"
cd "${{RUN_DIR}}"

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

case "${{1:-both}}" in
  mechanical)
    jobs=("P169_MECHANICAL_DC")
    ;;
  phase)
    jobs=("P169_PHASE_DC")
    ;;
  coupled)
    jobs=("M1_C4_TWO_CHECKPOINT_REF_DC")
    ;;
  both|all)
    jobs=("P169_MECHANICAL_DC" "P169_PHASE_DC")
    ;;
  *)
    echo "Unknown target: ${{1:-}}" >&2
    exit 64
    ;;
esac

for job in "${{jobs[@]}}"; do
  if [ "${{job}}" = "M1_C4_TWO_CHECKPOINT_REF_DC" ]; then
    inp="M1_C4_TWO_CHECKPOINT_REF.inp"
  else
    inp="${{job}}.inp"
  fi
  echo "Running Abaqus 2023 datacheck for ${{job}} (input=${{inp}})..."
  rm -f "${{job}}.dat" "${{job}}.log" "${{job}}.msg" "${{job}}.sta" "${{job}}.prt" "${{job}}.com"
  abaqus job="${{job}}" input="${{inp}}" user=f42_mixed_uel.for cpus=1 memory="16 gb" datacheck interactive > "${{job}}.stdout.txt" 2>&1
  test -f "${{job}}.dat"
  grep -q 'ANALYSIS DATACHECK COMPLETE' "${{job}}.dat"
  if grep -q '\\*\\*\\*ERROR' "${{job}}.dat"; then
    echo "ERROR: Datacheck failed for ${{job}}" >&2
    exit 66
  fi
  echo "${{job}}: AUTHENTIC_DATACHECK_PASS"
done

echo "AUTHENTIC_DATACHECK_PASS_BOTH"
"""
    (P169_DIR / "run_datacheck.sh").write_bytes(dc_sh.replace("\r\n", "\n").encode("utf-8"))

    # 7. submit_M1_C4_TWO_CHECKPOINT_REF.pbs
    pbs_text = f"""#!/bin/bash
#PBS -N M1_C4_TWO_CHECKPOINT_REF
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_c4_two_checkpoint_reference/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_c4_two_checkpoint_reference"
cd "${{RUN_DIR}}"

export JOB_NAME="M1_C4_TWO_CHECKPOINT_REF"
export NOTIFICATION_CONFIG="${{NOTIFICATION_CONFIG:-${{HOME}}/.config/adaptive-remeshing/notifications.env}}"
source "${{RUN_DIR}}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start

if ! type module >/dev/null 2>&1; then source /etc/profile.d/lmod.sh; fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

JOB_NAME="M1_C4_TWO_CHECKPOINT_REF"
INP_NAME="M1_C4_TWO_CHECKPOINT_REF.inp"
USER_SUB="f42_mixed_uel.for"

test ! -e "${{JOB_NAME}}.lck"

echo "Starting Abaqus/Standard 2023 Continuous C4 Two-Checkpoint Reference Simulation..."
echo "Displacement Targets: Ref A uy = 0.001865312544 mm (Step 3), Ref B uy = 0.001870312544 mm (Step 4)"
abaqus job="${{JOB_NAME}}" input="${{INP_NAME}}" user="${{USER_SUB}}" cpus=1 interactive
EXIT_CODE=$?

echo "Abaqus Finished with Exit Code: ${{EXIT_CODE}}"
exit ${{EXIT_CODE}}
"""
    (P169_DIR / "submit_M1_C4_TWO_CHECKPOINT_REF.pbs").write_bytes(pbs_text.replace("\r\n", "\n").encode("utf-8"))

    # 8. Compute file hashes for manifest
    files_map = {}
    for fname in [
        "M1_C4_TWO_CHECKPOINT_REF.inp",
        "f42_mixed_uel.for",
        "job_notifications.sh",
        "submit_M1_C4_TWO_CHECKPOINT_REF.pbs",
        "P169_MECHANICAL_DC.inp",
        "P169_PHASE_DC.inp",
        "run_datacheck.sh",
    ]:
        fpath = P169_DIR / fname
        files_map[fname] = sha256_file(fpath)

    pkg_manifest = {
        "package_number": 169,
        "purpose": (
            "Authentic Mode-I candidate C4 continuous reference simulation (7056 quads, 7265 nodes, f42_mixed_uel.for) "
            "evaluating both Reference A (uy = 0.0018653125442191958 mm) and Reference B (uy = 0.0018703125442191958 mm) "
            "to provide authentic, like-for-like, un-interpolated comparators for C5-R3 and C4-R8 acceptance."
        ),
        "files": files_map
    }
    pkg_manifest_path = P169_DIR / "PACKAGE_MANIFEST.json"
    pkg_manifest_path.write_text(json.dumps(pkg_manifest, indent=2), encoding="utf-8")
    files_map["PACKAGE_MANIFEST.json"] = sha256_file(pkg_manifest_path)

    # 9. Execution manifest
    qsub_cmd = (
        'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 '
        '-RemoteCommand "qsub -q entry_imfdfkmq /scratch9/pr21vyci/runs/mode1_c4_two_checkpoint_reference/submit_M1_C4_TWO_CHECKPOINT_REF.pbs"'
    )
    cmd_sha256 = hashlib.sha256(" ".join(qsub_cmd.strip().split()).encode()).hexdigest()

    exec_manifest = {
        "batch_name": "MODE1_PACKAGE169_C4_TWO_CHECKPOINT_REF",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "hours_valid": 24,
        "automatic_retry": False,
        "remote_run_dir": "/scratch9/pr21vyci/runs/mode1_c4_two_checkpoint_reference",
        "files": files_map,
        "jobs": [
            {
                "id": "M1_C4_TWO_CHECKPOINT_REF",
                "purpose": (
                    "Abaqus 2023 Candidate C4 Two-Checkpoint Continuous Reference Calculation (7056 quads, 7265 nodes, f42_mixed_uel.for) "
                    "evaluating Reference A (uy = 0.0018653125442191958 mm) and Reference B (uy = 0.0018703125442191958 mm) "
                    "to provide authentic, un-interpolated comparators for C5-R3 and C4-R8 physical acceptance."
                ),
                "input": "M1_C4_TWO_CHECKPOINT_REF.inp",
                "datacheck": "M1_C4_TWO_CHECKPOINT_REF_DC.dat",
                "additional_datachecks": [
                    "P169_MECHANICAL_DC.dat",
                    "P169_PHASE_DC.dat"
                ],
                "pbs": "submit_M1_C4_TWO_CHECKPOINT_REF.pbs",
                "queue": "entry_imfdfkmq",
                "cpus": 1,
                "memory_gb": 16,
                "walltime_hours": 8,
                "execution": "single-rank serial",
                "max_submissions": 1,
                "depends_on": [],
                "command": qsub_cmd,
                "command_sha256": cmd_sha256
            }
        ],
        "acceptance": {
            "M1_C4_TWO_CHECKPOINT_REF": (
                "Exit code 0; coupled convergence; Step 1 lands on uy = 0.0018003125442192 mm; "
                "Step 2 reaches Checkpoint 01 at uy = 0.0018603125442191958 mm; "
                "Step 3 terminates at Reference A uy = 0.0018653125442191958 mm (matching C5-R3); "
                "Step 4 terminates at Reference B uy = 0.0018703125442191958 mm (matching C4-R8 and Package 167); "
                "provides authentic reaction force, elastic energy, fracture energy, and total energy for dual-gate resolution."
            )
        }
    }
    exec_manifest_path = P169_DIR / "EXECUTION_MANIFEST_REF.json"
    exec_manifest_path.write_text(json.dumps(exec_manifest, indent=4), encoding="utf-8")
    print(f"Generated execution manifest: {exec_manifest_path.name}")

    return {
        "package_dir": str(P169_DIR),
        "files": files_map,
        "exec_manifest_sha256": sha256_file(exec_manifest_path)
    }


if __name__ == "__main__":
    res = build_package_169()
    print("Package 169 build complete:\n" + json.dumps(res, indent=2))
