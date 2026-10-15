"""Unit tests for Task F1478: Continuous HPC Research Execution Policy and Bridge Rules.

Validates that:
1. The authoritative bridge rules (.agents/scripts/bridge_rules.txt) enforce the
   10-rule Continuous HPC Research Execution Policy, report writing concurrency,
   submission decision deadlines, and safe bridge edits.
2. The upcoming supervisor meeting is updated to Thursday, 22 October 2026, 10:00 CEST.
3. The project alignment guard (.agents/scripts/project_alignment_guard.txt) includes
   the continuous research execution policy, Gate 6B closure recommendation, and
   has no stray syntax.
4. Invoke-ChatGPTBridge.ps1 successfully assembles prompts in -DryRun mode incorporating
   the continuous research execution policy and updated meeting dates.
"""

from pathlib import Path
import subprocess
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BRIDGE_RULES_PATH = REPO_ROOT / ".agents" / "scripts" / "bridge_rules.txt"
ALIGNMENT_GUARD_PATH = REPO_ROOT / ".agents" / "scripts" / "project_alignment_guard.txt"
BRIDGE_SCRIPT_PATH = REPO_ROOT / ".agents" / "scripts" / "Invoke-ChatGPTBridge.ps1"


def test_bridge_rules_continuous_hpc_policy_rules():
    """Verify bridge_rules.txt contains all 10 rules of the Continuous HPC Research Execution Policy."""
    assert BRIDGE_RULES_PATH.exists(), f"Missing bridge_rules.txt at {BRIDGE_RULES_PATH}"
    content = BRIDGE_RULES_PATH.read_text(encoding="utf-8")

    assert "CONTINUOUS HPC RESEARCH EXECUTION POLICY (MANDATORY)" in content

    # Rule 1
    assert "1. Numerical research takes operational priority over documentation" in content
    # Rule 2
    assert "2. Submit validated experiments without unnecessary delays" in content
    # Rule 3
    assert "3. Work concurrently while PBS jobs execute" in content
    # Rule 4
    assert "4. Maintain a scientific experiment pipeline" in content
    # Rule 5
    assert "5. Documentation must not monopolize execution" in content
    # Rule 6
    assert "6. Empty queue requires an active research decision" in content
    # Rule 7
    assert "7. No artificial HPC usage (scientific usefulness is the sole criterion)" in content
    # Rule 8
    assert "8. Respect research gates" in content
    # Rule 9
    assert "9. Reporting follows execution" in content
    assert "(1) HPC STATUS" in content
    assert "(2) NEW EXPERIMENT" in content
    assert "(3) SCIENTIFIC PROGRESS" in content
    assert "(4) DOCUMENTATION" in content
    assert "(5) NEXT ACTION" in content
    # Rule 10
    assert "10. Do not choose scheduler polling interval" in content

    # Deadlines and safe edits
    assert "Submission Decision Deadline" in content
    assert "Make Bridge Edits Safer" in content


def test_supervisor_meeting_date_updated_to_22_october():
    """Verify supervisor meeting date is updated to 22 October 2026 across persistent files."""
    for path in [BRIDGE_RULES_PATH, ALIGNMENT_GUARD_PATH]:
        assert path.exists(), f"File does not exist: {path}"
        content = path.read_text(encoding="utf-8")
        assert "22 October 2026" in content, f"Expected '22 October 2026' in {path.name}"
        assert "Meeting of Thursday, 08 October 2026, 10:00 CEST has concluded" in content or "08 October 2026, 10:00 CEST has concluded" in content or "POST-08 OCTOBER" in content or "POST-08-OCTOBER" in content


def test_project_alignment_guard_consistency():
    """Verify project_alignment_guard.txt syntax, policy inclusion, and gate status."""
    assert ALIGNMENT_GUARD_PATH.exists()
    content = ALIGNMENT_GUARD_PATH.read_text(encoding="utf-8")

    # Guard should not have stray syntax
    assert not content.strip().endswith('"@'), "Alignment guard has stray \"@ at EOF"

    # Must contain Continuous HPC policy
    assert "CONTINUOUS HPC RESEARCH EXECUTION POLICY (MANDATORY)" in content
    assert "Numerical research takes operational priority over documentation" in content
    assert "Empty queue requires an active research decision" in content

    # Gate status checks
    assert "Gate 6B" in content
    assert "Gate 6C" in content
    assert "ON_HOLD" in content or "on hold" in content


def test_invoke_chatgpt_bridge_dry_run():
    """Verify Invoke-ChatGPTBridge.ps1 -DryRun successfully assembles prompt with policy and 22 October date."""
    assert BRIDGE_SCRIPT_PATH.exists()

    cmd = [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        f". '{BRIDGE_SCRIPT_PATH}'; Invoke-ChatGPTBridge -PromptText 'Test Bridge Prompt Assembled By Pytest' -DryRun"
    ]

    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=30,
        stdin=subprocess.DEVNULL
    )
    assert res.returncode == 0, f"Bridge dry-run failed with code {res.returncode}:\nStdout: {res.stdout}\nStderr: {res.stderr}"

    assembled = res.stdout
    assert "CONTINUOUS HPC RESEARCH EXECUTION POLICY (MANDATORY)" in assembled
    assert "22 October 2026" in assembled
    assert "Numerical research takes operational priority over documentation" in assembled
