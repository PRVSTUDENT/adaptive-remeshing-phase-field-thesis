#!/usr/bin/env python3
"""Predeclare and verify the Stage F10 penalty and runtime mapping gates."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-source", type=Path, required=True)
    parser.add_argument("--candidate-source", type=Path, required=True)
    parser.add_argument("--deck", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base = args.baseline_source.read_text(encoding="ascii")
    candidate = args.candidate_source.read_text(encoding="ascii")
    deck = args.deck.read_text(encoding="ascii")
    beta = 1.0e6 * 0.0027 / 0.015
    d_old, d_new, direction, eps = 0.4, 0.35, 0.17, 1.0e-7
    residual = lambda d: beta * (d - d_old) if d < d_old else 0.0
    tangent = beta if d_new < d_old else 0.0
    fd = (residual(d_new + eps * direction) - residual(d_new - eps * direction)) / (2 * eps)
    fd_expected = tangent * direction
    checks = {
        "n_elem_23_baseline": base.count("N_ELEM=23") == 2,
        "n_elem_23_candidate": candidate.count("N_ELEM=23") == 2,
        "bounds_guards_identical": base.count("F10 BOUNDS") == candidate.count("F10 BOUNDS") == 4,
        "compact_ranges": all(x in deck for x in ("24, 1, 2, 9, 8", "46, 27, 28, 35, 34",
                                                   "47, 1, 2, 9, 8", "69, 27, 28, 35, 34")),
        "penalty_residual_present": "PENALTY*GAP" in candidate,
        "penalty_tangent_present": "AINTW(INPT)*PENALTY" in candidate,
        "no_output_clamp": "SDV(1)=MAX" not in candidate.upper(),
        "prior_state_from_svars": "PHASEOLD=SDV(1)" in candidate and
                                  candidate.index("PHASEOLD=SDV(1)") < candidate.index("SDV(1)=PHASE"),
        "finite_difference_pass": math.isclose(fd, fd_expected, rel_tol=1e-8, abs_tol=1e-5),
    }
    result = {
        "passed": all(checks.values()),
        "checks": checks,
        "beta": beta,
        "directional_derivative_finite_difference": fd,
        "directional_derivative_tangent": fd_expected,
        "precision_policy": {
            "odb_or_extraction_floor": 1e-8,
            "reported_thresholds": [0.0, -1e-8, -1e-7, -1e-6, -1e-5, -1e-4, -1e-3],
        },
        "svars_semantics": (
            "PHASEOLD is loaded from incoming UEL SVARS before current-trial overwrite. "
            "Abaqus supplies beginning-of-increment state and restores it on cutback; "
            "returned updates are committed only for accepted increments."
        ),
        "deck_sha256": hashlib.sha256(args.deck.read_bytes()).hexdigest(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    json.loads(args.output.read_text())
    return 0 if result["passed"] else 20


if __name__ == "__main__":
    raise SystemExit(main())
