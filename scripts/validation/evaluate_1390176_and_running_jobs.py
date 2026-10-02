#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Terminal evaluation of 1390176.mmaster02 and status check on dual jobs 1390278 and 1390279.
"""

import os
import subprocess
import json

def get_cmd_output(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    return out.decode('utf-8', errors='ignore'), err.decode('utf-8', errors='ignore'), p.returncode

def main():
    print("================================================================================")
    print("PBS ACCOUNTING AUDIT: 1390176.mmaster02, 1390278.mmaster02, 1390279.mmaster02")
    print("================================================================================")
    
    # 1. Check 1390176
    print("\n--- 1. TERMINAL ACCOUNTING FOR 1390176.mmaster02 ---")
    out_x, _, _ = get_cmd_output("qstat -x 1390176.mmaster02")
    print("qstat -x:\n%s" % out_x.strip())
    
    out_xf, _, _ = get_cmd_output("qstat -xf 1390176.mmaster02")
    for l in out_xf.splitlines():
        for k in ["Job_Name", "job_state", "exec_host", "resources_used.cput", "resources_used.walltime", "resources_used.mem", "resources_used.vmem", "Exit_status", "Stageout_status", "Mail_Users", "queue", "server", "Output_Path", "Error_Path"]:
            if k in l:
                print("  %s" % l.strip())

    # 2. Check 1390278 and 1390279
    print("\n--- 2. CURRENT ACCOUNTING FOR 1390278 & 1390279 ---")
    out_d, _, _ = get_cmd_output("qstat -x 1390278.mmaster02 1390279.mmaster02")
    print(out_d.strip())
    
    for jid in ["1390278.mmaster02", "1390279.mmaster02"]:
        out_f, _, _ = get_cmd_output("qstat -xf %s" % jid)
        print("\n  %s details:" % jid)
        for l in out_f.splitlines():
            for k in ["Job_Name", "job_state", "exec_host", "resources_used.cput", "resources_used.walltime", "resources_used.mem", "Exit_status", "Stageout_status"]:
                if k in l:
                    print("    %s" % l.strip())

    # 3. Check Solver Progress from .sta
    base_dir = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch"
    for name in ["M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL", "M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL"]:
        print("\n--- SOLVER PROGRESS (.sta): %s ---" % name)
        sta_path = os.path.join(base_dir, name, "%s.sta" % name)
        if os.path.exists(sta_path):
            with open(sta_path, "r") as fp:
                lines = fp.readlines()
            print("  Total lines in .sta: %d" % len(lines))
            tail_lines = lines[-10:] if len(lines) >= 10 else lines
            for l in tail_lines:
                print("  " + l.rstrip())
        else:
            print("  .sta file not found.")

if __name__ == "__main__":
    main()
