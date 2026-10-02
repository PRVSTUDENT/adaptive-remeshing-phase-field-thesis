#!/usr/bin/env python3
"""
Remove illegal wrapping elements from test_r2r5_step1.inp and test solve.
"""
from pathlib import Path

def test_without_wrapping():
    inp_path = Path("/home/pr21vyci/test_r2r5_step1.inp")
    with open(inp_path, "r", errors="ignore") as f:
        lines = f.readlines()
        
    bad_eids = {9720, 9840, 19596, 19716, 29472, 29592}
    
    clean_lines = []
    in_ic = False
    for line in lines:
        if line.startswith("*INITIAL CONDITIONS, TYPE=SOLUTION"):
            in_ic = True
            clean_lines.append(line)
            continue
        elif in_ic and line.startswith("*"):
            in_ic = False
            
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if parts:
            try:
                eid = int(parts[0])
                if eid in bad_eids:
                    continue
            except ValueError:
                pass
        clean_lines.append(line)
        
    out_path = Path("/home/pr21vyci/test_r2r5_clean.inp")
    with open(out_path, "w") as f:
        f.writelines(clean_lines)
        
    print(f"Created clean inp with {len(clean_lines)} lines")

if __name__ == "__main__":
    test_without_wrapping()
