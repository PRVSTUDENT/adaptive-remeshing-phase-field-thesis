#!/usr/bin/env python3
"""Validate one Stage-F8 minimal patch result without changing its evidence."""
import argparse
import json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--summary", type=Path, required=True)
    p.add_argument("--role", choices=("baseline", "candidate"), required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    data = json.loads(args.summary.read_text())
    if args.role == "baseline":
        classification = (
            "minimal_baseline_local_healing_reproduced"
            if data["strict_negative_sdv15"] else
            "minimal_baseline_local_healing_not_reproduced"
        )
        passed = True
    else:
        passed = (
            data["minimum_delta_sdv15"] >= -1.0e-8
            and data["minimum_delta_sdv16"] >= -1.0e-10
        )
        classification = (
            "irreversibility_candidate_qualified_minimal_model"
            if passed else "irreversibility_candidate_inconclusive"
        )
    result = {
        "role": args.role,
        "classification": classification,
        "acceptance_passed": passed,
        "precision_policy_sdv15": -1.0e-8,
        "history_policy_sdv16": -1.0e-10,
        "summary": data,
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    json.loads(args.output.read_text())
    return 0 if passed else 20


if __name__ == "__main__":
    raise SystemExit(main())

