#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAND_INP = ROOT / "models/generated/mode_ii/verification_batch/M2REF_H0_EXACT_FRACFIX_REPRO/M2REF_H0_EXACT_FRACFIX_REPRO.inp"

def main():
    with CAND_INP.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if any(k in line for k in ["*UEL Property", "*User Material", "*Solid Section"]):
                print(f"Line {i}: {line.strip()}")

if __name__ == "__main__":
    main()
