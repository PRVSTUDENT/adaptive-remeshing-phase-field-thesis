"""
Compare Post-Snap Continuation: Case A Reference vs Case B Offset Continuation
"""

import os
import json

scratch_dir = "/scratch9/pr21vyci/runs/mode1_experimental_offset_diagnostic"
dat_a = os.path.join(scratch_dir, "CaseA_cracked_solve.dat")
dat_b = os.path.join(scratch_dir, "CaseB_cracked_solve.dat")

def parse_rf_tables(dat_path):
    with open(dat_path, 'r') as f:
        text = f.read()
    sections = text.split("THE FOLLOWING TABLE IS PRINTED FOR NODES BELONGING TO NODE SET N_RP")
    rf_data = []
    for sec in sections[1:]:
        for line in sec.splitlines():
            line = line.strip()
            if not line or "Abaqus" in line or "Date" in line or "Time" in line or "PAGE" in line or "Page" in line:
                continue
            if line.startswith("MAXIMUM"):
                break
            if line.startswith("NODE") or line.startswith("MINIMUM") or line.startswith("AT NODE"):
                continue
            parts = line.split()
            if len(parts) >= 3:
                try:
                    nid = int(parts[0])
                    u2 = float(parts[1])
                    rf2 = float(parts[2])
                    rf_data.append({"node": nid, "u2_mm": u2, "rf2_kN": rf2, "rf2_N": rf2 * 1000.0})
                except ValueError:
                    pass
    return rf_data

rf_a = parse_rf_tables(dat_a)
rf_b = parse_rf_tables(dat_b)

print("=== POST-SNAP CONTINUATION REACTION FORCE COMPARISON ===")
print("Total Case A RF entries: %d" % len(rf_a))
print("Total Case B RF entries: %d" % len(rf_b))

# Print all Case B entries
print("\n--- All Case B Reaction Force Entries ---")
for i, entry in enumerate(rf_b):
    print("Case B Entry %d: U2 = %.6e mm, RF2 = %.6f N" % (i, entry["u2_mm"], entry["rf2_N"]))

# Case A reference points:
# Inc 64: Step 2 inc 1 (u = 0.00254 mm) -> Post-snap baseline
# Inc 65: Step 2 inc 2 (u = 0.00258 mm)
# Inc 66: Step 2 inc 3 (u = 0.00262 mm)
# Inc 67: Step 2 inc 4 (u = 0.00266 mm)
# Inc 68: Step 2 inc 5 (u = 0.00270 mm)

case_a_postsnap_rf = [
    rf_a[63], # Inc 64 (0-indexed: 63): u = 0.00254 mm
    rf_a[64], # Inc 65: u = 0.00258 mm
    rf_a[65], # Inc 66: u = 0.00262 mm
    rf_a[66], # Inc 67: u = 0.00266 mm
    rf_a[67], # Inc 68: u = 0.00270 mm
]

print("\n--- Step 1: Zero-Increment State Reconstruction (u = 0.00254 mm) ---")
rf_a_0 = case_a_postsnap_rf[0]["rf2_N"]
if len(rf_b) > 0:
    rf_b_0 = rf_b[0]["rf2_N"]
    err_0 = abs(rf_b_0 - rf_a_0) / abs(rf_a_0) * 100.0
    print("Case A Reference RF2:  %.6f N" % rf_a_0)
    print("Case B Reconstructed:  %.6f N" % rf_b_0)
    print("Zero-Increment Discontinuity: %.4f%%" % err_0)
else:
    print("Case B RF table empty!")

print("\n--- Step 2: Forward Continuation Parity ---")
comparison_rows = []
for i in range(1, 5):
    target_u = 0.00254 + i * 0.00004
    rf_a_val = case_a_postsnap_rf[i]["rf2_N"]
    if len(rf_b) > i:
        rf_b_val = rf_b[i]["rf2_N"]
        err = abs(rf_b_val - rf_a_val) / abs(rf_a_val) * 100.0
        print("Inc %d (u = %.5f mm): Case A = %.6f N, Case B = %.6f N | Error = %.4f%%" % 
              (i, target_u, rf_a_val, rf_b_val, err))
        comparison_rows.append({
            "increment": i,
            "target_u_mm": target_u,
            "case_a_rf2_N": rf_a_val,
            "case_b_rf2_N": rf_b_val,
            "rel_error_pct": err
        })
    else:
        print("Inc %d: Case B entry missing!" % i)

# Write comparison JSON
summary = {
    "zero_increment_u_mm": 0.00254,
    "zero_increment_case_a_rf2_N": rf_a_0,
    "zero_increment_case_b_rf2_N": rf_b[0]["rf2_N"] if len(rf_b) > 0 else None,
    "zero_increment_rel_error_pct": err_0 if len(rf_b) > 0 else None,
    "step2_continuation_rows": comparison_rows
}

with open(os.path.join(scratch_dir, "postsnap_continuation_parity.json"), 'w') as f:
    json.dump(summary, f, indent=2)

print("\nWrote postsnap_continuation_parity.json")
