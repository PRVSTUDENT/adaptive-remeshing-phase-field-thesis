#!/usr/bin/env python3
"""
Production Runtime Trace Checker for M2STATE_FRACFIX_RESTART1R1R4.
Verifies that UEL emits startup records for all 4 production representative pairs in PK5 mesh.
"""

import sys
import re
from pathlib import Path

EXPECTED_REPRESENTATIVES = {
    2292: {"jtype": 1, "physidx": 2292, "role": "High-d Quad Phase"},
    7186: {"jtype": 2, "physidx": 2292, "role": "High-d Quad Mech"},
    100:  {"jtype": 1, "physidx": 100,  "role": "Low-d Quad Phase"},
    4994: {"jtype": 2, "physidx": 100,  "role": "Low-d Quad Mech"},
    1500: {"jtype": 1, "physidx": 1500, "role": "Transition Quad Phase"},
    6394: {"jtype": 2, "physidx": 1500, "role": "Transition Quad Mech"},
    4862: {"jtype": 3, "physidx": 4862, "role": "Tri Pair Phase"},
    9756: {"jtype": 4, "physidx": 4862, "role": "Tri Pair Mech"}
}

def check_trace_file(trace_path: Path) -> int:
    if not trace_path.exists():
        print(f"[RESTART_TRACE_CHECKER] ERROR: Trace file {trace_path} does not exist.")
        return 1

    lines = trace_path.read_text(encoding="utf-8", errors="replace").splitlines()
    found_reps = set()
    pattern = re.compile(r'\[INGEST_TRACE\] KSTEP=(\d+) KINC=(\d+) JELEM=\s*(\d+) JTYPE=(\d+) PHYSIDX=\s*(\d+)')

    for line in lines:
        match = pattern.search(line)
        if match:
            kstep = int(match.group(1))
            kinc = int(match.group(2))
            jelem = int(match.group(3))
            jtype = int(match.group(4))
            physidx = int(match.group(5))

            if kstep == 2 and kinc == 1 and jelem in EXPECTED_REPRESENTATIVES:
                exp = EXPECTED_REPRESENTATIVES[jelem]
                if jtype == exp["jtype"] and physidx == exp["physidx"]:
                    found_reps.add(jelem)

    missing = set(EXPECTED_REPRESENTATIVES.keys()) - found_reps
    if missing:
        print(f"[RESTART_TRACE_CHECKER] FAIL: Missing trace records for representatives: {sorted(list(missing))}")
        return 1

    print(f"[RESTART_TRACE_CHECKER] PASS: All {len(found_reps)} production representative elements traced cleanly.")
    return 0

if __name__ == "__main__":
    t_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("M2STATE_FRACFIX_RESTART1R1R4.trace")
    sys.exit(check_trace_file(t_path))
