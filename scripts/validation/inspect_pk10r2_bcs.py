import re

inp_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp"

with open(inp_path, "r") as f:
    text = f.read()

# Check RP node
rp_match = re.findall(r"\*NSET,\s*NSET=N_RP\s*\n(\d+)", text, re.IGNORECASE)
print("N_RP match:", rp_match)

# Check N_TOP, N_BOTTOM
top_match = re.findall(r"\*NSET,\s*NSET=N_TOP", text, re.IGNORECASE)
bot_match = re.findall(r"\*NSET,\s*NSET=N_BOTTOM", text, re.IGNORECASE)
print("N_TOP defined:", len(top_match))
print("N_BOTTOM defined:", len(bot_match))

# Check EQUATION
eq_match = re.findall(r"\*EQUATION[\s\S]*?(?=\*|\Z)", text, re.IGNORECASE)
print("EQUATION block count:", len(eq_match))
if eq_match:
    print("EQUATION card sample:\n", eq_match[0][:200])

# Check BOUNDARY cards
bc_match = re.findall(r"\*BOUNDARY[\s\S]*?(?=\*|\Z)", text, re.IGNORECASE)
print("\nBOUNDARY blocks:")
for i, bc in enumerate(bc_match):
    print("--- BC Block %d ---" % (i+1))
    print(bc.strip())
