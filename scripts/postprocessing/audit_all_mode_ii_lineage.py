import os
import re
import hashlib
from pathlib import Path

def sha256(path):
    if not path.exists():
        return "FILE_NOT_FOUND"
    return hashlib.sha256(path.read_bytes()).hexdigest()

def audit_models():
    # Search for all relevant candidate directories
    targets = [
        ("1386372", "H0 uniform", "models/generated/mode_ii/h0_endpoint_corrected_serial"),
        ("1386447", "H1 uniform", "models/generated/mode_ii/h1_uniform_serial"),
        ("1386448", "H2 uniform", "models/generated/mode_ii/h2_uniform_serial"),
        ("1386469", "MM adaptive", "models/generated/mode_ii/adaptive_production_batch/M2ADAPT_MM_FRACFIX_PROD"),
        ("1386470", "PK5 adaptive", "models/generated/mode_ii/adaptive_production_batch/M2ADAPT_PK5_FRACFIX_PROD"),
        ("1388948", "Restart1 source", "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6R2"),
        ("1389229", "Restart2 R2R7", "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R7"),
        ("R2R8", "Restart2 R2R8", "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R8"),
    ]
    
    results = []
    
    for job_id, name, path_str in targets:
        p = Path(path_str)
        if not p.exists():
            # Search alternative paths
            print(f"Directory {path_str} not found directly, searching...")
            matches = list(Path(".").glob(f"**/{Path(path_str).name}"))
            if matches:
                p = matches[0]
            else:
                print(f"Could not find {path_str}")
                continue
                
        print(f"\n==========================================")
        print(f"AUDITING: Job {job_id} ({name}) in {p}")
        
        inps = list(p.glob("*.inp"))
        fors = list(p.glob("*.for"))
        
        inp_file = inps[0] if inps else None
        for_file = fors[0] if fors else None
        
        print(f"INP: {inp_file}")
        print(f"FOR: {for_file}")
        
        for_sha = sha256(for_file) if for_file else "NONE"
        print(f"FOR SHA256: {for_sha}")
        
        # Analyze FOR file
        props_in_for = {}
        if for_file and for_file.exists():
            for_lines = for_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line in for_lines:
                line_str = line.strip()
                if "PROPS(" in line_str and "=" in line_str and not line_str.startswith("C"):
                    print(f"   FOR PROPS line: {line_str}")
                if "N_PHYS" in line_str and "=" in line_str and not line_str.startswith("C"):
                    print(f"   FOR N_PHYS line: {line_str}")
                if "PHYSIDX" in line_str and "=" in line_str and not line_str.startswith("C"):
                    print(f"   FOR PHYSIDX line: {line_str}")
                if "DEG" in line_str and "=" in line_str and not line_str.startswith("C"):
                    print(f"   FOR DEG line: {line_str}")
                    
        # Analyze INP file
        if inp_file and inp_file.exists():
            inp_lines = inp_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            for i, line in enumerate(inp_lines):
                if line.startswith("*USER ELEMENT") or line.startswith("*UEL PROPERTY"):
                    print(f"   INP Line {i+1}: {line}")
                    for j in range(1, 4):
                        if i + j < len(inp_lines) and not inp_lines[i+j].startswith("*"):
                            print(f"      {inp_lines[i+j]}")

if __name__ == "__main__":
    audit_models()
