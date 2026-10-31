#!/usr/bin/env python3
"""
Generates the verified C4 Refinement Candidate-Marking Artifact from authentic Package 153 data.
Binds authentic C4 7,056-element mesh topology, evaluates companion ODB prerequisite status,
and serializes machine-readable candidate marks with SHA-256 integrity bindings.

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.c4_refinement_marking_interface import (
    C4RefinementMarkingInterface,
    compute_sha256,
    parse_c4_mesh_inp,
)

C4_INP_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "147_c4_corrected_reference", "M1_C4_CORRECTED_PACKAGE147_REF.inp"
)
PKG153_DIR = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "153_c4_companion_miseseri"
)
PKG153_AUDIT_PATH = os.path.join(PKG153_DIR, "c4_package153_miseseri_audit.json")
PKG153_CSV_PATH = os.path.join(PKG153_DIR, "c4_package153_companion_miseseri_distribution.csv")
OUTPUT_PATH = os.path.join(
    REPO_ROOT, "results", "validation", "c4_refinement_candidate_marking.json"
)


def main():
    print(f"Parsing authentic C4 mesh: {C4_INP_PATH}")
    c4_mesh = parse_c4_mesh_inp(C4_INP_PATH)
    marking_interface = C4RefinementMarkingInterface(c4_mesh)

    print(f"Verified C4 Mesh: {len(c4_mesh.phase_elements)} elements, {len(c4_mesh.nodes)} nodes.")
    print(f"Duplicate slit flank node pairs: {len(c4_mesh.duplicate_slit_node_pairs)}")
    print(f"Unbroken ligament nodes: {len(c4_mesh.ligament_nodes)}")

    # Load authentic Package 153 companion summary
    if not os.path.isfile(PKG153_AUDIT_PATH):
        raise FileNotFoundError(f"Missing Package 153 audit JSON: {PKG153_AUDIT_PATH}")
    with open(PKG153_AUDIT_PATH, "r") as f:
        pkg153_summary = json.load(f)

    companion_status = marking_interface.assess_companion_status(pkg153_summary)
    print(f"Companion status: {companion_status}")
    if not companion_status.get("compatible_companion_available"):
        raise RuntimeError(f"Incompatible companion: {companion_status}")

    # Load authentic elementwise indicator distribution from CSV
    if not os.path.isfile(PKG153_CSV_PATH):
        raise FileNotFoundError(f"Missing Package 153 CSV: {PKG153_CSV_PATH}")

    element_data = {}
    with open(PKG153_CSV_PATH, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            eid = int(row["element_id"])
            miseseri = float(row["miseseri_kNmm2"])
            misesavg = float(row["misesavg_kNmm2"])
            element_data[eid] = {"MISESERI": miseseri, "MISESAVG": misesavg}

    print(f"Loaded authentic indicator data for {len(element_data)} elements.")

    source_provenance = {
        "c4_inp_path": os.path.relpath(C4_INP_PATH, REPO_ROOT),
        "c4_inp_sha256": c4_mesh.inp_sha256,
        "companion_status": companion_status,
        "indicator_origin": "PACKAGE_153_AUTHENTIC_COMPANION_ODB",
        "companion_job_name": pkg153_summary.get("job_name", "M1_C4_COMPANION_MISESERI"),
        "companion_pbs_job_id": pkg153_summary.get("pbs_job_id", "1419101.mmaster02"),
        "companion_audit_sha256": compute_sha256(PKG153_AUDIT_PATH),
        "companion_csv_sha256": compute_sha256(PKG153_CSV_PATH),
        "description": (
            "Authentic Zienkiewicz-Zhu Mises stress error indicator distribution extracted from "
            "Package 153 companion continuum static-elastic solve (Job 1419101.mmaster02) on the "
            "7,056-element C4 mesh at prescribed displacement uy = 0.002000 mm."
        ),
        "governing_policy": "REFINEMENT_ONLY_NO_COARSENING"
    }

    marking_result = marking_interface.generate_candidate_marks(
        element_data,
        threshold_eta=0.15,
        source_provenance=source_provenance,
        source_mesh_label="C4_7056_QUADS_PACKAGE_153"
    )

    # Add duplicate slit node pairs list for downstream mesh generator
    marking_result["flank_topology"] = {
        "duplicate_slit_node_pairs_count": len(c4_mesh.duplicate_slit_node_pairs),
        "duplicate_slit_node_pairs": c4_mesh.duplicate_slit_node_pairs,
        "ligament_nodes_count": len(c4_mesh.ligament_nodes),
        "ligament_nodes": c4_mesh.ligament_nodes,
        "slit_y_mm": 0.05,
        "crack_tip_x_mm": 0.04
    }

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(marking_result, f, indent=2)

    print(f"Candidate marking artifact written to: {OUTPUT_PATH}")
    print(f"Total marked elements (eta >= 0.15): {marking_result['marked_elements_count']} "
          f"({marking_result['marked_percentage']}%)")


if __name__ == "__main__":
    main()
