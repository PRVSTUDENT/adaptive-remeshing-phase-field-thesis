#!/usr/bin/env python3
"""
Inspect H1 and H2 reference INP decks for boundary conditions and equations
"""

import os
import glob

def inspect_h1_h2_inps():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    inps = glob.glob(os.path.join(base_dir, "models/**/*.inp"), recursive=True)
    
    for inp in inps:
        basename = os.path.basename(inp)
        if any(k in basename.upper() for k in ["H1", "H2", "UNIFORM", "REF"]):
            print(f"\n=======================================================")
            print(f"FILE: {os.path.relpath(inp, base_dir)}")
            print(f"=======================================================")
            with open(inp, "r", errors="ignore") as f:
                lines = f.readlines()
            for i, l in enumerate(lines):
                if any(k in l.upper() for k in ["*EQUATION", "*BOUNDARY", "*STEP"]):
                    if i > len(lines) - 200:
                        print(f"Line {i+1}: {l.strip()}")
                        for j in range(1, 3):
                            if i+j < len(lines):
                                print(f"  + {lines[i+j].strip()}")

if __name__ == "__main__":
    inspect_h1_h2_inps()
