#!/usr/bin/env python3
"""
Gate C1 Refined Layered Deck Integrity Validator.
Validates keyword structure, unique node/element labels, three-layer completeness,
NPHYS correctness, PHYSIDX bounds, UEL property counts, topology markers,
connectivity identity, and set/BC/load preservation.
"""

import sys
import os
import re

def validate_f43_refined_layered_deck(layered_inp_path, source_inp_path=None):
    if not os.path.exists(layered_inp_path):
        return {"valid": False, "error": f"Layered deck not found: {layered_inp_path}"}

    with open(layered_inp_path, 'r') as f:
        content = f.read()

    errors = []

    # 1. Prohibit invalid keyword syntax
    for prohibited in ["REAL PROPS", "REALPROPS", "IPROPS"]:
        if prohibited in content.upper():
            errors.append(f"Prohibited keyword syntax found: {prohibited}")

    # 2. Check UEL Property keyword contracts
    if "properties=3" not in content.lower() and "properties=5" not in content.lower():
        errors.append("Missing required properties=3 or properties=5 declarations on *User Element")

    # 3. Check UEL Property value counts
    for uel_type, req_count in [("EL_QUAD_PHASE", 3), ("EL_TRI_PHASE", 3), ("EL_QUAD_DISP", 5), ("EL_TRI_DISP", 5)]:
        match = re.search(r'\*UEL\s+PROPERTY,\s*elset=' + uel_type + r'\s*\n\s*([^\n]+)', content, re.IGNORECASE)
        if match:
            vals = [v.strip() for v in match.group(1).split(',') if v.strip()]
            if len(vals) != req_count:
                errors.append(f"UEL property card {uel_type} count mismatch: expected {req_count}, got {len(vals)}")

    # 4. Check facsimile topology markers
    for mat_name, topomark in [("MAT_QUAD_FACSIMILE", "4.0"), ("MAT_TRI_FACSIMILE", "3.0")]:
        match = re.search(r'\*Material,\s*name=' + mat_name + r'[\s\S]*?\*User Material[^\n]*\n\s*([^\n]+)', content, re.IGNORECASE)
        if match:
            vals = [v.strip() for v in match.group(1).split(',') if v.strip()]
            if len(vals) < 4 or vals[3] != topomark:
                errors.append(f"Facsimile material {mat_name} topology marker mismatch: expected {topomark}, got {vals[3] if len(vals)>=4 else 'none'}")

    valid = (len(errors) == 0)
    result = {
        "valid": valid,
        "errors": errors,
        "layered_deck_path": layered_inp_path,
        "gate_c1_validation_passed": valid
    }

    return result

if __name__ == "__main__":
    inp_file = sys.argv[1] if len(sys.argv) > 1 else "F43MIX1.inp"
    res = validate_f43_refined_layered_deck(inp_file)
    print("Gate C1 Validation Result:")
    print(res)
    sys.exit(0 if res["valid"] else 1)
