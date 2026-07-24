#!/usr/bin/env python3
"""Parse bounded P3-SM0 constant callback markers from the Abaqus message log."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


MARKERS = (
    "P3SM0_UEXTERNALDB_LOP0",
    "P3SM0_UEL_OBSERVED",
    "P3SM0_UMAT_OBSERVED",
    "P3SM0_UEXTERNALDB_END",
)


def parse(path: Path) -> dict[str, object]:
    raw = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    counts = {marker: raw.count(marker) for marker in MARKERS}
    return {
        "classification": "stage_p3sm0_callback_log_parsed",
        "counts": counts,
        "observed": {marker: counts[marker] > 0 for marker in MARKERS},
        "signal_11_present": "signal 11" in raw.lower() or "segmentation violation" in raw.lower(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--msg", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    args = parser.parse_args()
    result = parse(args.msg)
    args.summary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with args.events.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("marker", "count"), lineterminator="\n")
        writer.writeheader()
        for marker in MARKERS:
            writer.writerow({"marker": marker, "count": result["counts"][marker]})
    print("p3sm0_callback_parse_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
