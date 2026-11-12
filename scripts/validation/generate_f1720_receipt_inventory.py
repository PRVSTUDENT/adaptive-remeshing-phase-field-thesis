#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generate_f1720_receipt_inventory.py
Audits and records the exact byte counts and SHA-256 hashes of the primary solver receipts
for Task F1720 adapted fracture simulation.
"""

import hashlib
import json
import os
import sys

PRIMARY_FILES = {
    "sta_original": "models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1720_ADAPTED_PFM.sta",
    "msg_original": "models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1720_ADAPTED_PFM.msg",
    "dat_original": "models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1720_ADAPTED_PFM.dat",
    "sta_text_copy": "results/validation/f1720_solver_receipts/PK_F1720_ADAPTED_PFM_sta.txt",
    "dat_text_copy": "results/validation/f1720_solver_receipts/PK_F1720_ADAPTED_PFM_dat.txt",
    "msg_terminal_copy": "results/validation/f1720_solver_receipts/PK_F1720_ADAPTED_PFM_msg_terminal.txt",
}

def get_file_info(filepath):
    if not os.path.exists(filepath):
        return {"exists": False}
    with open(filepath, "rb") as f:
        data = f.read()
    sha256 = hashlib.sha256(data).hexdigest().upper()
    return {
        "exists": True,
        "path": filepath.replace("\\", "/"),
        "name": os.path.basename(filepath),
        "size_bytes": len(data),
        "sha256": sha256
    }

def main():
    inventory = {
        "protocol": "PRIMARY_SOLVER_RECEIPT_QUALIFICATION_V1",
        "task_id": "F1720-METHOD-A-DIRECT-COUPLING-AND-REMESH-REPRODUCTION",
        "correlation_id": "HND-F1720-METHOD-A-FINAL-VALIDATION-004",
        "job_name": "PK_F1720_ADAPTED_PFM",
        "files": {}
    }

    for key, path in PRIMARY_FILES.items():
        info = get_file_info(path)
        inventory["files"][key] = info
        print(f"{key}: {info['name']} -> {info.get('size_bytes', 0)} bytes, SHA-256: {info.get('sha256', 'N/A')}")

    out_path = "results/validation/f1720_solver_receipts/RECEIPT_INVENTORY.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2)

    print(f"\nInventory saved to {out_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
