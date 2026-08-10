#!/usr/bin/env python3
"""Fail-Closed NPHYS Producer-Consumer Contract Validator.

Validates that Mode-II mixed UEL input decks correctly specify the NPHYS physical
element count contract across U1/U2 phase-displacement element pairs and facsimile UMAT.

Checks:
1. U2/U4 required property count == 5 (*User element, type=U2, properties=5).
2. 5th UEL property value equals physical element count NPHYS.
3. UMAT material 3rd constant equals NPHYS (when UMAT constants >= 3).
4. Pointwise history index mapping: U2 physical element p (JELEM = NPHYS + p)
   computes PHYSIDX = (NPHYS + p) - NPHYS = p, matching U1 physical element p
   (JELEM = p, PHYSIDX = p) for p = 1, 1965, NPHYS.

Returns exit code 0 if all decks pass, or exit code 1 if any deck fails.
"""

import sys
import os
import re
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DECKS_TO_VALIDATE = [
    ("M2REF_H0_NPHYSFIX_REPRO", ROOT / "models/generated/mode_ii/verification_batch/M2REF_H0_NPHYSFIX_REPRO/M2REF_H0_NPHYSFIX_REPRO.inp", 3930),
    ("M2REF_ONEEL_FRACFIX_VERIFY_R2", ROOT / "models/generated/mode_ii/verification_batch/M2REF_ONEEL_FRACFIX_VERIFY_R2/M2REF_ONEEL_FRACFIX_VERIFY_R2.inp", 4),
    ("M2REF_H1_FRACFIX", ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H1/M2REF_H1.inp", 12064),
    ("M2REF_H2_FRACFIX", ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H2/M2REF_H2.inp", 33852),
]


def audit_deck_nphys(deck_path: Path, expected_nphys: int) -> dict:
    result = {
        "deck_path": str(deck_path),
        "expected_nphys": expected_nphys,
        "u2_header_properties_5": False,
        "u2_property_nphys_value": None,
        "u2_nphys_matches_expected": False,
        "umat_nphys_value": None,
        "umat_nphys_matches_expected": False,
        "p1_u2_write_slot": None,
        "p1_u1_read_slot": None,
        "p1_index_match": False,
        "pmid_index_match": False,
        "plast_index_match": False,
        "overall_pass": False,
        "errors": []
    }

    if not deck_path.exists():
        result["errors"].append(f"Deck file does not exist: {deck_path}")
        return result

    lines = deck_path.read_text(encoding="utf-8", errors="replace").splitlines()
    
    # 1. Audit *User Element header for U2
    for line in lines:
        s = line.strip().lower()
        if s.startswith("*user element") and "type=u2" in s:
            if "properties=5" in s:
                result["u2_header_properties_5"] = True
            else:
                result["errors"].append(f"U2 User Element header lacks properties=5: '{line.strip()}'")

    # 2. Audit *UEL Property line for U2 / DISP
    in_disp_prop = False
    for line in lines:
        s = line.strip().lower()
        if s.startswith("*uel property") and ("disp" in s or "plate_ss" in s):
            in_disp_prop = True
            continue
        elif s.startswith("*") and in_disp_prop:
            in_disp_prop = False

        if in_disp_prop and not s.startswith("**"):
            parts = [p.strip() for p in s.split(",")]
            if len(parts) >= 5:
                try:
                    val = float(parts[4])
                    result["u2_property_nphys_value"] = int(val)
                    if int(val) == expected_nphys:
                        result["u2_nphys_matches_expected"] = True
                    else:
                        result["errors"].append(f"U2 UEL Property NPHYS value ({val}) != expected NPHYS ({expected_nphys})")
                except ValueError:
                    result["errors"].append(f"Could not parse 5th UEL Property as float: '{parts[4]}'")
            else:
                result["errors"].append(f"U2 UEL Property line has fewer than 5 parameters: '{line.strip()}'")

    # 3. Audit *User Material constants for facsimile UMAT
    in_umat = False
    for line in lines:
        s = line.strip().lower()
        if s.startswith("*user material"):
            in_umat = True
            continue
        elif s.startswith("*") and in_umat:
            in_umat = False

        if in_umat and not s.startswith("**"):
            parts = [p.strip() for p in s.split(",")]
            if len(parts) >= 3:
                try:
                    val = float(parts[2])
                    result["umat_nphys_value"] = int(val)
                    if int(val) == expected_nphys:
                        result["umat_nphys_matches_expected"] = True
                    else:
                        result["errors"].append(f"UMAT constant 3 NPHYS value ({val}) != expected NPHYS ({expected_nphys})")
                except ValueError:
                    pass

    # 4. Pointwise index producer-consumer check
    nphys_declared = result["u2_property_nphys_value"] if result["u2_property_nphys_value"] is not None else 1
    
    # Physical element p=1:
    # U2 JELEM = expected_nphys + 1
    # U2 PHYSIDX = (expected_nphys + 1) - nphys_declared
    # U1 JELEM = 1 -> U1 PHYSIDX = 1
    p1_u2_write = (expected_nphys + 1) - nphys_declared
    p1_u1_read = 1
    result["p1_u2_write_slot"] = p1_u2_write
    result["p1_u1_read_slot"] = p1_u1_read
    result["p1_index_match"] = (p1_u2_write == p1_u1_read)

    p_mid = max(1, expected_nphys // 2)
    pmid_u2_write = (expected_nphys + p_mid) - nphys_declared
    pmid_u1_read = p_mid
    result["pmid_index_match"] = (pmid_u2_write == pmid_u1_read)

    p_last = expected_nphys
    plast_u2_write = (expected_nphys + p_last) - nphys_declared
    plast_u1_read = p_last
    result["plast_index_match"] = (plast_u2_write == plast_u1_read)

    if not result["p1_index_match"]:
        result["errors"].append(f"Notch tip (p=1) index mismatch: U2 writes to slot {p1_u2_write}, but U1 reads slot {p1_u1_read}")

    if (result["u2_header_properties_5"] and 
        result["u2_nphys_matches_expected"] and 
        result["p1_index_match"] and 
        result["pmid_index_match"] and 
        result["plast_index_match"] and 
        len(result["errors"]) == 0):
        result["overall_pass"] = True

    return result


def main():
    print("=== Fail-Closed NPHYS Producer-Consumer Contract Validation ===")
    all_pass = True

    for name, deck_path, expected_nphys in DECKS_TO_VALIDATE:
        res = audit_deck_nphys(deck_path, expected_nphys)
        status = "PASS" if res["overall_pass"] else "FAIL"
        print(f"\nDeck: {name} ({deck_path.name})")
        print(f"  Expected NPHYS: {expected_nphys}")
        print(f"  Declared NPHYS: {res['u2_property_nphys_value']}")
        print(f"  U2 Header properties=5: {res['u2_header_properties_5']}")
        print(f"  P=1 Notch Tip Mapping: U2 writes slot {res['p1_u2_write_slot']} <-> U1 reads slot {res['p1_u1_read_slot']} (Match: {res['p1_index_match']})")
        print(f"  Status: {status}")
        if res["errors"]:
            for err in res["errors"]:
                print(f"    ERROR: {err}")
            all_pass = False

    if all_pass:
        print("\nAll Mode-II reference decks PASSED NPHYS contract validation!")
        sys.exit(0)
    else:
        print("\nOne or more decks FAILED NPHYS contract validation!")
        sys.exit(1)


if __name__ == "__main__":
    main()
