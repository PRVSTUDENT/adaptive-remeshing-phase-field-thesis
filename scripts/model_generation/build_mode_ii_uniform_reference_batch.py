#!/usr/bin/env python3
"""
Mode-II Uniform Phase-Field Reference Study Generator
Task: F43MODEREF-PREP1

Generates deterministic 3-layer mixed-UEL input decks and execution packages for
the 3-level Mode-II uniform mesh convergence study:
  - M2REF_H0: Coarse baseline (target h=0.0050 mm, h/l0=0.3333, 3,930 physical -> 11,790 layered elements)
  - M2REF_H1: Medium refinement (target h=0.0025 mm, h/l0=0.1667, 12,064 physical -> 36,192 layered elements)
  - M2REF_H2: Fine refinement (target h=0.0010 mm, h/l0=0.0667, 33,852 physical -> 101,556 layered elements)

All 3 reference candidates share identical scientific constants:
  - E = 210.0 kN/mm^2, nu = 0.3, Gc = 0.0027 kN/mm, l0 = 0.015 mm, k_res = 1.0e-7, thickness = 1.0 mm
  - 3-Layer UEL Architecture: U1/U3 phase, U2/U4 displacement, CPE4/CPE3 passive facsimile
  - User subroutine: f42_mixed_uel.for (SHA256: 5dc005383773a2923b943024b97dc15590a4f220e319fd289c891b15c30844f3)
  - 2-Step loading schedule to full-fracture displacement endpoint U1_final = 0.0100 mm:
      Step-1: 500 increments of 0.001 s via Amp-1 (0 -> 0.0050 mm)
      Step-2: 2000 increments of 0.0001 s via Amp-2 (0.0050 mm -> 0.0100 mm)
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Any

ROOT = Path(__file__).resolve().parents[2]

# Scientific constants
L0 = 0.015            # mm
GC = 0.0027           # kN/mm (2.7 N/mm)
EMOD = 210.0          # kN/mm^2 (210 GPa)
ENU = 0.3             # -
PARK = 1.0e-7         # -
THICKNESS = 1.0       # mm
PASSIVE_E = 1.0e-11   # -
DEPVAR = 18           # SDVs count

# Source Fortran UEL
SRC_UEL = ROOT / "models/generated/mode_ii/f42_mixed_element_uel/f42_mixed_uel.for"
EXPECTED_UEL_SHA256 = "5dc005383773a2923b943024b97dc15590a4f220e319fd289c891b15c30844f3"

# Source Mesh Decks
SRC_MESH_DECKS = {
    "M2REF_H0": {
        "source": ROOT / "models/generated/molnar_gravouil_2017/h_convergence_lc015/H0_exact/SingleNotch.inp",
        "n_phys_expected": 3930,
        "n_nodes_expected": 3998,
        "local_target_h": 0.0050,
        "walltime": "02:00:00",
        "memory": "8gb",
        "queue": "entry_imfdfkmq"
    },
    "M2REF_H1": {
        "source": ROOT / "models/generated/molnar_gravouil_2017/h_convergence_lc015/H1_h0025/H1_h0025.inp",
        "n_phys_expected": 12064,
        "n_nodes_expected": 12381,
        "local_target_h": 0.0025,
        "walltime": "06:00:00",
        "memory": "16gb",
        "queue": "entry_imfdfkmq"
    },
    "M2REF_H2": {
        "source": ROOT / "models/generated/molnar_gravouil_2017/h_convergence_lc015/H2_pub_h0010/H2_pub_h0010.inp",
        "n_phys_expected": 33852,
        "n_nodes_expected": 34507,
        "local_target_h": 0.0010,
        "walltime": "18:00:00",
        "memory": "32gb",
        "queue": "entry_imfdfkmq"
    }
}

OUT_BASE = ROOT / "models/generated/mode_ii/reference_convergence"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_physical_mesh(deck_path: Path, n_phys_expected: int) -> Tuple[Dict[int, Tuple[float, float]], Dict[int, List[int]]]:
    """Parse node coordinates and physical quad element connectivities from source deck."""
    nodes: Dict[int, Tuple[float, float]] = {}
    quads: Dict[int, List[int]] = {}

    lines = deck_path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_nodes = False
    in_elem = False

    for line in lines:
        s = line.strip()
        if not s or s.startswith("**"):
            continue
        if s.lower().startswith("*node"):
            in_nodes = True
            in_elem = False
            continue
        elif s.lower().startswith("*element"):
            in_nodes = False
            # Only read the first physical layer (1..n_phys_expected)
            if "u1" in s.lower() or not quads:
                in_elem = True
            else:
                in_elem = False
            continue
        elif s.startswith("*") and (in_nodes or in_elem):
            in_nodes = False
            in_elem = False

        if in_nodes:
            parts = [p.strip() for p in s.split(",")]
            if len(parts) >= 3:
                try:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    # Exclude the reference point node (if present at y >= 0.55)
                    if y <= 0.51:
                        nodes[nid] = (x, y)
                except ValueError:
                    pass

        if in_elem:
            parts = [p.strip() for p in s.split(",")]
            if len(parts) >= 5:
                try:
                    eid = int(parts[0])
                    if eid <= n_phys_expected:
                        nids = [int(p) for p in parts[1:5]]
                        quads[eid] = nids
                except ValueError:
                    pass

    return nodes, quads


def compute_mesh_stats(nodes: Dict[int, Tuple[float, float]], quads: Dict[int, List[int]]) -> Dict[str, Any]:
    """Compute geometric and element size metrics."""
    tot_area = 0.0
    h_areas = []
    
    for eid, nids in quads.items():
        coords = [nodes[n] for n in nids]
        area = 0.5 * sum(coords[i][0]*coords[(i+1)%4][1] - coords[(i+1)%4][0]*coords[i][1] for i in range(4))
        tot_area += abs(area)
        h_areas.append(abs(area)**0.5)

    h_areas.sort()
    n = len(h_areas)
    
    return {
        "n_physical": n,
        "n_nodes": len(nodes),
        "total_area_mm2": tot_area,
        "h_min_mm": h_areas[0],
        "h_median_mm": h_areas[n // 2],
        "h_mean_mm": sum(h_areas) / n,
        "h_max_mm": h_areas[-1],
        "h_over_l0_min": h_areas[0] / L0,
        "h_over_l0_median": h_areas[n // 2] / L0,
        "h_over_l0_mean": (sum(h_areas) / n) / L0,
        "h_over_l0_max": h_areas[-1] / L0
    }


def generate_reference_deck(
    case_name: str,
    nodes: Dict[int, Tuple[float, float]],
    quads: Dict[int, List[int]],
    out_file: Path
) -> str:
    n_phys = len(quads)
    physical_node_ids = set(nodes.keys())
    rp_node_id = max(physical_node_ids) + 1
    if rp_node_id in physical_node_ids:
        raise RuntimeError(f"RP node ID collision: {rp_node_id} already exists in physical node IDs")

    assert rp_node_id not in physical_node_ids
    all_node_labels = list(nodes.keys()) + [rp_node_id]
    assert len(all_node_labels) == len(set(all_node_labels))

    # Determine boundary node sets
    tol = 1.0e-5
    y_min = -0.50
    y_max = 0.50

    bottom_nodes = sorted([nid for nid, (x, y) in nodes.items() if abs(y - y_min) < tol])
    top_nodes = sorted([nid for nid, (x, y) in nodes.items() if abs(y - y_max) < tol])

    lines: List[str] = []
    lines.append("*Heading")
    lines.append(f"** Mode-II Phase-Field Uniform Reference Study: {case_name}")
    lines.append(f"** 3-Layer Mixed UEL Architecture: U1/U2/CPE4 ({n_phys} physical -> {3*n_phys} layered elements)")
    lines.append(f"** Formulation: l0={L0} mm, Gc={GC} kN/mm, E={EMOD} kN/mm^2, nu={ENU}, k={PARK}")
    lines.append(f"** Loading: 2-Step Shear Displacement to U1_final = 0.0100 mm")
    lines.append("*Preprint, echo=NO, model=NO, history=NO, contact=NO")

    # Nodes
    lines.append("** ==========================================================")
    lines.append("** NODES")
    lines.append("** ==========================================================")
    lines.append("*Node")
    for nid in sorted(nodes.keys()):
        x, y = nodes[nid]
        lines.append(f" {nid:7d}, {x:16.10f}, {y:16.10f}")
    # RP Node
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
    lines.append("*Nset, nset=SET_RP")
    lines.append(f" {rp_node_id:d}")

    # UEL User Elements definition
    lines.append("** ==========================================================")
    lines.append("** USER ELEMENTS (Layer 1: Phase U1, Layer 2: Displacement U2)")
    lines.append("** ==========================================================")
    lines.append("*User Element, type=U1, nodes=4, coordinates=2, properties=3, variables=1")
    lines.append(" 8,")
    lines.append("*User Element, type=U2, nodes=4, coordinates=2, properties=5, variables=18")
    lines.append(" 1, 2")

    # Layer 1: Phase UEL
    lines.append("** Layer 1: Phase UEL Elements (U1)")
    lines.append("*Element, type=U1, elset=PHASE_QUAD")
    for eid in sorted(quads.keys()):
        conn = ", ".join(f"{n:7d}" for n in quads[eid])
        lines.append(f" {eid:7d}, {conn}")

    # Layer 2: Displacement UEL
    lines.append("** Layer 2: Displacement UEL Elements (U2)")
    lines.append("*Element, type=U2, elset=DISP_QUAD")
    for eid in sorted(quads.keys()):
        disp_id = n_phys + eid
        conn = ", ".join(f"{n:7d}" for n in quads[eid])
        lines.append(f" {disp_id:7d}, {conn}")

    # Layer 3: Passive Facsimile Elements (CPE4)
    lines.append("** Layer 3: Passive Facsimile Elements (CPE4)")
    lines.append("*Element, type=CPE4, elset=UMAT_QUAD")
    for eid in sorted(quads.keys()):
        fac_id = 2 * n_phys + eid
        conn = ", ".join(f"{n:7d}" for n in quads[eid])
        lines.append(f" {fac_id:7d}, {conn}")

    # Aggregate sets
    lines.append("** Aggregate Element Sets")
    lines.append("*Elset, elset=PHASE")
    lines.append(" PHASE_QUAD")
    lines.append("*Elset, elset=DISP")
    lines.append(" DISP_QUAD")
    lines.append("*Elset, elset=UMATELEM")
    lines.append(" UMAT_QUAD")
    lines.append("*Elset, elset=All_elem")
    lines.append(" UMATELEM")

    # UEL Properties
    lines.append("** ==========================================================")
    lines.append("** UEL Properties")
    lines.append("** ==========================================================")
    lines.append("*UEL Property, elset=PHASE_QUAD")
    lines.append(f" {L0:.6e}, {GC:.6e}, {THICKNESS:.6e}")
    lines.append("*UEL Property, elset=DISP_QUAD")
    lines.append(f" {EMOD:.6e}, {ENU:.6e}, {THICKNESS:.6e}, {PARK:.6e}, {n_phys}.0")

    # Solid Section for Facsimile
    lines.append("** ==========================================================")
    lines.append("** Solid Sections for Visualization/Facsimile Layer")
    lines.append("** ==========================================================")
    lines.append("*Solid Section, elset=UMAT_QUAD, material=MAT_QUAD_FACSIMILE")
    lines.append(f" {THICKNESS:.6f},")
    lines.append("*Material, name=MAT_QUAD_FACSIMILE")
    lines.append("*Depvar")
    lines.append(f" {DEPVAR}")
    lines.append("*User Material, constants=4")
    lines.append(f" {PASSIVE_E:.6e}, {ENU:.6e}, {n_phys}.0, 4.0")

    # Linear Equations for Top Node Shear Coupling to RP
    lines.append("** ==========================================================")
    lines.append("** EQUATIONS (Multi-Point Top Shear Constraint to RP)")
    lines.append("** ==========================================================")
    for nid in top_nodes:
        lines.append("*Equation")
        lines.append(" 2")
        lines.append(f" {nid:d}, 1, 1.0, {rp_node_id:d}, 1, -1.0")

    # Initial Boundary Conditions
    lines.append("** ==========================================================")
    lines.append("** BOUNDARY CONDITIONS (Pure Shear Baseline)")
    lines.append("** ==========================================================")
    lines.append("** Name: bottom_fixed Type: Displacement/Rotation")
    lines.append("*Boundary")
    lines.append(" bottom_nodes, 1, 2")
    lines.append("** Name: top_vertical_restraint Type: Displacement/Rotation")
    lines.append("*Boundary")
    lines.append(" top_nodes, 2, 2")

    # Amplitudes for 2-step loading
    lines.append("** ==========================================================")
    lines.append("** AMPLITUDES (Full Fracture Two-Step Ramp)")
    lines.append("** ==========================================================")
    lines.append("*Amplitude, name=Amp-1")
    lines.append(" 0.0, 0.0, 0.5, 0.005")
    lines.append("*Amplitude, name=Amp-2")
    lines.append(" 0.0, 0.005, 0.2, 0.010")

    # STEP 1
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

    # STEP 2
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

    out_file.parent.mkdir(parents=True, exist_ok=True)
    deck_text = "\n".join(lines) + "\n"
    out_file.write_text(deck_text, encoding="utf-8")
    return sha256_file(out_file)


def generate_pbs_script(case_name: str, pkg_dir: Path, cfg: Dict[str, Any]) -> str:
    """Generate guarded PBS execution script."""
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
    pbs_file.write_text(content, encoding="utf-8")
    return sha256_file(pbs_file)


def generate_submit_wrapper(case_name: str, pkg_dir: Path) -> str:
    """Generate guarded submission wrapper enforcing human authorization."""
    sh_file = pkg_dir / f"submit_{case_name.lower()}.sh"
    content = f"""#!/bin/bash
set -euo pipefail

# Guarded submission wrapper for {case_name}
# Protocol version: 1
# Requires explicit prior human chat authorization.

AUTH_FILE="../M2REF_BATCH_SUBMISSION_RECORD.json"

if [ ! -f "$AUTH_FILE" ]; then
    echo "ERROR: Authorization record $AUTH_FILE missing. Direct submission prohibited." >&2
    exit 1
fi

echo "Submitting {case_name} to PBS..."
qsub {case_name}.pbs
"""
    sh_file.write_text(content, encoding="utf-8")
    return sha256_file(sh_file)


def main():
    print("=== Building Mode-II Uniform Reference Study Packages ===")
    
    # Verify source Fortran
    if not SRC_UEL.is_file():
        print(f"ERROR: Source Fortran subroutine not found at {SRC_UEL}")
        sys.exit(1)
    uel_sha = sha256_file(SRC_UEL)
    if uel_sha != EXPECTED_UEL_SHA256:
        print(f"ERROR: UEL SHA256 mismatch: {uel_sha} != {EXPECTED_UEL_SHA256}")
        sys.exit(1)

    uel_bytes = SRC_UEL.read_bytes()

    batch_manifest = {
        "study_name": "Mode-II Uniform Phase-Field Reference Convergence",
        "task_id": "F43MODEREF-PREP1",
        "protocol_version": 1,
        "uel_source_sha256": uel_sha,
        "material_constants": {
            "l0_mm": L0,
            "Gc_kN_per_mm": GC,
            "E_kN_per_mm2": EMOD,
            "nu": ENU,
            "k_residual": PARK,
            "thickness_mm": THICKNESS
        },
        "loading_endpoint": {
            "mode": "shear_displacement",
            "step1_u1_mm": 0.0050,
            "step1_increments": 500,
            "step2_u1_mm": 0.0100,
            "step2_increments": 2000,
            "target_final_u1_mm": 0.0100
        },
        "candidates": {}
    }

    for case_name, cfg in SRC_MESH_DECKS.items():
        print(f"\n--- Processing {case_name} ---")
        pkg_dir = OUT_BASE / case_name
        pkg_dir.mkdir(parents=True, exist_ok=True)

        # Parse source physical mesh
        nodes, quads = parse_physical_mesh(cfg["source"], cfg["n_phys_expected"])
        stats = compute_mesh_stats(nodes, quads)
        print(f"  Physical elements: {stats['n_physical']}, Nodes: {stats['n_nodes']}")
        print(f"  h_area range: [{stats['h_min_mm']:.6f}, {stats['h_max_mm']:.6f}] mm (median: {stats['h_median_mm']:.6f} mm)")
        print(f"  h/l0 range: [{stats['h_over_l0_min']:.4f}, {stats['h_over_l0_max']:.4f}] (median: {stats['h_over_l0_median']:.4f})")

        # Copy UEL subroutine
        dest_uel = pkg_dir / "f42_mixed_uel.for"
        dest_uel.write_bytes(uel_bytes)

        # Generate Input Deck
        deck_file = pkg_dir / f"{case_name}.inp"
        deck_sha = generate_reference_deck(case_name, nodes, quads, deck_file)
        print(f"  Deck written: {deck_file.name} (SHA256: {deck_sha[:16]}...)")

        # Generate PBS and Submit Wrappers
        pbs_sha = generate_pbs_script(case_name, pkg_dir, cfg)
        submit_sha = generate_submit_wrapper(case_name, pkg_dir)

        # Record candidate details
        batch_manifest["candidates"][case_name] = {
            "job_name": case_name,
            "deck_path": deck_file.relative_to(ROOT).as_posix(),
            "deck_sha256": deck_sha,
            "uel_path": dest_uel.relative_to(ROOT).as_posix(),
            "uel_sha256": uel_sha,
            "pbs_path": (pkg_dir / f"{case_name}.pbs").relative_to(ROOT).as_posix(),
            "pbs_sha256": pbs_sha,
            "submit_wrapper": (pkg_dir / f"submit_{case_name.lower()}.sh").relative_to(ROOT).as_posix(),
            "submit_sha256": submit_sha,
            "physical_elements": stats["n_physical"],
            "physical_nodes": stats["n_nodes"],
            "layered_elements": 3 * stats["n_physical"],
            "active_dofs": 3 * stats["n_nodes"],
            "local_target_h_mm": cfg["local_target_h"],
            "h_area_min_mm": stats["h_min_mm"],
            "h_area_median_mm": stats["h_median_mm"],
            "h_area_mean_mm": stats["h_mean_mm"],
            "h_area_max_mm": stats["h_max_mm"],
            "h_over_l0_min": stats["h_over_l0_min"],
            "h_over_l0_median": stats["h_over_l0_median"],
            "h_over_l0_mean": stats["h_over_l0_mean"],
            "h_over_l0_max": stats["h_over_l0_max"],
            "total_area_mm2": stats["total_area_mm2"],
            "resources": {
                "cpus": 1,
                "memory": cfg["memory"],
                "walltime": cfg["walltime"],
                "queue": cfg["queue"]
            }
        }

    manifest_file = OUT_BASE / "M2REF_BATCH_MANIFEST.json"
    manifest_file.write_text(json.dumps(batch_manifest, indent=2), encoding="utf-8")
    print(f"\nMaster Batch Manifest written to: {manifest_file}")


if __name__ == "__main__":
    main()
