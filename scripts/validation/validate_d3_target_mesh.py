#!/usr/bin/env python3
"""Validate the D3A2 deterministic target mesh."""

import argparse
import csv
import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.build_d3_target_transfer import target_ip_rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-dir", type=Path, default=Path("models/state_transfer/d3_interrupted_transfer/target"))
    parser.add_argument("--out", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/package/D3_TARGET_MESH_VALIDATION.json"))
    args = parser.parse_args()

    nodes = read_csv(args.target_dir / "target_nodes.csv")
    elements = read_csv(args.target_dir / "target_elements.csv")
    nodes_by_label = {int(row["node"]): (float(row["x"]), float(row["y"])) for row in nodes}
    ips = target_ip_rows(nodes_by_label, elements)  # type: ignore[arg-type]
    detj = [float(row["detJ"]) for row in ips]
    conn = [tuple(int(row[f"n{i}"]) for i in range(1, 5)) for row in elements]
    failures: list[str] = []
    if len(elements) < 5000 or len(elements) > 8000:
        failures.append(f"physical element count outside preferred range: {len(elements)}")
    if len(elements) >= 12064:
        failures.append("target element count is not less than H1=12064")
    if len(elements) == 3930:
        failures.append("target element count matches H0")
    if len(conn) != len(set(conn)):
        failures.append("duplicate target connectivity")
    if not any(abs(float(row["y"])) <= 1.0e-15 for row in nodes):
        failures.append("exact y=0 node line is absent")
    if any((not math.isfinite(v)) or v <= 0.0 for v in detj):
        failures.append("target has non-positive or non-finite detJ")
    status = {
        "classification": "stage_d3a2_target_mesh_validation_pass" if not failures else "stage_d3a2_target_mesh_validation_fail",
        "target_mesh_ok": not failures,
        "node_count": len(nodes),
        "physical_elements": len(elements),
        "integration_points": len(ips),
        "minimum_detJ": min(detj),
        "maximum_detJ": max(detj),
        "non_positive_detJ_count": sum(1 for value in detj if value <= 0.0),
        "y0_line_node_count": sum(1 for row in nodes if abs(float(row["y"])) <= 1.0e-15),
        "failures": failures,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
