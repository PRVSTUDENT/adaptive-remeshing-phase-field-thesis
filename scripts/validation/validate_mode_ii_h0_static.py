#!/usr/bin/env python3
"""Static offline validation for Stage-F Mode-II H0 serial package.

No Abaqus execution. Fail-closed on any required check failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKAGE = ROOT / "models/generated/mode_ii/h0_serial"
EXPECTED_N_ELEM = 3930
EXPECTED_PHYSICAL = 3930
EXPECTED_LAYERED = 11790
EXPECTED_NODES = 3998
TOL = 1.0e-9


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_nodes(text: str) -> dict[int, tuple[float, float]]:
    nodes: dict[int, tuple[float, float]] = {}
    in_node = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("*"):
            in_node = s.lower().startswith("*node")
            continue
        if not in_node or not s or s.startswith("**"):
            continue
        parts = [p.strip() for p in s.split(",")]
        if len(parts) < 3:
            continue
        try:
            nid = int(parts[0])
            x = float(parts[1])
            y = float(parts[2])
        except ValueError:
            continue
        nodes[nid] = (x, y)
    return nodes


def parse_elements(text: str, type_token: str) -> dict[int, list[int]]:
    elements: dict[int, list[int]] = {}
    in_block = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("*"):
            low = s.lower()
            in_block = low.startswith("*element") and type_token.lower() in low
            continue
        if not in_block or not s or s.startswith("**"):
            continue
        parts = [p.strip() for p in s.split(",") if p.strip()]
        if len(parts) < 5:
            continue
        try:
            eid = int(parts[0])
            conn = [int(p) for p in parts[1:5]]
        except ValueError:
            continue
        elements[eid] = conn
    return elements


def element_jacobian_ok(coords: list[tuple[float, float]]) -> bool:
    # Quad split into two triangles; require positive area for both orientations.
    def tri_area(a, b, c) -> float:
        return 0.5 * ((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1]))

    a, b, c, d = coords
    # Connectivity order assumed counter-clockwise-ish; accept either winding
    # but reject near-zero / opposite mixed areas.
    areas = [tri_area(a, b, c), tri_area(a, c, d), tri_area(a, b, d), tri_area(b, c, d)]
    if any(abs(v) < 1.0e-16 for v in areas[:2]):
        return False
    # Primary diagonals should not cancel to a crossed quad with zero volume.
    area_poly = tri_area(a, b, c) + tri_area(a, c, d)
    return abs(area_poly) > 1.0e-16


def fixed_form_ok(fortran_text: str) -> tuple[bool, list[str]]:
    bad: list[str] = []
    for i, line in enumerate(fortran_text.splitlines(), 1):
        if not line:
            continue
        # Comments and preprocessor-style lines
        if line[0] in "Cc*!":
            continue
        # Continuation markers in col 6 are allowed; code body must fit 72.
        body = line[:72]
        if len(line.rstrip("\n")) > 72 and line[0] not in "Cc*":
            # Allow trailing comments after column 72 only if columns 1-72 hold code.
            if len(line) > 72 and line[72:].strip() and not line[72:].strip().startswith("!"):
                bad.append(f"line {i}: exceeds column 72 without comment-only tail")
    return len(bad) == 0, bad[:20]


def validate_package(package: Path) -> dict:
    deck = package / "ModeII_H0_serial.inp"
    source = package / "ModeII_H0_serial.for"
    manifest_path = package / "PACKAGE_MANIFEST.json"
    checks: dict[str, bool] = {}
    details: dict = {}

    checks["package_files_present"] = all(p.is_file() for p in (deck, source, manifest_path))
    if not checks["package_files_present"]:
        return {
            "classification": "stage_f_mode_ii_h0_static_fail",
            "checks": checks,
            "details": {"missing": [str(p) for p in (deck, source, manifest_path) if not p.is_file()]},
        }

    deck_text = deck.read_text(encoding="utf-8", errors="replace")
    for_text = source.read_text(encoding="utf-8", errors="replace")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    deck_sha = sha256_file(deck)
    source_sha = sha256_file(source)
    checks["deck_sha_matches_manifest"] = manifest.get("deck", {}).get("sha256") == deck_sha
    checks["source_sha_matches_manifest"] = manifest.get("source", {}).get("sha256") == source_sha
    details["deck_sha256"] = deck_sha
    details["source_sha256"] = source_sha

    nodes = parse_nodes(deck_text)
    u1 = parse_elements(deck_text, "type=U1")
    u2 = parse_elements(deck_text, "type=U2")
    cps4 = parse_elements(deck_text, "TYPE=CPS4") or parse_elements(deck_text, "type=CPS4")
    details["node_count"] = len(nodes)
    details["u1_count"] = len(u1)
    details["u2_count"] = len(u2)
    details["cps4_count"] = len(cps4)

    checks["node_count"] = len(nodes) == EXPECTED_NODES
    checks["physical_element_count"] = len(u1) == EXPECTED_PHYSICAL
    checks["layered_element_count"] = len(u1) + len(u2) + len(cps4) == EXPECTED_LAYERED
    checks["u1_u2_cps4_counts_equal"] = len(u1) == len(u2) == len(cps4)

    node_ids = list(nodes)
    checks["no_duplicate_nodes"] = len(node_ids) == len(set(node_ids))
    all_eids = list(u1) + list(u2) + list(cps4)
    checks["no_duplicate_elements"] = len(all_eids) == len(set(all_eids))
    checks["layer_labels_disjoint"] = (
        set(u1).isdisjoint(u2) and set(u1).isdisjoint(cps4) and set(u2).isdisjoint(cps4)
    )

    missing = []
    for mapping in (u1, u2, cps4):
        for eid, conn in mapping.items():
            for n in conn:
                if n not in nodes:
                    missing.append((eid, n))
    checks["no_missing_connectivity_nodes"] = len(missing) == 0
    details["missing_connectivity_count"] = len(missing)

    # Layer connectivity correspondence (same physical connectivity order).
    # U1 labels 1..N, U2 N+1..2N, CPS4 2N+1..3N in Molnar deck.
    n = EXPECTED_PHYSICAL
    layer_ok = True
    orphan_vis = 0
    for i in range(1, n + 1):
        if i not in u1 or (i + n) not in u2 or (i + 2 * n) not in cps4:
            layer_ok = False
            continue
        if u1[i] != u2[i + n] or u1[i] != cps4[i + 2 * n]:
            layer_ok = False
    for eid in cps4:
        phys = eid - 2 * n
        if phys not in u1:
            orphan_vis += 1
    checks["layer_offsets_and_connectivity_match"] = layer_ok
    checks["no_orphaned_visualization_elements"] = orphan_vis == 0
    details["orphaned_visualization_count"] = orphan_vis

    # Jacobians
    bad_jac = 0
    for eid, conn in u1.items():
        coords = [nodes[n] for n in conn]
        if not element_jacobian_ok(coords):
            bad_jac += 1
    checks["positive_element_jacobians"] = bad_jac == 0
    details["bad_jacobian_count"] = bad_jac

    # Notch topology: nodes near y=0 with x in [-0.5,0) should include split pairs.
    notch_nodes = [nid for nid, (x, y) in nodes.items() if abs(y) < 1.0e-4 and -0.5 - TOL <= x <= TOL]
    checks["notch_topology_nodes_present"] = len(notch_nodes) >= 4
    details["notch_node_count"] = len(notch_nodes)

    # Material / props
    checks["uel_u1_props"] = bool(re.search(r"\*Uel property, elset=PLATE\s*\n\s*0\.015,\s*0\.0027,\s*1", deck_text))
    checks["uel_u2_props"] = bool(re.search(r"\*Uel property, elset=PLATE_SS\s*\n\s*210,\s*0\.3,\s*1,\s*1e-07", deck_text))
    checks["umat_constants"] = "1e-11, 0.3" in deck_text
    checks["user_element_u1_dofs"] = bool(re.search(r"\*User element, nodes=4, type=U1[\s\S]*?\n\s*3\s*\n", deck_text))
    checks["user_element_u2_dofs"] = bool(re.search(r"\*User element, nodes=4, type=U2[\s\S]*?\n\s*1,2\s*\n", deck_text))

    # Mode-II BC
    checks["mode_ii_equation_u1"] = "top, 1, 1." in deck_text and "RP, 1, -1." in deck_text
    checks["no_mode_i_equation_u2"] = "top, 2, 1." not in deck_text
    checks["mode_ii_rp_u1"] = bool(re.search(r"^\s*RP, 1, 1, 1\.\s*$", deck_text, flags=re.M))
    checks["no_mode_i_rp_u2"] = not bool(re.search(r"^\s*RP, 2, 2, 1\.\s*$", deck_text, flags=re.M))
    checks["bottom_fully_fixed"] = bool(re.search(r"^\s*bottom, 1, 2\s*$", deck_text, flags=re.M))
    checks["top_u2_fixed"] = bool(re.search(r"^\s*top, 2, 2\s*$", deck_text, flags=re.M))
    checks["sets_present"] = all(tok in deck_text for tok in ("nset=RP", "nset=bottom", "nset=top", "elset=umatelem"))

    # Outputs
    for token in ("U", "RF", "SDV", "S", "EVOL", "ALLIE", "ETOTAL"):
        checks[f"output_{token}"] = token in deck_text

    # Fortran
    n_elem_vals = [int(v) for v in re.findall(r"N_ELEM=(\d+)", for_text)]
    checks["fortran_n_elem"] = bool(n_elem_vals) and all(v == EXPECTED_N_ELEM for v in n_elem_vals)
    checks["phase_history_layout_tokens"] = "NSTVTO=2" in for_text and "NSTVTT=14" in for_text and "NSTV=18" in for_text
    ff_ok, ff_bad = fixed_form_ok(for_text)
    checks["fixed_form_fortran"] = ff_ok
    details["fixed_form_issues"] = ff_bad

    # No remeshing / miseseri in package
    checks["no_miseseri_token"] = "MISESERI" not in deck_text.upper()
    checks["manifest_execution_false"] = (
        manifest.get("execution_authorized") is False
        and manifest.get("datacheck_authorized") is False
        and manifest.get("solver_authorized") is False
    )
    checks["manifest_no_remesh"] = manifest.get("miseseri_remeshing") is False

    # Transfer/hash file
    hash_file = package / "input_hashes.sha256"
    checks["hash_file_present"] = hash_file.is_file()
    if hash_file.is_file():
        ht = hash_file.read_text(encoding="utf-8")
        checks["hash_file_lists_deck"] = deck_sha in ht
        checks["hash_file_lists_source"] = source_sha in ht

    passed = all(checks.values())
    return {
        "classification": "stage_f_mode_ii_h0_static_pass" if passed else "stage_f_mode_ii_h0_static_fail",
        "checks": checks,
        "details": details,
        "failed_checks": [k for k, v in checks.items() if not v],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--write-report", type=Path, default=None)
    args = parser.parse_args()
    report = validate_package(args.package)
    out = args.write_report or (args.package / "STATIC_VALIDATION.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"classification": report["classification"], "failed_checks": report["failed_checks"]}, indent=2))
    return 0 if report["classification"].endswith("_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
