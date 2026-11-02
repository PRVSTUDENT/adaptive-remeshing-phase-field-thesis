"""Unit test executing stage_package163_r2 main and verifying remote staging."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.hpc.stage_package163_r2 import main, run_remote_ssh

def test_stage_package163_r2():
    main()
    out = run_remote_ssh("ls -la /scratch9/pr21vyci/runs/mode1_c5_package163_r2_c2_1_continuation")
    assert "submit_M1_C5_P163_R2_C2_1.pbs" in out
    assert "EXECUTION_MANIFEST.json" in out
    assert "P163_R2_MECHANICAL_DC.dat" in out
