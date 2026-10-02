import os, sys, math, json

# 1. Audit Step 1 Phase Initialization in M2STATE_FRACFIX_RESTART2R3.inp
inp_path = "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R3/M2STATE_FRACFIX_RESTART2R3.inp"

total_nodes = 0
in_nodes = False
in_step1 = False
in_bcs = False
bcs_step1 = {}

with open(inp_path, "r") as f:
    for line in f:
        line_s = line.strip()
        if line_s.startswith("*NODE, NSET=N_PHYSICAL"):
            in_nodes = True
            continue
        elif in_nodes and line_s.startswith("*"):
            in_nodes = False
        
        if in_nodes and line_s:
            parts = [p.strip() for p in line_s.split(",")]
            if len(parts) >= 3 and parts[0].isdigit():
                nid = int(parts[0])
                if nid != 99999:
                    total_nodes += 1
                    
        if "*STEP, NAME=Step-1-PhaseInit" in line_s:
            in_step1 = True
            continue
        elif in_step1 and "*END STEP" in line_s:
            in_step1 = False
            
        if in_step1 and line_s.startswith("*BOUNDARY"):
            in_bcs = True
            continue
        elif in_step1 and in_bcs and line_s.startswith("*"):
            in_bcs = False
            
        if in_step1 and in_bcs and line_s:
            parts = [p.strip() for p in line_s.split(",")]
            if len(parts) >= 4 and parts[0].isdigit() and parts[1] == "3" and parts[2] == "3":
                nid = int(parts[0])
                val = float(parts[3])
                bcs_step1[nid] = val

print("=== STEP 1 PHASE INITIALIZATION AUDIT ===")
print("Total physical nodes:", total_nodes)
print("Total explicit DOF3 BCs in Step 1:", len(bcs_step1))
zero_bcs = sum(1 for v in bcs_step1.values() if v == 0.0)
nonzero_bcs = sum(1 for v in bcs_step1.values() if v > 0.0)
missing_bcs = total_nodes - len(bcs_step1)
min_val = min(bcs_step1.values()) if bcs_step1 else 0.0
max_val = max(bcs_step1.values()) if bcs_step1 else 0.0
print("Zero BC count:", zero_bcs)
print("Nonzero BC count:", nonzero_bcs)
print("Missing BC count:", missing_bcs)
print("Min nonzero value:", min_val)
print("Max value:", max_val)

# 2. Check D_AVG occurrences in Fortran subroutine
for_path = "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R3/f42_mixed_uel.for"
with open(for_path, "r") as f:
    for_lines = f.readlines()

print("\n=== D_AVG OCCURRENCES IN f42_mixed_uel.for ===")
for i, l in enumerate(for_lines):
    if "D_AVG" in l:
        print(f"Line {i+1:3d}: {l.strip()}")
