"""
Unit regression test suite for Bridge External Authentication Blocker Guard.
Verifies idempotent suppression of ChatGPT bridge calls during active institutional SSO blockers.
"""
import subprocess
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def run_ps1_test():
    test_script = os.path.join(REPO_ROOT, "tests", "unit", "test_bridge_external_blocker_guard.ps1")
    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy", "Bypass",
        "-File", test_script
    ]
    proc = subprocess.run(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return proc

def test_bridge_external_blocker_guard_ps1():
    proc = run_ps1_test()
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    assert proc.returncode == 0, f"PowerShell test failed with exit code {proc.returncode}"

if __name__ == "__main__":
    proc = run_ps1_test()
    print(proc.stdout)
    if proc.stderr:
        print(proc.stderr, file=sys.stderr)
    sys.exit(proc.returncode)
