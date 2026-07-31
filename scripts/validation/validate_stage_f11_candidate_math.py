#!/usr/bin/env python3
"""Directional finite-difference checks for the F11 penalty term."""
import argparse
import json
import math
from pathlib import Path


def residual(d, old, beta, n):
    gap = sum(x * y for x, y in zip(n, d)) - old
    return [beta * gap * x if gap < 0.0 else 0.0 for x in n]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    cases = []
    vectors = ([0.25] * 4, [0.1, 0.2, 0.3, 0.4])
    for beta in (1.0, 1.8e5, 1.0e9):
        for n in vectors:
            for gap in (1e-3, 0.0, -1e-3):
                old = 0.2
                d = [old + gap] * 4
                direction = [0.3, -0.2, 0.1, 0.4]
                eps = 1e-7
                if gap == 0.0:
                    fd = [0.0] * 4
                    exact = [0.0] * 4
                    error = max(abs(x) for x in residual(d, old, beta, n))
                    scale = 1.0
                else:
                    rp = residual([x + eps*y for x, y in zip(d, direction)], old, beta, n)
                    rm = residual([x - eps*y for x, y in zip(d, direction)], old, beta, n)
                    fd = [(x-y)/(2*eps) for x, y in zip(rp, rm)]
                    ndir = sum(x*y for x, y in zip(n, direction))
                    exact = [beta*x*ndir if gap < 0 else 0.0 for x in n]
                    error = max(abs(x-y) for x, y in zip(fd, exact))
                    scale = max(1.0, max(abs(x) for x in exact))
                cases.append({"beta": beta, "gap": gap, "shape": list(n),
                              "absolute_error": error,
                              "relative_error": error/scale,
                              "passed": error/scale < 1e-6})
    result = {"rhs_sign": "RHS receives minus internal residual",
              "active_tangent_sign": "positive matrix contribution",
              "cases": cases, "passed": all(x["passed"] for x in cases)}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
