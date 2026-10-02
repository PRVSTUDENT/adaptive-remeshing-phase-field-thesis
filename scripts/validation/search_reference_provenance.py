import os
import re
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def find_in_files():
    patterns = [
        r"0\.2995[0-9]*",
        r"0\.2948[0-9]*",
        r"0\.859[0-9]*",
        r"0\.855[0-9]*",
        r"1389351",
        r"1389352",
        r"138922[0-9]",
        r"138923[0-9]",
        r"138924[0-9]",
        r"M2CORR_H1",
        r"M2CORR_H2"
    ]
    
    print("=== SEARCHING PATTERNS IN DOCS, LOGS, LEDGERS, AND RUNS ===")
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in [".json", ".md", ".csv", ".py", ".txt"]:
            # skip large datasets
            if p.stat().st_size > 2_000_000:
                continue
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
                for pat in patterns:
                    m = re.findall(pat, txt)
                    if m:
                        lines = [line.strip() for line in txt.splitlines() if re.search(pat, line)]
                        for l in lines[:5]:
                            print(f"[{p.relative_to(ROOT)}] ({pat}): {l[:120]}")
            except Exception:
                pass

if __name__ == "__main__":
    find_in_files()
