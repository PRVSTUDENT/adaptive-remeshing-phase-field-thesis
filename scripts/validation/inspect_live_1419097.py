#!/usr/bin/env python3
import glob
import json
import os
import sys

base = "/scratch9/pr21vyci/runs/mode1_c4_package150_c1_2_continuation_r2/continuation_1419097.mmaster02"
dirs = sorted(glob.glob(os.path.join(base, "P150_S1_*_00_mechanical")))
print(f"Total mechanical solves discovered in Step 1: {len(dirs)}")

for d in dirs[-15:]:
    epath = os.path.join(d, "endpoint.json")
    if os.path.exists(epath):
        with open(epath) as f:
            data = json.load(f)
        outer = os.path.basename(d).split("_")[2]
        rf2 = float(data.get("rf2_kN", 0.0))
        frac = float(data.get("fracture_kNmm", 0.0))
        el = float(data.get("elastic_kNmm", 0.0))
        print(f"Outer {outer}: RF2 = {rf2:.6f} kN ({rf2*1000:.3f} N), Fracture = {frac:.6e} kNmm, Elastic = {el:.6e} kNmm")
