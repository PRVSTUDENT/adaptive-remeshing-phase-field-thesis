#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_package167_r1_continuation.py
Builder and Preflight for Mode-I Method C Stage C2-2 Package 167-R1 (+5 nm Continuation on C5 Mesh).
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2

Prepares immutable candidate Package 167-R1:
- Mesh: C5 (12,996 elements, 13,278 nodes, 51,984 integration points)
- Load increment: Advancing uy from 0.0018653125442191958 mm to 0.0018703125442191958 mm (+5.0 nm)
- Enforces strict authentic Checkpoint 02 binding from Package 163-R3 (Job 1419499.mmaster02)
- Rejects all disqualified Package 163-R2 artifacts (Job 1419489.mmaster02)
- Validated reference comparator: Package 169 Reference B (Job 1419543.mmaster02)
- Fixes indirect runtime import defect: adds scripts/state_transfer/c3_int_to_c4_spatial_mapping.py
"""

from __future__ import print_function, division
import json
import hashlib
import shutil
import sys
import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.stage_c2_2_specification import (
    get_c2_2_specification,
    evaluate_c2_2_submission_eligibility,
    BASELINE_UY_MM, TARGET_UY_MM, INCREMENT_UY_MM,
    FROZEN_UEL_SHA256, TOTAL_C5_NODES, TOTAL_C5_ELEMENTS,
    R3_RUN_DIR, ACTIVE_PREDECESSOR_JOB_ID, DISQUALIFIED_PREDECESSOR_JOB_IDS
)

PKG_167_SRC = REPO_ROOT / "models/pandey_kumar_mode1/167_c5_package167_c2_2_continuation"
PKG_167_R1_DIR = REPO_ROOT / "models/pandey_kumar_mode1/167_c5_package167_r1_c2_2_continuation"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c5_package167_r1_c2_2_continuation"
CHECKPOINT_02_SRC = R3_RUN_DIR / "evidence/1419499.mmaster02/converged_checkpoint_02.json"
CHECKPOINT_02_CANONICAL_HASH = "8201D8200A12C8A493ABA8550DA7D66DB9301C2389A9EA1409BCB5B9E57B4FEA"


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()


def canonical(cmd):
    return " ".join(cmd.strip().split())


def build_c2_2_r1_package():
    """
    Build candidate Package 167-R1 directory and manifests.
    """
    PKG_167_R1_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Verify Checkpoint 02 hash
    chkpt_path = PKG_167_SRC / "initial_checkpoint_02.json"
    chkpt_hash = sha256_file(chkpt_path)
    assert chkpt_hash == CHECKPOINT_02_CANONICAL_HASH, f"Checkpoint 02 hash mismatch: {chkpt_hash} != {CHECKPOINT_02_CANONICAL_HASH}"

    # 2. Verify frozen UEL hash
    uel_src = PKG_167_SRC / "f42_mixed_uel.for"
    uel_hash = sha256_file(uel_src)
    assert uel_hash == FROZEN_UEL_SHA256, f"Frozen UEL hash violation: {uel_hash} != {FROZEN_UEL_SHA256}"

    # 3. Copy base physics/model files from PKG_167_SRC
    base_files = [
        "initial_checkpoint_02.json",
        "f42_mixed_uel.for",
        "M1_C5_PACKAGE167_C2_2_CONTINUATION.inp",
        "P167_MECHANICAL_DC.inp",
        "P167_PHASE_DC.inp",
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
    ]

    for fname in base_files:
        src = PKG_167_SRC / fname
        dst = PKG_167_R1_DIR / fname
        shutil.copy2(src, dst)

    # 4. Create submit_M1_C5_P167_R1_C2_2.pbs
    pbs_content = f"""#!/bin/bash
#PBS -N M1_C5_P167_R1_C2_2
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o {REMOTE_RUN_DIR}/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="{REMOTE_RUN_DIR}"
cd "${{RUN_DIR}}"

export JOB_NAME="M1_C5_P167_R1_C2_2"
export NOTIFICATION_CONFIG="${{NOTIFICATION_CONFIG:-${{HOME}}/.config/adaptive-remeshing/notifications.env}}"
source "${{RUN_DIR}}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

repo="${{RUN_DIR}}/runtime"
python3 "${{repo}}/scripts/state_transfer/driver_package167_c5_continuation.py" \\
    --package "${{RUN_DIR}}" \\
    --output "${{RUN_DIR}}/continuation_${{PBS_JOBID}}" \\
    --extractor "${{repo}}/scripts/validation/extract_package148_iteration.py" \\
    --memory-gb 16 \\
    --timeout 25200 \\
    --max-outer 300
EXIT_CODE=$?

echo "Stage C2-2 Forward Continuation finished with exit code: ${{EXIT_CODE}}"
exit ${{EXIT_CODE}}
"""
    with open(PKG_167_R1_DIR / "submit_M1_C5_P167_R1_C2_2.pbs", "w", encoding="utf-8", newline="\n") as f:
        f.write(pbs_content)

    # 5. Create run_datacheck.sh
    dc_script_content = f"""#!/bin/bash
set -euo pipefail
cd "{REMOTE_RUN_DIR}"

case "${{1:-}}" in
  mechanical) job=P167_MECHANICAL_DC ;;
  phase) job=P167_PHASE_DC ;;
  *) echo 'Exact mechanical or phase role required' >&2; exit 64 ;;
esac

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

abaqus job="${{job}}" input="${{job}}.inp" user=f42_mixed_uel.for cpus=1 memory="16 gb" datacheck interactive > "${{job}}.stdout.txt" 2>&1
test -f "${{job}}.dat"
grep -q 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' "${{job}}.dat" || grep -q 'ANALYSIS DATACHECK COMPLETE' "${{job}}.dat"
if grep -q '\\*\\*\\*ERROR' "${{job}}.dat"; then exit 66; fi
echo "${{job}}: AUTHENTIC_DATACHECK_PASS"
"""
    with open(PKG_167_R1_DIR / "run_datacheck.sh", "w", encoding="utf-8", newline="\n") as f:
        f.write(dc_script_content)

    # 6. Build file list for manifests
    manifest_files = [
        "initial_checkpoint_02.json",
        "f42_mixed_uel.for",
        "M1_C5_PACKAGE167_C2_2_CONTINUATION.inp",
        "P167_MECHANICAL_DC.inp",
        "P167_PHASE_DC.inp",
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "initial_conditions_solution.inc",
        "job_notifications.sh",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "submit_M1_C5_P167_R1_C2_2.pbs",
        "run_datacheck.sh"
    ]

    # If DAT files exist in PKG_167_R1_DIR, add them
    for dat_name in ["P167_MECHANICAL_DC.dat", "P167_PHASE_DC.dat"]:
        dat_p = PKG_167_R1_DIR / dat_name
        if dat_p.is_file():
            manifest_files.append(dat_name)

    pkg_manifest_files = {}
    for mf in sorted(manifest_files):
        pkg_manifest_files[mf] = sha256_file(PKG_167_R1_DIR / mf).lower()

    pkg_manifest = {
        "schema": 1,
        "package": "Package 167-R1 Stage C2-2 +5 nm Forward Continuation",
        "mesh": "Candidate C5 Mesh (12,996 quads, 13,278 nodes, 51,984 GPs)",
        "baseline_uy_mm": BASELINE_UY_MM,
        "target_uy_mm": TARGET_UY_MM,
        "increment_nm": 5.0,
        "max_outer": 300,
        "predecessor_checkpoint_02_sha256": chkpt_hash,
        "reference_b_comparator_job_id": "1419543.mmaster02",
        "files": pkg_manifest_files
    }
    (PKG_167_R1_DIR / "PACKAGE_MANIFEST.json").write_text(json.dumps(pkg_manifest, indent=2), encoding="utf-8")

    exec_manifest_files = dict(pkg_manifest_files)
    exec_manifest_files["PACKAGE_MANIFEST.json"] = sha256_file(PKG_167_R1_DIR / "PACKAGE_MANIFEST.json").lower()

    # Complete transitive runtime sources including c3_int_to_c4_spatial_mapping.py!
    runtime_sources = {
        "scripts/state_transfer/driver_package167_c5_continuation.py": sha256_file(REPO_ROOT / "scripts/state_transfer/driver_package167_c5_continuation.py"),
        "scripts/validation/extract_package148_iteration.py": sha256_file(REPO_ROOT / "scripts/validation/extract_package148_iteration.py"),
        "scripts/state_transfer/c4_to_c5_spatial_mapping.py": sha256_file(REPO_ROOT / "scripts/state_transfer/c4_to_c5_spatial_mapping.py"),
        "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py": sha256_file(REPO_ROOT / "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py"),
        "scripts/state_transfer/driver_package146_147_pdas_continuation.py": sha256_file(REPO_ROOT / "scripts/state_transfer/driver_package146_147_pdas_continuation.py")
    }

    cmd = f'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq {REMOTE_RUN_DIR}/submit_M1_C5_P167_R1_C2_2.pbs"'
    cmd_sha256 = hashlib.sha256(canonical(cmd).encode()).hexdigest()

    jobs = [
        {
            "id": "M1_C5_P167_R1_C2_2",
            "purpose": "Mode-I Stage C2-2 Package 167-R1 +5 nm forward continuation on C5 receiver mesh advancing from Checkpoint 02 to target uy=0.001870312544 mm with max_outer=300",
            "input": "P167_MECHANICAL_DC.inp",
            "datacheck": "P167_MECHANICAL_DC.dat",
            "additional_datachecks": [
                "P167_PHASE_DC.dat"
            ],
            "pbs": "submit_M1_C5_P167_R1_C2_2.pbs",
            "queue": "entry_imfdfkmq",
            "cpus": 1,
            "memory_gb": 16,
            "walltime_hours": 8,
            "execution": "single-rank serial",
            "max_submissions": 1,
            "depends_on": [],
            "command": cmd,
            "command_sha256": cmd_sha256
        }
    ]

    exec_manifest = {
        "batch_name": "MODE1_PACKAGE167_R1_M1_C5_P167_R1_C2_2",
        "adapter": "mode1-qualified-batch-v2",
        "scientific_scope": "MODE1",
        "technical_stage": "MODE1_BASELINE",
        "configuration": "MODE1_BASELINE",
        "max_submissions": 1,
        "automatic_retry": False,
        "remote_run_dir": REMOTE_RUN_DIR,
        "runtime_root": f"{REMOTE_RUN_DIR}/runtime",
        "runtime_source_hashes": runtime_sources,
        "files": exec_manifest_files,
        "scientific_predecessor_review": "results/validation/mode1_f1597/package169_reference_evaluation.json",
        "jobs": jobs,
        "acceptance": {
            "M1_C5_P167_R1_C2_2": "Mode-I Stage C2-2 Package 167-R1 +5 nm forward continuation meeting coupled PDAS convergence (delta_d <= 1e-5, delta_u <= 1e-9 mm, delta_h <= 1e-4 MPa, force <= 2%, energy <= 2% against Package 169 Reference B) and physical acceptance with max_outer=300"
        }
    }
    (PKG_167_R1_DIR / "EXECUTION_MANIFEST.json").write_text(json.dumps(exec_manifest, indent=2), encoding="utf-8")

    return {
        "success": True,
        "status": "PACKAGE_167_R1_ASSEMBLED",
        "package_path": str(PKG_167_R1_DIR),
        "predecessor_checkpoint_sha256": chkpt_hash,
        "predecessor_job_id": ACTIVE_PREDECESSOR_JOB_ID,
        "reference_b_job_id": "1419543.mmaster02",
        "uel_sha256": uel_hash
    }


if __name__ == "__main__":
    res = build_c2_2_r1_package()
    print(json.dumps(res, indent=2))
