#!/usr/bin/env python3
"""
Generator for Mode-II Uniform Full References Batch (H1 and H2 extended to U1=0.050mm)
Candidates:
1. M2REF_H1_FULL_U050 (1 CPU / 8 GB / 12:00:00 / entry_imfdfkmq)
2. M2REF_H2_FULL_U050 (1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq)
"""

import sys
import os
import re
import json
import hashlib
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

SRC_H1_INP = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H1_FRACFIX/M2REF_H1_FRACFIX.inp"
SRC_H2_INP = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX/M2REF_H2_FRACFIX.inp"
AUTH_FOR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R14/f42_mixed_uel.for"
NOTIF_SH = ROOT / "scripts/hpc/notifications/job_notifications.sh"

DEST_BASE = ROOT / "models/generated/mode_ii/production_verification_batch"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def write_lf_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)

def transform_inp_deck(src_inp_path, job_name, nphys, u1_target=0.050000):
    print(f"Transforming INP deck from {src_inp_path.name} -> {job_name}.inp...")
    lines = src_inp_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    
    out_lines = []
    out_lines.append("*Heading")
    out_lines.append(f"** Mode-II Phase-Field Uniform Reference Study: {job_name}")
    out_lines.append(f"** Lineage: Staggered Phase-Mechanical Mixed UEL ({nphys} physical elements)")
    out_lines.append(f"** Formulation: l0=0.015 mm, Gc=0.0027 kN/mm, E=210.0 kN/mm^2, nu=0.3, k=1e-07, NPHYS={nphys}")
    out_lines.append(f"** Monotonic Shear Loading to U1 = {u1_target:.6f} mm")
    out_lines.append("*Preprint, echo=NO, model=NO, history=NO, contact=NO")
    out_lines.append("** ==========================================================")
    out_lines.append("** USER ELEMENTS (Clean 6-slot ABI: Layer 1 Phase U1, Layer 2 Mech U2)")
    out_lines.append("** ==========================================================")
    out_lines.append("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
    out_lines.append("3")
    out_lines.append("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
    out_lines.append("1, 2")
    out_lines.append("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
    out_lines.append("3")
    out_lines.append("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM")
    out_lines.append("1, 2")

    i = 0
    while i < len(lines):
        l = lines[i]
        l_upper = l.upper().strip()
        
        if l_upper.startswith("*HEADING") or l_upper.startswith("*PREPRINT"):
            i += 1
            continue
            
        if l_upper.startswith("*USER ELEMENT"):
            # Skip old user element card and its DOF lines
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("*"):
                i += 1
            continue

        if l_upper.startswith("*UEL PROPERTY"):
            out_lines.append("** ==========================================================")
            out_lines.append("** UEL PROPERTIES (Clean 6-slot ABI)")
            out_lines.append("** ==========================================================")
            out_lines.append("*UEL Property, elset=PHASE_QUAD")
            out_lines.append(f" 0.015, 0.0027, 210.0, 0.3, 1.0e-7, {nphys}.0")
            out_lines.append("*UEL Property, elset=DISP_QUAD")
            out_lines.append(f" 0.015, 0.0027, 210.0, 0.3, 1.0e-7, {nphys}.0")
            # Skip old property lines
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("*"):
                i += 1
            continue

        if l_upper.startswith("*STEP"):
            # We reached step definitions, skip all original steps
            break
            
        if l_upper.startswith("*AMPLITUDE"):
            # Skip amplitude
            while i < len(lines) and not lines[i].upper().strip().startswith("*STEP"):
                i += 1
            break
            
        out_lines.append(l)
        i += 1

    # Now append the single unified monotonic step
    out_lines.append("** ==========================================================")
    out_lines.append(f"** STEP: Monotonic Shear Loading to U1 = {u1_target:.6f} mm")
    out_lines.append("** ==========================================================")
    out_lines.append("*Step, name=ShearStep, nlgeom=NO, inc=20000")
    out_lines.append("*Static")
    out_lines.append(" 1.0E-5, 0.050000, 1.0E-9, 0.0005")
    out_lines.append("*Boundary")
    out_lines.append(f" RP, 1, 1, {u1_target:.6f}")
    out_lines.append(" RP, 2, 2, 0.0")
    out_lines.append("*Restart, write, frequency=0")
    out_lines.append("*Output, field, frequency=1")
    out_lines.append("*Node Output")
    out_lines.append(" U, RF")
    out_lines.append("*Node Output, nset=RP")
    out_lines.append(" U, RF")
    out_lines.append("*Element Output, elset=DISP_QUAD")
    out_lines.append(" SDV")
    out_lines.append("*Node Print, freq=1, nset=RP")
    out_lines.append(" U1, U2, RF1, RF2")
    out_lines.append("*Node Print, freq=1, nset=bottom_nodes")
    out_lines.append(" RF1, RF2")
    out_lines.append("*El Print, freq=1, elset=DISP_QUAD")
    out_lines.append(" SDV13, SDV14, SDV15, SDV16")
    out_lines.append("*End Step")

    return "\n".join(out_lines) + "\n"

def build_package(job_name, src_inp, nphys, cpus, mem_gb, walltime, queue):
    pkg_dir = DEST_BASE / job_name
    pkg_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nBuilding package {job_name} in {pkg_dir}...")

    # 1. INP
    inp_content = transform_inp_deck(src_inp, job_name, nphys, u1_target=0.050000)
    write_lf_file(pkg_dir / f"{job_name}.inp", inp_content)

    # 2. Fortran UEL with dummy UMAT stub
    for_content = AUTH_FOR.read_text(encoding="utf-8")
    if "SUBROUTINE UMAT" not in for_content:
        for_content += """
! ==============================================================================
! Dummy UMAT stub for passive visualizer elements if present
! ==============================================================================
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
    write_lf_file(pkg_dir / "f42_mixed_uel.for", for_content)

    # 3. Notification script
    shutil.copy2(NOTIF_SH, pkg_dir / "job_notifications.sh")

    # 4. PBS Script
    pbs_content = f"""#PBS -N {job_name}
#PBS -l select=1:ncpus={cpus}:mem={mem_gb}gb
#PBS -l walltime={walltime}
#PBS -q {queue}
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -j oe
#PBS -o {job_name}.pbs.log

cd $PBS_O_WORKDIR

# Source dual-channel notifications
if [ -f "./job_notifications.sh" ]; then
    source ./job_notifications.sh
    notification_load_config
    notify_start "{job_name}" "{job_name}" "$PBS_JOBID"
    notification_install_terminal_trap "{job_name}" "$PBS_JOBID"
fi

echo "=== PACKAGE INTEGRITY CHECK ==="
python3 validate_package_manifest.py
if [ $? -ne 0 ]; then
    echo "ERROR: Package manifest validation failed!"
    exit 1
fi

echo "=== ABAQUS SOLVER EXECUTION ==="
module load intel/2024.2.0 gcc/11.4.0 abaqus/2023 || true
unset SLURM_GTIDS
export OMP_NUM_THREADS={cpus}

abaqus job={job_name} input={job_name}.inp user=f42_mixed_uel.for cpus={cpus} interactive
SOLVER_EXIT=$?
echo "Abaqus solver finished with exit code: $SOLVER_EXIT"
exit $SOLVER_EXIT
"""
    write_lf_file(pkg_dir / f"{job_name}.pbs", pbs_content)

    # 5. Guarded wrapper
    wrapper_content = f"""#!/bin/bash
set -euo pipefail

JOB_NAME="{job_name}"
PBS_SCRIPT="{job_name}.pbs"

echo "=== GUARDED SUBMISSION WRAPPER: $JOB_NAME ==="

# Validate manifest
python3 validate_package_manifest.py

if [ "${{1:-}}" != "--execute" ]; then
    echo "DRY-RUN MODE: Validation passed. To submit, pass --execute"
    exit 0
fi

echo "EXECUTING GUARDED SUBMISSION..."
SUBMIT_OUTPUT=$(qsub "$PBS_SCRIPT")
echo "SUBMITTED JOB: $SUBMIT_OUTPUT"

# Telegram notification
if [ -f "./job_notifications.sh" ]; then
    source ./job_notifications.sh
    notification_load_config || true
    notify_submitted "$JOB_NAME" "$JOB_NAME" "$SUBMIT_OUTPUT" || true
fi
"""
    write_lf_file(pkg_dir / f"submit_{job_name.lower()}.sh", wrapper_content)
    os.chmod(pkg_dir / f"submit_{job_name.lower()}.sh", 0o755)

    # 6. Manifest validator
    val_py_content = """import sys
import json
import hashlib
from pathlib import Path

def validate():
    manifest_path = Path("PACKAGE_MANIFEST.json")
    if not manifest_path.exists():
        print("ERROR: PACKAGE_MANIFEST.json not found!")
        sys.exit(1)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failed = False
    for fn, exp_sha in manifest.get("files", {}).items():
        fp = Path(fn)
        if not fp.exists():
            print(f"ERROR: missing file {fn}")
            failed = True
            continue
        actual = hashlib.sha256(fp.read_bytes()).hexdigest()
        if actual != exp_sha:
            print(f"ERROR: SHA256 mismatch for {fn}: expected {exp_sha}, got {actual}")
            failed = True
    if failed:
        sys.exit(1)
    print("ALL FILES MATCH MANIFEST SHA256: PASS")

if __name__ == '__main__':
    validate()
"""
    write_lf_file(pkg_dir / "validate_package_manifest.py", val_py_content)

    # 7. Package manifest JSON
    manifest_files = {}
    for fn in [
        f"{job_name}.inp",
        "f42_mixed_uel.for",
        f"{job_name}.pbs",
        f"submit_{job_name.lower()}.sh",
        "job_notifications.sh",
        "validate_package_manifest.py"
    ]:
        manifest_files[fn] = sha256_file(pkg_dir / fn)

    manifest_data = {
        "package_name": job_name,
        "nphys": nphys,
        "cpus": cpus,
        "memory_gb": mem_gb,
        "walltime": walltime,
        "queue": queue,
        "automatic_retry": False,
        "files": manifest_files
    }
    write_lf_file(pkg_dir / "PACKAGE_MANIFEST.json", json.dumps(manifest_data, indent=2))
    
    pkg_sha = sha256_file(pkg_dir / "PACKAGE_MANIFEST.json")
    print(f"Package {job_name} built successfully! Manifest SHA256: {pkg_sha}")
    return pkg_sha

def main():
    print("================================================================================")
    print("BUILDING UNIFORM FULL REFERENCES BATCH (H1 and H2 to U1=0.050mm)")
    print("================================================================================")
    sha_h1 = build_package("M2REF_H1_FULL_U050", SRC_H1_INP, nphys=12064, cpus=1, mem_gb=8, walltime="12:00:00", queue="entry_imfdfkmq")
    sha_h2 = build_package("M2REF_H2_FULL_U050", SRC_H2_INP, nphys=33852, cpus=1, mem_gb=16, walltime="24:00:00", queue="entry_imfdfkmq")
    print("\nSummary of Generated Packages:")
    print(f"  M2REF_H1_FULL_U050 Manifest SHA256: {sha_h1}")
    print(f"  M2REF_H2_FULL_U050 Manifest SHA256: {sha_h2}")

if __name__ == '__main__':
    main()
