#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inspect PBS Accounting and Spool Logs for Stageout_status = 1
"""
import os
import subprocess

def run_cmd(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    print("STDOUT:\n%s" % out.decode('utf-8', errors='ignore'))
    if err:
        print("STDERR:\n%s" % err.decode('utf-8', errors='ignore'))

def main():
    ssh_cfg = os.path.join(os.environ['USERPROFILE'], '.ssh', 'codex_config')
    
    remote_script = (
        "echo '=== SCHEDULER ACCOUNTING LOGS ===' && "
        "qstat -xf 1391281.mmaster02 | grep -E 'Stage|Exit|comment|Error_Path|Output_Path' && "
        "qstat -xf 1391282.mmaster02 | grep -E 'Stage|Exit|comment|Error_Path|Output_Path'"
    )
    
    cmd_ssh = "ssh -F \"%s\" tu_freiberg \"%s\"" % (ssh_cfg, remote_script)
    run_cmd(cmd_ssh)

if __name__ == "__main__":
    main()
