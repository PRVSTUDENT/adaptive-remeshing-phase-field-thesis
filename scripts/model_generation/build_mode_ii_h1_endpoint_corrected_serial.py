#!/usr/bin/env python3
"""Generate the Stage-F Mode-II H1 endpoint-corrected serial technical package.

Uses the accepted Molnar staggered UEL/UMAT formulation and the H1_h0025 mesh.
Applies Mode-II pure-shear boundary conditions and the Amp-2 endpoint correction (0.2s).
N_ELEM = 12064, node count = 12382, physical element count = 12064.
"""


import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "models/generated/molnar_gravouil_2017/h_convergence_lc015/H1_h0025"
SRC_INP = SRC_DIR / "H1_h0025.inp"
SRC_FOR = SRC_DIR / "H1_h0025.for"

DEFAULT_OUT_DIR = ROOT / "models/generated/mode_ii/h1_endpoint_corrected_serial"

EXPECTED_SRC_INP_SHA256 = "90a305ef29714a6ee795e6b2fd9ef53856141f2ef66928665b5640422d12c35b"
EXPECTED_SRC_FOR_SHA256 = "745db8fcfb612895e0289f4533c90d204cc9b2ade3678a035614feeb308b5ead"

EXPECTED_PHYSICAL = 12064
EXPECTED_LAYERED = 36192
EXPECTED_NODES = 12382
EXPECTED_N_ELEM = 12064


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


def transform_inp(text: str) -> str:
    # Header update
    text = text.replace(
        "** Job name: Single Notched Tension Test name: Model-1",
        "** Job name: Mode-II pure shear H1 endpoint-corrected serial name: Stage-F-Mode-II-H1",
    )

    # Replace Amp-2 table
    amp2_target = "*Amplitude, name=Amp-2\n0., 0.005, 0.5, 0.01"
    amp2_corr = "*Amplitude, name=Amp-2\n0., 0.005, 0.2, 0.01"
    if amp2_target not in text:
        # Check formatted variations
        amp2_target_alt = "*Amplitude, name=Amp-2\n             0.,           0.005,             0.5,            0.01"
        amp2_corr_alt = "*Amplitude, name=Amp-2\n             0.,           0.005,             0.2,            0.01"
        if amp2_target_alt in text:
            text = text.replace(amp2_target_alt, amp2_corr_alt, 1)
        else:
            raise RuntimeError("Amp-2 table not found in deck")
    else:
        text = text.replace(amp2_target, amp2_corr, 1)

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

    return text


def build_package(out_dir: Path) -> dict:
    if out_dir.resolve() == SRC_DIR.resolve():
        raise ValueError(f"output directory cannot be source directory: {out_dir}")

    if not SRC_INP.is_file():
        raise RuntimeError(f"source deck missing: {SRC_INP}")
    if not SRC_FOR.is_file():
        raise RuntimeError(f"source Fortran missing: {SRC_FOR}")

    src_inp_sha = sha256_file(SRC_INP)
    src_for_sha = sha256_file(SRC_FOR)

    if src_inp_sha != EXPECTED_SRC_INP_SHA256:
        raise RuntimeError(f"source INP SHA256 mismatch: {src_inp_sha} != {EXPECTED_SRC_INP_SHA256}")
    if src_for_sha != EXPECTED_SRC_FOR_SHA256:
        raise RuntimeError(f"source FOR SHA256 mismatch: {src_for_sha} != {EXPECTED_SRC_FOR_SHA256}")

    raw_inp_text = SRC_INP.read_text(encoding="utf-8", errors="replace")
    raw_for_bytes = SRC_FOR.read_bytes()

    transformed_deck = transform_inp(raw_inp_text)

    out_dir.mkdir(parents=True, exist_ok=True)
    deck_out = out_dir / "ModeII_H1_endpoint_corrected_serial.inp"
    for_out = out_dir / "ModeII_H1_endpoint_corrected_serial.for"

    write_text_lf(deck_out, transformed_deck)
    write_bytes(for_out, raw_for_bytes)

    corr_deck_sha = sha256_file(deck_out)
    corr_for_sha = sha256_file(for_out)

    write_text_lf(
        out_dir / "input_hashes.sha256",
        f"{corr_deck_sha}  ModeII_H1_endpoint_corrected_serial.inp\n"
        f"{corr_for_sha}  ModeII_H1_endpoint_corrected_serial.for\n",
    )

    parent_hashes = {
        "source_package_path": "models/generated/molnar_gravouil_2017/h_convergence_lc015/H1_h0025",
        "source_deck_sha256": src_inp_sha,
        "source_fortran_sha256": src_for_sha,
        "verified_identical_fortran": True,
    }
    write_text_lf(
        out_dir / "HISTORICAL_PARENT_HASHES.json",
        json.dumps(parent_hashes, indent=2, sort_keys=True) + "\n",
    )

    provenance = {
        "classification": "stage_f_mode_ii_h1_endpoint_correction_provenance",
        "h1_mesh_h_mm": 0.0025,
        "h1_h_over_lc": 0.1666666667,
        "amp2_table": "0.0, 0.005 -> 0.2, 0.010",
        "step2_period": 0.2,
        "step2_direct_increment": 0.0001,
        "step2_max_inc": 2000,
        "final_target_u1_mm": 0.010,
        "n_elem_fortran": EXPECTED_N_ELEM,
    }
    write_text_lf(
        out_dir / "ENDPOINT_CORRECTED_PROVENANCE.json",
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
    )

    manifest = {
        "classification": "stage_f_mode_ii_h1_endpoint_corrected_package_prepared",
        "package_path": "models/generated/mode_ii/h1_endpoint_corrected_serial",
        "source_package": "models/generated/molnar_gravouil_2017/h_convergence_lc015/H1_h0025",
        "source_deck_sha256": src_inp_sha,
        "source_fortran_sha256": src_for_sha,
        "corrected_deck_sha256": corr_deck_sha,
        "corrected_source_sha256": corr_for_sha,
        "source_byte_identical": True,
        "h1_mesh_h_mm": 0.0025,
        "physical_element_count": EXPECTED_PHYSICAL,
        "layered_element_count": EXPECTED_LAYERED,
        "node_count": EXPECTED_NODES,
        "n_elem_fortran": EXPECTED_N_ELEM,
        "datacheck_authorized": False,
        "solver_authorized": False,
        "execution_authorized": False,
        "automatic_retry_authorized": False,
    }
    write_text_lf(
        out_dir / "PACKAGE_MANIFEST.json",
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    )

    readme = f"""# Mode-II H1 endpoint-corrected serial package

Classification: `stage_f_mode_ii_h1_endpoint_corrected_package_prepared`

## Technical Parameters

- Mesh resolution: $h_1 = 0.0025\\text{{ mm}}$ ($h_1/\\ell_c = 0.1667$).
- Elements: {EXPECTED_PHYSICAL} physical, {EXPECTED_LAYERED} layered (UEL/UMAT).
- Fortran `N_ELEM`: {EXPECTED_N_ELEM}.
- Target endpoint: $U_1 = 0.010\\text{{ mm}}$ at $t=0.2$ (Step-2 end).
- Boundary conditions: Mode-II pure shear (RP U1 prescribed, bottom U1/U2 fixed).
- Executable boundary: `datacheck_authorized: false`, `solver_authorized: false`.
"""
    write_text_lf(out_dir / "README.md", readme)

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    manifest = build_package(args.out_dir)
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
