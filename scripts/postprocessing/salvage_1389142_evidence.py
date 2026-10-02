#!/usr/bin/env python3
import os
import sys
import shutil
import json
import hashlib
import glob
from pathlib import Path

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    root = Path(__file__).resolve().parent.parent.parent
    src_dir = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R4"
    dest_dir = root / "runs/hpc/mode_ii_state_transfer/evidence/1389142.mmaster02"
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Copy lightweight text/log artifacts
    text_extensions = [".sta", ".dat", ".e1389142", ".com", ".prt"]
    for ext in text_extensions:
        matches = list(src_dir.glob(f"*{ext}"))
        for f in matches:
            shutil.copy2(f, dest_dir / f.name)
            print(f"Copied {f.name} to evidence dir.")
            
    # For large files like .o1389142 and .msg, take full or tail if huge
    o_file = src_dir / "M2STATE_FRACFIX_RESTART2R4.o1389142"
    if o_file.exists():
        # Copy head + tail summary if large
        shutil.copy2(o_file, dest_dir / o_file.name)
        print("Copied stdout log.")
        
    msg_file = src_dir / "M2STATE_FRACFIX_RESTART2R4.msg"
    if msg_file.exists():
        # If msg is > 50MB, copy or summarize
        shutil.copy2(msg_file, dest_dir / msg_file.name)
        print("Copied msg log.")
        
    # 2. Extract job evidence JSON
    evidence = {
        "job_id": "1389142.mmaster02",
        "candidate": "M2STATE_FRACFIX_RESTART2R4",
        "scheduler_status": "FINISHED",
        "exit_code": 0,
        "solver_executed": True,
        "solver_status": "THE ANALYSIS HAS COMPLETED SUCCESSFULLY",
        "step_1_increments": 1,
        "step_2_increments": 16,
        "step_2_time_completed": 0.007415,
        "target_mesh": "PK10R1",
        "source_job": "1388948.mmaster02",
        "source_frame": 13,
        "source_u1_mm": 0.007584926784038544,
        "scientific_evaluation": {
            "status": "FAIL",
            "reason": "U field contains NaNs across interior nodes due to N_TOP equation coupling to disconnected orphan nodes and uninitialized F_INT in JTYPE 4",
            "first_nan_step": 1,
            "first_nan_inc": 1,
            "odb_finite_frames": 1,
            "odb_nan_frames": 18
        },
        "file_hashes": {}
    }
    
    for f in dest_dir.glob("*"):
        if f.is_file() and f.name != "JOB_EVIDENCE.json":
            evidence["file_hashes"][f.name] = sha256_file(f)
            
    with open(dest_dir / "JOB_EVIDENCE.json", "w") as f:
        json.dump(evidence, f, indent=2)
        
    print("JOB_EVIDENCE.json written successfully.")

if __name__ == "__main__":
    main()
