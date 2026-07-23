#!/usr/bin/env python3
"""Generate the D3A3-R2 runtime H-state file used by UEXTERNALDB."""

import argparse
import csv
import hashlib
import json
from pathlib import Path


EXPECTED_ELEMENTS = 6400
EXPECTED_IPS = 4
EXPECTED_RECORDS = EXPECTED_ELEMENTS * EXPECTED_IPS


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/package/D3_TRANSFERRED_IP_H.csv"))
    parser.add_argument("--out", type=Path, default=Path("models/state_transfer/d3_interrupted_transfer/executable/d3_transfer_h.dat"))
    parser.add_argument("--manifest", type=Path, default=Path("models/state_transfer/d3_interrupted_transfer/executable/D3_TRANSFER_RUNTIME_MANIFEST.json"))
    args = parser.parse_args()

    with args.input.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows.sort(key=lambda row: (int(row["element"]), int(row["integration_point"])))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(
                f"{int(row['element'])} {int(row['integration_point'])} "
                f"{float(row['H']):.17e}\n"
            )

    manifest = {
        "classification": "stage_d3a3_r2_runtime_h_state_generated",
        "source_csv": str(args.input),
        "runtime_state_file": str(args.out),
        "records": len(rows),
        "expected_records": EXPECTED_RECORDS,
        "elements": EXPECTED_ELEMENTS,
        "integration_points_per_element": EXPECTED_IPS,
        "sha256": sha256(args.out),
        "format": "three whitespace-separated columns without header: element integration_point H",
        "sorted_by": ["element", "integration_point"],
    }
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
