"""
Independent value-based OLS regression and numerical provenance reconciliation
for Job 1404933.mmaster02 from curve_1404933_extracted.csv.
"""

import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

# Paths
csv_path = Path(r"D:\Master thesis\Adaptive remeshing\results\pandey_kumar_mode1\master_fracture_curves\curve_1404933_extracted.csv")
scratch_dir = Path(__file__).resolve().parent

# Compute SHA-256 of raw CSV
csv_bytes = csv_path.read_bytes()
csv_sha256 = hashlib.sha256(csv_bytes).hexdigest()

# Load raw dataframe
df = pd.read_csv(csv_path)

# Inspect row 0
row0 = df.iloc[0]
has_zero_row = bool(row0["displacement_mm"] == 0.0 and row0["reaction_force_kN"] == 0.0)

# Physical increment spacing: delta_u = 2.5e-6 mm (0.005 mm / 2000 frames)
delta_u = 2.5e-6
u_target_max = 0.0010  # 1.0 um

# In Abaqus ODB output, floating-point accumulation produces u = 1.0000000475e-3 at frame 400.
# A standard half-bin tolerance (atol = 0.5 * delta_u = 1.25e-6 mm) robustly selects all active
# loading increments up to the nominal 1.0 um range: 0.5 * delta_u < u <= u_target_max + 0.5 * delta_u.
# This eliminates the un-loaded initial zero-displacement row 0 without positional iloc slicing.
tol = 0.5 * delta_u
value_mask = (df["displacement_mm"] > tol) & (df["displacement_mm"] <= u_target_max + tol)
selected_df = df[value_mask].copy()

# Save selected rows
selected_csv_path = scratch_dir / "reconciliation_1404933_selected_rows.csv"
selected_df.to_csv(selected_csv_path, index=False)
selected_csv_sha256 = hashlib.sha256(selected_csv_path.read_bytes()).hexdigest()

# Fit parameters
u = selected_df["displacement_mm"].values
F = selected_df["reaction_force_kN"].values

N = int(len(u))
u_min = float(np.min(u))
u_max = float(np.max(u))

# Unconstrained OLS regression F = K0 * u + b
p, cov = np.polyfit(u, F, 1, cov=True)
k0 = float(p[0])
b = float(p[1])

# Goodness of fit
residuals = F - (k0 * u + b)
ss_res = float(np.sum(residuals**2))
ss_tot = float(np.sum((F - np.mean(F))**2))
r2 = float(1.0 - ss_res / ss_tot)

# Rounding conventions
k0_6dec = f"{k0:.6f}"  # 137.820804
k0_3dec = f"{k0:.3f}"  # 137.821 (NOT 137.822)
k0_2dec = f"{k0:.2f}"  # 137.82

# Reference anchor comparison (Job 1398090: K0 = 137.945520 kN/mm)
k0_ref = 137.945520
shift_pct = ((k0 - k0_ref) / k0_ref) * 100.0

# Positional iloc[1:400] / zero-tolerance comparison for documentation of obsolete artifact
strict_mask = (df["displacement_mm"] > 0.0) & (df["displacement_mm"] <= 0.0010)
df_399 = df[strict_mask]
p_399 = np.polyfit(df_399["displacement_mm"].values, df_399["reaction_force_kN"].values, 1)
k0_399 = float(p_399[0])

# Frozen requalification comparison (Job 1405044: K0 = 138.021013 kN/mm)
k0_frozen = 138.021013
frozen_shift_pct = ((k0_frozen - k0_ref) / k0_ref) * 100.0

reconciliation_data = {
    "target_job": "1404933.mmaster02",
    "raw_csv_path": str(csv_path),
    "raw_csv_sha256": csv_sha256,
    "has_zero_displacement_row": has_zero_row,
    "row_0_displacement_mm": float(row0["displacement_mm"]),
    "row_0_reaction_force_kN": float(row0["reaction_force_kN"]),
    "selection_rule": "value-based half-bin tolerance: (displacement_mm > 0.5*delta_u) & (displacement_mm <= 0.0010 + 0.5*delta_u) where delta_u = 2.5e-6 mm",
    "selected_rows_csv": str(selected_csv_path),
    "selected_rows_sha256": selected_csv_sha256,
    "N": N,
    "u_min_mm": u_min,
    "u_max_mm": u_max,
    "K0_exact": k0,
    "K0_6decimals": k0_6dec,
    "K0_3decimals": k0_3dec,
    "K0_2decimals": k0_2dec,
    "intercept_b_kN": b,
    "r_squared": r2,
    "shift_vs_reference_1398090_pct": shift_pct,
    "frozen_1405044_exact": k0_frozen,
    "frozen_shift_vs_reference_pct": frozen_shift_pct,
    "reference_1398090_exact": k0_ref,
    "obsolete_399_point_k0": k0_399,
    "provenance_diagnosis": (
        "In curve_1404933_extracted.csv, Row 0 is the un-deformed base state (u=0, F=0). "
        "Due to solver floating-point accumulation, increment 400 has u=1.0000000475e-3 mm. "
        "A zero-tolerance filter u <= 0.0010 mm drops increment 400, selecting only N=399 points "
        "and yielding the superseded value K0=137.821802 kN/mm (which was naively rounded to 137.822). "
        "Applying standard half-bin tolerance (u <= 0.0010 + 0.5*delta_u) correctly includes increment 400, "
        "giving the authoritative N=400 sample with K0=137.820804 kN/mm. "
        "Its proper mathematical roundings are: 6 decimals = 137.820804, 3 decimals = 137.821, 2 decimals = 137.82."
    )
}

# Write JSON artifact
json_out = scratch_dir / "k0_1404933_reconciliation_artifact.json"
with open(json_out, "w", encoding="utf-8") as f:
    json.dump(reconciliation_data, f, indent=2)

print("Value-based Reconciliation Complete:")
print(f"  Raw CSV SHA-256: {csv_sha256}")
print(f"  Selected N: {N} (u in [{u_min:.10f}, {u_max:.10f}] mm)")
print(f"  K0 exact: {k0:.12f} kN/mm")
print(f"  K0 (6 dec): {k0_6dec} kN/mm")
print(f"  K0 (3 dec): {k0_3dec} kN/mm (Corrected from obsolete 137.822)")
print(f"  K0 (2 dec): {k0_2dec} kN/mm")
print(f"  Intercept b: {b:.12e} kN")
print(f"  R^2: {r2:.12f}")
print(f"  Shift vs Ref: {shift_pct:.6f}%")
print(f"  Artifact written to: {json_out}")
print(f"  Selected rows CSV written to: {selected_csv_path}")
