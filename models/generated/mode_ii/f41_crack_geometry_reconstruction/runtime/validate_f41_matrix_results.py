#!/usr/bin/env python3
"""
Validate F41 Matrix Results

Validates that F41_CRACK_RECONSTRUCTION_AUDIT.json, F41_TOPOLOGY_MAP.json, and
F41_CAE_RECONSTRUCTION_MATRIX.json satisfy all scientific and technical acceptance criteria.
"""

import json
import os
import sys

def main():
    evidence_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    errors = []

    audit_path = os.path.join(evidence_dir, "F41_CRACK_RECONSTRUCTION_AUDIT.json")
    map_path = os.path.join(evidence_dir, "F41_TOPOLOGY_MAP.json")
    matrix_path = os.path.join(evidence_dir, "F41_CAE_RECONSTRUCTION_MATRIX.json")

    if not os.path.exists(audit_path):
        errors.append("F41_CRACK_RECONSTRUCTION_AUDIT.json missing")
    else:
        try:
            with open(audit_path, 'r') as f:
                audit = json.load(f)

            if audit.get("duplicate_pairs_before") != 15:
                errors.append("duplicate_pairs_before ({0}) is not 15".format(audit.get("duplicate_pairs_before")))
            if audit.get("merged_pair_count") != 15:
                errors.append("merged_pair_count ({0}) is not 15".format(audit.get("merged_pair_count")))
            if audit.get("duplicate_pairs_after") != 0:
                errors.append("duplicate_pairs_after ({0}) is not 0".format(audit.get("duplicate_pairs_after")))
            if audit.get("reconstructed_face_count", 0) < 1:
                errors.append("reconstructed_face_count ({0}) is less than 1".format(audit.get("reconstructed_face_count")))
            if audit.get("crack_geometry_recreated") is not True:
                errors.append("crack_geometry_recreated is not True")
            if audit.get("crack_tip_preserved") is not True:
                errors.append("crack_tip_preserved is not True")
            if audit.get("outer_boundary_preserved") is not True:
                errors.append("outer_boundary_preserved is not True")
            if audit.get("reconstruction_passed") is not True:
                errors.append("reconstruction_passed is not True")

        except Exception as exc:
            errors.append("Failed to parse F41_CRACK_RECONSTRUCTION_AUDIT.json: {0}".format(exc))

    if not os.path.exists(map_path):
        errors.append("F41_TOPOLOGY_MAP.json missing")
    else:
        try:
            with open(map_path, 'r') as f:
                t_map = json.load(f)

            if t_map.get("duplicate_pairs_count") != 15:
                errors.append("F41_TOPOLOGY_MAP duplicate_pairs_count ({0}) is not 15".format(t_map.get("duplicate_pairs_count")))
            pairs_list = t_map.get("node_pairs_mapping", [])
            if len(pairs_list) != 15:
                errors.append("F41_TOPOLOGY_MAP node_pairs_mapping length ({0}) is not 15".format(len(pairs_list)))
        except Exception as exc:
            errors.append("Failed to parse F41_TOPOLOGY_MAP.json: {0}".format(exc))

    if not os.path.exists(matrix_path):
        errors.append("F41_CAE_RECONSTRUCTION_MATRIX.json missing")
    else:
        try:
            with open(matrix_path, 'r') as f:
                mat = json.load(f)

            if mat.get("overall_passed") is not True:
                errors.append("F41_CAE_RECONSTRUCTION_MATRIX overall_passed is not True")
        except Exception as exc:
            errors.append("Failed to parse F41_CAE_RECONSTRUCTION_MATRIX.json: {0}".format(exc))

    if errors:
        print("F41_MATRIX_VALIDATION_FAILED:")
        for err in errors:
            print("  - " + err)
        return 1

    print("F41_MATRIX_VALIDATION_PASSED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
