from pathlib import Path
import re

dat_path = Path("/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.dat")
with open(dat_path) as f:
    for i, line in enumerate(f):
        if "NODE PRINT" in line or "N O D E   O U T P U T" in line or "N O D E" in line:
            print(f"Line {i}: {line.strip()[:100]}")
        if i > 5000:
            break
