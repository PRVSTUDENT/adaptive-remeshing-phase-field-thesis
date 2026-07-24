#!/usr/bin/env python3
"""Parse bounded Stage P Fortran diagnostics from an Abaqus message file."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


FIELDS = [
    "event",
    "variable_id",
    "operation_id",
    "routine_id",
    "shared_index",
    "element",
    "integration_point",
    "rank",
    "thread",
    "step",
    "increment",
    "initialization",
    "detail",
]


def integer_tokens(parts: list[str]) -> list[int]:
    values: list[int] = []
    for part in parts:
        try:
            values.append(int(part))
        except ValueError:
            continue
    return values


def parse(path: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows: list[dict[str, object]] = []
    callbacks = {"UEXTERNALDB": False, "UEL": False, "UMAT": False}
    threads: set[int] = set()
    ranks: set[int] = set()
    conflicts = 0
    final_counts: list[dict[str, int]] = []

    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        text = raw.strip()
        if "P2_INIT" in text:
            values = integer_tokens(text.split())
            rank, thread = values[-2:]
            callbacks["UEXTERNALDB"] = True
            ranks.add(rank)
            threads.add(thread)
            rows.append({"event": "initialization", "rank": rank, "thread": thread, "detail": text})
        elif "P2_FIRST" in text:
            callbacks["UEL"] |= "UEL_ENTER" in text
            callbacks["UMAT"] |= "UMAT_ENTER" in text
            values = integer_tokens(text.split())
            if len(values) >= 6:
                rank, thread, element, ip, step, increment = values[-6:]
                ranks.add(rank)
                threads.add(thread)
                rows.append(
                    {
                        "event": "first_callback",
                        "element": element,
                        "integration_point": ip,
                        "rank": rank,
                        "thread": thread,
                        "step": step,
                        "increment": increment,
                        "detail": text,
                    }
                )
        elif "P3_ACCESS" in text:
            values = integer_tokens(text.split())
            if len(values) >= 11:
                var_id, op_id, routine_id, index, element, ip, rank, thread, step, increment, init = values[-11:]
                ranks.add(rank)
                threads.add(thread)
                rows.append(
                    {
                        "event": "shared_access",
                        "variable_id": var_id,
                        "operation_id": op_id,
                        "routine_id": routine_id,
                        "shared_index": index,
                        "element": element,
                        "integration_point": ip,
                        "rank": rank,
                        "thread": thread,
                        "step": step,
                        "increment": increment,
                        "initialization": init,
                        "detail": text,
                    }
                )
        elif "P3_CONFLICT" in text:
            conflicts += 1
            rows.append({"event": "conflict", "detail": text})
        elif "P2_FINAL" in text:
            values = integer_tokens(text.split())
            if len(values) >= 4:
                rank, thread, uel_count, umat_count = values[-4:]
                final_counts.append(
                    {"rank": rank, "thread": thread, "UEL": uel_count, "UMAT": umat_count}
                )
        elif "P3_FINAL_CONFLICTS" in text:
            values = integer_tokens(text.split())
            if values:
                conflicts = max(conflicts, values[-1])

    summary = {
        "classification": "stage_p3_diagnostic_log_parsed",
        "callbacks": callbacks,
        "ranks": sorted(ranks),
        "threads": sorted(threads),
        "shared_access_records": sum(row.get("event") == "shared_access" for row in rows),
        "initialization_write_records": sum(
            row.get("event") == "shared_access"
            and row.get("variable_id") == 4
            and row.get("operation_id") == 2
            and row.get("initialization") == 1
            for row in rows
        ),
        "conflicting_shared_writes": conflicts,
        "final_call_counts": final_counts,
    }
    return rows, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--msg", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    rows, summary = parse(args.msg)
    args.events.parent.mkdir(parents=True, exist_ok=True)
    with args.events.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
