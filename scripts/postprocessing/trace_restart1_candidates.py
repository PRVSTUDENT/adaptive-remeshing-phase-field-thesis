import os
from pathlib import Path

def trace_restart1_candidates():
    base = Path("models/generated/mode_ii/production_state_transfer_batch")
    if not base.exists():
        print("Base does not exist")
        return
        
    for p in sorted(base.iterdir()):
        if p.is_dir() and "RESTART1" in p.name:
            print(f"\n==========================================")
            print(f"CANDIDATE: {p.name}")
            inp_files = list(p.glob("*.inp"))
            for_files = list(p.glob("*.for"))
            
            if inp_files:
                lines = inp_files[0].read_text(encoding="utf-8", errors="ignore").splitlines()
                for i, l in enumerate(lines):
                    if "uel property" in l.lower() and ("e_u2" in l.lower() or "disp_quad" in l.lower()):
                        print(f"   INP {inp_files[0].name} Line {i+1}: {l}")
                        for j in range(1, 3):
                            if i + j < len(lines):
                                print(f"      {lines[i+j]}")
                                
            if for_files:
                flines = for_files[0].read_text(encoding="utf-8", errors="ignore").splitlines()
                for l in flines:
                    lstr = l.strip()
                    if ("PROPS(" in lstr or "E_K" in lstr or "PARK" in lstr or "DEG" in lstr) and "=" in lstr and not lstr.startswith("C"):
                        print(f"   FOR {for_files[0].name}: {lstr}")

if __name__ == "__main__":
    trace_restart1_candidates()
