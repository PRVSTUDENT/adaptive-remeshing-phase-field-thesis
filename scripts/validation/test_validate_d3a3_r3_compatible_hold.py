#!/usr/bin/env python3
"""Synthetic tests for D3A3-R3 strengthened scientific gates.

Proves that:
  - an active-node decrease fails
  - a lower-bound violation fails
  - a negative active multiplier fails
  - a valid fixture creates both markers
"""

from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scripts.validation.validate_d3a3_r3_compatible_hold as v  # noqa: E402


def write_csv(path: Path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def phase_fields():
    return [
        "node",
        "x",
        "y",
        "active_lower_bound",
        "d_lower_bound",
        "d_F0",
        "d_F1",
        "d_F2",
        "d_F3",
        "F3_minus_F1",
        "F3_minus_lower_bound",
    ]


def make_phase_rows(active_f3=0.2, free_f3=0.3, active_lb=0.2, free_lb=0.1):
    # node 1 active, node 2 free
    return [
        {
            "node": 1,
            "x": 0.0,
            "y": 0.0,
            "active_lower_bound": True,
            "d_lower_bound": active_lb,
            "d_F0": active_lb,
            "d_F1": active_lb,
            "d_F2": active_f3,
            "d_F3": active_f3,
            "F3_minus_F1": active_f3 - active_lb,
            "F3_minus_lower_bound": active_f3 - active_lb,
        },
        {
            "node": 2,
            "x": 1.0,
            "y": 0.0,
            "active_lower_bound": False,
            "d_lower_bound": free_lb,
            "d_F0": 0.25,
            "d_F1": 0.25,
            "d_F2": free_f3,
            "d_F3": free_f3,
            "F3_minus_F1": free_f3 - 0.25,
            "F3_minus_lower_bound": free_f3 - free_lb,
        },
    ]


def make_state_rows(n_ip):
    rows = []
    for tag in ["F1_equilibrated", "F3_release_last"]:
        for i in range(1, n_ip + 1):
            # Keep spatial variation on F3; limit phase adjustment to < 0.01.
            base = 0.20 + 0.01 * ((i - 1) % 2)
            sdv15 = base if tag == "F1_equilibrated" else base + 0.005
            rows.append({
                "frame_tag": tag,
                "element": (i - 1) // 4 + 1,
                "uel_integration_point": ((i - 1) % 4) + 1,
                "odb_sdv15": sdv15,
                "odb_sdv16": 1.0e-3 + 1.0e-5 * i,
            })
    return rows


def make_kkt(ok=True, min_mult=1.0e-6, free_res=1.0e-12, bound_err=0.0):
    return {
        "classification": (
            "stage_d3a3_r3_fixed_state_kkt_pass"
            if ok
            else "stage_d3a3_r3_fixed_state_needs_reprojection"
        ),
        "D3A3_R3_fixed_state_kkt_ok": ok,
        "failures": [] if ok else ["minimum active multiplier = %s" % min_mult],
        "free_set_residual_infinity_norm": free_res,
        "minimum_active_set_multiplier": min_mult,
        "active_node_bound_error": bound_err,
        "node_coverage": 2,
    }


def build_fixture(root: Path, phase_rows, kkt, n_ip=4, expected_nodes=2, expected_active=1, expected_free=1):
    target = root / "target"
    d3a4 = root / "d3a4"
    target.mkdir()
    d3a4.mkdir()

    write_csv(target / "D3A3_R3_PHASE_NODE_STATE_BY_FRAME.csv", phase_fields(), phase_rows)
    write_csv(
        target / "D3A3_R3_ACTIVE_NODE_STATE.csv",
        phase_fields(),
        [r for r in phase_rows if r["active_lower_bound"]],
    )
    write_csv(
        target / "D3A3_R3_FREE_NODE_STATE.csv",
        phase_fields(),
        [r for r in phase_rows if not r["active_lower_bound"]],
    )
    write_json(
        target / "D3A3_R3_LOWER_BOUND_AUDIT.json",
        {
            "classification": "stage_d3a3_r3_lower_bound_audit_pass",
            "all_nodes": expected_nodes,
            "active_nodes": expected_active,
            "free_nodes": expected_free,
            "missing_recovered_values": 0,
        },
    )
    write_json(target / "D3A3_R3_F1_KKT_METRICS.json", kkt)
    write_csv(
        target / "D3A3_R3_F1_RESIDUAL_BY_NODE.csv",
        ["node", "residual_Kd_minus_f"],
        [{"node": 1, "residual_Kd_minus_f": 0.0}, {"node": 2, "residual_Kd_minus_f": 0.0}],
    )

    transfer_rows = []
    for i in range(1, n_ip + 1):
        transfer_rows.append({
            "element": (i - 1) // 4 + 1,
            "integration_point": ((i - 1) % 4) + 1,
            "uel_integration_point": ((i - 1) % 4) + 1,
            "sdv15_error": 0.0,
            "sdv16_error": 0.0,
        })
    write_csv(
        target / "D3A3_TRANSFER_VS_ODB.csv",
        ["element", "integration_point", "uel_integration_point", "sdv15_error", "sdv16_error"],
        transfer_rows,
    )
    write_csv(
        target / "D3A3_STATE_BY_FRAME.csv",
        ["frame_tag", "element", "uel_integration_point", "odb_sdv15", "odb_sdv16"],
        make_state_rows(n_ip),
    )
    write_csv(
        target / "D3A3_RF_U_CORRECTED.csv",
        ["frame_tag", "top_node_count", "top_u2_mean", "top_u2_min", "top_u2_max", "top_rf2_sum"],
        [
            {
                "frame_tag": "F1_equilibrated",
                "top_node_count": 81,
                "top_u2_mean": v.CHECKPOINT_U2,
                "top_u2_min": v.CHECKPOINT_U2,
                "top_u2_max": v.CHECKPOINT_U2,
                "top_rf2_sum": 1.0,
            },
            {
                "frame_tag": "F3_release_last",
                "top_node_count": 81,
                "top_u2_mean": v.CHECKPOINT_U2,
                "top_u2_min": v.CHECKPOINT_U2,
                "top_u2_max": v.CHECKPOINT_U2,
                "top_rf2_sum": 0.99,
            },
        ],
    )
    write_json(
        target / "D3A3_RELEASE_JUMP.json",
        {
            "equilibrated_vs_released": {
                "H_decrease_violations": 0,
                "d_healing_violations": 0,
            }
        },
    )
    write_json(
        target / "D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json",
        {
            "frames": [
                {
                    "frame_tag": "F1_equilibrated",
                    "total_reconstructed_internal_energy": 1.0,
                    "missing_phase_node_values": 0,
                    "missing_sdv12_values": 0,
                    "missing_sdv13_values": 0,
                    "non_positive_detJ_count": 0,
                },
                {
                    "frame_tag": "F3_release_last",
                    "total_reconstructed_internal_energy": 0.99,
                    "missing_phase_node_values": 0,
                    "missing_sdv12_values": 0,
                    "missing_sdv13_values": 0,
                    "non_positive_detJ_count": 0,
                },
            ]
        },
    )
    write_csv(
        d3a4 / "D3A4_ACTIVE_SET_BY_NODE.csv",
        ["node", "x", "y", "active_lower_bound", "d_lb"],
        [
            {"node": 1, "x": 0.0, "y": 0.0, "active_lower_bound": True, "d_lb": 0.2},
            {"node": 2, "x": 1.0, "y": 0.0, "active_lower_bound": False, "d_lb": 0.1},
        ],
    )
    return target, d3a4


def run_case(name, phase_rows, kkt, expect_ok, expect_fail_token=None, n_ip=4):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Patch coverage expectations for the tiny synthetic mesh.
        old = (v.EXPECTED_NODES, v.EXPECTED_ACTIVE, v.EXPECTED_FREE, v.EXPECTED_IP)
        v.EXPECTED_NODES = 2
        v.EXPECTED_ACTIVE = 1
        v.EXPECTED_FREE = 1
        v.EXPECTED_IP = n_ip
        try:
            target, d3a4 = build_fixture(root, phase_rows, kkt, n_ip=n_ip)
            status = v.validate(target, d3a4)
            v.apply_status(target, status)
            ok = bool(status["D3A3_ok"])
            has_r3 = (target / "D3A3_R3.ok").exists()
            has_all = (target / "D3A3.ok").exists()
            if ok != expect_ok:
                raise AssertionError("%s: expected ok=%s got %s failures=%s" % (name, expect_ok, ok, status["failures"]))
            if expect_ok:
                if not has_r3 or not has_all:
                    raise AssertionError("%s: expected both markers" % name)
                text = (target / "D3A3_R3.ok").read_text(encoding="utf-8").strip()
                if text != v.PASS_CLASSIFICATION:
                    raise AssertionError("%s: marker text %r" % (name, text))
            else:
                if has_r3 or has_all:
                    raise AssertionError("%s: markers must not exist on failure" % name)
                if expect_fail_token is not None:
                    joined = " | ".join(status["failures"])
                    if expect_fail_token not in joined:
                        raise AssertionError("%s: expected failure token %r in %r" % (name, expect_fail_token, joined))
            print("PASS", name, "classification=", status["classification"])
        finally:
            v.EXPECTED_NODES, v.EXPECTED_ACTIVE, v.EXPECTED_FREE, v.EXPECTED_IP = old


def test_active_free_helpers_directly():
    # Active-node decrease
    rows = make_phase_rows(active_f3=0.2 - 1.0e-6, free_f3=0.3)
    out = v.evaluate_active_free_gates(rows, expected_nodes=2, expected_active=1, expected_free=1)
    assert out["failures"], "active decrease should fail"
    assert any("phase drift" in f or "decrease" in f for f in out["failures"])

    # Lower-bound violation on free node
    rows = make_phase_rows(active_f3=0.2, free_f3=0.05, free_lb=0.1)
    out = v.evaluate_active_free_gates(rows, expected_nodes=2, expected_active=1, expected_free=1)
    assert any("lower-bound" in f for f in out["failures"])

    # Negative multiplier via KKT helper
    kkt = make_kkt(ok=False, min_mult=-1.0e-4)
    out = v.evaluate_kkt_gates(kkt)
    assert any("multiplier" in f for f in out["failures"])
    print("PASS helper_direct_gates")


def main():
    test_active_free_helpers_directly()

    # Valid fixture
    run_case(
        "valid_fixture_creates_markers",
        make_phase_rows(active_f3=0.2, free_f3=0.30),
        make_kkt(ok=True, min_mult=1.0e-6),
        expect_ok=True,
        n_ip=4,
    )

    # Active-node decrease / drift
    run_case(
        "active_node_decrease_fails",
        make_phase_rows(active_f3=0.2 - 1.0e-6, free_f3=0.30),
        make_kkt(ok=True),
        expect_ok=False,
        expect_fail_token="active-node phase drift",
        n_ip=4,
    )

    # Lower-bound violation
    run_case(
        "lower_bound_violation_fails",
        make_phase_rows(active_f3=0.2, free_f3=0.05, free_lb=0.1),
        make_kkt(ok=True),
        expect_ok=False,
        expect_fail_token="lower-bound",
        n_ip=4,
    )

    # Negative active multiplier
    run_case(
        "negative_active_multiplier_fails",
        make_phase_rows(active_f3=0.2, free_f3=0.30),
        make_kkt(ok=False, min_mult=-5.0e-4),
        expect_ok=False,
        expect_fail_token="multiplier",
        n_ip=4,
    )

    print("ALL_SYNTHETIC_R3_VALIDATOR_TESTS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
