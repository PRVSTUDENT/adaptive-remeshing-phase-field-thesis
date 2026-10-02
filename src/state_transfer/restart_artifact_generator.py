#!/usr/bin/env python3
"""
Target Restart Artifact Generator (Repaired for RP Boundary Separation):
Generates all executable restart includes and manifests for the target nonmatching mesh:
  - Mapped Primary State CSV (distinguishing physical vs auxiliary RP nodes)
  - Clean State-Install Boundary Include (U1, U2, U3 for physical nodes; U1 only for RP)
  - Clean U3-Only Boundary Include (physical nodes only, zero RP lines)
  - Mapped Binary Committed State File (SV_PHASE & SV_H)
  - Comprehensive Traceability Manifest
"""

import csv
import json
import hashlib
from typing import Dict, List, Any, Optional
from pathlib import Path

from .history_field_transfer import write_fortran_binary_state


def sha256_file(file_path: Path) -> str:
    """Computes SHA256 hex digest of file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_target_restart_artifacts(
    output_dir: Path,
    target_mesh_name: str,
    node_records: List[Dict[str, Any]],
    target_h_fields: Dict[int, Any],
    target_phase_fields: Dict[int, float],
    source_provenance: Dict[str, Any],
    mapping_summary: Dict[str, Any],
    write_binary: bool = True
) -> Dict[str, Any]:
    """
    Generates all target restart artifacts and records SHA256 hashes.
    Strictly separates physical mesh nodes from auxiliary RP control nodes.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write Mapped Primary State CSV
    primary_csv_path = output_dir / f"{target_mesh_name}_PRIMARY_STATE.csv"
    with open(primary_csv_path, "w", newline="", encoding="utf-8") as f:
        fields = ["target_node_id", "node_type", "x", "y", "U1", "U2", "U3", "source_element_id", "residual", "is_inside"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in node_records:
            writer.writerow({
                "target_node_id": r["target_node_id"],
                "node_type": r.get("node_type", "PHYSICAL_MESH"),
                "x": f"{r['x']:.10f}",
                "y": f"{r['y']:.10f}",
                "U1": f"{r['U1']:.12e}" if r["U1"] is not None else "",
                "U2": f"{r['U2']:.12e}" if r["U2"] is not None else "",
                "U3": f"{r['U3']:.12e}" if r["U3"] is not None else "",
                "source_element_id": r.get("source_element_id") or "",
                "residual": f"{r['residual']:.12e}" if r.get("residual") is not None else "",
                "is_inside": r["is_inside"]
            })

    # 2. Write Clean State-Install Boundary Include (U1, U2, U3 for physical; U1 only for RP)
    # Note: *Boundary keyword is issued in the parent step; this include contains raw data lines.
    state_install_inp_path = output_dir / f"{target_mesh_name}_STATE_INSTALL_BOUNDARY.inp"
    with open(state_install_inp_path, "w", encoding="utf-8") as f:
        f.write("** Repaired Mapped State-Install Boundary Conditions for Target Mesh\n")
        f.write("** Physical Nodes: Prescribe U1, U2, U3\n")
        f.write("** Auxiliary RP Node: Prescribe U1 only (top U2 FREE preserved, no DOF 3)\n")
        for r in node_records:
            nid = r["target_node_id"]
            ntype = r.get("node_type", "PHYSICAL_MESH")
            if ntype == "AUXILIARY_RP":
                if r["U1"] is not None:
                    f.write(f"{nid:8d}, 1, 1, {r['U1']:16.8e}\n")
            elif r["is_inside"] and r["U1"] is not None:
                f.write(f"{nid:8d}, 1, 1, {r['U1']:16.8e}\n")
                f.write(f"{nid:8d}, 2, 2, {r['U2']:16.8e}\n")
                f.write(f"{nid:8d}, 3, 3, {r['U3']:16.8e}\n")

    # 3. Write Clean U3-Only Boundary Include (Physical Nodes Only, NO RP)
    # Note: *Boundary keyword is issued in the parent step; this include contains raw data lines.
    u3_only_inp_path = output_dir / f"{target_mesh_name}_U3_ONLY_BOUNDARY.inp"
    with open(u3_only_inp_path, "w", encoding="utf-8") as f:
        f.write("** Repaired Mapped U3-Only Phase Clamping Boundary Conditions for Target Mesh\n")
        f.write("** Physical Nodes Only (Auxiliary RP excluded)\n")
        for r in node_records:
            nid = r["target_node_id"]
            ntype = r.get("node_type", "PHYSICAL_MESH")
            if ntype != "AUXILIARY_RP" and r["is_inside"] and r["U3"] is not None:
                f.write(f"{nid:8d}, 3, 3, {r['U3']:16.8e}\n")

    # 4. Write Mapped Binary Committed State File (if requested)
    binary_state_path = output_dir / f"{target_mesh_name}_SOURCE_STATE.bin"
    binary_state_hash = None
    if write_binary:
        write_fortran_binary_state(
            str(binary_state_path),
            target_phase_fields,
            target_h_fields,
            n_capacity=100000
        )
        binary_state_hash = sha256_file(binary_state_path)

    # Compute Artifact Hashes
    primary_csv_hash = sha256_file(primary_csv_path)
    state_install_hash = sha256_file(state_install_inp_path)
    u3_only_hash = sha256_file(u3_only_inp_path)

    # 5. Write Traceability Manifest
    manifest = {
        "target_mesh_name": target_mesh_name,
        "source_provenance": source_provenance,
        "mapping_summary": mapping_summary,
        "generated_artifacts": {
            "primary_state_csv": {
                "filename": primary_csv_path.name,
                "sha256": primary_csv_hash
            },
            "state_install_boundary_inp": {
                "filename": state_install_inp_path.name,
                "sha256": state_install_hash
            },
            "u3_only_boundary_inp": {
                "filename": u3_only_inp_path.name,
                "sha256": u3_only_hash
            }
        },
        "transfer_algorithm": {
            "spatial_search": "SpatialGridIndex with Newton-Raphson inverse isoparametric mapping",
            "primary_fields_interpolation": "C0 continuous bilinear quad shape functions (physical nodes only)",
            "rp_boundary_separation": "RP node prescribed U1 only; DOF 2 and DOF 3 excluded",
            "history_fields_interpolation": "Gauss-point normalized isoparametric interpolation",
            "inside_tolerance": 1.0e-6
        }
    }

    if binary_state_hash:
        manifest["generated_artifacts"]["committed_binary_state"] = {
            "filename": binary_state_path.name,
            "sha256": binary_state_hash
        }

    manifest_path = output_dir / f"{target_mesh_name}_TRANSFER_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    manifest_hash = sha256_file(manifest_path)
    manifest["manifest_sha256"] = manifest_hash

    return manifest
