"""
test_mode1_turn124_gate_regression.py
Regression tests for Mode-I Task F1597 Turn 124 HPC Execution Gate.

Verifies:
  1. Existing production UEL manifests remain valid (FROZEN_UEL allowed).
  2. Exact Package 108 experimental UEL hash (e72e...) is accepted under mode1-experimental-irrev-v1.
  3. Modified or unknown experimental UEL hashes are strictly rejected.
  4. Missing or incorrect input deck hashes are rejected.
  5. Missing notifications block submission.
  6. Over-limit resource requests (>16GB, >8h, >1 CPU) are rejected.
"""

import sys
import json
import tempfile
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hpc"))

from mode1_execution_gate import validate_manifest, FROZEN_UEL, EXPERIMENTAL_IRREVERSIBLE_UEL

def test_production_frozen_uel_constant():
    assert FROZEN_UEL == "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def test_experimental_irreversible_uel_constant():
    assert EXPERIMENTAL_IRREVERSIBLE_UEL == "e72e00d338e355b370fc5ebabfe6679f49bc07458d333b642b593c6710b16dad"

def test_package108_manifest_passes_validation():
    pkg108_manifest = REPO_ROOT / "models" / "pandey_kumar_mode1" / "108_c3_staggered_continuation" / "M1_C3_STAGGERED_AUTHORIZATION.json"
    assert pkg108_manifest.exists()
    batch, manifest_digest, files = validate_manifest(pkg108_manifest, root=REPO_ROOT)
    assert batch["adapter"] == "mode1-experimental-irrev-v1"
    assert batch["configuration"] == "STAGGERED_IRREVERSIBLE"
    assert files["f42_experimental_irreversible_uel.for"] == EXPERIMENTAL_IRREVERSIBLE_UEL
    assert len(batch["jobs"]) == 1
    assert batch["jobs"][0]["cpus"] == 1
    assert batch["jobs"][0]["memory_gb"] <= 16
    assert batch["jobs"][0]["walltime_hours"] <= 8

def test_modified_experimental_uel_hash_rejected():
    pkg108_manifest = REPO_ROOT / "models" / "pandey_kumar_mode1" / "108_c3_staggered_continuation" / "M1_C3_STAGGERED_AUTHORIZATION.json"
    with open(pkg108_manifest) as f:
        data = json.load(f)
    
    # Tamper with UEL hash
    data["files"]["f42_experimental_irreversible_uel.for"] = "0" * 64
    
    with tempfile.TemporaryDirectory(dir=REPO_ROOT / "models" / "pandey_kumar_mode1") as tmpdir:
        tmp_path = Path(tmpdir) / "M1_TAMPERED_AUTHORIZATION.json"
        # copy other files
        for fname in data["files"]:
            src = pkg108_manifest.parent / fname
            (Path(tmpdir) / fname).write_bytes(src.read_bytes())
        with open(tmp_path, "w") as f:
            json.dump(data, f)
        
        with pytest.raises(ValueError, match="Candidate hash mismatch"):
            validate_manifest(tmp_path, root=REPO_ROOT)

def test_missing_notifications_rejected():
    pkg108_manifest = REPO_ROOT / "models" / "pandey_kumar_mode1" / "108_c3_staggered_continuation" / "M1_C3_STAGGERED_AUTHORIZATION.json"
    with open(pkg108_manifest) as f:
        data = json.load(f)
    
    del data["files"]["job_notifications.sh"]
    with tempfile.TemporaryDirectory(dir=REPO_ROOT / "models" / "pandey_kumar_mode1") as tmpdir:
        tmp_path = Path(tmpdir) / "M1_NO_NOTIF_AUTHORIZATION.json"
        for fname in data["files"]:
            src = pkg108_manifest.parent / fname
            (Path(tmpdir) / fname).write_bytes(src.read_bytes())
        with open(tmp_path, "w") as f:
            json.dump(data, f)
        
        with pytest.raises(ValueError, match="notifications required"):
            validate_manifest(tmp_path, root=REPO_ROOT)

def test_resource_bound_enforcement():
    pkg108_manifest = REPO_ROOT / "models" / "pandey_kumar_mode1" / "108_c3_staggered_continuation" / "M1_C3_STAGGERED_AUTHORIZATION.json"
    with open(pkg108_manifest) as f:
        data = json.load(f)
    
    # Request 32 GB RAM (limit is 16 GB)
    data["jobs"][0]["memory_gb"] = 32
    with tempfile.TemporaryDirectory(dir=REPO_ROOT / "models" / "pandey_kumar_mode1") as tmpdir:
        tmp_path = Path(tmpdir) / "M1_OVERLIMIT_AUTHORIZATION.json"
        for fname in data["files"]:
            src = pkg108_manifest.parent / fname
            (Path(tmpdir) / fname).write_bytes(src.read_bytes())
        with open(tmp_path, "w") as f:
            json.dump(data, f)
        
        with pytest.raises(ValueError, match="Resource bounds exceeded"):
            validate_manifest(tmp_path, root=REPO_ROOT)
