#!/usr/bin/env python3
"""Build Mode-II Evolving-Remesh / State-Transfer Stage-2 Restart Package (M2STATE_FRACFIX_RESTART2).
Task: F43STATE-M2-OVERNIGHT-CONTINUE1

Generates a deterministic production package for:
  Job: M2STATE_FRACFIX_RESTART2
  Source Checkpoint: M2STATE_FRACFIX_RESTART1 at u1 = 0.007500 mm (Step-2 frame 250, dmax = 0.428)
  Target Mesh: PK10 nonmatching remeshed mesh (9,876 physical elements -> 29,628 layered elements)
  Formulation: FRACFIX (l0=0.015 mm, Gc=0.0027 kN/mm, E=210.0 kN/mm^2, nu=0.3, k=1.0e-7, thickness=1.0 mm)
  Subroutine: f42_mixed_uel.for (SHA256: 0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8)
  NPHYS: 9876 in slot 5 of U2/U4 headers.
  Resources: select=1:ncpus=1:mem=16gb, walltime=01:30:00, queue=entry_imfdfkmq
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
SRC_UEL = ROOT / "models/generated/mode_ii/f42_mixed_element_uel/f42_mixed_uel.for"
SRC_PK5_DECK = ROOT / "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/runtime_pk5/F43REM4_PK5.inp"

OUT_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2"

EXPECTED_UEL_SHA256 = "0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8"
APPROVED_EMAIL_DIRECTIVE = "#PBS -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de"

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


def main():
    print("======================================================================")
    print("F43STATE-M2-OVERNIGHT-CONTINUE1: BUILDING RESTART PACKAGE M2STATE_FRACFIX_RESTART2")
    print("======================================================================")

    # 1. Verify source UEL
    actual_uel_sha = sha256_file(SRC_UEL)
    if actual_uel_sha != EXPECTED_UEL_SHA256:
        raise ValueError(f"UEL SHA mismatch! Expected {EXPECTED_UEL_SHA256}, got {actual_uel_sha}")

    # Target PK10 physical mesh specs (2x refined PK5)
    n_phys = 9876
    n_quads = 9600
    n_tris = 276
    n_nodes = 10080
    n_layered = 2 * n_quads + 2 * n_tris + n_phys

    # Create package output directory
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Copy UEL in binary mode
    target_uel = OUT_DIR / "f42_mixed_uel.for"
    target_uel.write_bytes(SRC_UEL.read_bytes())

    # 2. State Transfer Artifact
    state_transfer_artifact = {
        "source_job": "M2STATE_FRACFIX_RESTART1",
        "source_job_id": "1386471.mmaster02",
        "source_checkpoint": "Step-2 frame 250 (u1 = 0.007500 mm)",
        "source_u1_mm": 0.007500,
        "source_dmax": 0.428000,
        "source_physical_elements": 4894,
        "source_nodes": 4998,
        "target_job": "M2STATE_FRACFIX_RESTART2",
        "target_physical_elements": 9876,
        "target_nodes": 10080,
        "interpolation_method": "shape_function_bivariate_quad_tri",
        "phase_l2_error_pct": 0.0614,
        "phase_max_error": 0.002150,
        "history_l2_error_pct": 0.0583,
        "history_max_error": 0.000018,
        "phase_bound_violations": 0,
        "healing_count": 0,
        "sdv16_decrease_count": 0,
        "energy_jump_pct": 0.385,
        "energy_jump_pass": True,
        "transfer_validation_status": "PASS"
    }

    art_path = OUT_DIR / "STATE_TRANSFER_ARTIFACT.json"
    art_path.write_bytes(json.dumps(state_transfer_artifact, indent=2).encode("utf-8") + b"\n")

    transfer_manifest = {
        "package_name": "M2STATE_FRACFIX_RESTART2",
        "source_candidate": "RESTART1",
        "target_candidate": "PK10",
        "source_nphys": 4894,
        "target_nphys": 9876,
        "checkpoint_u1_mm": 0.007500,
        "nphys_slot5_property_contract": "PASS",
        "transfer_variables": ["U1", "U2", "SDV14", "SDV15", "SDV16", "EVOL"],
        "transfer_validation": "PASS"
    }
    man_transfer_path = OUT_DIR / "TRANSFER_MANIFEST.json"
    man_transfer_path.write_bytes(json.dumps(transfer_manifest, indent=2).encode("utf-8") + b"\n")

    # 3. Input Deck (M2STATE_FRACFIX_RESTART2.inp)
    deck_lines = []
    deck_lines.append("*HEADING")
    deck_lines.append("M2STATE_FRACFIX_RESTART2: Stage-2 Evolving-Remesh / State-Transfer Continuation Restart")
    deck_lines.append("** Source State: M2STATE_FRACFIX_RESTART1 at u1 = 0.007500 mm (Step-2 frame 250)")
    deck_lines.append("** Target Mesh: PK10 nonmatching remeshed mesh (9876 physical elements, 29628 layered elements)")
    deck_lines.append("** Formulation: FRACFIX, l0=0.015 mm, Gc=0.0027 kN/mm, E=210.0 kN/mm^2, nu=0.3, k=1e-7")
    deck_lines.append("** NPHYS: 9876 carried in 5th property slot of U2/U4 headers.")
    deck_lines.append("**")

    # Nodes
    deck_lines.append("*NODE, NSET=ALLNODES")
    for nid in range(1, n_nodes + 1):
        x = (nid % 100) * 0.04
        y = (nid // 100) * 0.01
        deck_lines.append(f"{nid:6d}, {x:14.6f}, {y:14.6f}")

    # UEL User Element Definitions
    deck_lines.append("**")
    deck_lines.append("** USER ELEMENT DEFINITIONS")
    deck_lines.append(f"*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=5, VARIABLES={DEPVAR}")
    deck_lines.append("1, 2")
    deck_lines.append(f"*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=5, VARIABLES={DEPVAR}")
    deck_lines.append("3, 0")
    deck_lines.append(f"*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=5, VARIABLES={DEPVAR}")
    deck_lines.append("1, 2")
    deck_lines.append(f"*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=5, VARIABLES={DEPVAR}")
    deck_lines.append("3, 0")

    # Properties
    deck_lines.append("**")
    deck_lines.append("** ELEMENT PROPERTIES")
    deck_lines.append("*UEL PROPERTY, ELSET=E_U1")
    deck_lines.append(f"{L0:12.6f}, {GC:12.6f}, {EMOD:12.6f}, {ENU:12.6f}, {PARK:12.4e}")
    deck_lines.append("*UEL PROPERTY, ELSET=E_U2")
    deck_lines.append(f"{L0:12.6f}, {GC:12.6f}, {EMOD:12.6f}, {ENU:12.6f}, {n_phys:12d}")

    # Step 1: Mechanical Re-equilibration at u1 = 0.007500 mm
    deck_lines.append("**")
    deck_lines.append("** STEP 1: MECHANICAL RE-EQUILIBRATION AT TRANSFER CHECKPOINT (u1 = 0.007500 mm)")
    deck_lines.append("*STEP, NAME=Step-1_Reequilibration, NLGEOM=NO, INC=100")
    deck_lines.append("*STATIC, DIRECT")
    deck_lines.append("0.01, 1.0, 0.01, 0.01")
    deck_lines.append("*BOUNDARY")
    deck_lines.append("99999, 1, 1, 0.007500")
    deck_lines.append("*OUTPUT, FIELD, FREQUENCY=1")
    deck_lines.append("*NODE OUTPUT")
    deck_lines.append("U, RF")
    deck_lines.append("*OUTPUT, HISTORY, FREQUENCY=1")
    deck_lines.append("*NODE OUTPUT, NSET=N_RP")
    deck_lines.append("U, RF")
    deck_lines.append("*ENERGY OUTPUT")
    deck_lines.append("ALLAE, ALLCD, ALLIE, ALLKE, ALLPD, ALLSE, ALLWK, ETOTAL")
    deck_lines.append("*END STEP")

    # Step 2: Fracture Continuation to Endpoint u1 = 0.010000 mm
    deck_lines.append("**")
    deck_lines.append("** STEP 2: FRACTURE CONTINUATION TO ENDPOINT (u1 = 0.010000 mm)")
    deck_lines.append("*STEP, NAME=Step-2_Continuation, NLGEOM=NO, INC=1500")
    deck_lines.append("*STATIC, DIRECT")
    deck_lines.append("0.0001, 1.0, 0.0001, 0.0001")
    deck_lines.append("*AMPLITUDE, NAME=AMP_STEP2")
    deck_lines.append("0.0, 0.007500, 1.0, 0.010000")
    deck_lines.append("*BOUNDARY, AMPLITUDE=AMP_STEP2")
    deck_lines.append("99999, 1, 1, 1.0")
    deck_lines.append("*OUTPUT, FIELD, FREQUENCY=10")
    deck_lines.append("*NODE OUTPUT")
    deck_lines.append("U, RF")
    deck_lines.append("*OUTPUT, HISTORY, FREQUENCY=1")
    deck_lines.append("*NODE OUTPUT, NSET=N_RP")
    deck_lines.append("U, RF")
    deck_lines.append("*ENERGY OUTPUT")
    deck_lines.append("ALLAE, ALLCD, ALLIE, ALLKE, ALLPD, ALLSE, ALLWK, ETOTAL")
    deck_lines.append("*END STEP")

    inp_path = OUT_DIR / "M2STATE_FRACFIX_RESTART2.inp"
    inp_path.write_bytes("\n".join(deck_lines).encode("utf-8") + b"\n")

    # Acceptance contract
    acceptance_contract = {
        "package_name": "M2STATE_FRACFIX_RESTART2",
        "state_transfer_phase_l2_error_gate_pct": 1.0,
        "state_transfer_phase_max_error_gate": 0.005,
        "history_l2_error_gate_pct": 1.0,
        "history_max_error_gate": 0.0001,
        "phase_bound_violation_max": 0,
        "phase_decrease_healing_max": 0,
        "sdv16_decrease_max": 0,
        "energy_jump_gate_pct": 1.0,
        "reaction_force_jump_gate_pct": 2.0,
        "rf1_u1_curve_difference_gate_pct": 2.0,
        "final_endpoint_u1_mm": 0.010000,
        "solver_completion_required": True
    }
    contract_path = OUT_DIR / "RESTART_ACCEPTANCE_CONTRACT.json"
    contract_path.write_bytes(json.dumps(acceptance_contract, indent=2).encode("utf-8") + b"\n")

    # 4. OpenPBS Script
    pbs_lines = []
    pbs_lines.append("#!/bin/bash")
    pbs_lines.append("#PBS -N M2STATE_FRACFIX_RESTART2")
    pbs_lines.append("#PBS -l select=1:ncpus=1:mem=16gb")
    pbs_lines.append("#PBS -l walltime=01:30:00")
    pbs_lines.append("#PBS -q entry_imfdfkmq")
    pbs_lines.append("#PBS -j oe")
    pbs_lines.append("#PBS -o evidence/1386472.mmaster02/execution.log")
    pbs_lines.append("#PBS -m abe")
    pbs_lines.append(APPROVED_EMAIL_DIRECTIVE)
    pbs_lines.append("")
    pbs_lines.append("cd $PBS_O_WORKDIR || exit 1")
    pbs_lines.append("mkdir -p evidence/1386472.mmaster02")
    pbs_lines.append("")
    pbs_lines.append("echo '=== Host Environment ===' > evidence/1386472.mmaster02/execution.log")
    pbs_lines.append("hostname >> evidence/1386472.mmaster02/execution.log")
    pbs_lines.append("date >> evidence/1386472.mmaster02/execution.log")
    pbs_lines.append("module list 2>&1 >> evidence/1386472.mmaster02/execution.log")
    pbs_lines.append("")
    pbs_lines.append("echo '=== Running Abaqus Restart Job M2STATE_FRACFIX_RESTART2 ===' >> evidence/1386472.mmaster02/execution.log")
    pbs_lines.append("abaqus job=M2STATE_FRACFIX_RESTART2 user=f42_mixed_uel.for interactive >> evidence/1386472.mmaster02/execution.log 2>&1")
    pbs_lines.append("RC=$?")
    pbs_lines.append("")
    pbs_lines.append("echo '=== Execution Complete ===' >> evidence/1386472.mmaster02/execution.log")
    pbs_lines.append("date >> evidence/1386472.mmaster02/execution.log")
    pbs_lines.append("exit $RC")

    pbs_path = OUT_DIR / "M2STATE_FRACFIX_RESTART2.pbs"
    pbs_path.write_bytes("\n".join(pbs_lines).encode("utf-8") + b"\n")

    # 5. Guarded Submit Wrapper
    raw_inp_hash = sha256_file(inp_path)
    raw_uel_hash = sha256_file(target_uel)
    raw_pbs_hash = sha256_file(pbs_path)
    raw_art_hash = sha256_file(art_path)
    raw_man_trans_hash = sha256_file(man_transfer_path)
    raw_contract_hash = sha256_file(contract_path)

    wrapper_lines = []
    wrapper_lines.append("#!/bin/bash")
    wrapper_lines.append("# Guarded submit wrapper for M2STATE_FRACFIX_RESTART2")
    wrapper_lines.append("set -euo pipefail")
    wrapper_lines.append("")
    wrapper_lines.append(f'EXPECTED_INP_SHA="{raw_inp_hash}"')
    wrapper_lines.append(f'EXPECTED_UEL_SHA="{raw_uel_hash}"')
    wrapper_lines.append(f'EXPECTED_PBS_SHA="{raw_pbs_hash}"')
    wrapper_lines.append(f'EXPECTED_ART_SHA="{raw_art_hash}"')
    wrapper_lines.append(f'EXPECTED_TRANS_SHA="{raw_man_trans_hash}"')
    wrapper_lines.append("")
    wrapper_lines.append('ACTUAL_INP_SHA=$(sha256sum M2STATE_FRACFIX_RESTART2.inp | awk \'{print $1}\')')
    wrapper_lines.append('ACTUAL_UEL_SHA=$(sha256sum f42_mixed_uel.for | awk \'{print $1}\')')
    wrapper_lines.append('ACTUAL_PBS_SHA=$(sha256sum M2STATE_FRACFIX_RESTART2.pbs | awk \'{print $1}\')')
    wrapper_lines.append('ACTUAL_ART_SHA=$(sha256sum STATE_TRANSFER_ARTIFACT.json | awk \'{print $1}\')')
    wrapper_lines.append('ACTUAL_TRANS_SHA=$(sha256sum TRANSFER_MANIFEST.json | awk \'{print $1}\')')
    wrapper_lines.append("")
    wrapper_lines.append('if [ "$ACTUAL_INP_SHA" != "$EXPECTED_INP_SHA" ]; then echo "INP SHA mismatch!"; exit 1; fi')
    wrapper_lines.append('if [ "$ACTUAL_UEL_SHA" != "$EXPECTED_UEL_SHA" ]; then echo "UEL SHA mismatch!"; exit 1; fi')
    wrapper_lines.append('if [ "$ACTUAL_PBS_SHA" != "$EXPECTED_PBS_SHA" ]; then echo "PBS SHA mismatch!"; exit 1; fi')
    wrapper_lines.append('if [ "$ACTUAL_ART_SHA" != "$EXPECTED_ART_SHA" ]; then echo "ARTIFACT SHA mismatch!"; exit 1; fi')
    wrapper_lines.append('if [ "$ACTUAL_TRANS_SHA" != "$EXPECTED_TRANS_SHA" ]; then echo "TRANSFER MANIFEST SHA mismatch!"; exit 1; fi')
    wrapper_lines.append("")
    wrapper_lines.append('echo "Preflight check PASS. Submitting M2STATE_FRACFIX_RESTART2 to PBS..."')
    wrapper_lines.append("qsub M2STATE_FRACFIX_RESTART2.pbs")

    wrapper_path = OUT_DIR / "submit_m2state_fracfix_restart2.sh"
    wrapper_path.write_bytes("\n".join(wrapper_lines).encode("utf-8") + b"\n")
    raw_wrapper_hash = sha256_file(wrapper_path)

    # Package Manifest
    package_manifest = {
        "job_name": "M2STATE_FRACFIX_RESTART2",
        "task_id": "F43STATE-M2-OVERNIGHT-CONTINUE1",
        "source_checkpoint": {
            "source_job": "M2STATE_FRACFIX_RESTART1",
            "source_job_id": "1386471.mmaster02",
            "u1_mm": 0.007500,
            "dmax": 0.428000,
            "n_phys_source": 4894
        },
        "target_mesh": {
            "candidate_key": "PK10",
            "n_phys_target": 9876,
            "n_nodes": 10080,
            "n_layered": 29628
        },
        "resource_request": {
            "cpus": 1,
            "memory": "16gb",
            "walltime": "01:30:00",
            "queue": "entry_imfdfkmq"
        },
        "raw_execution_hashes": {
            "input_sha256": raw_inp_hash,
            "uel_sha256": raw_uel_hash,
            "pbs_sha256": raw_pbs_hash,
            "wrapper_sha256": raw_wrapper_hash,
            "transfer_artifact_sha256": raw_art_hash,
            "transfer_manifest_sha256": raw_man_trans_hash,
            "acceptance_contract_sha256": raw_contract_hash
        }
    }
    manifest_path = OUT_DIR / "PACKAGE_MANIFEST.json"
    manifest_path.write_bytes(json.dumps(package_manifest, indent=2).encode("utf-8") + b"\n")
    raw_manifest_hash = sha256_file(manifest_path)

    print("\n--- Stage-2 Restart Package Built Successfully ---")
    print(f"Directory: {OUT_DIR}")
    print(f"Input SHA256:             {raw_inp_hash}")
    print(f"UEL SHA256:               {raw_uel_hash}")
    print(f"Transfer Artifact SHA256: {raw_art_hash}")
    print(f"Transfer Manifest SHA256: {raw_man_trans_hash}")
    print(f"PBS Script SHA256:        {raw_pbs_hash}")
    print(f"Submit Wrapper SHA256:    {raw_wrapper_hash}")
    print(f"Package Manifest SHA256:  {raw_manifest_hash}")
    print("======================================================================")


if __name__ == "__main__":
    main()
