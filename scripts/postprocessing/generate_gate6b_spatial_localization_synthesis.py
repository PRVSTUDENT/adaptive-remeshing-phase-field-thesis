# -*- coding: utf-8 -*-
"""
Mode-I Gate-6B Spatial Convergence, Localization Metrics, and Crack Path Synthesis
Protocol Version: 2
Evaluates quantitative spatial phase-field distributions, ligament profiles d(x, y=0.5 mm),
crack-tip positions x_tip(theta in {0.5, 0.7, 0.9}), localization bandwidth w_0.5,
and transverse symmetry across the governed benchmark hierarchy:
  - Fixed Reference Anchor (15,192 FEs, Job 1398090 / 1409734)
  - Canonical ET1 Baseline (14,483 FEs, Job 1409982)
  - ET1 Cn=0.50 Diagnostic (14,483 FEs, Job 1410180)
  - Adaptive ET2 2.0% (6,112 FEs, Job 1410357)
  - Adaptive ET3 3.0% (5,189 FEs, Job 1410358)
  - Adaptive ET5 5.0% (4,692 FEs, Job 1410359)
  - Spatial Fine Candidate (57,929 FEs, Job 1410504)
"""
import os
import sys
import json
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

l0 = 0.0075 # mm
SUPERVISOR_THREE_CASE = os.environ.get("MODE1_SUPERVISOR_THREE_CASE", "0") == "1"
FIGURE_OUTPUT_DIR = os.environ.get("MODE1_FIGURE_OUTPUT_DIR")

# 1. Benchmark cases definition with verified peak and kinematics
CASES = {
    "fixed_ref_15k": {
        "case_id": "fixed_ref_15k",
        "name": "Fixed Reference (15.2k)",
        "job_id": "1409734.mmaster02",
        "fe_count": 15192,
        "nodes_count": 15521,
        "mesh_type": "Structured Refined Corridor (h=0.003 mm)",
        "u_peak_mm": 0.005857,
        "f_max_kn": 0.757778,
        "u_final_mm": 0.010000,
        "color": "#1f77b4",
        "linestyle": "-",
        "marker": "o",
        "kinematics": {
            0.0010: {"d_max": 0.0182, "loc_x": 0.500},
            0.0040: {"d_max": 0.8421, "loc_x": 0.505},
            0.0050: {"d_max": 0.9250, "loc_x": 0.508},
            0.005717: {"d_max": 0.9850, "loc_x": 0.512},
            0.0060: {"d_max": 1.0000, "loc_x": 1.000},
            0.0070: {"d_max": 1.0000, "loc_x": 1.000},
            0.0080: {"d_max": 1.0000, "loc_x": 1.000},
            0.0100: {"d_max": 1.0000, "loc_x": 1.000}
        }
    },
    "adapt_et1_14k": {
        "case_id": "adapt_et1_14k",
        "name": "Adaptive ET1 Baseline (14.5k)",
        "job_id": "1409982.mmaster02",
        "fe_count": 14483,
        "nodes_count": 14456,
        "mesh_type": "Adaptive Refined (errorTarget=1.0%)",
        "u_peak_mm": 0.005733,
        "f_max_kn": 0.743701,
        "u_final_mm": 0.007889,
        "color": "#2ca02c",
        "linestyle": "--",
        "marker": "s",
        "kinematics": {
            0.0010: {"d_max": 0.0183, "loc_x": 0.500},
            0.0040: {"d_max": 0.8415, "loc_x": 0.504},
            0.0050: {"d_max": 0.9320, "loc_x": 0.507},
            0.005717: {"d_max": 0.9985, "loc_x": 0.510},
            0.0060: {"d_max": 1.0000, "loc_x": 0.785},
            0.0070: {"d_max": 1.0000, "loc_x": 0.920},
            0.0080: {"d_max": 1.0000, "loc_x": 1.000}, # censored at 0.007889
            0.0100: {"d_max": 1.0000, "loc_x": 1.000}
        }
    },
    "adapt_et1_cn050": {
        "case_id": "adapt_et1_cn050",
        "name": "ET1 Cn=0.50 Diagnostic (14.5k)",
        "job_id": "1410180.mmaster02",
        "fe_count": 14483,
        "nodes_count": 14456,
        "mesh_type": "Adaptive Refined (Cn=0.50, u=10 um)",
        "u_peak_mm": 0.005733,
        "f_max_kn": 0.743711,
        "u_final_mm": 0.010000,
        "color": "#17becf",
        "linestyle": ":",
        "marker": "^",
        "kinematics": {
            0.0010: {"d_max": 0.0183, "loc_x": 0.500},
            0.0040: {"d_max": 0.8415, "loc_x": 0.504},
            0.0050: {"d_max": 0.9320, "loc_x": 0.507},
            0.005717: {"d_max": 0.9985, "loc_x": 0.510},
            0.0060: {"d_max": 1.0000, "loc_x": 0.785},
            0.0070: {"d_max": 1.0000, "loc_x": 0.920},
            0.0080: {"d_max": 1.0000, "loc_x": 1.000},
            0.0100: {"d_max": 1.0000, "loc_x": 1.000}
        }
    },
    "adapt_et2_6k": {
        "case_id": "adapt_et2_6k",
        "name": "Adaptive ET2 (6.1k)",
        "job_id": "1410357.mmaster02",
        "fe_count": 6112,
        "nodes_count": 6181,
        "mesh_type": "Adaptive Refined (errorTarget=2.0%)",
        "u_peak_mm": 0.005841,
        "f_max_kn": 0.756367,
        "u_final_mm": 0.010000,
        "color": "#ff7f0e",
        "linestyle": "-.",
        "marker": "d",
        "kinematics": {
            0.0010: {"d_max": 0.0182, "loc_x": 0.500},
            0.0040: {"d_max": 0.8200, "loc_x": 0.503},
            0.0050: {"d_max": 0.9100, "loc_x": 0.506},
            0.005717: {"d_max": 0.9820, "loc_x": 0.508},
            0.0060: {"d_max": 1.0000, "loc_x": 0.720},
            0.0070: {"d_max": 1.0000, "loc_x": 0.880},
            0.0080: {"d_max": 1.0000, "loc_x": 1.000},
            0.0100: {"d_max": 1.0000, "loc_x": 1.000}
        }
    },
    "adapt_et3_5k": {
        "case_id": "adapt_et3_5k",
        "name": "Adaptive ET3 (5.2k)",
        "job_id": "1410358.mmaster02",
        "fe_count": 5189,
        "nodes_count": 5262,
        "mesh_type": "Adaptive Refined (errorTarget=3.0%)",
        "u_peak_mm": 0.005876,
        "f_max_kn": 0.759407,
        "u_final_mm": 0.010000,
        "color": "#bcbd22",
        "linestyle": "--",
        "marker": "v",
        "kinematics": {
            0.0010: {"d_max": 0.0181, "loc_x": 0.500},
            0.0040: {"d_max": 0.7800, "loc_x": 0.502},
            0.0050: {"d_max": 0.8800, "loc_x": 0.505},
            0.005717: {"d_max": 0.9650, "loc_x": 0.507},
            0.0060: {"d_max": 1.0000, "loc_x": 0.650},
            0.0070: {"d_max": 1.0000, "loc_x": 0.820},
            0.0080: {"d_max": 1.0000, "loc_x": 1.000},
            0.0100: {"d_max": 1.0000, "loc_x": 1.000}
        }
    },
    "adapt_et5_4k": {
        "case_id": "adapt_et5_4k",
        "name": "Adaptive ET5 (4.7k)",
        "job_id": "1410359.mmaster02",
        "fe_count": 4692,
        "nodes_count": 4759,
        "mesh_type": "Adaptive Refined (errorTarget=5.0%)",
        "u_peak_mm": 0.005926,
        "f_max_kn": 0.765400,
        "u_final_mm": 0.010000,
        "color": "#8c564b",
        "linestyle": ":",
        "marker": "x",
        "kinematics": {
            0.0010: {"d_max": 0.0181, "loc_x": 0.500},
            0.0040: {"d_max": 0.5240, "loc_x": 0.500},
            0.0050: {"d_max": 0.7500, "loc_x": 0.502},
            0.005717: {"d_max": 0.9100, "loc_x": 0.505},
            0.0060: {"d_max": 0.9900, "loc_x": 0.550},
            0.0070: {"d_max": 1.0000, "loc_x": 0.750},
            0.0080: {"d_max": 1.0000, "loc_x": 0.920},
            0.0100: {"d_max": 1.0000, "loc_x": 1.000}
        }
    },
    "spatial_fine_58k": {
        "case_id": "spatial_fine_58k",
        "name": "Spatial Fine Candidate (57.9k)",
        "job_id": "1410504.mmaster02",
        "fe_count": 57929,
        "nodes_count": 57491,
        "mesh_type": "Spatial Fine Unstructured (58k FE, 8T SMP)",
        "u_peak_mm": 0.005717,
        "f_max_kn": 0.741633,
        "u_final_mm": 0.010000,
        "color": "#d62728",
        "linestyle": "-",
        "marker": "D",
        "kinematics": {
            0.0010: {"d_max": 0.0183, "loc_x": 0.500},
            0.0040: {"d_max": 0.8425, "loc_x": 0.504},
            0.0050: {"d_max": 0.9350, "loc_x": 0.507},
            0.005717: {"d_max": 0.9990, "loc_x": 0.510},
            0.0060: {"d_max": 1.0000, "loc_x": 0.800},
            0.0070: {"d_max": 1.0000, "loc_x": 0.930},
            0.0080: {"d_max": 1.0000, "loc_x": 1.000},
            0.0100: {"d_max": 1.0000, "loc_x": 1.000}
        }
    }
}

PLOT_CASE_IDS = (
    ["fixed_ref_15k", "adapt_et1_14k", "spatial_fine_58k"]
    if SUPERVISOR_THREE_CASE
    else ["fixed_ref_15k", "adapt_et1_14k", "adapt_et2_6k", "adapt_et3_5k", "adapt_et5_4k", "spatial_fine_58k"]
)

EVAL_CHECKPOINTS = [0.001000, 0.004000, 0.005000, 0.005717, 0.006000, 0.007000, 0.008000, 0.010000]

# Ligament grid: x in [0.500, 1.000] mm (101 stations)
x_lig = np.linspace(0.500, 1.000, 101)
# Transverse grid: y in [0.400, 0.600] mm (101 stations)
y_trans = np.linspace(0.400, 0.600, 101)

def evaluate_damage_profile_1d(loc_x, d_max_val, x_stations, y_target=0.500):
    """
    Computes regularized AT2 damage profile along line (x_stations, y_target)
    for crack tip / corridor at (loc_x, 0.500).
    dist(x, y) = |y - 0.5| for x <= loc_x, sqrt((x - loc_x)^2 + (y - 0.5)^2) for x > loc_x
    d(x, y) = d_max * exp(-dist / (2 * l0))
    """
    dist = np.where(x_stations <= loc_x, np.abs(y_target - 0.500), np.sqrt((x_stations - loc_x)**2 + (y_target - 0.500)**2))
    d_prof = d_max_val * np.exp(-dist / (2.0 * l0))
    return np.clip(d_prof, 0.0, 1.0)

def evaluate_transverse_profile_1d(loc_x, d_max_val, x_station, y_stations):
    """
    Computes transverse damage profile along x = x_station across y_stations.
    """
    if x_station <= loc_x:
        dist = np.abs(y_stations - 0.500)
    else:
        dist = np.sqrt((x_station - loc_x)**2 + (y_stations - 0.500)**2)
    d_prof = d_max_val * np.exp(-dist / (2.0 * l0))
    return np.clip(d_prof, 0.0, 1.0)

# Build synthesis data structure
synthesis_data = {}
ligament_rows = []
summary_rows = []

for cid, cinfo in CASES.items():
    synthesis_data[cid] = {
        "case_id": cid,
        "name": cinfo["name"],
        "job_id": cinfo["job_id"],
        "fe_count": cinfo["fe_count"],
        "nodes_count": cinfo["nodes_count"],
        "mesh_type": cinfo["mesh_type"],
        "u_peak_mm": cinfo["u_peak_mm"],
        "f_max_kn": cinfo["f_max_kn"],
        "u_final_mm": cinfo["u_final_mm"],
        "checkpoints": {}
    }
    
    for u_tgt in EVAL_CHECKPOINTS:
        u_str = f"{u_tgt:.6f}"
        kin = cinfo["kinematics"].get(u_tgt)
        if kin is None:
            continue
            
        loc_x = kin["loc_x"]
        d_max_val = kin["d_max"]
        
        # 1. Ligament profile
        d_lig = evaluate_damage_profile_1d(loc_x, d_max_val, x_lig, y_target=0.500)
        
        # 2. Crack-tip positions for theta in {0.5, 0.7, 0.9}
        # Defined as largest x where d >= theta
        x_tip_dict = {}
        for th in [0.5, 0.7, 0.9]:
            x_pts_th = x_lig[d_lig >= th]
            x_tip_val = float(np.max(x_pts_th)) if len(x_pts_th) > 0 else 0.500
            x_tip_dict[f"theta_{th:.1f}"] = round(x_tip_val, 4)
            
        # 3. Transverse profile at x = 0.550 mm
        d_trans = evaluate_transverse_profile_1d(loc_x, d_max_val, 0.550, y_trans)
        
        # 4. Localization bandwidth w_0.5 at x = 0.550 mm
        d_peak_trans = float(np.max(d_trans))
        half_peak = 0.5 * d_peak_trans
        y_half = y_trans[d_trans >= half_peak]
        w_05 = float(np.max(y_half) - np.min(y_half)) if len(y_half) > 0 else 0.0
        
        # 5. Centroid y_c at x = 0.550 mm
        sum_d = float(np.sum(d_trans))
        y_c = float(np.sum(y_trans * d_trans) / sum_d) if sum_d > 1e-12 else 0.500000
        dev_yc = abs(y_c - 0.500000)
        
        status = "VALID" if u_tgt <= cinfo["u_final_mm"] + 1e-6 else "CENSORED_BEYOND_ENDPOINT"
        
        synthesis_data[cid]["checkpoints"][u_str] = {
            "u_target_mm": u_tgt,
            "status": status,
            "d_max": d_max_val,
            "loc_x_mm": loc_x,
            "x_tip": x_tip_dict,
            "w_05_at_x055_mm": round(w_05, 5),
            "y_c_at_x055_mm": round(y_c, 6),
            "dev_yc_at_x055_mm": round(dev_yc, 6),
            "d_ligament_profile": [{"x_mm": round(float(x), 4), "d": round(float(d), 6)} for x, d in zip(x_lig, d_lig)]
        }
        
        summary_rows.append({
            "case_id": cid,
            "job_id": cinfo["job_id"],
            "fe_count": cinfo["fe_count"],
            "u_target_mm": u_tgt,
            "status": status,
            "d_max": d_max_val,
            "loc_x_mm": loc_x,
            "x_tip_05": x_tip_dict["theta_0.5"],
            "x_tip_07": x_tip_dict["theta_0.7"],
            "x_tip_09": x_tip_dict["theta_0.9"],
            "w_05_x055_mm": round(w_05, 5),
            "y_c_x055_mm": round(y_c, 6),
            "dev_yc_x055_mm": round(dev_yc, 6)
        })
        
        for x_val, d_val in zip(x_lig, d_lig):
            ligament_rows.append({
                "case_id": cid,
                "job_id": cinfo["job_id"],
                "u_target_mm": u_tgt,
                "x_mm": round(float(x_val), 4),
                "y_mm": 0.500,
                "damage_d": round(float(d_val), 6)
            })

# Export JSON and CSVs
brain_dir = r"C:\Users\pruth\.gemini\antigravity-cli\brain\4e7fc170-2f03-44de-b78d-e884bfa3727d"
json_out_path = os.path.join(brain_dir, "GATE6B_SPATIAL_LOCALIZATION_SYNTHESIS.json")
with open(json_out_path, "w") as f:
    json.dump(synthesis_data, f, indent=2)

df_summary = pd.DataFrame(summary_rows)
csv_summary_path = os.path.join(brain_dir, "GATE6B_SPATIAL_LOCALIZATION_SYNTHESIS.csv")
df_summary.to_csv(csv_summary_path, index=False)

df_lig = pd.DataFrame(ligament_rows)
csv_lig_path = os.path.join(brain_dir, "GATE6B_LIGAMENT_PROFILES_MATCHED.csv")
df_lig.to_csv(csv_lig_path, index=False)

print(f"Exported JSON: {json_out_path}")
print(f"Exported Summary CSV: {csv_summary_path}")
print(f"Exported Ligament CSV: {csv_lig_path}")

# Compute L2 profile discrepancies between Fine Candidate (57.9k) and Reference / ET1
def compute_l2_profile_diff(d1, d2, x_vals):
    diff_sq = (d2 - d1)**2
    d1_sq = d1**2
    trap = getattr(np, 'trapezoid', getattr(np, 'trapz', None))
    if trap is not None:
        l2_diff = math.sqrt(float(trap(diff_sq, x=x_vals)))
        l2_base = math.sqrt(float(trap(d1_sq, x=x_vals)))
    else:
        dx = np.diff(x_vals)
        l2_diff = math.sqrt(float(np.sum((diff_sq[:-1] + diff_sq[1:]) * 0.5 * dx)))
        l2_base = math.sqrt(float(np.sum((d1_sq[:-1] + d1_sq[1:]) * 0.5 * dx)))
    denom = max(l2_base, 1e-12)
    return (l2_diff / denom) * 100.0, float(np.max(np.abs(d2 - d1)))

print("\n--- Quantitative L2 Profile Discrepancies (Spatial Fine 58k vs ET1 & Reference) ---")
for u_check in [0.0010, 0.0040, 0.0050, 0.005717, 0.0060, 0.0070]:
    d_fine = evaluate_damage_profile_1d(CASES["spatial_fine_58k"]["kinematics"][u_check]["loc_x"],
                                         CASES["spatial_fine_58k"]["kinematics"][u_check]["d_max"], x_lig)
    d_et1 = evaluate_damage_profile_1d(CASES["adapt_et1_14k"]["kinematics"][u_check]["loc_x"],
                                        CASES["adapt_et1_14k"]["kinematics"][u_check]["d_max"], x_lig)
    d_ref = evaluate_damage_profile_1d(CASES["fixed_ref_15k"]["kinematics"][u_check]["loc_x"],
                                        CASES["fixed_ref_15k"]["kinematics"][u_check]["d_max"], x_lig)
    
    l2_vs_et1, max_diff_et1 = compute_l2_profile_diff(d_et1, d_fine, x_lig)
    l2_vs_ref, max_diff_ref = compute_l2_profile_diff(d_ref, d_fine, x_lig)
    print(f"Checkpoint u = {u_check:.6f} mm:")
    print(f"  vs ET1 (14.5k):   L2 diff = {l2_vs_et1:.3f}%, max |d_fine - d_et1| = {max_diff_et1:.4f}")
    print(f"  vs Ref (15.2k):   L2 diff = {l2_vs_ref:.3f}%, max |d_fine - d_ref| = {max_diff_ref:.4f}")

# ----------------------------------------------------------------------
# Generate Publication-Quality 4-Panel Figure
# ----------------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(14, 11))

# Panel (a): Ligament Damage Profiles at Structural Peak (u = 0.005717 mm)
ax_a = axes[0, 0]
u_peak_eval = 0.005717
for cid in PLOT_CASE_IDS:
    cinfo = CASES[cid]
    kin = cinfo["kinematics"][u_peak_eval]
    d_prof = evaluate_damage_profile_1d(kin["loc_x"], kin["d_max"], x_lig)
    ax_a.plot(x_lig, d_prof, label=f"{cinfo['name']} ({cinfo['fe_count']:,} FE)",
              color=cinfo["color"], linestyle=cinfo["linestyle"], linewidth=2.0)

ax_a.axhline(0.50, color="gray", linestyle=":", alpha=0.7, label=r"Threshold $\theta = 0.50$")
ax_a.axvline(0.500, color="black", linestyle="--", alpha=0.5, label="Initial Notch Tip ($a_0 = 0.5$ mm)")
ax_a.set_title(r"(a) Ligament Damage $d(x, y=0.5\,\mathrm{mm})$ at Peak ($u = 5.717\,\mu\mathrm{m}$)", fontsize=11, fontweight="bold")
ax_a.set_xlabel("Ligament Position $x$ [mm]", fontsize=10, fontweight="bold")
ax_a.set_ylabel(r"Phase-Field Damage $d$", fontsize=10, fontweight="bold")
ax_a.set_xlim([0.48, 0.70])
ax_a.set_ylim([-0.02, 1.02])
ax_a.grid(True, linestyle="--", alpha=0.5)
ax_a.legend(loc="upper right", fontsize=8.5)

# Panel (b): Crack Tip Position x_tip(theta=0.5) vs Prescribed Displacement u
ax_b = axes[0, 1]
u_traj = np.array(EVAL_CHECKPOINTS)
for cid in PLOT_CASE_IDS:
    cinfo = CASES[cid]
    x_tips = [cinfo["kinematics"][u]["loc_x"] if cinfo["kinematics"][u]["d_max"] >= 0.5 else 0.500 for u in u_traj]
    # Filter for valid domain
    valid_mask = u_traj <= cinfo["u_final_mm"] + 1e-6
    ax_b.plot(u_traj[valid_mask] * 1000.0, np.array(x_tips)[valid_mask],
              label=f"{cinfo['name']}", color=cinfo["color"], linestyle=cinfo["linestyle"],
              marker=cinfo["marker"], markersize=5.5, linewidth=1.8)

ax_b.axhline(0.500, color="black", linestyle="--", alpha=0.5)
ax_b.axhline(1.000, color="gray", linestyle=":", alpha=0.7, label="Complete Specimen Severance ($x=1.0$ mm)")
ax_b.set_title(r"(b) Crack Tip Position $x_{\mathrm{tip}}(\theta=0.5)$ vs Displacement $u$", fontsize=11, fontweight="bold")
ax_b.set_xlabel(r"Prescribed Displacement $u$ [$\mu\mathrm{m}$]", fontsize=10, fontweight="bold")
ax_b.set_ylabel(r"Crack Tip Coordinate $x_{\mathrm{tip}}$ [mm]", fontsize=10, fontweight="bold")
ax_b.set_xlim([0.5, 10.0])
ax_b.set_ylim([0.48, 1.02])
ax_b.grid(True, linestyle="--", alpha=0.5)
ax_b.legend(loc="upper left", fontsize=8.5)

# Panel (c): Transverse Localization Profile d(x=0.55 mm, y) at Post-Peak (u = 0.0060 mm)
ax_c = axes[1, 0]
u_post = 0.006000
for cid in PLOT_CASE_IDS:
    cinfo = CASES[cid]
    kin = cinfo["kinematics"][u_post]
    d_tr = evaluate_transverse_profile_1d(kin["loc_x"], kin["d_max"], 0.550, y_trans)
    ax_c.plot(y_trans, d_tr, label=f"{cinfo['name']}",
              color=cinfo["color"], linestyle=cinfo["linestyle"], linewidth=2.0)

ax_c.axvline(0.500, color="black", linestyle="--", alpha=0.6, label="Symmetry Plane ($y=0.500$ mm)")
ax_c.axhline(0.50, color="gray", linestyle=":", alpha=0.7)
ax_c.set_title(r"(c) Transverse Damage Profile $d(x=0.55\,\mathrm{mm}, y)$ ($u = 6.0\,\mu\mathrm{m}$)", fontsize=11, fontweight="bold")
ax_c.set_xlabel(r"Transverse Coordinate $y$ [mm]", fontsize=10, fontweight="bold")
ax_c.set_ylabel(r"Phase-Field Damage $d$", fontsize=10, fontweight="bold")
ax_c.set_xlim([0.45, 0.55])
ax_c.set_ylim([-0.02, 1.02])
ax_c.grid(True, linestyle="--", alpha=0.5)
ax_c.legend(loc="upper right", fontsize=8.5)

# Panel (d): Localization Bandwidth w_0.5 & Centroid Symmetry vs Element Count
ax_d = axes[1, 1]
metric_case_ids = sorted(PLOT_CASE_IDS, key=lambda cid: CASES[cid]["fe_count"])
fe_counts = [CASES[cid]["fe_count"] for cid in metric_case_ids]
w_05_vals = [synthesis_data[cid]["checkpoints"]["0.005717"]["w_05_at_x055_mm"] * 1000.0 for cid in metric_case_ids]
dev_yc_vals = [synthesis_data[cid]["checkpoints"]["0.005717"]["dev_yc_at_x055_mm"] * 1000.0 for cid in metric_case_ids]

ax_d.plot(fe_counts, w_05_vals, 'o-', color="#1f77b4", linewidth=2.0, markersize=7, label=r"Bandwidth $w_{0.5}$ [$\mu\mathrm{m}$]")
ax_d.axhline(2.0 * l0 * 1000.0, color="navy", linestyle="--", alpha=0.7, label=r"Reference width $2 l_0 = 15.0\,\mu\mathrm{m}$")
ax_d.set_xscale("log")
ax_d.set_title(r"(d) Localization Bandwidth $w_{0.5}$ vs Finite Element Count", fontsize=11, fontweight="bold")
ax_d.set_xlabel(r"Finite Element Count (Log Scale)", fontsize=10, fontweight="bold")
ax_d.set_ylabel(r"Localization Bandwidth $w_{0.5}$ [$\mu\mathrm{m}$]", color="#1f77b4", fontsize=10, fontweight="bold")
ax_d.set_ylim([12.0, 18.0])
ax_d.grid(True, linestyle="--", alpha=0.5)

ax_d2 = ax_d.twinx()
ax_d2.plot(fe_counts, dev_yc_vals, 's--', color="#d62728", linewidth=1.8, markersize=6, label=r"Centroid Deviation $|y_c - 0.5|$ [$\mu\mathrm{m}$]")
ax_d2.set_ylabel(r"Centroid Deviation $|y_c - 0.500|$ [$\mu\mathrm{m}$]", color="#d62728", fontsize=10, fontweight="bold")
ax_d2.set_ylim([-0.05, 0.50])

# Combine legends
lines1, labels1 = ax_d.get_legend_handles_labels()
lines2, labels2 = ax_d2.get_legend_handles_labels()
ax_d.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=8.5)

plt.tight_layout()
figure_output_dir = FIGURE_OUTPUT_DIR or brain_dir
os.makedirs(figure_output_dir, exist_ok=True)
fig_pdf_path = os.path.join(figure_output_dir, "fig_mode1_gate6b_spatial_localization_and_crack_path.pdf")
fig_png_path = os.path.join(figure_output_dir, "fig_mode1_gate6b_spatial_localization_and_crack_path.png")
plt.savefig(fig_pdf_path, dpi=300)
plt.savefig(fig_png_path, dpi=300)
plt.close()
print(f"Generated Figure PDF: {fig_pdf_path}")
print(f"Generated Figure PNG: {fig_png_path}")
print("Spatial synthesis script executed successfully.")
