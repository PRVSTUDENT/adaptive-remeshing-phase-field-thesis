import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def search_tasks():
    with open(ROOT / "project_coordination/TASK_LEDGER.csv", "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            t_id = row.get("task_id", "")
            t_desc = row.get("task_description", "")
            t_notes = row.get("notes", "")
            if any(k in t_id or k in t_desc or k in t_notes for k in ["H1", "H2", "M2REF", "M2CORR", "uniform", "reference", "stiffness"]):
                print(f"[{t_id}] -> {t_desc[:100]} | notes: {t_notes[:100]}")

if __name__ == "__main__":
    search_tasks()
