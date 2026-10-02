from pathlib import Path

def inspect_adaptive_models():
    targets = [
        ("1386469", "MM adaptive", "models/generated/mode_ii/production_adaptive_batch/M2ADAPT_MM_FRACFIX_PROD"),
        ("1386470", "PK5 adaptive", "models/generated/mode_ii/production_adaptive_batch/M2ADAPT_PK5_FRACFIX_PROD"),
    ]
    
    for job_id, name, path_str in targets:
        p = Path(path_str)
        print(f"\n==========================================")
        print(f"AUDITING: Job {job_id} ({name}) in {p}")
        
        inps = list(p.glob("*.inp"))
        fors = list(p.glob("*.for"))
        
        inp_file = inps[0] if inps else None
        for_file = fors[0] if fors else None
        
        print(f"INP: {inp_file}")
        print(f"FOR: {for_file}")
        
        if for_file and for_file.exists():
            for_lines = for_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            for line in for_lines:
                line_str = line.strip()
                if "PROPS(" in line_str and "=" in line_str and not line_str.startswith("C"):
                    print(f"   FOR PROPS line: {line_str}")
                if "DEG" in line_str and "=" in line_str and not line_str.startswith("C"):
                    print(f"   FOR DEG line: {line_str}")
                    
        if inp_file and inp_file.exists():
            inp_lines = inp_file.read_text(encoding="utf-8", errors="ignore").splitlines()
            for i, line in enumerate(inp_lines):
                if line.startswith("*USER ELEMENT") or line.startswith("*UEL PROPERTY"):
                    print(f"   INP Line {i+1}: {line}")
                    for j in range(1, 4):
                        if i + j < len(inp_lines) and not inp_lines[i+j].startswith("*"):
                            print(f"      {inp_lines[i+j]}")

if __name__ == "__main__":
    inspect_adaptive_models()
