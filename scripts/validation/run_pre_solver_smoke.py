#!/usr/bin/env python3
"""Run local or cluster pre-solver smoke test for Stage F Mode-II H0 serial PBS script."""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def to_posix_path(p: Path) -> str:
    s = p.resolve().as_posix()
    if len(s) >= 2 and s[1] == ":":
        s = "/mnt/" + s[0].lower() + s[2:]
    return s


def run_pre_solver_smoke(
    project_root: Path = ROOT,
    stage_root: Path | None = None,
    scratch_root: Path | None = None,
    evidence_root: Path | None = None,
    project_revision: str | None = None,
    allow_no_modules: bool = False,
    output_summary: Path | None = None,
    evidence_output_dir: Path | None = None,
) -> tuple[int, dict]:
    started_at_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    failures: list[str] = []

    if project_revision is None:
        try:
            rev_proc = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            project_revision = rev_proc.stdout.strip()
        except Exception:
            project_revision = "unknown"

    req_stage_root = stage_root if stage_root is not None else project_root / "tmp" / "smoke_stage"
    staged_root = req_stage_root / "mode_ii_h0_staged" / project_revision
    req_scratch_root = scratch_root if scratch_root is not None else req_stage_root / "scratch"
    req_evidence_root = evidence_root if evidence_root is not None else req_stage_root / "evidence"

    res_stage_root = req_stage_root.resolve()
    res_scratch_root = req_scratch_root.resolve()
    res_evidence_root = req_evidence_root.resolve()

    if staged_root.exists():
        shutil.rmtree(staged_root, ignore_errors=True)
    if req_scratch_root.exists():
        shutil.rmtree(req_scratch_root, ignore_errors=True)
    if req_evidence_root.exists():
        shutil.rmtree(req_evidence_root, ignore_errors=True)

    (staged_root / "models" / "generated" / "mode_ii").mkdir(parents=True, exist_ok=True)
    (staged_root / "runtime" / "scripts" / "hpc" / "stage_f").mkdir(parents=True, exist_ok=True)
    (staged_root / "runtime" / "scripts" / "postprocessing").mkdir(parents=True, exist_ok=True)
    (staged_root / "runtime" / "scripts" / "validation").mkdir(parents=True, exist_ok=True)
    req_scratch_root.mkdir(parents=True, exist_ok=True)
    req_evidence_root.mkdir(parents=True, exist_ok=True)

    pkg_src = project_root / "models" / "generated" / "mode_ii" / "h0_serial"
    pbs_src = project_root / "scripts" / "hpc" / "stage_f" / "02_mode_ii_h0_serial.pbs"
    ext_src = project_root / "scripts" / "postprocessing" / "extract_molnar_single_notch.py"
    val_src = project_root / "scripts" / "validation" / "validate_mode_ii_h0_serial_results.py"
    verifier_src = project_root / "scripts" / "validation" / "verify_mode_ii_h0_runtime_staging.py"

    for required_file in (
        pkg_src / "ModeII_H0_serial.inp",
        pkg_src / "ModeII_H0_serial.for",
        pbs_src,
        ext_src,
        val_src,
        verifier_src,
    ):
        if not required_file.is_file():
            failures.append(f"Missing required source file: {required_file}")

    if failures:
        completed_at_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        summary = {
            "classification": "stage_f_mode_ii_h0_pre_solver_smoke_fail",
            "pbs_exit_code": -1,
            "status_classification_pass": False,
            "pre_solver_smoke_ok": False,
            "runtime_staging_classification_pass": False,
            "runtime_failures_empty": False,
            "abaqus_invoked": False,
            "extractor_invoked": False,
            "validator_invoked": False,
            "odb_file_count": 0,
            "abaqus_lock_file_count": 0,
            "solver_output_file_count": 0,
            "module_environment_loaded": False,
            "failures": failures,
        }
        if output_summary:
            output_summary.parent.mkdir(parents=True, exist_ok=True)
            output_summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 1, summary

    staged_pkg = staged_root / "models" / "generated" / "mode_ii" / "h0_serial"
    staged_pbs = staged_root / "runtime" / "scripts" / "hpc" / "stage_f" / "02_mode_ii_h0_serial.pbs"
    staged_ext = staged_root / "runtime" / "scripts" / "postprocessing" / "extract_molnar_single_notch.py"
    staged_val = staged_root / "runtime" / "scripts" / "validation" / "validate_mode_ii_h0_serial_results.py"
    staged_verifier = (
        staged_root / "runtime" / "scripts" / "validation" / "verify_mode_ii_h0_runtime_staging.py"
    )

    shutil.copytree(pkg_src, staged_pkg)
    shutil.copy(pbs_src, staged_pbs)
    shutil.copy(ext_src, staged_ext)
    shutil.copy(val_src, staged_val)
    shutil.copy(verifier_src, staged_verifier)

    deck_sha = sha256_file(staged_pkg / "ModeII_H0_serial.inp")
    source_sha = sha256_file(staged_pkg / "ModeII_H0_serial.for")
    ext_sha = sha256_file(staged_ext)
    val_sha = sha256_file(staged_val)
    verifier_sha = sha256_file(staged_verifier)
    pbs_sha = sha256_file(staged_pbs)

    login_manifest = staged_root / "MODE_II_H0_LOGIN_MANIFEST.json"
    login_manifest.write_text(
        json.dumps(
            {
                "classification": "stage_f_mode_ii_h0_login_staging_complete",
                "compute_git_required": False,
                "deck_sha256": deck_sha,
                "extractor_sha256": ext_sha,
                "pbs_script_sha256": pbs_sha,
                "project_revision": project_revision,
                "source_sha256": source_sha,
                "staging_checker_sha256": verifier_sha,
                "validator_sha256": val_sha,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    p_staged = to_posix_path(staged_root)
    p_runtime = to_posix_path(staged_root / "runtime")
    p_login = to_posix_path(login_manifest)
    p_scratch = to_posix_path(req_scratch_root)
    p_evidence = to_posix_path(req_evidence_root)
    pbs_posix = to_posix_path(staged_pbs)

    allow_modules_val = "1" if allow_no_modules else "0"
    cmd_str = (
        f"PRESTAGED_ROOT='{p_staged}' "
        f"PRESTAGED_RUNTIME_ROOT='{p_runtime}' "
        f"LOGIN_MANIFEST_PATH='{p_login}' "
        f"PROJECT_REVISION='{project_revision}' "
        "MODE_II_H0_PRE_SOLVER_ONLY=1 "
        f"MODE_II_H0_ALLOW_LOCAL_NO_MODULES={allow_modules_val} "
        "PBS_JOBID=manual_f1_j1_r2_preflight "
        f"EVIDENCE_ROOT='{p_evidence}' "
        f"SCRATCH_RUN='{p_scratch}' "
        f"bash '{pbs_posix}'"
    )

    bash_executable = shutil.which("bash") or "bash"
    proc = subprocess.run(
        [bash_executable, "-c", cmd_str],
        cwd=staged_root,
        capture_output=True,
        text=True,
    )

    completed_at_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

    status_file = req_scratch_root / "MODE_II_H0_SERIAL_STATUS.json"
    staging_file = req_scratch_root / "MODE_II_H0_RUNTIME_STAGING_CHECK.json"
    smoke_marker = req_scratch_root / "MODE_II_H0_PRE_SOLVER_SMOKE.ok"
    serial_marker = req_scratch_root / "MODE_II_H0_SERIAL.ok"
    executables_file = req_scratch_root / "executables.txt"

    status_data: dict = {}
    staging_data: dict = {}

    status_classification_pass = False
    pre_solver_smoke_ok = False
    runtime_staging_classification_pass = False
    runtime_failures_empty = False
    abaqus_invoked = False
    extractor_invoked = False
    validator_invoked = False
    module_environment_loaded = False

    if proc.returncode != 0:
        failures.append(f"PBS script process returned nonzero exit code: {proc.returncode}")

    if not status_file.is_file():
        failures.append(f"Status file missing: {status_file}")
    else:
        try:
            status_data = json.loads(status_file.read_text(encoding="utf-8"))
            if status_data.get("classification") == "stage_f_mode_ii_h0_pre_solver_smoke_pass":
                status_classification_pass = True
            else:
                failures.append(f"Unexpected status classification: {status_data.get('classification')}")

            if "MODE_II_H0_SERIAL_ok" in status_data:
                failures.append("MODE_II_H0_SERIAL_ok is improperly present in smoke status JSON")

            if status_data.get("pre_solver_smoke_ok") is True:
                pre_solver_smoke_ok = True
            else:
                failures.append("pre_solver_smoke_ok is missing or false in status JSON")

            if status_data.get("abaqus_invoked") is True:
                abaqus_invoked = True
                failures.append("Abaqus was reported as invoked during pre-solver smoke")

            if status_data.get("extractor_invoked") is True:
                extractor_invoked = True
                failures.append("Extractor was reported as invoked during pre-solver smoke")

            if status_data.get("validator_invoked") is True:
                validator_invoked = True
                failures.append("Validator was reported as invoked during pre-solver smoke")

            for rc_key in ("abaqus_return_code", "extractor_return_code", "validator_return_code"):
                if status_data.get(rc_key) is not None:
                    failures.append(
                        f"{rc_key} must be null in pre-solver smoke status JSON but got {status_data.get(rc_key)}"
                    )

            if status_data.get("module_environment_loaded") is True:
                module_environment_loaded = True

            if status_data.get("failures"):
                failures.extend([f"Status report failure: {f}" for f in status_data["failures"]])
        except Exception as err:
            failures.append(f"Failed to parse status file JSON: {err}")

    if not staging_file.is_file():
        failures.append(f"Staging check file missing: {staging_file}")
    else:
        try:
            staging_data = json.loads(staging_file.read_text(encoding="utf-8"))
            if staging_data.get("classification") == "stage_f_mode_ii_h0_runtime_staging_pass":
                runtime_staging_classification_pass = True
            else:
                failures.append(f"Unexpected staging classification: {staging_data.get('classification')}")

            if staging_data.get("failures") == []:
                runtime_failures_empty = True
            else:
                failures.extend([f"Staging failure: {f}" for f in staging_data.get("failures", [])])
        except Exception as err:
            failures.append(f"Failed to parse staging file JSON: {err}")

    if not smoke_marker.is_file():
        failures.append(f"Smoke marker file missing: {smoke_marker}")

    if serial_marker.is_file():
        failures.append(f"Full solver completion marker improperly created during smoke: {serial_marker}")

    if not allow_no_modules:
        if not module_environment_loaded:
            failures.append("Cluster qualification requires module_environment_loaded = true")

        if not executables_file.is_file():
            failures.append(f"Executables log missing: {executables_file}")
        else:
            exec_text = executables_file.read_text(encoding="utf-8")
            if not exec_text.strip() or "abaqus" not in exec_text.lower() or "not found" in exec_text.lower():
                failures.append("Cluster qualification requires a valid Abaqus executable path in executables.txt")
            if "python3" not in exec_text.lower() or "not found" in exec_text.lower():
                failures.append("Cluster qualification requires python3 in executables.txt")

    odb_files: list[Path] = []
    lck_files: list[Path] = []
    solver_out_files: list[Path] = []

    for search_dir in (req_stage_root, req_scratch_root, req_evidence_root):
        if search_dir.exists():
            odb_files.extend(search_dir.rglob("*.odb"))
            lck_files.extend(search_dir.rglob("*.lck"))
            for ext in (".dat", ".msg", ".sta", ".prt", ".com", ".sim"):
                solver_out_files.extend(search_dir.rglob(f"*{ext}"))

    odb_file_count = len(odb_files)
    abaqus_lock_file_count = len(lck_files)
    solver_output_file_count = len(solver_out_files)

    if odb_file_count > 0:
        failures.append(f"Found {odb_file_count} .odb files during pre-solver smoke run")
    if abaqus_lock_file_count > 0:
        failures.append(f"Found {abaqus_lock_file_count} .lck files during pre-solver smoke run")
    if solver_output_file_count > 0:
        failures.append(f"Found {solver_output_file_count} solver output files during pre-solver smoke run")

    classification = (
        "stage_f_mode_ii_h0_pre_solver_smoke_pass"
        if not failures
        else "stage_f_mode_ii_h0_pre_solver_smoke_fail"
    )

    summary = {
        "classification": classification,
        "pbs_exit_code": proc.returncode,
        "status_classification_pass": status_classification_pass,
        "pre_solver_smoke_ok": pre_solver_smoke_ok,
        "runtime_staging_classification_pass": runtime_staging_classification_pass,
        "runtime_failures_empty": runtime_failures_empty,
        "abaqus_invoked": abaqus_invoked,
        "extractor_invoked": extractor_invoked,
        "validator_invoked": validator_invoked,
        "odb_file_count": odb_file_count,
        "abaqus_lock_file_count": abaqus_lock_file_count,
        "solver_output_file_count": solver_output_file_count,
        "module_environment_loaded": module_environment_loaded,
        "failures": failures,
    }

    if evidence_output_dir is not None:
        evidence_output_dir.mkdir(parents=True, exist_ok=True)

        (evidence_output_dir / "stdout.log").write_text(proc.stdout, encoding="utf-8")
        (evidence_output_dir / "stderr.log").write_text(proc.stderr, encoding="utf-8")

        for f_name, f_path in (
            ("MODE_II_H0_SERIAL_STATUS.json", status_file),
            ("MODE_II_H0_RUNTIME_MANIFEST.json", req_scratch_root / "MODE_II_H0_RUNTIME_MANIFEST.json"),
            ("MODE_II_H0_RUNTIME_STAGING_CHECK.json", staging_file),
            ("MODE_II_H0_LOGIN_MANIFEST.json", login_manifest),
            ("executables.txt", executables_file),
        ):
            if f_path.is_file():
                shutil.copy(f_path, evidence_output_dir / f_name)
            else:
                (evidence_output_dir / f_name).write_text("", encoding="utf-8")

        cmd_metadata = {
            "hostname": platform.node(),
            "timestamp_utc": started_at_utc,
            "project_revision": project_revision,
            "pbs_script_sha256": pbs_sha,
            "staging_verifier_sha256": verifier_sha,
            "requested_stage_root": str(req_stage_root),
            "resolved_stage_root": str(res_stage_root),
            "requested_scratch_root": str(req_scratch_root),
            "resolved_scratch_root": str(res_scratch_root),
            "requested_evidence_root": str(req_evidence_root),
            "resolved_evidence_root": str(res_evidence_root),
            "environment_variables": {
                "MODE_II_H0_PRE_SOLVER_ONLY": "1",
                "MODE_II_H0_ALLOW_LOCAL_NO_MODULES": allow_modules_val,
            },
            "module_bypass_allowed": allow_no_modules,
        }
        (evidence_output_dir / "SMOKE_COMMAND.json").write_text(
            json.dumps(cmd_metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        (evidence_output_dir / "SMOKE_SUMMARY.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        inv_data = {
            "odb_file_count": odb_file_count,
            "abaqus_lock_file_count": abaqus_lock_file_count,
            "solver_output_file_count": solver_output_file_count,
        }
        (evidence_output_dir / "file_inventory.json").write_text(
            json.dumps(inv_data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        bundle_files = [
            "SMOKE_COMMAND.json",
            "SMOKE_SUMMARY.json",
            "MODE_II_H0_SERIAL_STATUS.json",
            "MODE_II_H0_RUNTIME_MANIFEST.json",
            "MODE_II_H0_RUNTIME_STAGING_CHECK.json",
            "MODE_II_H0_LOGIN_MANIFEST.json",
            "executables.txt",
            "stdout.log",
            "stderr.log",
            "file_inventory.json",
        ]

        file_hashes: dict[str, str] = {}
        for bf in bundle_files:
            bf_path = evidence_output_dir / bf
            if bf_path.is_file():
                file_hashes[bf] = sha256_file(bf_path)
            else:
                failures.append(f"Bundle file missing in output directory: {bf}")

        bundle_manifest = {
            "classification": "stage_f_mode_ii_h0_pre_solver_smoke_evidence_complete",
            "hostname": platform.node(),
            "started_at_utc": started_at_utc,
            "completed_at_utc": completed_at_utc,
            "project_revision": project_revision,
            "pbs_exit_code": proc.returncode,
            "module_environment_loaded": module_environment_loaded,
            "abaqus_invoked": abaqus_invoked,
            "odb_file_count": odb_file_count,
            "files": file_hashes,
            "failures": summary["failures"],
        }
        manifest_path = evidence_output_dir / "EVIDENCE_BUNDLE_MANIFEST.json"
        manifest_path.write_text(
            json.dumps(bundle_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        # Verify every hash in bundle manifest after writing
        for bf, expected_hash in file_hashes.items():
            actual_hash = sha256_file(evidence_output_dir / bf)
            if actual_hash != expected_hash:
                failures.append(
                    f"Hash verification failed for {bf}: expected {expected_hash}, got {actual_hash}"
                )

    if output_summary:
        output_summary.parent.mkdir(parents=True, exist_ok=True)
        output_summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return (0 if classification == "stage_f_mode_ii_h0_pre_solver_smoke_pass" else 1), summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--stage-root", type=Path, default=None)
    parser.add_argument("--scratch-root", type=Path, default=None)
    parser.add_argument("--evidence-root", type=Path, default=None)
    parser.add_argument("--project-revision", type=str, default=None)
    parser.add_argument("--allow-no-modules", action="store_true", default=False)
    parser.add_argument("--output-summary", type=Path, default=None)
    parser.add_argument("--evidence-output-dir", type=Path, default=None)

    args = parser.parse_args()

    rc, summary = run_pre_solver_smoke(
        project_root=args.project_root.resolve(),
        stage_root=args.stage_root.resolve() if args.stage_root else None,
        scratch_root=args.scratch_root.resolve() if args.scratch_root else None,
        evidence_root=args.evidence_root.resolve() if args.evidence_root else None,
        project_revision=args.project_revision,
        allow_no_modules=args.allow_no_modules,
        output_summary=args.output_summary.resolve() if args.output_summary else None,
        evidence_output_dir=args.evidence_output_dir.resolve() if args.evidence_output_dir else None,
    )

    print(json.dumps(summary, indent=2, sort_keys=True))
    return rc


if __name__ == "__main__":
    sys.exit(main())
