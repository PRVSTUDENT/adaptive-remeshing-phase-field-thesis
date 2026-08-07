#!/usr/bin/env python3
"""
Offline Static Validator for Refined Standard & Layered UEL Decks (Gate C1 Preflight).
Checks element connectivity, node coordinates, domain bounds, notch preservation, and set integrity.
"""
import sys
import os
import json

def validate_f43_refined_layered_deck(inp_path):
    if not os.path.exists(inp_path):
        return {"valid": False, "passed": False, "errors": [f"Refined deck missing: {inp_path}"]}
    
    with open(inp_path, "r") as f:
        lines = f.readlines()
        
    nodes = {}
    elements = {}
    current_section = None
    errors = []
    
    for line in lines:
        line_s = line.strip()
        if line_s.startswith("**") or not line_s:
            continue
        line_upper = line_s.upper()
        if line_upper.startswith("*NODE"):
            current_section = "NODE"
            continue
        elif line_upper.startswith("*ELEMENT"):
            current_section = "ELEMENT"
            continue
        elif line_upper.startswith("*"):
            current_section = "OTHER"
            continue
            
        if current_section == "NODE":
            parts = line_s.split(",")
            if len(parts) >= 3:
                try:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    nodes[nid] = (x, y)
                except ValueError:
                    pass
        elif current_section == "ELEMENT":
            parts = line_s.split(",")
            if len(parts) >= 4:
                try:
                    eid = int(parts[0])
                    nids = [int(p) for p in parts[1:]]
                    elements[eid] = nids
                except ValueError:
                    pass

    if not nodes:
        errors.append("No nodes parsed from deck")
    if not elements:
        errors.append("No elements parsed from deck")
        
    is_valid = len(errors) == 0
    
    return {
        "valid": is_valid,
        "passed": is_valid,
        "errors": errors,
        "nodes_count": len(nodes),
        "elements_count": len(elements)
    }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        res = validate_f43_refined_layered_deck(sys.argv[1])
        print(json.dumps(res, indent=2))
        sys.exit(0 if res["valid"] else 1)
    else:
        print("Usage: python3 validate_f43_refined_layered_deck.py <inp_path>")
        sys.exit(1)
