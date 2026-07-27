#!/usr/bin/env python3
"""Generate the Stage-F Mode-II H0 endpoint-corrected serial technical package.

Uses the frozen historical package (models/generated/mode_ii/h0_serial/) as input.
Changes strictly the Amp-2 endpoint time from 0.5 to 0.2.
Fortran source remains 100% byte-identical to historical source.
Fail-closed checks ensure deterministic, verified output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HISTORICAL_DIR = ROOT / "models/generated/mode_ii/h0_serial"
HISTORICAL_DECK = HISTORICAL_DIR / "ModeII_H0_serial.inp"
HISTORICAL_FORTRAN = HISTORICAL_DIR / "ModeII_H0_serial.for"

DEFAULT_OUT_DIR = ROOT / "models/generated/mode_ii/h0_endpoint_corrected_serial"

EXPECTED_HISTORICAL_DECK_SHA256 = "32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b"
EXPECTED_HISTORICAL_FORTRAN_SHA256 = "5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c"

ENDPOINT_AUDIT_REVISION = "49d7d4f1a941a09fbfd3aca147fd612a0a9a6a4c"

EXPECTED_N_ELEM = 3930
EXPECTED_PHYSICAL = 3930
EXPECTED_LAYERED = 11790
EXPECTED_NODES = 3998


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


def build_package(out_dir: Path) -> dict:
    # Fail-closed check: reject output path equal to historical path
    if out_dir.resolve() == HISTORICAL_DIR.resolve():
        raise ValueError(f"output directory cannot be historical directory: {out_dir}")

    # Fail-closed check: verify historical inputs exist and match recorded hashes
    if not HISTORICAL_DECK.is_file():
        raise RuntimeError(f"historical deck missing: {HISTORICAL_DECK}")
    if not HISTORICAL_FORTRAN.is_file():
        raise RuntimeError(f"historical Fortran missing: {HISTORICAL_FORTRAN}")

    hist_deck_sha = sha256_file(HISTORICAL_DECK)
    hist_for_sha = sha256_file(HISTORICAL_FORTRAN)

    if hist_deck_sha != EXPECTED_HISTORICAL_DECK_SHA256:
        raise RuntimeError(
            f"historical deck SHA256 mismatch: {hist_deck_sha} != {EXPECTED_HISTORICAL_DECK_SHA256}"
        )
    if hist_for_sha != EXPECTED_HISTORICAL_FORTRAN_SHA256:
        raise RuntimeError(
            f"historical Fortran SHA256 mismatch: {hist_for_sha} != {EXPECTED_HISTORICAL_FORTRAN_SHA256}"
        )

    hist_deck_text = HISTORICAL_DECK.read_text(encoding="utf-8", errors="replace")
    hist_for_bytes = HISTORICAL_FORTRAN.read_bytes()

    # Fail-closed checks on deck content
    amp2_target = "*Amplitude, name=Amp-2\n             0.,           0.005,             0.5,            0.01"
    amp2_count = hist_deck_text.count("*Amplitude, name=Amp-2")
    if amp2_count == 0:
        raise RuntimeError("expected historical Amp-2 block absent")
    if amp2_count > 1:
        raise RuntimeError(f"more than one matching Amp-2 block exists ({amp2_count})")
    if amp2_target not in hist_deck_text:
        raise RuntimeError("historical Amp-2 content does not match expected table")

    if "*Step, name=Step-2, nlgeom=NO, inc=2000" not in hist_deck_text:
        raise RuntimeError("Step-2 maximum increments is not 2000")
    if "0.0001, 0.2," not in hist_deck_text:
        raise RuntimeError("Step-2 direct increment (0.0001) or period (0.2) not found")

    if "RP, 1, 1, 1." not in hist_deck_text:
        raise RuntimeError("pure-shear boundary conditions (RP U1) absent")

    # Perform the exact single scientific change
    corrected_amp2 = "*Amplitude, name=Amp-2\n             0.,           0.005,             0.2,            0.01"
    corrected_deck_text = hist_deck_text.replace(amp2_target, corrected_amp2, 1)

    # Verify deck difference scope
    hist_lines = hist_deck_text.splitlines()
    corr_lines = corrected_deck_text.splitlines()
    diffs = [(i + 1, h, c) for i, (h, c) in enumerate(zip(hist_lines, corr_lines)) if h != c]
    if len(diffs) != 1:
        raise RuntimeError(f"expected exactly 1 modified line in deck, found {len(diffs)}: {diffs}")

    out_dir.mkdir(parents=True, exist_ok=True)

    deck_out_path = out_dir / "ModeII_H0_endpoint_corrected_serial.inp"
    for_out_path = out_dir / "ModeII_H0_endpoint_corrected_serial.for"

    write_text_lf(deck_out_path, corrected_deck_text)
    write_bytes(for_out_path, hist_for_bytes)

    # Fail-closed check: Fortran byte identity
    corr_for_sha = sha256_file(for_out_path)
    if corr_for_sha != hist_for_sha:
        raise RuntimeError("generated Fortran source is not byte-identical to historical source")

    corr_deck_sha = sha256_file(deck_out_path)

    # Write input_hashes.sha256
    hashes_path = out_dir / "input_hashes.sha256"
    write_text_lf(
        hashes_path,
        f"{corr_deck_sha}  ModeII_H0_endpoint_corrected_serial.inp\n"
        f"{corr_for_sha}  ModeII_H0_endpoint_corrected_serial.for\n",
    )

    # Write HISTORICAL_PARENT_HASHES.json
    hist_parent_data = {
        "historical_package_path": "models/generated/mode_ii/h0_serial",
        "historical_deck_filename": "ModeII_H0_serial.inp",
        "historical_deck_sha256": hist_deck_sha,
        "historical_fortran_filename": "ModeII_H0_serial.for",
        "historical_fortran_sha256": hist_for_sha,
        "verified_identical_fortran": True,
    }
    write_text_lf(
        out_dir / "HISTORICAL_PARENT_HASHES.json",
        json.dumps(hist_parent_data, indent=2, sort_keys=True) + "\n",
    )

    # Write ENDPOINT_CORRECTION_PROVENANCE.json
    provenance_data = {
        "classification": "stage_f_mode_ii_h0_endpoint_correction_provenance",
        "endpoint_audit_revision": ENDPOINT_AUDIT_REVISION,
        "historical_failed_job_id": "1378942.mmaster02",
        "historical_failed_submission_revision": "69d4d0a6ade66f4c0a1ea47020eb6e8916c11abd",
        "correction_kind": "amplitude_endpoint_time_only",
        "amp2_table_before": "0.0, 0.005 -> 0.5, 0.010",
        "amp2_table_after": "0.0, 0.005 -> 0.2, 0.010",
        "step2_period": 0.2,
        "step2_direct_increment": 0.0001,
        "step2_max_inc": 2000,
        "final_target_u1_mm": 0.010,
        "rate_independent_formulation_verified": True,
    }
    write_text_lf(
        out_dir / "ENDPOINT_CORRECTION_PROVENANCE.json",
        json.dumps(provenance_data, indent=2, sort_keys=True) + "\n",
    )

    # Write PACKAGE_MANIFEST.json
    manifest = {
        "classification": "stage_f_mode_ii_h0_endpoint_corrected_package_prepared",
        "package_path": "models/generated/mode_ii/h0_endpoint_corrected_serial",
        "endpoint_audit_revision": ENDPOINT_AUDIT_REVISION,
        "historical_parent_package": "models/generated/mode_ii/h0_serial",
        "historical_parent_deck_sha256": hist_deck_sha,
        "historical_parent_source_sha256": hist_for_sha,
        "corrected_deck_sha256": corr_deck_sha,
        "corrected_source_sha256": corr_for_sha,
        "source_byte_identical_to_historical": True,
        "deck_change_scope": "amplitude_endpoint_time_only",
        "expected_deck_difference_count": 1,
        "geometry_unchanged": True,
        "mesh_unchanged": True,
        "element_counts_unchanged": True,
        "node_count_unchanged": True,
        "n_elem_fortran_unchanged": True,
        "formulation_unchanged": True,
        "material_parameters_unchanged": True,
        "boundary_conditions_unchanged": True,
        "output_requests_unchanged": True,
        "final_target_u1_mm": 0.010,
        "step2_period": 0.2,
        "step2_direct_increment": 0.0001,
        "step2_max_inc": 2000,
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

    # Write README.md
    readme = f"""# Mode-II H0 endpoint-corrected serial package

Classification: `stage_f_mode_ii_h0_endpoint_corrected_package_prepared`
Endpoint Audit Revision: `{ENDPOINT_AUDIT_REVISION}`

## Scope

- Geometry/mesh: accepted Mode-I H0 supplementary single-notch mesh (unchanged).
- Formulation: accepted Molnar staggered UEL/UMAT (`N_ELEM=3930`, byte-identical Fortran).
- Correction: Amp-2 endpoint time changed from 0.5 to 0.2 (`0.0, 0.005 -> 0.2, 0.010`).
- Target endpoint: $U_1 = 0.010\\text{{ mm}}$ at Step-2 end ($t=0.2$, 2000 increments).
- Executable boundary: `datacheck_authorized: false`, `solver_authorized: false`.

## Files

- `ModeII_H0_endpoint_corrected_serial.inp`
- `ModeII_H0_endpoint_corrected_serial.for`
- `PACKAGE_MANIFEST.json`
- `input_hashes.sha256`
- `HISTORICAL_PARENT_HASHES.json`
- `ENDPOINT_CORRECTION_PROVENANCE.json`
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
