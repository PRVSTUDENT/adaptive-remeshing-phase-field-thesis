#!/usr/bin/env python3
"""
F132DIAG Semantic Input Deck Comparison Script
Task ID: F132DIAG-M2-CORRECTED-H2-VS-PK10R1-MODEL-EQUIVALENCE-AND-MESH-CONVERGENCE1
"""

import sys
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

H2_INP = ROOT / "models/generated/mode_ii/production_verification_batch/M2CORR_H2_FULL_U050/M2CORR_H2_FULL_U050.inp"
PK10_INP = ROOT / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.inp"

def extract_deck_keywords(inp_path):
    keywords = {}
    current_kw = None
    current_lines = []
    
    with open(inp_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_s = line.strip()
            if line_s.startswith("**"):
                continue
            if line_s.startswith("*"):
                if current_kw:
                    keywords[current_kw] = current_lines
                current_kw = line_s.upper()
                current_lines = []
            elif current_kw:
                current_lines.append(line_s)
                
        if current_kw:
            keywords[current_kw] = current_lines
            
    return keywords

def main():
    h2_kw = extract_deck_keywords(H2_INP)
    pk10_kw = extract_deck_keywords(PK10_INP)

    print("================================================================================")
    print("F132DIAG SEMANTIC INPUT DECK COMPARISON")
    print("================================================================================")

    print("\nH2 Keywords:")
    for k in sorted(h2_kw.keys()):
        if not k.startswith("*NODE") and not k.startswith("*ELEMENT"):
            print(f"  {k}: {h2_kw[k]}")

    print("\nPK10R1 Keywords:")
    for k in sorted(pk10_kw.keys()):
        if not k.startswith("*NODE") and not k.startswith("*ELEMENT"):
            print(f"  {k}: {pk10_kw[k]}")

if __name__ == "__main__":
    main()
