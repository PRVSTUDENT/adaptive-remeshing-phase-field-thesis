#!/usr/bin/env python3
"""Build Mode-II Adaptive MM/PK5 Fracture Production Pair (FRACFIX).
Task: F43ADAPT-PROD-PREP1

Generates deterministic production packages for:
  1. M2ADAPT_MM_FRACFIX_PROD (2,206 physical elements -> 6,618 layered elements)
  2. M2ADAPT_PK5_FRACFIX_PROD (4,894 physical elements -> 14,682 layered elements)

Formulation & Architecture:
  - 3-Layer Mixed UEL: U1/U2 (quads), U3/U4 (triangles), CPE4/CPE3 (facsimile)
  - 2-Step Full Fracture Loading:
      Step-1: Amp-1 shear to 0.0050 mm (500 increments, direct dt=0.001)
      Step-2: Amp-2 shear to 0.0100 mm (2000 increments, direct dt=0.0001)
  - Qualified Subroutine: f42_mixed_uel.for (SHA256: 0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8)
  - Parameters: l0=0.015 mm, Gc=0.0027 kN/mm, E=210.0 kN/mm^2, nu=0.3, k=1.0e-7, thickness=1.0 mm
  - NPHYS mapping: 5 UEL properties for U2/U4 with true NPHYS passed in 5th property slot.
  - Complete output requests: RP U/RF, UMATELEM S/E/SDV/EVOL, global energy ALLAE..ETOTAL.
  - Corrected OpenPBS notification: -m abe, 2-recipient email, mem=8gb.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
SRC_UEL = ROOT / "models/generated/mode_ii/f42_mixed_element_uel/f42_mixed_uel.for"
OUT_BASE = ROOT / "models/generated/mode_ii/production_adaptive_batch"

EXPECTED_UEL_SHA256 = "0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8"

APPROVED_EMAIL_DIRECTIVE = "#PBS -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de"

BATCH_CONFIGS = {
    "M2ADAPT_MM_FRACFIX_PROD": {
        "candidate_key": "MM",
        "candidate_name": "F43REM4_MM",
        "source_deck": ROOT / "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/runtime_mm/F43REM4_MM.inp",
        "source_sha256": "d404356d5ce9a47461dae0f82e3fe9eee2929ccfa73a30b436af72ab56c43374",
        "n_phys_expected": 2206,
        "n_quads_expected": 2137,
        "n_tris_expected": 69,
        "n_nodes_expected": 2294,
        "memory": "8gb",
        "walltime": "02:00:00",
        "queue": "entry_imfdfkmq",
        "cpus": 1,
    },
    "M2ADAPT_PK5_FRACFIX_PROD": {
        "candidate_key": "PK5",
        "candidate_name": "F43REM4_PK5",
        "source_deck": ROOT / "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/runtime_pk5/F43REM4_PK5.inp",
        "source_sha256": "87ab62c411f8d14ef9eca2857036e88fb2cbd9ccdf0171a80c5e97e7edc7ffa9",
        "n_phys_expected": 4894,
        "n_quads_expected": 4766,
        "n_tris_expected": 128,
        "n_nodes_expected": 4998,
        "memory": "8gb",
        "walltime": "04:00:00",
        "queue": "entry_imfdfkmq",
        "cpus": 1,
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


def parse_physical_mesh(deck_path: Path) -> Tuple[Dict[int, Tuple[float, float]], Dict[int, List[int]], Dict[int, List[int]]]:
    """Parse node coordinates, quad elements, and tri elements from standard Abaqus deck."""
    nodes: Dict[int, Tuple[float, float]] = {}
    quads: Dict[int, List[int]] = {}
    tris: Dict[int, List[int]] = {}

    lines = deck_path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_nodes = False
    in_cpe4 = False
    in_cpe3 = False

    for line in lines:
        s = line.strip()
        if not s or s.startswith("**"):
            continue
        if s.lower().startswith("*node"):
            in_nodes = True
            in_cpe4 = False
            in_cpe3 = False
            continue
        elif s.lower().startswith("*element"):
            in_nodes = False
            if "cpe4" in s.lower():
                in_cpe4 = True
                in_cpe3 = False
            elif "cpe3" in s.lower():
                in_cpe4 = False
                in_cpe3 = True
            else:
                in_cpe4 = False
                in_cpe3 = False
            continue
        elif s.startswith("*") and (in_nodes or in_cpe4 or in_cpe3):
            in_nodes = False
            in_cpe4 = False
            in_cpe3 = False

        if in_nodes:
            parts = [p.strip() for p in s.split(",")]
            if len(parts) >= 3:
                try:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    nodes[nid] = (x, y)
                except ValueError:
                    pass
        elif in_cpe4:
            parts = [p.strip() for p in s.split(",")]
            if len(parts) >= 5:
                try:
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:5]]
                    quads[eid] = conn
                except ValueError:
                    pass
        elif in_cpe3:
            parts = [p.strip() for p in s.split(",")]
            if len(parts) >= 4:
                try:
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:4]]
                    tris[eid] = conn
                except ValueError:
                    pass

    return nodes, quads, tris


def format_id_list(ids: List[int], per_line: int = 16) -> List[str]:
    lines = []
    for i in range(0, len(ids), per_line):
        chunk = ids[i:i + per_line]
        lines.append(", ".join(str(x) for x in chunk))
    return lines


def generate_production_deck(case_name: str, cfg: Dict[str, Any]) -> str:
    src_deck = cfg["source_deck"]
    nodes, quads, tris = parse_physical_mesh(src_deck)

    n_nodes = len(nodes)
    n_quads = len(quads)
    n_tris = len(tris)
    n_phys = n_quads + n_tris

    if n_phys != cfg["n_phys_expected"]:
        raise ValueError(f"Physical element count mismatch for {case_name}: {n_phys} != {cfg['n_phys_expected']}")
    if n_quads != cfg["n_quads_expected"]:
        raise ValueError(f"Quad count mismatch for {case_name}: {n_quads} != {cfg['n_quads_expected']}")
    if n_tris != cfg["n_tris_expected"]:
        raise ValueError(f"Tri count mismatch for {case_name}: {n_tris} != {cfg['n_tris_expected']}")
    if n_nodes != cfg["n_nodes_expected"]:
        raise ValueError(f"Node count mismatch for {case_name}: {n_nodes} != {cfg['n_nodes_expected']}")

    sorted_node_ids = sorted(nodes.keys())
    sorted_quad_ids = sorted(quads.keys())
    sorted_tri_ids = sorted(tris.keys())

    # Map physical elements into contiguous 1..NPHYS ordering:
    # 1..n_quads for quads, n_quads+1..n_phys for tris
    quad_physical_map = {}
    for idx, old_id in enumerate(sorted_quad_ids, start=1):
        quad_physical_map[idx] = quads[old_id]

    tri_physical_map = {}
    for idx, old_id in enumerate(sorted_tri_ids, start=n_quads + 1):
        tri_physical_map[idx] = tris[old_id]

    # Identify boundary nodes: bottom y <= -0.49999, top y >= 0.49999
    bottom_nodes = [nid for nid, (x, y) in nodes.items() if y <= -0.49999]
    top_nodes = [nid for nid, (x, y) in nodes.items() if y >= 0.49999]
    bottom_nodes.sort()
    top_nodes.sort()

    lines = []
    lines.append("*Heading")
    lines.append(f"** Mode-II Phase-Field Adaptive Production Model: {case_name}")
    lines.append(f"** Candidate: {cfg['candidate_name']} ({n_phys} physical elements, {n_nodes} nodes)")
    lines.append(f"** 3-Layer Mixed UEL Architecture: U1/U2/U3/U4/CPE4/CPE3 ({3 * n_phys} layered elements)")
    lines.append(f"** Formulation: l0={L0} mm, Gc={GC} kN/mm, E={EMOD} kN/mm^2, nu={ENU}, k={PARK}, thickness={THCK} mm")
    lines.append("** Loading: Two-Step Pure Shear to U1_final = 0.0100 mm")
    lines.append("*Preprint, echo=NO, model=NO, history=NO, contact=NO")
    lines.append("** ==========================================================")
    lines.append("** PARTS & USER ELEMENT DECLARATIONS")
    lines.append("** ==========================================================")
    lines.append("*Part, name=PlatePart")
    lines.append("*User Element, nodes=4, type=U1, properties=3, coordinates=2, VARIABLES=18")
    lines.append(" 3")
    lines.append("*User Element, nodes=4, type=U2, properties=5, coordinates=2, VARIABLES=18")
    lines.append(" 1, 2")
    if n_tris > 0:
        lines.append("*User Element, nodes=3, type=U3, properties=3, coordinates=2, VARIABLES=18")
        lines.append(" 3")
        lines.append("*User Element, nodes=3, type=U4, properties=5, coordinates=2, VARIABLES=18")
        lines.append(" 1, 2")

    lines.append("*Node")
    for nid in sorted_node_ids:
        x, y = nodes[nid]
        lines.append(f" {nid:7d}, {x:18.10e}, {y:18.10e}")

    # Layer 1: Phase Elements (1 .. n_phys)
    lines.append("** ==========================================================")
    lines.append("** Layer 1: Phase-Field Elements (U1 Quads & U3 Tris)")
    lines.append("** ==========================================================")
    lines.append("*Element, type=U1")
    for p_id in range(1, n_quads + 1):
        conn = quad_physical_map[p_id]
        lines.append(f" {p_id:7d}, {conn[0]:7d}, {conn[1]:7d}, {conn[2]:7d}, {conn[3]:7d}")

    if n_tris > 0:
        lines.append("*Element, type=U3")
        for p_id in range(n_quads + 1, n_phys + 1):
            conn = tri_physical_map[p_id]
            lines.append(f" {p_id:7d}, {conn[0]:7d}, {conn[1]:7d}, {conn[2]:7d}")

    # Layer 2: Displacement Elements (n_phys+1 .. 2*n_phys)
    lines.append("** ==========================================================")
    lines.append("** Layer 2: Displacement Elements (U2 Quads & U4 Tris)")
    lines.append("** ==========================================================")
    lines.append("*Element, type=U2")
    for p_id in range(1, n_quads + 1):
        d_id = n_phys + p_id
        conn = quad_physical_map[p_id]
        lines.append(f" {d_id:7d}, {conn[0]:7d}, {conn[1]:7d}, {conn[2]:7d}, {conn[3]:7d}")

    if n_tris > 0:
        lines.append("*Element, type=U4")
        for p_id in range(n_quads + 1, n_phys + 1):
            d_id = n_phys + p_id
            conn = tri_physical_map[p_id]
            lines.append(f" {d_id:7d}, {conn[0]:7d}, {conn[1]:7d}, {conn[2]:7d}")

    # Layer 3: Facsimile Visualization Elements (2*n_phys+1 .. 3*n_phys)
    lines.append("** ==========================================================")
    lines.append("** Layer 3: Facsimile Visualization Elements (CPE4 Quads & CPE3 Tris)")
    lines.append("** ==========================================================")
    lines.append("*Element, type=CPE4")
    for p_id in range(1, n_quads + 1):
        f_id = 2 * n_phys + p_id
        conn = quad_physical_map[p_id]
        lines.append(f" {f_id:7d}, {conn[0]:7d}, {conn[1]:7d}, {conn[2]:7d}, {conn[3]:7d}")

    if n_tris > 0:
        lines.append("*Element, type=CPE3")
        for p_id in range(n_quads + 1, n_phys + 1):
            f_id = 2 * n_phys + p_id
            conn = tri_physical_map[p_id]
            lines.append(f" {f_id:7d}, {conn[0]:7d}, {conn[1]:7d}, {conn[2]:7d}")

    # Element sets
    lines.append("** ==========================================================")
    lines.append("** ELEMENT SETS")
    lines.append("** ==========================================================")
    lines.append("*Elset, elset=PHASE_QUAD, generate")
    lines.append(f" 1, {n_quads}, 1")
    lines.append("*Elset, elset=DISP_QUAD, generate")
    lines.append(f" {n_phys + 1}, {n_phys + n_quads}, 1")
    lines.append("*Elset, elset=UMAT_QUAD, generate")
    lines.append(f" {2 * n_phys + 1}, {2 * n_phys + n_quads}, 1")

    if n_tris > 0:
        lines.append("*Elset, elset=PHASE_TRI, generate")
        lines.append(f" {n_quads + 1}, {n_phys}, 1")
        lines.append("*Elset, elset=DISP_TRI, generate")
        lines.append(f" {n_phys + n_quads + 1}, {2 * n_phys}, 1")
        lines.append("*Elset, elset=UMAT_TRI, generate")
        lines.append(f" {2 * n_phys + n_quads + 1}, {3 * n_phys}, 1")

    lines.append("*Elset, elset=PHASE_ALL, generate")
    lines.append(f" 1, {n_phys}, 1")
    lines.append("*Elset, elset=DISP_ALL, generate")
    lines.append(f" {n_phys + 1}, {2 * n_phys}, 1")
    lines.append("*Elset, elset=UMATELEM, generate")
    lines.append(f" {2 * n_phys + 1}, {3 * n_phys}, 1")

    # UEL Properties
    lines.append("** ==========================================================")
    lines.append("** UEL PROPERTIES (l0, Gc, thickness, E, nu, park, NPHYS)")
    lines.append("** ==========================================================")
    lines.append("*UEL Property, elset=PHASE_QUAD")
    lines.append(f" {L0:.6e}, {GC:.6e}, {THCK:.6e}")
    lines.append("*UEL Property, elset=DISP_QUAD")
    lines.append(f" {EMOD:.6e}, {ENU:.6e}, {THCK:.6e}, {PARK:.6e}, {n_phys}.0")
    if n_tris > 0:
        lines.append("*UEL Property, elset=PHASE_TRI")
        lines.append(f" {L0:.6e}, {GC:.6e}, {THCK:.6e}")
        lines.append("*UEL Property, elset=DISP_TRI")
        lines.append(f" {EMOD:.6e}, {ENU:.6e}, {THCK:.6e}, {PARK:.6e}, {n_phys}.0")

    # Solid sections for facsimile
    lines.append("** ==========================================================")
    lines.append("** SOLID SECTIONS FOR FACSIMILE LAYER")
    lines.append("** ==========================================================")
    lines.append("*Solid Section, elset=UMAT_QUAD, material=MAT_QUAD_FACSIMILE")
    lines.append(f" {THCK:.6e}")
    if n_tris > 0:
        lines.append("*Solid Section, elset=UMAT_TRI, material=MAT_TRI_FACSIMILE")
        lines.append(f" {THCK:.6e}")

    lines.append("*End Part")

    # Assembly
    lines.append("** ==========================================================")
    lines.append("** ASSEMBLY & BOUNDARY SETS")
    lines.append("** ==========================================================")
    lines.append("*Assembly, name=Assembly")
    lines.append("*Instance, name=PlateInstance, part=PlatePart")
    lines.append("*End Instance")
    lines.append("** Reference Point for Shear Loading")
    lines.append("*Node")
    lines.append(" 1, 0.0, 0.600000024, 0.0")
    lines.append("*Nset, nset=RP")
    lines.append(" 1")

    lines.append("*Nset, nset=bottom_nodes, instance=PlateInstance")
    for chunk in format_id_list(bottom_nodes):
        lines.append(" " + chunk)

    lines.append("*Nset, nset=top_nodes, instance=PlateInstance")
    for chunk in format_id_list(top_nodes):
        lines.append(" " + chunk)

    lines.append("*Elset, elset=UMATELEM, instance=PlateInstance")
    lines.append(" UMATELEM")
    lines.append("*Elset, elset=All_elem, instance=PlateInstance")
    lines.append(" UMATELEM")

    lines.append("** Constraint: Mode-II Pure Shear top_nodes -> RP")
    lines.append("*Equation")
    lines.append(" 2")
    lines.append(" top_nodes, 1, 1.")
    lines.append(" RP, 1, -1.")
    lines.append("*End Assembly")

    # Materials
    lines.append("** ==========================================================")
    lines.append("** MATERIALS (Passive Facsimile Visualization Material)")
    lines.append("** ==========================================================")
    lines.append("*Material, name=MAT_QUAD_FACSIMILE")
    lines.append(f"*Depvar")
    lines.append(f" {DEPVAR}")
    lines.append("*User Material, constants=4")
    lines.append(f" {PASSIVE_E:.6e}, {ENU:.6e}, {n_phys}.0, 4.0")

    if n_tris > 0:
        lines.append("*Material, name=MAT_TRI_FACSIMILE")
        lines.append(f"*Depvar")
        lines.append(f" {DEPVAR}")
        lines.append("*User Material, constants=4")
        lines.append(f" {PASSIVE_E:.6e}, {ENU:.6e}, {n_phys}.0, 3.0")

    # Model BCs
    lines.append("** ==========================================================")
    lines.append("** BOUNDARY CONDITIONS (Pure Shear Baseline)")
    lines.append("** ==========================================================")
    lines.append("*Boundary")
    lines.append(" bottom_nodes, 1, 2")
    lines.append("*Boundary")
    lines.append(" top_nodes, 2, 2")

    # Full Fracture Two-Step Ramp Amplitudes
    lines.append("** ==========================================================")
    lines.append("** AMPLITUDES (Full Fracture Two-Step Ramp)")
    lines.append("** ==========================================================")
    lines.append("*Amplitude, name=Amp-1")
    lines.append(" 0.0, 0.0, 0.5, 0.005")
    lines.append("*Amplitude, name=Amp-2")
    lines.append(" 0.0, 0.005, 0.2, 0.010")

    # Step-1
    lines.append("** ----------------------------------------------------------")
    lines.append("** STEP: Step-1 (Pre-cracking shear to 0.0050 mm)")
    lines.append("** ----------------------------------------------------------")
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

    # Step-2
    lines.append("** ----------------------------------------------------------")
    lines.append("** STEP: Step-2 (Full fracture shear to 0.0100 mm)")
    lines.append("** ----------------------------------------------------------")
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

    return "\n".join(lines) + "\n"


def generate_production_pbs(case_name: str, cfg: Dict[str, Any]) -> str:
    lines = [
        "#!/bin/bash",
        f"#PBS -N {case_name}",
        f"#PBS -l select=1:ncpus={cfg['cpus']}:mem={cfg['memory']}",
        f"#PBS -l walltime={cfg['walltime']}",
        f"#PBS -q {cfg['queue']}",
        "#PBS -m abe",
        APPROVED_EMAIL_DIRECTIVE,
        "#PBS -j oe",
        '#PBS -o evidence/$PBS_JOBID/execution.log',
        "",
        "set -euo pipefail",
        "",
        'cd "$PBS_O_WORKDIR"',
        'mkdir -p evidence/"$PBS_JOBID"',
        "",
        'echo "=== Host Environment ==="',
        "hostname",
        "date",
        "module list || true",
        "",
        "module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7",
        "",
        f'echo "=== Running Abaqus Job {case_name} ==="',
        f"abaqus job={case_name} input={case_name}.inp user=f42_mixed_uel.for cpus={cfg['cpus']} interactive double=both ask_delete=OFF",
        "",
        'echo "=== Execution Complete ==="',
        "date",
        ""
    ]
    return "\n".join(lines)


def generate_submission_wrapper(case_name: str) -> str:
    lines = [
        "#!/bin/bash",
        "set -euo pipefail",
        "",
        f"# Guarded submission wrapper for {case_name}",
        "# Protocol version: 1",
        "# Requires explicit prior human chat authorization.",
        "",
        'AUTH_FILE="../M2ADAPT_BATCH_SUBMISSION_RECORD.json"',
        "",
        'if [ ! -f "$AUTH_FILE" ]; then',
        '    echo "ERROR: Authorization record $AUTH_FILE missing. Direct submission prohibited." >&2',
        "    exit 1",
        "fi",
        "",
        f'echo "Submitting {case_name} to PBS..."',
        f"qsub {case_name}.pbs",
        ""
    ]
    return "\n".join(lines)


def build_adaptive_production_batch() -> Dict[str, Any]:
    print("======================================================================")
    print("F43ADAPT-PROD-PREP1: BUILD MODE-II ADAPTIVE FRACTURE PRODUCTION PAIR")
    print("======================================================================")

    if not SRC_UEL.is_file():
        raise FileNotFoundError(f"Subroutine missing: {SRC_UEL}")
    uel_sha = sha256_file(SRC_UEL)
    if uel_sha != EXPECTED_UEL_SHA256:
        raise ValueError(f"UEL SHA mismatch: {uel_sha} != {EXPECTED_UEL_SHA256}")
    print(f"Qualified FRACFIX UEL SHA256 verified: {uel_sha}")

    OUT_BASE.mkdir(parents=True, exist_ok=True)
    summary_report: Dict[str, Any] = {
        "protocol_version": 1,
        "task_id": "F43ADAPT-PROD-PREP1",
        "uel_source_sha256": uel_sha,
        "packages": {}
    }

    for case_name, cfg in BATCH_CONFIGS.items():
        print(f"\n--- Generating Package: {case_name} ---")
        pkg_dir = OUT_BASE / case_name
        pkg_dir.mkdir(parents=True, exist_ok=True)

        inp_content = generate_production_deck(case_name, cfg)
        inp_path = pkg_dir / f"{case_name}.inp"
        inp_path.write_text(inp_content, encoding="utf-8", newline="\n")
        inp_sha = sha256_file(inp_path)
        print(f"  Input deck written: {inp_path.name} (SHA256: {inp_sha})")

        uel_dst = pkg_dir / "f42_mixed_uel.for"
        uel_dst.write_bytes(SRC_UEL.read_bytes())
        uel_pkg_sha = sha256_file(uel_dst)
        print(f"  UEL written: {uel_dst.name} (SHA256: {uel_pkg_sha})")

        pbs_content = generate_production_pbs(case_name, cfg)
        pbs_path = pkg_dir / f"{case_name}.pbs"
        pbs_path.write_text(pbs_content, encoding="utf-8", newline="\n")
        pbs_sha = sha256_file(pbs_path)
        print(f"  PBS written: {pbs_path.name} (SHA256: {pbs_sha})")

        sub_content = generate_submission_wrapper(case_name)
        sub_path = pkg_dir / f"submit_{case_name.lower()}.sh"
        sub_path.write_text(sub_content, encoding="utf-8", newline="\n")
        sub_sha = sha256_file(sub_path)
        print(f"  Submit wrapper written: {sub_path.name} (SHA256: {sub_sha})")

        manifest = {
            "case_name": case_name,
            "candidate_key": cfg["candidate_key"],
            "candidate_name": cfg["candidate_name"],
            "physical_node_count": cfg["n_nodes_expected"],
            "physical_element_count": cfg["n_phys_expected"],
            "physical_quads": cfg["n_quads_expected"],
            "physical_tris": cfg["n_tris_expected"],
            "layered_element_count": 3 * cfg["n_phys_expected"],
            "inp_sha256": inp_sha,
            "uel_sha256": uel_pkg_sha,
            "pbs_sha256": pbs_sha,
            "submit_sh_sha256": sub_sha,
            "memory": cfg["memory"],
            "walltime": cfg["walltime"],
            "queue": cfg["queue"],
            "cpus": cfg["cpus"]
        }
        manifest_path = pkg_dir / "PACKAGE_MANIFEST.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
        manifest_sha = sha256_file(manifest_path)
        print(f"  Manifest written: {manifest_path.name} (SHA256: {manifest_sha})")

        summary_report["packages"][case_name] = {
            "dir": str(pkg_dir),
            "manifest": manifest,
            "manifest_sha256": manifest_sha,
            "raw_hashes": {
                "input": inp_sha,
                "uel": uel_pkg_sha,
                "pbs": pbs_sha,
                "wrapper": sub_sha,
                "manifest": manifest_sha
            }
        }

    summary_file = OUT_BASE / "F43ADAPT_PRODUCTION_BATCH_SUMMARY.json"
    summary_file.write_text(json.dumps(summary_report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"\nBatch generation summary written: {summary_file}")
    return summary_report


if __name__ == "__main__":
    build_adaptive_production_batch()
