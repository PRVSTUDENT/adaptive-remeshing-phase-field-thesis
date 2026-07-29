#!/usr/bin/env python3
"""Generate Stage F Candidate Job B: Pandey-Kumar coarse auxiliary-continuum MISESERI pre-analysis.

Uses the H0 coarse mesh (3,930 CPS4 continuum elements) with standard Abaqus linear elastic material.
Outputs von Mises stress discretization recovery error indicators (MISESERI, MISESAVG) at load level U1 = 0.001 mm.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_INP = ROOT / "models/generated/mode_ii/h0_endpoint_corrected_serial/ModeII_H0_endpoint_corrected_serial.inp"
DEFAULT_OUT_DIR = ROOT / "models/generated/mode_ii/miseseri_preanalysis"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def build_miseseri_deck(src_inp_text: str, target_u1: float = 0.001) -> str:
    lines = src_inp_text.splitlines()
    new_lines = []

    # Strip UEL definitions and keep only the standard CPS4 element block (3930 elements)
    skipping_uel = False
    for line in lines:
        if line.startswith("** Job name:"):
            new_lines.append("** Job name: Mode-II Pandey-Kumar MISESERI pre-analysis name: Stage-F-MISESERI-Preanalysis")
            continue
        if line.startswith("*User element"):
            skipping_uel = True
            continue
        if line.startswith("*Element, type=U1") or line.startswith("*Element, type=U2"):
            skipping_uel = True
            continue
        if line.startswith("*Element, TYPE=CPS4") or line.startswith("*Element, type=CPS4"):
            skipping_uel = False

        if skipping_uel:
            continue

        if line.startswith("*User Material"):
            # Replace UMAT dummy material with standard elastic material definition
            new_lines.append("*Elastic")
            new_lines.append(" 210., 0.3")
            continue

        if line.startswith(" 1e-11, 0.3"):
            continue

        if line.startswith("*Output, field"):
            new_lines.append("*Output, field, frequency=1")
            new_lines.append("*Node Output")
            new_lines.append(" U, RF")
            new_lines.append("*Element Output, elset=umatelem")
            new_lines.append(" MISESERI, MISESAVG, S, E")
            break

        new_lines.append(line)

    new_lines.append("*End Step")
    return "\n".join(new_lines) + "\n"


def build_package(out_dir: Path = DEFAULT_OUT_DIR, target_u1: float = 0.001) -> dict:
    if not SRC_INP.is_file():
        raise FileNotFoundError(f"Source H0 deck missing: {SRC_INP}")

    out_dir.mkdir(parents=True, exist_ok=True)

    inp_text = SRC_INP.read_text(encoding="utf-8")
    preanalysis_deck = build_miseseri_deck(inp_text, target_u1=target_u1)

    out_inp = out_dir / "ModeII_MISESERI_preanalysis.inp"
    write_text_lf(out_inp, preanalysis_deck)

    deck_sha = sha256_file(out_inp)

    input_hashes_file = out_dir / "input_hashes.sha256"
    write_text_lf(input_hashes_file, f"{deck_sha}  ModeII_MISESERI_preanalysis.inp\n")

    manifest = {
        "job_name": "mode_ii_miseseri_preanalysis",
        "method": "pandey_kumar_miseseri_preanalysis",
        "coarse_source_mesh": "H0",
        "preanalysis_load_u1_mm": target_u1,
        "continuum_elements": 3930,
        "element_type": "CPS4",
        "material": "Elastic (E=210, nu=0.3)",
        "output_requests": ["MISESERI", "MISESAVG", "S", "E", "U", "RF"],
        "deck_sha256": deck_sha,
        "out_dir": str(out_dir.relative_to(ROOT)),
    }

    manifest_file = out_dir / "GENERATION_MANIFEST.json"
    write_text_lf(manifest_file, json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    report_text = f"""# Package Report: Candidate Job B (Pandey-Kumar MISESERI Pre-Analysis)

- **Job Name:** `mode_ii_miseseri_preanalysis`
- **Coarse Mesh:** H0 ($3,930$ CPS4 continuum elements)
- **Pre-Analysis Elastic Load Target:** $U_1 = {target_u1:.4f}\\text{{ mm}}$ (~8.3% of $U_{{1,\\mathrm{{peak}}}}$)
- **Material:** Standard Abaqus Elastic ($E = 210\\text{{ kN/mm}}^2, \\nu = 0.3$)
- **Output Requests:** `MISESERI`, `MISESAVG`, `S`, `E`, `U`, `RF`
- **Deck SHA-256:** `{deck_sha}`
"""
    write_text_lf(out_dir / "PACKAGE_REPORT.md", report_text)

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--target-u1", type=float, default=0.001)
    args = parser.parse_args()

    res = build_package(args.out_dir, args.target_u1)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
