#!/usr/bin/env python3
"""Parse the frozen P3-T4 callback, access, ownership and conflict protocol."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


FIELDS = (
    "event", "callback", "variable_id", "operation", "routine",
    "physical_index", "element", "integration_point", "rank", "thread",
    "step", "increment", "initialization", "active_rank", "active_thread",
    "detail",
)
BASE_MARKERS = (
    "P3SM0_UEXTERNALDB_LOP0", "P3SM0_UEL_OBSERVED",
    "P3SM0_UMAT_OBSERVED", "P3SM0_UEXTERNALDB_END",
)


def ints(text: str) -> list[int]:
    values = []
    for token in text.split():
        try:
            values.append(int(token))
        except ValueError:
            pass
    return values


def parse(path: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    raw = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    rows: list[dict[str, object]] = []
    ranks: set[int] = set()
    threads: set[int] = set()
    callback_threads: dict[str, set[int]] = {"UEL": set(), "UMAT": set()}
    begins: Counter[tuple[int, int]] = Counter()
    ends: Counter[tuple[int, int]] = Counter()
    final_counts: list[dict[str, int]] = []
    conflicts = duplicates = ownership = 0

    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if "P3T4_FIRST_CALLBACK" in line:
            values = ints(line)
            if len(values) >= 6:
                rank, thread, element, ip, step, increment = values[-6:]
                callback = "UEL" if "UEL_ENTER" in line else "UMAT"
                ranks.add(rank)
                threads.add(thread)
                callback_threads[callback].add(thread)
                rows.append({"event": "first_callback", "callback": callback,
                             "element": element, "integration_point": ip,
                             "rank": rank, "thread": thread, "step": step,
                             "increment": increment, "detail": line})
        elif "P3T4_ACCESS" in line:
            values = ints(line)
            if len(values) >= 11:
                var, op, routine, index, element, ip, rank, thread, step, inc, init = values[-11:]
                ranks.add(rank)
                threads.add(thread)
                rows.append({"event": "access", "variable_id": var,
                             "operation": "read" if op == 1 else "write",
                             "routine": "UEL" if routine == 1 else "UMAT",
                             "physical_index": index, "element": element,
                             "integration_point": ip, "rank": rank,
                             "thread": thread, "step": step, "increment": inc,
                             "initialization": init, "detail": line})
        elif "P3T4_BEGIN_WRITE" in line:
            values = ints(line)
            if len(values) >= 10:
                var, routine, index, element, ip, rank, thread, step, inc, init = values[-10:]
                begins[(var, index)] += 1
                ranks.add(rank)
                threads.add(thread)
                rows.append({"event": "begin_write", "variable_id": var,
                             "routine": "UEL" if routine == 1 else "UMAT",
                             "physical_index": index, "element": element,
                             "integration_point": ip, "rank": rank,
                             "thread": thread, "step": step, "increment": inc,
                             "initialization": init, "detail": line})
        elif "P3T4_END_WRITE" in line:
            values = ints(line)
            if len(values) >= 4:
                var, index, rank, thread = values[-4:]
                ends[(var, index)] += 1
                ranks.add(rank)
                threads.add(thread)
                rows.append({"event": "end_write", "variable_id": var,
                             "physical_index": index, "rank": rank,
                             "thread": thread, "detail": line})
        elif "P3T4_DUPLICATE_INIT" in line:
            duplicates += 1
            rows.append({"event": "duplicate_initialization", "detail": line})
        elif "P3T4_OWNERSHIP_CHANGE" in line:
            ownership += 1
            rows.append({"event": "ownership_change", "detail": line})
        elif "P3T4_CONFLICT_" in line:
            conflicts += 1
            kind = ("read_during_write" if "READ_DURING_WRITE" in line
                    else "write_during_write")
            rows.append({"event": "conflict_" + kind, "detail": line})
        elif "P3T4_FINAL_THREAD_COUNTS" in line:
            values = ints(line)
            if len(values) >= 4:
                rank, thread, uel, umat = values[-4:]
                ranks.add(rank)
                threads.add(thread)
                final_counts.append({"rank": rank, "thread": thread,
                                     "UEL": uel, "UMAT": umat})

    unmatched = sum(abs(begins[key] - ends[key]) for key in begins.keys() | ends.keys())
    summary = {
        "classification": "stage_p3t4_diagnostics_parsed",
        "base_markers": {marker: raw.count(marker) for marker in BASE_MARKERS},
        "ranks": sorted(ranks),
        "threads": sorted(threads),
        "callback_threads": {key: sorted(value) for key, value in callback_threads.items()},
        "access_records": sum(row.get("event") == "access" for row in rows),
        "begin_write_records": sum(begins.values()),
        "end_write_records": sum(ends.values()),
        "unmatched_begin_end_records": unmatched,
        "initialization_write_count": sum(
            row.get("event") == "begin_write"
            and row.get("initialization") == 1
            and row.get("variable_id") == 4
            for row in rows
        ),
        "duplicate_initialization_count": duplicates,
        "concurrent_conflict_count": conflicts,
        "ownership_change_count": ownership,
        "final_thread_counts": final_counts,
        "signal_11_present": (
            "signal 11" in raw.lower() or "segmentation violation" in raw.lower()
        ),
    }
    return rows, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--msg", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    rows, summary = parse(args.msg)
    with args.events.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
