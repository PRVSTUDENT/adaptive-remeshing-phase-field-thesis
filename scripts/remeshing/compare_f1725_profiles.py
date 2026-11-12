import json

p = 'models/pandey_kumar_mode1/217_f1725_physics_study/f1725_physics_study_results.json'
with open(p, 'r') as f:
    d = json.load(f)

cases_to_compare = [
    "F1725_S1_ET350",
    "F1725_S2_ET345",
    "F1725_S2_COARSEN_ET315"
]

print("CENTERLINE PROFILES COMPARISON (bin width = 10% of ligament clearance)")
for lig in ["Ligament 1", "Ligament 2", "Ligament 3", "Ligament 4"]:
    print("\n" + "=" * 90)
    print(f">>> {lig} <<<")
    header = f"{'Case Name':<25} | {'Count':<5} |"
    for b in range(10):
        header += f" t={b*0.1+0.05:.2f} |"
    print(header)
    print("-" * 90)
    for c in cases_to_compare:
        prof = d[c]['metrics']['centerline_profiles'][lig]
        row = f"{c:<25} | {prof['count']:<5} |"
        for val in prof['profile_bins']:
            row += f" {val:5.2f}u |"
        print(row)
