#!/usr/bin/env python3
"""Validate Stage D2A static package or extracted ODB ingestion evidence."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


TOL = 1.0e-8


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def f(value: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"nonfinite value {value}")
    return out


def static_validate(package: Path) -> dict[str, object]:
    validation = json.loads((package / "executable/PACKAGE_VALIDATION.json").read_text(encoding="utf-8"))
    required = [
        package / "target_nodes.csv",
        package / "target_elements.csv",
        package / "target_transferred_nodal_d.csv",
        package / "target_transferred_ip_H.csv",
        package / "executable/D2A_serial_ingestion.inp",
        package / "executable/d2_transfer_table.inc",
        package / "executable/d2_tiny_transfer_uel.for",
    ]
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise RuntimeError(f"missing package files: {missing}")
    if validation.get("phase_dof_confirmed") != 3:
        raise RuntimeError("phase DOF was not confirmed as 3")
    return {"static_validation": "pass", "package_validation": validation}


def extracted_validate(package: Path, out_dir: Path, job_id: str) -> dict[str, object]:
    nodes = read_csv(out_dir / "D2A_NODE_COMPARISON.csv")
    ips = read_csv(out_dir / "D2A_IP_COMPARISON.csv")
    target_nodes = read_csv(package / "target_transferred_nodal_d.csv")
    target_ips = read_csv(package / "target_transferred_ip_H.csv")
    failures: list[str] = []
    max_node = 0.0
    max_sdv15 = 0.0
    max_sdv16 = 0.0
    node_values = []
    h_values = []
    for row in nodes:
        if row["d_odb"] in ("", "None"):
            failures.append(f"missing node {row['node']}")
            continue
        d_odb = f(row["d_odb"])
        d_transfer = f(row["d_transfer"])
        err = abs(d_odb - d_transfer)
        max_node = max(max_node, err)
        node_values.append(d_odb)
        if err > TOL:
            failures.append(f"node {row['node']} d error {err}")
        if d_odb < -TOL or d_odb > 1.0 + TOL:
            failures.append(f"node {row['node']} d outside [0,1]: {d_odb}")
    for row in ips:
        if row["sdv15_odb"] in ("", "None") or row["sdv16_odb"] in ("", "None"):
            failures.append(f"missing ip {row['element']}/{row['ip']}")
            continue
        sdv15 = f(row["sdv15_odb"])
        sdv16 = f(row["sdv16_odb"])
        h_transfer = f(row["H_transfer"])
        e15 = abs(sdv15 - f(row["d_interpolated_transfer"]))
        e16 = abs(sdv16 - h_transfer)
        max_sdv15 = max(max_sdv15, e15)
        max_sdv16 = max(max_sdv16, e16)
        h_values.append(sdv16)
        if e15 > TOL:
            failures.append(f"element/ip {row['element']}/{row['ip']} SDV15 error {e15}")
        if e16 > TOL:
            failures.append(f"element/ip {row['element']}/{row['ip']} SDV16 error {e16}")
        if sdv16 < h_transfer - 1.0e-10:
            failures.append(f"element/ip {row['element']}/{row['ip']} H decreased")
    if len(nodes) != len(target_nodes):
        failures.append("target-node coverage is not 100%")
    if len(ips) != len(target_ips):
        failures.append("target element/IP coverage is not 100%")
    if len(set(round(v, 14) for v in node_values)) <= 1:
        failures.append("nodal d appears uniformly/default overwritten")
    if len(set(round(v, 14) for v in h_values)) <= 1:
        failures.append("history H appears uniformly/default overwritten")

    status = {
        "classification": "stage_d2a_state_ingestion_pass" if not failures else "stage_d2a_state_ingestion_fail",
        "D2A_ok": not failures,
        "job_id": job_id,
        "solver_exit": 0,
        "odb_readable": True,
        "target_node_coverage": len(nodes) / float(len(target_nodes)) if target_nodes else 0.0,
        "target_ip_coverage": len(ips) / float(len(target_ips)) if target_ips else 0.0,
        "max_nodal_d_error": max_node,
        "max_sdv15_interpolation_error": max_sdv15,
        "max_sdv16_H_error": max_sdv16,
        "tolerance": TOL,
        "failures": failures,
    }
    (out_dir / "D2A_STATE_INGESTION_STATUS.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = [
        "# D2A State Routing Report",
        "",
        f"Classification: `{status['classification']}`",
        "",
        f"- Job: `{job_id}`",
        f"- Target-node coverage: `{status['target_node_coverage']}`",
        f"- Target element/IP coverage: `{status['target_ip_coverage']}`",
        f"- Maximum nodal d error: `{max_node}`",
        f"- Maximum SDV15 interpolation error: `{max_sdv15}`",
        f"- Maximum SDV16/H error: `{max_sdv16}`",
        f"- Failures: `{len(failures)}`",
        "",
        "D2A verifies transfer ingestion only; it is not a fracture response benchmark.",
        "",
    ]
    (out_dir / "D2A_STATE_ROUTING_REPORT.md").write_text("\n".join(report), encoding="utf-8", newline="\n")
    if not failures:
        (out_dir / "D2A.ok").write_text("", encoding="utf-8")
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=Path("models/state_transfer/d2_tiny_transfer"))
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--job-id", default="not_submitted")
    parser.add_argument("--static-only", action="store_true")
    args = parser.parse_args()
    package = args.package
    static_status = static_validate(package)
    if args.static_only:
        print(json.dumps(static_status, indent=2, sort_keys=True))
        return 0
    if args.out_dir is None:
        raise SystemExit("--out-dir is required unless --static-only is used")
    status = extracted_validate(package, args.out_dir, args.job_id)
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["D2A_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
