#!/usr/bin/env python3
"""C2B: scientific gate on auxiliary continuum MISESERI + offline remesh.

Exits nonzero unless gate passes, then writes refined physical mesh using frozen
remeshing parameters.
"""

import argparse
import csv
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/model_generation"))
sys.path.insert(0, str(ROOT / "scripts/remeshing"))

from build_refined_mesh_from_miseseri import (  # noqa: E402
    apply_marks,
    build_mesh,
    corridor_stats,
    refined_zone_from_rows,
)


def load_rows(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def classify_region(x, y):
    if -0.05 <= x <= 0.35 and abs(y) <= 0.03:
        return "notch_corridor"
    if abs(y) >= 0.45 or y >= 0.40 or y <= -0.40:
        return "outer_boundary"
    if abs(x) >= 0.45:
        return "outer_boundary"
    return "far_field"


def top_frac_indices(vals, frac):
    n = len(vals)
    k = max(1, int(math.ceil(frac * n)))
    order = sorted(range(n), key=lambda i: vals[i], reverse=True)
    return set(order[:k])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--tech-json", type=Path, default=None)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    rows = load_rows(args.csv)
    tech = {}
    if args.tech_json and args.tech_json.exists():
        tech = json.loads(args.tech_json.read_text(encoding="utf-8"))

    n = len(rows)
    miseseri = [float(r["MISESERI"]) for r in rows]
    vm = [float(r["von_mises"]) if r.get("von_mises") not in ("", None) else float("nan") for r in rows]
    xs = [float(r["centroid_x"]) for r in rows]
    ys = [float(r["centroid_y"]) for r in rows]
    regions = [classify_region(x, y) for x, y in zip(xs, ys)]

    max_e = max(miseseri) if miseseri else 0.0
    max_vm = max(v for v in vm if v == v) if any(v == v for v in vm) else 0.0
    finite = all(math.isfinite(v) for v in miseseri) and all(v == v or True for v in vm)
    # require all von_mises finite
    finite = all(math.isfinite(v) for v in miseseri) and all(math.isfinite(v) for v in vm if v == v)
    finite_vm = all(math.isfinite(v) for v in vm)

    top5 = top_frac_indices(miseseri, 0.05)
    corridor5 = sum(1 for i in top5 if regions[i] == "notch_corridor") / float(len(top5))
    boundary5 = sum(1 for i in top5 if regions[i] == "outer_boundary") / float(len(top5))

    # Gates (user-specified)
    # von Mises in MPa (aux deck uses MPa)
    g_vm = max_vm > 1.0
    g_e = max_e > 1.0e-6
    g_cor = corridor5 >= 0.25
    g_dom = corridor5 >= boundary5
    g_n = n == 3930
    g_fields = True
    if tech:
        fp = tech.get("field_present", {})
        g_fields = all(fp.get(k, False) for k in ("MISESERI", "MISESAVG", "S", "EVOL", "U", "RF"))
        g_fields = g_fields and tech.get("n_phys_ok", True)

    checks = {
        "n_elements_3930": g_n,
        "fields_present": g_fields,
        "miseseri_finite": all(math.isfinite(v) for v in miseseri),
        "von_mises_finite": finite_vm,
        "max_von_mises_gt_1_MPa": g_vm,
        "max_MISESERI_gt_1e-6": g_e,
        "top5_corridor_ge_0.25": g_cor,
        "top5_corridor_ge_boundary": g_dom,
        "max_MISESERI": max_e,
        "max_von_mises_MPa": max_vm,
        "top5_corridor_fraction": corridor5,
        "top5_boundary_fraction": boundary5,
    }
    gate_pass = all(
        [
            checks["n_elements_3930"],
            checks["fields_present"],
            checks["miseseri_finite"],
            checks["von_mises_finite"],
            checks["max_von_mises_gt_1_MPa"],
            checks["max_MISESERI_gt_1e-6"],
            checks["top5_corridor_ge_0.25"],
            checks["top5_corridor_ge_boundary"],
        ]
    )

    classification = (
        "miseseri_preanalysis_suitable_for_remeshing"
        if gate_pass
        else "miseseri_preanalysis_scientific_gate_fail"
    )
    if max_e < 1.0e-12 or max_vm < 1.0e-6:
        classification = "miseseri_output_available_but_scientifically_inactive"

    summary = {
        "classification": classification,
        "gate_pass": gate_pass,
        "checks": checks,
        "region_counts": dict(Counter(regions)),
        "n": n,
        "tech": tech,
    }
    (args.out_dir / "C2B_FIELD_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    # annotate CSV
    max_e_safe = max_e if max_e > 0 else 1.0
    for i, r in enumerate(rows):
        r["region_classification"] = regions[i]
        r["normalized_MISESERI"] = float(r["MISESERI"]) / max_e_safe
        r["in_top_5pct"] = 1 if i in top5 else 0
    out_csv = args.out_dir / "C2A_MISESERI_ELEMENT_DATA.csv"
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    report = [
        "# C2B Scientific Gate Report",
        "",
        "classification: `%s`" % classification,
        "gate_pass: **%s**" % ("PASS" if gate_pass else "FAIL"),
        "",
        "## Checks",
        "",
    ]
    for k, v in sorted(checks.items()):
        report.append("- `%s`: %s" % (k, v))
    report.extend(["", "## Decision", "", "```text", "job3_style_remesh = %s" % gate_pass, "```", ""])
    (args.out_dir / "C2B_GATE_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(json.dumps({"classification": classification, "gate_pass": gate_pass, "max_MISESERI": max_e, "max_vm": max_vm}, indent=2))
    if not gate_pass:
        return 14

    # Remesh with frozen params
    config = json.loads(args.config.read_text(encoding="utf-8"))
    rule = config["rule"]
    # ensure keys
    if "minElementSize_mm" not in rule:
        rule["minElementSize_mm"] = rule.get("minElementSize", 0.0025)
    if "maxElementSize_mm" not in rule:
        rule["maxElementSize_mm"] = rule.get("maxElementSize", 0.025)

    # rows need h_mean for apply_marks - compute from EVOL if square-ish
    for r in rows:
        if "h_mean" not in r or r["h_mean"] in ("", None):
            # approximate from EVOL for plane strain unit thickness: h ~ sqrt(EVOL)
            try:
                r["h_mean"] = math.sqrt(float(r["EVOL"])) if float(r["EVOL"]) > 0 else 0.005
            except Exception:
                r["h_mean"] = 0.005
        r["xc"] = r["centroid_x"]
        r["yc"] = r["centroid_y"]

    sizing = apply_marks(rows, rule)
    min_h = float(rule["minElementSize_mm"])
    max_h = float(rule["maxElementSize_mm"])
    zone = refined_zone_from_rows(rows, min_h)
    nodes, conn = build_mesh(min_h, zone, max_h)
    # write mesh
    nodes_csv = args.out_dir / "refined_mesh_nodes.csv"
    elems_csv = args.out_dir / "refined_mesh_elements.csv"
    with nodes_csv.open("w", encoding="utf-8", newline="\n") as f:
        f.write("node_id,x,y\n")
        for nid in sorted(nodes):
            f.write("%s,%s,%s\n" % (nid, nodes[nid][0], nodes[nid][1]))
    with elems_csv.open("w", encoding="utf-8", newline="\n") as f:
        f.write("element_id,n1,n2,n3,n4\n")
        for i, c in enumerate(conn, start=1):
            f.write("%s,%s,%s,%s,%s\n" % (i, c[0], c[1], c[2], c[3]))
    phys = args.out_dir / "refined_physical.inp"
    lines = ["*Heading", "** C2B refined physical mesh", "*Node"]
    for nid in sorted(nodes):
        lines.append("%s, %.10g, %.10g" % (nid, nodes[nid][0], nodes[nid][1]))
    lines.append("*Element, type=CPS4, elset=physical")
    for i, c in enumerate(conn, start=1):
        lines.append("%s, %s, %s, %s, %s" % (i, c[0], c[1], c[2], c[3]))
    phys.write_text("\n".join(lines) + "\n", encoding="utf-8")

    cor = corridor_stats(nodes, conn, zone)
    target_ok = bool(cor and abs(cor["median"] - min_h) <= 0.25 * min_h)
    man = {
        "status": "pass" if target_ok else "fail_mesh_size_target",
        "sizing": sizing,
        "refined_zone": zone,
        "corridor_h": cor,
        "n_nodes": len(nodes),
        "n_elements": len(conn),
        "rule": rule,
        "claim_boundary": "custom_MISESERI_offline_pre_refinement_not_native_abaqus_adaptive",
    }
    (args.out_dir / "remeshing_rule_manifest.json").write_text(
        json.dumps(man, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(man, indent=2, sort_keys=True))
    return 0 if target_ok else 14


if __name__ == "__main__":
    raise SystemExit(main())
