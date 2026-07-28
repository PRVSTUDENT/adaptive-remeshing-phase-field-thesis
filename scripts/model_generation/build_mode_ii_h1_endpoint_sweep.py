#!/usr/bin/env python3
"""Generate the four Stage-F Mode-II H1 endpoint sweep packages.

Variants:
  - u015: target U1 = 0.015 mm, Step 2 period = 0.4 s, max increments = 4000
  - u020: target U1 = 0.020 mm, Step 2 period = 0.6 s, max increments = 6000
  - u030: target U1 = 0.030 mm, Step 2 period = 1.0 s, max increments = 10000
  - u040: target U1 = 0.040 mm, Step 2 period = 1.4 s, max increments = 14000

All packages preserve the H1 uniform mesh (12,064 physical elements, 12,382 nodes)
and Fortran source byte-identically. Redundant tension BCs (topl, bottoml) are removed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "models/generated/molnar_gravouil_2017/h_convergence_lc015/H1_h0025"
SRC_INP = SRC_DIR / "H1_h0025.inp"
SRC_FOR = SRC_DIR / "H1_h0025.for"

DEFAULT_SWEEP_DIR = ROOT / "models/generated/mode_ii/h1_endpoint_sweep"

EXPECTED_SRC_INP_SHA256 = "90a305ef29714a6ee795e6b2fd9ef53856141f2ef66928665b5640422d12c35b"
EXPECTED_SRC_FOR_SHA256 = "745db8fcfb612895e0289f4533c90d204cc9b2ade3678a035614feeb308b5ead"

EXPECTED_PHYSICAL = 12064
EXPECTED_LAYERED = 36192
EXPECTED_NODES = 12382
EXPECTED_N_ELEM = 12064

VARIANTS = {
    "u015": {
        "job_name": "m2h1_u015",
        "target_u1_mm": 0.015,
        "step2_period_s": 0.4,
        "step2_max_inc": 4000,
        "description": "Mode-II H1 endpoint sweep U1 = 0.015 mm",
    },
    "u020": {
        "job_name": "m2h1_u020",
        "target_u1_mm": 0.020,
        "step2_period_s": 0.6,
        "step2_max_inc": 6000,
        "description": "Mode-II H1 endpoint sweep U1 = 0.020 mm",
    },
    "u030": {
        "job_name": "m2h1_u030",
        "target_u1_mm": 0.030,
        "step2_period_s": 1.0,
        "step2_max_inc": 10000,
        "description": "Mode-II H1 endpoint sweep U1 = 0.030 mm",
    },
    "u040": {
        "job_name": "m2h1_u040",
        "target_u1_mm": 0.040,
        "step2_period_s": 1.4,
        "step2_max_inc": 14000,
        "description": "Mode-II H1 endpoint sweep U1 = 0.040 mm",
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def transform_inp_variant(text: str, variant_key: str) -> str:
    vinfo = VARIANTS[variant_key]
    target_u1 = vinfo["target_u1_mm"]
    period_s = vinfo["step2_period_s"]
    max_inc = vinfo["step2_max_inc"]
    job_name = vinfo["job_name"]

    # Header update
    text = text.replace(
        "** Job name: Single Notched Tension Test name: Model-1",
        f"** Job name: Mode-II pure shear H1 endpoint sweep {variant_key} name: Stage-F-{job_name}",
    )

    # Replace Amp-2 table
    amp2_target = "*Amplitude, name=Amp-2\n0., 0.005, 0.5, 0.01"
    amp2_corr = f"*Amplitude, name=Amp-2\n0., 0.005, {period_s:.1f}, {target_u1:.3f}"
    if amp2_target not in text:
        amp2_target_alt = "*Amplitude, name=Amp-2\n             0.,           0.005,             0.5,            0.01"
        amp2_corr_alt = f"*Amplitude, name=Amp-2\n             0.,           0.005,             {period_s:.1f},            {target_u1:.3f}"
        if amp2_target_alt in text:
            text = text.replace(amp2_target_alt, amp2_corr_alt, 1)
        else:
            raise RuntimeError(f"Amp-2 table not found in deck for variant {variant_key}")
    else:
        text = text.replace(amp2_target, amp2_corr, 1)

    # Update Step 2 card (*Step, name=Step-2, ... \n ... \n 1e-04, 0.2, 1e-12, 1e-04)
    # Search for Step 2 time step line and max increment count
    step2_start = text.find("*Step, name=Step-2")
    if step2_start != -1:
        step2_text = text[step2_start:]
        # Replace increment count line if present (INC=2000 -> INC=max_inc)
        step2_text_mod = re.sub(r"INC=\d+", f"INC={max_inc}", step2_text, count=1, flags=re.IGNORECASE)
        # Replace step time line: 1e-04, 0.2, 1e-12, 1e-04 -> 1e-04, period_s, 1e-12, 1e-04
        step2_text_mod = re.sub(
            r"0\.0001,\s*0\.2,",
            f"0.0001, {period_s:.1f},",
            step2_text_mod,
            count=1,
        )
        text = text[:step2_start] + step2_text_mod

    # Replace Equation: top 2 -> 1, RP 2 -> 1
    eq_old = "top, 2, 1.\nRP, 2, -1."
    eq_new = "top, 1, 1.\nRP, 1, -1."
    if eq_old in text:
        text = text.replace(eq_old, eq_new, 1)

    # Replace Step-1 & Step-2 boundary conditions to RP, 1, 1, 1. (Mode-II shear)
    bc_old_step1 = "*Boundary, amplitude=Amp-1\nRP, 2, 2, 1."
    bc_new_step1 = "*Boundary, amplitude=Amp-1\nRP, 1, 1, 1."
    if bc_old_step1 in text:
        text = text.replace(bc_old_step1, bc_new_step1, 1)

    bc_old_step2 = "*Boundary, amplitude=Amp-2\nRP, 2, 2, 1."
    bc_new_step2 = "*Boundary, amplitude=Amp-2\nRP, 1, 1, 1."
    if bc_old_step2 in text:
        text = text.replace(bc_old_step2, bc_new_step2, 1)

    # Bottom BC: fixed U1 and U2
    if "*Boundary\nbottom, 2, 2" in text:
        text = text.replace("*Boundary\nbottom, 2, 2", "*Boundary\nbottom, 1, 2", 1)

    # Remove redundant tension BCs (bottoml, 1, 1 and topl, 1, 1)
    text = text.replace("*Boundary\nbottoml, 1, 1\n", "")
    text = text.replace("*Boundary\ntopl, 1, 1\n", "")

    return text


def build_variant_package(variant_key: str, out_dir: Path) -> dict:
    vinfo = VARIANTS[variant_key]
    job_name = vinfo["job_name"]
    target_u1 = vinfo["target_u1_mm"]
    period_s = vinfo["step2_period_s"]
    max_inc = vinfo["step2_max_inc"]

    src_inp_sha = sha256_file(SRC_INP)
    src_for_sha = sha256_file(SRC_FOR)

    raw_inp_text = SRC_INP.read_text(encoding="utf-8", errors="replace")
    raw_for_bytes = SRC_FOR.read_bytes()

    transformed_deck = transform_inp_variant(raw_inp_text, variant_key)

    v_dir = out_dir / variant_key
    v_dir.mkdir(parents=True, exist_ok=True)

    deck_out = v_dir / f"{job_name}.inp"
    for_out = v_dir / f"{job_name}.for"

    write_text_lf(deck_out, transformed_deck)
    write_bytes(for_out, raw_for_bytes)

    deck_sha = sha256_file(deck_out)
    for_sha = sha256_file(for_out)

    write_text_lf(
        v_dir / "input_hashes.sha256",
        f"{deck_sha}  {job_name}.inp\n" f"{for_sha}  {job_name}.for\n",
    )

    manifest = {
        "classification": "stage_f_mode_ii_h1_endpoint_sweep_package_prepared",
        "variant": variant_key,
        "job_name": job_name,
        "target_u1_mm": target_u1,
        "step1_u1_mm": 0.005,
        "step1_period_s": 0.5,
        "step2_period_s": period_s,
        "step2_max_increments": max_inc,
        "package_path": f"models/generated/mode_ii/h1_endpoint_sweep/{variant_key}",
        "deck_filename": f"{job_name}.inp",
        "fortran_filename": f"{job_name}.for",
        "deck_sha256": deck_sha,
        "fortran_sha256": for_sha,
        "source_deck_sha256": src_inp_sha,
        "source_fortran_sha256": src_for_sha,
        "physical_element_count": EXPECTED_PHYSICAL,
        "layered_element_count": EXPECTED_LAYERED,
        "node_count": EXPECTED_NODES,
        "n_elem_fortran": EXPECTED_N_ELEM,
    }

    write_text_lf(
        v_dir / "GENERATION_MANIFEST.json",
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    )

    pkg_report = f"""# Mode-II H1 Endpoint Sweep Package Report: {variant_key}

Classification: `stage_f_mode_ii_h1_endpoint_sweep_package_report`
Variant: `{variant_key}`
Job Name: `{job_name}`

## Technical Specification

- **Target Displacement:** $U_1 = {target_u1:.3f}\\text{{ mm}}$
- **Step 1:** Linear loading to $U_1 = 0.005\\text{{ mm}}$, period $0.5\\text{{ s}}$, 500 max increments
- **Step 2:** Shear propagation to $U_1 = {target_u1:.3f}\\text{{ mm}}$, period ${period_s:.1f}\\text{{ s}}$, {max_inc} max increments
- **Displacement Increment:** $\\Delta U_1 \\le 2.5 \\times 10^{{-6}}\\text{{ mm/inc}}$
- **Mesh:** $h_1 = 0.0025\\text{{ mm}}$, {EXPECTED_PHYSICAL} physical elements, {EXPECTED_LAYERED} layered elements, {EXPECTED_NODES} nodes
- **Fortran `N_ELEM`:** {EXPECTED_N_ELEM}
- **Deck SHA-256:** `{deck_sha}`
- **Fortran SHA-256:** `{for_sha}`
"""
    write_text_lf(v_dir / "PACKAGE_REPORT.md", pkg_report)

    return manifest


def build_all_packages(out_dir: Path) -> dict[str, dict]:
    results = {}
    for vkey in VARIANTS:
        results[vkey] = build_variant_package(vkey, out_dir)
    return results


def verify_determinism(out_dir: Path) -> bool:
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        dir1 = Path(tmp1)
        dir2 = Path(tmp2)

        res1 = build_all_packages(dir1)
        res2 = build_all_packages(dir2)

        for vkey in VARIANTS:
            d1 = res1[vkey]["deck_sha256"]
            d2 = res2[vkey]["deck_sha256"]
            f1 = res1[vkey]["fortran_sha256"]
            f2 = res2[vkey]["fortran_sha256"]
            if d1 != d2 or f1 != f2:
                print(f"Error: Non-deterministic build for variant {vkey}")
                return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_SWEEP_DIR)
    args = parser.parse_args()

    print("Verifying deterministic generation across two isolated builds...")
    if not verify_determinism(args.out_dir):
        print("Determinism check FAILED!")
        return 1
    print("Determinism check PASSED!")

    manifests = build_all_packages(args.out_dir)
    print("\nGenerated Packages Summary:")
    print(json.dumps(manifests, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
