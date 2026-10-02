import os
import re
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def check_hpc_ledger():
    ledger = ROOT / "project_coordination/HPC_JOB_LEDGER.csv"
    if not ledger.exists():
        print(f"No HPC_JOB_LEDGER.csv at {ledger}")
        return
    with open(ledger, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            job_name = row.get("job_name", "")
            job_id = row.get("job_id", "")
            if any(k in job_name for k in ["H1", "H2", "M2REF", "M2CORR", "1389"]):
                print(f"{job_id:20s} | {job_name:42s} | {row.get('status',''):12s} | {row.get('notes','')[:80]}")

def search_text(query):
    print(f"\n--- Searching for '{query}' across repo ---")
    matches = []
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in [".json", ".md", ".csv", ".txt", ".py", ".sh", ".dat"]:
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
                if query in txt:
                    matches.append(str(p.relative_to(ROOT)))
            except Exception as e:
                pass
    for m in matches[:25]:
        print(f"  Found in {m}")
    if len(matches) > 25:
        print(f"  ... and {len(matches) - 25} more files")

if __name__ == "__main__":
    check_hpc_ledger()
    search_text("0.29483")
    search_text("0.29957")
    search_text("0.8593")
    search_text("0.8557")
    search_text("1389351")
    search_text("1389352")
