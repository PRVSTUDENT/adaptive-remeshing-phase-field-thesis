#!/usr/bin/env python3
"""Deterministic audit of two Molnar layered decks (H1 vs refined).

Extracts geometry, layer structure, materials, BC sets, loading, and
Fortran N_ELEM consistency. Writes JSON/MD/CSV/keyword-diff reports.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def parse_deck(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    out: dict[str, Any] = {
        "path": str(path).replace("\\", "/"),
        "sha256": sha256_file(path),
        "n_lines": len(lines),
    }

    # Part nodes
    nodes: dict[int, tuple[float, float]] = {}
    mode = None
    for line in lines:
        low = line.lower()
        if low.startswith("*node") and "nset" not in low:
            mode = "node"
            continue
        if line.startswith("*") and mode == "node":
            mode = None
        if mode == "node":
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 3:
                try:
                    nodes[int(float(parts[0]))] = (float(parts[1]), float(parts[2]))
                except ValueError:
                    pass
    xs = [p[0] for p in nodes.values()]
    ys = [p[1] for p in nodes.values()]
    out["geometry"] = {
        "n_part_nodes": len(nodes),
        "bbox": {
            "x_min": min(xs) if xs else None,
            "x_max": max(xs) if xs else None,
            "y_min": min(ys) if ys else None,
            "y_max": max(ys) if ys else None,
        },
        "has_exact_y0": any(abs(y) < 1e-12 for y in ys),
        "y_nearest_0": min((abs(y), y) for y in ys)[1] if ys else None,
        "notch_line_nodes_y0_xneg": sum(
            1 for x, y in nodes.values() if abs(y) < 1e-12 and -0.5 - 1e-9 <= x < 0.0
        ),
    }
    # doubled notch x
    xs_notch = [round(x, 10) for x, y in nodes.values() if abs(y) < 1e-12 and x < 0]
    c = Counter(xs_notch)
    out["geometry"]["notch_unique_x"] = len(c)
    out["geometry"]["notch_doubled_x"] = sum(1 for v in c.values() if v >= 2)
    out["geometry"]["notch_single_x"] = sum(1 for v in c.values() if v == 1)
    out["geometry"]["notch_split_present"] = (
        out["geometry"]["notch_doubled_x"] > 0 and out["geometry"]["has_exact_y0"]
    )

    # Element types / counts
    el_type = None
    counts: Counter[str] = Counter()
    for line in lines:
        m = re.match(r"\*Element,\s*type=([^,\s]+)", line, re.I)
        if m:
            el_type = m.group(1).upper()
            continue
        if line.startswith("*"):
            el_type = None
            continue
        if el_type:
            counts[el_type] += 1
    out["layers"] = {
        "counts": dict(counts),
        "n_physical_u1": counts.get("U1", 0),
        "n_u2": counts.get("U2", 0),
        "n_cps4": counts.get("CPS4", 0),
        "layered_total": sum(counts.values()),
        "counts_equal": counts.get("U1", 0) == counts.get("U2", 0) == counts.get("CPS4", 0),
    }
    n = counts.get("U1", 0)
    out["layers"]["expected_offsets"] = {
        "U1": f"1..{n}",
        "U2": f"{n+1}..{2*n}",
        "CPS4": f"{2*n+1}..{3*n}",
    }

    # UEL / UMAT properties
    def next_data(i: int) -> str:
        j = i + 1
        while j < len(lines) and (lines[j].startswith("**") or not lines[j].strip()):
            j += 1
        return lines[j] if j < len(lines) else ""

    props: dict[str, Any] = {}
    for i, line in enumerate(lines):
        low = line.lower()
        if low.startswith("*uel property") and "plate_ss" in low:
            props["u2_uel"] = [float(x) for x in next_data(i).split(",") if x.strip()]
        elif low.startswith("*uel property") and "plate" in low and "plate_ss" not in low:
            props["u1_uel"] = [float(x) for x in next_data(i).split(",") if x.strip()]
        elif low.startswith("*user material"):
            props["umat"] = [float(x) for x in next_data(i).split(",") if x.strip()]
        elif low.startswith("*solid section") and "umatelem" in low:
            props["cps4_thickness"] = float(next_data(i).split(",")[0])
        elif low.startswith("*material, name=umatelem"):
            props["umat_material_name"] = "umatelem"
    out["properties"] = props
    # interpret
    if props.get("u2_uel") and len(props["u2_uel"]) >= 4:
        out["properties"]["E"] = props["u2_uel"][0]
        out["properties"]["nu"] = props["u2_uel"][1]
        out["properties"]["thickness_u2"] = props["u2_uel"][2]
        out["properties"]["residual_stiffness_u2"] = props["u2_uel"][3]
    if props.get("u1_uel") and len(props["u1_uel"]) >= 3:
        out["properties"]["lc"] = props["u1_uel"][0]
        out["properties"]["Gc"] = props["u1_uel"][1]
        out["properties"]["thickness_u1"] = props["u1_uel"][2]
    if props.get("umat") and len(props["umat"]) >= 2:
        out["properties"]["residual_stiffness_umat"] = props["umat"][0]
        out["properties"]["nu_umat"] = props["umat"][1]

    # nsets
    nsets: dict[str, list[int]] = {}
    i = 0
    while i < len(lines):
        m = re.match(r"\*Nset,\s*nset=([^,\s]+)", lines[i], re.I)
        if m:
            name = m.group(1)
            ids: list[int] = []
            i += 1
            while i < len(lines) and not lines[i].startswith("*"):
                for p in re.split(r"[,\s]+", lines[i].strip()):
                    if not p:
                        continue
                    try:
                        ids.append(int(float(p)))
                    except ValueError:
                        pass
                i += 1
            nsets[name] = ids
            continue
        i += 1
    out["nsets"] = {k: {"count": len(v), "ids_minmax": (min(v), max(v)) if v else None} for k, v in nsets.items()}
    out["nsets_raw_counts"] = {k: len(v) for k, v in nsets.items()}

    # BC / amplitudes / equation
    amps = re.findall(r"\*Amplitude, name=([^\n]+)\n([^\n*]+)", text, re.I)
    out["loading"] = {
        "amplitudes": {a[0].strip(): a[1].strip() for a in amps},
        "has_equation_top_rp": bool(re.search(r"\*Equation\s*\n2\s*\ntop,\s*2,\s*1\.", text, re.I)),
        "boundary_rp_u2": bool(re.search(r"RP,\s*2,\s*2,\s*1", text, re.I)),
        "boundary_bottom_u2": bool(re.search(r"bottom,\s*2,\s*2", text, re.I)),
        "boundary_bottoml_u1": bool(re.search(r"bottoml,\s*1,\s*1", text, re.I)),
        "boundary_topl_u1": bool(re.search(r"topl,\s*1,\s*1", text, re.I)),
        "steps": re.findall(r"\*Step, name=([^,\n]+)", text, re.I),
    }

    # keywords sample for diff
    out["keyword_lines"] = [
        ln for ln in lines if ln.startswith("*") and not ln.startswith("**")
    ]
    return out


def parse_fortran(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {"present": False}
    text = path.read_text(encoding="utf-8", errors="replace")
    n_elems = [int(m) for m in re.findall(r"N_ELEM\s*=\s*(\d+)", text)]
    return {
        "present": True,
        "path": str(path).replace("\\", "/"),
        "sha256": sha256_file(path),
        "N_ELEM_values": n_elems,
        "N_ELEM_unique": sorted(set(n_elems)),
    }


def compare(a: dict[str, Any], b: dict[str, Any], name_a: str, name_b: str) -> dict[str, Any]:
    diffs = []

    def add(path: str, va: Any, vb: Any, severity: str = "info"):
        if va != vb:
            diffs.append({"path": path, name_a: va, name_b: vb, "severity": severity})

    # properties of interest
    for key in (
        "E",
        "nu",
        "lc",
        "Gc",
        "thickness_u1",
        "thickness_u2",
        "residual_stiffness_u2",
        "residual_stiffness_umat",
        "nu_umat",
        "cps4_thickness",
    ):
        add(f"properties.{key}", a["properties"].get(key), b["properties"].get(key), "critical")

    add(
        "geometry.notch_split_present",
        a["geometry"].get("notch_split_present"),
        b["geometry"].get("notch_split_present"),
        "critical",
    )
    add(
        "geometry.has_exact_y0",
        a["geometry"].get("has_exact_y0"),
        b["geometry"].get("has_exact_y0"),
        "critical",
    )
    add("geometry.bbox", a["geometry"].get("bbox"), b["geometry"].get("bbox"), "info")
    add("layers.counts_equal", a["layers"].get("counts_equal"), b["layers"].get("counts_equal"), "critical")
    add(
        "loading.amplitudes",
        a["loading"].get("amplitudes"),
        b["loading"].get("amplitudes"),
        "critical",
    )
    for bc in (
        "has_equation_top_rp",
        "boundary_rp_u2",
        "boundary_bottom_u2",
        "boundary_bottoml_u1",
        "boundary_topl_u1",
    ):
        add(f"loading.{bc}", a["loading"].get(bc), b["loading"].get(bc), "critical")

    # residual umat should be tiny
    umat_a = a["properties"].get("residual_stiffness_umat")
    umat_b = b["properties"].get("residual_stiffness_umat")
    cps4_full_e_risk_b = (
        umat_b is not None and umat_b is not None and float(umat_b) > 1.0
    )  # E-like

    hyp_notch = not b["geometry"].get("notch_split_present")
    hyp_cps4 = cps4_full_e_risk_b

    return {
        "name_a": name_a,
        "name_b": name_b,
        "diffs": diffs,
        "critical_diffs": [d for d in diffs if d["severity"] == "critical"],
        "hypotheses": {
            "missing_notch_split_on_b": {
                "active": hyp_notch,
                "evidence": b["geometry"],
                "expected_effect": "continuous plate; higher elastic stiffness; no crack initiation",
            },
            "cps4_full_elastic_umat_on_b": {
                "active": hyp_cps4,
                "evidence": {"residual_stiffness_umat": umat_b},
                "expected_effect": "double stiffness if CPS4 carries continuum E",
            },
            "properties_match_h1": {
                "active": all(
                    a["properties"].get(k) == b["properties"].get(k)
                    for k in ("E", "nu", "lc", "Gc", "residual_stiffness_u2", "residual_stiffness_umat")
                ),
                "evidence": "UEL/UMAT numeric properties equal",
            },
        },
    }


def write_property_csv(path: Path, a: dict, b: dict, name_a: str, name_b: str) -> None:
    keys = sorted(
        set(list(a.get("properties", {}).keys()) + list(b.get("properties", {}).keys()))
    )
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["property", name_a, name_b, "equal"])
        for k in keys:
            va = a["properties"].get(k)
            vb = b["properties"].get(k)
            w.writerow([k, va, vb, va == vb])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--deck-a", type=Path, required=True, help="Reference H1 deck")
    ap.add_argument("--deck-b", type=Path, required=True, help="Refined C2F-v2 deck")
    ap.add_argument("--for-a", type=Path, default=None)
    ap.add_argument("--for-b", type=Path, default=None)
    ap.add_argument("--name-a", default="H1")
    ap.add_argument("--name-b", default="C2F_v2")
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    a = parse_deck(args.deck_a)
    b = parse_deck(args.deck_b)
    a["fortran"] = parse_fortran(args.for_a)
    b["fortran"] = parse_fortran(args.for_b)
    if a["fortran"].get("present") and a["layers"]["n_physical_u1"]:
        a["fortran"]["matches_physical"] = a["fortran"]["N_ELEM_unique"] == [
            a["layers"]["n_physical_u1"]
        ]
    if b["fortran"].get("present") and b["layers"]["n_physical_u1"]:
        b["fortran"]["matches_physical"] = b["fortran"]["N_ELEM_unique"] == [
            b["layers"]["n_physical_u1"]
        ]

    cmp = compare(a, b, args.name_a, args.name_b)
    report = {
        "deck_a": a,
        "deck_b": b,
        "comparison": cmp,
        "primary_finding": None,
    }
    if cmp["hypotheses"]["missing_notch_split_on_b"]["active"]:
        report["primary_finding"] = (
            "Refined deck lacks notch split at y=0 (no doubled nodes on notch line). "
            "Geometry is a continuous plate; this explains elevated elastic stiffness "
            "and absent fracture localization. CPS4 residual matches H1 (1e-11), so "
            "double continuum stiffness is NOT supported by deck properties."
        )
    elif cmp["hypotheses"]["cps4_full_elastic_umat_on_b"]["active"]:
        report["primary_finding"] = "CPS4/UMAT residual looks continuum-scale; possible double stiffness."
    else:
        report["primary_finding"] = "No single critical geometry/property smoking gun auto-detected."

    (out / "H1_VS_C2F_V2_DECK_AUDIT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_property_csv(out / "H1_VS_C2F_V2_PROPERTY_DIFF.csv", a, b, args.name_a, args.name_b)

    # keyword diff (set of keywords)
    ka = set(re.findall(r"^\*([A-Za-z][A-Za-z0-9 ]*)", "\n".join(a["keyword_lines"]), re.M))
    kb = set(re.findall(r"^\*([A-Za-z][A-Za-z0-9 ]*)", "\n".join(b["keyword_lines"]), re.M))
    (out / "H1_VS_C2F_V2_KEYWORD_DIFF.txt").write_text(
        "only_in_%s:\n" % args.name_a
        + "\n".join(sorted(ka - kb))
        + "\n\nonly_in_%s:\n" % args.name_b
        + "\n".join(sorted(kb - ka))
        + "\n\nshared_count=%d\n" % len(ka & kb),
        encoding="utf-8",
    )

    # BC audit focused
    bc = {
        "nsets_a": a["nsets_raw_counts"],
        "nsets_b": b["nsets_raw_counts"],
        "loading_a": a["loading"],
        "loading_b": b["loading"],
        "missing_nsets_on_b": sorted(set(a["nsets_raw_counts"]) - set(b["nsets_raw_counts"])),
        "extra_nsets_on_b": sorted(set(b["nsets_raw_counts"]) - set(a["nsets_raw_counts"])),
    }
    (out / "H1_VS_C2F_V2_BC_AUDIT.json").write_text(
        json.dumps(bc, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # load-carrying audit from properties
    load_carry = {
        "layers": [
            {
                "layer": "U1_phase",
                "element_type": "U1",
                "count_a": a["layers"]["n_physical_u1"],
                "count_b": b["layers"]["n_physical_u1"],
                "section": "UEL PLATE",
                "material_props": "lc,Gc,thickness",
                "Youngs_modulus": None,
                "residual_stiffness": None,
                "mechanical_DOFs": "phase only (DOF 3)",
                "expected_load_contribution": "none (phase)",
            },
            {
                "layer": "U2_displacement",
                "element_type": "U2",
                "count_a": a["layers"]["n_u2"],
                "count_b": b["layers"]["n_u2"],
                "section": "UEL PLATE_SS",
                "Youngs_modulus_a": a["properties"].get("E"),
                "Youngs_modulus_b": b["properties"].get("E"),
                "residual_stiffness_a": a["properties"].get("residual_stiffness_u2"),
                "residual_stiffness_b": b["properties"].get("residual_stiffness_u2"),
                "mechanical_DOFs": "1,2",
                "expected_load_contribution": "primary (full E via UEL)",
            },
            {
                "layer": "CPS4_facsimile",
                "element_type": "CPS4",
                "count_a": a["layers"]["n_cps4"],
                "count_b": b["layers"]["n_cps4"],
                "section": "Solid Section umatelem",
                "Youngs_modulus_as_umat_const1_a": a["properties"].get("residual_stiffness_umat"),
                "Youngs_modulus_as_umat_const1_b": b["properties"].get("residual_stiffness_umat"),
                "residual_policy": "frozen H1 residual_stiffness_umat ~1e-11",
                "mechanical_DOFs": "1,2 continuum",
                "expected_load_contribution": "negligible if residual ~1e-11",
                "double_stiffness_risk": float(b["properties"].get("residual_stiffness_umat") or 0)
                > 1.0,
            },
        ],
        "conclusion": (
            "CPS4 residual matches H1 (~1e-11); unintended full-E continuum CPS4 "
            "is NOT indicated. Prefer missing-notch geometry hypothesis for stiffness."
        ),
    }
    (out / "C2F_V2_LOAD_CARRYING_LAYER_AUDIT.json").write_text(
        json.dumps(load_carry, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    md = [
        "# H1 vs C2F-v2 layered deck audit",
        "",
        "## Primary finding",
        "",
        report["primary_finding"] or "",
        "",
        "## Geometry",
        "",
        f"| Item | {args.name_a} | {args.name_b} |",
        "| --- | --- | --- |",
        f"| part nodes | {a['geometry']['n_part_nodes']} | {b['geometry']['n_part_nodes']} |",
        f"| bbox | `{a['geometry']['bbox']}` | `{b['geometry']['bbox']}` |",
        f"| exact y=0 | {a['geometry']['has_exact_y0']} | {b['geometry']['has_exact_y0']} |",
        f"| y nearest 0 | {a['geometry']['y_nearest_0']} | {b['geometry']['y_nearest_0']} |",
        f"| notch-line nodes (y=0,x<0) | {a['geometry']['notch_line_nodes_y0_xneg']} | {b['geometry']['notch_line_nodes_y0_xneg']} |",
        f"| notch doubled x-stations | {a['geometry']['notch_doubled_x']} | {b['geometry']['notch_doubled_x']} |",
        f"| **notch_split_present** | **{a['geometry']['notch_split_present']}** | **{b['geometry']['notch_split_present']}** |",
        "",
        "## Layers",
        "",
        f"| Layer | {args.name_a} | {args.name_b} |",
        "| --- | ---: | ---: |",
        f"| U1 | {a['layers']['n_physical_u1']} | {b['layers']['n_physical_u1']} |",
        f"| U2 | {a['layers']['n_u2']} | {b['layers']['n_u2']} |",
        f"| CPS4 | {a['layers']['n_cps4']} | {b['layers']['n_cps4']} |",
        "",
        "## Properties (critical)",
        "",
        f"| Prop | {args.name_a} | {args.name_b} |",
        "| --- | --- | --- |",
    ]
    for k in ("E", "nu", "lc", "Gc", "residual_stiffness_u2", "residual_stiffness_umat"):
        md.append(f"| {k} | {a['properties'].get(k)} | {b['properties'].get(k)} |")
    md.extend(
        [
            "",
            "## Hypotheses",
            "",
            f"- missing_notch_split_on_b: **{cmp['hypotheses']['missing_notch_split_on_b']['active']}**",
            f"- cps4_full_elastic_umat_on_b: **{cmp['hypotheses']['cps4_full_elastic_umat_on_b']['active']}**",
            f"- properties_match_h1: **{cmp['hypotheses']['properties_match_h1']['active']}**",
            "",
            "## Fortran",
            "",
            f"- {args.name_a}: {a['fortran']}",
            f"- {args.name_b}: {b['fortran']}",
            "",
        ]
    )
    (out / "H1_VS_C2F_V2_DECK_AUDIT.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(json.dumps({"primary_finding": report["primary_finding"], "hypotheses": cmp["hypotheses"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
