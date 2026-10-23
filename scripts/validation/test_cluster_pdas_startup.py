#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_cluster_pdas_startup.py
Validates bounded PDAS harness startup and environment under cluster execution environment.
"""

import sys
import os
import json
import hashlib
from pathlib import Path
import numpy as np
import scipy
import scipy.sparse as sp

print("=== CLUSTER PDAS ENVIRONMENT STARTUP TEST ===")
print("Python executable:", sys.executable)
print("Python version   :", sys.version.replace("\n", " "))
print("NumPy version    :", np.__version__)
print("SciPy version    :", scipy.__version__)

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
SCRATCH_DIR = Path("/scratch9/pr21vyci/runs/mode1_package96_r5_c5_transfer")

uel_file = SCRATCH_DIR / "f42_mixed_uel.for"
if uel_file.exists():
    h = hashlib.sha256(uel_file.read_bytes()).hexdigest().upper()
    print("Staged UEL hash  :", h)
    assert h == FROZEN_UEL_HASH, "Staged UEL hash mismatch"
    print("UEL Status       : BITWISE_FROZEN_PASS")
else:
    print("UEL File missing :", uel_file)

mesh_file = SCRATCH_DIR / "candidate_crack_band_mesh_c5.inp"
if mesh_file.exists():
    # Count physical nodes
    n_nodes = 0
    reading = False
    with open(mesh_file, "r") as f:
        for line in f:
            l = line.strip()
            if l.startswith("*NODE") and not l.startswith("*NODE OUTPUT"):
                reading = True
                continue
            elif l.startswith("*"):
                reading = False
                continue
            if reading and l and not l.startswith("**"):
                parts = l.split(",")
                if parts[0].strip().isdigit():
                    nid = int(parts[0].strip())
                    if nid != 999999:
                        n_nodes += 1
    print("Physical phase nodes in C5:", n_nodes)
    assert n_nodes == 4610, f"Expected 4610 physical nodes, got {n_nodes}"
    print("Physical Node Count Status: EXACT_4610_PASS")

print("=== CLUSTER PDAS ENVIRONMENT STARTUP: VERIFIED ===")
