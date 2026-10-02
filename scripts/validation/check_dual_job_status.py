#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inspect full scheduler state, sidecar status, and solver progress for dual jobs:
- 1390278.mmaster02 (M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL)
- 1390279.mmaster02 (M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL)
"""

import os
import subprocess
import json

def get_cmd_output(cmd):
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        return out.decode('utf-8', errors='ignore'), err.decode('utf-8', errors='ignore'), p.returncode
    except Exception as e:
        return "", str(e), 1

def main():
    print("================================================================================")
    print("DUAL-JOB STATUS AUDIT: 1390278.mmaster02 & 1390279.mmaster02")
    print("================================================================================")
    
    # 1. Short qstat
    out, _, _ = get_cmd_output("qstat -x 1390278.mmaster02 1390279.mmaster02")
    print("\n--- SCHEDULER OVERVIEW (qstat -x) ---")
    print(out.strip())
    
    # 2. Detailed qstat -xf
    for jid in ["1390278.mmaster02", "1390279.mmaster02"]:
        print("\n--- DETAILED SCHEDULER ACCOUNTING: %s ---" % jid)
        out_f, _, _ = get_cmd_output("qstat -xf %s" % jid)
        for line in out_f.splitlines():
            for key in ["Job_Name", "job_state", "exec_host", "resources_used.cput", "resources_used.walltime", "resources_used.mem", "resources_used.vmem", "Exit_status", "Stageout_status", "Mail_Users", "queue", "server"]:
                if key in line:
                    print("  %s" % line.strip())

    # 3. Sidecar Daemon Status
    print("\n--- SIDECAR DAEMON STATUS ---")
    out_pid, _, _ = get_cmd_output("cat /home/pr21vyci/projects/adaptive-remeshing/scripts/hpc/notifications/hpc_job_watcher.pid")
    pid = out_pid.strip()
    out_ps, _, _ = get_cmd_output("ps -p %s -o pid,vsz,rss,etime,args" % pid if pid else "echo No PID")
    print("  Watcher PID: %s" % pid)
    print("  Process info:\n%s" % out_ps.strip())
    
    out_log, _, _ = get_cmd_output("tail -n 25 /home/pr21vyci/projects/adaptive-remeshing/scripts/hpc/notifications/hpc_job_watcher.log")
    print("\n--- RECENT SIDECAR LOG ENTRIES ---")
    print(out_log.strip())

    # 4. Solver Progress from .sta
    base_dir = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch"
    for name in ["M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL", "M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL"]:
        print("\n--- SOLVER PROGRESS (.sta): %s ---" % name)
        sta_path = os.path.join(base_dir, name, "%s.sta" % name)
        if os.path.exists(sta_path):
            with open(sta_path, "r") as fp:
                lines = fp.readlines()
            print("  Total lines in .sta: %d" % len(lines))
            tail_lines = lines[-12:] if len(lines) >= 12 else lines
            for l in tail_lines:
                print("  " + l.rstrip())
        else:
            print("  .sta file not yet created.")

if __name__ == "__main__":
    main()
