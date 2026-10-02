#!/usr/bin/env python3
"""
Deep Forensic Audit of PK10R2 (1390043.mmaster02) vs H1/H2 Reference Models
"""

import os
import sys
import glob
import re

def audit_equations_and_bcs():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print("Base Dir:", base_dir)
    
    # Check all INP files in models/
    inp_files = glob.glob(os.path.join(base_dir, "models/**/*.inp"), recursive=True)
    print(f"Found {len(inp_files)} INP files in models/")
    
    for inp in inp_files:
        with open(inp, "r", errors="ignore") as f:
            lines = f.readlines()
            
        eq_lines = []
        for i, line in enumerate(lines):
            if "*EQUATION" in line.upper():
                eq_lines.append((i+1, lines[i:i+6]))
                
        if eq_lines:
            print(f"\n--- INP: {os.path.relpath(inp, base_dir)} ---")
            for line_no, chunk in eq_lines:
                print(f"  Line {line_no}:")
                for c in chunk:
                    print("   ", c.strip())

if __name__ == "__main__":
    audit_equations_and_bcs()
