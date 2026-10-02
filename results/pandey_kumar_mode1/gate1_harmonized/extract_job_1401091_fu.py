"""
Standalone extraction script for Job 1401091 (PK_M1_HARM_S).
Parses printed node output table for N_RP (node 999999) from PK_MODE1_STANDARD_PFM.dat.
Outputs: job_1401091_fu.csv (increment, step, u_mm, F_kN).
"""

import os
import re
import pandas as pd

def extract_fu(dat_path, out_csv_path):
    records = []
    current_step = 1
    current_inc = 0
    total_inc = 0
    
    step_re = re.compile(r'^\s*STEP\s+(\d+)\s+INCREMENT\s+(\d+)')
    inc_re = re.compile(r'^\s*INCREMENT\s+(\d+)\s+SUMMARY')
    node_table_header = 'THE FOLLOWING TABLE IS PRINTED FOR NODES BELONGING TO NODE SET N_RP'
    
    in_table = False
    with open(dat_path, 'r') as f:
        for line in f:
            m_step = step_re.search(line)
            if m_step:
                current_step = int(m_step.group(1))
                current_inc = int(m_step.group(2))
                continue
                
            m_inc = inc_re.search(line)
            if m_inc:
                current_inc = int(m_inc.group(1))
                continue
                
            if node_table_header in line:
                in_table = True
                continue
                
            if in_table:
                stripped = line.strip()
                if stripped.startswith('999999'):
                    parts = stripped.split()
                    if len(parts) == 3:
                        u2 = float(parts[1])
                        rf2 = float(parts[2])
                    elif len(parts) >= 4:
                        u2 = float(parts[-2])
                        rf2 = float(parts[-1])
                    else:
                        continue
                    
                    total_inc += 1
                    records.append({
                        'increment': current_inc,
                        'step': current_step,
                        'u_mm': u2,
                        'F_kN': rf2
                    })
                    in_table = False
                elif 'MAXIMUM' in stripped or 'SUMMARY' in stripped:
                    in_table = False

    df = pd.DataFrame(records)
    df.to_csv(out_csv_path, index=False)
    print(f"Extracted {len(df)} points to {out_csv_path}")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Check candidate model directory for dat file
    project_root = os.path.abspath(os.path.join(base_dir, "..", ".."))
    dat_path = os.path.join(project_root, "models", "pandey_kumar_mode1", "01_standard_pfm_bvp_harmonized", "PK_MODE1_STANDARD_PFM.dat")
    out_csv = os.path.join(base_dir, "job_1401091_fu.csv")
    if not os.path.exists(dat_path):
        # fallback to current directory
        dat_path = os.path.join(base_dir, "PK_MODE1_STANDARD_PFM.dat")
    extract_fu(dat_path, out_csv)
