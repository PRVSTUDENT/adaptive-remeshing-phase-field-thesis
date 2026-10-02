#!/usr/bin/env python3
"""
Salvage and Extraction Script for Uniform Full References Batch
- Job 1: 1389351.mmaster02 (M2REF_H1_FULL_U050)
- Job 2: 1389352.mmaster02 (M2REF_H2_FULL_U050)
"""

import os
import sys
import json
import re
import hashlib
import subprocess
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

JOBS = [
    {
        "job_id": "1389351.mmaster02",
        "job_name": "M2REF_H1_FULL_U050",
        "mesh": "H1",
        "nphys": 12064,
        "remote_dir": "projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2REF_H1_FULL_U050",
        "local_dir": ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389351.mmaster02"
    },
    {
        "job_id": "1389352.mmaster02",
        "job_name": "M2REF_H2_FULL_U050",
        "mesh": "H2",
        "nphys": 33852,
        "remote_dir": "projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2REF_H2_FULL_U050",
        "local_dir": ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389352.mmaster02"
    }
]

def run_ssh(cmd):
    full_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, cmd]
    return subprocess.run(full_cmd, capture_output=True, text=True)

def download_file(remote_path, local_path):
    scp_cmd = ["scp", "-i", SSH_KEY, f"{SSH_HOST}:{remote_path}", str(local_path)]
    res = subprocess.run(scp_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Failed to download {remote_path}: {res.stderr}")
        return False
    return True

def parse_sta_file(sta_path):
    increments = []
    lines = sta_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    for l in lines:
        parts = l.strip().split()
        if len(parts) >= 8:
            try:
                step = int(parts[0])
                inc = int(parts[1])
                att = int(parts[2])
                sev = int(parts[3])
                equil = int(parts[4])
                tot_iters = int(parts[5])
                tot_time = float(parts[6])
                step_time = float(parts[7])
                inc_time = float(parts[8]) if len(parts) > 8 else 0.0
                increments.append({
                    "step": step,
                    "inc": inc,
                    "att": att,
                    "equil": equil,
                    "tot_iters": tot_iters,
                    "tot_time": tot_time,
                    "step_time": step_time,
                    "inc_time": inc_time
                })
            except ValueError:
                continue
    return increments

def parse_dat_rp_and_damage(dat_path):
    print(f"Parsing DAT file {dat_path.name} (size {dat_path.stat().st_size / 1e6:.1f} MB)...")
    trajectory = []
    
    current_inc = None
    current_time = None
    rp_u1 = None
    rp_rf1 = None
    max_d = None
    max_h = None
    
    in_sdv_max = False
    in_rp_table = False
    
    with open(dat_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "INCREMENT" in line and "SUMMARY" in line:
                m = re.search(r"INCREMENT\s+(\d+)\s+SUMMARY", line)
                if m:
                    if current_inc is not None and rp_u1 is not None and rp_rf1 is not None:
                        trajectory.append({
                            "inc": current_inc,
                            "time": current_time,
                            "u1": rp_u1,
                            "rf1": rp_rf1,
                            "d_max": max_d if max_d is not None else 0.0,
                            "h_max": max_h if max_h is not None else 0.0
                        })
                    current_inc = int(m.group(1))
                    current_time = None
                    rp_u1 = None
                    rp_rf1 = None
                    max_d = None
                    max_h = None
                    in_sdv_max = False
                    in_rp_table = False
                    continue

            if "STEP TIME COMPLETED" in line:
                m = re.search(r"STEP TIME COMPLETED\s+([\d.E+-]+)", line)
                if m:
                    current_time = float(m.group(1))

            if "E L E M E N T   O U T P U T" in line or "ELEMENT OUTPUT" in line:
                in_sdv_max = True
                continue

            if in_sdv_max and line.strip().startswith("MAXIMUM"):
                parts = line.strip().split()
                if len(parts) >= 5:
                    try:
                        max_d = float(parts[2])
                        max_h = float(parts[4])
                    except (ValueError, IndexError):
                        pass
                in_sdv_max = False
                continue

            if "NODE SET RP" in line:
                in_rp_table = True
                continue

            if in_rp_table:
                if line.strip().startswith("MAXIMUM"):
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        try:
                            rp_u1 = float(parts[1])
                            rp_rf1 = float(parts[3])
                        except (ValueError, IndexError):
                            pass
                    in_rp_table = False
                    continue

    if current_inc is not None and rp_u1 is not None and rp_rf1 is not None:
        trajectory.append({
            "inc": current_inc,
            "time": current_time,
            "u1": rp_u1,
            "rf1": rp_rf1,
            "d_max": max_d if max_d is not None else 0.0,
            "h_max": max_h if max_h is not None else 0.0
        })

    return trajectory

def main():
    print("================================================================================")
    print("SALVAGING EVIDENCE FOR UNIFORM FULL REFERENCES BATCH (H1 and H2)")
    print("================================================================================")

    results = {}

    for job in JOBS:
        print(f"\n--- Processing {job['job_name']} ({job['job_id']}) ---")
        job['local_dir'].mkdir(parents=True, exist_ok=True)
        
        # Download lightweight evidence
        files_to_dl = [
            f"{job['job_name']}.sta",
            f"{job['job_name']}.msg",
            f"{job['job_name']}.prt",
            f"{job['job_name']}.pbs.log",
            f"{job['job_name']}.com",
            f"{job['job_name']}.env",
            f"{job['job_name']}.inp",
            "PACKAGE_MANIFEST.json",
            "validate_package_manifest.py",
            "job_notifications.sh",
            f"submit_{job['job_name'].lower()}.sh",
            "f42_mixed_uel.for",
            f"{job['job_name']}.dat"
        ]
        
        for fn in files_to_dl:
            remote_fp = f"{job['remote_dir']}/{fn}"
            local_fp = job['local_dir'] / fn
            if not local_fp.exists() or local_fp.stat().st_size == 0:
                print(f"Downloading {fn}...")
                download_file(remote_fp, local_fp)

        # Parse STA
        sta_fp = job['local_dir'] / f"{job['job_name']}.sta"
        sta_incs = parse_sta_file(sta_fp)
        print(f"STA Increments parsed: {len(sta_incs)} (Final step time: {sta_incs[-1]['step_time']:.6f} mm)")

        # Parse DAT
        dat_fp = job['local_dir'] / f"{job['job_name']}.dat"
        traj = parse_dat_rp_and_damage(dat_fp)
        print(f"DAT Trajectory parsed: {len(traj)} increments")

        # Write trajectory CSV
        csv_fp = job['local_dir'] / "rf1_u1_trajectory.csv"
        with open(csv_fp, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["increment", "step_time_mm", "u1_mm", "rf1_kN", "rf1_N", "d_max", "h_max_kN_mm2"])
            for pt in traj:
                rf1_kn = pt['rf1'] if pt['rf1'] is not None else 0.0
                rf1_n = rf1_kn * 1000.0
                u1 = pt['u1'] if pt['u1'] is not None else pt['time']
                writer.writerow([pt['inc'], f"{pt['time']:.6f}", f"{u1:.6f}", f"{rf1_kn:.6f}", f"{rf1_n:.3f}", f"{pt['d_max']:.4f}", f"{pt['h_max']:.6f}"])

        # Find Peak Force and Post-Peak Metrics
        peak_pt = max(traj, key=lambda x: (x['rf1'] if x['rf1'] is not None else 0.0))
        terminal_pt = traj[-1]
        
        # Min load after peak
        post_peak_pts = [p for p in traj if p['inc'] >= peak_pt['inc']]
        min_post_peak_pt = min(post_peak_pts, key=lambda x: (x['rf1'] if x['rf1'] is not None else 999.0))
        
        drop_pct = (peak_pt['rf1'] - min_post_peak_pt['rf1']) / peak_pt['rf1'] * 100.0

        results[job['job_name']] = {
            "job_id": job['job_id'],
            "mesh": job['mesh'],
            "nphys": job['nphys'],
            "total_incs": len(traj),
            "final_u1": terminal_pt['u1'],
            "peak_u1": peak_pt['u1'],
            "peak_rf1_kN": peak_pt['rf1'],
            "peak_rf1_N": peak_pt['rf1'] * 1000.0,
            "min_postpeak_u1": min_post_peak_pt['u1'],
            "min_postpeak_rf1_kN": min_post_peak_pt['rf1'],
            "min_postpeak_rf1_N": min_post_peak_pt['rf1'] * 1000.0,
            "postpeak_drop_pct": drop_pct,
            "terminal_rf1_kN": terminal_pt['rf1'],
            "terminal_rf1_N": terminal_pt['rf1'] * 1000.0,
            "terminal_d_max": terminal_pt['d_max'],
            "terminal_h_max": terminal_pt['h_max']
        }

    print("\n================================================================================")
    print("UNIFORM REFERENCE BATCH SCIENTIFIC SUMMARY")
    print("================================================================================")
    for name, r in results.items():
        print(f"\nModel: {name} (Job: {r['job_id']}, Mesh: {r['mesh']})")
        print(f"  Physical Elements: {r['nphys']}")
        print(f"  Total Increments: {r['total_incs']} (Completed to U1 = {r['final_u1']:.6f} mm)")
        print(f"  Peak Force: RF1 = {r['peak_rf1_kN']:.6f} kN ({r['peak_rf1_N']:.2f} N) at U1 = {r['peak_u1']:.6f} mm")
        print(f"  Post-Peak Minimum: RF1 = {r['min_postpeak_rf1_kN']:.6f} kN ({r['min_postpeak_rf1_N']:.2f} N) at U1 = {r['min_postpeak_u1']:.6f} mm")
        print(f"  Post-Peak Load Drop: {r['postpeak_drop_pct']:.2f}%")
        print(f"  Terminal Force (U1=0.050mm): RF1 = {r['terminal_rf1_kN']:.6f} kN ({r['terminal_rf1_N']:.2f} N)")
        print(f"  Terminal Damage d_max: {r['terminal_d_max']:.4f}")
        print(f"  Terminal History H_max: {r['terminal_h_max']:.6f} kN/mm^2")

    # Save Batch Scientific Comparison JSON
    out_json = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/UNIFORM_FULL_REFERENCES_BATCH_SUMMARY.json"
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nSaved batch summary JSON to {out_json}")

if __name__ == '__main__':
    main()
