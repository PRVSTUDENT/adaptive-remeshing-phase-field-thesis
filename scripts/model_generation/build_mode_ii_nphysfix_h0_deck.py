#!/usr/bin/env python3
"""Build Corrected Mode-II H0 Verification Package (M2REF_H0_NPHYSFIX_REPRO).

Generates M2REF_H0_NPHYSFIX_REPRO input deck with corrected NPHYS property contract
(NPHYS = 3930.0 for 3,930 physical quad elements).

Uses qualified repaired subroutine f42_mixed_uel.for (SHA256: 0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8).
"""

import sys
import os
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_UEL = ROOT / "models/generated/mode_ii/f42_mixed_element_uel/f42_mixed_uel.for"
SRC_H0_INP = ROOT / "models/generated/mode_ii/h0_endpoint_corrected_serial/ModeII_H0_endpoint_corrected_serial.inp"
OUT_BASE = ROOT / "models/generated/mode_ii/verification_batch"

EXPECTED_UEL_SHA256 = "0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8"

L0 = 0.015
GC = 0.0027
EMOD = 210.0
ENU = 0.3
PARK = 1.0e-7
THCK = 1.0
DEPVAR = 18
PASSIVE_E = 1.0e-11
NPHYS_H0 = 3930


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def generate_nphysfix_h0_inp(pkg_dir: Path) -> str:
    out_file = pkg_dir / "M2REF_H0_NPHYSFIX_REPRO.inp"
    src_text = SRC_H0_INP.read_text(encoding="utf-8")

    lines = []
    for line in src_text.splitlines():
        line_s = line.strip()
        if line_s.startswith("*Heading"):
            lines.append("*Heading")
            lines.append("** Mode-II Phase-Field Corrected H0 Benchmark: M2REF_H0_NPHYSFIX_REPRO")
            lines.append("** 3-Layer Mixed UEL Architecture: U1/U2/CPE4 (3,930 physical elements, 3,998 nodes)")
            lines.append("** NPHYS Contract: NPHYS = 3930.0 under U2 UEL property and UMAT material constants")
        elif line_s.lower().startswith("*user element") and "type=u2" in line_s.lower():
            lines.append("*User element, nodes=4, type=U2, properties=5, coordinates=2, VARIABLES=56")
            lines.append("1,2")
        elif line_s.lower().startswith("*user element") and "type=u1" in line_s.lower():
            lines.append("*User element, nodes=4, type=U1, properties=3, coordinates=2, VARIABLES=8")
            lines.append("3")
        elif line_s.lower().startswith("*uel property") and ("plate_ss" in line_s.lower() or "disp" in line_s.lower()):
            lines.append(line)
            lines.append(f" {EMOD:.6e}, {ENU:.6e}, {THCK:.6e}, {PARK:.6e}, {NPHYS_H0:.1f}")
        elif line_s.lower().startswith("*uel property") and ("plate" in line_s.lower() or "phase" in line_s.lower()) and "plate_ss" not in line_s.lower():
            lines.append(line)
            lines.append(f" {L0:.6e}, {GC:.6e}, {THCK:.6e}")
        elif line_s.lower().startswith("*user material") and "constants=" in line_s.lower():
            lines.append("*User Material, constants=4")
            lines.append(f" {PASSIVE_E:.6e}, {ENU:.6e}, {NPHYS_H0:.1f}, 4.0")
        elif "2.100000e+05" in line_s or "210.0" in line_s or "1.000000e-11" in line_s:
            # Skip old property value lines from source deck
            continue
        elif "1.500000e-02, 2.700000e-03" in line_s or "0.015, 0.0027" in line_s:
            continue
        else:
            lines.append(line)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    deck_text = "\n".join(lines) + "\n"
    out_file.write_bytes(deck_text.encode("utf-8"))
    return sha256_file(out_file)


def generate_pbs_script(case_name: str, pkg_dir: Path, memory="8GB", walltime="01:00:00", queue="entry_imfdfkmq") -> str:
    pbs_file = pkg_dir / f"{case_name}.pbs"
    content = f"""#!/bin/bash
#PBS -N {case_name}
#PBS -l select=1:ncpus=1:mem={memory}
#PBS -l walltime={walltime}
#PBS -q {queue}
#PBS -j oe
#PBS -o evidence/$PBS_JOBID/execution.log

set -euo pipefail

cd "$PBS_O_WORKDIR"
mkdir -p evidence/"$PBS_JOBID"

echo "=== Host Environment ==="
hostname
date
module list || true

module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

echo "=== Pre-execution Hashes ==="
sha256sum {case_name}.inp
sha256sum f42_mixed_uel.for

echo "=== Running Abaqus Standard ==="
abaqus job={case_name} user=f42_mixed_uel.for interactive

echo "=== Execution Complete ==="
date
"""
    pbs_file.parent.mkdir(parents=True, exist_ok=True)
    pbs_file.write_bytes(content.encode("utf-8"))
    return sha256_file(pbs_file)


def generate_submit_wrapper(case_name: str, pkg_dir: Path) -> str:
    sh_file = pkg_dir / f"submit_{case_name.lower()}.sh"
    content = f"""#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

JOB_ID=$(qsub {case_name}.pbs)
echo "Submitted {case_name} under Job ID: $JOB_ID"
"""
    sh_file.parent.mkdir(parents=True, exist_ok=True)
    sh_file.write_bytes(content.encode("utf-8"))
    return sha256_file(sh_file)


def build_package(case_name: str) -> dict:
    pkg_dir = OUT_BASE / case_name
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # Copy UEL source
    uel_target = pkg_dir / "f42_mixed_uel.for"
    uel_target.write_bytes(SRC_UEL.read_bytes())
    uel_sha = sha256_file(uel_target)
    assert uel_sha == EXPECTED_UEL_SHA256, f"UEL SHA mismatch: {uel_sha} != {EXPECTED_UEL_SHA256}"

    inp_sha = generate_nphysfix_h0_inp(pkg_dir)
    pbs_sha = generate_pbs_script(case_name, pkg_dir)
    wrapper_sha = generate_submit_wrapper(case_name, pkg_dir)

    manifest = {
        "case_name": case_name,
        "n_phys": NPHYS_H0,
        "inp_sha256": inp_sha,
        "uel_sha256": uel_sha,
        "pbs_sha256": pbs_sha,
        "wrapper_sha256": wrapper_sha,
    }
    manifest_file = pkg_dir / f"{case_name}_MANIFEST.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest_sha = sha256_file(manifest_file)
    manifest["manifest_sha256"] = manifest_sha

    return manifest


if __name__ == "__main__":
    res = build_package("M2REF_H0_NPHYSFIX_REPRO")
    print("=== Built M2REF_H0_NPHYSFIX_REPRO ===")
    print(json.dumps(res, indent=2))
