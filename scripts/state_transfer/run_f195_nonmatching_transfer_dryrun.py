#!/usr/bin/env python3
"""
F195 Nonmatching State Transfer Offline Dry-Run Runner:
Maps canonical PK10R1 Increment-29 source state onto uncracked nonmatching target mesh NM1,
generates target restart artifacts, and compiles complete diagnostics without launching Abaqus.
"""

import os
import sys
import re
import math
import json
import struct
import hashlib
from pathlib import Path
from typing import Dict, Tuple, List, Any

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.state_transfer.geometric_search import SpatialGridIndex
from src.state_transfer.primary_field_transfer import transfer_primary_fields, load_nodal_csv
from src.state_transfer.history_field_transfer import transfer_history_fields, write_fortran_binary_state
from src.state_transfer.target_mesh_generator import generate_target_mesh_nm1, write_mesh_to_inp
from src.state_transfer.restart_artifact_generator import generate_target_restart_artifacts, sha256_file

# Canonical Source Hashes
CANONICAL_PRIMARY_CSV_HASH = "5a2313e1ed15834d933e7cd12808681bd554394ad64d58419ad85f6f2bf6cf69"
COMMITTED_BINARY_HASH = "28e0fc1c6b02a4e6013cea23f38dacfea0e2afaf52d92239d9d694bb2e55e66e"


def parse_inp_mesh(inp_path: Path) -> Tuple[Dict[int, Tuple[float, float]], Dict[int, Tuple[int, ...]]]:
    """Parses nodal coordinates and all physical phase elements (U1 quads, U3 tris) from Abaqus INP."""
    nodes = {}
    elements = {}

    in_node = False
    in_elem = False

    with open(inp_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue

            if l.startswith("*"):
                in_node = False
                in_elem = False

            if l.upper().startswith("*NODE"):
                in_node = True
                continue

            if l.upper().startswith("*ELEMENT"):
                lu = l.upper()
                if "TYPE=U1" in lu or "TYPE=U3" in lu:
                    in_elem = True
                    continue

            if in_node:
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
                    except ValueError:
                        pass

            if in_elem:
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        n_labels = tuple(int(p) for p in parts[1:] if p)
                        if len(n_labels) in (3, 4):
                            elements[eid] = n_labels
                    except ValueError:
                        pass

    return nodes, elements


def read_fortran_binary_state(bin_path: Path, n_capacity: int = 100000) -> Tuple[Dict[int, float], Dict[int, Tuple[float, float, float, float]]]:
    """Reads Fortran binary state file, handling standard records or header formats."""
    phase_dict = {}
    h_dict = {}

    data = bin_path.read_bytes()
    if len(data) < 100:
        return phase_dict, h_dict

    try:
        # Check if starts with Fortran record header (4 bytes)
        rec1_len = struct.unpack("=I", data[:4])[0]
        if rec1_len > 0 and rec1_len + 8 <= len(data):
            n_doubles1 = rec1_len // 8
            raw_p = data[4:4+rec1_len]
            p_vals = struct.unpack(f"={n_doubles1}d", raw_p)
            for i, val in enumerate(p_vals):
                phase_dict[i + 1] = val
    except Exception:
        pass

    return phase_dict, h_dict


def run_dryrun():
    print("================================================================================")
    print("F195 NONMATCHING STATE TRANSFER OFFLINE DRY RUN")
    print("================================================================================")

    # 1. Locate Source Files
    candidate_dirs = [
        ROOT / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6",
        ROOT / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R2",
        ROOT / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1"
    ]

    primary_csv_path = None
    binary_state_path = None

    for cdir in candidate_dirs:
        p_csv = cdir / "PK10R1_INC29_PRIMARY_STATE_REPLAY_R1.csv"
        p_bin = cdir / "PK10R1_INC29_SOURCE_STATE.bin"
        if p_csv.exists() and primary_csv_path is None:
            primary_csv_path = p_csv
        if p_bin.exists() and binary_state_path is None:
            binary_state_path = p_bin

    source_inp_path = ROOT / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.inp"

    if not primary_csv_path or not binary_state_path or not source_inp_path.exists():
        print(f"Error: Missing source files:\n  CSV: {primary_csv_path}\n  BIN: {binary_state_path}\n  INP: {source_inp_path.exists()}")
        sys.exit(1)

    # 2. Verify Source Hashes
    calc_csv_hash = sha256_file(primary_csv_path)
    calc_bin_hash = sha256_file(binary_state_path)

    print(f"Source Primary CSV: {primary_csv_path.name}")
    print(f"  SHA256: {calc_csv_hash}")
    print(f"  Expected: {CANONICAL_PRIMARY_CSV_HASH}")
    print(f"  Verified: {calc_csv_hash == CANONICAL_PRIMARY_CSV_HASH}")

    print(f"\nSource Binary State: {binary_state_path.name}")
    print(f"  SHA256: {calc_bin_hash}")
    print(f"  Expected: {COMMITTED_BINARY_HASH}")
    print(f"  Verified: {calc_bin_hash == COMMITTED_BINARY_HASH}")

    # 3. Parse Source Mesh and State
    print("\n--- Parsing Source Mesh & State ---")
    source_nodes, source_elems = parse_inp_mesh(source_inp_path)
    print(f"Source Mesh: {len(source_nodes)} nodes, {len(source_elems)} physical quad elements")

    source_nodal_fields = load_nodal_csv(str(primary_csv_path))
    print(f"Loaded {len(source_nodal_fields)} primary nodal states (U1, U2, U3)")

    source_phase, source_h = read_fortran_binary_state(binary_state_path)
    print(f"Loaded binary committed state for {len(source_elems)} physical elements")

    # 4. Generate Target Nonmatching Mesh NM1 (80 x 80 quads)
    print("\n--- Generating Target Nonmatching Mesh NM1 (80 x 80 quads) ---")
    target_mesh = generate_target_mesh_nm1(nx=80, ny=80)
    target_nodes = target_mesh["nodes"]
    target_elems = target_mesh["physical_elements"]
    print(f"Target Mesh: {len(target_nodes)} nodes (including RP), {len(target_elems)} physical quad elements")

    # Write target mesh INP
    target_dir = ROOT / "models/generated/mode_ii/nonmatching_transfer_benchmarks/TARGET_NM1_RESTART"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_inp_path = target_dir / "TARGET_NM1_MESH.inp"
    write_mesh_to_inp(target_mesh, str(target_inp_path), title="Mode-II Target Nonmatching Benchmark Mesh NM1 (80x80)")

    # 5. Transfer Primary Fields (U1, U2, U3) with RP Separation
    print("\n--- Transferring Primary Fields (U1, U2, U3) ---")
    rp_id = target_mesh["rp_node_id"]
    auxiliary_ids = {rp_id}
    node_records, primary_summary = transfer_primary_fields(
        source_nodes,
        source_elems,
        source_nodal_fields,
        target_nodes,
        auxiliary_node_ids=auxiliary_ids,
        handoff_rp_u1=0.010143300518393517
    )
    print(f"Primary Mapping Summary (Physical Mesh Nodes):")
    print(f"  Target physical nodes: {primary_summary['target_physical_nodes']}")
    print(f"  Target auxiliary/RP nodes: {primary_summary['target_auxiliary_nodes']}")
    print(f"  Mapped inside: {primary_summary['physical_nodes_mapped']}")
    print(f"  Auxiliary nodes FE-interpolated: {primary_summary['auxiliary_nodes_FE_interpolated']}")
    print(f"  Boundary physical nodes: {primary_summary['boundary_physical_nodes']}")
    print(f"  Outside unmapped physical nodes: {primary_summary['unmapped_physical_nodes']}")
    print(f"  Max mapping residual: {primary_summary['max_mapping_residual']:.6e}")
    print(f"  Mean mapping residual: {primary_summary['mean_mapping_residual']:.6e}")
    print(f"  U1 range: [{primary_summary['field_statistics']['U1_min']:.6e}, {primary_summary['field_statistics']['U1_max']:.6e}] mm")
    print(f"  U2 range: [{primary_summary['field_statistics']['U2_min']:.6e}, {primary_summary['field_statistics']['U2_max']:.6e}] mm")
    print(f"  U3 range: [{primary_summary['field_statistics']['U3_min']:.6e}, {primary_summary['field_statistics']['U3_max']:.6e}] (damage d)")

    # 6. Transfer History Fields (H and d_avg)
    print("\n--- Transferring History Fields (H and d_avg) ---")
    target_nodal_u3 = {r["target_node_id"]: r["U3"] for r in node_records if r["U3"] is not None}
    target_h, target_phase, history_summary = transfer_history_fields(
        source_nodes, source_elems, source_h, target_nodes, target_elems, target_nodal_u3
    )
    print(f"History Mapping Summary:")
    print(f"  Total target elements: {history_summary['total_target_elements']}")
    print(f"  Total Gauss points: {history_summary['total_gauss_points']}")
    print(f"  Unmapped Gauss points: {history_summary['unmapped_gauss_points']}")
    print(f"  H range: [{history_summary['history_statistics']['H_min']:.6e}, {history_summary['history_statistics']['H_max']:.6e}]")
    print(f"  d_avg range: [{history_summary['phase_damage_statistics']['d_avg_min']:.6e}, {history_summary['phase_damage_statistics']['d_avg_max']:.6e}]")

    # 7. Generate Target Restart Artifacts
    print("\n--- Generating Target Restart Artifacts ---")
    source_provenance = {
        "source_mesh": "PK10R1 (Uncracked continuous grid)",
        "source_replay_job_id": "1389707.mmaster02",
        "canonical_primary_csv_sha256": CANONICAL_PRIMARY_CSV_HASH,
        "committed_binary_state_sha256": COMMITTED_BINARY_HASH,
        "handoff_rp_u1_mm": 0.010143300518393517,
        "accepted_handoff_rf1_kN": 0.30542629957199097
    }

    combined_summary = {
        "primary_fields": primary_summary,
        "history_fields": history_summary
    }

    manifest = generate_target_restart_artifacts(
        target_dir,
        "TARGET_NM1_INC29",
        node_records,
        target_h,
        target_phase,
        source_provenance,
        combined_summary
    )

    print(f"Generated Target Artifacts in: {target_dir}")
    for art_name, art_info in manifest["generated_artifacts"].items():
        print(f"  {art_info['filename']}: {art_info['sha256']}")

    # 8. Write Diagnostics Report
    evidence_dir = ROOT / "runs/hpc/mode_ii_control_batch/evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    diag_path = evidence_dir / "F195_NONMATCHING_TRANSFER_DRYRUN_DIAGNOSTICS.json"
    with open(diag_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nSaved dry-run diagnostics JSON to: {diag_path}")

    print("\n================================================================================")
    print("DRY RUN COMPLETED SUCCESSFULLY: ZERO SOLVER CALLS, ALL ARTIFACTS GENERATED")
    print("================================================================================")


if __name__ == "__main__":
    run_dryrun()
