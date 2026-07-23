#!/usr/bin/env python3
"""Audit the D3A2 target split-notch topology."""

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.build_d3_target_transfer import target_ip_rows  # noqa: E402


TOL = 1.0e-10
NOTCH_X0 = -0.5
NOTCH_TIP_X = 0.0


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: List[str], rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def same(a: float, b: float, tol: float = TOL) -> bool:
    return abs(a - b) <= tol


def validate(target_dir: Path, out_dir: Path) -> Dict[str, object]:
    nodes = read_csv(target_dir / "target_nodes.csv")
    elements = read_csv(target_dir / "target_elements.csv")
    nodes_by_label = {int(row["node"]): (float(row["x"]), float(row["y"])) for row in nodes}
    labels_by_coord: Dict[Tuple[float, float], List[int]] = defaultdict(list)
    for label, (x, y) in nodes_by_label.items():
        labels_by_coord[(round(x, 12), round(y, 12))].append(label)

    failures: List[str] = []
    pair_rows: List[Dict[str, object]] = []
    notch_xs = sorted(
        x for x, y in labels_by_coord
        if same(y, 0.0) and NOTCH_X0 - TOL <= x < NOTCH_TIP_X - TOL
    )
    for x in notch_xs:
        labels = sorted(labels_by_coord[(round(x, 12), 0.0)])
        if len(labels) != 2:
            failures.append(f"notch face coordinate x={x} has {len(labels)} labels, expected 2")
            continue
        pair_rows.append(
            {
                "x": x,
                "y": 0.0,
                "upper_node": labels[0],
                "lower_node": labels[1],
                "coincident": True,
            }
        )

    tip_labels = sorted(labels_by_coord.get((round(NOTCH_TIP_X, 12), 0.0), []))
    if len(tip_labels) != 1:
        failures.append(f"notch tip at x=0 has {len(tip_labels)} labels, expected 1 shared label")
    if not notch_xs:
        failures.append("no duplicated open-notch face coordinates found")
        notch_length = None
    else:
        notch_length = NOTCH_TIP_X - min(notch_xs)
        if abs(notch_length - 0.5) > TOL:
            failures.append(f"notch length is {notch_length}, expected 0.5")

    crossing_rows: List[Dict[str, object]] = []
    duplicate_pairs = {float(row["x"]): (int(row["upper_node"]), int(row["lower_node"])) for row in pair_rows}
    duplicate_nodes = {node for pair in duplicate_pairs.values() for node in pair}
    for elem in elements:
        label = int(elem["element"])
        conn = [int(elem[f"n{i}"]) for i in range(1, 5)]
        duplicate_in_elem = [node for node in conn if node in duplicate_nodes]
        for x, (upper, lower) in duplicate_pairs.items():
            if upper in conn and lower in conn:
                crossing_rows.append(
                    {
                        "element": label,
                        "x": x,
                        "upper_node": upper,
                        "lower_node": lower,
                        "connectivity": " ".join(str(n) for n in conn),
                        "reason": "element contains both coincident notch-face labels",
                    }
                )
        # Guard against an element using notch-face nodes from both sides through
        # different coordinates on the open seam.
        side_by_node = {}
        for x, (upper, lower) in duplicate_pairs.items():
            side_by_node[upper] = "upper"
            side_by_node[lower] = "lower"
        sides = {side_by_node[node] for node in duplicate_in_elem if node in side_by_node}
        if len(sides) > 1:
            crossing_rows.append(
                {
                    "element": label,
                    "x": "",
                    "upper_node": "",
                    "lower_node": "",
                    "connectivity": " ".join(str(n) for n in conn),
                    "reason": "element mixes upper and lower open-notch face nodes",
                }
            )

    if crossing_rows:
        failures.append(f"{len(crossing_rows)} elements cross or mix open notch faces")

    ips = target_ip_rows(nodes_by_label, elements)  # type: ignore[arg-type]
    detj_values = [float(row["detJ"]) for row in ips]
    non_positive = sum(1 for value in detj_values if value <= 0.0 or not math.isfinite(value))
    if non_positive:
        failures.append(f"{non_positive} target integration points have non-positive/non-finite detJ")

    out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(
        out_dir / "D3_TARGET_NOTCH_NODE_PAIRS.csv",
        ["x", "y", "upper_node", "lower_node", "coincident"],
        pair_rows,
    )
    write_csv(
        out_dir / "D3_TARGET_NOTCH_CROSSING_ELEMENTS.csv",
        ["element", "x", "upper_node", "lower_node", "connectivity", "reason"],
        crossing_rows,
    )
    status = {
        "classification": "stage_d3a2_target_notch_topology_pass" if not failures else "stage_d3a2_target_notch_topology_fail",
        "target_notch_topology_ok": not failures,
        "notch_start_x": NOTCH_X0,
        "notch_tip_x": NOTCH_TIP_X,
        "notch_length": notch_length,
        "duplicated_open_face_node_pairs": len(pair_rows),
        "tip_node_labels": tip_labels,
        "upper_and_lower_faces_have_distinct_node_labels": all(row["upper_node"] != row["lower_node"] for row in pair_rows),
        "crossing_element_count": len(crossing_rows),
        "minimum_detJ": min(detj_values),
        "maximum_detJ": max(detj_values),
        "non_positive_detJ_count": non_positive,
        "failures": failures,
    }
    (out_dir / "D3_TARGET_NOTCH_TOPOLOGY.json").write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(status, indent=2, sort_keys=True))
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-dir", type=Path, default=Path("models/state_transfer/d3_interrupted_transfer/target"))
    parser.add_argument("--out-dir", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/package"))
    args = parser.parse_args()
    status = validate(args.target_dir, args.out_dir)
    return 0 if status["target_notch_topology_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
