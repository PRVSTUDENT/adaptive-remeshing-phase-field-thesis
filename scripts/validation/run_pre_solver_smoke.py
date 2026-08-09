#!/usr/bin/env python3
"""Run local or cluster pre-solver smoke test for Stage F Mode-II H0 serial PBS script."""


import argparse
import datetime
import hashlib
import json
import os
import platform
import re
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


def verify_evidence_bundle(bundle_dir: Path) -> tuple[int, dict]:
    failures: list[str] = []
    bundle_dir = Path(bundle_dir)

    if not bundle_dir.exists() or not bundle_dir.is_dir():
        return 1, {
            "classification": "stage_f_mode_ii_h0_pre_solver_smoke_evidence_fail",
            "bundle_dir": str(bundle_dir),
            "failures": [f"Evidence bundle directory does not exist or is not a directory: {bundle_dir}"],
        }

    manifest_file = bundle_dir / "EVIDENCE_BUNDLE_MANIFEST.json"
    manifest_data: dict = {}
    if not manifest_file.is_file() or manifest_file.stat().st_size == 0:
        failures.append("EVIDENCE_BUNDLE_MANIFEST.json is missing or empty")
    else:
        try:
            parsed = json.loads(manifest_file.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                manifest_data = parsed
            else:
                failures.append("EVIDENCE_BUNDLE_MANIFEST.json root is not a JSON object")
        except Exception as err:
            failures.append(f"Failed to parse EVIDENCE_BUNDLE_MANIFEST.json: {err}")

    if manifest_data.get("classification") != "stage_f_mode_ii_h0_pre_solver_smoke_evidence_complete":
        failures.append(
            f"Manifest classification is not evidence-complete: {manifest_data.get('classification')}"
        )

    if manifest_data.get("failures") != []:
        failures.append(f"Manifest contains non-empty failures list: {manifest_data.get('failures')}")

    files_map = manifest_data.get("files")
    if not isinstance(files_map, dict):
        failures.append("Manifest files field is missing or not a dictionary")
        files_map = {}

    required_bundle_files = [
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
        "MODE_II_H0_PRE_SOLVER_SMOKE.ok",
    ]

    for req_fn in required_bundle_files:
        if req_fn not in files_map:
            failures.append(f"Required bundle file missing from manifest files map: {req_fn}")

    if (bundle_dir / "MODE_II_H0_SERIAL.ok").exists():
        failures.append("Forbidden serial completion marker MODE_II_H0_SERIAL.ok present in bundle")

    for fn, exp_hash in files_map.items():
        if not isinstance(exp_hash, str) or not re.match(r"^[0-9a-f]{64}$", exp_hash):
            failures.append(f"Invalid SHA-256 format for {fn} in manifest: {exp_hash}")
            continue

        f_path = bundle_dir / fn
        if not f_path.is_file():
            failures.append(f"Listed bundle file missing from disk: {fn}")
            continue

        if fn not in ("stdout.log", "stderr.log", "MODE_II_H0_PRE_SOLVER_SMOKE.ok") and f_path.stat().st_size == 0:
            failures.append(f"Required bundle file is empty: {fn}")

        try:
            actual_hash = sha256_file(f_path)
            if actual_hash != exp_hash:
                failures.append(f"Hash mismatch for {fn}: expected {exp_hash}, got {actual_hash}")
        except Exception as err:
            failures.append(f"Could not compute hash for {fn}: {err}")

    status_path = bundle_dir / "MODE_II_H0_SERIAL_STATUS.json"
    if status_path.is_file() and status_path.stat().st_size > 0:
        try:
            s_data = json.loads(status_path.read_text(encoding="utf-8"))
            if s_data.get("classification") != "stage_f_mode_ii_h0_pre_solver_smoke_pass":
                failures.append(f"Status classification is not pass: {s_data.get('classification')}")
            if s_data.get("pre_solver_smoke_ok") is not True:
                failures.append("Status pre_solver_smoke_ok is not true")
            if "MODE_II_H0_SERIAL_ok" in s_data:
                failures.append("Status contains forbidden key MODE_II_H0_SERIAL_ok")
            if s_data.get("abaqus_invoked") is not False:
                failures.append("Status abaqus_invoked is not false")
            if s_data.get("extractor_invoked") is not False:
                failures.append("Status extractor_invoked is not false")
            if s_data.get("validator_invoked") is not False:
                failures.append("Status validator_invoked is not false")
            if s_data.get("abaqus_return_code") is not None:
                failures.append("Status abaqus_return_code is not null")
            if s_data.get("extractor_return_code") is not None:
                failures.append("Status extractor_return_code is not null")
            if s_data.get("validator_return_code") is not None:
                failures.append("Status validator_return_code is not null")
        except Exception as err:
            failures.append(f"Failed to parse status file JSON during verification: {err}")

    staging_path = bundle_dir / "MODE_II_H0_RUNTIME_STAGING_CHECK.json"
    if staging_path.is_file() and staging_path.stat().st_size > 0:
        try:
            stg_data = json.loads(staging_path.read_text(encoding="utf-8"))
            if stg_data.get("classification") != "stage_f_mode_ii_h0_runtime_staging_pass":
                failures.append(f"Staging classification is not pass: {stg_data.get('classification')}")
            if stg_data.get("failures") != []:
                failures.append(f"Staging check contains failures: {stg_data.get('failures')}")
        except Exception as err:
            failures.append(f"Failed to parse staging file JSON during verification: {err}")

    inv_path = bundle_dir / "file_inventory.json"
    if inv_path.is_file() and inv_path.stat().st_size > 0:
        try:
            inv_data = json.loads(inv_path.read_text(encoding="utf-8"))
            if inv_data.get("odb_file_count", 0) != 0:
                failures.append(f"File inventory contains non-zero ODB count: {inv_data.get('odb_file_count')}")
            if inv_data.get("abaqus_lock_file_count", 0) != 0:
                failures.append(
                    f"File inventory contains non-zero lock file count: {inv_data.get('abaqus_lock_file_count')}"
                )
            if inv_data.get("solver_output_file_count", 0) != 0:
                failures.append(
                    f"File inventory contains non-zero solver output count: {inv_data.get('solver_output_file_count')}"
                )
        except Exception as err:
            failures.append(f"Failed to parse file_inventory.json during verification: {err}")

    classification = (
        "stage_f_mode_ii_h0_pre_solver_smoke_evidence_complete"
        if not failures
        else "stage_f_mode_ii_h0_pre_solver_smoke_evidence_fail"
    )
    return (0 if not failures else 1), {
        "classification": classification,
        "bundle_dir": str(bundle_dir),
        "failures": failures,
    }


def run_pre_solver_smoke(
    project_root: Path | str = ROOT,
    stage_root: Path | str | None = None,
    scratch_root: Path | str | None = None,
    evidence_root: Path | str | None = None,
    project_revision: str | None = None,
    allow_no_modules: bool = False,
    output_summary: Path | str | None = None,
    evidence_output_dir: Path | str | None = None,
) -> tuple[int, dict]:
    started_at_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    failures: list[str] = []

    req_project_root = os.fspath(project_root)
    req_stage_root = (
        os.fspath(stage_root)
        if stage_root is not None
        else str(Path(req_project_root) / "tmp" / "smoke_stage")
    )
    req_scratch_root = (
        os.fspath(scratch_root)
        if scratch_root is not None
        else str(Path(req_stage_root) / "scratch")
    )
    req_evidence_root = (
        os.fspath(evidence_root)
        if evidence_root is not None
        else str(Path(req_stage_root) / "evidence")
    )

    proj_root_path = Path(req_project_root).resolve()
    res_stage_root = Path(req_stage_root).resolve()
    res_scratch_root = Path(req_scratch_root).resolve()
    res_evidence_root = Path(req_evidence_root).resolve()

    if project_revision is None:
        try:
            rev_proc = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=proj_root_path,
                capture_output=True,
                text=True,
                check=True,
            )
            project_revision = rev_proc.stdout.strip()
        except Exception:
            project_revision = "unknown"

    staged_root = res_stage_root / "mode_ii_h0_staged" / project_revision

    if staged_root.exists():
        shutil.rmtree(staged_root, ignore_errors=True)
    if res_scratch_root.exists():
        shutil.rmtree(res_scratch_root, ignore_errors=True)
    if res_evidence_root.exists():
        shutil.rmtree(res_evidence_root, ignore_errors=True)

    (staged_root / "models" / "generated" / "mode_ii").mkdir(parents=True, exist_ok=True)
    (staged_root / "runtime" / "scripts" / "hpc" / "stage_f").mkdir(parents=True, exist_ok=True)
    (staged_root / "runtime" / "scripts" / "postprocessing").mkdir(parents=True, exist_ok=True)
    (staged_root / "runtime" / "scripts" / "validation").mkdir(parents=True, exist_ok=True)
    res_scratch_root.mkdir(parents=True, exist_ok=True)
    res_evidence_root.mkdir(parents=True, exist_ok=True)

    pkg_src = proj_root_path / "models" / "generated" / "mode_ii" / "h0_serial"
    pbs_src = proj_root_path / "scripts" / "hpc" / "stage_f" / "02_mode_ii_h0_serial.pbs"
    ext_src = proj_root_path / "scripts" / "postprocessing" / "extract_molnar_single_notch.py"
    val_src = proj_root_path / "scripts" / "validation" / "validate_mode_ii_h0_serial_results.py"
    verifier_src = proj_root_path / "scripts" / "validation" / "verify_mode_ii_h0_runtime_staging.py"

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
            "pre_solver_marker_present": False,
            "serial_solver_marker_absent": True,
            "failures": failures,
        }
        if output_summary:
            out_sum_path = Path(output_summary)
            out_sum_path.parent.mkdir(parents=True, exist_ok=True)
            out_sum_path.write_text(
                json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
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
    p_scratch = to_posix_path(res_scratch_root)
    p_evidence = to_posix_path(res_evidence_root)
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

    status_file = res_scratch_root / "MODE_II_H0_SERIAL_STATUS.json"
    staging_file = res_scratch_root / "MODE_II_H0_RUNTIME_STAGING_CHECK.json"
    smoke_marker = res_scratch_root / "MODE_II_H0_PRE_SOLVER_SMOKE.ok"
    serial_marker = res_scratch_root / "MODE_II_H0_SERIAL.ok"
    executables_file = res_scratch_root / "executables.txt"

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

    for search_dir in (res_stage_root, res_scratch_root, res_evidence_root):
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

    pre_solver_marker_present = smoke_marker.is_file()
    serial_solver_marker_absent = not serial_marker.is_file()

    summary = {
        "classification": "stage_f_mode_ii_h0_pre_solver_smoke_pass"
        if not failures
        else "stage_f_mode_ii_h0_pre_solver_smoke_fail",
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
        "pre_solver_marker_present": pre_solver_marker_present,
        "serial_solver_marker_absent": serial_solver_marker_absent,
        "failures": failures,
    }

    if evidence_output_dir is not None:
        evidence_out_path = Path(evidence_output_dir)
        evidence_out_path.mkdir(parents=True, exist_ok=True)

        (evidence_out_path / "stdout.log").write_text(proc.stdout, encoding="utf-8")
        (evidence_out_path / "stderr.log").write_text(proc.stderr, encoding="utf-8")

        for f_name, f_path in (
            ("MODE_II_H0_SERIAL_STATUS.json", status_file),
            ("MODE_II_H0_RUNTIME_MANIFEST.json", res_scratch_root / "MODE_II_H0_RUNTIME_MANIFEST.json"),
            ("MODE_II_H0_RUNTIME_STAGING_CHECK.json", staging_file),
            ("MODE_II_H0_LOGIN_MANIFEST.json", login_manifest),
            ("executables.txt", executables_file),
            ("MODE_II_H0_PRE_SOLVER_SMOKE.ok", smoke_marker),
        ):
            if f_path.is_file():
                shutil.copy(f_path, evidence_out_path / f_name)
            else:
                failures.append(f"Required smoke artifact missing: {f_name}")

        cmd_metadata = {
            "hostname": platform.node(),
            "timestamp_utc": started_at_utc,
            "project_revision": project_revision,
            "pbs_script_sha256": pbs_sha,
            "staging_verifier_sha256": verifier_sha,
            "requested_stage_root": req_stage_root,
            "resolved_stage_root": str(res_stage_root),
            "requested_scratch_root": req_scratch_root,
            "resolved_scratch_root": str(res_scratch_root),
            "requested_evidence_root": req_evidence_root,
            "resolved_evidence_root": str(res_evidence_root),
            "environment_variables": {
                "MODE_II_H0_PRE_SOLVER_ONLY": "1",
                "MODE_II_H0_ALLOW_LOCAL_NO_MODULES": allow_modules_val,
            },
            "module_bypass_allowed": allow_no_modules,
        }
        (evidence_out_path / "SMOKE_COMMAND.json").write_text(
            json.dumps(cmd_metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        (evidence_out_path / "SMOKE_SUMMARY.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        inv_data = {
            "odb_file_count": odb_file_count,
            "abaqus_lock_file_count": abaqus_lock_file_count,
            "solver_output_file_count": solver_output_file_count,
        }
        (evidence_out_path / "file_inventory.json").write_text(
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
            "MODE_II_H0_PRE_SOLVER_SMOKE.ok",
        ]

        file_hashes: dict[str, str] = {}
        for bf in bundle_files:
            bf_path = evidence_out_path / bf
            if bf_path.is_file():
                file_hashes[bf] = sha256_file(bf_path)

        initial_classification = (
            "stage_f_mode_ii_h0_pre_solver_smoke_evidence_complete"
            if not failures
            else "stage_f_mode_ii_h0_pre_solver_smoke_evidence_fail"
        )

        bundle_manifest = {
            "classification": initial_classification,
            "hostname": platform.node(),
            "started_at_utc": started_at_utc,
            "completed_at_utc": completed_at_utc,
            "project_revision": project_revision,
            "pbs_exit_code": proc.returncode,
            "module_environment_loaded": module_environment_loaded,
            "abaqus_invoked": abaqus_invoked,
            "odb_file_count": odb_file_count,
            "pre_solver_marker_present": pre_solver_marker_present,
            "serial_solver_marker_absent": serial_solver_marker_absent,
            "files": file_hashes,
            "failures": list(failures),
        }
        manifest_path = evidence_out_path / "EVIDENCE_BUNDLE_MANIFEST.json"
        manifest_path.write_text(
            json.dumps(bundle_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        # Call reusable evidence-bundle verifier
        bundle_rc, bundle_ver_result = verify_evidence_bundle(evidence_out_path)
        if bundle_rc != 0 or failures:
            for bf_err in bundle_ver_result.get("failures", []):
                if bf_err not in failures:
                    failures.append(bf_err)

            bundle_manifest["classification"] = "stage_f_mode_ii_h0_pre_solver_smoke_evidence_fail"
            bundle_manifest["failures"] = list(failures)
            manifest_path.write_text(
                json.dumps(bundle_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )

        summary["failures"] = list(failures)
        (evidence_out_path / "SMOKE_SUMMARY.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    final_classification = (
        "stage_f_mode_ii_h0_pre_solver_smoke_pass"
        if not failures
        else "stage_f_mode_ii_h0_pre_solver_smoke_fail"
    )
    summary["classification"] = final_classification

    if output_summary:
        out_sum_path = Path(output_summary)
        out_sum_path.parent.mkdir(parents=True, exist_ok=True)
        out_sum_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return (0 if final_classification == "stage_f_mode_ii_h0_pre_solver_smoke_pass" else 1), summary


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
    parser.add_argument("--verify-evidence-bundle", type=Path, default=None)

    args = parser.parse_args()

    if args.verify_evidence_bundle is not None:
        rc, result = verify_evidence_bundle(args.verify_evidence_bundle)
        print(json.dumps(result, indent=2, sort_keys=True))
        return rc

    rc, summary = run_pre_solver_smoke(
        project_root=args.project_root,
        stage_root=args.stage_root,
        scratch_root=args.scratch_root,
        evidence_root=args.evidence_root,
        project_revision=args.project_revision,
        allow_no_modules=args.allow_no_modules,
        output_summary=args.output_summary,
        evidence_output_dir=args.evidence_output_dir,
    )

    print(json.dumps(summary, indent=2, sort_keys=True))
    return rc


if __name__ == "__main__":
    sys.exit(main())
