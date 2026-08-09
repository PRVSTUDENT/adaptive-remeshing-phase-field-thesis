#!/usr/bin/env python3
"""Build Repaired Mode-II Verification Batch (Pair 1).

Generates two independent verification packages:
  1. M2REF_ONEEL_FRACFIX_VERIFY (1-element analytical/source unit verification)
  2. M2REF_H0_FRACFIX_REPRO (accepted H0 benchmark mesh reproduction)

Uses the qualified repaired subroutine f42_mixed_uel.for (SHA256: 0bc43781...).
"""

import sys
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
SRC_UEL = ROOT / "models/generated/mode_ii/f42_mixed_element_uel/f42_mixed_uel.for"
OUT_BASE = ROOT / "models/generated/mode_ii/verification_batch"

EXPECTED_UEL_SHA256 = "0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8"

VERIFY_CONFIGS = {
    "M2REF_ONEEL_FRACFIX_VERIFY": {
        "memory": "8GB",
        "walltime": "00:15:00",
        "queue": "entry_imfdfkmq",
        "n_div_x": 1,
        "n_div_y": 1,
    },
    "M2REF_H0_FRACFIX_REPRO": {
        "memory": "8GB",
        "walltime": "01:00:00",
        "queue": "entry_imfdfkmq",
        "n_div_x": 50,
        "n_div_y": 50,
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


def generate_structured_mesh(n_div_x: int, n_div_y: int) -> Tuple[Dict[int, Tuple[float, float]], Dict[int, List[int]]]:
    x_min, x_max = -0.50, 0.50
    y_min, y_max = -0.50, 0.50

    dx = (x_max - x_min) / float(n_div_x)
    dy = (y_max - y_min) / float(n_div_y)

    nodes = {}
    node_id_grid = {}
    nid = 1

    for j in range(n_div_y + 1):
        y = y_min + j * dy
        for i in range(n_div_x + 1):
            x = x_min + i * dx
            nodes[nid] = (round(x, 10), round(y, 10))
            node_id_grid[(i, j)] = nid
            nid += 1

    quads = {}
    eid = 1
    for j in range(n_div_y):
        for i in range(n_div_x):
            n1 = node_id_grid[(i, j)]
            n2 = node_id_grid[(i + 1, j)]
            n3 = node_id_grid[(i + 1, j + 1)]
            n4 = node_id_grid[(i, j + 1)]
            quads[eid] = [n1, n2, n3, n4]
            eid += 1

    return nodes, quads


def generate_inp_deck(case_name: str, pkg_dir: Path, n_div_x: int, n_div_y: int) -> str:
    out_file = pkg_dir / f"{case_name}.inp"
    nodes, quads = generate_structured_mesh(n_div_x, n_div_y)

    n_phys = len(nodes)
    n_quad_elems = len(quads)

    rp_node_id = n_phys + 1

    tol = 1.0e-5
    y_min, y_max = -0.50, 0.50
    bottom_nodes = sorted([nid for nid, (x, y) in nodes.items() if abs(y - y_min) < tol])
    top_nodes = sorted([nid for nid, (x, y) in nodes.items() if abs(y - y_max) < tol])

    lines = []
    lines.append("*Heading")
    lines.append(f"** Mode-II Phase-Field Verification Study: {case_name}")
    lines.append(f"** 3-Layer Mixed UEL Architecture: U1/U2/CPE4 ({n_phys} physical nodes, {n_quad_elems} quads)")
    lines.append("*Preprint, echo=NO, model=NO, history=NO, contact=NO")

    # Nodes
    lines.append("*Node")
    for nid in sorted(nodes.keys()):
        x, y = nodes[nid]
        lines.append(f" {nid:7d}, {x:16.10f}, {y:16.10f}")
    lines.append(f" {rp_node_id:7d},     0.0000000000,     0.6000000000")

    # Node sets
    lines.append("*Nset, nset=bottom_nodes")
    for i in range(0, len(bottom_nodes), 10):
        chunk = bottom_nodes[i:i+10]
        lines.append(" " + ", ".join(f"{n:d}" for n in chunk))

    lines.append("*Nset, nset=top_nodes")
    for i in range(0, len(top_nodes), 10):
        chunk = top_nodes[i:i+10]
        lines.append(" " + ", ".join(f"{n:d}" for n in chunk))

    lines.append("*Nset, nset=RP")
    lines.append(f" {rp_node_id:d}")

    # UEL User Elements definition (Corrected variable counts: 8 for U1, 56 for U2)
    lines.append("*User Element, type=U1, nodes=4, coordinates=2, properties=3, variables=8")
    lines.append(" 8,")
    lines.append("*User Element, type=U2, nodes=4, coordinates=2, properties=5, variables=56")
    lines.append(" 1, 2")

    # Layer 1: Phase UEL
    lines.append("*Element, type=U1, elset=PHASE_QUAD")
    for eid in sorted(quads.keys()):
        conn = ", ".join(f"{n:7d}" for n in quads[eid])
        lines.append(f" {eid:7d}, {conn}")

    # Layer 2: Displacement UEL
    lines.append("*Element, type=U2, elset=DISP_QUAD")
    for eid in sorted(quads.keys()):
        disp_id = n_phys + eid
        conn = ", ".join(f"{n:7d}" for n in quads[eid])
        lines.append(f" {disp_id:7d}, {conn}")

    # Layer 3: Passive Facsimile Elements (CPE4)
    lines.append("*Element, type=CPE4, elset=UMAT_QUAD")
    for eid in sorted(quads.keys()):
        fac_id = 2 * n_phys + eid
        conn = ", ".join(f"{n:7d}" for n in quads[eid])
        lines.append(f" {fac_id:7d}, {conn}")

    # Aggregate sets
    lines.append("*Elset, elset=PHASE")
    lines.append(" PHASE_QUAD")
    lines.append("*Elset, elset=DISP")
    lines.append(" DISP_QUAD")
    lines.append("*Elset, elset=UMATELEM")
    lines.append(" UMAT_QUAD")

    # UEL Properties
    lines.append("*UEL Property, elset=PHASE_QUAD")
    lines.append(f" {L0:.6e}, {GC:.6e}, {THCK:.6e}")
    lines.append("*UEL Property, elset=DISP_QUAD")
    lines.append(f" {EMOD:.6e}, {ENU:.6e}, {THCK:.6e}, {PARK:.6e}, {n_phys}.0")

    # Solid Section for Facsimile
    lines.append("*Solid Section, elset=UMAT_QUAD, material=MAT_QUAD_FACSIMILE")
    lines.append(f" {THCK:.6f},")
    lines.append("*Material, name=MAT_QUAD_FACSIMILE")
    lines.append("*Depvar")
    lines.append(f" {DEPVAR}")
    lines.append("*User Material, constants=4")
    lines.append(f" {PASSIVE_E:.6e}, {ENU:.6e}, {n_phys}.0, 4.0")

    # Linear Equations for Top Node Shear Coupling to RP
    for nid in top_nodes:
        lines.append("*Equation")
        lines.append(" 2")
        lines.append(f" {nid:d}, 1, 1.0, {rp_node_id:d}, 1, -1.0")

    # Initial Boundary Conditions
    lines.append("*Boundary")
    lines.append(" bottom_nodes, 1, 2")
    lines.append("*Boundary")
    lines.append(" top_nodes, 2, 2")

    # Amplitudes
    lines.append("*Amplitude, name=Amp-1")
    lines.append(" 0.0, 0.0, 0.5, 0.005")
    lines.append("*Amplitude, name=Amp-2")
    lines.append(" 0.0, 0.005, 0.2, 0.010")

    # STEP 1
    lines.append("*Step, name=Step-1, nlgeom=NO, inc=500")
    lines.append("*Static, direct")
    lines.append(" 0.001, 0.5,")
    lines.append("*Boundary, amplitude=Amp-1")
    lines.append(" RP, 1, 1, 1.0")
    lines.append("*Restart, write, frequency=0")
    lines.append("*Output, field, time interval=0.01")
    lines.append("*Node Output")
    lines.append(" U, RF")
    lines.append("*Node Output, nset=RP")
    lines.append(" RF, U")
    lines.append("*Element Output, elset=UMATELEM")
    lines.append(" SDV, S, EVOL")
    lines.append("*Output, history, variable=PRESELECT")
    lines.append("*Energy Output")
    lines.append(" ALLAE, ALLCD, ALLIE, ALLKE, ALLPD, ALLSE, ALLWK, ETOTAL")
    lines.append("*End Step")

    # STEP 2
    lines.append("*Step, name=Step-2, nlgeom=NO, inc=2000")
    lines.append("*Static, direct")
    lines.append(" 0.0001, 0.2,")
    lines.append("*Boundary, amplitude=Amp-2")
    lines.append(" RP, 1, 1, 1.0")
    lines.append("*Restart, write, frequency=0")
    lines.append("*Output, field, time interval=0.01")
    lines.append("*Node Output")
    lines.append(" U, RF")
    lines.append("*Node Output, nset=RP")
    lines.append(" RF, U")
    lines.append("*Element Output, elset=UMATELEM")
    lines.append(" SDV, S, EVOL")
    lines.append("*Output, history, variable=PRESELECT")
    lines.append("*Energy Output")
    lines.append(" ALLAE, ALLCD, ALLIE, ALLKE, ALLPD, ALLSE, ALLWK, ETOTAL")
    lines.append("*End Step")

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
    print("=== Building Repaired Mode-II Verification Packages (Pair 1) ===")
    
    uel_sha = sha256_file(SRC_UEL)
    assert uel_sha == EXPECTED_UEL_SHA256, f"Expected {EXPECTED_UEL_SHA256}, got {uel_sha}"
    print(f"Source UEL: {SRC_UEL}")
    print(f"Source UEL SHA256: {uel_sha}")

    uel_bytes = SRC_UEL.read_bytes()

    batch_manifest = {
        "study_name": "Mode-II Verification Batch (Pair 1)",
        "task_id": "F43MODEREF-FRACFIX-VERIFY1",
        "uel_source_sha256": uel_sha,
        "cases": {},
    }

    for case_name, cfg in VERIFY_CONFIGS.items():
        pkg_dir = OUT_BASE / case_name
        pkg_dir.mkdir(parents=True, exist_ok=True)

        dest_uel = pkg_dir / "f42_mixed_uel.for"
        dest_uel.write_bytes(uel_bytes)
        assert sha256_file(dest_uel) == uel_sha

        inp_sha = generate_inp_deck(case_name, pkg_dir, cfg["n_div_x"], cfg["n_div_y"])
        pbs_sha = generate_pbs_script(case_name, pkg_dir, cfg)
        sh_sha = generate_submit_wrapper(case_name, pkg_dir)

        pkg_manifest = {
            "case_name": case_name,
            "n_div_x": cfg["n_div_x"],
            "n_div_y": cfg["n_div_y"],
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
