#!/usr/bin/env python3
"""Generate the Stage-F Mode-II H0 serial technical package.

Uses the accepted Molnar staggered formulation and the Mode-I H0 supplementary
mesh. Changes only pure-shear boundary conditions, job metadata, and required
output requests. Does not submit jobs or enable MISESERI remeshing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_INP = ROOT / "models/generated/molnar_gravouil_2017/h_convergence_lc015/H0_exact/SingleNotch.inp"
SRC_FOR = ROOT / "models/generated/molnar_gravouil_2017/h_convergence_lc015/H0_exact/SingleNotch.for"
OUT_DIR = ROOT / "models/generated/mode_ii/h0_serial"
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


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def transform_inp(text: str) -> str:
    # Header
    text = text.replace(
        "** Job name: Single Notched Tension Test name: Model-1",
        "** Job name: Mode-II pure shear H0 serial name: Stage-F-Mode-II-H0",
    )
    text = text.replace(
        "** Created by: Gergely Molnar and Anthony Gravouil, 2016",
        "** Created by: Gergely Molnar and Anthony Gravouil, 2016\n"
        "** Stage-F Mode-II pure-shear adaptation: geometry/mesh/N_ELEM unchanged;\n"
        "** only pure-shear BC, RP coupling DOF, and output requests modified.",
    )

    # Replace Mode-I RP/top vertical coupling with pure-shear horizontal coupling.
    old_eq = (
        "** Constraint: Constraint-1\n"
        "*Equation\n"
        "2\n"
        "top, 2, 1.\n"
        "RP, 2, -1.\n"
    )
    new_eq = (
        "** Constraint: Mode-II pure-shear top U1 -> RP U1\n"
        "*Equation\n"
        "2\n"
        "top, 1, 1.\n"
        "RP, 1, -1.\n"
    )
    if old_eq not in text:
        raise RuntimeError("expected Mode-I equation block not found")
    text = text.replace(old_eq, new_eq, 1)

    # Replace both step BC blocks carefully by rewriting the full step region.
    # Step-1 BC section
    old_bc_step1 = (
        "** Name: Load Type: Displacement/Rotation\n"
        "*Boundary, amplitude=Amp-1\n"
        "RP, 2, 2, 1.\n"
        "** Name: support Type: Displacement/Rotation\n"
        "*Boundary\n"
        "bottom, 2, 2\n"
        "** Name: support_l Type: Displacement/Rotation\n"
        "*Boundary\n"
        "bottoml, 1, 1\n"
        "** Name: support_top Type: Displacement/Rotation\n"
        "*Boundary\n"
        "topl, 1, 1\n"
    )
    new_bc_step1 = (
        "** Name: Mode-II shear load Type: Displacement/Rotation\n"
        "*Boundary, amplitude=Amp-1\n"
        "RP, 1, 1, 1.\n"
        "** Name: bottom_fixed Type: Displacement/Rotation\n"
        "*Boundary\n"
        "bottom, 1, 2\n"
        "** Name: top_vertical_restraint Type: Displacement/Rotation\n"
        "*Boundary\n"
        "top, 2, 2\n"
    )
    if old_bc_step1 not in text:
        raise RuntimeError("expected Mode-I step-1 BC block not found")
    text = text.replace(old_bc_step1, new_bc_step1, 1)

    old_bc_step2 = (
        "** Name: Load Type: Displacement/Rotation\n"
        "*Boundary, amplitude=Amp-2\n"
        "RP, 2, 2, 1.\n"
    )
    new_bc_step2 = (
        "** Name: Mode-II shear load Type: Displacement/Rotation\n"
        "*Boundary, amplitude=Amp-2\n"
        "RP, 1, 1, 1.\n"
    )
    if old_bc_step2 not in text:
        raise RuntimeError("expected Mode-I step-2 BC block not found")
    text = text.replace(old_bc_step2, new_bc_step2, 1)

    # Expand field outputs in both steps to required Stage-F set.
    old_out = (
        "*Output, field, time interval=0.01\n"
        "*Node Output\n"
        "U, \n"
        "** \n"
        "** FIELD OUTPUT: Reaction\n"
        "** \n"
        "*Node Output, nset=RP\n"
        "RF, U\n"
        "** \n"
        "** HISTORY OUTPUT: H-Output-1\n"
        "** \n"
        "*element output, elset=umatelem\n"
        "SDV\n"
    )
    new_out = (
        "*Output, field, time interval=0.01\n"
        "*Node Output\n"
        "U, RF\n"
        "** \n"
        "** FIELD OUTPUT: Reaction\n"
        "** \n"
        "*Node Output, nset=RP\n"
        "RF, U\n"
        "** \n"
        "** FIELD OUTPUT: Element state and continuum\n"
        "** \n"
        "*Element Output, elset=umatelem\n"
        "SDV, S, EVOL\n"
        "** \n"
        "** HISTORY OUTPUT: Energies\n"
        "** \n"
        "*Output, history, variable=PRESELECT\n"
        "*Energy Output\n"
        "ALLAE, ALLCD, ALLIE, ALLKE, ALLPD, ALLSE, ALLWK, ETOTAL\n"
    )
    count = text.count(old_out)
    if count != 2:
        raise RuntimeError(f"expected two Mode-I output blocks, found {count}")
    text = text.replace(old_out, new_out)

    # Ensure no residual Mode-I RP DOF-2 prescriptions remain in BC lines.
    if re.search(r"^RP, 2, 2", text, flags=re.M):
        raise RuntimeError("residual Mode-I RP U2 prescription remains")
    if "top, 2, 1." in text and "top, 1, 1." not in text:
        raise RuntimeError("Mode-II equation not applied")
    return text


def transform_fortran(text: str) -> str:
    # Keep scientific source identical except a header provenance comment.
    banner = (
        "C Stage-F Mode-II H0 serial package: isolated copy of accepted H0\n"
        "C Molnar staggered source. N_ELEM and formulation unchanged.\n"
        "C Only the input deck BCs/loading/output differ for pure shear.\n"
    )
    if text.startswith("C ======"):
        return banner + text
    return banner + text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    if not SRC_INP.is_file() or not SRC_FOR.is_file():
        raise SystemExit(f"missing Mode-I H0 source deck/source: {SRC_INP} / {SRC_FOR}")

    base_inp = SRC_INP.read_text(encoding="utf-8", errors="replace")
    base_for = SRC_FOR.read_text(encoding="utf-8", errors="replace")
    if f"N_ELEM={EXPECTED_N_ELEM}" not in base_for:
        raise SystemExit(f"source Fortran N_ELEM is not {EXPECTED_N_ELEM}")

    mode_ii_inp = transform_inp(base_inp)
    mode_ii_for = transform_fortran(base_for)

    deck_path = out_dir / "ModeII_H0_serial.inp"
    source_path = out_dir / "ModeII_H0_serial.for"
    write_text_lf(deck_path, mode_ii_inp)
    write_text_lf(source_path, mode_ii_for)

    # Keep a byte-stable LF copy of the parent Mode-I H0 hashes for audit.
    parent_hashes = {
        "mode_i_h0_inp": str(SRC_INP.relative_to(ROOT)).replace("\\", "/"),
        "mode_i_h0_inp_sha256": sha256_file(SRC_INP),
        "mode_i_h0_for": str(SRC_FOR.relative_to(ROOT)).replace("\\", "/"),
        "mode_i_h0_for_sha256": sha256_file(SRC_FOR),
    }

    deck_sha = sha256_file(deck_path)
    source_sha = sha256_file(source_path)
    hashes_path = out_dir / "input_hashes.sha256"
    write_text_lf(
        hashes_path,
        "\n".join(
            [
                f"{deck_sha}  ModeII_H0_serial.inp",
                f"{source_sha}  ModeII_H0_serial.for",
                "",
            ]
        ),
    )

    manifest = {
        "classification": "stage_f_mode_ii_h0_package_prepared",
        "benchmark_mode": "Mode-II",
        "loading_angle_degrees": 0,
        "formulation": "molnar_staggered_uel_umat",
        "miseseri_remeshing": False,
        "physical_element_count": EXPECTED_PHYSICAL,
        "layered_element_count": EXPECTED_LAYERED,
        "node_count": EXPECTED_NODES,
        "n_elem_fortran": EXPECTED_N_ELEM,
        "deck": {
            "path": "ModeII_H0_serial.inp",
            "sha256": deck_sha,
        },
        "source": {
            "path": "ModeII_H0_serial.for",
            "sha256": source_sha,
            "scientific_formulation_changed": False,
            "n_elem_changed": False,
        },
        "parent_mode_i_h0": parent_hashes,
        "boundary_conditions": {
            "bottom": "U1_U2_fixed",
            "top_U1": "prescribed_via_RP_equation",
            "top_U2": "fixed",
            "reaction_component": "RF1",
            "displacement_component": "U1",
        },
        "outputs_requested": ["U", "RF", "SDV", "S", "EVOL", "energies"],
        "execution_authorized": False,
        "datacheck_authorized": False,
        "solver_authorized": False,
    }
    write_text_lf(
        out_dir / "PACKAGE_MANIFEST.json",
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    )

    readme = """# Mode-II H0 serial technical package

Classification: `stage_f_mode_ii_h0_package_prepared`

## Scope

- Geometry/mesh: accepted Mode-I H0 supplementary single-notch mesh.
- Formulation: accepted Molnar staggered UEL/UMAT (`N_ELEM=3930`).
- Change: pure-shear loading (top U1 via RP; bottom fully fixed; top U2 fixed).
- No MISESERI remeshing in this package.
- No execution authorization.

## Files

- `ModeII_H0_serial.inp`
- `ModeII_H0_serial.for`
- `PACKAGE_MANIFEST.json`
- `input_hashes.sha256`
- `BENCHMARK_DEFINITION.md`

## Next gates

1. Offline static validator pass.
2. Fail-closed lane preparation.
3. Separate datacheck authorization-only commit before any submission.
"""
    write_text_lf(out_dir / "README.md", readme)

    definition = """# Mode-II H0 benchmark definition freeze (F0.1)

## Geometry

- Domain: 1.0 mm x 1.0 mm rectangle.
- Left-edge notch length 0.5 mm at y = 0 (mid-height).
- Plane strain, thickness 1.0 mm.
- Mesh: Mode-I H0 supplementary structured mesh, ~0.005 mm local size,
  3930 physical UEL elements / 11790 layered elements / 3999 nodes.

## Material and fracture (Molnar)

- E = 210 kN/mm^2
- nu = 0.3
- Gc = 0.0027 kN/mm
- lc = 0.015 mm
- residual k = 1e-7 (U2); UMAT visualization constant 1e-11
- Phase-field convention: d = 0 intact, d = 1 fully broken

## Boundary conditions (pure shear, alpha = 0 deg)

- Bottom edge: U1 = U2 = 0
- Top edge: U2 = 0; U1 prescribed through equation coupling to RP
- RP DOF 1 amplitude schedule retained from Mode-I H0 technical envelope:
  0 -> 0.005 mm (Step-1), then to 0.010 mm (Step-2)
- Reaction evidence component: RF1; displacement component: U1

## Reference data

- RF-U: `reference_data_insufficient` for pure shear (Fig. 7 is tension).
- Crack path: qualitative curved/diagonal shear path (Fig. 6c).
- Path extraction threshold: provisional SDV15 >= 0.5

## Formulation boundary

Do not mix Msekh or Pandey formulations. Pandey is relevant only later for
MISESERI pre-refinement methodology after F1 baseline passes.
"""
    write_text_lf(out_dir / "BENCHMARK_DEFINITION.md", definition)

    print(json.dumps({"classification": manifest["classification"], "out_dir": str(out_dir), "deck_sha256": deck_sha, "source_sha256": source_sha}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
