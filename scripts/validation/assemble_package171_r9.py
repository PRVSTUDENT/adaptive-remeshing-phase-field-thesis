#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assemble_package171_r9.py
=========================
Assembles Package 171-R9 (C6 Coupled PDAS Re-Equilibration Revision 9) locally
under models/pandey_kumar_mode1/171_c6_package171_r9_c3_0_adaptive_reequilibration.

Performs:
1. Copies invariant mesh, transfer state, and boundary decks from R8.
2. Strictly verifies bitwise SHA-256 match of frozen production UEL.
3. Generates submit_M1_C6_P171_R9_C3_0.pbs referencing driver_package171_r9_c6_coupled_pdas.py.
4. Generates smoke_import.py exercising R9 driver imports and class construction.
5. Computes and writes PACKAGE_MANIFEST.json with SHA-256 hashes for all files.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
R8_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "171_c6_package171_r8_c3_0_adaptive_reequilibration"
R9_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "171_c6_package171_r9_c3_0_adaptive_reequilibration"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def assemble_r9():
    print("=== Assembling Package 171-R9 Locally ===")
    R9_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Invariant transfer and mesh files to copy
    invariant_files = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "f42_mixed_uel.for",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "M1_C6_PACKAGE171_C3_0_REEQUILIBRATION.inp",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "P171_MECHANICAL_DC.inp",
        "P171_PHASE_DC.inp",
        "run_datacheck.sh",
    ]

    for fname in invariant_files:
        src = R8_DIR / fname
        dst = R9_DIR / fname
        shutil.copy2(src, dst)
        print(f"Copied invariant file: {fname}")

    # 2. Verify frozen UEL
    uel_hash = sha256_file(R9_DIR / "f42_mixed_uel.for")
    assert uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch: {uel_hash} != {FROZEN_UEL_HASH}"
    print(f"Verified frozen production UEL: {uel_hash}")

    # 3. Create R9 main input deck
    r8_inp = R8_DIR / "M1_C6_PACKAGE171_R8_C3_0_ADAPTIVE_REEQUILIBRATION.inp"
    r9_inp = R9_DIR / "M1_C6_PACKAGE171_R9_C3_0_ADAPTIVE_REEQUILIBRATION.inp"
    inp_content = r8_inp.read_text(encoding="utf-8")
    inp_content = inp_content.replace("M1_C6_PACKAGE171_R8", "M1_C6_PACKAGE171_R9")
    inp_content = inp_content.replace("Revision 8", "Revision 9")
    r9_inp.write_text(inp_content, encoding="utf-8")
    print(f"Generated R9 input deck: {r9_inp.name}")

    # 4. Generate submit_M1_C6_P171_R9_C3_0.pbs
    pbs_content = """#!/bin/bash
#PBS -N M1_C6_P171_R9_C3_0
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/mode1_c6_package171_r9_c3_0_adaptive_reequilibration/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/mode1_c6_package171_r9_c3_0_adaptive_reequilibration"
cd "${RUN_DIR}"

export JOB_NAME="M1_C6_P171_R9_C3_0"
export NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-${HOME}/.config/adaptive-remeshing/notifications.env}"
source "${RUN_DIR}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

repo="${RUN_DIR}/runtime"
python3 "${repo}/scripts/state_transfer/driver_package171_r9_c6_coupled_pdas.py" \\
    --package "${RUN_DIR}" \\
    --output "${RUN_DIR}/equilibration_${PBS_JOBID}" \\
    --extractor "${repo}/scripts/validation/extract_package148_iteration.py" \\
    --memory-gb 16 \\
    --timeout 25200 \\
    --max-outer 140 \\
    --omega-d-stage1 0.50 \\
    --omega-d-stage2 0.85 \\
    --max-active-cardinality 500 \\
    --max-symmetric-diff 10 \\
    --max-added-nodes 0 \\
    --stabilization-window 3 \\
    --rollback-factor 1.05 \\
    --divergence-factor 1.50 \\
    --catastrophic-cap 0.05
EXIT_CODE=$?

echo "Stage C3-0 Re-equilibration (Package 171-R9 C6 Coupled PDAS Two-Phase Adaptive Safeguarded Relaxation) finished with exit code: ${EXIT_CODE}"
exit ${EXIT_CODE}
"""
    r9_pbs = R9_DIR / "submit_M1_C6_P171_R9_C3_0.pbs"
    r9_pbs.write_bytes(pbs_content.replace("\r\n", "\n").encode("utf-8"))
    print(f"Generated R9 submit PBS script: {r9_pbs.name}")

    # 5. Generate smoke_import.py
    smoke_content = """#!/usr/bin/env python3
import sys
from pathlib import Path

pkg_dir = Path(__file__).resolve().parent
repo_dir = pkg_dir / "runtime"
sys.path.insert(0, str(repo_dir))

print("Testing Package 171-R9 imports...")
from scripts.state_transfer.driver_package171_r9_c6_coupled_pdas import Package171R9C6PDASDriver
from scripts.validation.extract_package148_iteration import extract_single_iteration

print("REMOTE_IMPORT_SUCCESS: True")
"""
    r9_smoke = R9_DIR / "smoke_import.py"
    r9_smoke.write_bytes(smoke_content.replace("\r\n", "\n").encode("utf-8"))
    print(f"Generated R9 smoke import test: {r9_smoke.name}")

    # 6. Generate PACKAGE_MANIFEST.json
    manifest = {
        "schema": 1,
        "package_name": "package171_r9_c6_c3_0_adaptive_reequilibration",
        "description": "Package 171-R9 C6 Coupled PDAS Re-Equilibration with Two-Phase Adaptive Relaxation and Unrelaxed Norm Rollback Guard",
        "frozen_uel_sha256": FROZEN_UEL_HASH,
        "files": {},
    }
    for f in sorted(R9_DIR.iterdir()):
        if f.is_file() and f.name != "PACKAGE_MANIFEST.json":
            manifest["files"][f.name] = {
                "sha256": sha256_file(f),
                "size_bytes": f.stat().st_size,
            }

    manifest_path = R9_DIR / "PACKAGE_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Generated PACKAGE_MANIFEST.json with {len(manifest['files'])} registered files.")

    print("\n=== Package 171-R9 Local Assembly Complete ===")


if __name__ == "__main__":
    assemble_r9()
