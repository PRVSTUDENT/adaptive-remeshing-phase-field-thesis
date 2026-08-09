#!/usr/bin/env python3
"""Static validator for Stage-F Mode-II H0 endpoint-corrected serial package."""


import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "configs/studies/mode_ii_molnar_shear_endpoint_corrected.yaml"
PACKAGE_DIR = ROOT / "models/generated/mode_ii/h0_endpoint_corrected_serial"
HISTORICAL_DIR = ROOT / "models/generated/mode_ii/h0_serial"

EXPECTED_HISTORICAL_DECK_SHA256 = "32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b"
EXPECTED_HISTORICAL_FORTRAN_SHA256 = "5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c"
EXPECTED_ENDPOINT_AUDIT_REVISION = "49d7d4f1a941a09fbfd3aca147fd612a0a9a6a4c"

EXPECTED_N_ELEM = 3930
EXPECTED_PHYSICAL = 3930
EXPECTED_LAYERED = 11790
EXPECTED_NODES = 3998


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_simple_yaml(text: str) -> dict:
    result = {}
    current_key = None
    stack = [result]
    indent_levels = [-1]

    for raw_line in text.splitlines():
        line = raw_line.split("#")[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        content = line.strip()

        while len(indent_levels) > 1 and indent <= indent_levels[-1]:
            indent_levels.pop()
            stack.pop()

        if ":" in content:
            k, v = content.split(":", 1)
            k = k.strip()
            v = v.strip()

            if v:
                val = v.strip('"\'')
                if val.lower() == "true":
                    val = True
                elif val.lower() == "false":
                    val = False
                else:
                    try:
                        val = int(val)
                    except ValueError:
                        try:
                            val = float(val)
                        except ValueError:
                            pass
                stack[-1][k] = val
            else:
                new_dict = {}
                stack[-1][k] = new_dict
                stack.append(new_dict)
                indent_levels.append(indent)

    return result


def validate(package_dir: Path = PACKAGE_DIR, config_path: Path = CONFIG_PATH) -> dict:
    failures = []
    checks = []

    def check(condition: bool, msg: str) -> None:
        checks.append(msg)
        if not condition:
            failures.append(msg)

    # 1. Paths and Config
    check(config_path.is_file(), f"corrected config file exists ({config_path})")
    cfg = {}
    if config_path.is_file():
        with config_path.open("r", encoding="utf-8") as f:
            text = f.read()
            if yaml is not None:
                cfg = yaml.safe_load(text)
            else:
                cfg = parse_simple_yaml(text)
    if config_path.is_file():
        with config_path.open("r", encoding="utf-8") as f:
            text = f.read()
            if yaml is not None:
                cfg = yaml.safe_load(text)
            else:
                cfg = parse_simple_yaml(text)

    check(
        cfg.get("status") == "stage_f_mode_ii_h0_endpoint_corrected_prepared",
        "config status is stage_f_mode_ii_h0_endpoint_corrected_prepared",
    )
    check(
        cfg.get("provenance", {}).get("endpoint_audit_revision") == EXPECTED_ENDPOINT_AUDIT_REVISION,
        f"config provenance endpoint_audit_revision matches ({EXPECTED_ENDPOINT_AUDIT_REVISION})",
    )

    loading_cfg = cfg.get("loading", {})
    check(loading_cfg.get("step2_amplitude_endpoint_time") == 0.2, "config step2_amplitude_endpoint_time is 0.2")
    check(loading_cfg.get("step2_time") == 0.2, "config step2_time is 0.2")
    check(loading_cfg.get("step2_final_displacement_mm") == 0.010, "config step2_final_displacement_mm is 0.010")

    exec_cfg = cfg.get("execution_boundary", {})
    check(exec_cfg.get("datacheck_authorized") is False, "config datacheck_authorized is false")
    check(exec_cfg.get("solver_authorized") is False, "config solver_authorized is false")
    check(exec_cfg.get("execution_authorized") is False, "config execution_authorized is false")

    # 2. Package Files Existence
    check(package_dir.is_dir(), f"package directory exists ({package_dir})")
    deck_path = package_dir / "ModeII_H0_endpoint_corrected_serial.inp"
    for_path = package_dir / "ModeII_H0_endpoint_corrected_serial.for"
    manifest_path = package_dir / "PACKAGE_MANIFEST.json"
    hashes_path = package_dir / "input_hashes.sha256"
    hist_hashes_path = package_dir / "HISTORICAL_PARENT_HASHES.json"
    prov_path = package_dir / "ENDPOINT_CORRECTION_PROVENANCE.json"

    for p in [deck_path, for_path, manifest_path, hashes_path, hist_hashes_path, prov_path]:
        check(p.is_file(), f"expected package file exists ({p.name})")

    # 3. Hashes Verification
    if hashes_path.is_file() and deck_path.is_file() and for_path.is_file():
        hashes_text = hashes_path.read_text(encoding="utf-8")
        calc_deck_sha = sha256_file(deck_path)
        calc_for_sha = sha256_file(for_path)
        check(f"{calc_deck_sha}  ModeII_H0_endpoint_corrected_serial.inp" in hashes_text, "hashes manifest matches deck SHA256")
        check(f"{calc_for_sha}  ModeII_H0_endpoint_corrected_serial.for" in hashes_text, "hashes manifest matches source SHA256")

    # 4. Historical Parent Verification
    hist_deck_path = HISTORICAL_DIR / "ModeII_H0_serial.inp"
    hist_for_path = HISTORICAL_DIR / "ModeII_H0_serial.for"
    check(hist_deck_path.is_file(), "historical deck exists")
    check(hist_for_path.is_file(), "historical source exists")
    if hist_deck_path.is_file() and hist_for_path.is_file():
        hist_deck_sha = sha256_file(hist_deck_path)
        hist_for_sha = sha256_file(hist_for_path)
        check(hist_deck_sha == EXPECTED_HISTORICAL_DECK_SHA256, "historical deck hash has not changed")
        check(hist_for_sha == EXPECTED_HISTORICAL_FORTRAN_SHA256, "historical source hash has not changed")

        # Source byte identity
        if for_path.is_file():
            corr_for_bytes = for_path.read_bytes()
            hist_for_bytes = hist_for_path.read_bytes()
            check(corr_for_bytes == hist_for_bytes, "corrected source is 100% byte-identical to historical source")

    # 5. Deck Content Verification
    if deck_path.is_file() and hist_deck_path.is_file():
        deck_text = deck_path.read_text(encoding="utf-8")
        hist_text = hist_deck_path.read_text(encoding="utf-8")

        # Scope of changes: exactly 1 line changed
        deck_lines = deck_text.splitlines()
        hist_lines = hist_text.splitlines()
        check(len(deck_lines) == len(hist_lines), "deck line count equals historical deck line count")
        diffs = [(i + 1, h, c) for i, (h, c) in enumerate(zip(hist_lines, deck_lines)) if h != c]
        check(len(diffs) == 1, f"corrected deck differs from historical deck on exactly 1 line (found {len(diffs)})")

        if len(diffs) == 1:
            line_num, old_line, new_line = diffs[0]
            check("0.5,            0.01" in old_line, "diff old line is historical Amp-2 endpoint (0.5, 0.01)")
            check("0.2,            0.01" in new_line, "diff new line is corrected Amp-2 endpoint (0.2, 0.01)")

        # Amp-2 schedule checks
        check(
            "*Amplitude, name=Amp-2\n             0.,           0.005,             0.2,            0.01" in deck_text,
            "Amp-2 starts at 0.005 at t=0.0 and reaches 0.010 at t=0.2",
        )

        # Step-2 parameters
        check("*Step, name=Step-2, nlgeom=NO, inc=2000" in deck_text, "Step-2 max inc is 2000")
        check("0.0001, 0.2," in deck_text, "Step-2 period is 0.2 and direct increment is 0.0001")

        # Step-1 checks
        check("*Step, name=Step-1, nlgeom=NO, inc=500" in deck_text, "Step-1 remains unchanged (max inc 500)")
        check("0.001, 0.5," in deck_text, "Step-1 period remains 0.5 (direct inc 0.001)")

        # Pure shear BCs checks
        check("top, 1, 1." in deck_text, "pure-shear top horizontal equation present (top, 1, 1.)")
        check("RP, 1, 1, 1." in deck_text, "RP U1 prescribed load present (RP, 1, 1, 1.)")
        check("top, 2, 2" in deck_text, "top vertical restraint present (top, 2, 2)")
        check("bottom, 1, 2" in deck_text, "bottom fully fixed present (bottom, 1, 2)")
        check("RP, 2, 2" not in deck_text, "no residual Mode-I RP U2 loading present")

        # Geometry & Mesh constants
        check("N_ELEM=3930" in for_path.read_text(encoding="utf-8"), "Fortran N_ELEM remains 3930")
        check("elset=umatelem" in deck_text, "umatelem set present")

    # 6. Manifest Verification
    if manifest_path.is_file():
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
        check(manifest.get("datacheck_authorized") is False, "manifest datacheck_authorized is false")
        check(manifest.get("solver_authorized") is False, "manifest solver_authorized is false")
        check(manifest.get("execution_authorized") is False, "manifest execution_authorized is false")
        check(manifest.get("automatic_retry_authorized") is False, "manifest automatic_retry_authorized is false")
        check(manifest.get("source_byte_identical_to_historical") is True, "manifest source_byte_identical_to_historical is true")
        check(manifest.get("final_target_u1_mm") == 0.010, "manifest final_target_u1_mm is 0.010")

    result = {
        "classification": "stage_f_mode_ii_h0_endpoint_corrected_static_pass" if not failures else "stage_f_mode_ii_h0_endpoint_corrected_static_fail",
        "passed": len(failures) == 0,
        "total_checks": len(checks),
        "failures": failures,
        "package_dir": str(package_dir),
        "endpoint_audit_revision": EXPECTED_ENDPOINT_AUDIT_REVISION,
    }

    validation_json = package_dir / "STATIC_VALIDATION.json"
    validation_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, default=PACKAGE_DIR)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    args = parser.parse_args()

    result = validate(args.package_dir, args.config)
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
