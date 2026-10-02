import os
import sys

def audit_target_r2r10():
    r2r10_dir = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R10"
    
    # 1. Inspect R2R10 Step 1 DAT file for reactions
    dat_step1 = os.path.join(r2r10_dir, "M2STATE_FRACFIX_RESTART2R10_STEP1.dat")
    with open(dat_step1, 'r') as f:
        text = f.read()
    
    print("=== Inspecting R2R10 Step 1 DAT ===")
    lines = text.splitlines()
    for i, l in enumerate(lines):
        if "99999" in l:
            print("RP node line:", l)
        if "TOTAL" in l:
            print("TOTAL line:", l)
            
    # Parse node 99999
    for l in lines:
        parts = l.split()
        if len(parts) >= 3 and parts[0] == "99999":
            try:
                rf1 = float(parts[1])
                rf2 = float(parts[2])
                print("Parsed Node 99999 RF1=%.8f, RF2=%.8f" % (rf1, rf2))
            except:
                pass
                
    # 2. Inspect R2R10 input deck for initial conditions
    inp_file = os.path.join(r2r10_dir, "M2STATE_FRACFIX_RESTART2R10.inp")
    with open(inp_file, 'r') as f:
        inp_text = f.read()
        
    print("\n=== Inspecting R2R10 INP Initial Conditions ===")
    sdv_lines = []
    in_ic = False
    for l in inp_text.splitlines():
        if l.startswith("*INITIAL CONDITIONS, TYPE=SOLUTION"):
            in_ic = True
            continue
        if in_ic:
            if l.startswith("*"):
                in_ic = False
            else:
                sdv_lines.append(l.strip())
                
    print("Found %d initial condition lines" % len(sdv_lines))
    # Parse SDV values
    h_values = []
    sdv14_values = []
    sdv15_values = []
    for l in sdv_lines:
        parts = [float(p) for p in l.split(",") if p.strip()]
        if len(parts) >= 17:
            # parts[0] is elem_id, parts[1..18] are SDVs
            # SDV14 is index 14, SDV15 is index 15, SDV16 is index 16
            sdv14_values.append(parts[14])
            sdv15_values.append(parts[15])
            h_values.append(parts[16])
            
    if h_values:
        print("Target H (SDV16) stats across %d elements:" % len(h_values))
        print("  min = %.8f" % min(h_values))
        print("  max = %.8f" % max(h_values))
        print("  mean = %.8f" % (sum(h_values) / float(len(h_values))))
        
    if sdv14_values:
        print("Target SDV14 (damage at IP) stats:")
        print("  min = %.8f, max = %.8f, mean = %.8f" % (min(sdv14_values), max(sdv14_values), sum(sdv14_values)/float(len(sdv14_values))))
    if sdv15_values:
        print("Target SDV15 (damage at IP) stats:")
        print("  min = %.8f, max = %.8f, mean = %.8f" % (min(sdv15_values), max(sdv15_values), sum(sdv15_values)/float(len(sdv15_values))))

    # Check Step 1 displacement prescription and Step 2 loading
    print("\n=== Step 1 and Step 2 BCs ===")
    in_step = 0
    for l in inp_text.splitlines():
        if l.startswith("*STEP"):
            in_step += 1
            print("--- STEP %d ---" % in_step)
        if in_step > 0:
            if "*BOUNDARY" in l or "99999" in l or "N_TOP" in l:
                print("  ", l)
            if l.startswith("*END STEP") and in_step >= 2:
                break

if __name__ == "__main__":
    audit_target_r2r10()
