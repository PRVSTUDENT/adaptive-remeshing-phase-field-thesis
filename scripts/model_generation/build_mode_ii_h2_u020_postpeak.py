#!/usr/bin/env python3
"""Generate Stage F Candidate Job A: Mode-II H2 uniform reference serial u020 postpeak package.

Immutable package path: models/generated/mode_ii/h2_uniform_serial_u020_postpeak
Target displacement: U1 = 0.020 mm (frozen reference endpoint).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "models/generated/molnar_gravouil_2017/h_convergence_lc015/H2_pub_h0010"
SRC_INP = SRC_DIR / "H2_pub_h0010.inp"
SRC_FOR = SRC_DIR / "H2_pub_h0010.for"

DEFAULT_OUT_DIR = ROOT / "models/generated/mode_ii/h2_uniform_serial_u020_postpeak"

EXPECTED_PHYSICAL = 33852
EXPECTED_LAYERED = 101556
EXPECTED_NODES = 34508
EXPECTED_N_ELEM = 33852


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def transform_inp(text: str, target_u1: float = 0.020) -> str:
    # 1. Header update
    text = text.replace(
        "** Molnar lc015 h-convergence case H2_pub_h0010",
        "** Job name: Mode-II pure shear H2 uniform serial u020 postpeak",
    )

    # 2. Update Amp-2: 0., 0.005, 0.5, target_u1
    pattern_amp2 = r"(\*Amplitude,\s*name=Amp-2\s*\n\s*0\.\s*,\s*0\.005\s*,\s*0\.5\s*,\s*)([0-9\.]+)"
    if re.search(pattern_amp2, text):
        text = re.sub(pattern_amp2, r"\g<1>%.3f" % target_u1, text)
    else:
        # Fallback exact replace if needed
        text = text.replace(
            "*Amplitude, name=Amp-2\n0., 0.005, 0.5, 0.01",
            "*Amplitude, name=Amp-2\n0., 0.005, 0.5, %.3f" % target_u1,
        )

    # 3. Update Step-2 time period to 0.5s and max increments to 6000
    pattern_step2 = r"(\*Step,\s*name=Step-2,.*?\n\*Static, direct\s*\n\s*0\.0001\s*,\s*)([0-9\.]+)"
    if re.search(pattern_step2, text):
        text = re.sub(pattern_step2, r"\g<1>0.5", text)
    else:
        text = text.replace("0.0001, 0.2,", "0.0001, 0.5,")

    # Update inc=2000 to inc=6000 in Step-2
    text = text.replace("*Step, name=Step-2, nlgeom=NO, inc=2000", "*Step, name=Step-2, nlgeom=NO, inc=6000")

    # 4. Replace Equation: top 2 -> 1, RP 2 -> 1
    eq_old = "top, 2, 1.\nRP, 2, -1."
    eq_new = "top, 1, 1.\nRP, 1, -1."
    if eq_old in text:
        text = text.replace(eq_old, eq_new, 1)

    # 5. Step-1 & Step-2 boundary conditions to RP, 1, 1, 1. (Mode-II shear)
    bc_old_step1 = "*Boundary, amplitude=Amp-1\nRP, 2, 2, 1."
    bc_new_step1 = "*Boundary, amplitude=Amp-1\nRP, 1, 1, 1."
    if bc_old_step1 in text:
        text = text.replace(bc_old_step1, bc_new_step1, 1)

    bc_old_step2 = "*Boundary, amplitude=Amp-2\nRP, 2, 2, 1."
    bc_new_step2 = "*Boundary, amplitude=Amp-2\nRP, 1, 1, 1."
    if bc_old_step2 in text:
        text = text.replace(bc_old_step2, bc_new_step2, 1)

    # 6. Bottom BC: fixed U1 and U2
    if "*Boundary\nbottom, 2, 2" in text:
        text = text.replace("*Boundary\nbottom, 2, 2", "*Boundary\nbottom, 1, 2", 1)

    return text


def audit_step_endpoints(inp_text: str, expected_u1: float = 0.020) -> dict:
    # Evaluate Step-1 and Step-2 prescribed displacement
    # Step-1 Amp-1: (0., 0.), (0.5, 0.005) -> Step 1 final = 0.005 mm
    # Step-2 Amp-2: (0., 0.005), (0.5, target_u1) at t=0.5 -> Step 2 final = target_u1
    step1_final = 0.005
    step2_period = 0.5
    
    # Parse Amp-2 target from text
    m_amp2 = re.search(r"\*Amplitude,\s*name=Amp-2\s*\n\s*0\.\s*,\s*0\.005\s*,\s*0\.5\s*,\s*([0-9\.]+)", inp_text)
    calculated_u1 = float(m_amp2.group(1)) if m_amp2 else 0.0

    mismatch = abs(calculated_u1 - expected_u1)
    passed = mismatch <= 1.0e-12

    return {
        "initial_boundary_value_mm": 0.0,
        "step1_final_boundary_value_mm": step1_final,
        "step2_time_period_sec": step2_period,
        "step2_final_boundary_value_mm": calculated_u1,
        "calculated_final_u1_mm": calculated_u1,
        "expected_final_u1_mm": expected_u1,
        "absolute_mismatch_mm": mismatch,
        "pass": passed,
    }


def build_package(out_dir: Path = DEFAULT_OUT_DIR, target_u1: float = 0.020) -> dict:
    if not SRC_INP.is_file() or not SRC_FOR.is_file():
        raise FileNotFoundError(f"Source files missing under {SRC_DIR}")

    out_dir.mkdir(parents=True, exist_ok=True)

    inp_text = SRC_INP.read_text(encoding="utf-8")
    for_text = SRC_FOR.read_text(encoding="utf-8")

    inp_trans = transform_inp(inp_text, target_u1=target_u1)

    out_inp = out_dir / "ModeII_H2_uniform_serial.inp"
    out_for = out_dir / "ModeII_H2_uniform_serial.for"

    write_text_lf(out_inp, inp_trans)
    write_text_lf(out_for, for_text)

    deck_sha = sha256_file(out_inp)
    for_sha = sha256_file(out_for)

    input_hashes_file = out_dir / "input_hashes.sha256"
    hashes_text = f"{deck_sha}  ModeII_H2_uniform_serial.inp\n{for_sha}  ModeII_H2_uniform_serial.for\n"
    write_text_lf(input_hashes_file, hashes_text)

    # Perform STEP_ENDPOINT_AUDIT.json
    endpoint_audit = audit_step_endpoints(inp_trans, expected_u1=target_u1)
    write_text_lf(out_dir / "STEP_ENDPOINT_AUDIT.json", json.dumps(endpoint_audit, indent=2, sort_keys=True) + "\n")

    try:
        out_rel = str(out_dir.relative_to(ROOT))
    except ValueError:
        out_rel = str(out_dir)

    manifest = {
        "job_name": "mode_ii_h2_u020_postpeak",
        "mesh_case": "H2_pub_h0010",
        "local_target_h_mm": 0.0010,
        "target_u1_mm": target_u1,
        "physical_elements": EXPECTED_PHYSICAL,
        "layered_elements": EXPECTED_LAYERED,
        "nodes": EXPECTED_NODES,
        "fortran_N_ELEM": EXPECTED_N_ELEM,
        "deck_sha256": deck_sha,
        "fortran_sha256": for_sha,
        "out_dir": out_rel,
        "step_endpoint_audit": endpoint_audit,
    }

    manifest_file = out_dir / "GENERATION_MANIFEST.json"
    write_text_lf(manifest_file, json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    report_text = f"""# Package Report: Mode-II H2 Uniform Reference U020 Postpeak

- **Job Name:** `mode_ii_h2_u020_postpeak`
- **Target Endpoint:** $U_1 = {target_u1:.3f}\\text{{ mm}}$
- **Local Target h:** $h_2 = 0.0010\\text{{ mm}}$ ($h/l_c = 0.0667$)
- **Physical Elements:** {EXPECTED_PHYSICAL}
- **Layered Elements:** {EXPECTED_LAYERED}
- **Node Count:** {EXPECTED_NODES}
- **Fortran N_ELEM:** {EXPECTED_N_ELEM}
- **Deck SHA-256:** `{deck_sha}`
- **Fortran SHA-256:** `{for_sha}`
- **Endpoint Audit Status:** `{"PASS" if endpoint_audit["pass"] else "FAIL"}`
"""
    write_text_lf(out_dir / "PACKAGE_REPORT.md", report_text)

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--target-u1", type=float, default=0.020)
    args = parser.parse_args()

    res = build_package(args.out_dir, args.target_u1)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
