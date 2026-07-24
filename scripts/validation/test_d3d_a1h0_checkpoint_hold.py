#!/usr/bin/env python3
"""Static and synthetic tests for D3D-A1H0 preparation."""

import csv
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.validation.validate_d3d_a1h0_checkpoint_hold import PASS, POSTFAIL, UPDATE, classify

EXE = ROOT / "models/state_transfer/d3_interrupted_transfer/executable_d3d_a1_checkpoint_hold_r1"
PACKAGE = ROOT / "runs/hpc/stage_d3/fracture_continuation/package_d3d_a1_checkpoint_r1"


def base():
    return {
        "phase_node_coverage": 6601, "history_coverage": 25600,
        "top_node_count": 81, "top_u2_error": 0.0, "top_rf": 1.0,
        "maximum_phase_drift": 0.0, "phase_decrease_violations": 0,
        "H_decrease_violations": 0, "relative_top_rf_change": 0.001,
        "relative_energy_change": 0.001, "free_residual_infinity_norm": 1e-12,
        "minimum_active_multiplier": -9e-9, "active_bound_error": 0.0,
        "state_reset": False, "spatial_variation_retained": True,
    }


def test_static():
    deck = (EXE / "D3D_A1H0_checkpoint_hold.inp").read_text(encoding="utf-8")
    assert deck.count("*Step,") == 2
    assert "INGEST_D3D_A1_CANDIDATE" in deck
    assert "D3D_A1_MECHANICAL_CHECKPOINT_EQUILIBRATION" in deck
    assert "RELEASE" not in deck.upper()
    assert "CONTINUATION" not in deck.upper()
    sections = deck.split("*Step,")[1:]
    for section in sections:
        fixed = 0
        for line in section.splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4 and parts[0].isdigit() and parts[1:3] == ["3", "3"]:
                fixed += 1
        assert fixed == 6601
    with (PACKAGE / "D3_ACTIVE_SET_BY_NODE.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    active = sum(str(r["active_lower_bound"]).lower() in ("true", "1", "yes") for r in rows)
    assert (active, len(rows) - active) == (6374, 227)
    package_h = [r["H"] for r in csv.DictReader((PACKAGE / "D3_TRANSFERRED_IP_H.csv").open(newline="", encoding="utf-8"))]
    runtime_h = [line.split()[2] for line in (EXE / "d3_transfer_h.dat").read_text(encoding="utf-8").splitlines()]
    assert len(package_h) == len(runtime_h) == 25600
    assert all(float(a) == float(b) for a, b in zip(package_h, runtime_h))
    r4 = ROOT / "models/state_transfer/d3_interrupted_transfer/executable_r4_compatible_r2/d3_transfer_uel.for"
    assert hashlib.sha256(r4.read_bytes()).digest() == hashlib.sha256((EXE / "d3_transfer_uel.for").read_bytes()).digest()


def test_classifications():
    good = base()
    assert classify(good)[0] == PASS
    update = base(); update["minimum_active_multiplier"] = -1.1e-8
    assert classify(update)[0] == UPDATE
    cases = {
        "phase coverage": ("phase_node_coverage", 6600),
        "H coverage": ("history_coverage", 25599),
        "phase drift": ("maximum_phase_drift", 2e-10),
        "H decrease": ("H_decrease_violations", 1),
        "RF discontinuity": ("relative_top_rf_change", 0.0101),
        "energy discontinuity": ("relative_energy_change", 0.0101),
        "free residual": ("free_residual_infinity_norm", 1.1e-8),
    }
    for name, (key, value) in cases.items():
        fixture = base(); fixture[key] = value
        assert classify(fixture)[0] == POSTFAIL, name


def main():
    test_static(); print("PASS test_static")
    test_classifications(); print("PASS test_classifications")
    print("D3D_A1H0_TESTS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
