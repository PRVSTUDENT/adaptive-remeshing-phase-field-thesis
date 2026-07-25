#!/usr/bin/env python3
"""Parse P3-SM1R baseline callbacks and documented GETRANK events."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


BASE_MARKERS = (
    "P3SM0_UEXTERNALDB_LOP0",
    "P3SM0_UEL_OBSERVED",
    "P3SM0_UMAT_OBSERVED",
    "P3SM0_UEXTERNALDB_END",
)
BEFORE = "P3SM1R_BEFORE_GETRANK"
AFTER = "P3SM1R_AFTER_GETRANK"
MARKERS = BASE_MARKERS + (BEFORE, AFTER)


def parse(path: Path) -> dict[str, object]:
    raw = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    counts = {marker: raw.count(marker) for marker in MARKERS}
    returned = []
    events = []
    for line_number, line in enumerate(raw.splitlines(), 1):
        for marker in MARKERS:
            if marker in line:
                process_id = ""
                if marker == AFTER:
                    tail = line.split(marker, 1)[1].strip().split()
                    if tail:
                        try:
                            process_id = int(tail[0])
                            returned.append(process_id)
                        except ValueError:
                            pass
                events.append({"line": line_number, "marker": marker,
                               "process_id": process_id})
    before_count = counts[BEFORE]
    after_count = counts[AFTER]
    return {
        "classification": "stage_p3sm1r_callback_log_parsed",
        "counts": counts,
        "observed": {marker: counts[marker] > 0 for marker in MARKERS},
        "before_count": before_count,
        "after_count": after_count,
        "returned_process_ids": returned,
        "unique_process_ids": sorted(set(returned)),
        "unmatched_before_calls": max(0, before_count - after_count),
        "before_after_count_mismatch": before_count != after_count,
        "signal_11_present": "signal 11" in raw.lower() or "segmentation violation" in raw.lower(),
        "last_marker": events[-1]["marker"] if events else "",
        "events": events,
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
        writer = csv.DictWriter(
            handle, fieldnames=("line", "marker", "process_id"), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(result["events"])
    print("p3sm1r_callback_parse_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
