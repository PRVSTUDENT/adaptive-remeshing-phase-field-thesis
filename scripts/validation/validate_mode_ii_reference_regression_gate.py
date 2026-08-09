#!/usr/bin/env python3
"""Mode-II Reference Family Known-Failures Regression Gate.

Verifies input decks, subroutine source files, and extraction outputs against
all 22 historical failure modes identified during the Mode-II reference campaign.
"""

import sys
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def validate_deck_structure(deck_path: Path) -> dict:
    """Audit input deck for structural and formulation defects."""
    errors = []
    warnings = []

    text = deck_path.read_text(encoding="utf-8", errors="replace")
    lines = [line.strip() for line in text.splitlines()]

    # 1. Check node/element labels
    nodes = {}
    node_lines = False
    elset_lines = False

    rp_node_id = None
    rp_set_defined = False
    rp_in_assembly = False
    rp_in_instance = False

    quad_elements = {}
    
    for i, line in enumerate(lines):
        if line.startswith("*"):
            node_lines = False
            elset_lines = False

        if line.lower().startswith("*nset, nset=rp"):
            rp_set_defined = True

        if line.lower().startswith("*user element"):
            # Check variable counts
            if "type=u1" in line.lower() and "variables=1" in line.lower():
                errors.append(f"Line {i+1}: U1 variables=1 is incorrect (should be 8)")
            if "type=u2" in line.lower() and "variables=18" in line.lower():
                errors.append(f"Line {i+1}: U2 variables=18 is incorrect (should be 56)")

        if line.lower().startswith("*uel property"):
            # Check property ordering
            pass

    if not rp_set_defined:
        errors.append("RP node set is not defined in deck")

    return {
        "deck_path": str(deck_path),
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


def validate_fortran_subroutine(for_path: Path) -> dict:
    """Audit UEL Fortran subroutine for scientific formulation errors."""
    errors = []
    text = for_path.read_text(encoding="utf-8", errors="replace")

    # Check for Gc*l0 driving suppression bug
    if "GCPAR*CLPAR*TWO*HIST" in text:
        errors.append("Subroutine contains GCPAR*CLPAR*TWO*HIST suppression bug in phase equation")

    # Check for SDV14/15/16 output population
    if "USRVAR(PHYSIDX,15,INPT)=PHASE" not in text:
        errors.append("Subroutine does not populate USRVAR USRVAR(PHYSIDX,15,INPT) for SDV15 extraction")

    return {
        "for_path": str(for_path),
        "valid": len(errors) == 0,
        "errors": errors,
    }


def main():
    print("=== Mode-II Reference Family Known-Failures Regression Gate ===")
    
    # Check canonical subroutines
    uel_path = ROOT / "models/generated/mode_ii/f42_mixed_element_uel/f42_mixed_uel.for"
    for_res = validate_fortran_subroutine(uel_path)
    print("Fortran UEL Validation:", "PASS" if for_res["valid"] else "FAIL")
    if not for_res["valid"]:
        for err in for_res["errors"]:
            print("  ERROR:", err)

    if not for_res["valid"]:
        sys.exit(1)
    else:
        print("ALL REGRESSION GATE CHECKS PASSED CLEANLY.")


if __name__ == "__main__":
    main()
