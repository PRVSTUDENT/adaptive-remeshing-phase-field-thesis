#!/usr/bin/env python3
"""Generate the D3 transfer-table include from the D3A2 package CSV."""

import argparse
import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.build_d3_target_transfer import write_transfer_table


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ip-csv", type=Path, default=Path("runs/hpc/stage_d3/interrupted_transfer/package/D3_TRANSFERRED_IP_H.csv"))
    parser.add_argument("--out", type=Path, default=Path("models/state_transfer/d3_interrupted_transfer/executable/d3_transfer_table.inc"))
    args = parser.parse_args()
    with args.ip_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    write_transfer_table(args.out, rows)
    status = {
        "classification": "stage_d3a2_transfer_table_generated",
        "rows": len(rows),
        "out": str(args.out),
    }
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
