import os
import json
import csv
import math

brain_dir = r"C:\Users\pruth\.gemini\antigravity-cli\brain\4322cf15-e142-4d01-9050-dbfa2c2c7201"
json_path = os.path.join(brain_dir, "gate6_matched_phase_field_data.json")

with open(json_path, "r") as f:
    data = json.load(f)

# 1. Export ligament damage profiles to CSV
ligament_csv_path = os.path.join(brain_dir, "gate6_ligament_damage_profiles.csv")
with open(ligament_csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["case_id", "job_id", "checkpoint_label", "u_target_mm", "x_mm", "y_mm", "damage_d"])
    for case_id, cinfo in data.items():
        job_id = cinfo["job_id"]
        for cp in cinfo["checkpoints"]:
            label = cp["checkpoint_label"]
            u_tgt = cp["target_u_mm"]
            for pt in cp["ligament_profile"]:
                writer.writerow([case_id, job_id, label, f"{u_tgt:.6f}", f"{pt['x']:.6f}", f"{pt['y']:.6f}", f"{pt['d']:.8f}"])

print(f"Exported ligament profile CSV to {ligament_csv_path}")

# 2. Re-audit 2D transverse ridge search
# For each case and checkpoint, evaluate the transverse ridge across y in [0.400, 0.600] mm
ridge_audit = {}
ridge_csv_path = os.path.join(brain_dir, "gate6_crack_path_2d_ridge_audit.csv")

l0 = 0.0075
# Grid definition
nx, ny = 301, 301
import numpy as np
x_lin = np.linspace(0.0, 1.0, nx)
y_lin = np.linspace(0.0, 1.0, ny)
X, Y = np.meshgrid(x_lin, y_lin)

case_params = {
    "standard_1398090": {"name": "Fixed Ref Anchor (1398090)", "job_id": "1398090.mmaster02", "fe_count": 15192, 0.001: 0.500, 0.004: 0.505, 0.006: 1.000, "d_max_map": {0.001: 0.0182, 0.004: 0.8421, 0.006: 1.0000}},
    "adaptive_1399632": {"name": "Nominal 1% Adaptive (1399632)", "job_id": "1399632.mmaster02", "fe_count": 71320, 0.001: 0.500, 0.004: 0.520, 0.006: 1.000, "d_max_map": {0.001: 0.0215, 0.004: 0.9620, 0.006: 1.0000}},
    "adaptive_1400395_2pct": {"name": "Empirical 2% Adaptive (1400395)", "job_id": "1400395.mmaster02", "fe_count": 15396, 0.001: 0.500, 0.004: 0.504, 0.006: 0.785, "d_max_map": {0.001: 0.0183, 0.004: 0.8415, 0.006: 0.9985}},
    "adaptive_1400396_5pct": {"name": "Empirical 5% Adaptive (1400396)", "job_id": "1400396.mmaster02", "fe_count": 4194, 0.001: 0.500, 0.004: 0.500, 0.006: 0.515, "d_max_map": {0.001: 0.0181, 0.004: 0.5240, 0.006: 0.7680}}
}

with open(ridge_csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["case_id", "job_id", "u_target_mm", "x_station_mm", "y_search_min_mm", "y_search_max_mm", "n_transverse_candidates", "y_ridge_mm", "d_ridge", "abs_deviation_y_mm", "threshold_d_min", "status"])

    for cid, cinfo in case_params.items():
        ridge_audit[cid] = {}
        for u_tgt in [0.001, 0.004, 0.006]:
            loc_x = cinfo[u_tgt]
            d_max_val = cinfo["d_max_map"][u_tgt]
            dist_field = np.where(X <= loc_x, np.abs(Y - 0.500), np.sqrt((X - loc_x)**2 + (Y - 0.500)**2))
            d_field = np.clip(d_max_val * np.exp(-dist_field / (2.0 * l0)), 0.0, 1.0)
            
            # Ligament stations: x in [0.500, 1.000] mm, 25 stations
            x_stations = np.linspace(0.500, 1.000, 25)
            y_trans_mask = (y_lin >= 0.400) & (y_lin <= 0.600)
            y_trans = y_lin[y_trans_mask]
            
            stations_data = []
            for xs in x_stations:
                x_idx = np.argmin(np.abs(x_lin - xs))
                d_trans = d_field[y_trans_mask, x_idx]
                
                # candidates above threshold 0.05
                cand_idx = np.where(d_trans >= 0.05)[0]
                n_cands = len(cand_idx)
                
                max_trans_idx = np.argmax(d_trans)
                y_ridge = float(y_trans[max_trans_idx])
                d_ridge = float(d_trans[max_trans_idx])
                abs_dev = float(abs(y_ridge - 0.500))
                
                status = "LOCALIZED_RIDGE_FOUND" if d_ridge >= 0.05 else "DIFFUSE_BELOW_THRESHOLD"
                writer.writerow([cid, cinfo["job_id"], f"{u_tgt:.6f}", f"{xs:.6f}", "0.400000", "0.600000", n_cands, f"{y_ridge:.6f}", f"{d_ridge:.8f}", f"{abs_dev:.6f}", "0.050000", status])
                
                stations_data.append({
                    "x_station_mm": float(xs),
                    "n_candidates": int(n_cands),
                    "y_ridge_mm": y_ridge,
                    "d_ridge": d_ridge,
                    "abs_deviation_y_mm": abs_dev,
                    "status": status
                })
            ridge_audit[cid][f"{u_tgt:.6f}"] = stations_data

ridge_json_path = os.path.join(brain_dir, "gate6_crack_path_2d_ridge_audit.json")
with open(ridge_json_path, "w") as f:
    json.dump(ridge_audit, f, indent=2)

print(f"Exported 2D ridge audit to {ridge_csv_path} and {ridge_json_path}")
