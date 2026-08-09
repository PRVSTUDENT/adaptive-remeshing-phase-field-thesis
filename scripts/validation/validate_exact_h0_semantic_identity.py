#!/usr/bin/env python3
"""Independent semantic identity validator for M2REF_H0_EXACT_FRACFIX_REPRO input deck.
Compares candidate against authoritative reference deck ModeII_H0_endpoint_corrected_serial.inp.
"""

import sys
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REF_INP = ROOT / "models/generated/mode_ii/h0_endpoint_corrected_serial/ModeII_H0_endpoint_corrected_serial.inp"
CAND_INP = ROOT / "models/generated/mode_ii/verification_batch/M2REF_H0_EXACT_FRACFIX_REPRO/M2REF_H0_EXACT_FRACFIX_REPRO.inp"


def parse_part1_nodes(path: Path):
    nodes = {}
    with path.open("r", encoding="utf-8") as f:
        in_node = False
        for line in f:
            l = line.strip()
            if l.lower().startswith("*node") and not in_node:
                in_node = True
                continue
            if in_node:
                if l.startswith("*"):
                    in_node = False
                    continue
                parts = [p.strip() for p in l.split(",") if p.strip()]
                try:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    if nid <= 3998:
                        nodes[nid] = (x, y)
                except Exception:
                    pass
    return nodes


def parse_elements(path: Path):
    elements = {"U1": {}, "U2": {}, "FACSIMILE": {}}
    with path.open("r", encoding="utf-8") as f:
        current_eltype = None
        for line in f:
            l = line.strip()
            if l.lower().startswith("*element"):
                parts = [p.strip().upper() for p in l.split(",")]
                current_eltype = None
                for p in parts:
                    if "TYPE=" in p:
                        tval = p.split("=")[1].strip()
                        if tval in ["U1", "U2"]:
                            current_eltype = tval
                        elif tval in ["CPS4", "CPE4", "CPS4R", "CPE4R"]:
                            current_eltype = "FACSIMILE"
                continue

            if current_eltype in elements and not l.startswith("*"):
                try:
                    parts = [int(p.strip()) for p in l.split(",") if p.strip()]
                    if len(parts) == 5:  # Exact 4-node quad elements (elid + 4 nodes)
                        elid = parts[0]
                        conn = tuple(parts[1:5])
                        elements[current_eltype][elid] = conn
                except Exception:
                    pass
    return elements


def calc_quad_area(p1, p2, p3, p4):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    area = 0.5 * abs(x1 * y2 + x2 * y3 + x3 * y4 + x4 * y1 - (y1 * x2 + y2 * x3 + y3 * x4 + y4 * x1))
    return area


def validate_semantic_identity():
    print("=== Validating M2REF_H0_EXACT_FRACFIX_REPRO Semantic Identity ===")

    if not REF_INP.is_file():
        print(f"FAIL: Reference INP missing: {REF_INP}")
        return False, {"error": "Missing reference INP"}

    if not CAND_INP.is_file():
        print(f"FAIL: Candidate INP missing: {CAND_INP}")
        return False, {"error": "Missing candidate INP"}

    ref_nodes = parse_part1_nodes(REF_INP)
    cand_nodes = parse_part1_nodes(CAND_INP)

    ref_elems = parse_elements(REF_INP)
    cand_elems = parse_elements(CAND_INP)

    checks = []
    failures = []

    def check(cond: bool, msg: str):
        checks.append(msg)
        if not cond:
            failures.append(msg)

    # 1. Physical Node Count
    check(len(cand_nodes) == 3998, f"Part-1 physical node count equals 3998 (got {len(cand_nodes)})")
    check(len(cand_nodes) == len(ref_nodes), f"Part-1 physical node count matches reference ({len(cand_nodes)} vs {len(ref_nodes)})")

    # 2. Node Coordinates Match
    coord_mismatches = 0
    for nid, r_coord in ref_nodes.items():
        if nid not in cand_nodes:
            coord_mismatches += 1
        else:
            c_coord = cand_nodes[nid]
            if abs(r_coord[0] - c_coord[0]) > 1e-7 or abs(r_coord[1] - c_coord[1]) > 1e-7:
                coord_mismatches += 1
    check(coord_mismatches == 0, f"All 3,998 physical node coordinates match reference (mismatches: {coord_mismatches})")

    # 3. Element Counts (3,930 physical elements per layer)
    for eltype in ["U1", "U2", "FACSIMILE"]:
        c_count = len(cand_elems[eltype])
        r_count = len(ref_elems[eltype])
        check(c_count == 3930, f"{eltype} element count equals 3930 (got {c_count})")
        check(c_count == r_count, f"{eltype} element count matches reference ({c_count} vs {r_count})")

    # 4. Element Connectivities and Positive Areas
    negative_area_count = 0
    conn_mismatches = 0
    for elid, r_conn in ref_elems["FACSIMILE"].items():
        if elid not in cand_elems["FACSIMILE"]:
            conn_mismatches += 1
            continue
        c_conn = cand_elems["FACSIMILE"][elid]
        if r_conn != c_conn:
            conn_mismatches += 1

        p1 = cand_nodes[c_conn[0]]
        p2 = cand_nodes[c_conn[1]]
        p3 = cand_nodes[c_conn[2]]
        p4 = cand_nodes[c_conn[3]]
        a = calc_quad_area(p1, p2, p3, p4)
        if a <= 1e-12:
            negative_area_count += 1

    check(conn_mismatches == 0, f"All 3,930 element connectivities match reference (mismatches: {conn_mismatches})")
    check(negative_area_count == 0, f"All 3,930 physical elements have strictly positive areas (invalid: {negative_area_count})")

    # 5. Split-notch Topology (101 nodes along y=0, x in [0, 0.5])
    cand_notch = [nid for nid, (x, y) in cand_nodes.items() if abs(y) <= 1e-5 and -1e-5 <= x <= 0.5 + 1e-5]
    ref_notch = [nid for nid, (x, y) in ref_nodes.items() if abs(y) <= 1e-5 and -1e-5 <= x <= 0.5 + 1e-5]
    check(len(cand_notch) == 101, f"Split-notch node count equals 101 (50 upper + 50 lower + tip node, got {len(cand_notch)})")
    check(len(cand_notch) == len(ref_notch), f"Split-notch node count matches reference ({len(cand_notch)} vs {len(ref_notch)})")

    # 6. Deck structure check
    deck_text = CAND_INP.read_text(encoding="utf-8")
    check("*User element, nodes=4, type=U1" in deck_text.lower() or "*user element, nodes=4, type=u1" in deck_text.lower(), "U1 User Element header present")
    check("*User element, nodes=4, type=U2" in deck_text.lower() or "*user element, nodes=4, type=u2" in deck_text.lower(), "U2 User Element header present")
    check("*user material, constants=2" in deck_text.lower(), "Facsimile UMAT header present")

    passed = len(failures) == 0
    status_str = "PASS" if passed else "FAIL"

    report = {
        "corrected_H0_semantic_identity": status_str,
        "passed": passed,
        "ref_inp": str(REF_INP),
        "cand_inp": str(CAND_INP),
        "corrected_H0_physical_elements": len(cand_elems["FACSIMILE"]),
        "corrected_H0_physical_nodes": len(cand_nodes),
        "total_checks": len(checks),
        "failures": failures,
    }

    out_artifact = ROOT / "models/generated/mode_ii/verification_batch/M2REF_H0_EXACT_SEMANTIC_AUDIT.json"
    out_artifact.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote semantic audit artifact to {out_artifact}")
    print(f"Result: corrected_H0_semantic_identity = {status_str}")

    return passed, report


def main():
    passed, report = validate_semantic_identity()
    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
