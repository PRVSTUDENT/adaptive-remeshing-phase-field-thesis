from pathlib import Path
import re

dat_path = Path("/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.dat")
with open(dat_path) as f:
    lines = [next(f) for _ in range(3000)]

for i, l in enumerate(lines):
    if any(k in l for k in ["INCREMENT", "NODE", "U1", "RF1", "12383"]):
        print(f"{i}: {l.rstrip()[:100]}")
