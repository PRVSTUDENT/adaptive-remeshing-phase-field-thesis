#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Write STAGE_D_COMMITTED_STATE.bin in exact Fortran UNFORMATTED sequential record format.
Capacity: N_CAPACITY = 100,000 elements.
Record 1: SV_PHASE_COMMITTED (100,000 doubles = 800,000 bytes)
Record 2: SV_H_COMMITTED (100,000 x 4 doubles = 3,200,000 bytes)
Total Size: 4,000,016 bytes.
"""

import os
import struct
import numpy as np

def write_fortran_committed_state_bin(bin_path, n_phys, tgt_d_elem, tgt_H_gp):
    N_CAPACITY = 100000
    
    # 1. SV_PHASE_COMMITTED array
    sv_phase = np.zeros(N_CAPACITY, dtype=np.float64)
    for eid in range(1, min(n_phys + 1, N_CAPACITY + 1)):
        sv_phase[eid - 1] = tgt_d_elem.get(eid, 0.0)
        
    # 2. SV_H_COMMITTED array (100000 x 4)
    # Fortran column-major order for array (N_CAPACITY, 4):
    # element 1 GP 1..4, element 2 GP 1..4 ... or in Fortran (N, 4): column 1 is all GP1s, column 2 is all GP2s...
    # In Fortran: SV_H(I, KPT) -> first dimension is I (1..100000), second is KPT (1..4)
    # So in memory order: KPT=1 (all I), KPT=2 (all I), KPT=3 (all I), KPT=4 (all I)
    sv_h = np.zeros((N_CAPACITY, 4), dtype=np.float64)
    for eid in range(1, min(n_phys + 1, N_CAPACITY + 1)):
        for k in range(4):
            sv_h[eid - 1, k] = tgt_H_gp[eid - 1, k]
            
    # Write Fortran sequential unformatted file
    rec1_len = N_CAPACITY * 8 # 800,000 bytes
    rec2_len = N_CAPACITY * 4 * 8 # 3,200,000 bytes
    
    with open(bin_path, "wb") as f:
        # Record 1
        f.write(struct.pack("i", rec1_len))
        f.write(sv_phase.tobytes())
        f.write(struct.pack("i", rec1_len))
        
        # Record 2 (Column-major Fortran order)
        f.write(struct.pack("i", rec2_len))
        f.write(sv_h.flatten(order='F').tobytes())
        f.write(struct.pack("i", rec2_len))
        
    file_size = os.path.getsize(bin_path)
    print("Wrote Fortran binary state: %s (Size: %d bytes, expected: 4000016)" % (bin_path, file_size))
    assert file_size == 4000016, "Error: File size is %d, expected 4000016" % file_size

if __name__ == "__main__":
    out_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL"
    bin_path = os.path.join(out_dir, "STAGE_D_COMMITTED_STATE.bin")
    dummy_d = {i: 0.1 for i in range(1, 18361)}
    dummy_h = np.full((18360, 4), 0.05)
    write_fortran_committed_state_bin(bin_path, 18360, dummy_d, dummy_h)
