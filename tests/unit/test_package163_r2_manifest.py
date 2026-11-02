"""Unit test verifying Package 163-R2 execution manifest validation."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.hpc.mode1_execution_gate import validate_manifest

def test_package163_r2_manifest_validation():
    manifest_path = REPO_ROOT / "models/pandey_kumar_mode1/163_c5_package163_r2_c2_1_continuation/EXECUTION_MANIFEST.json"
    batch, key, files = validate_manifest(manifest_path, REPO_ROOT)
    assert batch["batch_name"] == "MODE1_PACKAGE163_R2_M1_C5_P163_R2_C2_1"
    assert len(batch["jobs"]) == 1
    assert batch["jobs"][0]["id"] == "M1_C5_P163_R2_C2_1"
    assert len(key) == 64
    assert len(files) == 15  # 14 package files + PACKAGE_MANIFEST.json
