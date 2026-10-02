import os
import subprocess

def main():
    key = os.path.expanduser("~/.ssh/tu_freiberg_codex")
    remote_cmd = "grep -n '***ERROR' /home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R1/M2STATE_FRACFIX_RESTART2R1.dat"
    cmd = ["ssh", "-i", key, "-o", "BatchMode=yes", "pr21vyci@mlogin01.hrz.tu-freiberg.de", remote_cmd]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)

if __name__ == "__main__":
    main()
