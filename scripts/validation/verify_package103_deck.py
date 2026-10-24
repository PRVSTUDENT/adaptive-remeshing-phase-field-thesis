#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_package103_deck.py
Audits and validates the newly generated Package 103 input deck and PBS script.
"""

import sys
import hashlib
from pathlib import Path
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def verify():
    pkg_dir = REPO_ROOT / "models/pandey_kumar_mode1/103_c5_h1_transfer_pilot"
    deck_path = pkg_dir / "M1_C5_PACKAGE103_H1_PILOT.inp"
    uel_path = pkg_dir / "f42_mixed_uel.for"
    pbs_path = pkg_dir / "submit_M1_C5_PACKAGE103_H1_PILOT.pbs"
    manifest_path = pkg_dir / "PACKAGE_MANIFEST.json"
    d_npy = REPO_ROOT / "results/validation/mode1_f1597/c5_h1_bound_constrained_d.npy"

    assert deck_path.exists(), f"Missing {deck_path}"
    assert uel_path.exists(), f"Missing {uel_path}"
    assert pbs_path.exists(), f"Missing {pbs_path}"
    assert manifest_path.exists(), f"Missing {manifest_path}"
    assert d_npy.exists(), f"Missing {d_npy}"

    # 1. Check frozen UEL hash
    with open(uel_path, "rb") as f:
        actual_uel = hashlib.sha256(f.read()).hexdigest().upper()
    assert actual_uel == FROZEN_UEL_HASH, f"UEL hash mismatch! Got {actual_uel}"
    print(f"[PASS] Bitwise Frozen UEL Verified: {actual_uel}")

    # 2. Check input deck syntax
    lines = deck_path.read_text(encoding="utf-8").splitlines()
    in_init_cond = False
    init_lines = []
    bc_damage_lines = []

    for i, line in enumerate(lines):
        l = line.strip()
        if not l or l.startswith("**"): continue
        if l.startswith("*INITIAL CONDITIONS, TYPE=SOLUTION"):
            in_init_cond = True
            continue
        elif l.startswith("*"):
            if in_init_cond:
                in_init_cond = False

        if in_init_cond:
            init_lines.append((i+1, l))

        if ", 3, 3," in l and not l.startswith("*"):
            bc_damage_lines.append(l)

    # Check 3-line card syntax (<= 8 fields per card)
    print(f"Auditing {len(init_lines)} *INITIAL CONDITIONS data lines...")
    assert len(init_lines) == 4440 * 9, f"Expected 39,960 lines, got {len(init_lines)}"
    
    max_fields = 0
    for line_num, text in init_lines:
        fields = [f.strip() for f in text.split(",") if f.strip()]
        max_fields = max(max_fields, len(fields))
        if len(fields) > 8:
            raise ValueError(f"Line {line_num} violates card limit: {len(fields)} fields! Text: {text}")

    print(f"[PASS] All {len(init_lines)} lines strictly satisfy <= 8 fields per card (max observed: {max_fields})")

    # 3. Check damage BCs
    d_H1 = np.load(d_npy)
    assert len(bc_damage_lines) == 4610, f"Expected 4610 damage BC lines, got {len(bc_damage_lines)}"
    for idx, bc_str in enumerate(bc_damage_lines):
        parts = [p.strip() for p in bc_str.split(",")]
        nid = int(parts[0])
        val = float(parts[3])
        # Compare with d_H1[idx]
        assert abs(val - d_H1[idx]) < 1e-9, f"Damage mismatch at node {nid}: {val} vs {d_H1[idx]}"

    print(f"[PASS] All 4,610 damage boundary condition values match qualified H^1 damage field")

    # 4. Check PBS script directives
    pbs_text = pbs_path.read_text(encoding="utf-8")
    assert "#PBS -m abe" in pbs_text, "Missing #PBS -m abe"
    assert "pr21vyci@mailserver.tu-freiberg.de" in pbs_text, "Missing notification recipient"
    assert "job_notifications.sh" in pbs_text, "Missing job_notifications.sh sourcing"
    assert "notify_start" in pbs_text, "Missing notify_start"
    assert "notification_install_terminal_trap" in pbs_text, "Missing terminal trap"
    print("[PASS] Dual-channel notifications and shell traps verified in PBS script")

    print("\nPackage 103 deck audit: ALL 4 CHECKS PASSED!")

if __name__ == "__main__":
    verify()
