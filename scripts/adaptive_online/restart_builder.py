#!/usr/bin/env python3
"""
Four-Stage Restart Input Deck & Production Package Builder.
Builds complete 4-step restart packages matching the validated Stage-D/E/F architecture:
  Step 1: STATE_INSTALL       (Install mapped u1, u2, u3 and binary H state)
  Step 2: MECH_EQUILIBRATION  (Equilibrate displacement with phase locked)
  Step 3: PHASE_RELEASE       (Release phase locking with IA=20, dt_min=1e-14 baseline, isolated displacement-correction control)
  Step 4: CONTINUATION        (Monotonic shear loading from handoff_u1 to target_u1)

Includes full 3-layer element architecture:
  Layer 1: Phase (U1/U3)
  Layer 2: Displacement (U2/U4)
  Layer 3: Companion Facsimile (CPE4/CPE3) for field extraction and next-cycle decision
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import sys
ROOT = Path(__file__).resolve().parents[2]
CANONICAL_UEL_SOURCE = ROOT / "models/generated/mode_ii/stage_f_topology_batch/M2CORR_STAGE_F_TOPOLOGY_CHANGE_TRANSFER_VAL/f44_mixed_uel_restart_stateinit.for"
APPROVED_EMAIL_DIRECTIVE = "#PBS -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de"

DEFAULT_L0 = 0.015
DEFAULT_GC = 0.0027
DEFAULT_EMOD = 210.0
DEFAULT_ENU = 0.30
DEFAULT_PARK = 1.0e-7
DEFAULT_THICKNESS = 1.0
DEFAULT_PASSIVE_E = 1.0e-11
DEFAULT_DEPVAR = 18


def sha256_file(path: Path) -> str:
    if not Path(path).is_file():
        return "FILE_NOT_FOUND"
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_four_stage_restart_package(
    target_mesh_data: Dict[str, Any],
    cycle_id: str,
    handoff_u1: float,
    target_u1: float,
    output_dir: Path,
    target_prefix: str,
    source_job_id: str = "PREVIOUS_CYCLE",
    l0: float = DEFAULT_L0,
    gc: float = DEFAULT_GC,
    emod: float = DEFAULT_EMOD,
    enu: float = DEFAULT_ENU,
    park: float = DEFAULT_PARK,
    thickness: float = DEFAULT_THICKNESS,
    cpus: int = 1,
    memory: str = "16gb",
    walltime: str = "01:00:00",
    queue: str = "entry_imfdfkmq",
    datacheck_mode: bool = False
) -> Dict[str, Any]:
    """
    Assembles complete 4-stage restart execution package with 3-layer architecture.
    """
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    job_name = f"M2ADAPT_{cycle_id.upper()}_RESTART"
    nodes = target_mesh_data["nodes"]
    elements = target_mesh_data["elements"]
    node_sets = target_mesh_data["node_sets"]
    n_phys = len(elements)
    
    quad_elements = {eid: conn for eid, conn in elements.items() if len(conn) == 4}
    tri_elements = {eid: conn for eid, conn in elements.items() if len(conn) == 3}
    n_quads = len(quad_elements)
    n_tris = len(tri_elements)

    rp_id = target_mesh_data.get("rp_id", 99999)
    rp_coords = target_mesh_data.get("rp_coords", (0.0, 0.6, 0.0))

    # 1. Create MODE_STAGED.flag
    staged_flag_path = output_dir / "MODE_STAGED.flag"
    staged_flag_path.write_bytes(b"EXPLICIT_MODE = 1 (STAGED_TRANSFER_RESTART)\n")

    # 2. Copy Canonical UEL Subroutine
    target_uel_path = output_dir / "f44_mixed_uel_restart_stateinit.for"
    if CANONICAL_UEL_SOURCE.is_file():
        target_uel_path.write_bytes(CANONICAL_UEL_SOURCE.read_bytes())
    else:
        target_uel_path.write_bytes(b"C Minimal stub\n")

    # 3. Generate 4-Stage Restart INP Deck with Complete 3-Layer Model
    inp_path = output_dir / f"{job_name}.inp"
    lines: List[str] = []

    lines.append("*Heading")
    lines.append(f" {job_name}: 4-Stage Adaptive Remeshing Restart ({cycle_id})")
    lines.append(f"** Handoff Displacement U1 = {handoff_u1:.8f} mm -> Target Displacement U1 = {target_u1:.8f} mm")
    lines.append(f"** Physical elements = {n_phys} (Quads: {n_quads}, Tris: {n_tris}), Physical nodes = {len(nodes)}")
    lines.append(f"** Total Layered elements = {3 * n_phys}")
    lines.append(f"** Sequence: STATE_INSTALL -> MECH_EQUILIBRATION -> PHASE_RELEASE (IA=20, dt_min=1e-14) -> CONTINUATION")
    lines.append(f"** UEL Mode: PROPS(7) = 1.0 (Staged Transfer Restart)")
    lines.append("*Preprint, echo=NO, model=NO, history=NO, contact=NO")
    lines.append("**")

    # User Elements
    if n_quads > 0:
        lines.append(f"*User Element, nodes=4, type=U1, properties=7, coordinates=2, VARIABLES={DEFAULT_DEPVAR}, UNSYMM")
        lines.append(" 3")
        lines.append(f"*User Element, nodes=4, type=U2, properties=7, coordinates=2, VARIABLES={DEFAULT_DEPVAR}, UNSYMM")
        lines.append(" 1, 2")
    if n_tris > 0:
        lines.append(f"*User Element, nodes=3, type=U3, properties=7, coordinates=2, VARIABLES={DEFAULT_DEPVAR}, UNSYMM")
        lines.append(" 3")
        lines.append(f"*User Element, nodes=3, type=U4, properties=7, coordinates=2, VARIABLES={DEFAULT_DEPVAR}, UNSYMM")
        lines.append(" 1, 2")

    # Nodes
    lines.append("*Node")
    for nid in sorted(nodes.keys()):
        x, y = nodes[nid]
        lines.append(f" {nid:7d}, {x:18.10e}, {y:18.10e}")
    lines.append(f" {rp_id:7d}, {rp_coords[0]:18.10e}, {rp_coords[1]:18.10e}, {rp_coords[2]:18.10e}")

    # Layer 1: Phase Elements (1 .. NPHYS)
    lines.append(f"** Layer 1: Phase Elements (1 .. {n_phys})")
    if n_quads > 0:
        lines.append("*Element, type=U1, elset=PHASE_QUAD")
        for eid in sorted(quad_elements.keys()):
            conn = quad_elements[eid]
            lines.append(f" {eid:7d}, " + ", ".join(f"{n:7d}" for n in conn))
    if n_tris > 0:
        lines.append("*Element, type=U3, elset=PHASE_TRI")
        for eid in sorted(tri_elements.keys()):
            conn = tri_elements[eid]
            lines.append(f" {eid:7d}, " + ", ".join(f"{n:7d}" for n in conn))

    # Layer 2: Displacement Elements (NPHYS+1 .. 2*NPHYS)
    lines.append(f"** Layer 2: Displacement Elements ({n_phys + 1} .. {2 * n_phys})")
    if n_quads > 0:
        lines.append("*Element, type=U2, elset=DISP_QUAD")
        for eid in sorted(quad_elements.keys()):
            conn = quad_elements[eid]
            mech_eid = n_phys + eid
            lines.append(f" {mech_eid:7d}, " + ", ".join(f"{n:7d}" for n in conn))
    if n_tris > 0:
        lines.append("*Element, type=U4, elset=DISP_TRI")
        for eid in sorted(tri_elements.keys()):
            conn = tri_elements[eid]
            mech_eid = n_phys + eid
            lines.append(f" {mech_eid:7d}, " + ", ".join(f"{n:7d}" for n in conn))

    # Layer 3: Companion Facsimile Output Elements (2*NPHYS+1 .. 3*NPHYS)
    lines.append(f"** Layer 3: Companion Facsimile Output Elements ({2 * n_phys + 1} .. {3 * n_phys})")
    if n_quads > 0:
        lines.append("*Element, type=CPE4, elset=UMAT_QUAD")
        for eid in sorted(quad_elements.keys()):
            conn = quad_elements[eid]
            vis_eid = 2 * n_phys + eid
            lines.append(f" {vis_eid:7d}, " + ", ".join(f"{n:7d}" for n in conn))
    if n_tris > 0:
        lines.append("*Element, type=CPE3, elset=UMAT_TRI")
        for eid in sorted(tri_elements.keys()):
            conn = tri_elements[eid]
            vis_eid = 2 * n_phys + eid
            lines.append(f" {vis_eid:7d}, " + ", ".join(f"{n:7d}" for n in conn))

    # Aggregate Sets
    lines.append("** Aggregate Element Sets")
    lines.append("*Elset, elset=PHASE")
    if n_quads > 0: lines.append(" PHASE_QUAD")
    if n_tris > 0: lines.append(" PHASE_TRI")

    lines.append("*Elset, elset=DISP")
    if n_quads > 0: lines.append(" DISP_QUAD")
    if n_tris > 0: lines.append(" DISP_TRI")

    lines.append("*Elset, elset=UMATELEM")
    if n_quads > 0: lines.append(" UMAT_QUAD")
    if n_tris > 0: lines.append(" UMAT_TRI")

    lines.append("*Elset, elset=All_elem\n UMATELEM")

    # Node sets
    for nset_name in ["bottom_nodes", "top_nodes", "left_nodes", "right_nodes"]:
        if nset_name in node_sets:
            items = node_sets[nset_name]
            lines.append(f"*Nset, nset={nset_name}")
            for i in range(0, len(items), 16):
                chunk = items[i:i + 16]
                lines.append(" " + ", ".join(f"{nid:7d}" for nid in chunk))

    lines.append(f"*Nset, nset=RP\n {rp_id:7d}")

    # UEL Properties (PROPS(7) = 1.0 for Staged Transfer Restart)
    if n_quads > 0:
        lines.append("*UEL Property, elset=PHASE_QUAD")
        lines.append(f" {l0:.6e}, {gc:.6e}, {emod:.6e}, {enu:.6e}, {park:.6e}, {n_phys:.1f}, 1.0")
        lines.append("*UEL Property, elset=DISP_QUAD")
        lines.append(f" {l0:.6e}, {gc:.6e}, {emod:.6e}, {enu:.6e}, {park:.6e}, {n_phys:.1f}, 1.0")

    if n_tris > 0:
        lines.append("*UEL Property, elset=PHASE_TRI")
        lines.append(f" {l0:.6e}, {gc:.6e}, {emod:.6e}, {enu:.6e}, {park:.6e}, {n_phys:.1f}, 1.0")
        lines.append("*UEL Property, elset=DISP_TRI")
        lines.append(f" {l0:.6e}, {gc:.6e}, {emod:.6e}, {enu:.6e}, {park:.6e}, {n_phys:.1f}, 1.0")

    # Companion Solid Sections & Materials
    if n_quads > 0:
        lines.append("*Solid Section, elset=UMAT_QUAD, material=MAT_QUAD_FACSIMILE")
        lines.append(f" {thickness:.6e}")
        lines.append("*Material, name=MAT_QUAD_FACSIMILE")
        lines.append(f"*Depvar\n {DEFAULT_DEPVAR}")
        lines.append(f"*User Material, constants=4\n {DEFAULT_PASSIVE_E:.6e}, {DEFAULT_ENU:.6e}, {n_phys:.1f}, 4.0")

    if n_tris > 0:
        lines.append("*Solid Section, elset=UMAT_TRI, material=MAT_TRI_FACSIMILE")
        lines.append(f" {thickness:.6e}")
        lines.append("*Material, name=MAT_TRI_FACSIMILE")
        lines.append(f"*Depvar\n {DEFAULT_DEPVAR}")
        lines.append(f"*User Material, constants=4\n {DEFAULT_PASSIVE_E:.6e}, {DEFAULT_ENU:.6e}, {n_phys:.1f}, 3.0")

    # Mode-II Shear Coupling Equations
    lines.append("** Mode-II Shear Coupling Equations (top_nodes U1 -> RP U1)")
    for nid in node_sets.get("top_nodes", []):
        lines.append("*Equation\n 2")
        lines.append(f" {nid:d}, 1, 1.0, {rp_id:d}, 1, -1.0")

    # --------------------------------------------------------------------------
    # STEP 1: STATE_INSTALL
    # --------------------------------------------------------------------------
    lines.append("** ==========================================================")
    lines.append("** STEP 1: State Installation & Binary History Ingestion")
    lines.append("** ==========================================================")
    lines.append("*Step, name=STATE_INSTALL, nlgeom=NO, inc=10")
    lines.append("*Static\n 1.0, 1.0, 1.0e-5, 1.0")
    lines.append("*Boundary, op=NEW")
    lines.append(f"*Include, input={target_prefix}_STATE_INSTALL_BOUNDARY.inp")
    lines.append("*Output, field, freq=1")
    lines.append("*Node Output, nset=RP\n U, RF")
    lines.append("*End Step")

    # --------------------------------------------------------------------------
    # STEP 2: MECH_EQUILIBRATION
    # --------------------------------------------------------------------------
    lines.append("** ==========================================================")
    lines.append("** STEP 2: Mechanical Equilibration (Phase Field Locked)")
    lines.append("** ==========================================================")
    lines.append("*Step, name=MECH_EQUILIBRATION, nlgeom=NO, inc=100")
    lines.append("*Static\n 1.0, 1.0, 1.0e-5, 1.0")
    lines.append("*Boundary, op=NEW")
    lines.append(" bottom_nodes, 1, 2, 0.0")
    lines.append(f" RP, 1, 1, {handoff_u1:.12e}")
    lines.append(" RP, 2, 2, 0.0")
    lines.append(f"*Include, input={target_prefix}_U3_ONLY_BOUNDARY.inp")
    lines.append("*Output, field, freq=1")
    lines.append("*Node Output, nset=RP\n U, RF")
    lines.append("*End Step")

    # --------------------------------------------------------------------------
    # STEP 3: PHASE_RELEASE (Validated Stage-D/E/F Baseline + Isolated Field Control)
    # --------------------------------------------------------------------------
    lines.append("** ==========================================================")
    lines.append("** STEP 3: Phase Field Release & Equilibrium (IA=25, dt_min=1e-14)")
    lines.append("** ==========================================================")
    lines.append("*Step, name=PHASE_RELEASE, nlgeom=NO, inc=500")
    lines.append("*Static\n 0.001, 1.0, 1.0e-14, 1.0")
    lines.append("*Controls, parameters=time incrementation")
    lines.append(" 25, 25, 25, 25, 25, 4, 50, 25")
    lines.append("*Controls, parameters=field, field=displacement")
    lines.append(" 0.01, 10.0")
    lines.append("*Controls, parameters=field, field=temperature")
    lines.append(" 0.01, 10.0")
    lines.append("*Boundary, op=NEW")
    lines.append(" bottom_nodes, 1, 2, 0.0")
    lines.append(f" RP, 1, 1, {handoff_u1:.12e}")
    lines.append(" RP, 2, 2, 0.0")
    lines.append("*Output, field, freq=1")
    lines.append("*Node Output, nset=RP\n U, RF")
    lines.append("*End Step")

    # --------------------------------------------------------------------------
    # STEP 4: CONTINUATION (Validated Stage-D/E/F Controls)
    # --------------------------------------------------------------------------
    lines.append("** ==========================================================")
    lines.append(f"** STEP 4: Continuation Monotonic Shear ({handoff_u1:.6f} mm -> {target_u1:.6f} mm)")
    lines.append("** ==========================================================")
    lines.append("*Step, name=CONTINUATION, nlgeom=NO, inc=10000")
    lines.append("*Static\n 0.001, 1.0, 1.0e-14, 0.02")
    lines.append("*Controls, parameters=time incrementation")
    lines.append(" 25, 25, 25, 25, 25, 4, 50, 25")
    lines.append("*Controls, parameters=field, field=displacement")
    lines.append(" 0.05, 10.0")
    lines.append("*Controls, parameters=field, field=temperature")
    lines.append(" 0.05, 10.0")
    lines.append("*Boundary, op=MOD")
    lines.append(f" RP, 1, 1, {target_u1:.12e}")
    lines.append(" RP, 2, 2, 0.0")
    lines.append("*Output, field, freq=1")
    lines.append("*Node Output\n U, RF")
    lines.append("*Node Output, nset=RP\n U, RF")
    lines.append("*Element Output, elset=UMATELEM\n S, E, SDV, EVOL")
    lines.append("*Output, history, variable=PRESELECT")
    lines.append("*Energy Output\n ALLAE, ALLCD, ALLIE, ALLKE, ALLPD, ALLSE, ALLWK, ETOTAL")
    lines.append("*End Step")

    deck_content = "\n".join(lines) + "\n"
    with open(inp_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(deck_content)

    inp_hash = sha256_file(inp_path)
    uel_hash = sha256_file(target_uel_path)

    # 4. OpenPBS Script with Full Governance Lifecycle Notifications
    pbs_job_name = f"M2ADAPT_{cycle_id.upper()[:8]}"
    pbs_path = output_dir / f"{job_name}.pbs"
    
    exec_cmd = "abaqus datacheck" if datacheck_mode else "abaqus"
    effective_walltime = "00:30:00" if datacheck_mode else walltime

    pbs_lines = [
        "#!/bin/bash",
        f"#PBS -N {pbs_job_name}",
        f"#PBS -l select=1:ncpus={cpus}:mem={memory}",
        f"#PBS -l walltime={effective_walltime}",
        f"#PBS -q {queue}",
        "#PBS -j oe",
        f"#PBS -o pbs_execution_{job_name}.log",
        "#PBS -m abe",
        APPROVED_EMAIL_DIRECTIVE,
        "",
        "cd $PBS_O_WORKDIR || exit 1",
        "mkdir -p evidence",
        "",
        "# Source authoritative fail-closed dual-channel notification system",
        "NOTIF_SCRIPT=\"\"",
        "for cand in \\",
        "  \"scripts/hpc/notifications/job_notifications.sh\" \\",
        "  \"../../../../scripts/hpc/notifications/job_notifications.sh\" \\",
        "  \"/home/pr21vyci/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh\" \\",
        "  \"${HOME}/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh\"; do",
        "  if [ -f \"$cand\" ]; then",
        "    NOTIF_SCRIPT=\"$cand\"",
        "    break",
        "  fi",
        "done",
        "",
        "if [ -n \"$NOTIF_SCRIPT\" ]; then",
        "  source \"$NOTIF_SCRIPT\"",
        "  notification_install_terminal_trap",
        "  notify_start",
        "fi",
        "",
        "echo '=== Environment ===' > pbs_execution.log",
        "hostname >> pbs_execution.log",
        "date >> pbs_execution.log",
        "",
        "module purge 2>&1 >> pbs_execution.log || true",
        "module load gcc/11.4.0 2>&1 >> pbs_execution.log || true",
        "module load intel/2024.2.0 2>&1 >> pbs_execution.log || true",
        "module load abaqus/2023 2>&1 >> pbs_execution.log || true",
        "",
        f"echo '=== Running Abaqus ({exec_cmd}) {job_name} ===' >> pbs_execution.log",
        f"{exec_cmd} job={job_name} input={job_name}.inp user=f44_mixed_uel_restart_stateinit.for cpus={cpus} interactive >> pbs_execution.log 2>&1",
        "RC=$?",
        "",
        "echo '=== Completed with Return Code: ' $RC ' ===' >> pbs_execution.log",
        "date >> pbs_execution.log",
        "",
        "exit $RC"
    ]
    with open(pbs_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(pbs_lines) + "\n")
    pbs_hash = sha256_file(pbs_path)

    # 5. Guarded Submit Wrapper with Preflight SHA Checks
    wrapper_path = output_dir / f"submit_{job_name.lower()}.sh"
    wrapper_lines = [
        "#!/bin/bash",
        f"# Guarded submit wrapper for {job_name}",
        "set -euo pipefail",
        "",
        f'EXPECTED_INP_SHA="{inp_hash}"',
        f'EXPECTED_UEL_SHA="{uel_hash}"',
        f'EXPECTED_PBS_SHA="{pbs_hash}"',
        "",
        f'ACTUAL_INP_SHA=$(sha256sum {job_name}.inp | awk \'{{print $1}}\')',
        'ACTUAL_UEL_SHA=$(sha256sum f44_mixed_uel_restart_stateinit.for | awk \'{print $1}\')',
        f'ACTUAL_PBS_SHA=$(sha256sum {job_name}.pbs | awk \'{{print $1}}\')',
        "",
        'if [ "$ACTUAL_INP_SHA" != "$EXPECTED_INP_SHA" ]; then echo "ERROR: INP SHA mismatch!"; exit 1; fi',
        'if [ "$ACTUAL_UEL_SHA" != "$EXPECTED_UEL_SHA" ]; then echo "ERROR: UEL SHA mismatch!"; exit 1; fi',
        'if [ "$ACTUAL_PBS_SHA" != "$EXPECTED_PBS_SHA" ]; then echo "ERROR: PBS SHA mismatch!"; exit 1; fi',
        "",
        f'echo "Preflight check PASS. Submitting {job_name} to PBS..."',
        f'JOB_ID=$(qsub {job_name}.pbs)',
        'echo "Submitted Job ID: $JOB_ID"',
        'NOTIF_SCRIPT=""',
        'for cand in \\',
        '  "scripts/hpc/notifications/job_notifications.sh\" \\',
        '  \"../../../../scripts/hpc/notifications/job_notifications.sh\" \\',
        '  \"/home/pr21vyci/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh\" \\',
        '  \"${HOME}/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh\"; do',
        '  if [ -f "$cand" ]; then',
        '    NOTIF_SCRIPT="$cand"',
        '    break',
        '  fi',
        'done',
        'if [ -n "$NOTIF_SCRIPT" ]; then',
        '  source "$NOTIF_SCRIPT"',
        f'  notify_submitted "$JOB_ID" "{job_name}" "Submitted to queue {queue}" || true',
        'fi'
    ]
    with open(wrapper_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(wrapper_lines) + "\n")
    wrapper_hash = sha256_file(wrapper_path)

    # 6. Acceptance Contract
    acceptance_contract = {
        "job_name": job_name,
        "cycle_id": cycle_id,
        "handoff_u1_mm": handoff_u1,
        "target_u1_mm": target_u1,
        "datacheck_only": datacheck_mode,
        "max_phase_bound_violations": 0,
        "max_healing_count": 0,
        "max_h_negative_count": 0,
        "max_reaction_force_jump_pct": 2.0,
        "solver_completion_required": not datacheck_mode
    }
    contract_path = output_dir / "RESTART_ACCEPTANCE_CONTRACT.json"
    with open(contract_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(acceptance_contract, f, indent=2)

    # 7. Package Manifest
    package_manifest = {
        "job_name": job_name,
        "cycle_id": cycle_id,
        "source_job_id": source_job_id,
        "datacheck_mode": datacheck_mode,
        "target_mesh": {
            "num_physical_elements": n_phys,
            "num_layered_elements": 3 * n_phys,
            "num_nodes": len(nodes)
        },
        "segment_interval": {
            "handoff_u1_mm": handoff_u1,
            "target_u1_mm": target_u1,
            "delta_u1_mm": target_u1 - handoff_u1
        },
        "hashes": {
            "input_deck_sha256": inp_hash,
            "uel_sha256": uel_hash,
            "pbs_script_sha256": pbs_hash,
            "wrapper_sha256": wrapper_hash
        },
        "resources": {
            "cpus": cpus,
            "memory": memory,
            "walltime": effective_walltime,
            "queue": queue
        }
    }
    manifest_path = output_dir / "PACKAGE_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(package_manifest, f, indent=2)

    return package_manifest

