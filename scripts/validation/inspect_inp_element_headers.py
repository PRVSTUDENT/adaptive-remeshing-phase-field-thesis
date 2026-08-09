#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REF_INP = ROOT / "models/generated/mode_ii/h0_endpoint_corrected_serial/ModeII_H0_endpoint_corrected_serial.inp"
CAND_INP = ROOT / "models/generated/mode_ii/verification_batch/M2REF_H0_EXACT_FRACFIX_REPRO/M2REF_H0_EXACT_FRACFIX_REPRO.inp"

def print_element_headers(path: Path, label: str):
    print(f"=== Element Headers for {label} ===")
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if line.strip().lower().startswith("*element"):
                print(f"Line {i}: {line.strip()}")
            elif line.strip().lower().startswith("*node"):
                print(f"Line {i}: {line.strip()}")

if __name__ == "__main__":
    print_element_headers(REF_INP, "REF INP")
    print()
    print_element_headers(CAND_INP, "CAND INP")
