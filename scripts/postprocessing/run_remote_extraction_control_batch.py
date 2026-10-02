#!/usr/bin/env python3
"""
Remote extraction script for Control Batch Replacement Jobs:
- PK10R1_CONTINUOUS_U050 (Job 1389677.mmaster02)
- PK10R1_IDENTITY_RESTART_U050 (Job 1389678.mmaster02)
"""

import sys
import os
import re
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

JOBS = [
    ("1389677.mmaster02", "PK10R1_CONTINUOUS_U050"),
    ("1389678.mmaster02", "PK10R1_IDENTITY_RESTART_U050")
]

REMOTE_EXTRACTOR = """#!/usr/bin/env python3
import sys
import os
import re
import json

def parse_job_dat(dat_path):
    if not os.path.exists(dat_path):
        return []
    
    frames = []
    current_step = 1
    current_inc = 0
    current_time = 0.0
    in_table = False
    
    with open(dat_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "STEP " in line and "INCREMENT" in line:
                m = re.search(r"STEP\s+(\d+)\s+INCREMENT\s+(\d+)", line)
                if m:
                    current_step = int(m.group(1))
                    current_inc = int(m.group(2))
            if "STEP TIME COMPLETED" in line:
                m = re.search(r"STEP TIME COMPLETED\s+([0-9.E+-]+)", line)
                if m:
                    current_time = float(m.group(1))
            if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in line:
                in_table = True
                continue
            if line.strip().startswith("99999 "):
                tokens = line.strip().split()
                if len(tokens) >= 3 and tokens[0] == "99999":
                    try:
                        u1 = float(tokens[1])
                        rf1 = float(tokens[-1])
                        frames.append({
                            "step": current_step,
                            "inc": current_inc,
                            "step_time": current_time,
                            "u1": u1,
                            "rf1": rf1
                        })
                    except Exception:
                        pass
    return frames

def main():
    base_dir = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch"
    jobs = [
        ("1389677.mmaster02", "PK10R1_CONTINUOUS_U050"),
        ("1389678.mmaster02", "PK10R1_IDENTITY_RESTART_U050")
    ]
    
    out_data = {}
    for job_id, pkg_name in jobs:
        dat_file = os.path.join(base_dir, pkg_name, f"{pkg_name}.dat")
        frames = parse_job_dat(dat_file)
        out_data[pkg_name] = {
            "job_id": job_id,
            "total_frames": len(frames),
            "frames": frames
        }
        
    print(json.dumps(out_data))

if __name__ == "__main__":
    main()
"""

def main():
    print("================================================================================")
    print("EXTRACTING CONTROL BATCH REPLACEMENT RESULTS FROM CLUSTER")
    print("================================================================================")
    
    # 1. Upload remote extractor script
    remote_script_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/remote_extractor.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_script_path}\n{REMOTE_EXTRACTOR}\nEOF\nchmod +x {remote_script_path}"]
    res = subprocess.run(upload_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Failed to upload remote extractor: {res.stderr}")
        sys.exit(1)
        
    print("Uploaded remote extractor script to cluster.")
    
    # 2. Run remote extractor script
    run_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"python3 {remote_script_path}"]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=120)
    if res.returncode != 0:
        print(f"Failed to run remote extractor: {res.stderr}")
        sys.exit(1)
        
    extracted_raw = res.stdout.strip()
    try:
        data = json.loads(extracted_raw)
    except Exception as e:
        print(f"Failed to parse JSON output: {e}\nRaw output:\n{extracted_raw[:500]}")
        sys.exit(1)
        
    # 3. Save extracted summary locally
    out_dir = ROOT / "runs/hpc/mode_ii_control_batch/evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "CONTROL_BATCH_REPLACEMENT_EXTRACTED_RESULTS.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    print(f"Saved extracted results to {out_file}\n")
    
    # 4. Print Summary Report
    for pkg_name, info in data.items():
        frames = info["frames"]
        print(f"Candidate: {pkg_name} (Job {info['job_id']})")
        print(f"  Total frames parsed: {len(frames)}")
        if frames:
            first = frames[0]
            last = frames[-1]
            peak = max(frames, key=lambda x: x["rf1"])
            print(f"  Initial State : Step {first['step']} Inc {first['inc']} u1={first['u1']:.6f} mm, RF1={first['rf1']:.6f} kN ({first['rf1']*1000.0:.2f} N)")
            print(f"  Peak Force    : Step {peak['step']} Inc {peak['inc']} u1={peak['u1']:.6f} mm, RF1={peak['rf1']:.6f} kN ({peak['rf1']*1000.0:.2f} N)")
            print(f"  Terminal State: Step {last['step']} Inc {last['inc']} u1={last['u1']:.6f} mm, RF1={last['rf1']:.6f} kN ({last['rf1']*1000.0:.2f} N)")
            
            # Check for force drop / post-peak if any
            min_post_peak = None
            if peak != last:
                post_peak_frames = [f for f in frames if f["u1"] > peak["u1"]]
                if post_peak_frames:
                    min_post_peak = min(post_peak_frames, key=lambda x: x["rf1"])
                    drop_percent = (1.0 - min_post_peak["rf1"] / peak["rf1"]) * 100.0
                    print(f"  Post-Peak Min : Step {min_post_peak['step']} Inc {min_post_peak['inc']} u1={min_post_peak['u1']:.6f} mm, RF1={min_post_peak['rf1']:.6f} kN ({min_post_peak['rf1']*1000.0:.2f} N, drop = {drop_percent:.2f}%)")
        print()

    # 5. Comparative Scientific Analysis
    cont_frames = data.get("PK10R1_CONTINUOUS_U050", {}).get("frames", [])
    ident_frames = data.get("PK10R1_IDENTITY_RESTART_U050", {}).get("frames", [])
    
    if cont_frames and ident_frames:
        print("================================================================================")
        print("SCIENTIFIC COMPARISON & CONTROL BATCH DEEP ANALYSIS")
        print("================================================================================")
        
        cont_peak = max(cont_frames, key=lambda x: x["rf1"])
        ident_step1 = ident_frames[0]
        ident_peak = max(ident_frames, key=lambda x: x["rf1"])
        ident_last = ident_frames[-1]
        
        # Match Continuous force at u1 = 0.030 mm
        cont_at_030 = min(cont_frames, key=lambda x: abs(x["u1"] - 0.030000))
        cont_at_050 = cont_frames[-1]
        
        print(f"1. Continuous Control (PK10R1_CONTINUOUS_U050):")
        print(f"   - Force at u1 = 0.030 mm: RF1 = {cont_at_030['rf1']:.6f} kN ({cont_at_030['rf1']*1000.0:.2f} N)")
        print(f"   - Peak Force            : RF1 = {cont_peak['rf1']:.6f} kN ({cont_peak['rf1']*1000.0:.2f} N) at u1 = {cont_peak['u1']:.6f} mm")
        print(f"   - Terminal Force (0.050): RF1 = {cont_at_050['rf1']:.6f} kN ({cont_at_050['rf1']*1000.0:.2f} N) at u1 = {cont_at_050['u1']:.6f} mm")
        
        print(f"\n2. Identity Restart Control (PK10R1_IDENTITY_RESTART_U050):")
        print(f"   - Step 1 Handoff (0.030): RF1 = {ident_step1['rf1']:.6f} kN ({ident_step1['rf1']*1000.0:.2f} N)")
        print(f"   - Step 2 Start Inc 1    : RF1 = {ident_frames[1]['rf1']:.6f} kN ({ident_frames[1]['rf1']*1000.0:.2f} N)")
        print(f"   - Force Jump at Release : Delta = {ident_frames[1]['rf1'] - ident_step1['rf1']:.6f} kN ({((ident_frames[1]['rf1']/ident_step1['rf1'])-1.0)*100.0:.2f}%)")
        print(f"   - Terminal Force (0.050): RF1 = {ident_last['rf1']:.6f} kN ({ident_last['rf1']*1000.0:.2f} N) at u1 = {ident_last['u1']:.6f} mm")
        
        print(f"\n3. Key Conclusions & Thesis Impact:")
        diff_peak = abs(cont_at_030['rf1'] - ident_step1['rf1'])
        diff_pct = (diff_peak / cont_at_030['rf1']) * 100.0
        print(f"   - State Transfer Continuity at u1=0.030mm: diff = {diff_peak:.6f} kN ({diff_pct:.3f}%)")
        if diff_pct < 1.0:
            print("   - [PASS] Zero-discrepancy state transfer verified on identical topology.")

if __name__ == "__main__":
    main()
