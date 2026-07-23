#!/usr/bin/env python3
"""Sparse assembly smoke for the D3A3-R3 qualified postprocessing interpreter.

Assembles the production 6601-node phase system using the exact D3A4
quadrature/assembly path and transferred IP history from package_compatible_r1.
No active-set solve is performed.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.solve_d3a4_phase_compatibility import (  # noqa: E402
    assemble,
    load_mesh,
)

EXPECTED_NODES = 6601
EXPECTED_ELEMENTS = 6400
EXPECTED_IPS = 25600


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_transferred_h(package_dir: Path):
    path = package_dir / "D3_TRANSFERRED_IP_H.csv"
    rows = read_csv(path)
    h = {}
    for row in rows:
        key = (int(row["element"]), int(row["integration_point"]))
        h[key] = float(row["H"])
    return h


def all_finite_sparse(matrix):
    data = np.asarray(matrix.data, dtype=float)
    if data.size == 0:
        return True
    return bool(np.all(np.isfinite(data)))


def run(model_dir: Path, package_dir: Path, out: Path):
    nodes, elements = load_mesh(model_dir)
    h_by_ip = load_transferred_h(package_dir)
    labels, _index, k, f, assembly = assemble(nodes, elements, h_by_ip)

    failures = []
    if len(labels) != EXPECTED_NODES:
        failures.append("nodes = %s expected %s" % (len(labels), EXPECTED_NODES))
    if len(elements) != EXPECTED_ELEMENTS:
        failures.append("elements = %s expected %s" % (len(elements), EXPECTED_ELEMENTS))
    if assembly["integration_points"] != EXPECTED_IPS:
        failures.append(
            "integration_points = %s expected %s"
            % (assembly["integration_points"], EXPECTED_IPS)
        )
    if assembly["non_positive_detJ"] != 0:
        failures.append("non_positive_detJ = %s" % assembly["non_positive_detJ"])
    if k.shape != (EXPECTED_NODES, EXPECTED_NODES):
        failures.append("matrix shape = %s expected (%s, %s)" % (k.shape, EXPECTED_NODES, EXPECTED_NODES))
    if len(f) != EXPECTED_NODES:
        failures.append("rhs length = %s expected %s" % (len(f), EXPECTED_NODES))
    if not all_finite_sparse(k):
        failures.append("matrix contains non-finite values")
    if not bool(np.all(np.isfinite(f))):
        failures.append("rhs contains non-finite values")
    if len(h_by_ip) != EXPECTED_IPS:
        failures.append("loaded H records = %s expected %s" % (len(h_by_ip), EXPECTED_IPS))

    status = {
        "classification": (
            "stage_d3a3_r3_postpython_assembly_pass"
            if not failures
            else "stage_d3a3_r3_postpython_assembly_fail"
        ),
        "sparse_assembly_pass": not failures,
        "failures": failures,
        "nodes": len(labels),
        "elements": len(elements),
        "integration_points": int(assembly["integration_points"]),
        "non_positive_detJ": int(assembly["non_positive_detJ"]),
        "matrix_shape": [int(k.shape[0]), int(k.shape[1])],
        "matrix_nnz": int(k.nnz),
        "rhs_length": int(len(f)),
        "matrix_all_finite": all_finite_sparse(k),
        "rhs_all_finite": bool(np.all(np.isfinite(f))),
        "loaded_H_records": len(h_by_ip),
        "history_source": str(package_dir / "D3_TRANSFERRED_IP_H.csv"),
        "assembly": "scripts.state_transfer.solve_d3a4_phase_compatibility.assemble",
        "solver_executed": False,
        "active_set_solve": False,
        "frobenius_norm_proxy": float(math.sqrt(float(np.sum(np.asarray(k.data, dtype=float) ** 2)))),
    }
    write_json(out, status)
    print(json.dumps(status, indent=2, sort_keys=True))
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("models/state_transfer/d3_interrupted_transfer"),
    )
    parser.add_argument(
        "--package-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/package_compatible_r1"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "runs/hpc/stage_d3/interrupted_transfer/r3_postpython_environment/"
            "D3A3_R3_POSTPYTHON_ASSEMBLY.json"
        ),
    )
    args = parser.parse_args()
    status = run(args.model_dir, args.package_dir, args.out)
    return 0 if status["sparse_assembly_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
