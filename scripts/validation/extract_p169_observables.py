"""Extract reaction force of N_RP and energies at all steps."""

import re
from pathlib import Path

inp_path = Path("models/pandey_kumar_mode1/169_c4_two_checkpoint_reference/M1_C4_TWO_CHECKPOINT_REF.inp")
dat_path = Path("models/pandey_kumar_mode1/169_c4_two_checkpoint_reference/evidence/1419543.mmaster02/M1_C4_TWO_CHECKPOINT_REF.dat")
energy_path = Path("models/pandey_kumar_mode1/169_c4_two_checkpoint_reference/evidence/1419543.mmaster02/uel_energy_balance.csv")

with open(inp_path, "r") as f:
    inp_text = f.read()

nsets = {}
current_nset = None
for line in inp_text.splitlines():
    line = line.strip()
    if line.upper().startswith("*NSET"):
        m = re.search(r"NSET=([A-Za-z0-9_]+)", line, re.IGNORECASE)
        if m:
            current_nset = m.group(1).upper()
            nsets[current_nset] = []
        else:
            current_nset = None
    elif line.startswith("*"):
        current_nset = None
    elif current_nset:
        parts = [p.strip() for p in line.split(",") if p.strip()]
        for p in parts:
            try:
                nsets[current_nset].append(int(p))
            except ValueError:
                pass

rp_node = nsets["N_RP"][0]
print(f"N_RP node ID: {rp_node}")

with open(dat_path, "r", encoding="utf-8", errors="ignore") as f:
    dat_text = f.read()

tables = dat_text.split("THE FOLLOWING TABLE IS PRINTED FOR ALL NODES")

for t_idx in range(1, len(tables)):
    table_str = tables[t_idx]
    # find line starting with rp_node
    for line in table_str.splitlines():
        parts = line.strip().split()
        if parts and parts[0] == str(rp_node):
            print(f"Table {t_idx} (Step {t_idx}): node {rp_node} -> {line.strip()}")
            # The columns are: NODE, FOOTNOTE(optional), U1, U2, U3, RF1, RF2, RF3
            # Let's inspect parts
            print(f"  parts: {parts}")

# Also check energy records
energy_records = []
with open(energy_path, "r") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 7:
            try:
                energy_records.append({
                    "step": int(parts[0]),
                    "inc": int(parts[1]),
                    "tot_time": float(parts[2]),
                    "step_time": float(parts[3]),
                    "E_el": float(parts[4]),
                    "E_fr": float(parts[5]),
                    "E_tot": float(parts[6]),
                })
            except ValueError:
                pass

for s in [1, 2, 3, 4]:
    s_recs = [r for r in energy_records if r["step"] == s]
    if s_recs:
        last = s_recs[-1]
        print(f"Step {s} terminal energy: E_el={last['E_el']:.8e}, E_fr={last['E_fr']:.8e}, E_tot={last['E_tot']:.8e}")
