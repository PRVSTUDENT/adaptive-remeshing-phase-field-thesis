import os
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def find_job_evidence():
    job_ids = [
        "1389686",
        "1389687",
        "1389684",
        "1389707",
        "1389718",
        "1389715",
        "1389719",
        "1389721"
    ]
    
    print("=== SEARCHING EVIDENCE FILES FOR HISTORICAL JOBS ===")
    for jid in job_ids:
        print(f"\n--- Looking for {jid} ---")
        found = []
        for p in ROOT.rglob(f"*{jid}*"):
            found.append(str(p.relative_to(ROOT)))
        for f in found[:10]:
            print(f"  {f}")
        if len(found) > 10:
            print(f"  ... and {len(found)-10} more files")

if __name__ == "__main__":
    find_job_evidence()
