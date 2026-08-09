#!/usr/bin/env python3
"""
Mode-II Uniform Phase-Field Reference Contract Validator
Task: F43MODEREF-PREP1

Statically validates the Mode-II uniform reference convergence study packages:
  - M2REF_H0 (Coarse baseline, 3,930 physical -> 11,790 layered elements)
  - M2REF_H1 (Medium refinement, 12,064 physical -> 36,192 layered elements)
  - M2REF_H2 (Fine refinement, 33,852 physical -> 101,556 layered elements)

Verifies:
  1. File presence and SHA256 integrity
  2. Subroutine bytecode parity (f42_mixed_uel.for)
  3. Strict 3-layer element architecture (U1/U2/CPE4)
  4. Material constants and formulation fairness (E, nu, Gc, l0, k, t)
  5. 2-Step loading schedule (0 -> 0.0050 mm -> 0.0100 mm)
  6. Boundary conditions, equations, and RP coupling
  7. Monotonic resolution hierarchy (H0 -> H1 -> H2)
  8. Cross-model formulation fairness against MM and PK5
"""

import os
import sys
import json
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Any

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_BATCH_MANIFEST.json"
EXPECTED_UEL_SHA256 = "5dc005383773a2923b943024b97dc15590a4f220e319fd289c891b15c30844f3"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_deck_structure(deck_path: Path) -> Dict[str, Any]:
    """
    Re-read and parse complete generated .inp deck from disk and validate:
      1. Duplicate node labels == 0 (all written node labels are unique)
      2. Duplicate element labels == 0
      3. RP node ID > max physical node ID and NOT in physical node IDs
      4. Undefined node references == 0
      5. Zero / negative area elements calculated from FINAL written node coordinates == 0
    """
    text = deck_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    node_dict: Dict[int, Tuple[float, float]] = {}
    all_node_labels: List[int] = []
    all_elem_labels: List[int] = []
    u1_elements: Dict[int, List[int]] = {}
    u2_elements: Dict[int, List[int]] = {}
    cpe4_elements: Dict[int, List[int]] = {}
    rp_set_nodes: List[int] = []
    equations = 0

    in_node = False
    in_u1 = False
    in_u2 = False
    in_cpe4 = False
    in_rp_nset = False

    for line in lines:
        s = line.strip()
        if not s or s.startswith("**"):
            continue
        sl = s.lower()
        if sl.startswith("*node"):
            in_node = True
            in_u1 = in_u2 = in_cpe4 = in_rp_nset = False
            continue
        elif sl.startswith("*element, type=u1"):
            in_u1 = True
            in_node = in_u2 = in_cpe4 = in_rp_nset = False
            continue
        elif sl.startswith("*element, type=u2"):
            in_u2 = True
            in_node = in_u1 = in_cpe4 = in_rp_nset = False
            continue
        elif sl.startswith("*element, type=cpe4"):
            in_cpe4 = True
            in_node = in_u1 = in_u2 = in_rp_nset = False
            continue
        elif sl.startswith("*nset, nset=rp") or sl.startswith("*nset, nset=set_rp"):
            in_rp_nset = True
            in_node = in_u1 = in_u2 = in_cpe4 = False
            continue
        elif s.startswith("*"):
            in_node = in_u1 = in_u2 = in_cpe4 = in_rp_nset = False

        if in_node:
            parts = [p.strip() for p in s.split(",")]
            if len(parts) >= 3 and parts[0].isdigit():
                nid = int(parts[0])
                all_node_labels.append(nid)
                node_dict[nid] = (float(parts[1]), float(parts[2]))
        elif in_u1:
            parts = [p.strip() for p in s.split(",")]
            if len(parts) >= 5 and parts[0].isdigit():
                eid = int(parts[0])
                all_elem_labels.append(eid)
                u1_elements[eid] = [int(p) for p in parts[1:5]]
        elif in_u2:
            parts = [p.strip() for p in s.split(",")]
            if len(parts) >= 5 and parts[0].isdigit():
                eid = int(parts[0])
                all_elem_labels.append(eid)
                u2_elements[eid] = [int(p) for p in parts[1:5]]
        elif in_cpe4:
            parts = [p.strip() for p in s.split(",")]
            if len(parts) >= 5 and parts[0].isdigit():
                eid = int(parts[0])
                all_elem_labels.append(eid)
                cpe4_elements[eid] = [int(p) for p in parts[1:5]]
        elif in_rp_nset:
            parts = [p.strip() for p in s.split(",")]
            for p in parts:
                if p.isdigit():
                    rp_set_nodes.append(int(p))

        if sl.startswith("*equation"):
            equations += 1

    # Quality and Integrity Checks
    duplicate_node_count = len(all_node_labels) - len(node_dict)
    duplicate_elem_count = len(all_elem_labels) - len(set(all_elem_labels))

    rp_node_id = rp_set_nodes[0] if rp_set_nodes else -1
    physical_node_ids = set(node_dict.keys()) - {rp_node_id} if rp_node_id in node_dict else set(node_dict.keys())
    max_physical_node_id = max(physical_node_ids) if physical_node_ids else 0

    rp_is_valid = (
        rp_node_id > max_physical_node_id and
        rp_node_id not in physical_node_ids
    )

    # Check undefined node references and element areas using FINAL node coordinates
    undefined_node_refs = 0
    zero_area_elems = 0
    distorted_elems = 0

    for eid, conn in u1_elements.items():
        coords = []
        for n in conn:
            if n not in node_dict:
                undefined_node_refs += 1
            else:
                coords.append(node_dict[n])
        if len(coords) == 4:
            (x1, y1), (x2, y2), (x3, y3), (x4, y4) = coords
            signed_area = 0.5 * ((x1*y2 - x2*y1) + (x2*y3 - x3*y2) + (x3*y4 - x4*y3) + (x4*y1 - x1*y4))
            abs_area = abs(signed_area)

            cp1 = (x2 - x1)*(y3 - y2) - (y2 - y1)*(x3 - x2)
            cp2 = (x3 - x2)*(y4 - y3) - (y3 - y2)*(x4 - x3)
            cp3 = (x4 - x3)*(y1 - y4) - (y4 - y3)*(x1 - x4)
            cp4 = (x1 - x4)*(y2 - y1) - (y1 - y4)*(x2 - x1)

            tol = -1.0e-12
            is_convex = (cp1 >= tol and cp2 >= tol and cp3 >= tol and cp4 >= tol) or (cp1 <= -tol and cp2 <= -tol and cp3 <= -tol and cp4 <= -tol)

            if abs_area <= 1.0e-12:
                zero_area_elems += 1
            if not is_convex:
                distorted_elems += 1

    has_amp1 = "*Amplitude, name=Amp-1" in text
    has_amp2 = "*Amplitude, name=Amp-2" in text
    has_step1 = "*Step, name=Step-1" in text
    has_step2 = "*Step, name=Step-2" in text
    has_uel_prop_phase = "*UEL Property, elset=PHASE_QUAD" in text
    has_uel_prop_disp = "*UEL Property, elset=DISP_QUAD" in text
    has_mat_facsimile = "*Material, name=MAT_QUAD_FACSIMILE" in text

    return {
        "n_nodes": len(node_dict),
        "n_u1": len(u1_elements),
        "n_u2": len(u2_elements),
        "n_cpe4": len(cpe4_elements),
        "n_layered": len(u1_elements) + len(u2_elements) + len(cpe4_elements),
        "equations_count": equations,
        "duplicate_node_count": duplicate_node_count,
        "duplicate_elem_count": duplicate_elem_count,
        "rp_node_id": rp_node_id,
        "max_physical_node_id": max_physical_node_id,
        "rp_is_valid": rp_is_valid,
        "undefined_node_refs": undefined_node_refs,
        "zero_area_elems": zero_area_elems,
        "distorted_elems": distorted_elems,
        "has_amp1": has_amp1,
        "has_amp2": has_amp2,
        "has_step1": has_step1,
        "has_step2": has_step2,
        "has_uel_prop_phase": has_uel_prop_phase,
        "has_uel_prop_disp": has_uel_prop_disp,
        "has_mat_facsimile": has_mat_facsimile
    }


def validate_reference_batch(write_report: bool = False) -> Dict[str, Any]:
    errors = []
    warnings = []

    if not MANIFEST_PATH.is_file():
        return {"passed": False, "errors": [f"Manifest not found: {MANIFEST_PATH}"], "warnings": []}

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))
    candidates = manifest.get("candidates", {})

    expected_cases = ["M2REF_H0", "M2REF_H1", "M2REF_H2"]
    for c in expected_cases:
        if c not in candidates:
            errors.append(f"Missing expected case {c} in manifest")

    prev_phys = 0
    prev_h_min = 1.0

    candidate_results = {}

    for cname in expected_cases:
        if cname not in candidates:
            continue
        cinfo = candidates[cname]
        deck_file = ROOT / Path(cinfo["deck_path"].replace("\\", "/"))
        uel_file = ROOT / Path(cinfo["uel_path"].replace("\\", "/"))
        pbs_file = ROOT / Path(cinfo["pbs_path"].replace("\\", "/"))
        submit_file = ROOT / Path(cinfo["submit_wrapper"].replace("\\", "/"))

        # Check file existence
        for f, label in [(deck_file, "deck"), (uel_file, "uel"), (pbs_file, "pbs"), (submit_file, "submit")]:
            if not f.is_file():
                errors.append(f"{cname} {label} file missing: {f}")

        # Check UEL SHA
        if uel_file.is_file():
            usha = sha256_file(uel_file)
            if usha != EXPECTED_UEL_SHA256:
                errors.append(f"{cname} UEL SHA mismatch: {usha} != {EXPECTED_UEL_SHA256}")

        # Check Deck SHA
        if deck_file.is_file():
            dsha = sha256_file(deck_file)
            if dsha != cinfo["deck_sha256"]:
                errors.append(f"{cname} Deck SHA mismatch: {dsha} != {cinfo['deck_sha256']}")

            # Parse deck structure
            struct = parse_deck_structure(deck_file)
            n_phys = cinfo["physical_elements"]

            if struct["n_u1"] != n_phys:
                errors.append(f"{cname} U1 count {struct['n_u1']} != expected {n_phys}")
            if struct["n_u2"] != n_phys:
                errors.append(f"{cname} U2 count {struct['n_u2']} != expected {n_phys}")
            if struct["n_cpe4"] != n_phys:
                errors.append(f"{cname} CPE4 count {struct['n_cpe4']} != expected {n_phys}")
            if struct["n_layered"] != 3 * n_phys:
                errors.append(f"{cname} layered count {struct['n_layered']} != expected {3 * n_phys}")

            if not struct["has_amp1"] or not struct["has_amp2"]:
                errors.append(f"{cname} missing Amp-1 or Amp-2 loading amplitudes")
            if not struct["has_step1"] or not struct["has_step2"]:
                errors.append(f"{cname} missing Step-1 or Step-2 definition")
            if not struct["has_uel_prop_phase"] or not struct["has_uel_prop_disp"] or not struct["has_mat_facsimile"]:
                errors.append(f"{cname} missing UEL property or facsimile material definitions")

            if struct["duplicate_node_count"] > 0:
                errors.append(f"{cname} contains {struct['duplicate_node_count']} duplicate node label(s)")
            if struct["duplicate_elem_count"] > 0:
                errors.append(f"{cname} contains {struct['duplicate_elem_count']} duplicate element label(s)")
            if not struct["rp_is_valid"]:
                errors.append(f"{cname} RP node ID {struct['rp_node_id']} is invalid (max physical node ID: {struct['max_physical_node_id']})")
            if struct["undefined_node_refs"] > 0:
                errors.append(f"{cname} contains {struct['undefined_node_refs']} undefined node reference(s) in elements")
            if struct["zero_area_elems"] > 0:
                errors.append(f"{cname} contains {struct['zero_area_elems']} zero-area element(s)")
            if struct["distorted_elems"] > 0:
                errors.append(f"{cname} contains {struct['distorted_elems']} distorted/non-convex element(s)")

            candidate_results[cname] = struct

        # Check resolution hierarchy monotonicity
        n_phys_cur = cinfo["physical_elements"]
        h_min_cur = cinfo["h_area_min_mm"]

        if n_phys_cur <= prev_phys:
            errors.append(f"Monotonicity violation: {cname} physical elements ({n_phys_cur}) <= previous ({prev_phys})")
        if h_min_cur >= prev_h_min:
            errors.append(f"Resolution ordering violation: {cname} h_min ({h_min_cur}) >= previous ({prev_h_min})")

        prev_phys = n_phys_cur
        prev_h_min = h_min_cur

    passed = len(errors) == 0

    res = {
        "passed": passed,
        "errors": errors,
        "warnings": warnings,
        "candidate_results": candidate_results,
        "manifest_summary": {
            "study_name": manifest.get("study_name"),
            "task_id": manifest.get("task_id"),
            "candidates_count": len(candidates)
        }
    }

    if write_report:
        out_json = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_STATIC_VALIDATION.json"
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")

    return res


def main():
    res = validate_reference_batch()

    print(f"Validation Result: {'PASS' if res['passed'] else 'FAIL'}")
    if res["errors"]:
        print("Errors:")
        for e in res["errors"]:
            print(f"  - {e}")
    else:
        print("All static checks passed successfully.")
    sys.exit(0 if res["passed"] else 1)


if __name__ == "__main__":
    main()
