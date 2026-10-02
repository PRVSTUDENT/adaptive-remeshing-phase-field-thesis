from pathlib import Path
import csv

csv_path = Path("/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/nonmatching_transfer_benchmarks/TARGET_NM1_RESTART/TARGET_NM1_INC29_PRIMARY_STATE.csv")
with open(csv_path) as f:
    reader = csv.DictReader(f)
    for r in reader:
        if r["is_inside"] == "False":
            print(r)
