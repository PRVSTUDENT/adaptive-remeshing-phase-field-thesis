import os
import re
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def search_production_verification():
    print("=== SEARCHING PRODUCTION VERIFICATION BATCH & CONTROL BATCH ===")
    for p in ROOT.rglob("*"):
        if "production_verification_batch" in str(p) or "mode_ii_control_batch" in str(p):
            if p.is_file() and p.suffix in [".json", ".md", ".csv", ".txt", ".py", ".sh"]:
                try:
                    txt = p.read_text(encoding="utf-8", errors="ignore")
                    for pat in ["0.29", "0.85", "529.", "639.", "533.", "peak", "stiffness"]:
                        if pat in txt:
                            print(f"[{p.relative_to(ROOT)}] contains '{pat}'")
                            lines = [l.strip() for l in txt.splitlines() if pat in l]
                            for l in lines[:5]:
                                print(f"    {l[:100]}")
                except Exception:
                    pass

if __name__ == "__main__":
    search_production_verification()
