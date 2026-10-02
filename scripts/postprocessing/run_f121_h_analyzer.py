#!/usr/bin/env python3
"""
Detailed Analysis of PhaseInit History H advancement and Free-Phase Residual
"""
import sys, os, json, math, subprocess

SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

REMOTE_SCRIPT = """#!/usr/bin/env python3
import sys, os, json, math

# Let's inspect R13 terminal H vs PhaseInit terminal H
# We can check DAT tables or ODB fields if DAT has SVARS / H

def analyze_h_change():
    # In R13 terminal DAT vs PhaseInit DAT
    # Let's inspect DAT output files
    r13_dat = "projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R13/M2STATE_FRACFIX_RESTART2R13.dat"
    pi_dat  = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/PK10R1_IDENTITY_RESTART_U050/PK10R1_IDENTITY_RESTART_U050.dat"

    print("Checking DAT sizes:", os.path.getsize(r13_dat), os.path.getsize(pi_dat))

if __name__ == "__main__":
    analyze_h_change()
"""

def main():
    remote_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/f121_h_analyzer.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_path}\n{REMOTE_SCRIPT}\nEOF"]
    subprocess.run(upload_cmd, check=True)
    res = subprocess.run(["ssh", "-i", SSH_KEY, SSH_HOST, f"python3 {remote_path}"], capture_output=True, text=True)
    print(res.stdout)

if __name__ == "__main__":
    main()
