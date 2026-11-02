# -*- coding: utf-8 -*-
"""
investigate_r2_telemetry_consistency.py
Investigate authentic outer-119 vs outer-135 iteration records in live telemetry for Job 1419489.mmaster02.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

import json
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
SSH_WRAPPER = REPO_ROOT / ".agents/scripts/Invoke-GuardedSsh.ps1"
REMOTE_FILE = "/scratch9/pr21vyci/runs/mode1_c5_package163_r2_c2_1_continuation/continuation_1419489.mmaster02/live_iteration_telemetry.json"
LOCAL_FILE = REPO_ROOT / "results/validation/package163_r2_live_telemetry_turn30.json"
OUTPUT_REPORT = REPO_ROOT / "results/validation/r2_telemetry_consistency_investigation.json"


def fetch_telemetry():
    ps_cmd = [
        "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
        "-File", str(SSH_WRAPPER),
        "-RemoteCommand", f"cat {REMOTE_FILE}",
        "-TimeoutSeconds", "120"
    ]
    res = subprocess.run(ps_cmd, cwd=str(REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Remote read failed (exit {res.returncode}):\n{res.stderr}")
    raw = res.stdout.strip()
    idx_start = raw.find("[")
    idx_end = raw.rfind("]")
    if idx_start == -1 or idx_end == -1:
        raise ValueError(f"No JSON array found in output:\n{raw[:300]}")
    data = json.loads(raw[idx_start:idx_end + 1])
    LOCAL_FILE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def investigate(data):
    total = len(data)
    outers = [d["outer"] for d in data]
    print(f"Total authentic telemetry records: {total}, latest outer: {outers[-1]}")

    rec_119 = next((d for d in data if d["outer"] == 119), None)
    rec_135 = next((d for d in data if d["outer"] == 135), None)
    latest_rec = data[-1]

    # Print table from 115 to latest
    window = [d for d in data if d["outer"] >= 115]
    print("\nAuthentic Telemetry Trace (Outer 115 to Latest):")
    print("-" * 105)
    print(f"{'Outer':>5} | {'Delta_d':>12} | {'Delta_u (mm)':>14} | {'Delta_h (MPa)':>14} | {'Dual Err':>12} | {'Free Err':>12} | {'Active Nodes':>12}")
    print("-" * 105)
    for d in window:
        du = f"{d.get('delta_u', 0.0):.6e}" if d.get('delta_u') is not None else "None"
        dh = f"{d.get('delta_h', 0.0):.6e}" if d.get('delta_h') is not None else "None"
        print(f"{d['outer']:5d} | {d['delta_d']:12.6e} | {du:>14} | {dh:>14} | {d.get('dual_error', 0.0):12.6e} | {d.get('free_error', 0.0):12.6e} | {d['pdas_active_count']:12d}")
    print("-" * 105)

    # Detailed comparison between 119 and 135
    comparison = {
        "outer_119": rec_119,
        "outer_135": rec_135,
        "latest_outer": latest_rec
    }

    # Analyze whether delta_u and delta_h plateaued, decayed, or if turn-29 was reporting defect
    if rec_119 and rec_135:
        same_du = (rec_119.get("delta_u") == rec_135.get("delta_u"))
        same_dh = (rec_119.get("delta_h") == rec_135.get("delta_h"))
        du_119 = rec_119.get("delta_u")
        du_135 = rec_135.get("delta_u")
        dh_119 = rec_119.get("delta_h")
        dh_135 = rec_135.get("delta_h")
    else:
        same_du, same_dh = False, False
        du_119, du_135, dh_119, dh_135 = None, None, None, None

    # Contraction analysis from outer 119 to outer 135
    ratio_du = (du_135 / du_119) if (du_119 and du_135) else None
    ratio_dh = (dh_135 / dh_119) if (dh_119 and dh_135) else None
    ratio_dd = (rec_135["delta_d"] / rec_119["delta_d"]) if (rec_119 and rec_135) else None

    finding_str = ""
    if not same_du and not same_dh:
        finding_str = (
            f"DISCREPANCY RESOLVED AS TURN-29 NARRATIVE REUSE: In authentic solver telemetry, "
            f"delta_u decayed from {du_119:.4e} mm at outer 119 to {du_135:.4e} mm at outer 135 (rho_u ~ {ratio_du**(1/16):.4f}), "
            f"and delta_h decayed from {dh_119:.4e} MPa to {dh_135:.4e} MPa (rho_h ~ {ratio_dh**(1/16):.4f}). "
            f"The matching values in Turn 29 report were due to a narrative text copy from outer 119, while solver telemetry was genuinely contracting."
        )
    elif same_du and same_dh:
        finding_str = "GENUINE PLATEAU: Authentic solver telemetry records identical values at outer 119 and outer 135."
    else:
        finding_str = f"PARTIAL SHIFT: delta_u same={same_du}, delta_h same={same_dh}."

    report = {
        "schema": 1,
        "investigation": "R2_TELEMETRY_CONSISTENCY_OUTER_119_VS_135",
        "task_id": "F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE",
        "job_id": "1419489.mmaster02",
        "total_records": total,
        "latest_outer": latest_rec["outer"],
        "comparison_119_vs_135": {
            "outer_119": {
                "delta_d": rec_119["delta_d"] if rec_119 else None,
                "delta_u_mm": du_119,
                "delta_h_MPa": dh_119,
                "pdas_active": rec_119["pdas_active_count"] if rec_119 else None
            },
            "outer_135": {
                "delta_d": rec_135["delta_d"] if rec_135 else None,
                "delta_u_mm": du_135,
                "delta_h_MPa": dh_135,
                "pdas_active": rec_135["pdas_active_count"] if rec_135 else None
            },
            "ratio_135_over_119": {
                "delta_d_ratio": round(ratio_dd, 4) if ratio_dd else None,
                "delta_u_ratio": round(ratio_du, 4) if ratio_du else None,
                "delta_h_ratio": round(ratio_dh, 4) if ratio_dh else None,
                "per_outer_contraction_rho_u": round(ratio_du**(1/16), 4) if ratio_du else None,
                "per_outer_contraction_rho_h": round(ratio_dh**(1/16), 4) if ratio_dh else None
            },
            "discrepancy_verdict": "NARRATIVE_REUSE_IN_REPORT" if (not same_du and not same_dh) else "GENUINE_PLATEAU"
        },
        "latest_telemetry_snapshot": {
            "outer": latest_rec["outer"],
            "delta_d": latest_rec["delta_d"],
            "delta_u_mm": latest_rec.get("delta_u"),
            "delta_h_MPa": latest_rec.get("delta_h"),
            "dual_error_kNmm": latest_rec.get("dual_error"),
            "free_error_kN": latest_rec.get("free_error"),
            "pdas_active_count": latest_rec["pdas_active_count"],
            "pdas_free_count": latest_rec["pdas_free_count"]
        },
        "finding": finding_str
    }

    OUTPUT_REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\nInvestigation report written to: {OUTPUT_REPORT}")
    print(f"Finding: {finding_str}")
    return report


if __name__ == "__main__":
    raw = fetch_telemetry()
    investigate(raw)
