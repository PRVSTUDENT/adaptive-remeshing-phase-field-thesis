#!/usr/bin/env python3
"""Run pre-solver smoke qualification for Stage-F Mode-II H0 endpoint-corrected serial lane."""


import argparse
import datetime
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = ROOT / "models/generated/mode_ii/h0_endpoint_corrected_serial"
DEFAULT_OUT_DIR = ROOT / "runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/smoke_evidence/local"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_evidence_bundle(bundle_dir: Path) -> tuple[int, dict]:
    failures: list[str] = []
    bundle_dir = Path(bundle_dir)

    if not bundle_dir.exists() or not bundle_dir.is_dir():
        return 1, {
            "classification": "stage_f_mode_ii_h0_endpoint_corrected_smoke_evidence_fail",
            "bundle_dir": str(bundle_dir),
            "failures": [f"Evidence bundle directory does not exist: {bundle_dir}"],
        }

    manifest_file = bundle_dir / "EVIDENCE_BUNDLE_MANIFEST.json"
    manifest_data: dict = {}
    if not manifest_file.is_file() or manifest_file.stat().st_size == 0:
        failures.append("EVIDENCE_BUNDLE_MANIFEST.json missing or empty")
    else:
        try:
            manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        except Exception as err:
            failures.append(f"Failed to parse manifest: {err}")

    if manifest_data.get("classification") != "stage_f_mode_ii_h0_endpoint_corrected_smoke_evidence_complete":
        failures.append(f"Manifest classification invalid: {manifest_data.get('classification')}")

    files_map = manifest_data.get("files", {})
    for rel_path, expected_hash in files_map.items():
        fp = bundle_dir / rel_path
        if not fp.is_file():
            failures.append(f"Bundle file missing: {rel_path}")
        else:
            actual_hash = sha256_file(fp)
            if actual_hash != expected_hash:
                failures.append(f"Hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")

    passed = len(failures) == 0
    classification = (
        "stage_f_mode_ii_h0_endpoint_corrected_smoke_evidence_complete"
        if passed
        else "stage_f_mode_ii_h0_endpoint_corrected_smoke_evidence_fail"
    )

    return (0 if passed else 1), {
        "classification": classification,
        "bundle_dir": str(bundle_dir),
        "failures": failures,
    }


def run_smoke(output_dir: Path) -> tuple[int, dict]:
    failures: list[str] = []
    checks: list[str] = []

    def check(cond: bool, msg: str) -> None:
        checks.append(msg)
        if not cond:
            failures.append(msg)

    # Package existence
    check(PACKAGE_DIR.is_dir(), f"package dir exists ({PACKAGE_DIR})")
    deck_path = PACKAGE_DIR / "ModeII_H0_endpoint_corrected_serial.inp"
    for_path = PACKAGE_DIR / "ModeII_H0_endpoint_corrected_serial.for"
    manifest_path = PACKAGE_DIR / "PACKAGE_MANIFEST.json"

    check(deck_path.is_file(), "deck file exists")
    check(for_path.is_file(), "Fortran source file exists")
    check(manifest_path.is_file(), "package manifest exists")

    # Corrected endpoint semantics check
    if deck_path.is_file():
        text = deck_path.read_text(encoding="utf-8")
        check("*Amplitude, name=Amp-2\n             0.,           0.005,             0.2,            0.01" in text, "deck contains Amp-2 endpoint time 0.2")
        check("0.0001, 0.2," in text, "deck contains Step-2 period 0.2")

    # Source identity check
    hist_for = ROOT / "models/generated/mode_ii/h0_serial/ModeII_H0_serial.for"
    if for_path.is_file() and hist_for.is_file():
        check(for_path.read_bytes() == hist_for.read_bytes(), "source Fortran is byte-identical to historical source")

    # No solver execution or prohibited files in package
    odb_files = list(PACKAGE_DIR.glob("*.odb"))
    check(len(odb_files) == 0, f"no ODB files present in package (found {len(odb_files)})")
    check(not (PACKAGE_DIR / "SOLVER_SUCCESS").exists(), "no SOLVER_SUCCESS marker in package")

    # Required scripts existence
    req_scripts = [
        ROOT / "scripts/model_generation/build_mode_ii_h0_endpoint_corrected_serial.py",
        ROOT / "scripts/validation/validate_mode_ii_h0_endpoint_corrected_static.py",
        ROOT / "scripts/validation/validate_mode_ii_h0_endpoint_corrected_results.py",
    ]
    for s in req_scripts:
        check(s.is_file(), f"required script exists ({s.name})")

    # Get git revision if possible
    rev = "unknown"
    try:
        rev = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        pass

    passed = len(failures) == 0

    output_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "classification": "stage_f_mode_ii_h0_endpoint_corrected_pre_solver_smoke_pass" if passed else "stage_f_mode_ii_h0_endpoint_corrected_pre_solver_smoke_fail",
        "passed": passed,
        "revision": rev,
        "package_dir": str(PACKAGE_DIR),
        "total_checks": len(checks),
        "failures": failures,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    # Generate evidence files
    summary_path = output_dir / "SMOKE_SUMMARY.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    files_map = {
        "SMOKE_SUMMARY.json": sha256_file(summary_path),
    }

    evidence_manifest = {
        "classification": "stage_f_mode_ii_h0_endpoint_corrected_smoke_evidence_complete" if passed else "stage_f_mode_ii_h0_endpoint_corrected_smoke_evidence_fail",
        "failures": failures,
        "files": files_map,
        "output_dir": str(output_dir),
    }

    manifest_file = output_dir / "EVIDENCE_BUNDLE_MANIFEST.json"
    manifest_file.write_text(json.dumps(evidence_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return (0 if passed else 1), summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--verify-evidence-bundle", type=Path, default=None)
    args = parser.parse_args()

    if args.verify_evidence_bundle:
        rc, res = verify_evidence_bundle(args.verify_evidence_bundle)
        print(json.dumps(res, indent=2))
        return rc

    rc, res = run_smoke(args.output_dir)
    print(json.dumps(res, indent=2))
    return rc


if __name__ == "__main__":
    sys.exit(main())
