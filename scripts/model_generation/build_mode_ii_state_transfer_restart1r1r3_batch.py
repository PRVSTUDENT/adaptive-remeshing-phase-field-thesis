#!/usr/bin/env python3
"""
Build Production Scientific State-Transfer Restart Candidate: M2STATE_FRACFIX_RESTART1R1R3.
Task ID: F44STATE-M2-FRACFIX-RESTART1R1R2-EXACT-WRAPPER-BYTE-AUDIT1

Revision Summary:
- Supersedes M2STATE_FRACFIX_RESTART1R1R2 (which is preserved read-only on disk and cluster).
- Resolves EXECUTION_CRITICAL_WRAPPER_TEXT_FORMAT_DEFECT:
  * Ensures submit_m2state_fracfix_restart1r1r3.sh and M2STATE_FRACFIX_RESTART1R1R3.pbs are written
    strictly with LF line endings (\n, CR_count = 0) so direct execution under Linux bash succeeds cleanly
    with exit code 0 without requiring tr -d '\r' or line-ending preprocessing.
- Scientific formulation, topology, state-transfer artifact data, acceptance thresholds, UEL equations,
  trace representatives, and mapping remain 100% byte/logic identical to R1R1R2.
"""

import os
import sys
import json
import math
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
SRC_PK5_DECK = ROOT / "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/runtime_pk5/F43REM4_PK5.inp"
SRC_MM_DECK = ROOT / "models/generated/mode_ii/production_adaptive_batch/M2ADAPT_MM_FRACFIX_PROD/M2ADAPT_MM_FRACFIX_PROD.inp"
OUT_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R3"

L0 = 0.015
GC = 0.0027
EMOD = 210.0
ENU = 0.3
PARK = 1.0e-7
THCK = 1.0
DEPVAR = 18
PASSIVE_E = 1.0e-11


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_lf_file(path: Path, text: str):
    """Write text file using strict LF line endings (\n) without CR (\r)."""
    clean_text = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_bytes(clean_text.encode("utf-8"))


def parse_physical_mesh(deck_path: Path) -> Tuple[Dict[int, Tuple[float, float]], Dict[int, List[int]], Dict[int, List[int]]]:
    nodes: Dict[int, Tuple[float, float]] = {}
    quads: Dict[int, List[int]] = {}
    tris: Dict[int, List[int]] = {}

    lines = deck_path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_nodes = False
    in_cpe4 = False
    in_cpe3 = False

    for line in lines:
        s = line.strip()
        if not s or s.startswith("**"):
            continue
        if s.upper().startswith("*NODE"):
            in_nodes = True
            in_cpe4 = False
            in_cpe3 = False
            continue
        elif s.upper().startswith("*ELEMENT"):
            in_nodes = False
            if "CPE4" in s.upper():
                in_cpe4 = True
                in_cpe3 = False
            elif "CPE3" in s.upper():
                in_cpe4 = False
                in_cpe3 = True
            else:
                in_cpe4 = False
                in_cpe3 = False
            continue
        elif s.startswith("*"):
            in_nodes = False
            in_cpe4 = False
            in_cpe3 = False
            continue

        parts = [p.strip() for p in s.split(",") if p.strip()]
        if in_nodes:
            if len(parts) >= 3:
                nid = int(parts[0])
                x = float(parts[1])
                y = float(parts[2])
                nodes[nid] = (x, y)
        elif in_cpe4:
            if len(parts) >= 5:
                eid = int(parts[0])
                nids = [int(p) for p in parts[1:5]]
                quads[eid] = nids
        elif in_cpe3:
            if len(parts) >= 4:
                eid = int(parts[0])
                nids = [int(p) for p in parts[1:4]]
                tris[eid] = nids

    return nodes, quads, tris


def main():
    print("======================================================================")
    print("BUILDING CANDIDATE M2STATE_FRACFIX_RESTART1R1R3 (LF LINE ENDINGS)")
    print("======================================================================")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Parse target PK5 physical mesh
    nodes, quads, tris = parse_physical_mesh(SRC_PK5_DECK)
    n_nodes = len(nodes)
    n_quads = len(quads)
    n_tris = len(tris)
    n_phys = n_quads + n_tris
    print(f"Target PK5 Mesh: {n_phys} physical elements ({n_quads} quads, {n_tris} tris), {n_nodes} nodes")

    # Read existing R1R1R2 artifact and decks to preserve exact numerical state and UEL code
    r1r2_dir = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R2"
    r1r2_inp = (r1r2_dir / "M2STATE_FRACFIX_RESTART1R1R2.inp").read_text(encoding="utf-8")
    r1r2_uel = (r1r2_dir / "f42_mixed_uel.for").read_text(encoding="utf-8")
    r1r2_artifact = (r1r2_dir / "STATE_TRANSFER_ARTIFACT.json").read_text(encoding="utf-8")
    r1r2_transfer = (r1r2_dir / "TRANSFER_MANIFEST.json").read_text(encoding="utf-8")
    r1r2_contract = (r1r2_dir / "RESTART_ACCEPTANCE_CONTRACT.json").read_text(encoding="utf-8")
    r1r2_checker = (r1r2_dir / "verify_restart_trace.py").read_text(encoding="utf-8")

    # Update candidate name references to R1R1R3
    inp_code = r1r2_inp.replace("M2STATE_FRACFIX_RESTART1R1R2", "M2STATE_FRACFIX_RESTART1R1R3")
    uel_code = r1r2_uel.replace("M2STATE_FRACFIX_RESTART1R1R2", "M2STATE_FRACFIX_RESTART1R1R3")
    
    artifact_dict = json.loads(r1r2_artifact)
    artifact_dict["target_job"] = "M2STATE_FRACFIX_RESTART1R1R3"
    artifact_str = json.dumps(artifact_dict, indent=2) + "\n"

    transfer_dict = json.loads(r1r2_transfer)
    transfer_dict["target_job"] = "M2STATE_FRACFIX_RESTART1R1R3"
    transfer_str = json.dumps(transfer_dict, indent=2) + "\n"

    contract_dict = json.loads(r1r2_contract)
    contract_dict["target_job"] = "M2STATE_FRACFIX_RESTART1R1R3"
    contract_str = json.dumps(contract_dict, indent=2) + "\n"

    checker_code = r1r2_checker.replace("M2STATE_FRACFIX_RESTART1R1R2", "M2STATE_FRACFIX_RESTART1R1R3")

    # Write target files
    write_lf_file(OUT_DIR / "M2STATE_FRACFIX_RESTART1R1R3.inp", inp_code)
    write_lf_file(OUT_DIR / "f42_mixed_uel.for", uel_code)
    write_lf_file(OUT_DIR / "STATE_TRANSFER_ARTIFACT.json", artifact_str)
    write_lf_file(OUT_DIR / "TRANSFER_MANIFEST.json", transfer_str)
    write_lf_file(OUT_DIR / "RESTART_ACCEPTANCE_CONTRACT.json", contract_str)
    write_lf_file(OUT_DIR / "verify_restart_trace.py", checker_code)

    # Write PBS Script with STRICT LF Line Endings
    pbs_code = f"""#!/bin/bash
#PBS -N M2STATE_FRACFIX_RESTART1R1R3
#PBS -l select=1:ncpus=1:mpiprocs=1:mem=8gb
#PBS -l walltime=04:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -o M2STATE_FRACFIX_RESTART1R1R3.pbs.log

cd $PBS_O_WORKDIR

echo "[PBS_PREFLIGHT] Starting M2STATE_FRACFIX_RESTART1R1R3 Production Restart Job..."
date

# Step 0: Package Hash Preflight Verification
python3 -c "
import json, hashlib, sys
from pathlib import Path

m = json.loads(Path('PACKAGE_MANIFEST.json').read_text())
for f, expected_hash in m['file_hashes'].items():
    p = Path(f)
    if not p.exists():
        print(f'[PBS_PREFLIGHT] ERROR: Missing file {{f}}')
        sys.exit(1)
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    if actual != expected_hash:
        print(f'[PBS_PREFLIGHT] ERROR: Hash mismatch for {{f}}: expected {{expected_hash}}, got {{actual}}')
        sys.exit(1)
print('[PBS_PREFLIGHT] PACKAGE HASHES VERIFIED 100% MATCH.')
"
if [ $? -ne 0 ]; then
  echo "[PBS_PREFLIGHT] ERROR: Package manifest verification failed."
  exit 1
fi

# Step 1: Purge and Load Qualified Modules
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7

echo "[PBS_PREFLIGHT] Abaqus environment loaded."
abaqus information=release

# Step 2: Run Abaqus Execution Step
abaqus job=M2STATE_FRACFIX_RESTART1R1R3 user=f42_mixed_uel.for input=M2STATE_FRACFIX_RESTART1R1R3.inp interactive

ABAQUS_RC=$?
echo "[PBS_PREFLIGHT] Abaqus execution finished with exit code $ABAQUS_RC"

if [ $ABAQUS_RC -ne 0 ]; then
  echo "[PBS_PREFLIGHT] ERROR: Abaqus execution failed with exit code $ABAQUS_RC"
  exit $ABAQUS_RC
fi

echo "[PBS_PREFLIGHT] Abaqus continuation step completed successfully."

# Step 3: Concatenate trace sinks and run checker
cat M2STATE_FRACFIX_RESTART1R1R3.dat M2STATE_FRACFIX_RESTART1R1R3.msg M2STATE_FRACFIX_RESTART1R1R3.log > M2STATE_FRACFIX_RESTART1R1R3.trace 2>/dev/null

python3 verify_restart_trace.py M2STATE_FRACFIX_RESTART1R1R3.trace
CHECKER_RC=$?

if [ $CHECKER_RC -ne 0 ]; then
  echo "[PBS_PREFLIGHT] ERROR: Production restart trace checker failed with exit code $CHECKER_RC"
  exit $CHECKER_RC
fi

echo "[PBS_PREFLIGHT] ALL PRODUCTION RESTART CONTRACTS QUALIFIED SUCCESSFULLY."
"""
    write_lf_file(OUT_DIR / "M2STATE_FRACFIX_RESTART1R1R3.pbs", pbs_code)

    # Write Submit Wrapper with STRICT LF Line Endings
    submit_code = f"""#!/bin/bash
# Guarded Submission Wrapper for M2STATE_FRACFIX_RESTART1R1R3
# Protocol: Standalone direct-human authorization required before direct qsub.

DRY_RUN=false
if [ "$1" == "--dry-run" ]; then
  DRY_RUN=true
fi

echo "[WRAPPER] Preflight verification for M2STATE_FRACFIX_RESTART1R1R3..."

MANIFEST="PACKAGE_MANIFEST.json"
if [ ! -f "$MANIFEST" ]; then
  echo "[WRAPPER] ERROR: $MANIFEST not found."
  exit 1
fi

python3 -c "
import json, hashlib, sys
from pathlib import Path

m = json.loads(Path('$MANIFEST').read_text())
for f, expected_hash in m['file_hashes'].items():
    p = Path(f)
    if not p.exists():
        print(f'[WRAPPER] ERROR: Missing package file {{f}}')
        sys.exit(1)
    actual = hashlib.sha256(p.read_bytes()).hexdigest()
    if actual != expected_hash:
        print(f'[WRAPPER] ERROR: Hash mismatch for {{f}}: expected {{expected_hash}}, got {{actual}}')
        sys.exit(1)
print('[WRAPPER] ALL PACKAGE FILE HASHES VERIFIED MATCH.')
"
if [ $? -ne 0 ]; then
  echo "[WRAPPER] ERROR: Package manifest hash verification failed."
  exit 1
fi

if [ "$DRY_RUN" = true ]; then
  echo "[WRAPPER] DRY-RUN COMPLETE: Preflight passed cleanly. qsub was NOT called."
  exit 0
fi

echo "[WRAPPER] FAIL-CLOSED: Direct qsub requires explicit human authorization."
exit 1
"""
    write_lf_file(OUT_DIR / "submit_m2state_fracfix_restart1r1r3.sh", submit_code)

    # Write PACKAGE_MANIFEST.json
    package_files = [
        "M2STATE_FRACFIX_RESTART1R1R3.inp",
        "f42_mixed_uel.for",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "verify_restart_trace.py",
        "M2STATE_FRACFIX_RESTART1R1R3.pbs",
        "submit_m2state_fracfix_restart1r1r3.sh"
    ]
    file_hashes = {f: sha256_file(OUT_DIR / f) for f in package_files}
    package_manifest = {
        "package_name": "M2STATE_FRACFIX_RESTART1R1R3",
        "protocol_version": 1,
        "task_id": "F44STATE-M2-FRACFIX-RESTART1R1R2-EXACT-WRAPPER-BYTE-AUDIT1",
        "execution_mode": "SERIAL",
        "cpus": 1,
        "memory_gb": 8,
        "walltime": "04:00:00",
        "file_hashes": file_hashes
    }
    manifest_str = json.dumps(package_manifest, indent=2) + "\n"
    write_lf_file(OUT_DIR / "PACKAGE_MANIFEST.json", manifest_str)
    print(f"Wrote PACKAGE_MANIFEST.json: {OUT_DIR / 'PACKAGE_MANIFEST.json'}")

    print("======================================================================")
    print("M2STATE_FRACFIX_RESTART1R1R3 PREPARATION COMPLETE (LF LINE ENDINGS)")
    print("======================================================================")


if __name__ == "__main__":
    main()
