"""Build reviewed Package 157 Revision 5 Segment 2 continuation from an authentic committed checkpoint.

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Ingests an authentic committed checkpoint (e.g., converged_checkpoint_05.json from Segment 1
or an authentic offline test fixture), validates all 7,265 nodal displacement states,
7,265 phase values, and 28,224 GP driving histories, and deterministically generates
the complete Package 157 Revision 5 Segment 2 model package.
"""
from __future__ import print_function, division
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.state_transfer.checkpoint_ingestion import (
    validate_checkpoint_structure,
    generate_restart_assets,
    NUM_PHYSICAL_NODES,
    NUM_PHYSICAL_ELEMENTS,
    TOTAL_HISTORY_POINTS,
)
from scripts.state_transfer.driver_package157_r5_seg2 import (
    AdaptiveContinuationR5Seg2,
    START as SEG2_START,
    TARGETS as SEG2_TARGETS,
)

REL = "models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r5_seg2"
REMOTE = "/scratch9/pr21vyci/runs/mode1_c4_package157_c1_2_continuation_r5_seg2"
JOB = "M1_C4_P157_C1_2_R5_SEG2"
SOURCES = [
    "scripts/state_transfer/driver_package157_r5_seg2.py",
    "scripts/state_transfer/driver_package150_c1_2_continuation.py",
    "scripts/state_transfer/driver_package146_147_pdas_continuation.py",
    "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py",
    "scripts/validation/extract_package148_iteration.py",
    "scripts/state_transfer/checkpoint_ingestion.py",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text(path, value):
    path.write_bytes(value.replace("\r\n", "\n").encode("utf-8"))


def pbs(job, body, hours=8):
    return """#!/bin/bash
#PBS -N %s
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=%02d:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o %s/%s.pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
set -euo pipefail
RUN_DIR="%s"
cd "${RUN_DIR}"
export JOB_NAME="%s"
export NOTIFICATION_CONFIG="${NOTIFICATION_CONFIG:-${HOME}/.config/adaptive-remeshing/notifications.env}"
source "${RUN_DIR}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start
if ! type module >/dev/null 2>&1; then
 source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort
%s
""" % (job, hours, REMOTE, job, REMOTE, job, body)


def manifest(files, runtime, job, pbs_name, purpose, hours, predecessor_review):
    command = (
        'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "qsub -q entry_imfdfkmq '
        + REMOTE
        + "/"
        + pbs_name
        + '"'
    )
    return dict(
        batch_name="MODE1_PACKAGE157_" + job,
        adapter="mode1-qualified-batch-v2",
        scientific_scope="MODE1",
        technical_stage="C1-2",
        configuration="MODE1_BASELINE",
        max_submissions=1,
        automatic_retry=False,
        remote_run_dir=REMOTE,
        runtime_root=REMOTE + "/runtime",
        runtime_source_hashes=runtime,
        files=files,
        scientific_predecessor_review=predecessor_review,
        jobs=[
            dict(
                id=job,
                purpose=purpose,
                input="P157_MECHANICAL_DC.inp",
                datacheck="P157_MECHANICAL_DC.dat",
                additional_datachecks=["P157_PHASE_DC.dat"],
                pbs=pbs_name,
                queue="entry_imfdfkmq",
                cpus=1,
                memory_gb=16,
                walltime_hours=hours,
                execution="single-rank serial",
                max_submissions=1,
                depends_on=[],
                command=command,
                command_sha256=hashlib.sha256(command.encode()).hexdigest(),
            )
        ],
        acceptance={job: purpose},
    )


def build_package_seg2(checkpoint_path, package_dir=None, dry_run=False, expected_baseline_uy=None):
    """Build Package 157 Revision 5 Segment 2 from checkpoint_path."""
    chk_path = Path(checkpoint_path).resolve()
    if not chk_path.is_file():
        raise FileNotFoundError("Missing checkpoint file: %s" % chk_path)

    chk_data = json.loads(chk_path.read_text(encoding="utf-8"))
    baseline_uy = expected_baseline_uy if expected_baseline_uy is not None else SEG2_START
    parsed = validate_checkpoint_structure(chk_data, expected_target_uy=baseline_uy)

    package = Path(package_dir).resolve() if package_dir else ROOT / REL
    if dry_run:
        return {
            "status": "VALIDATED_DRY_RUN",
            "checkpoint": str(chk_path),
            "target_uy_mm": parsed["target_uy_mm"],
            "nodes": len(parsed["u"]),
            "elements": NUM_PHYSICAL_ELEMENTS,
            "history_points": len(parsed["h"]),
        }

    if package.exists():
        shutil.rmtree(package)
    package.mkdir(parents=True, exist_ok=False)

    template_source = ROOT / "models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r5"
    for name in ["f42_mixed_uel.for", "job_notifications.sh", "M1_C4_PACKAGE150_C1_2_CONTINUATION.inp"]:
        shutil.copyfile(template_source / name, package / name)
    assert sha(package / "f42_mixed_uel.for") == "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

    assets = generate_restart_assets(parsed, package)

    runtime = {name: sha(ROOT / name).upper() for name in SOURCES}
    initial_files = {p.name: sha(p) for p in package.iterdir()}

    # Compute targets for this baseline
    targets = [baseline_uy + i * 1e-5 for i in range(1, 6)]

    pkg = dict(
        schema=1,
        package=157,
        revision="R5_SEG2",
        files=initial_files,
        runtime_source_hashes=runtime,
        baseline_uy_mm=baseline_uy,
        targets_mm=targets,
        history_gp_order="MAPPER_ROW_FROM_UEL_PERIMETER",
        history_card_max_difference_MPa=assets["max_card_difference_MPa"],
        checkpoint_source=str(chk_path),
        checkpoint_sha256=sha(chk_path).upper(),
        max_outer=100,
        max_phase=20,
        minimum_increment_mm=5e-6,
        maximum_subdivision_level=2,
        physical_acceptance="UNVERIFIED",
        force_discrepancy_pct_max=5.0,
        raw_energy_discrepancy_pct_max=2.0,
    )
    text(package / "PACKAGE_MANIFEST.json", json.dumps(pkg, indent=2) + "\n")

    controller = AdaptiveContinuationR5Seg2(package, package / "unused", ROOT / SOURCES[4], max_outer=100)
    controller.load()
    for role in ("mechanical", "phase"):
        text(
            package / ("P157_" + role.upper() + "_DC.inp"),
            controller._deck(1, role, controller.d0, set(controller.d0), controller.u0, controller.h0, targets[0]),
        )

    dc = """#!/bin/bash
set -euo pipefail
cd "${1:?exact run directory required}"
for role in MECHANICAL PHASE; do
 job="P157_${role}_DC"
 test ! -e "${job}.dat"
 abaqus job="${job}" input="${job}.inp" user=f42_mixed_uel.for cpus=1 memory="16 gb" datacheck interactive > "${job}.stdout.txt" 2>&1
 test -f "${job}.dat"
 grep -q 'ANALYSIS DATACHECK COMPLETE' "${job}.dat"
 if grep -q '\\*\\*\\*ERROR' "${job}.dat"; then exit 66; fi
done
echo AUTHENTIC_DATACHECK_PASS_BOTH
"""
    text(package / "run_datacheck.sh", dc)

    startup = (
        'python3 "${RUN_DIR}/runtime/scripts/state_transfer/driver_package157_r5_seg2.py" --package "${RUN_DIR}"'
        ' --output "${RUN_DIR}/continuation_${PBS_JOBID}"'
        ' --extractor "${RUN_DIR}/runtime/scripts/validation/extract_package148_iteration.py"'
    )
    text(package / ("submit_" + JOB + ".pbs"), pbs(JOB, startup, 8))

    dc_job = "M1_C4_P157_R5_SEG2_DC"
    qualification_body = """test ! -e compute_datacheck
mkdir compute_datacheck
cp P157_MECHANICAL_DC.inp P157_PHASE_DC.inp f42_mixed_uel.for compute_datacheck/
bash "${RUN_DIR}/run_datacheck.sh" "${RUN_DIR}/compute_datacheck"
%s --startup-only > "${RUN_DIR}/compute_startup.json"
hostname > "${RUN_DIR}/compute_datacheck_host.txt" """ % startup
    text(package / ("submit_" + dc_job + ".pbs"), pbs(dc_job, qualification_body, 1))

    pkg["files"] = {p.name: sha(p) for p in package.iterdir() if p.name != "PACKAGE_MANIFEST.json"}
    text(package / "PACKAGE_MANIFEST.json", json.dumps(pkg, indent=2) + "\n")
    files = {p.name: sha(p) for p in package.iterdir()}

    for filename, jid, purpose, hours in [
        (
            "EXECUTION_MANIFEST.json",
            JOB,
            (
                "Reviewed R5 Segment 2 forward continuation (5 x 10 nm increments, max_outer=100) from accepted"
                " Segment 1; convergence and full state preservation required; physical PASS only after matching-load"
                " force <=5% and raw energy <=2% review. No C5 execution or automatic PBS retry."
            ),
            8,
        ),
        (
            "QUALIFICATION_EXECUTION_MANIFEST.json",
            dc_job,
            (
                "Required authentic COMPUTE-NODE Abaqus mechanical/phase datachecks and actual R5 Segment 2 runtime"
                " startup; zero numerical continuation."
            ),
            1,
        ),
    ]:
        text(
            package / filename,
            json.dumps(
                manifest(
                    files,
                    runtime,
                    jid,
                    "submit_" + jid + ".pbs",
                    purpose,
                    hours,
                    "results/validation/package157_r5_seg2_preparation/segment2_restart_readiness.json",
                ),
                indent=2,
            )
            + "\n",
        )

    return {
        "status": "PACKAGE_BUILT",
        "package": str(package),
        "job": JOB,
        "files_count": len(files),
        "baseline_uy_mm": baseline_uy,
        "targets_mm": targets,
        "max_outer": 100,
        "max_card_difference_MPa": assets["max_card_difference_MPa"],
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True, help="Path to authentic checkpoint JSON")
    parser.add_argument("--package-dir", default=None, help="Output package directory")
    parser.add_argument("--expected-baseline-uy", type=float, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = build_package_seg2(
        checkpoint_path=args.checkpoint,
        package_dir=args.package_dir,
        dry_run=args.dry_run,
        expected_baseline_uy=args.expected_baseline_uy,
    )
    print(json.dumps(result, indent=2))
