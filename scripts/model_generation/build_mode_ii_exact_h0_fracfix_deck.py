#!/usr/bin/env python3
"""Build Exact Repaired Mode-II Verification Batch (Pair 1R).

Generates two independent verification packages:
  1. M2REF_H0_EXACT_FRACFIX_REPRO (accepted 3,930-element H0 benchmark reproduction with repaired UEL)
  2. M2REF_ONEEL_FRACFIX_VERIFY_R2 (1-element analytical/source unit verification with normalized PBS)

Uses the qualified repaired subroutine f42_mixed_uel.for (SHA256: 0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8).
"""

import sys
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
SRC_UEL = ROOT / "models/generated/mode_ii/f42_mixed_element_uel/f42_mixed_uel.for"
SRC_H0_INP = ROOT / "models/generated/mode_ii/h0_endpoint_corrected_serial/ModeII_H0_endpoint_corrected_serial.inp"
OUT_BASE = ROOT / "models/generated/mode_ii/verification_batch"

EXPECTED_UEL_SHA256 = "0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8"

VERIFY_CONFIGS = {
    "M2REF_ONEEL_FRACFIX_VERIFY_R2": {
        "memory": "8GB",
        "walltime": "00:15:00",
        "queue": "entry_imfdfkmq",
        "kind": "oneel",
    },
    "M2REF_H0_EXACT_FRACFIX_REPRO": {
        "memory": "8GB",
        "walltime": "01:00:00",
        "queue": "entry_imfdfkmq",
        "kind": "exact_h0",
    },
}

L0 = 0.015
GC = 0.0027
EMOD = 210.0
ENU = 0.3
PARK = 1.0e-7
THCK = 1.0
DEPVAR = 18
PASSIVE_E = 1.0e-11


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def generate_oneel_inp(pkg_dir: Path) -> str:
    out_file = pkg_dir / "M2REF_ONEEL_FRACFIX_VERIFY_R2.inp"
    lines = [
        "*Heading",
        "** Mode-II Phase-Field Verification Study: M2REF_ONEEL_FRACFIX_VERIFY_R2",
        "** 3-Layer Mixed UEL Architecture: U1/U2/CPE4 (4 physical nodes, 1 quad)",
        "*Preprint, echo=NO, model=NO, history=NO, contact=NO",
        "*Node",
        "       1,   -0.5000000000,   -0.5000000000",
        "       2,    0.5000000000,   -0.5000000000",
        "       3,    0.5000000000,    0.5000000000",
        "       4,   -0.5000000000,    0.5000000000",
        "       5,    0.0000000000,    0.6000000000",
        "*Nset, nset=bottom_nodes",
        " 1, 2",
        "*Nset, nset=top_nodes",
        " 3, 4",
        "*Nset, nset=RP",
        " 5",
        "*User Element, type=U1, nodes=4, coordinates=2, properties=3, variables=8",
        " 8,",
        "*User Element, type=U2, nodes=4, coordinates=2, properties=5, variables=56",
        " 1, 2",
        "*Element, type=U1, elset=PHASE_QUAD",
        "       1,       1,       2,       3,       4",
        "*Element, type=U2, elset=DISP_QUAD",
        "       5,       1,       2,       3,       4",
        "*Element, type=CPE4, elset=UMAT_QUAD",
        "       9,       1,       2,       3,       4",
        "*Elset, elset=PHASE",
        " PHASE_QUAD",
        "*Elset, elset=DISP",
        " DISP_QUAD",
        "*Elset, elset=UMATELEM",
        " UMAT_QUAD",
        "*UEL Property, elset=PHASE_QUAD",
        " 1.500000e-02, 2.700000e-03, 1.000000e+00",
        "*UEL Property, elset=DISP_QUAD",
        " 2.100000e+02, 3.000000e-01, 1.000000e+00, 1.000000e-07, 4.0",
        "*Solid Section, elset=UMAT_QUAD, material=MAT_QUAD_FACSIMILE",
        " 1.000000,",
        "*Material, name=MAT_QUAD_FACSIMILE",
        "*Depvar",
        " 18",
        "*User Material, constants=4",
        " 1.000000e-11, 3.000000e-01, 4.0, 4.0",
        "*Equation",
        " 2",
        " 3, 1, 1.0, 5, 1, -1.0",
        "*Equation",
        " 2",
        " 4, 1, 1.0, 5, 1, -1.0",
        "*Boundary",
        " bottom_nodes, 1, 2",
        "*Boundary",
        " top_nodes, 2, 2",
        "*Amplitude, name=Amp-1",
        " 0.0, 0.0, 0.5, 0.005",
        "*Amplitude, name=Amp-2",
        " 0.0, 0.005, 0.2, 0.010",
        "*Step, name=Step-1, nlgeom=NO, inc=500",
        "*Static, direct",
        " 0.001, 0.5,",
        "*Boundary, amplitude=Amp-1",
        " RP, 1, 1, 1.0",
        "*Restart, write, frequency=0",
        "*Output, field, time interval=0.01",
        "*Node Output",
        " U, RF",
        "*Node Output, nset=RP",
        " RF, U",
        "*Element Output, elset=UMATELEM",
        " SDV, S, EVOL",
        "*Output, history, variable=PRESELECT",
        "*Energy Output",
        " ALLAE, ALLCD, ALLIE, ALLKE, ALLPD, ALLSE, ALLWK, ETOTAL",
        "*End Step",
        "*Step, name=Step-2, nlgeom=NO, inc=2000",
        "*Static, direct",
        " 0.0001, 0.2,",
        "*Boundary, amplitude=Amp-2",
        " RP, 1, 1, 1.0",
        "*Restart, write, frequency=0",
        "*Output, field, time interval=0.01",
        "*Node Output",
        " U, RF",
        "*Node Output, nset=RP",
        " RF, U",
        "*Element Output, elset=UMATELEM",
        " SDV, S, EVOL",
        "*Output, history, variable=PRESELECT",
        "*Energy Output",
        " ALLAE, ALLCD, ALLIE, ALLKE, ALLPD, ALLSE, ALLWK, ETOTAL",
        "*End Step",
    ]
    out_file.parent.mkdir(parents=True, exist_ok=True)
    deck_text = "\n".join(lines) + "\n"
    out_file.write_bytes(deck_text.encode("utf-8"))
    return sha256_file(out_file)


def generate_exact_h0_inp(pkg_dir: Path) -> str:
    out_file = pkg_dir / "M2REF_H0_EXACT_FRACFIX_REPRO.inp"
    src_text = SRC_H0_INP.read_text(encoding="utf-8")

    # In source deck ModeII_H0_endpoint_corrected_serial.inp:
    # We replace UEL definitions and property lines with repaired UEL definitions.
    # The source deck already has:
    # 3930 physical elements, 3998 physical nodes, split notch topology, RP node 3999, top/bottom equations, BCs, Step 1 & Step 2.
    # We enforce exact UEL Property values matching f42_mixed_uel.for!

    lines = []
    for line in src_text.splitlines():
        line_s = line.strip()
        if line_s.startswith("*Heading"):
            lines.append("*Heading")
            lines.append("** Mode-II Phase-Field Exact Accepted H0 Benchmark: M2REF_H0_EXACT_FRACFIX_REPRO")
            lines.append("** 3-Layer Mixed UEL Architecture: U1/U2/CPE4 (3,930 physical elements, 3,998 nodes)")
        elif line_s.startswith("*User Element, type=U2"):
            lines.append("*User Element, type=U2, nodes=4, coordinates=2, properties=5, variables=56")
        elif line_s.startswith("*UEL Property, elset=DISP_QUAD"):
            lines.append("*UEL Property, elset=DISP_QUAD")
            lines.append(f" {EMOD:.6e}, {ENU:.6e}, {THCK:.6e}, {PARK:.6e}, 3998.0")
        elif line_s.startswith("*User Material, constants=4"):
            lines.append("*User Material, constants=4")
            lines.append(f" {PASSIVE_E:.6e}, {ENU:.6e}, 3998.0, 4.0")
        elif line_s.startswith(" 2.100000e+05, 3.000000e-01, 1.000000e+00, 1.000000e-07, 3998.0"):
            # skip old line if replaced
            continue
        elif line_s.startswith(" 1.000000e-11, 3.000000e-01, 3998.0, 4.0"):
            # skip old line if replaced
            continue
        else:
            lines.append(line)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    deck_text = "\n".join(lines) + "\n"
    out_file.write_bytes(deck_text.encode("utf-8"))
    return sha256_file(out_file)


def generate_pbs_script(case_name: str, pkg_dir: Path, cfg: dict) -> str:
    pbs_file = pkg_dir / f"{case_name}.pbs"
    content = f"""#!/bin/bash
#PBS -N {case_name}
#PBS -l select=1:ncpus=1:mem={cfg['memory']}
#PBS -l walltime={cfg['walltime']}
#PBS -q {cfg['queue']}
#PBS -m abe
#PBS -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de
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

echo "=== Running Abaqus Job {case_name} ==="
abaqus job={case_name} input={case_name}.inp user=f42_mixed_uel.for cpus=1 interactive double=both ask_delete=OFF

echo "=== Execution Complete ==="
date
"""
    content_lf = content.replace("\r\n", "\n")
    pbs_file.write_bytes(content_lf.encode("utf-8"))
    return sha256_file(pbs_file)


def generate_submit_wrapper(case_name: str, pkg_dir: Path) -> str:
    sh_file = pkg_dir / f"submit_{case_name.lower()}.sh"
    content = f"""#!/bin/bash
set -euo pipefail

# Guarded submission wrapper for {case_name}
# Protocol version: 1
# Requires explicit prior human chat authorization.

AUTH_FILE="../VERIFICATION_BATCH_SUBMISSION_RECORD.json"

if [ ! -f "$AUTH_FILE" ]; then
    echo "ERROR: Authorization record $AUTH_FILE missing. Direct submission prohibited." >&2
    exit 1
fi

echo "Submitting {case_name} to PBS..."
qsub {case_name}.pbs
"""
    content_lf = content.replace("\r\n", "\n")
    sh_file.write_bytes(content_lf.encode("utf-8"))
    return sha256_file(sh_file)


def main():
    print("=== Building Exact Repaired Mode-II Verification Packages (Pair 1R) ===")

    uel_sha = sha256_file(SRC_UEL)
    assert uel_sha == EXPECTED_UEL_SHA256, f"Expected {EXPECTED_UEL_SHA256}, got {uel_sha}"
    print(f"Source UEL: {SRC_UEL}")
    print(f"Source UEL SHA256: {uel_sha}")

    uel_bytes = SRC_UEL.read_bytes()

    batch_manifest = {
        "study_name": "Exact Repaired Mode-II Verification Batch (Pair 1R)",
        "task_id": "F43MODEREF-H0IDENTITY-FIX1",
        "uel_source_sha256": uel_sha,
        "cases": {},
    }

    for case_name, cfg in VERIFY_CONFIGS.items():
        pkg_dir = OUT_BASE / case_name
        pkg_dir.mkdir(parents=True, exist_ok=True)

        dest_uel = pkg_dir / "f42_mixed_uel.for"
        dest_uel.write_bytes(uel_bytes)
        assert sha256_file(dest_uel) == uel_sha

        if cfg["kind"] == "oneel":
            inp_sha = generate_oneel_inp(pkg_dir)
        else:
            inp_sha = generate_exact_h0_inp(pkg_dir)

        pbs_sha = generate_pbs_script(case_name, pkg_dir, cfg)
        sh_sha = generate_submit_wrapper(case_name, pkg_dir)

        pkg_manifest = {
            "case_name": case_name,
            "inp_sha256": inp_sha,
            "uel_sha256": uel_sha,
            "pbs_sha256": pbs_sha,
            "submit_sh_sha256": sh_sha,
            "memory": cfg["memory"],
            "walltime": cfg["walltime"],
            "queue": cfg["queue"],
        }
        with open(pkg_dir / "PACKAGE_MANIFEST.json", "w") as f:
            json.dump(pkg_manifest, f, indent=2)

        batch_manifest["cases"][case_name] = pkg_manifest
        print(f"Generated {case_name}: INP={inp_sha[:10]}, UEL={uel_sha[:10]}, PBS={pbs_sha[:10]}")

    manifest_path = OUT_BASE / "VERIFICATION_BATCH_MANIFEST.json"
    with open(manifest_path, "w") as f:
        json.dump(batch_manifest, f, indent=2)

    print(f"\nWrote verification batch manifest to {manifest_path}")


if __name__ == "__main__":
    main()
