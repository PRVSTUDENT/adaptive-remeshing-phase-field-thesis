#!/usr/bin/env python3
"""Fail-closed static integrity checks for a regenerated Mode-II deck."""
from __future__ import print_function

import argparse
import json
import re


def labels_in_blocks(text, keyword):
    labels = []
    active = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("*"):
            active = line.upper().startswith(keyword)
            continue
        if active and line and not line.startswith("**"):
            token = line.split(",", 1)[0].strip()
            if token.isdigit():
                labels.append(int(token))
    return labels


def validate_text(text):
    upper = text.upper()
    nodes = labels_in_blocks(text, "*NODE")
    elements = labels_in_blocks(text, "*ELEMENT")
    checks = {
        "no_duplicate_node_labels": len(nodes) == len(set(nodes)) and bool(nodes),
        "no_duplicate_element_labels": len(elements) == len(set(elements)) and bool(elements),
        "required_all_elem": "ELSET=ALL_ELEM" in upper,
        "required_umatelem": "ELSET=UMATELEM" in upper,
        "sections_present": "*SOLID SECTION" in upper or "*UEL PROPERTY" in upper,
        "boundary_conditions_present": "*BOUNDARY" in upper,
        "rp_equations_present": "*EQUATION" in upper,
        "plane_strain_elements_present": "TYPE=CPE4" in upper,
        "uel_elements_present": re.search(r"TYPE=U\d+", upper) is not None,
        "uel_properties_present": "*UEL PROPERTY" in upper,
        "output_requests_present": "*OUTPUT" in upper,
    }
    checks.update({
        "slit_topology": "requires_coordinate_connectivity_audit",
        "jacobians": "requires_generated_mesh_geometry_audit",
        "n_elem_fortran_match": "requires_destination_fortran_manifest",
        "label_offsets": "requires_destination_manifest",
        "local_h_over_lc": "requires_generated_mesh_geometry_audit",
    })
    passed = all(value is True for value in checks.values())
    return {
        "classification": "refined_deck_integrity_pass" if passed else "refined_deck_integrity_incomplete",
        "passed": passed,
        "checks": checks,
        "node_count": len(nodes),
        "element_count": len(elements),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("deck")
    parser.add_argument("--output")
    args = parser.parse_args()
    with open(args.deck, errors="replace") as stream:
        result = validate_text(stream.read())
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        with open(args.output, "w") as stream:
            stream.write(payload)
    print(payload, end="")
    raise SystemExit(0 if result["passed"] else 2)


if __name__ == "__main__":
    main()
