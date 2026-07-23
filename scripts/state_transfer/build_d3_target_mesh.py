#!/usr/bin/env python3
"""Build the deterministic D3A2 nonmatching target mesh files."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.build_d3_target_transfer import build_target_mesh, target_ip_rows, write_csv, write_mesh_files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=Path("models/state_transfer/d3_interrupted_transfer"))
    parser.add_argument("--nx", type=int, default=80)
    parser.add_argument("--ny", type=int, default=80)
    args = parser.parse_args()

    nodes, elements = build_target_mesh(args.nx, args.ny)
    nodes_by_label = {int(row["node"]): (float(row["x"]), float(row["y"])) for row in nodes}
    ips = target_ip_rows(nodes_by_label, elements)
    write_mesh_files(args.model_dir, nodes, elements)
    write_csv(
        args.model_dir / "target" / "target_ip_quadrature.csv",
        ["element", "integration_point", "x", "y", "gauss_xi", "gauss_eta", "gauss_weight", "detJ", "jacobian_weight"],
        ips,
    )
    status = {
        "classification": "stage_d3a2_target_mesh_built",
        "model_dir": str(args.model_dir),
        "nodes": len(nodes),
        "physical_elements": len(elements),
        "integration_points": len(ips),
    }
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
