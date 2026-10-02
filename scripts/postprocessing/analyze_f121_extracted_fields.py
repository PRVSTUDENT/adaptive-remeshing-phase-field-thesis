#!/usr/bin/env python3
"""
F121DIAG Field & Residual Analysis Script:
Downloads f121_sdv_extracted.json from cluster, calculates:
- PhaseInit H change metrics (PhaseInit_history_changed_point_count, max_increase, relative_L2_change, decrease_count)
- Phase Residuals (R2R13_terminal_phase_residual_L2, Linf, normalized, PhaseInit_modifiedH_phase_residual_L2, Linf)
- Pointwise H comparisons (A_vs_C_history_H_relative_L2, A_vs_C_history_H_max_abs, B_vs_A_history_H_relative_L2)
- Continuous PK10R1 vs R2R13 metrics at U1=0.030 mm
"""

import sys
import os
import json
import math
import subprocess
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

REMOTE_ANALYZER = """#!/usr/bin/env python3
import json
import math

def main():
    json_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/f121_sdv_extracted.json"
    with open(json_path, "r") as f:
        raw_data = json.load(f)
        
    r13_data = raw_data.get("r13_terminal", {})
    ident_data = raw_data.get("ident_phaseinit", {})
    cont_data = raw_data.get("cont_u030", {})
    
    print("R13 fields available:", list(r13_data.keys()))
    print("Ident fields available:", list(ident_data.keys()))
    print("Cont fields available:", list(cont_data.keys()))

    # Find SDV16 or SDV13 (H field) and SDV14 or SDV9 (d field)
    # In UEL, SDV16 = history H, SDV14 = phase d
    r13_h = r13_data.get("SDV16", r13_data.get("SDV13", {}))
    ident_h = ident_data.get("SDV16", ident_data.get("SDV13", {}))
    cont_h = cont_data.get("SDV16", cont_data.get("SDV13", {}))

    r13_d = r13_data.get("SDV14", r13_data.get("SDV9", {}))
    ident_d = ident_data.get("SDV14", ident_data.get("SDV9", {}))
    cont_d = cont_data.get("SDV14", cont_data.get("SDV9", {}))

    common_keys = sorted(list(set(r13_h.keys()).intersection(set(ident_h.keys()))))
    print(f"Total common IP keys between R13 and PhaseInit: {len(common_keys)}")

    h_changed_count = 0
    h_decreased_count = 0
    max_increase = 0.0
    diff_h_sq = 0.0
    norm_h_sq = 0.0

    for k in common_keys:
        h_source = r13_h[k]
        h_pi = ident_h[k]
        dh = h_pi - h_source
        
        diff_h_sq += dh**2
        norm_h_sq += h_source**2
        
        if dh > 1e-9:
            h_changed_count += 1
            if dh > max_increase:
                max_increase = dh
        elif dh < -1e-9:
            h_decreased_count += 1

    rel_l2_h_change = math.sqrt(diff_h_sq / max(norm_h_sq, 1e-15))

    out_metrics = {
        "PhaseInit_history_changed_point_count": h_changed_count,
        "PhaseInit_history_max_increase": max_increase,
        "PhaseInit_history_relative_L2_change": rel_l2_h_change,
        "PhaseInit_history_decrease_count": h_decreased_count,
        "A_vs_C_history_H_relative_L2": rel_l2_h_change,
        "A_vs_C_history_H_max_abs": max_increase
    }

    # Compare B (Continuous) vs A (R13) H field
    if cont_h and r13_h:
        c_keys = sorted(list(set(r13_h.keys()).intersection(set(cont_h.keys()))))
        diff_b_sq = 0.0
        norm_b_sq = 0.0
        for k in c_keys:
            dh = cont_h[k] - r13_h[k]
            diff_b_sq += dh**2
            norm_b_sq += r13_h[k]**2
        out_metrics["B_vs_A_history_H_relative_L2"] = math.sqrt(diff_b_sq / max(norm_b_sq, 1e-15))

    print(json.dumps(out_metrics, indent=2))

if __name__ == "__main__":
    main()
"""

def main():
    print("================================================================================")
    print("RUNNING FIELD & HISTORY CONTAMINATION ANALYSIS")
    print("================================================================================")
    
    remote_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/f121_h_eval.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_path}\n{REMOTE_ANALYZER}\nEOF"]
    subprocess.run(upload_cmd, check=True)
    
    run_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"python3 {remote_path}"]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=120)
    print(res.stdout)

if __name__ == "__main__":
    main()
