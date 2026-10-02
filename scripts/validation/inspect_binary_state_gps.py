#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inspect all 4 GPs of Target Elements around the crack tip from STAGE_D_COMMITTED_STATE.bin using little-endian unpack.
"""

import os
import sys
import struct

ROOT = "/home/pr21vyci/projects/adaptive-remeshing"
if not os.path.exists(ROOT):
    ROOT = "D:/Master thesis/Adaptive remeshing"
bin_path = os.path.join(ROOT, "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/STAGE_D_COMMITTED_STATE.bin")

def inspect_bin():
    print("Inspecting binary state file (little-endian): %s" % bin_path)
    with open(bin_path, "rb") as fp:
        # Record 1: 100,000 double precision floats (little-endian)
        h1 = struct.unpack("<I", fp.read(4))[0]
        n_doubles_1 = h1 // 8
        d_phase = struct.unpack("<%dd" % n_doubles_1, fp.read(h1))
        t1 = struct.unpack("<I", fp.read(4))[0]
        
        # Record 2: 400,000 double precision floats (little-endian, column-major: 100000 x 4)
        h2 = struct.unpack("<I", fp.read(4))[0]
        n_doubles_2 = h2 // 8
        h_flat = struct.unpack("<%dd" % n_doubles_2, fp.read(h2))
        t2 = struct.unpack("<I", fp.read(4))[0]
        
    print("Record 1 header: %d bytes, max d: %.6f (len: %d)" % (h1, max(d_phase), len(d_phase)))
    print("Record 2 header: %d bytes, max H: %.6f (len: %d)" % (h2, max(h_flat), len(h_flat)))
    
    print("\n--- TARGET ELEMENTS AROUND CRACK TIP IN BINARY FILE ---")
    # In column-major Fortran array H(100000, 4):
    # Element idx (0-indexed) has GP1 at idx + 0*100000, GP2 at idx + 1*100000, GP3 at idx + 2*100000, GP4 at idx + 3*100000
    for eid in [4369, 4370, 4371, 4372, 4373, 4463, 4464, 4465, 4466]:
        idx = eid - 1
        d_val = d_phase[idx]
        gp1 = h_flat[idx + 0*100000]
        gp2 = h_flat[idx + 1*100000]
        gp3 = h_flat[idx + 2*100000]
        gp4 = h_flat[idx + 3*100000]
        max_h = max(gp1, gp2, gp3, gp4)
        print("Target Element %4d: d_avg = %.6f | H GP1: %.6f, GP2: %.6f, GP3: %.6f, GP4: %.6f | max H = %.6f" % (
            eid, d_val, gp1, gp2, gp3, gp4, max_h))

if __name__ == "__main__":
    inspect_bin()
