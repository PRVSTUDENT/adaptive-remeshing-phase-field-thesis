#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_c5_companion_deck.py
==========================
Constructs the reusable C5 companion-continuum linear-elastic Abaqus input deck
for authentic patch-recovery stress error estimation (MISESERI, MISESAVG).

Extracts the authentic 12,996-element quad mesh directly from C5 candidate mesh
(models/pandey_kumar_mode1/155_c5_candidate_mesh/M1_C5_CANDIDATE_MESH.inp), preserving:
1. Exactly 13,278 physical nodes + RP 999999.
2. Exactly 12,996 CPE4 continuum elements (elset=ALL_QUADS).
3. Exactly 53 duplicate coincident slit-flank node pairs (y = 0.050 mm, x <= 0.040 mm).
4. Exactly 62 shared ligament nodes (y = 0.050 mm, x > 0.040 mm).
5. Exact node sets: N_TOP (115 nodes), N_BOTTOM (115 nodes), N_PIN (node 1), N_RP (node 999999).
6. Exactly 115 kinematic tie equations in DOF 2 (u_y) connecting N_TOP to RP 999999.
7. Linear-elastic material properties: E = 210.0 kN/mm^2, nu = 0.3.
8. Static step with parameterized displacement target u_y (default Checkpoint 01: 0.001860312544 mm).
9. Element output requesting S, MISESERI, MISESAVG, EVOL.

Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
C5_SOURCE_INP = REPO_ROOT / "models" / "pandey_kumar_mode1" / "155_c5_candidate_mesh" / "M1_C5_CANDIDATE_MESH.inp"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "168_c5_companion_miseseri"

# Canonical Checkpoint 03 target displacement
CHECKPOINT_03_TARGET_UY = 0.0018703125442191958

# Development fallback fixture: Checkpoint 01 from physically accepted Job 1419485.mmaster02
DEFAULT_TARGET_UY = 0.0018603125442191958


class DependencyBlockedError(RuntimeError):
    """Raised when a required predecessor dependency (e.g. Checkpoint 03) is missing or unaccepted."""
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def load_and_validate_checkpoint(
    checkpoint_path: Path,
    require_checkpoint_03: bool = False
) -> dict:
    """
    Validates that a provided checkpoint JSON file is physically converged and complete
    on the 12,996-quad Candidate C5 mesh (13,278 nodes).
    Enforces Checkpoint 03 parameters if require_checkpoint_03 is True.
    """
    cp_path = Path(checkpoint_path)
    if not cp_path.is_file():
        raise DependencyBlockedError(f"Checkpoint file does not exist: {cp_path}")

    chk_sha = sha256_file(cp_path)
    try:
        data = json.loads(cp_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to parse checkpoint JSON at {cp_path}: {exc}")

    # Verify coupled convergence
    if not data.get("coupled_convergence", False):
        raise ValueError(f"Checkpoint {cp_path} is not converged: coupled_convergence={data.get('coupled_convergence')}")

    target_uy = data.get("target_uy_mm")
    if target_uy is None or not math.isfinite(target_uy):
        raise ValueError(f"Invalid target_uy_mm in checkpoint: {target_uy}")

    disp = data.get("displacement", [])
    dmg = data.get("damage", [])
    if len(disp) != 13278:
        raise ValueError(f"Expected 13,278 nodal displacements on C5 mesh, got {len(disp)}")
    if len(dmg) != 13278:
        raise ValueError(f"Expected 13,278 nodal damage values on C5 mesh, got {len(dmg)}")

    # Checkpoint 03 specific requirements
    if require_checkpoint_03:
        if not math.isclose(target_uy, CHECKPOINT_03_TARGET_UY, rel_tol=1e-8):
            raise DependencyBlockedError(
                f"FAIL_CLOSED: Checkpoint at {cp_path} has uy={target_uy:.10f} mm; "
                f"expected Checkpoint 03 at uy={CHECKPOINT_03_TARGET_UY:.10f} mm"
            )

    return {
        "path": str(cp_path),
        "sha256": chk_sha,
        "target_uy_mm": float(target_uy),
        "baseline_uy_mm": float(data.get("baseline_uy_mm", 0.0)),
        "reaction_force_kN": float(data.get("reaction_force_kN", 0.0)),
        "total_energy_kNmm": float(data.get("total_energy_kNmm", 0.0)),
        "outer_iteration": int(data.get("outer_iteration", 0)),
        "coupled_convergence": bool(data.get("coupled_convergence", False)),
        "contract": data.get("contract", "")
    }


def extract_c5_mesh_components(inp_path: Path):
    """
    Extracts nodes, layer 1 phase elements (to re-label as CPE4 continuum quads),
    node sets, and equations from the authoritative C5 candidate input deck.
    """
    if not inp_path.is_file():
        raise FileNotFoundError(f"Source C5 input deck not found: {inp_path}")

    with inp_path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    # In M1_C5_CANDIDATE_MESH.inp:
    # Lines 11 to 13290: *Node (13,278 nodes + RP 999999)
    # Lines 13290 to 13312: *Nset (N_BOTTOM, N_PIN, N_TOP, N_RP)
    # Lines 13312 to 13657: *Equation (115 equations)
    # Lines 13658 to 26654: *Element, type=U1, elset=PHASE_QUADS (12,996 quads)

    node_lines = [l for l in lines[11:13290] if not l.strip().startswith("*") and not l.strip().startswith("**") and l.strip()]
    nset_lines = lines[13290:13312]
    eq_lines = lines[13312:13657]
    elem_lines = [l for l in lines[13658:26654] if not l.strip().startswith("*") and not l.strip().startswith("**") and l.strip()]

    if len(node_lines) != 13279:
        raise ValueError(f"Expected 13279 node lines (13278 + RP), got {len(node_lines)}")
    if len(elem_lines) != 12996:
        raise ValueError(f"Expected 12996 quad elements, got {len(elem_lines)}")

    return node_lines, elem_lines, nset_lines, eq_lines


def build_c5_companion_deck(
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    displacement_target: float | None = None,
    checkpoint_path: Path | None = None,
    require_checkpoint_03: bool = False,
    job_name: str = "M1_C5_COMPANION_MISESERI"
) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_inp = output_dir / f"{job_name}.inp"

    cp_info = None
    if checkpoint_path is not None:
        cp_info = load_and_validate_checkpoint(checkpoint_path, require_checkpoint_03=require_checkpoint_03)
        actual_target_uy = cp_info["target_uy_mm"]
    elif require_checkpoint_03:
        raise DependencyBlockedError(
            "FAIL_CLOSED: Checkpoint 03 (uy=0.001870312544 mm) is strictly required for Package 168 execution, "
            "but no checkpoint path was provided."
        )
    elif displacement_target is not None:
        actual_target_uy = float(displacement_target)
    else:
        actual_target_uy = DEFAULT_TARGET_UY

    node_lines, elem_lines, nset_lines, eq_lines = extract_c5_mesh_components(C5_SOURCE_INP)

    with out_inp.open("w", encoding="utf-8") as f:
        f.write("*Heading\n")
        f.write(f"** Mode-I C5 Companion Continuum Linear-Elastic Model for MISESERI Recovery\n")
        f.write(f"** Prescribed Load Target: uy = {actual_target_uy:.10f} mm\n")
        f.write(f"** Discretization: 12,996 CPE4 Continuum Quads, 13,278 Nodes + RP 999999\n")
        f.write(f"** Slit Topology: 53 coincident split pairs (x <= 0.040, y = 0.050 mm)\n")
        f.write(f"** Protocol Version: 2 (Task F1598)\n")
        f.write("*Preprint, echo=NO, model=NO, history=NO, contact=NO\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("** NODES (13,278 physical nodes + RP 999999)\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*Node\n")
        for l in node_lines:
            f.write(l)

        f.write("** ----------------------------------------------------------\n")
        f.write("** CONTINUUM CPE4 ELEMENTS (12,996 Quads)\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*Element, type=CPE4, elset=ALL_QUADS\n")
        for l in elem_lines:
            f.write(l)

        f.write("** ----------------------------------------------------------\n")
        f.write("** NODE SETS (N_BOTTOM, N_PIN, N_TOP, N_RP)\n")
        f.write("** ----------------------------------------------------------\n")
        for l in nset_lines:
            f.write(l)

        f.write("** ----------------------------------------------------------\n")
        f.write("** EQUATIONS: 115 Kinematic ties in DOF 2 (u_y) to RP 999999\n")
        f.write("** ----------------------------------------------------------\n")
        for l in eq_lines:
            f.write(l)

        f.write("** ----------------------------------------------------------\n")
        f.write("** SOLID SECTION & LINEAR ISOTROPIC ELASTICITY\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*Solid Section, elset=ALL_QUADS, material=STEEL\n")
        f.write("1.0\n")
        f.write("*Material, name=STEEL\n")
        f.write("*Elastic\n")
        f.write("210.0, 0.3\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("** BOUNDARY CONDITIONS & STATIC SOLVE\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*Boundary\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("999999, 1, 1, 0.0\n")
        f.write("*Step, name=STATIC_ELASTIC, perturb\n")
        f.write("*Static\n")
        f.write("*Boundary\n")
        f.write(f"999999, 2, 2, {actual_target_uy:.10f}\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("** ELEMENT OUTPUT FOR AUTHENTIC MISESERI RECOVERY\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*Output, field, frequency=1\n")
        f.write("*Element Output, elset=ALL_QUADS\n")
        f.write("S, MISESERI, MISESAVG, EVOL\n")
        f.write("*Node Output\n")
        f.write("U, RF\n")
        f.write("*Output, history, frequency=1\n")
        f.write("*Node Output, nset=N_RP\n")
        f.write("RF2, U2\n")
        f.write("*End Step\n")

    inp_sha = sha256_file(out_inp)

    # Manifest
    manifest = {
        "schema": 1,
        "package_name": "MODE1_C5_COMPANION_MISESERI",
        "job_name": job_name,
        "purpose": (
            "Companion continuum linear-elastic static model on Candidate C5 discretization "
            "(12,996 CPE4 quads, 13,278 nodes) to recover authentic Abaqus MISESERI/MISESAVG "
            "error indicators for causal, same-load Method C C5->C6 adaptive remeshing."
        ),
        "mesh_provenance": {
            "source_deck": str(C5_SOURCE_INP.relative_to(REPO_ROOT)),
            "source_sha256": sha256_file(C5_SOURCE_INP),
            "elements": 12996,
            "nodes": 13278,
            "element_type": "CPE4",
            "duplicate_slit_flank_pairs": 53,
            "ligament_nodes": 62,
            "kinematic_tie_equations": 115
        },
        "loading": {
            "step_name": "STATIC_ELASTIC",
            "perturbation": True,
            "prescribed_u2_mm": actual_target_uy,
            "load_source_fixture": (
                f"Validated checkpoint {cp_info['path']} at uy = {actual_target_uy:.10f} mm"
                if cp_info else f"Parameterized displacement target uy = {actual_target_uy:.10f} mm"
            )
        },
        "material": {
            "name": "STEEL",
            "youngs_modulus_kN_mm2": 210.0,
            "poissons_ratio": 0.3
        },
        "output_fields_requested": ["S", "MISESERI", "MISESAVG", "EVOL", "U", "RF"],
        "files": {
            f"{job_name}.inp": inp_sha
        }
    }

    if cp_info is not None:
        manifest["checkpoint_lineage"] = {
            "consumed_checkpoint_path": cp_info["path"],
            "consumed_checkpoint_sha256": cp_info["sha256"],
            "target_uy_mm": cp_info["target_uy_mm"],
            "baseline_uy_mm": cp_info["baseline_uy_mm"],
            "reaction_force_kN": cp_info["reaction_force_kN"],
            "total_energy_kNmm": cp_info["total_energy_kNmm"],
            "outer_iteration": cp_info["outer_iteration"],
            "coupled_convergence": cp_info["coupled_convergence"],
            "contract": cp_info["contract"]
        }

    manifest_path = output_dir / "PACKAGE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Generated C5 companion deck: {out_inp} (SHA-256: {inp_sha})")
    print(f"Generated manifest: {manifest_path}")

    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build C5 Companion Continuum Deck")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--uy", type=float, default=None, help="Explicit target displacement (testing fallback)")
    parser.add_argument("--checkpoint", type=str, default=None, help="Path to validated accepted checkpoint JSON")
    parser.add_argument("--require-checkpoint-03", action="store_true", help="Strictly enforce Checkpoint 03 dependency")
    parser.add_argument("--job-name", type=str, default="M1_C5_COMPANION_MISESERI")
    args = parser.parse_args()

    checkpoint_arg = Path(args.checkpoint) if args.checkpoint else None
    build_c5_companion_deck(
        Path(args.output_dir),
        displacement_target=args.uy,
        checkpoint_path=checkpoint_arg,
        require_checkpoint_03=args.require_checkpoint_03,
        job_name=args.job_name
    )
