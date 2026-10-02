from pathlib import Path

def inspect_mm_inp():
    p = Path("models/generated/mode_ii/production_adaptive_batch/M2ADAPT_MM_FRACFIX_PROD/M2ADAPT_MM_FRACFIX_PROD.inp")
    lines = p.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.startswith("*USER ELEMENT") or line.startswith("*UEL PROPERTY"):
            print(f"Line {i+1}: {line}")
            for j in range(1, 4):
                if i + j < len(lines) and not lines[i+j].startswith("*"):
                    print(f"   {lines[i+j]}")

if __name__ == "__main__":
    inspect_mm_inp()
