"""
Compare Energy Continuity between Case A and Case B
"""

import os
import json

scratch_dir = "/scratch9/pr21vyci/runs/mode1_experimental_offset_diagnostic"
dat_a = os.path.join(scratch_dir, "CaseA_cracked_solve.dat")
dat_b = os.path.join(scratch_dir, "CaseB_cracked_solve.dat")

def parse_energy_tables(dat_path):
    with open(dat_path, 'r') as f:
        text = f.read()
    sections = text.split("TOTAL ENERGIES")
    energy_records = []
    for sec in sections[1:]:
        for line in sec.splitlines():
            line = line.strip()
            if not line or "Abaqus" in line or "Date" in line or "Time" in line or "PAGE" in line or "Page" in line:
                continue
            if line.startswith("TOTAL") or line.startswith("STEP") or line.startswith("INCREMENT"):
                continue
            parts = line.split()
            # Typically columns: ALLSE, ALLVD, ALLCD, ALLWK, ALLKE, ALLPD, ALLIE, ALLAE, ALLFD, ETOTAL
            # Or similar
            if len(parts) >= 8:
                try:
                    vals = [float(p) for p in parts]
                    energy_records.append(vals)
                except ValueError:
                    pass
    return energy_records

e_a = parse_energy_tables(dat_a)
e_b = parse_energy_tables(dat_b)

print("=== ENERGY HISTORY COMPARISON ===")
print("Case A total energy records: %d" % len(e_a))
print("Case B total energy records: %d" % len(e_b))

# Also read history from ODB for both
from odbAccess import openOdb
odb_a = openOdb(os.path.join(scratch_dir, "CaseA_cracked_solve.odb"))
odb_b = openOdb(os.path.join(scratch_dir, "CaseB_cracked_solve.odb"))

def get_history_energy(odb):
    res = {}
    for step_name in odb.steps.keys():
        st = odb.steps[step_name]
        res[step_name] = {}
        for region_name in st.historyRegions.keys():
            hr = st.historyRegions[region_name]
            for hk in hr.historyOutputs.keys():
                ho = hr.historyOutputs[hk]
                res[step_name][hk] = [d[1] for d in ho.data]
    return res

h_a = get_history_energy(odb_a)
h_b = get_history_energy(odb_b)

odb_a.close()
odb_b.close()

print("\n--- History Energies in Case B ---")
for step_name, d in h_b.items():
    print("Step: %s" % step_name)
    for k in sorted(d.keys()):
        if len(d[k]) > 0:
            print("  %s: initial = %e, final = %e" % (k, d[k][0], d[k][-1]))

# Plateau reference in Case A:
# Step 2 inc 2 is index 2 of Step-2
print("\n--- Comparison of Energies at Plateau Baseline ---")
allie_a_plateau = h_a["Step-2"]["ALLIE"][2] # Step 2 inc 2
allse_a_plateau = h_a["Step-2"]["ALLSE"][2]
allwk_a_plateau = h_a["Step-2"]["ALLWK"][2]

allie_b_step1 = h_b["Step-1"]["ALLIE"][-1]
allse_b_step1 = h_b["Step-1"]["ALLSE"][-1]
allwk_b_step1 = h_b["Step-1"]["ALLWK"][-1]

print("Case A Plateau (u=0.00258 mm): ALLIE = %e, ALLSE = %e, ALLWK = %e" % (allie_a_plateau, allse_a_plateau, allwk_a_plateau))
print("Case B Step 1 (reconstructed): ALLIE = %e, ALLSE = %e, ALLWK = %e" % (allie_b_step1, allse_b_step1, allwk_b_step1))

err_se = abs(allse_b_step1 - allse_a_plateau) / abs(allse_a_plateau) * 100.0 if allse_a_plateau != 0 else 0
print("Strain Energy (ALLSE) Error: %.4f%%" % err_se)

energy_summary = {
    "allie_case_a_plateau": allie_a_plateau,
    "allse_case_a_plateau": allse_a_plateau,
    "allwk_case_a_plateau": allwk_a_plateau,
    "allie_case_b_step1": allie_b_step1,
    "allse_case_b_step1": allse_b_step1,
    "allwk_case_b_step1": allwk_b_step1,
    "strain_energy_rel_error_pct": err_se
}

with open(os.path.join(scratch_dir, "plateau_energy_parity.json"), 'w') as f:
    json.dump(energy_summary, f, indent=2)

print("Wrote plateau_energy_parity.json")
