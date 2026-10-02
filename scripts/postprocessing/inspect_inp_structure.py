#!/usr/bin/env python3
import sys
import os

def parse_inp(inp_path):
    if not os.path.exists(inp_path):
        inp_path = "M2STATE_FRACFIX_RESTART2R6.inp"
    with open(inp_path, "r") as f:
        lines = f.readlines()
        
    keywords = []
    for i, line in enumerate(lines):
        if line.startswith("*"):
            keywords.append((i+1, line.strip()))
            
    for lnum, kw in keywords:
        if any(x in kw for x in ["STEP", "OUTPUT", "BOUNDARY", "EQUATION", "USER ELEMENT", "ELEMENT", "INITIAL"]):
            print(f"{lnum:7d}: {kw}")

if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "M2STATE_FRACFIX_RESTART2R6.inp"
    parse_inp(p)
