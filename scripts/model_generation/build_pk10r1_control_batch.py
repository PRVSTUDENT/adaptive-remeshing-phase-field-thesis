#!/usr/bin/env python3
"""
Model Generator for Mode-II Control Batch:
1. PK10R1_CONTINUOUS_U050 (Continuous solve on PK10R1 from virgin U1=0 to 0.050mm, no restart/transfer/PhaseInit)
2. PK10R1_IDENTITY_RESTART_U050 (Identity restart on PK10R1 from U1=0.030 to 0.050mm with PhaseInit clamp-release)
"""

import os
import sys
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE_R14_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R14"
CONTROL_BATCH_DIR = ROOT / "models/generated/mode_ii/production_control_batch"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def make_validation_script():
    return '''#!/usr/bin/env python3
import sys, json, hashlib
from pathlib import Path

def main():
    pkg_dir = Path(__file__).resolve().parent
    manifest_path = pkg_dir / "PACKAGE_MANIFEST.json"
    if not manifest_path.exists():
        print("FAIL: PACKAGE_MANIFEST.json not found")
        sys.exit(1)
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    all_ok = True
    for rel_path, expected_hash in manifest.get("file_hashes", {}).items():
        file_path = pkg_dir / rel_path
        if not file_path.exists():
            print(f"FAIL: Missing file {rel_path}")
            all_ok = False
            continue
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            print(f"FAIL: Hash mismatch for {rel_path}")
            all_ok = False
    if all_ok:
        print("MANIFEST_VALIDATION_PASS")
        sys.exit(0)
    else:
        print("MANIFEST_VALIDATION_FAIL")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

def make_pbs_script(job_name, mem_gb=16, walltime="24:00:00", cpus=1):
    return f'''#PBS -N {job_name}
#PBS -l select=1:ncpus={cpus}:mem={mem_gb}gb
#PBS -l walltime={walltime}
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -o {job_name}.pbs.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

export XDG_RUNTIME_DIR=${{XDG_RUNTIME_DIR:-/tmp}}
source /etc/profile.d/lmod.sh 2>/dev/null || source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true
module purge 2>/dev/null || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7
set -euo pipefail


cd $PBS_O_WORKDIR

# Source notification system
source ./job_notifications.sh
notification_load_config 2>/dev/null || true
notify_start "{job_name}" "$PBS_JOBID" "entry_imfdfkmq" "{cpus}" "{mem_gb}gb" "{walltime}"
notification_install_terminal_trap "{job_name}" "$PBS_JOBID"

echo "=== PACKAGE INTEGRITY CHECK ==="
python3 validate_package_manifest.py

echo "=== ABAQUS SOLVER EXECUTION ==="
rm -f {job_name}.lck || true
abaqus job={job_name} user=f42_mixed_uel.for input={job_name}.inp double=both interactive cpus={cpus} memory="{mem_gb * 1000} mb"
'''


def make_guarded_wrapper(job_name):
    return f'''#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Guarded Wrapper for {job_name} ==="

if [ -f "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh" ]; then
    source "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"
elif [ -f "./job_notifications.sh" ]; then
    source "./job_notifications.sh"
fi

echo "1. Validating package manifest..."
python3 validate_package_manifest.py

if [[ "${{1:-}}" == "--dry-run" ]]; then
    echo "DRY_RUN_PASS: Package is valid and ready for submission."
    exit 0
elif [[ "${{1:-}}" == "--execute" ]]; then
    echo "2. Submitting PBS job..."
    JOB_ID=$(qsub {job_name}.pbs)
    echo "SUBMITTED: $JOB_ID"
    if type notify_submitted >/dev/null 2>&1; then
        notify_submitted "{job_name}" "$JOB_ID"
    fi
    exit 0
else
    echo "Usage: $0 --dry-run | --execute"
    exit 1
fi
'''

def build_continuous_inp(src_inp_path, out_inp_path, job_name):
    # Read src INP, excluding *INITIAL CONDITIONS section but preserving *EQUATION block before *STEP
    mesh_lines = []
    in_ic = False
    with open(src_inp_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "*INITIAL CONDITIONS" in line:
                in_ic = True
                continue
            if "*EQUATION" in line:
                in_ic = False
            if "*STEP" in line:
                break
            if not in_ic:
                mesh_lines.append(line)

    # Clean heading
    mesh_lines[0] = f"*HEADING\nMode-II Control Candidate: {job_name} (Continuous virgin solve to U1=0.050mm)\n"

    # Add continuous Step definition
    step_lines = [
        "** ==========================================================\n",
        "** STEP: Monotonic Shear Loading to U1 = 0.050000 mm (Continuous Virgin Solve)\n",
        "** ==========================================================\n",
        "*STEP, NAME=ShearStep, INC=20000\n",
        "*STATIC\n",
        "1.0E-5, 0.050000, 1.0E-9, 0.0005\n",
        "*BOUNDARY\n",
        "N_BOTTOM, 1, 2, 0.00\n",
        "99999, 1, 1, 0.050000\n",
        "99999, 2, 2, 0.00\n",
        "*OUTPUT, FIELD, FREQ=1\n",
        "*NODE OUTPUT, NSET=N_TOP\n",
        "U, RF\n",
        "*NODE OUTPUT, NSET=N_BOTTOM\n",
        "U, RF\n",
        "*NODE OUTPUT, NSET=N_RP\n",
        "U, RF\n",
        "*NODE PRINT, FREQ=1\n",
        "U, RF\n",
        "*EL PRINT, FREQ=1, ELSET=E_QUAD_MECH\n",
        "SDV14, SDV15, SDV16\n",
        "*EL PRINT, FREQ=1, ELSET=E_TRI_MECH\n",
        "SDV14, SDV15, SDV16\n",
        "*END STEP\n"
    ]

    out_inp_path.write_text("".join(mesh_lines) + "".join(step_lines), encoding="utf-8")
    print(f"Created continuous INP: {out_inp_path} ({out_inp_path.stat().st_size / 1e6:.2f} MB)")


def build_identity_restart_inp(src_inp_path, out_inp_path, job_name):
    # Identity restart uses exact content from R2R14 INP but with updated heading
    lines = src_inp_path.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
    lines[0] = f"*HEADING\nMode-II Control Candidate: {job_name} (Identity restart from U1=0.030 to 0.050mm on PK10R1)\n"
    out_inp_path.write_text("".join(lines), encoding="utf-8")
    print(f"Created identity restart INP: {out_inp_path} ({out_inp_path.stat().st_size / 1e6:.2f} MB)")

def build_package(job_name, is_continuous):
    pkg_dir = CONTROL_BATCH_DIR / job_name
    pkg_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nBuilding package: {job_name} in {pkg_dir}")

    src_inp = SOURCE_R14_DIR / "M2STATE_FRACFIX_RESTART2R14.inp"
    out_inp = pkg_dir / f"{job_name}.inp"
    
    if is_continuous:
        build_continuous_inp(src_inp, out_inp, job_name)
    else:
        build_identity_restart_inp(src_inp, out_inp, job_name)

    # Copy UEL and append dummy UMAT stub
    src_uel = SOURCE_R14_DIR / "f42_mixed_uel.for"
    uel_code = src_uel.read_text(encoding="utf-8")
    if "SUBROUTINE UMAT" not in uel_code:
        uel_code += """

C ======================================================================
C Dummy UMAT stub to satisfy Abaqus pre-processor linker requirements
C ======================================================================
      SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1 RPL,DDSDDT,DRPLDE,DRPLDT,
     2 STRAN,DSTRAN,TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,CMNAME,
     3 NDI,NSHR,NTENS,NSTATV,PROPS,NPROPS,COORDS,DROT,PNEWDT,
     4 CELENT,DFGRD0,DFGRD1,NOEL,NPT,LAYER,KSPT,KSTEP,KINC)
      INCLUDE 'ABA_PARAM.INC'
      CHARACTER*80 CMNAME
      DIMENSION STRESS(NTENS),STATEV(NSTATV),
     1 DDSDDE(NTENS,NTENS),DDSDDT(NTENS),DRPLDE(NTENS),
     2 STRAN(NTENS),DSTRAN(NTENS),TIME(2),PREDEF(1),DPRED(1),
     3 PROPS(NPROPS),COORDS(3),DROT(3,3),DFGRD0(3,3),DFGRD1(3,3)
      RETURN
      END
"""
    out_uel = pkg_dir / "f42_mixed_uel.for"
    out_uel.write_text(uel_code, encoding="utf-8")

    # Copy job notifications
    src_notif = SOURCE_R14_DIR / "job_notifications.sh"
    out_notif = pkg_dir / "job_notifications.sh"
    notif_content = src_notif.read_text(encoding="utf-8").replace("\r\n", "\n")
    with open(out_notif, "w", encoding="utf-8", newline="\n") as f:
        f.write(notif_content)

    # Create PBS
    pbs_path = pkg_dir / f"{job_name}.pbs"
    pbs_content = make_pbs_script(job_name).replace("\r\n", "\n")
    with open(pbs_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(pbs_content)

    # Create wrapper
    wrapper_path = pkg_dir / f"submit_{job_name.lower()}.sh"
    wrapper_content = make_guarded_wrapper(job_name).replace("\r\n", "\n")
    with open(wrapper_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(wrapper_content)
    os.chmod(wrapper_path, 0o755)

    # Create validator
    val_path = pkg_dir / "validate_package_manifest.py"
    val_content = make_validation_script().replace("\r\n", "\n")
    with open(val_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(val_content)

    # Generate Manifest
    files_to_hash = [
        f"{job_name}.inp",
        "f42_mixed_uel.for",
        f"{job_name}.pbs",
        f"submit_{job_name.lower()}.sh",
        "job_notifications.sh",
        "validate_package_manifest.py"
    ]
    file_hashes = {}
    for fn in sorted(files_to_hash):
        file_hashes[fn] = sha256_file(pkg_dir / fn)

    manifest = {
        "candidate": job_name,
        "mesh": "PK10R1",
        "nphys_elements": 9612,
        "is_continuous": is_continuous,
        "resource_contract": {
            "cpus": 1,
            "memory": "16 GB",
            "walltime": "24:00:00",
            "queue": "entry_imfdfkmq"
        },
        "file_hashes": file_hashes
    }

    manifest_json_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
    manifest_sha = hashlib.sha256(manifest_json_bytes).hexdigest()
    manifest["manifest_sha256"] = manifest_sha

    manifest_path = pkg_dir / "PACKAGE_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(manifest, indent=2) + "\n")
    print(f"Package {job_name} manifest SHA256: {manifest_sha}")

    return {
        "candidate": job_name,
        "manifest_sha256": manifest_sha,
        "pkg_dir": pkg_dir
    }

def main():
    print("================================================================================")
    print("BUILDING MODE-II INDEPENDENT CONTROL BATCH (PK10R1 CONTINUOUS & IDENTITY RESTART)")
    print("================================================================================")

    res1 = build_package("PK10R1_CONTINUOUS_U050", is_continuous=True)
    res2 = build_package("PK10R1_IDENTITY_RESTART_U050", is_continuous=False)

    print("\n--- CONTROL BATCH SUMMARY ---")
    print(f"1. {res1['candidate']}: manifest_sha256 = {res1['manifest_sha256']}")
    print(f"2. {res2['candidate']}: manifest_sha256 = {res2['manifest_sha256']}")

if __name__ == '__main__':
    main()
