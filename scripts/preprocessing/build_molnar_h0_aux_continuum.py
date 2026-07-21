#!/usr/bin/env python3
"""Build H0 auxiliary continuum pre-analysis deck (no UEL/UMAT).

Standard plane-strain continuum with real elastic properties for Abaqus
MISESERI recovery. Same H0 geometry/mesh/BCs and U_pre=0.00464 mm.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/preprocessing"))
from build_molnar_unified_deck import (  # noqa: E402
    chunked_numbers,
    parse_author_physical_mesh,
    write_text_lf,
)

PRESERVED_INP = ROOT / "models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.inp"
OUT_DEFAULT = ROOT / "models/generated/molnar_gravouil_2017/aux_continuum/H0_aux_miseseri"


def sha256_file(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            d.update(block)
    return d.hexdigest()


def build_deck(nodes, conn, nsets, u_pre=0.00464) -> str:
    physical = len(conn)
    max_node = max(nodes)
    rp = max_node + 1
    # Consistent units: length mm, force N, stress MPa => E = 210000 MPa
    E = 210000.0
    nu = 0.3
    lines = [
        "*Heading",
        "** Stage C C2A auxiliary continuum H0 MISESERI pre-analysis",
        "** No UEL, no UMAT, no residual stiffness",
        f"** physical_elements={physical}",
        f"** U_pre_mm={u_pre}",
        "** units: mm, N, MPa (E=210000 MPa, nu=0.3)",
        "** element: CPE4 plane strain",
        "*Preprint, echo=NO, model=NO, history=NO, contact=NO",
        "*Part, name=Part-1",
        "*Node",
    ]
    for nid in sorted(nodes):
        x, y = nodes[nid]
        lines.append(f"{nid}, {x:.10g}, {y:.10g}")
    lines.append("*Element, type=CPE4, elset=PLATE")
    for i, c in enumerate(conn, start=1):
        lines.append(f"{i}, {c[0]}, {c[1]}, {c[2]}, {c[3]}")
    lines.extend(
        [
            "*Elset, elset=PLATE, generate",
            f"1, {physical}, 1",
            "*Elset, elset=All_elem, generate",
            f"1, {physical}, 1",
            "*Solid Section, elset=PLATE, material=Steel",
            ",",
            "*End Part",
            "*Assembly, name=Assembly",
            "*Instance, name=Part-1-1, part=Part-1",
            "*End Instance",
            "*Node",
            f"{rp}, 0.5, 0.5, 0.0",
            "*Nset, nset=RP",
            f"{rp},",
        ]
    )
    for name in ("bottom", "top", "bottoml", "topl"):
        lines.append(f"*Nset, nset={name}, instance=Part-1-1")
        lines.extend(chunked_numbers(list(nsets[name])))
    lines.extend(
        [
            "*Elset, elset=PLATE, instance=Part-1-1, generate",
            f"1, {physical}, 1",
            "*Elset, elset=All_elem, instance=Part-1-1, generate",
            f"1, {physical}, 1",
            "*Equation",
            "2",
            "top, 2, 1.",
            "RP, 2, -1.",
            "*End Assembly",
            f"** U_pre = {u_pre} mm",
            "*Amplitude, name=Amp-pre",
            f"0., 0., 1., {u_pre}",
            "*Material, name=Steel",
            "*Elastic",
            f"{E}, {nu}",
            "*Step, name=Step-pre, nlgeom=NO, inc=200",
            "*Static, direct",
            "0.005, 1.0,",
            "*Boundary, amplitude=Amp-pre",
            "RP, 2, 2, 1.",
            "*Boundary",
            "bottom, 2, 2",
            "*Boundary",
            "bottoml, 1, 1",
            "*Boundary",
            "topl, 1, 1",
            "*Restart, write, frequency=0",
            "*Output, field, time interval=0.05",
            "*Node Output",
            "U,",
            "*Node Output, nset=RP",
            "RF, U",
            "*Element Output, elset=PLATE",
            "S, EVOL, MISESERI, MISESAVG",
            "*End Step",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--u-pre", type=float, default=0.00464)
    args = parser.parse_args()
    mesh = parse_author_physical_mesh(PRESERVED_INP)
    text = build_deck(mesh["nodes"], mesh["connectivity"], mesh["nsets"], args.u_pre)
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    deck = out / "molnar_h0_aux_miseseri.inp"
    write_text_lf(deck, text)
    # mesh dumps for remesh rebuild
    with (out / "mesh_nodes.csv").open("w", encoding="utf-8", newline="\n") as f:
        f.write("node_id,x,y\n")
        for nid in sorted(mesh["nodes"]):
            x, y = mesh["nodes"][nid]
            f.write(f"{nid},{x},{y}\n")
    with (out / "mesh_elements.csv").open("w", encoding="utf-8", newline="\n") as f:
        f.write("element_id,n1,n2,n3,n4\n")
        for i, c in enumerate(mesh["connectivity"], start=1):
            f.write(f"{i},{c[0]},{c[1]},{c[2]},{c[3]}\n")
    h = sha256_file(deck)
    write_text_lf(out / "input_hashes.sha256", f"{h}  molnar_h0_aux_miseseri.inp\n")
    man = {
        "deck": "molnar_h0_aux_miseseri.inp",
        "deck_sha256": h,
        "physical_elements": len(mesh["connectivity"]),
        "nodes": len(mesh["nodes"]),
        "u_pre_mm": args.u_pre,
        "E_MPa": 210000.0,
        "nu": 0.3,
        "element_type": "CPE4",
        "plane_strain": True,
        "no_uel": True,
        "no_umat": True,
        "purpose": "C2A_auxiliary_continuum_MISESERI",
    }
    write_text_lf(out / "generation_manifest.json", json.dumps(man, indent=2, sort_keys=True) + "\n")
    write_text_lf(
        out / "README.md",
        "# H0 auxiliary continuum MISESERI deck\n\n"
        "Standard CPE4 plane-strain continuum, real elastic steel properties.\n"
        "No UEL/UMAT. Used only for Stage C C2A pre-analysis.\n",
    )
    print(json.dumps(man, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
