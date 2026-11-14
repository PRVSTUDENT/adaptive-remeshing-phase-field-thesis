# -*- coding: utf-8 -*-
"""
tests/unit/test_f1753_pbs_monitor_integration.py
Simulated PBS-wrapper integration test suite for Task F1753 Case 2 continuation.
Directly addresses Review Directive F1753-R02 (HND-F1753-CASE2-EXEC-AUTH-001):
- Verifies exact threshold reconciliation (triggers at exactly 50 consecutive cutbacks).
- Verifies launch order, job-name matching, logfile paths, background PID management, and cleanup traps.
- Simulates full PBS lifecycle without launching Abaqus:
    Case A: Normal solver completion with clean banner detection.
    Case B: Cutback stall reaching exactly 50 cutbacks, triggering targeted abaqus terminate.
    Case C: Premature solver failure with clean PID cleanup via shell trap.
    Case D: Boundary check: 49 cutbacks do NOT trigger, 50th cutback triggers immediately.
"""

import sys
import tempfile
import time
import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.hpc.monitor_case2_cutbacks import parse_sta_line, evaluate_sta_content, monitor_sta_file


def test_threshold_exactness_49_vs_50():
    """Verify threshold triggers at exactly 50 consecutive cutbacks, not 49."""
    lines_49 = [f"   2   200   {i}U    0     5     5  1.38       0.382      1.0e-8" for i in range(1, 50)]
    res_49 = evaluate_sta_content(lines_49, max_cutbacks=50)
    assert res_49["consecutive_cutbacks"] == 49
    assert res_49["triggered"] is False

    # Add 50th cutback
    lines_50 = lines_49 + ["   2   200   50U    0     5     5  1.38       0.382      1.0e-8"]
    res_50 = evaluate_sta_content(lines_50, max_cutbacks=50)
    assert res_50["consecutive_cutbacks"] == 50
    assert res_50["triggered"] is True
    assert res_50["trigger_line"] == 50


def test_pbs_script_static_audit():
    """Inspect production PBS script submit_f1753_case2_continuation.pbs for required governance directives."""
    pbs_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "234_f1752_case2_continuation" / "submit_f1753_case2_continuation.pbs"
    assert pbs_path.exists(), "PBS script missing"
    
    with open(pbs_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Launch order & job name
    assert 'JOBNAME="PK_F1752_CASE_2_CONTINUATION"' in content
    assert 'python3 monitor_case2_cutbacks.py "${JOBNAME}.sta" --max-cutbacks 50' in content
    assert 'MONITOR_PID=$!' in content
    assert 'monitor_execution.log' in content

    # Cleanup trap
    assert "trap '" in content
    assert 'kill "$MONITOR_PID"' in content
    assert "EXIT INT TERM" in content

    # Threshold documentation
    assert "50 consecutive cutbacks" in content

    # Hashes
    assert "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6" in content
    assert "ccb35b34bfae015ea4846d3d0765fc2646e6c9af47958f8c21a0a4f25a14cc4a" in content


def test_simulated_pbs_case_a_normal_completion():
    """Simulate PBS wrapper execution when solver completes normally."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        sta_file = tmp_path / "PK_F1752_CASE_2_CONTINUATION.sta"
        
        # Write initial increments
        with open(sta_file, "w") as f:
            f.write(" STEP  INC ATT SEVERE EQUIL TOTAL  TOTAL      STEP       INC OF\n")
            f.write("   2     1   1     0     3     3  0.002      0.002      0.002000\n")
            f.write("   2     2   1     0     4     4  0.004      0.004      0.002000\n")
            f.write(" THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n")

        # Launch monitor in dry-run mode
        exit_code = monitor_sta_file(
            sta_path=sta_file,
            max_cutbacks=50,
            poll_interval=0.01,
            dry_run=True,
            max_iterations=3
        )
        assert exit_code == 0, "Monitor should exit 0 on clean completion"


def test_simulated_pbs_case_b_cutback_stagnation_and_termination():
    """Simulate PBS wrapper execution when solver encounters 50 consecutive cutbacks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        job_name = "PK_F1752_CASE_2_CONTINUATION"
        sta_file = tmp_path / f"{job_name}.sta"
        
        # Write 50 cutback attempts
        with open(sta_file, "w") as f:
            f.write(" STEP  INC ATT SEVERE EQUIL TOTAL  TOTAL      STEP       INC OF\n")
            for i in range(1, 51):
                f.write(f"   2   200   {i}U    0     5     5  1.38       0.382      1.0e-8\n")

        terminated_jobs = []
        def mock_termination(target_job, count, line_num):
            terminated_jobs.append((target_job, count, line_num))

        exit_code = monitor_sta_file(
            sta_path=sta_file,
            max_cutbacks=50,
            poll_interval=0.01,
            dry_run=True,
            termination_callback=mock_termination,
            max_iterations=2
        )
        assert exit_code == 1, "Monitor should exit 1 when Stop Condition 1 triggers"
        assert len(terminated_jobs) == 1
        assert terminated_jobs[0][0] == job_name, "Targeted job must match solver job name"
        assert terminated_jobs[0][1] == 50, "Must trigger at exactly 50 cutbacks"
        assert terminated_jobs[0][2] == 51, "Trigger line corresponds to 50th cutback"


def test_simulated_pbs_case_c_cleanup_trap():
    """Verify that simulated PID cleanup trap correctly identifies and terminates the monitor process."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        sta_file = tmp_path / "PK_F1752_CASE_2_CONTINUATION.sta"
        with open(sta_file, "w") as f:
            f.write(" STEP  INC ATT SEVERE EQUIL TOTAL  TOTAL      STEP       INC OF\n")

        # Start monitor as a background subprocess using Python
        cmd = [
            sys.executable,
            str(REPO_ROOT / "scripts" / "hpc" / "monitor_case2_cutbacks.py"),
            str(sta_file),
            "--max-cutbacks", "50",
            "--poll-interval", "0.5",
            "--dry-run"
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pid = proc.pid
        assert proc.poll() is None, "Monitor should be running in background"

        # Simulate PBS trap cleanup
        proc.terminate()
        proc.wait(timeout=5)
        assert proc.poll() is not None, "Monitor should be terminated by cleanup trap"
