import os
import sys
import shutil
import hashlib
import json
import difflib

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def clean_lf(filepath):
    with open(filepath, "rb") as f:
        content = f.read()
    content_lf = content.replace(b"\r\n", b"\n")
    with open(filepath, "wb") as f:
        f.write(content_lf)

base_dir = r"D:\Master thesis\Adaptive remeshing\models\generated\mode_ii\stage_e_refinement_coarsening_batch"
r1_dir = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL")
r2_dir = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R2_VAL")

r1_inp = os.path.join(r1_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL.inp")
r2_inp = os.path.join(r2_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R2_VAL.inp")

with open(r1_inp, "r") as f:
    r1_lines = f.readlines()

# Reconstruct R2 directly from R1 lines
# In Step 3 (around lines 101799-101815):
# change static: 0.001, 1.0, 1.0e-11, 1.0 -> 0.001, 1.0, 5.0e-12, 1.0
# change controls: 4, 8, 9, 16, 10, 4, 50, 12 -> 4, 8, 9, 16, 10, 4, 50, 13
# In Step 4 (around lines 101816-101835):
# KEEP STATIC: 0.001, 1.0, 1.0e-11, 0.02
# KEEP CONTROLS: 4, 8, 9, 16, 10, 4, 50, 12

r2_lines = []
in_step3 = False
in_step4 = False
s3_static_modified = False
s3_controls_modified = False

for idx, line in enumerate(r1_lines):
    l_strip = line.strip()
    if "*STEP, NAME=PHASE_RELEASE" in line:
        in_step3 = True
        in_step4 = False
    elif "*STEP, NAME=CONTINUATION" in line:
        in_step3 = False
        in_step4 = True
    elif "*END STEP" in line:
        in_step3 = False
        in_step4 = False

    if in_step3 and l_strip == "0.001, 1.0, 1.0e-11, 1.0":
        r2_lines.append("0.001, 1.0, 5.0e-12, 1.0\n")
        s3_static_modified = True
    elif in_step3 and l_strip == "4, 8, 9, 16, 10, 4, 50, 12":
        r2_lines.append("4, 8, 9, 16, 10, 4, 50, 13\n")
        s3_controls_modified = True
    else:
        r2_lines.append(line)

assert s3_static_modified, "Step 3 STATIC was not modified!"
assert s3_controls_modified, "Step 3 CONTROLS was not modified!"

with open(r2_inp, "w") as f:
    f.writelines(r2_lines)
clean_lf(r2_inp)

# Ensure LF on R1 for diff
clean_lf(r1_inp)

with open(r1_inp, "r") as f1, open(r2_inp, "r") as f2:
    r1_norm = f1.readlines()
    r2_norm = f2.readlines()

diff = list(difflib.unified_diff(r1_norm, r2_norm, fromfile="1391300_R1", tofile="M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R2_VAL", lineterm="\n"))

print("UNIFIED DIFF LENGTH (lines):", len(diff))
print("--- UNIFIED DIFF ---")
for l in diff:
    print(l.rstrip())
print("--------------------")

