import pytest
import re
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
R6_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "108_r6_c3_multi_increment_continuation"
INP_PATH = R6_DIR / "M1_C3_STAGGERED_R6_CONTINUATION.inp"
MANIFEST_PATH = R6_DIR / "M1_C3_STAGGERED_R6_AUTHORIZATION.json"

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def test_production_uel_bitwise_frozen():
    prod_uel = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
    expected = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
    actual = compute_sha256(prod_uel)
    assert actual.lower() == expected, f"Production UEL modified: {actual}"

def test_experimental_uel_hash():
    uel_path = R6_DIR / "f42_experimental_irreversible_uel.for"
    expected = "e72e00d338e355b370fc5ebabfe6679f49bc07458d333b642b593c6710b16dad"
    actual = compute_sha256(uel_path)
    assert actual.lower() == expected, f"Experimental UEL modified: {actual}"

def test_r6_manifest_integrity():
    assert MANIFEST_PATH.exists()
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["batch_name"] == "MODE1_C3_STAGGERED_CONTINUATION_R6"
    assert manifest["adapter"] == "mode1-experimental-irrev-v1"
    assert manifest["jobs"][0]["id"] == "M1_C3_STAGGERED_R6"
    for name, expected_hash in manifest["files"].items():
        actual_hash = compute_sha256(R6_DIR / name)
        assert actual_hash == expected_hash, f"File hash mismatch for {name}"

def test_r6_16_steps_kinematics():
    assert INP_PATH.exists()
    lines = INP_PATH.read_text(encoding="utf-8").splitlines()

    # Parse steps
    steps = []
    current_step = None
    current_lines = []

    for line in lines:
        if line.strip().lower().startswith("*step"):
            if current_step:
                steps.append((current_step, current_lines))
            current_step = line.strip()
            current_lines = []
        elif current_step:
            current_lines.append(line.strip())
            if line.strip().lower().startswith("*end step"):
                steps.append((current_step, current_lines))
                current_step = None
                current_lines = []

    assert len(steps) == 16, f"Expected 16 steps, found {len(steps)}"

    # Step 1: Stage-A
    step1_hdr, step1_body = steps[0]
    assert "stage-a" in step1_hdr.lower()
    rp_target_step1 = None
    for line in step1_body:
        if "n_rp" in line.lower():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4 and parts[1] == "2":
                rp_target_step1 = float(parts[3])
    assert rp_target_step1 is not None
    assert abs(rp_target_step1 - 0.00196510735) < 1e-8

    # Increments 1 to 5
    u_base = 0.00196510735
    previous_target = u_base

    for inc in range(1, 6):
        expected_u = u_base + inc * 1e-6

        # Mech1 step (Index: 3*inc - 2)
        mech1_hdr, mech1_body = steps[3*inc - 2]
        assert f"inc{inc}-mech1" in mech1_hdr.lower()

        # Check boundary cards
        boundary_blocks = []
        cur_b_hdr = None
        cur_b_lines = []
        for line in mech1_body:
            if line.lower().startswith("*boundary"):
                if cur_b_hdr:
                    boundary_blocks.append((cur_b_hdr, cur_b_lines))
                cur_b_hdr = line
                cur_b_lines = []
            elif cur_b_hdr and not line.startswith("*"):
                cur_b_lines.append(line)
        if cur_b_hdr:
            boundary_blocks.append((cur_b_hdr, cur_b_lines))

        # Check for NO OP=NEW mixing
        for b_hdr, _ in boundary_blocks:
            assert "op=new" not in b_hdr.lower(), f"Mech1 step {mech1_hdr} must use OP=MOD, not OP=NEW!"

        # N_RP target must be present and un-fixed
        rp_found = False
        for b_hdr, b_lines in boundary_blocks:
            for l in b_lines:
                if "n_rp" in l.lower():
                    assert "fixed" not in b_hdr.lower(), "Prescribed boundary block must not have 'fixed'"
                    parts = [p.strip() for p in l.split(",")]
                    val = float(parts[3])
                    assert abs(val - expected_u) < 1e-8
                    rp_found = True
        assert rp_found, f"N_RP target {expected_u} not found in Mech1"

        # Verify strictly increasing
        assert expected_u > previous_target
        previous_target = expected_u

        # Phase1 step (Index: 3*inc - 1)
        phase_hdr, phase_body = steps[3*inc - 1]
        assert f"inc{inc}-phase1" in phase_hdr.lower()
        phase_b = [l for l in phase_body if l.lower().startswith("*boundary")]
        assert len(phase_b) == 1
        assert "op=new" in phase_b[0].lower() and "fixed" in phase_b[0].lower()
        # DOF 3 must NOT be in phase body
        dof3_fixed = any("n_all" in l.lower() and "3" in l and "3" in l for l in phase_body)
        assert not dof3_fixed, "DOF 3 must NOT be fixed in Phase step!"

        # Mech2 step (Index: 3*inc)
        mech2_hdr, mech2_body = steps[3*inc]
        assert f"inc{inc}-mech2" in mech2_hdr.lower()
        mech2_b = [l for l in mech2_body if l.lower().startswith("*boundary")]
        assert len(mech2_b) == 1
        assert "op=new" in mech2_b[0].lower() and "fixed" in mech2_b[0].lower()
        # Phase fixed, boundaries fixed at current converged state
        assert any("n_all" in l.lower() and "3" in l for l in mech2_body)
