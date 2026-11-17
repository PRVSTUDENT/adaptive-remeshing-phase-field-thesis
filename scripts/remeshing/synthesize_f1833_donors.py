# -*- coding: utf-8 -*-
"""
scripts/remeshing/synthesize_f1833_donors.py
============================================
Task F1833: Synthesize State-Consistent Multi-State Recovery Donors for Cases 1, 2, 3.
Uses MultiStateRecoveryDonorBuilder.synthesize_envelope_odb from
reusable_2d_adaptive_framework.py, which implements:
    eta_e = max_k ( MISESERI_{e,k} / MISESAVG_k )
"""
from __future__ import print_function
import os
import sys
import shutil
import hashlib
import time

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
framework_dir = os.path.join(REPO_ROOT, "scripts", "remeshing")
if framework_dir not in sys.path:
    sys.path.insert(0, framework_dir)

from reusable_2d_adaptive_framework import MultiStateRecoveryDonorBuilder

F1833_BASE = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "273_f1833_state_consistent_normalization")

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def synthesize_case1():
    print("\n" + "="*80)
    print("SYNTHESIZING CASE 1 STATE-CONSISTENT RECOVERY DONOR (5 STATES)")
    print("="*80)
    c1_dir = os.path.join(F1833_BASE, "case1")
    if not os.path.exists(c1_dir):
        os.makedirs(c1_dir)
    src_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case1")
    states = [
        "PK_C1_STATE1_INITIATION.odb",
        "PK_C1_STATE2_EARLY_PROPAGATION.odb",
        "PK_C1_STATE3_MID_PROPAGATION.odb",
        "PK_C1_STATE4_OUTER_PROPAGATION.odb",
        "PK_C1_STATE5_TERMINAL_SEVERANCE.odb"
    ]
    solved_odbs = [os.path.join(src_dir, s) for s in states]
    for p in solved_odbs:
        if not os.path.exists(p):
            raise IOError("Missing solved recovery ODB: %s" % p)
    target_odb = os.path.join(c1_dir, "PK_CASE1_MULTISTATE_RECOVERY.odb")
    t0 = time.time()
    MultiStateRecoveryDonorBuilder.synthesize_envelope_odb(
        solved_odbs=solved_odbs,
        target_odb_path=target_odb,
        step_name='RECOVERY_STEP',
        frame_desc="Case 1 State-Consistent Relative Error Envelope (5 States)"
    )
    t_el = time.time() - t0
    sha = compute_sha256(target_odb)
    sz = os.path.getsize(target_odb)
    print("Synthesized Case 1 Donor in %.2f s:" % t_el)
    print("  Path:   %s" % target_odb)
    print("  Size:   %d bytes" % sz)
    print("  SHA256: %s" % sha)
    return target_odb, sha, t_el

def synthesize_case2():
    print("\n" + "="*80)
    print("SYNTHESIZING CASE 2 STATE-CONSISTENT RECOVERY DONOR (4 STATES)")
    print("="*80)
    c2_dir = os.path.join(F1833_BASE, "case2")
    if not os.path.exists(c2_dir):
        os.makedirs(c2_dir)
    src_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case2")
    states = [
        "PK_C2_STATE1_PREANALYSIS.odb",
        "PK_C2_STATE2_HOLE_ARREST.odb",
        "PK_C2_STATE3_DISTAL_NUCLEATION.odb",
        "PK_C2_STATE4_OUTER_PROPAGATION.odb"
    ]
    solved_odbs = [os.path.join(src_dir, s) for s in states]
    for p in solved_odbs:
        if not os.path.exists(p):
            raise IOError("Missing solved recovery ODB: %s" % p)
    target_odb = os.path.join(c2_dir, "PK_HOLE_MULTISTATE_RECOVERY.odb")
    t0 = time.time()
    MultiStateRecoveryDonorBuilder.synthesize_envelope_odb(
        solved_odbs=solved_odbs,
        target_odb_path=target_odb,
        step_name='RECOVERY_STEP',
        frame_desc="Case 2 State-Consistent Relative Error Envelope (4 States)"
    )
    t_el = time.time() - t0
    sha = compute_sha256(target_odb)
    sz = os.path.getsize(target_odb)
    print("Synthesized Case 2 Donor in %.2f s:" % t_el)
    print("  Path:   %s" % target_odb)
    print("  Size:   %d bytes" % sz)
    print("  SHA256: %s" % sha)
    return target_odb, sha, t_el

def synthesize_case3():
    print("\n" + "="*80)
    print("SYNTHESIZING CASE 3 STATE-CONSISTENT RECOVERY DONOR (3 STATES)")
    print("="*80)
    c3_dir = os.path.join(F1833_BASE, "case3")
    if not os.path.exists(c3_dir):
        os.makedirs(c3_dir)
    src_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case3")
    states = [
        "SEC43_C3_STATE1_INITIATION.odb",
        "SEC43_C3_STATE2_HOLE_ARREST.odb",
        "SEC43_C3_STATE3_PROPAGATION.odb"
    ]
    solved_odbs = [os.path.join(src_dir, s) for s in states]
    for p in solved_odbs:
        if not os.path.exists(p):
            raise IOError("Missing solved recovery ODB: %s" % p)
    target_odb = os.path.join(c3_dir, "SEC43_MULTISTATE_RECOVERY.odb")
    t0 = time.time()
    MultiStateRecoveryDonorBuilder.synthesize_envelope_odb(
        solved_odbs=solved_odbs,
        target_odb_path=target_odb,
        step_name='RECOVERY_STEP',
        frame_desc="Case 3 State-Consistent Relative Error Envelope (3 States)"
    )
    t_el = time.time() - t0
    sha = compute_sha256(target_odb)
    sz = os.path.getsize(target_odb)
    print("Synthesized Case 3 Donor in %.2f s:" % t_el)
    print("  Path:   %s" % target_odb)
    print("  Size:   %d bytes" % sz)
    print("  SHA256: %s" % sha)
    return target_odb, sha, t_el

def prepare_case5():
    print("\n" + "="*80)
    print("PREPARING CASE 5 PRE-CRACK DONOR (SINGLE-STATE PARITY)")
    print("="*80)
    c5_dir = os.path.join(F1833_BASE, "case5")
    if not os.path.exists(c5_dir):
        os.makedirs(c5_dir)
    src_odb = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_COARSE.odb")
    target_odb = os.path.join(c5_dir, "PK_F1726_SEVEN_HOLE_COARSE.odb")
    if not os.path.exists(src_odb):
        raise IOError("Missing Case 5 coarse ODB: %s" % src_odb)
    shutil.copyfile(src_odb, target_odb)
    sha = compute_sha256(target_odb)
    sz = os.path.getsize(target_odb)
    print("Prepared Case 5 Donor:")
    print("  Path:   %s" % target_odb)
    print("  Size:   %d bytes" % sz)
    print("  SHA256: %s" % sha)
    return target_odb, sha, 0.0

def main():
    res = {}
    p1, s1, t1 = synthesize_case1()
    res["case_1"] = {"path": p1, "sha256": s1, "walltime_s": t1}
    p2, s2, t2 = synthesize_case2()
    res["case_2"] = {"path": p2, "sha256": s2, "walltime_s": t2}
    p3, s3, t3 = synthesize_case3()
    res["case_3"] = {"path": p3, "sha256": s3, "walltime_s": t3}
    p5, s5, t5 = prepare_case5()
    res["case_5"] = {"path": p5, "sha256": s5, "walltime_s": t5}
    print("\nALL FOUR DONORS READY FOR REMESHING EXECUTION.")

if __name__ == "__main__":
    main()
