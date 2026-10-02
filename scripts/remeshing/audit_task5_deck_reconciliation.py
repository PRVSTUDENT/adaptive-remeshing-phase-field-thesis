#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Forensic Input Deck Reconciliation for Task-5 Jobs:
- 1398090.mmaster02 (Standard Fixed Baseline)
- 1399632.mmaster02 (Adaptive 1.0% Predecessor)
- 1400368.mmaster02 (Adaptive 2.0% Deployed Run)
- 1400382.mmaster02 (Adaptive 5.0% Deployed Run)
"""

from __future__ import print_function
import os
import re
import sys
import hashlib
import json

def get_sha256(filepath):
    if not os.path.exists(filepath):
        return "FILE_NOT_FOUND"
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def parse_deck(filepath):
    if not os.path.exists(filepath):
        return {"error": "File not found: %s" % filepath}
    
    sha256 = get_sha256(filepath)
    with open(filepath, "r") as f:
        lines = [line.strip() for line in f]
        
    data = {
        "filepath": filepath,
        "sha256": sha256,
        "heading": "",
        "steps": [],
        "user_elements": [],
        "elements": {},
        "nodes_count": 0,
        "uel_properties": [],
        "solid_sections": [],
        "materials": [],
        "equations_count": 0,
        "boundary_conditions": [],
        "outputs": [],
        "restart_requests": [],
        "controls": []
    }
    
    current_step = None
    in_nodes = False
    in_elements = False
    in_step = False
    in_boundary = False
    elem_type = None
    
    for i, line in enumerate(lines):
        if not line or line.startswith("**"):
            continue
            
        if line.startswith("*"):
            in_nodes = False
            in_elements = False
            in_boundary = False
            
            upper_line = line.upper()
            
            if upper_line.startswith("*HEADING"):
                if i + 1 < len(lines) and not lines[i+1].startswith("*") and not lines[i+1].startswith("**"):
                    data["heading"] = lines[i+1]
                    
            elif upper_line.startswith("*USER ELEMENT"):
                data["user_elements"].append(line)
                
            elif upper_line.startswith("*NODE") and not upper_line.startswith("*NODE OUTPUT") and not upper_line.startswith("*NODE PRINT") and not upper_line.startswith("*NODE FILE"):
                in_nodes = True
                
            elif upper_line.startswith("*ELEMENT"):
                in_elements = True
                match = re.search(r"TYPE\s*=\s*([A-Za-z0-9_]+)", upper_line)
                elem_type = match.group(1) if match else "UNKNOWN"
                if elem_type not in data["elements"]:
                    data["elements"][elem_type] = 0
                    
            elif upper_line.startswith("*UEL PROPERTY"):
                if i + 1 < len(lines):
                    data["uel_properties"].append((line, lines[i+1]))
                    
            elif upper_line.startswith("*SOLID SECTION"):
                data["solid_sections"].append(line)
                
            elif upper_line.startswith("*MATERIAL"):
                data["materials"].append(line)
                
            elif upper_line.startswith("*EQUATION"):
                data["equations_count"] += 1
                
            elif upper_line.startswith("*BOUNDARY"):
                in_boundary = True
                
            elif upper_line.startswith("*STEP"):
                in_step = True
                current_step = {
                    "header": line,
                    "static": None,
                    "static_params": None,
                    "boundary": [],
                    "outputs": [],
                    "controls": []
                }
                data["steps"].append(current_step)
                
            elif upper_line.startswith("*STATIC"):
                if current_step is not None:
                    current_step["static"] = line
                    if i + 1 < len(lines):
                        current_step["static_params"] = lines[i+1]
                        
            elif upper_line.startswith("*CONTROLS"):
                if current_step is not None:
                    current_step["controls"].append(line)
                    if i + 1 < len(lines):
                        current_step["controls"].append(lines[i+1])
                else:
                    data["controls"].append(line)
                    
            elif upper_line.startswith("*OUTPUT") or upper_line.startswith("*NODE OUTPUT") or upper_line.startswith("*ELEMENT OUTPUT") or upper_line.startswith("*NODE PRINT"):
                if current_step is not None:
                    current_step["outputs"].append(line)
                    if i + 1 < len(lines) and not lines[i+1].startswith("*"):
                        current_step["outputs"].append(lines[i+1])
                else:
                    data["outputs"].append(line)
                    
            elif upper_line.startswith("*RESTART"):
                if current_step is not None:
                    current_step["outputs"].append(line)
                else:
                    data["restart_requests"].append(line)
                    
            elif upper_line.startswith("*END STEP"):
                in_step = False
                current_step = None
                
            continue
            
        if in_nodes:
            data["nodes_count"] += 1
            
        elif in_elements:
            if elem_type in data["elements"]:
                data["elements"][elem_type] += 1
                
        elif in_boundary:
            if current_step is not None:
                current_step["boundary"].append(line)
            else:
                data["boundary_conditions"].append(line)
                
    return data

if __name__ == "__main__":
    import pprint
    # Local paths or cluster paths
    deck_paths = {
        "1398090 (Standard Baseline)": "models/pandey_kumar_mode1/01_standard_pfm_reference/PK_MODE1_STANDARD_PFM.inp",
        "1399632 (Adaptive 1.0% Predecessor)": "models/pandey_kumar_mode1/02_proposed_adaptive_refined/predecessor_1399632/PK_MODE1_PROPOSED_PFM.inp",
        "1400368 (Adaptive 2.0% Deployed)": "models/pandey_kumar_mode1/06_production_adaptive_2pct/PK_MODE1_PROPOSED_PFM.inp",
        "1400382 (Adaptive 5.0% Deployed)": "models/pandey_kumar_mode1/07_production_adaptive_5pct/PK_MODE1_5PCT_PFM.inp",
        "02_proposed 2.0% Current": "models/pandey_kumar_mode1/02_proposed_adaptive_refined/PK_MODE1_PROPOSED_PFM.inp"
    }
    
    results = {}
    for name, p in deck_paths.items():
        if os.path.exists(p):
            results[name] = parse_deck(p)
        else:
            print("Missing local path:", p)
            
    with open("scripts/remeshing/deck_reconciliation_audit.json", "w") as out:
        json.dump(results, out, indent=2)
        
    print("Reconciliation Audit Dumped to scripts/remeshing/deck_reconciliation_audit.json")
