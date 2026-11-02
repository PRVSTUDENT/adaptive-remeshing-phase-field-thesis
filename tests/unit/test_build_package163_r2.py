"""Unit test verifying Package 163-R2 build and manifest integrity."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.build_package163_r2_c5_continuation import build

def test_build_package163_r2():
    build()
    r2_pkg = Path("models/pandey_kumar_mode1/163_c5_package163_r2_c2_1_continuation")
    assert r2_pkg.is_dir()
    assert (r2_pkg / "EXECUTION_MANIFEST.json").is_file()
    assert (r2_pkg / "PACKAGE_MANIFEST.json").is_file()
    assert (r2_pkg / "submit_M1_C5_P163_R2_C2_1.pbs").is_file()
    assert (r2_pkg / "f42_mixed_uel.for").is_file()
