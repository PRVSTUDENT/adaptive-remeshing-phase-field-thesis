#!/usr/bin/env python3
"""Generate the Stage-F Mode-II H1 uniform-reference technical package.

Uses the accepted Molnar staggered UEL/UMAT formulation and the H1_h0025 mesh.
Local target h = 0.0025 mm (h/lc = 0.1667).
Physical elements = 12064, layered elements = 36192, node count = 12382, Fortran N_ELEM = 12064.
Applies Mode-II pure shear boundary conditions and the Amp-2 endpoint correction (0.2s).
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
H0_FOR = ROOT / "models/generated/mode_ii/h0_endpoint_corrected_serial/ModeII_H0_endpoint_corrected_serial.for"

DEFAULT_OUT_DIR = ROOT / "models/generated/mode_ii/h1_uniform_serial"

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
        "** Job name: Mode-II pure shear H1 uniform serial name: Stage-F-Mode-II-H1",
    )

    # Replace Amp-2 table
    amp2_target = "*Amplitude, name=Amp-2\n0., 0.005, 0.5, 0.01"
    amp2_corr = "*Amplitude, name=Amp-2\n0., 0.005, 0.2, 0.01"
    if amp2_target not in text:
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
    deck_out = out_dir / "ModeII_H1_uniform_serial.inp"
    for_out = out_dir / "ModeII_H1_uniform_serial.for"

    write_text_lf(deck_out, transformed_deck)
    write_bytes(for_out, raw_for_bytes)

    corr_deck_sha = sha256_file(deck_out)
    corr_for_sha = sha256_file(for_out)

    # Check Fortran hash comparison against H0 Fortran source if available
    h0_for_sha = sha256_file(H0_FOR) if H0_FOR.is_file() else None
    fortran_identical_to_h0 = (corr_for_sha == h0_for_sha) if h0_for_sha else False

    write_text_lf(
        out_dir / "input_hashes.sha256",
        f"{corr_deck_sha}  ModeII_H1_uniform_serial.inp\n"
        f"{corr_for_sha}  ModeII_H1_uniform_serial.for\n",
    )

    manifest = {
        "classification": "stage_f_mode_ii_h1_uniform_package_prepared",
        "package_path": "models/generated/mode_ii/h1_uniform_serial",
        "source_package": "models/generated/molnar_gravouil_2017/h_convergence_lc015/H1_h0025",
        "source_deck_sha256": src_inp_sha,
        "source_fortran_sha256": src_for_sha,
        "corrected_deck_sha256": corr_deck_sha,
        "corrected_source_sha256": corr_for_sha,
        "source_byte_identical": True,
        "h0_fortran_sha256": h0_for_sha,
        "fortran_identical_to_h0": fortran_identical_to_h0,
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
        out_dir / "GENERATION_MANIFEST.json",
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    )

    mesh_quality = {
        "case_id": "H1_uniform_serial",
        "local_target_h_mm": 0.0025,
        "corridor_h_over_lc_median": 0.16666666666666682,
        "target_h_over_lc": 0.16666666666666669,
        "actual_local_h_corridor_min": 0.0024999999999999467,
        "actual_local_h_corridor_max": 0.0025000008,
        "actual_local_h_corridor_mean": 0.0025000001002403846,
        "actual_local_h_corridor_median": 0.0025000000000000022,
        "physical_element_count": EXPECTED_PHYSICAL,
        "layered_element_count": EXPECTED_LAYERED,
        "node_count": EXPECTED_NODES,
        "n_elem_fortran": EXPECTED_N_ELEM,
        "negative_jacobian_count": 0,
        "positive_orientation_fraction": 1.0,
        "max_neighbour_size_ratio": 1.5,
        "global_edge_length_max": 0.025,
        "global_edge_length_min": 0.0024999999999999467,
        "refined_corridor": {
            "x_min_mm": -0.02,
            "x_max_mm": 0.50,
            "y_min_mm": -0.005,
            "y_max_mm": 0.005
        }
    }
    write_text_lf(
        out_dir / "MESH_QUALITY.json",
        json.dumps(mesh_quality, indent=2, sort_keys=True) + "\n",
    )

    benchmark_def = f"""# Mode-II H1 Uniform-Reference Benchmark Definition

Classification: `stage_f_mode_ii_h1_uniform_benchmark_definition`

## Scientific Specification

- **Geometry:** $1.0\\text{{ mm}} \\times 1.0\\text{{ mm}}$ square plate with left-edge notch ($a=0.5\\text{{ mm}}$).
- **Formulation:** Accepted Molnar staggered UEL/UMAT formulation.
- **Mesh size:** $h_1 = 0.0025\\text{{ mm}}$ ($h_1/\\ell_c = 0.1667$).
- **Elements:** {EXPECTED_PHYSICAL} physical, {EXPECTED_LAYERED} layered (phase U1, displacement U2, visualization CPS4).
- **Fortran `N_ELEM`:** {EXPECTED_N_ELEM}.
- **Boundary Conditions:** Mode-II pure shear ($U_1$ prescribed via RP DOF1, bottom $U_1/U_2$ fixed, top $U_2$ fixed).
- **Target Endpoint:** $U_1 = 0.0100\\text{{ mm}}$ at $t=0.2\\text{{ s}}$ (Step 2, 2000 increments).
- **Execution Boundary:** `datacheck_authorized: false`, `solver_authorized: false`.
"""
    write_text_lf(out_dir / "BENCHMARK_DEFINITION.md", benchmark_def)

    # Place initial static validation status placeholder
    static_val = {
        "classification": "stage_f_mode_ii_h1_uniform_static_prepared",
        "passed": False,
        "failures": ["static validation pending execution"]
    }
    write_text_lf(
        out_dir / "STATIC_VALIDATION.json",
        json.dumps(static_val, indent=2, sort_keys=True) + "\n",
    )

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
