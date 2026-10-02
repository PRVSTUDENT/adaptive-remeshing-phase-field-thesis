from pathlib import Path

dat_path = Path("/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.dat")
with open(dat_path) as f:
    for i in range(600):
        next(f)
    lines = [next(f) for _ in range(60)]

for i, l in enumerate(lines):
    print(f"{600+i}: {l.rstrip()}")
