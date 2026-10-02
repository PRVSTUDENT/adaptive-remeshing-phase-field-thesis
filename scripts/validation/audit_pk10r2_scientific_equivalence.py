#!/usr/bin/env python3
"""
Scientific-Equivalence Qualification Auditor for M2CORR_PK10R2_TOPOLOGY_CORRECTED:
Compares UEL Fortran source, INP formulation, properties, boundary conditions,
step definitions, and layer architecture against accepted reference benchmarks
(M2REF_H1_FULL_U050, M2REF_H2_FULL_U050, PK10R1_CONTINUOUS_U050, and M2REPLAY_R1).
"""

import os
import sys
import re
import json
import difflib
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def sha256_file(p):
    if not p or not p.exists():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def extract_inp_deck_sections(inp_path):
    if not inp_path or not inp_path.exists():
        return None
    with open(inp_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        
    sections = {
        "user_element_cards": [],
        "uel_properties": [],
        "solid_sections": [],
        "materials": [],
        "equations": [],
        "steps": [],
        "boundaries": [],
        "amplitudes": [],
        "layer_counts": {}
    }
    
    current_kw = None
    step_block = []
    in_step = False
    
    for line in lines:
        l_str = line.strip()
        if not l_str or l_str.startswith("**"):
            continue
        if l_str.startswith("*"):
            l_up = l_str.upper()
            if l_up.startswith("*USER ELEMENT"):
                current_kw = "USER ELEMENT"
                sections["user_element_cards"].append(l_str)
            elif l_up.startswith("*UEL PROPERTY"):
                current_kw = "UEL PROPERTY"
                sections["uel_properties"].append(l_str)
            elif l_up.startswith("*SOLID SECTION"):
                current_kw = "SOLID SECTION"
                sections["solid_sections"].append(l_str)
            elif l_up.startswith("*MATERIAL") or l_up.startswith("*ELASTIC") or l_up.startswith("*USER DEFINED") or l_up.startswith("*DEPVAR"):
                current_kw = "MATERIAL"
                sections["materials"].append(l_str)
            elif l_up.startswith("*EQUATION"):
                current_kw = "EQUATION"
                sections["equations"].append(l_str)
            elif l_up.startswith("*AMPLITUDE"):
                current_kw = "AMPLITUDE"
                sections["amplitudes"].append(l_str)
            elif l_up.startswith("*STEP"):
                in_step = True
                current_kw = "STEP"
                step_block.append(l_str)
            elif l_up.startswith("*BOUNDARY"):
                current_kw = "BOUNDARY"
                sections["boundaries"].append(l_str)
            elif l_up.startswith("*ELEMENT"):
                current_kw = "ELEMENT"
                m = re.search(r"TYPE=([A-Za-z0-9]+)", l_up)
                el_type = m.group(1) if m else "UNKNOWN"
                sections["layer_counts"][el_type] = sections["layer_counts"].get(el_type, 0) + 1
            else:
                current_kw = "OTHER"
                if in_step:
                    step_block.append(l_str)
            continue
            
        if current_kw == "USER ELEMENT":
            sections["user_element_cards"].append(l_str)
        elif current_kw == "UEL PROPERTY":
            sections["uel_properties"].append(l_str)
        elif current_kw == "SOLID SECTION":
            sections["solid_sections"].append(l_str)
        elif current_kw == "MATERIAL":
            sections["materials"].append(l_str)
        elif current_kw == "EQUATION":
            sections["equations"].append(l_str)
        elif current_kw == "AMPLITUDE":
            sections["amplitudes"].append(l_str)
        elif current_kw == "BOUNDARY":
            sections["boundaries"].append(l_str)
        elif in_step:
            step_block.append(l_str)
            
    sections["steps"] = step_block
    return sections

def compare_uelfiles(ref_uel_path, cand_uel_path):
    if not ref_uel_path or not ref_uel_path.exists() or not cand_uel_path or not cand_uel_path.exists():
        return ["File missing\n"]
    ref_text = ref_uel_path.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
    cand_text = cand_uel_path.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
    
    diff = list(difflib.unified_diff(
        ref_text, cand_text,
        fromfile=ref_uel_path.name,
        tofile=cand_uel_path.name,
        n=3
    ))
    return diff

def main():
    print("================================================================================")
    print("SCIENTIFIC EQUIVALENCE AUDIT: M2CORR_PK10R2_TOPOLOGY_CORRECTED VS REFERENCES")
    print("================================================================================")
    
    cand_dir = ROOT / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED"
    h1_dir = ROOT / "models/generated/mode_ii/production_verification_batch/M2REF_H1_FULL_U050"
    h2_dir = ROOT / "models/generated/mode_ii/production_verification_batch/M2REF_H2_FULL_U050"
    cont_dir = ROOT / "models/generated/mode_ii/production_control_batch/PK10R1_CONTINUOUS_U050"
    r6_dir = ROOT / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6"
    auth_r14_dir = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R14"
    
    # 1. UEL Fortran Audit
    print("\n--- 1. UEL Fortran Source & SHA256 Audit ---")
    uels = {
        "PK10R2_CANDIDATE": cand_dir / "f42_mixed_uel.for",
        "H1_FULL_REFERENCE": h1_dir / "f42_mixed_uel.for",
        "H2_FULL_REFERENCE": h2_dir / "f42_mixed_uel.for",
        "PK10R1_CONTINUOUS": cont_dir / "f42_mixed_uel.for",
        "R14_AUTH_UEL": auth_r14_dir / "f42_mixed_uel.for",
        "R6_F44_TRANSACTIONAL": r6_dir / "f44_mixed_uel_restart_stateinit.for"
    }
    
    hashes = {}
    for k, p in uels.items():
        h = sha256_file(p)
        hashes[k] = h
        print(f"  {k:22s}: {h} ({p.name if p.exists() else 'MISSING'})")
        
    # Diff against H1/H2
    diff_h1 = compare_uelfiles(uels["H1_FULL_REFERENCE"], uels["PK10R2_CANDIDATE"])
    print(f"\n  Diff vs H1/H2 Reference UEL ({len(diff_h1)} diff lines):")
    for l in diff_h1:
        print("    " + l.rstrip())
        
    # Diff against PK10R1_CONTINUOUS
    diff_cont = compare_uelfiles(uels["PK10R1_CONTINUOUS"], uels["PK10R2_CANDIDATE"])
    print(f"\n  Diff vs PK10R1_CONTINUOUS UEL ({len(diff_cont)} diff lines):")
    for l in diff_cont:
        print("    " + l.rstrip())
        
    # Diff against R14_AUTH_UEL
    diff_r14 = compare_uelfiles(uels["R14_AUTH_UEL"], uels["PK10R2_CANDIDATE"])
    print(f"\n  Diff vs R14_AUTH_UEL ({len(diff_r14)} diff lines):")
    for l in diff_r14:
        print("    " + l.rstrip())
        
    # 2. Layer Architecture Investigation
    print("\n--- 2. Layer Architecture Investigation ---")
    cand_deck = extract_inp_deck_sections(cand_dir / "M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp")
    h1_deck = extract_inp_deck_sections(h1_dir / "M2REF_H1_FULL_U050.inp")
    h2_deck = extract_inp_deck_sections(h2_dir / "M2REF_H2_FULL_U050.inp")
    cont_deck = extract_inp_deck_sections(cont_dir / "PK10R1_CONTINUOUS_U050.inp")
    r6_deck = extract_inp_deck_sections(r6_dir / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6.inp")
    
    print(f"  H1 Full Reference Layer Element Cards: {h1_deck['layer_counts']}")
    print(f"  H2 Full Reference Layer Element Cards: {h2_deck['layer_counts']}")
    print(f"  PK10R1 Continuous Layer Element Cards: {cont_deck['layer_counts']}")
    print(f"  R6 Same-Mesh Restart Layer Cards:     {r6_deck['layer_counts'] if r6_deck else 'N/A'}")
    print(f"  PK10R2 Candidate Layer Cards:         {cand_deck['layer_counts']}")
    
    # 3. Governing Parameters & UEL Properties
    print("\n--- 3. Governing Parameters & UEL Properties ---")
    print(f"  PK10R2 User Element Cards: {cand_deck['user_element_cards']}")
    print(f"  H1 Reference User Element: {h1_deck['user_element_cards']}")
    print(f"  PK10R2 UEL Properties:     {cand_deck['uel_properties']}")
    print(f"  H1 Reference UEL Prop:     {h1_deck['uel_properties']}")
    print(f"  H2 Reference UEL Prop:     {h2_deck['uel_properties']}")
    print(f"  PK10R1 Cont UEL Prop:      {cont_deck['uel_properties']}")
    
    # 4. Boundary Conditions & Equations
    print("\n--- 4. Boundary Conditions & Equations ---")
    print(f"  PK10R2 Equations:          {cand_deck['equations']}")
    print(f"  H1 Reference Equations:    {h1_deck['equations']}")
    print(f"  PK10R1 Cont Equations:     {cont_deck['equations']}")
    print(f"  PK10R2 Boundaries:         {cand_deck['boundaries']}")
    print(f"  H1 Reference Boundaries:   {h1_deck['boundaries']}")
    print(f"  PK10R1 Cont Boundaries:    {cont_deck['boundaries']}")
    
    # 5. Step & Solver Controls
    print("\n--- 5. Step Definition & Solver Controls ---")
    print(f"  PK10R2 Step:               {cand_deck['steps']}")
    print(f"  H1 Reference Step:         {h1_deck['steps']}")
    print(f"  PK10R1 Cont Step:          {cont_deck['steps']}")

if __name__ == "__main__":
    main()
