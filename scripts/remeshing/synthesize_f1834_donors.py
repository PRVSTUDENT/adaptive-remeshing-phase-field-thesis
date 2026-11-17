# -*- coding: utf-8 -*-
"""
scripts/remeshing/synthesize_f1834_donors.py
============================================
Task F1834: Synthesize State-Consistent Multi-State Recovery Donors with
Load-Threshold Guard for Cases 1, 2, 3 across multiple threshold ratios:
    theta in {0.10, 0.25, 0.50, 0.80}

Uses MultiStateRecoveryDonorBuilder.synthesize_envelope_odb from
scripts/remeshing/reusable_2d_adaptive_framework.py.
"""
from __future__ import print_function
import os
import sys
import shutil
import hashlib
import time
import json

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
framework_dir = os.path.join(REPO_ROOT, "scripts", "remeshing")
if framework_dir not in sys.path:
    sys.path.insert(0, framework_dir)

from reusable_2d_adaptive_framework import MultiStateRecoveryDonorBuilder

F1834_BASE = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "274_f1834_blowup_guard")

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def synthesize_case1_threshold(theta, tag):
    out_dir = os.path.join(F1834_BASE, tag, "case1")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
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
    target_odb = os.path.join(out_dir, "PK_CASE1_MULTISTATE_RECOVERY.odb")
    t0 = time.time()
    MultiStateRecoveryDonorBuilder.synthesize_envelope_odb(
        solved_odbs=solved_odbs,
        target_odb_path=target_odb,
        step_name='RECOVERY_STEP',
        frame_desc="Case 1 Multi-State Error Envelope (theta=%.2f)" % theta,
        load_threshold_ratio=theta
    )
    t_el = time.time() - t0
    sha = compute_sha256(target_odb)
    print("Synthesized Case 1 (theta=%.2f, %s) in %.2f s: SHA=%s" % (theta, tag, t_el, sha))
    return target_odb, sha, t_el

def synthesize_case2_threshold(theta, tag):
    out_dir = os.path.join(F1834_BASE, tag, "case2")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
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
    target_odb = os.path.join(out_dir, "PK_HOLE_MULTISTATE_RECOVERY.odb")
    t0 = time.time()
    MultiStateRecoveryDonorBuilder.synthesize_envelope_odb(
        solved_odbs=solved_odbs,
        target_odb_path=target_odb,
        step_name='RECOVERY_STEP',
        frame_desc="Case 2 Multi-State Error Envelope (theta=%.2f)" % theta,
        load_threshold_ratio=theta
    )
    t_el = time.time() - t0
    sha = compute_sha256(target_odb)
    print("Synthesized Case 2 (theta=%.2f, %s) in %.2f s: SHA=%s" % (theta, tag, t_el, sha))
    return target_odb, sha, t_el

def synthesize_case3_threshold(theta, tag):
    out_dir = os.path.join(F1834_BASE, tag, "case3")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
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
    target_odb = os.path.join(out_dir, "SEC43_MULTISTATE_RECOVERY.odb")
    t0 = time.time()
    MultiStateRecoveryDonorBuilder.synthesize_envelope_odb(
        solved_odbs=solved_odbs,
        target_odb_path=target_odb,
        step_name='RECOVERY_STEP',
        frame_desc="Case 3 Multi-State Error Envelope (theta=%.2f)" % theta,
        load_threshold_ratio=theta
    )
    t_el = time.time() - t0
    sha = compute_sha256(target_odb)
    print("Synthesized Case 3 (theta=%.2f, %s) in %.2f s: SHA=%s" % (theta, tag, t_el, sha))
    return target_odb, sha, t_el

def prepare_case5_threshold(tag):
    out_dir = os.path.join(F1834_BASE, tag, "case5")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    src_odb = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_COARSE.odb")
    target_odb = os.path.join(out_dir, "PK_F1726_SEVEN_HOLE_COARSE.odb")
    if not os.path.exists(src_odb):
        raise IOError("Missing Case 5 coarse ODB: %s" % src_odb)
    shutil.copyfile(src_odb, target_odb)
    sha = compute_sha256(target_odb)
    print("Prepared Case 5 (%s) in 0.00 s: SHA=%s" % (tag, sha))
    return target_odb, sha, 0.0

def main():
    thresholds = [
        (0.10, "thresh_010"),
        (0.25, "thresh_025"),
        (0.50, "thresh_050"),
        (0.80, "thresh_080"),
    ]
    manifest = {}
    for theta, tag in thresholds:
        print("\n" + "="*80)
        print("SYNTHESIZING DONORS FOR THETA = %.2f (%s)" % (theta, tag))
        print("="*80)
        t_start = time.time()
        p1, s1, t1 = synthesize_case1_threshold(theta, tag)
        p2, s2, t2 = synthesize_case2_threshold(theta, tag)
        p3, s3, t3 = synthesize_case3_threshold(theta, tag)
        p5, s5, t5 = prepare_case5_threshold(tag)
        manifest[tag] = {
            "theta": theta,
            "case_1": {"path": p1, "sha256": s1, "walltime_s": t1},
            "case_2": {"path": p2, "sha256": s2, "walltime_s": t2},
            "case_3": {"path": p3, "sha256": s3, "walltime_s": t3},
            "case_5": {"path": p5, "sha256": s5, "walltime_s": t5},
            "total_walltime_s": time.time() - t_start
        }
    manifest_path = os.path.join(F1834_BASE, "donor_synthesis_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print("\nSaved synthesis manifest to: %s" % manifest_path)

if __name__ == "__main__":
    main()
