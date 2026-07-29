#!/usr/bin/env python3
import hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

VARIANTS = {
    "1379481.mmaster02": ("u015", "1379481.mmaster02"),
    "1379482.mmaster02": ("u020", "1379482.mmaster02"),
    "1379483.mmaster02": ("u030", "1379483.mmaster02"),
    "1379484.mmaster02": ("u040", "1379484.mmaster02"),
}

SOURCE_COMMIT = "c264a205d8f6354f0a2d2109867feac35a98bdcd"
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    base_evidence = ROOT / "runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/evidence"
    for job_id, (var_name, jid) in VARIANTS.items():
        job_dir = base_evidence / job_id
        if not job_dir.is_dir():
            print(f"Skipping missing dir {job_dir}")
            continue
            
        inventory_file = job_dir / "EVIDENCE_FILE_INVENTORY.csv"
        lines = ["repo_relative_path,file_size_bytes,sha256,original_cluster_path,copied_at_utc\n"]
        
        cluster_base = f"/home/pr21vyci/adaptive-remeshing-evidence/stage_f/mode_ii_h1_endpoint_sweep/{var_name}/{job_id}"
        
        for file_path in sorted(job_dir.rglob("*")):
            if file_path.is_file() and file_path.name != "EVIDENCE_FILE_INVENTORY.csv":
                rel_path = file_path.relative_to(ROOT).as_posix()
                sub_path = file_path.relative_to(job_dir).as_posix()
                cluster_path = f"{cluster_base}/{sub_path}"
                size = file_path.stat().st_size
                digest = sha256_file(file_path)
                lines.append(f"{rel_path},{size},{digest},{cluster_path},{TIMESTAMP}\n")
                
        with open(inventory_file, "w", encoding="utf-8", newline="") as f:
            f.writelines(lines)
            
        print(f"Wrote inventory with {len(lines)-1} files to {inventory_file}")

if __name__ == "__main__":
    main()
