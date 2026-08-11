#!/usr/bin/env python3
"""Compute auditable Mode-II H2 endpoint overlap and convergence metrics."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
H0 = ROOT / "models/generated/mode_ii/verification_batch/M2REF_H0_NPHYSFIX_REPRO/evidence/1386372.mmaster02"
H1 = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H1_FRACFIX/evidence/1386447.mmaster02"
H2_OLD = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX/evidence/1386448.mmaster02"
H2_NEW = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX_ENDPOINT/evidence/1388330.mmaster02"


def trapz(y, x):
    return float(np.trapezoid(y, x) if hasattr(np, "trapezoid") else np.trapz(y, x))


def curve(path):
    df = pd.read_csv(path / "rf1_u1_curve.csv").sort_values("u1")
    return df.drop_duplicates("u1", keep="last")


def damage(path):
    df = pd.read_csv(path / "damage_history.csv").sort_values("u1")
    return df.drop_duplicates("u1", keep="last")


def compare(a, b, umax, denominator="a"):
    grid = np.linspace(0.0, umax, 20001)
    ya = np.interp(grid, a.u1, a.rf1)
    yb = np.interp(grid, b.u1, b.rf1)
    ref = ya if denominator == "a" else yb
    area_a, area_b = trapz(ya, grid), trapz(yb, grid)
    return {
        "u_max_mm": float(umax),
        "normalized_L2_pct": float(np.sqrt(trapz((yb-ya)**2, grid)) / np.sqrt(trapz(ref**2, grid)) * 100.0),
        "area_a_kN_mm": area_a,
        "area_b_kN_mm": area_b,
        "absolute_area_difference_pct": float(abs(area_b-area_a) / abs(area_a) * 100.0),
        "signed_area_difference_pct": float((area_b-area_a) / area_a * 100.0),
        "maximum_absolute_RF_difference_kN": float(np.max(np.abs(yb-ya))),
        "endpoint_RF_a_kN": float(ya[-1]),
        "endpoint_RF_b_kN": float(yb[-1]),
        "endpoint_RF_difference_pct": float((yb[-1]-ya[-1]) / ya[-1] * 100.0),
    }


def stiffness(df):
    f = df[(df.u1 > 0.0) & (df.u1 <= 0.002)]
    return float(np.dot(f.u1, f.rf1) / np.dot(f.u1, f.u1))


def initiation(df, threshold):
    hit = df[df.d_max >= threshold]
    return None if hit.empty else float(hit.iloc[0].u1)


h0, h1, old, new = map(curve, (H0, H1, H2_OLD, H2_NEW))
d0, d1, dold, dnew = map(damage, (H0, H1, H2_OLD, H2_NEW))
overlap = min(float(old.u1.max()), float(new.u1.max()))
common12 = min(float(h1.u1.max()), float(new.u1.max()))
common02 = min(float(h0.u1.max()), float(new.u1.max()))

old_new = compare(old, new, overlap)
h1_new = compare(h1, new, common12)
h0_new = compare(h0, new, common02)

old_new["endpoint_dmax_old"] = float(np.interp(overlap, dold.u1, dold.d_max))
old_new["endpoint_dmax_new"] = float(np.interp(overlap, dnew.u1, dnew.d_max))
old_new["endpoint_dmax_difference"] = old_new["endpoint_dmax_new"] - old_new["endpoint_dmax_old"]
h1_new["endpoint_dmax_h1"] = float(np.interp(common12, d1.u1, d1.d_max))
h1_new["endpoint_dmax_h2"] = float(np.interp(common12, dnew.u1, dnew.d_max))
h1_new["endpoint_dmax_difference"] = h1_new["endpoint_dmax_h2"] - h1_new["endpoint_dmax_h1"]

peak_i = int(np.argmax(new.rf1.to_numpy()))
result = {
    "old_h2_vs_new_h2_overlap": old_new,
    "h1_vs_new_h2_common_domain": h1_new,
    "h0_vs_new_h2_available_domain_not_full_path": h0_new,
    "new_h2": {
        "final_u1_mm": float(new.iloc[-1].u1),
        "final_rf1_kN": float(new.iloc[-1].rf1),
        "maximum_rf1_kN": float(new.iloc[peak_i].rf1),
        "u1_at_maximum_rf1_mm": float(new.iloc[peak_i].u1),
        "interior_peak": bool(peak_i < len(new)-1),
        "initial_stiffness_origin_ols_kN_per_mm": stiffness(new),
        "final_dmax": float(dnew.iloc[-1].d_max),
        "damage_initiation_u1_d_ge_0p5_mm": initiation(dnew, 0.5),
        "damage_initiation_u1_d_ge_0p9_mm": initiation(dnew, 0.9),
    },
    "stiffness": {
        "h0_kN_per_mm": stiffness(h0),
        "h1_kN_per_mm": stiffness(h1),
        "new_h2_kN_per_mm": stiffness(new),
        "h2_vs_h1_pct": (stiffness(new)-stiffness(h1))/stiffness(h1)*100.0,
    },
    "damage_initiation_d_ge_0p5_mm": {
        "old_h2": initiation(dold, 0.5), "new_h2": initiation(dnew, 0.5),
        "h1": initiation(d1, 0.5),
    },
    "damage_initiation_d_ge_0p9_mm": {
        "old_h2": initiation(dold, 0.9), "new_h2": initiation(dnew, 0.9),
        "h1": initiation(d1, 0.9),
    },
}

out = H2_NEW / "H2_ENDPOINT_COMPARISON_SUMMARY.json"
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
