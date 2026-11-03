"""
test_package171_r6_pbs_syntax.py
================================
Regression test verifying that submit_M1_C6_P171_R6_C3_0.pbs contains strictly
normalized Linux LF line endings (\n), contains no Windows CRLF (\r\n) line
terminators that break Bash line-continuation backslashes, passes bash -n syntax
check, and satisfies all required PBS batch directives.
"""

import subprocess
import shutil
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
R6_DIR = WORKSPACE / "models/pandey_kumar_mode1/171_c6_package171_r6_c3_0_reequilibration"
PBS_SCRIPT = R6_DIR / "submit_M1_C6_P171_R6_C3_0.pbs"


def test_pbs_script_exists():
    assert PBS_SCRIPT.is_file(), f"Missing PBS script: {PBS_SCRIPT}"


def test_pbs_script_strict_lf_line_endings():
    """Verify that the PBS script contains no \r\n (CRLF) or bare \r."""
    raw = PBS_SCRIPT.read_bytes()
    assert b"\r\n" not in raw, "PBS script contains Windows CRLF (\\r\\n) line endings!"
    assert b"\r" not in raw, "PBS script contains bare carriage return (\\r) characters!"


def test_pbs_script_required_directives():
    """Verify all mandatory PBS directives and environment modules are present."""
    text = PBS_SCRIPT.read_text(encoding="utf-8")
    required = [
        "#!/bin/bash",
        "#PBS -N M1_C6_P171_R6_C3_0",
        "#PBS -l select=1:ncpus=1:mem=16gb",
        "#PBS -l walltime=08:00:00",
        "#PBS -q entry_imfdfkmq",
        "#PBS -j oe",
        "#PBS -r n",
        "#PBS -m abe",
        "#PBS -M pr21vyci@mailserver.tu-freiberg.de",
        "set -euo pipefail",
        'RUN_DIR="/scratch9/pr21vyci/runs/mode1_c6_package171_r6_c3_0_reequilibration"',
        'cd "${RUN_DIR}"',
        'source "${RUN_DIR}/job_notifications.sh"',
        "notification_load_config",
        "notification_install_terminal_trap",
        "notify_start",
        "module load gcc/11.4.0 intel/2024.2.0 abaqus/2023",
        "command -v ifort",
        "driver_package171_r6_c6_coupled_pdas.py",
        "--memory-gb 16",
        "--timeout 25200",
        "--max-outer 100",
        "--damping-omega-d 0.5",
    ]
    for item in required:
        assert item in text, f"Missing required directive/content: {item}"


def test_pbs_script_bash_syntax():
    """Test bash -n parsing on local bash if available."""
    bash = shutil.which("bash")
    if bash:
        res = subprocess.run([bash, "-n", str(PBS_SCRIPT)], capture_output=True, text=True, stdin=subprocess.DEVNULL)
        assert res.returncode == 0, f"bash -n failed on {PBS_SCRIPT}: {res.stderr}"
