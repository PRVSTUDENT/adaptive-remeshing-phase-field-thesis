import os
import sys
import json
import math

# Paths
base_dir = "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/batch_mode1_energy_convergence/S1_h0030_15k"
diag_dir = "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/batch_mode1_energy_convergence/S1_h0030_15k_diagnostic_r2"

base_dat = os.path.join(base_dir, "PK_M1_S1_H0030.dat")
diag_dat = os.path.join(diag_dir, "PK_M1_S1_DIAG_R2.dat")

base_json = os.path.join(base_dir, "CANONICAL_S1_1406015_REHARVEST.json")
diag_eb = os.path.join(diag_dir, "uel_energy_balance.csv")

print("================================================================================")
print("STAGE 1 -> STAGE 5 TERMINAL EVALUATION & MECHANICAL PARITY AUDIT")
print("Job 1406839.mmaster02 (Diagnostic R2) vs Job 1406015.mmaster02 (Canonical Baseline)")
print("================================================================================")

def parse_dat(dat_path):
    u_list, rf_list = [], []
    with open(dat_path, "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) == 3 and parts[0] == "999999":
                try:
                    u_list.append(float(parts[1]))
                    rf_list.append(float(parts[2]))
                except ValueError:
                    pass
    return u_list, rf_list

u_base, rf_base = parse_dat(base_dat)
u_diag, rf_diag = parse_dat(diag_dat)

print("\n--- 1. PARSED DAT FILES ---")
print("Baseline 1406015 DAT points: " + str(len(u_base)))
print("Diagnostic 1406839 DAT points: " + str(len(u_diag)))

# Initial stiffness K0 (linear regression over first 400 increments)
def calc_k0(u_list, rf_list, n=400):
    x = u_list[:n]
    y = rf_list[:n]
    x_mean = sum(x) / n
    y_mean = sum(y) / n
    num = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    den = sum((x[i] - x_mean)**2 for i in range(n))
    slope = num / den
    intercept = y_mean - slope * x_mean
    ss_tot = sum((y[i] - y_mean)**2 for i in range(n))
    ss_res = sum((y[i] - (slope * x[i] + intercept))**2 for i in range(n))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
    return slope, intercept, r2

k0_base, b_base, r2_base = calc_k0(u_base, rf_base)
k0_diag, b_diag, r2_diag = calc_k0(u_diag, rf_diag)

fmax_base = max(rf_base)
idx_base = rf_base.index(fmax_base)
u_fmax_base = u_base[idx_base]

fmax_diag = max(rf_diag)
idx_diag = rf_diag.index(fmax_diag)
u_fmax_diag = u_diag[idx_diag]

print("\n--- 2. CANONICAL MECHANICAL METRICS ---")
print("Baseline 1406015:")
print("  K0        = " + str(k0_base) + " kN/mm (Intercept: " + str(b_base) + " kN, R^2 = " + str(r2_base) + ")")
print("  F_max     = " + str(fmax_base) + " kN (at index " + str(idx_base+1) + ")")
print("  u(F_max)  = " + str(u_fmax_base) + " mm")
print("  Final RF  = " + str(rf_base[-1]) + " kN at u = " + str(u_base[-1]) + " mm")

print("\nDiagnostic 1406839:")
print("  K0        = " + str(k0_diag) + " kN/mm (Intercept: " + str(b_diag) + " kN, R^2 = " + str(r2_diag) + ")")
print("  F_max     = " + str(fmax_diag) + " kN (at index " + str(idx_diag+1) + ")")
print("  u(F_max)  = " + str(u_fmax_diag) + " mm")
print("  Final RF  = " + str(rf_diag[-1]) + " kN at u = " + str(u_diag[-1]) + " mm")

delta_k0_rel = abs(k0_diag - k0_base) / k0_base * 100.0
delta_fmax_rel = abs(fmax_diag - fmax_base) / fmax_base * 100.0
delta_u_peak = abs(u_fmax_diag - u_fmax_base)

print("\n--- 3. MECHANICAL PARITY CRITERIA CHECKS ---")
print("1. |Delta K0| / K0 = " + str(delta_k0_rel) + " % (Threshold <= 0.05%): " + ("PASS" if delta_k0_rel <= 0.05 else "FAIL"))
print("2. |Delta F_max| / F_max = " + str(delta_fmax_rel) + " % (Threshold <= 0.05%): " + ("PASS" if delta_fmax_rel <= 0.05 else "FAIL"))
print("3. |Delta u_peak| = " + str(delta_u_peak) + " mm (Threshold <= 1e-4 mm): " + ("PASS" if delta_u_peak <= 1e-4 else "FAIL"))

# Interpolation on common displacement domain
u_common_min = max(u_base[0], u_diag[0])
u_common_max = min(u_base[-1], u_diag[-1])
print("Common displacement domain: [" + str(u_common_min) + ", " + str(u_common_max) + "] mm")

# Helper for linear interpolation on monotonic array
def interp_1d(x_target, x_arr, y_arr):
    if x_target <= x_arr[0]:
        return y_arr[0]
    if x_target >= x_arr[-1]:
        return y_arr[-1]
    # binary search
    low = 0
    high = len(x_arr) - 1
    while high - low > 1:
        mid = (low + high) // 2
        if x_arr[mid] <= x_target:
            low = mid
        else:
            high = mid
    t = (x_target - x_arr[low]) / (x_arr[high] - x_arr[low])
    return y_arr[low] + t * (y_arr[high] - y_arr[low])

# Evaluate deviation at 10,000 common points
n_pts = 10000
u_eval = [u_common_min + i * (u_common_max - u_common_min) / (n_pts - 1) for i in range(n_pts)]
dev_pre = []
dev_full = []
for u in u_eval:
    rf_b = interp_1d(u, u_base, rf_base)
    rf_d = interp_1d(u, u_diag, rf_diag)
    rel_dev = abs(rf_d - rf_b) / fmax_base * 100.0
    dev_full.append(rel_dev)
    if u <= u_fmax_base:
        dev_pre.append(rel_dev)

max_dev_pre = max(dev_pre)
max_dev_full = max(dev_full)

print("4. Pre-peak normalized force deviation: " + str(max_dev_pre) + " % (Threshold <= 0.05%): " + ("PASS" if max_dev_pre <= 0.05 else "FAIL"))
print("5. Full common-horizon normalized force deviation: " + str(max_dev_full) + " % (Threshold <= 0.10%): " + ("PASS" if max_dev_full <= 0.10 else "FAIL"))

# External work quadratures (Left, Trapezoidal, Right Riemann)
def calc_work_quadratures(u_list, rf_list):
    w_left = 0.0
    w_trap = 0.0
    w_right = 0.0
    for i in range(1, len(u_list)):
        du = u_list[i] - u_list[i-1]
        w_left += rf_list[i-1] * du
        w_trap += 0.5 * (rf_list[i-1] + rf_list[i]) * du
        w_right += rf_list[i] * du
    return w_left, w_trap, w_right

w_left_b, w_trap_b, w_right_b = calc_work_quadratures(u_base, rf_base)
w_left_d, w_trap_d, w_right_d = calc_work_quadratures(u_diag, rf_diag)

print("\n--- 4. EXTERNAL WORK QUADRATURES ---")
print("Baseline 1406015 (through u = " + str(u_base[-1]) + " mm):")
print("  W_left  = " + str(w_left_b) + " kN*mm")
print("  W_trap  = " + str(w_trap_b) + " kN*mm")
print("  W_right = " + str(w_right_b) + " kN*mm")
print("  |W_right - W_left| = " + str(abs(w_right_b - w_left_b)) + " kN*mm")

print("Diagnostic 1406839 (through u = " + str(u_diag[-1]) + " mm):")
print("  W_left  = " + str(w_left_d) + " kN*mm")
print("  W_trap  = " + str(w_trap_d) + " kN*mm")
print("  W_right = " + str(w_right_d) + " kN*mm")
print("  |W_right - W_left| = " + str(abs(w_right_d - w_left_d)) + " kN*mm")

# Check canonical baseline json
if os.path.exists(base_json):
    with open(base_json, "r") as f:
        bj = json.load(f)
    print("\n--- 5. BASELINE 1406015 REHARVEST JSON STATE ---")
    print("Baseline keys: " + str(list(bj.keys())))
    if "terminal_energies" in bj:
        print("  terminal_energies: " + str(bj["terminal_energies"]))
    if "reconstructed_odb_energy" in bj:
        print("  reconstructed_odb_energy: " + str(bj["reconstructed_odb_energy"]))
    if "energy_balance" in bj:
        print("  energy_balance: " + str(bj["energy_balance"]))
    if "canonical_table_row" in bj:
        print("  canonical_table_row: " + str(bj["canonical_table_row"]))
