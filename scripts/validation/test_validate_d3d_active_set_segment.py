#!/usr/bin/env python3
"""Synthetic tests for hardened D3D postprocessing gates.

Proves:
  - long-format F3 phase prefix comparison passes
  - missing prefix coverage fails
  - F0/F2 KKT failure does not control the D3D outcome
  - negative F4 multiplier → active-set-update-required
  - free residual failure → postprocessing-fail
  - phase decrease → active-set-update-required
  - H decrease → active-set-update-required
  - endpoint U2 mismatch fails
  - fewer than 10 increments fails
  - nonfinite TOP RF fails
  - valid fixture creates D3D.ok
"""

from __future__ import annotations

import csv
import json
import math
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scripts.validation.analyze_d3d_continuation_irreversibility as irr  # noqa: E402
import scripts.validation.analyze_d3d_per_frame_kkt as kkt  # noqa: E402
import scripts.validation.validate_d3d_active_set_segment as v  # noqa: E402
import scripts.validation.validate_d3d_r4_prefix as pref  # noqa: E402

N_IP = 4
N_NODES = 2
CHECKPOINT_U2 = 0.003000000026077032
SEGMENT_U2 = 0.0031


def write_csv(path: Path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def cont_tags(n_inc=10):
    # initial + (n_inc-1) interior + end = n_inc+1 frames => n_inc increments
    tags = ["F4_segment_initial"]
    for i in range(1, n_inc):
        tags.append("F4_segment_inc_%03d" % i)
    tags.append("F4_segment_end")
    return tags


def make_manifest(n_inc=10, endpoint_u2=SEGMENT_U2, nonfinite_rf=False, top_nodes=81):
    tags = cont_tags(n_inc)
    frames = []
    # prefix frames
    for tag, step, u2 in [
        ("F0_ingested", "INGEST_COMPATIBLE_R2", 0.0),
        ("F1_equilibrated", "CHECKPOINT_EQUILIBRATION_COMPATIBLE_R2_FIXED", CHECKPOINT_U2),
        ("F2_release_first", "ACTIVE_SET_R2_RELEASE_HOLD", CHECKPOINT_U2),
        ("F3_release_last", "ACTIVE_SET_R2_RELEASE_HOLD", CHECKPOINT_U2),
    ]:
        frames.append(
            {
                "frame_tag": tag,
                "step_name": step,
                "frame_index": 0,
                "step_time": 1.0 if tag != "F0_ingested" else 1.0,
                "normalized_step_time": 1.0,
                "expected_top_u2": u2,
                "actual_top_u2_mean": u2,
                "actual_top_u2_min": u2,
                "actual_top_u2_max": u2,
                "top_node_count": top_nodes,
                "top_rf2_sum": 0.4,
            }
        )
    n_frames = len(tags)
    for i, tag in enumerate(tags):
        t = i / float(n_frames - 1) if n_frames > 1 else 0.0
        expected = CHECKPOINT_U2 + (SEGMENT_U2 - CHECKPOINT_U2) * t
        actual = endpoint_u2 if tag == "F4_segment_end" else expected
        rf = float("nan") if nonfinite_rf and tag == "F4_segment_end" else 0.41 + 0.001 * i
        frames.append(
            {
                "frame_tag": tag,
                "step_name": "ACTIVE_SET_VALIDITY_SEGMENT",
                "frame_index": i,
                "step_time": t,
                "normalized_step_time": t,
                "expected_top_u2": expected if tag != "F4_segment_end" else SEGMENT_U2,
                "actual_top_u2_mean": actual if tag != "F4_segment_end" else endpoint_u2,
                "actual_top_u2_min": actual if tag != "F4_segment_end" else endpoint_u2,
                "actual_top_u2_max": actual if tag != "F4_segment_end" else endpoint_u2,
                "top_node_count": top_nodes,
                "top_rf2_sum": rf,
            }
        )
    step4 = [f for f in frames if f["step_name"] == "ACTIVE_SET_VALIDITY_SEGMENT"]
    return {
        "classification": "stage_d3d_frame_manifest_written",
        "frames": frames,
        "step4_frame_count": len(step4),
        "accepted_continuation_increments": max(0, len(step4) - 1),
        "step4_first_time": 0.0,
        "step4_last_time": 1.0,
        "step4_endpoint_expected_u2": SEGMENT_U2,
        "step4_top_node_count_ok": True,
        "expected_top_nodes": 81,
        "checkpoint_u2": CHECKPOINT_U2,
        "segment_u2": SEGMENT_U2,
    }


def make_rf_from_manifest(manifest):
    rows = []
    for f in manifest["frames"]:
        rows.append(
            {
                "frame_tag": f["frame_tag"],
                "step": f["step_name"],
                "frame_index": f["frame_index"],
                "top_node_count": f["top_node_count"],
                "top_u2_mean": f["actual_top_u2_mean"],
                "top_u2_min": f["actual_top_u2_min"],
                "top_u2_max": f["actual_top_u2_max"],
                "top_rf2_sum": f["top_rf2_sum"],
            }
        )
    return rows


def make_state(tags, phase_vals=None, h_vals=None):
    # Minimal IP set for state_reset / spatial checks in final validator uses EXPECTED_IPS=25600
    # so we must write 25600 rows per endpoint tag for coverage checks — expensive but OK for one endpoint.
    # For speed, write only for tags used and full 25600 only for endpoint + F3.
    rows = []
    phase_vals = phase_vals or {}
    h_vals = h_vals or {}
    for tag in tags:
        base_d = phase_vals.get(tag, 0.2)
        base_h = h_vals.get(tag, 1.0e-3)
        for i in range(1, v.EXPECTED_IPS + 1):
            d = base_d + 0.01 * ((i - 1) % 3)  # spatial variation
            h = base_h + 1.0e-6 * i
            rows.append(
                {
                    "frame_tag": tag,
                    "element": (i - 1) // 4 + 1,
                    "uel_integration_point": ((i - 1) % 4) + 1,
                    "odb_sdv15": d,
                    "odb_sdv16": h,
                }
            )
    return rows


def make_phase_long(tags, d_by_tag=None, n_nodes=None):
    n_nodes = n_nodes or v.EXPECTED_NODES
    d_by_tag = d_by_tag or {}
    rows = []
    for tag in tags:
        base = d_by_tag.get(tag, 0.2)
        for n in range(1, n_nodes + 1):
            rows.append(
                {
                    "frame_tag": tag,
                    "node": n,
                    "recovered_d_mean": base + 1.0e-6 * (n % 5),
                }
            )
    return rows


def make_kkt_rows(cont_tags_list, free_res=1e-12, min_mult=1e-6, bound=0.0, include_bad_f0=False):
    rows = []
    if include_bad_f0:
        rows.append(
            {
                "frame_tag": "F0_ingested",
                "role": "ignored",
                "node_coverage": v.EXPECTED_NODES,
                "ip_coverage": v.EXPECTED_IPS,
                "non_positive_detJ": 0,
                "free_residual_inf": 1.0,  # would fail if gated
                "minimum_active_multiplier": -1.0,
                "active_bound_error": 1.0,
                "active_nodes_below_tol": 10,
                "kkt_ok": False,
                "scientific_active_multiplier_violation": True,
                "analysis_ok": True,
                "failures": "free_residual;active_multiplier",
            }
        )
        rows.append(
            {
                "frame_tag": "F2_release_first",
                "role": "ignored",
                "node_coverage": v.EXPECTED_NODES,
                "ip_coverage": v.EXPECTED_IPS,
                "non_positive_detJ": 0,
                "free_residual_inf": 1.0,
                "minimum_active_multiplier": -1.0,
                "active_bound_error": 0.0,
                "active_nodes_below_tol": 5,
                "kkt_ok": False,
                "scientific_active_multiplier_violation": True,
                "analysis_ok": True,
                "failures": "free_residual",
            }
        )
    rows.append(
        {
            "frame_tag": "F3_release_last",
            "role": "baseline",
            "node_coverage": v.EXPECTED_NODES,
            "ip_coverage": v.EXPECTED_IPS,
            "non_positive_detJ": 0,
            "free_residual_inf": 1e-12,
            "minimum_active_multiplier": 1e-6,
            "active_bound_error": 0.0,
            "active_nodes_below_tol": 0,
            "kkt_ok": True,
            "scientific_active_multiplier_violation": False,
            "analysis_ok": True,
            "failures": "",
        }
    )
    for tag in cont_tags_list:
        m = min_mult[tag] if isinstance(min_mult, dict) else min_mult
        fr = free_res[tag] if isinstance(free_res, dict) else free_res
        rows.append(
            {
                "frame_tag": tag,
                "role": "continuation",
                "node_coverage": v.EXPECTED_NODES,
                "ip_coverage": v.EXPECTED_IPS,
                "non_positive_detJ": 0,
                "free_residual_inf": fr,
                "minimum_active_multiplier": m,
                "active_bound_error": bound,
                "active_nodes_below_tol": 1 if m < -1e-8 else 0,
                "kkt_ok": (fr <= 1e-8) and (m >= -1e-8) and (bound <= 1e-10),
                "scientific_active_multiplier_violation": m < -1e-8,
                "analysis_ok": True,
                "failures": "",
            }
        )
    return rows


def make_kkt_summary(cont_tags_list, free_res=1e-12, min_mult=1e-6, complete=True):
    most = min_mult if not isinstance(min_mult, dict) else min(min_mult.values())
    first = None
    if isinstance(min_mult, dict):
        for t, m in min_mult.items():
            if m < -1e-8:
                first = t
                break
    elif min_mult < -1e-8:
        first = cont_tags_list[0] if cont_tags_list else None
    return {
        "classification": "stage_d3d_per_frame_kkt_analysis_complete"
        if complete
        else "stage_d3d_per_frame_kkt_analysis_incomplete",
        "analysis_complete": complete,
        "failures": [] if complete else ["synthetic incomplete"],
        "continuation_frames_expected": len(cont_tags_list),
        "continuation_frames_evaluated": len(cont_tags_list),
        "continuation_frames_kkt_ok": len(cont_tags_list),
        "first_continuation_frame_with_negative_multiplier": first,
        "most_negative_continuation_multiplier": most if first else None,
        "maximum_free_residual": free_res if not isinstance(free_res, dict) else max(free_res.values()),
        "maximum_active_bound_error": 0.0,
        "active_nodes_below_tolerance": 1 if first else 0,
    }


def make_irr(phase_dec=0, h_dec=0, lb_dec=0, complete=True):
    return {
        "classification": "stage_d3d_irreversibility_audit_complete"
        if complete
        else "stage_d3d_irreversibility_audit_incomplete",
        "audit_complete": complete,
        "failures": [] if complete else ["missing"],
        "phase_decrease_violations": phase_dec if complete else None,
        "H_decrease_violations": h_dec if complete else None,
        "below_lower_bound_violations": lb_dec if complete else None,
        "pair_count": 10,
    }


def make_prefix(ok=True, failures=None):
    return {
        "classification": "stage_d3d_r4_prefix_reproduction_pass"
        if ok
        else "stage_d3d_r4_prefix_reproduction_fail",
        "D3D_r4_prefix_ok": ok,
        "failures": failures or ([] if ok else ["prefix fail"]),
    }


def make_energy(tags):
    return {
        "classification": "synthetic",
        "frames": [
            {
                "frame_tag": t,
                "total_reconstructed_internal_energy": 1.0,
                "missing_phase_node_values": 0,
                "missing_sdv12_values": 0,
                "missing_sdv13_values": 0,
            }
            for t in tags
        ],
    }


def build_valid_fixture(
    root: Path,
    n_inc=10,
    free_res=1e-12,
    min_mult=1e-6,
    phase_dec=0,
    h_dec=0,
    lb_dec=0,
    endpoint_u2=SEGMENT_U2,
    nonfinite_rf=False,
    include_bad_f0=False,
    prefix_ok=True,
):
    tags = cont_tags(n_inc)
    all_tags = ["F3_release_last"] + tags
    manifest = make_manifest(n_inc=n_inc, endpoint_u2=endpoint_u2, nonfinite_rf=nonfinite_rf)
    write_json(root / "D3D_FRAME_MANIFEST.json", manifest)
    write_csv(
        root / "D3D_FRAME_MANIFEST.csv",
        list(manifest["frames"][0].keys()),
        manifest["frames"],
    )
    write_csv(
        root / "D3D_TOP_RF_U.csv",
        [
            "frame_tag",
            "step",
            "frame_index",
            "top_node_count",
            "top_u2_mean",
            "top_u2_min",
            "top_u2_max",
            "top_rf2_sum",
        ],
        make_rf_from_manifest(manifest),
    )
    write_json(root / "D3D_R4_PREFIX_COMPARISON.json", make_prefix(ok=prefix_ok))
    krows = make_kkt_rows(tags, free_res=free_res, min_mult=min_mult, include_bad_f0=include_bad_f0)
    write_csv(root / "D3D_PER_FRAME_KKT.csv", list(krows[0].keys()), krows)
    write_json(
        root / "D3D_PER_FRAME_KKT_SUMMARY.json",
        make_kkt_summary(tags, free_res=free_res, min_mult=min_mult),
    )
    irr_summary = make_irr(phase_dec, h_dec, lb_dec)
    irr_summary["ordered_tags"] = all_tags
    irr_summary["pair_count"] = len(tags)
    write_json(root / "D3D_IRREVERSIBILITY_AUDIT.json", irr_summary)
    write_csv(
        root / "D3D_IRREVERSIBILITY_BY_FRAME_PAIR.csv",
        ["left_frame", "right_frame", "phase_node_coverage", "ip_coverage"],
        [
            {
                "left_frame": all_tags[i],
                "right_frame": all_tags[i + 1],
                "phase_node_coverage": v.EXPECTED_NODES,
                "ip_coverage": v.EXPECTED_IPS,
            }
            for i in range(len(tags))
        ],
    )
    # Endpoint + F3 state only (coverage check uses endpoint)
    write_csv(
        root / "D3D_STATE_BY_FRAME.csv",
        ["frame_tag", "element", "uel_integration_point", "odb_sdv15", "odb_sdv16"],
        make_state(["F3_release_last", "F4_segment_end"]),
    )
    # Phase file presence only for required-files check in final validator
    write_csv(
        root / "D3D_PHASE_NODE_STATE_BY_FRAME.csv",
        ["frame_tag", "node", "recovered_d_mean"],
        make_phase_long(["F3_release_last", "F4_segment_end"], n_nodes=2),
    )
    write_json(root / "D3D_RECONSTRUCTED_ENERGY_BY_FRAME.json", make_energy(all_tags))
    write_csv(
        root / "D3D_ACTIVE_MULTIPLIER_CANDIDATES.csv",
        ["frame_tag", "node", "x", "y", "multiplier", "d", "d_lb"],
        (
            [
                {
                    "frame_tag": tags[0],
                    "node": 1,
                    "x": 0.0,
                    "y": 0.0,
                    "multiplier": min_mult if not isinstance(min_mult, dict) else -1e-6,
                    "d": 0.2,
                    "d_lb": 0.2,
                }
            ]
            if (
                (not isinstance(min_mult, dict) and min_mult < -1e-8)
                or (isinstance(min_mult, dict) and any(m < -1e-8 for m in min_mult.values()))
            )
            else []
        ),
    )
    return tags


def test_long_format_prefix_pass():
    with tempfile.TemporaryDirectory() as tmp:
        d3d = Path(tmp) / "d3d"
        r4 = Path(tmp) / "r4"
        d3d.mkdir()
        r4.mkdir()
        # Full 25600 IP identical state
        state = []
        for i in range(1, pref.EXPECTED_IPS + 1):
            state.append(
                {
                    "frame_tag": "F3_release_last",
                    "element": (i - 1) // 4 + 1,
                    "uel_integration_point": ((i - 1) % 4) + 1,
                    "odb_sdv15": 0.1 + 1e-6 * i,
                    "odb_sdv16": 1e-3 + 1e-8 * i,
                }
            )
        write_csv(
            d3d / "D3D_STATE_BY_FRAME.csv",
            ["frame_tag", "element", "uel_integration_point", "odb_sdv15", "odb_sdv16"],
            state,
        )
        write_csv(
            r4 / "D3A3_STATE_BY_FRAME.csv",
            ["frame_tag", "element", "uel_integration_point", "odb_sdv15", "odb_sdv16"],
            state,
        )
        phase_long = []
        phase_wide = []
        for n in range(1, pref.EXPECTED_NODES + 1):
            val = 0.2 + 1e-7 * n
            phase_long.append(
                {"frame_tag": "F3_release_last", "node": n, "recovered_d_mean": val}
            )
            phase_wide.append({"node": n, "d_F3": val})
        write_csv(
            d3d / "D3D_PHASE_NODE_STATE_BY_FRAME.csv",
            ["frame_tag", "node", "recovered_d_mean"],
            phase_long,
        )
        write_csv(r4 / "D3A3_R4_PHASE_NODE_STATE_BY_FRAME.csv", ["node", "d_F3"], phase_wide)
        u2 = CHECKPOINT_U2
        rf = {
            "frame_tag": "F3_release_last",
            "step": "ACTIVE_SET_R2_RELEASE_HOLD",
            "frame_index": 10,
            "top_node_count": 81,
            "top_u2_mean": u2,
            "top_u2_min": u2,
            "top_u2_max": u2,
            "top_rf2_sum": 0.3945,
        }
        write_csv(
            d3d / "D3D_TOP_RF_U.csv",
            list(rf.keys()),
            [rf],
        )
        write_csv(
            r4 / "D3A3_RF_U_CORRECTED.csv",
            list(rf.keys()),
            [rf],
        )
        e = {
            "frames": [
                {
                    "frame_tag": "F3_release_last",
                    "total_reconstructed_internal_energy": 12.34,
                }
            ]
        }
        write_json(d3d / "D3D_RECONSTRUCTED_ENERGY_BY_FRAME.json", e)
        write_json(r4 / "D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json", e)
        status = pref.validate(d3d, r4)
        assert status["D3D_r4_prefix_ok"], status["failures"]
        assert status["sdv15_compared_ips"] == 25600
        assert status["phase_compared_nodes"] == 6601
        print("PASS test_long_format_prefix_pass")


def test_missing_prefix_coverage_fails():
    with tempfile.TemporaryDirectory() as tmp:
        d3d = Path(tmp) / "d3d"
        r4 = Path(tmp) / "r4"
        d3d.mkdir()
        r4.mkdir()
        # Only 10 IPs
        state = [
            {
                "frame_tag": "F3_release_last",
                "element": 1,
                "uel_integration_point": i,
                "odb_sdv15": 0.1,
                "odb_sdv16": 1e-3,
            }
            for i in range(1, 5)
        ]
        write_csv(
            d3d / "D3D_STATE_BY_FRAME.csv",
            ["frame_tag", "element", "uel_integration_point", "odb_sdv15", "odb_sdv16"],
            state,
        )
        write_csv(
            r4 / "D3A3_STATE_BY_FRAME.csv",
            ["frame_tag", "element", "uel_integration_point", "odb_sdv15", "odb_sdv16"],
            state,
        )
        write_csv(
            d3d / "D3D_PHASE_NODE_STATE_BY_FRAME.csv",
            ["frame_tag", "node", "recovered_d_mean"],
            [{"frame_tag": "F3_release_last", "node": 1, "recovered_d_mean": 0.2}],
        )
        write_csv(
            r4 / "D3A3_R4_PHASE_NODE_STATE_BY_FRAME.csv",
            ["node", "d_F3"],
            [{"node": 1, "d_F3": 0.2}],
        )
        write_csv(
            d3d / "D3D_TOP_RF_U.csv",
            ["frame_tag", "top_node_count", "top_u2_mean", "top_rf2_sum"],
            [{"frame_tag": "F3_release_last", "top_node_count": 81, "top_u2_mean": CHECKPOINT_U2, "top_rf2_sum": 0.1}],
        )
        write_csv(
            r4 / "D3A3_RF_U_CORRECTED.csv",
            ["frame_tag", "top_node_count", "top_u2_mean", "top_rf2_sum"],
            [{"frame_tag": "F3_release_last", "top_node_count": 81, "top_u2_mean": CHECKPOINT_U2, "top_rf2_sum": 0.1}],
        )
        e = {"frames": [{"frame_tag": "F3_release_last", "total_reconstructed_internal_energy": 1.0}]}
        write_json(d3d / "D3D_RECONSTRUCTED_ENERGY_BY_FRAME.json", e)
        write_json(r4 / "D3A3_RECONSTRUCTED_ENERGY_BY_FRAME_CORRECTED.json", e)
        status = pref.validate(d3d, r4)
        assert not status["D3D_r4_prefix_ok"]
        assert any("coverage" in f.lower() or "25600" in f for f in status["failures"])
        print("PASS test_missing_prefix_coverage_fails")


def test_valid_creates_ok():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build_valid_fixture(root, include_bad_f0=True)
        status = v.validate(root)
        assert status["classification"] == v.PASS, status
        assert (root / "D3D.ok").exists()
        print("PASS test_valid_creates_ok (F0/F2 KKT fail ignored)")


def test_negative_multiplier_update():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build_valid_fixture(root, min_mult=-1.0e-6)
        status = v.validate(root)
        assert status["classification"] == v.UPDATE, status
        assert not (root / "D3D.ok").exists()
        assert (root / "D3D_ACTIVE_SET_UPDATE_REQUIRED.json").exists()
        upd = json.loads((root / "D3D_ACTIVE_SET_UPDATE_REQUIRED.json").read_text(encoding="utf-8"))
        assert upd["candidates"]
        print("PASS test_negative_multiplier_update")


def test_free_residual_post_fail():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build_valid_fixture(root, free_res=1.0e-6)
        status = v.validate(root)
        assert status["classification"] == v.POST_FAIL, status
        assert not (root / "D3D.ok").exists()
        print("PASS test_free_residual_post_fail")


def test_phase_decrease_update():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build_valid_fixture(root, phase_dec=3)
        status = v.validate(root)
        assert status["classification"] == v.UPDATE, status
        print("PASS test_phase_decrease_update")


def test_h_decrease_update():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build_valid_fixture(root, h_dec=2)
        status = v.validate(root)
        assert status["classification"] == v.UPDATE, status
        print("PASS test_h_decrease_update")


def test_endpoint_u2_mismatch():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build_valid_fixture(root, endpoint_u2=0.00305)
        status = v.validate(root)
        assert status["classification"] == v.POST_FAIL, status
        assert any("U2" in f for f in status["failures"])
        print("PASS test_endpoint_u2_mismatch")


def test_fewer_than_10_increments():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build_valid_fixture(root, n_inc=5)
        status = v.validate(root)
        assert status["classification"] == v.POST_FAIL, status
        assert any("increments" in f for f in status["failures"])
        print("PASS test_fewer_than_10_increments")


def test_nonfinite_top_rf():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build_valid_fixture(root, nonfinite_rf=True)
        status = v.validate(root)
        assert status["classification"] == v.POST_FAIL, status
        assert any("RF" in f for f in status["failures"])
        print("PASS test_nonfinite_top_rf")


def test_missing_irr_fields_not_default_zero():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        build_valid_fixture(root)
        # Overwrite audit with incomplete missing totals
        write_json(
            root / "D3D_IRREVERSIBILITY_AUDIT.json",
            {
                "classification": "stage_d3d_irreversibility_audit_incomplete",
                "audit_complete": False,
                "failures": ["synthetic"],
                # deliberately omit phase_decrease_violations
            },
        )
        status = v.validate(root)
        assert status["classification"] == v.POST_FAIL, status
        assert any("missing required field" in f or "incomplete" in f for f in status["failures"])
        print("PASS test_missing_irr_fields_not_default_zero")


def test_missing_f4_phase_history_frame_fails():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        tags = build_valid_fixture(root)
        assert len(tags) == 11
        missing_tag = tags[5]
        present_tags = ["F3_release_last"] + [tag for tag in tags if tag != missing_tag]
        phase_rows = [
            {"frame_tag": tag, "node": 1, "recovered_d_mean": 0.2}
            for tag in present_tags
        ]
        state_rows = [
            {
                "frame_tag": tag,
                "element": 1,
                "uel_integration_point": 1,
                "odb_sdv15": 0.2,
                "odb_sdv16": 1.0e-3,
            }
            for tag in present_tags
        ]
        write_csv(
            root / "D3D_PHASE_NODE_STATE_BY_FRAME.csv",
            ["frame_tag", "node", "recovered_d_mean"],
            phase_rows,
        )
        write_csv(
            root / "D3D_STATE_BY_FRAME.csv",
            ["frame_tag", "element", "uel_integration_point", "odb_sdv15", "odb_sdv16"],
            state_rows,
        )
        pairs = read_csv(root / "D3D_IRREVERSIBILITY_BY_FRAME_PAIR.csv")
        pairs = [
            row
            for row in pairs
            if row["left_frame"] != missing_tag and row["right_frame"] != missing_tag
        ]
        write_csv(
            root / "D3D_IRREVERSIBILITY_BY_FRAME_PAIR.csv",
            ["left_frame", "right_frame", "phase_node_coverage", "ip_coverage"],
            pairs,
        )
        status = v.validate(root)
        assert status["classification"] == v.POST_FAIL, status
        assert any("irreversibility pair" in f for f in status["technical_failures"])
        print("PASS test_missing_f4_phase_history_frame_fails")


def test_kkt_scope_helpers():
    assert kkt.is_continuation_frame("F4_segment_end")
    assert not kkt.is_continuation_frame("F0_ingested")
    assert not kkt.is_continuation_frame("F2_release_first")
    assert kkt.is_reported_frame("F3_release_last")
    assert not kkt.is_reported_frame("F0_ingested")
    print("PASS test_kkt_scope_helpers")


def test_irreversibility_pair_order():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        tags = ["F3_release_last", "F4_segment_initial", "F4_segment_end"]
        # Monotone phase/H
        d = {"F3_release_last": 0.2, "F4_segment_initial": 0.21, "F4_segment_end": 0.22}
        h = {"F3_release_last": 1e-3, "F4_segment_initial": 1.1e-3, "F4_segment_end": 1.2e-3}
        phase_rows = []
        state_rows = []
        for tag in tags:
            for n in range(1, 5):
                phase_rows.append(
                    {"frame_tag": tag, "node": n, "recovered_d_mean": d[tag]}
                )
            for i in range(1, 5):
                state_rows.append(
                    {
                        "frame_tag": tag,
                        "element": 1,
                        "uel_integration_point": i,
                        "odb_sdv15": d[tag],
                        "odb_sdv16": h[tag],
                    }
                )
        write_csv(
            root / "D3D_PHASE_NODE_STATE_BY_FRAME.csv",
            ["frame_tag", "node", "recovered_d_mean"],
            phase_rows,
        )
        write_csv(
            root / "D3D_STATE_BY_FRAME.csv",
            ["frame_tag", "element", "uel_integration_point", "odb_sdv15", "odb_sdv16"],
            state_rows,
        )
        write_csv(
            root / "D3D_FRAME_MANIFEST.csv",
            ["frame_tag", "step_name", "frame_index", "step_time"],
            [
                {
                    "frame_tag": "F3_release_last",
                    "step_name": "ACTIVE_SET_R2_RELEASE_HOLD",
                    "frame_index": 10,
                    "step_time": 1.0,
                },
                {
                    "frame_tag": "F4_segment_initial",
                    "step_name": "ACTIVE_SET_VALIDITY_SEGMENT",
                    "frame_index": 0,
                    "step_time": 0.0,
                },
                {
                    "frame_tag": "F4_segment_end",
                    "step_name": "ACTIVE_SET_VALIDITY_SEGMENT",
                    "frame_index": 1,
                    "step_time": 1.0,
                },
            ],
        )
        audit = irr.analyze(root)
        assert audit["audit_complete"]
        assert audit["phase_decrease_violations"] == 0
        assert audit["H_decrease_violations"] == 0
        # Now introduce phase decrease
        phase_rows = [
            r
            if r["frame_tag"] != "F4_segment_end"
            else {**r, "recovered_d_mean": 0.10}
            for r in phase_rows
        ]
        write_csv(
            root / "D3D_PHASE_NODE_STATE_BY_FRAME.csv",
            ["frame_tag", "node", "recovered_d_mean"],
            phase_rows,
        )
        audit2 = irr.analyze(root)
        assert audit2["phase_decrease_violations"] > 0
        print("PASS test_irreversibility_pair_order")


def main():
    test_kkt_scope_helpers()
    test_long_format_prefix_pass()
    test_missing_prefix_coverage_fails()
    test_valid_creates_ok()
    test_negative_multiplier_update()
    test_free_residual_post_fail()
    test_phase_decrease_update()
    test_h_decrease_update()
    test_endpoint_u2_mismatch()
    test_fewer_than_10_increments()
    test_nonfinite_top_rf()
    test_missing_irr_fields_not_default_zero()
    test_missing_f4_phase_history_frame_fails()
    test_irreversibility_pair_order()
    print("ALL D3D postprocessing synthetic tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
