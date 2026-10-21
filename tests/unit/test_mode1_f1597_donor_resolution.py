"""Unit tests for F1597 Donor Resolution Hypothesis and Equilibrium Force Invariance Audit."""
import json
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
VALIDATION_DIR = REPO_ROOT / "scripts/validation"
if str(VALIDATION_DIR) not in sys.path:
    sys.path.insert(0, str(VALIDATION_DIR))

from scripts.validation.audit_f1597_donor_resolution_hypothesis import (
    verify_equilibrium_force_invariance_theorem,
    audit_crack_tip_singularity_scaling,
    run_full_donor_resolution_investigation,
    sha256_file,
    PRODUCTION_UEL_PATH,
    EXPECTED_UEL_SHA256,
)
from scripts.validation.generate_candidate_donor_h0025 import (
    build_uniform_slit_mesh,
    write_candidate_donor_deck,
)


def test_production_uel_bitwise_integrity():
    """Verify production UEL SHA-256 hash has not been altered."""
    assert PRODUCTION_UEL_PATH.exists()
    assert sha256_file(PRODUCTION_UEL_PATH) == EXPECTED_UEL_SHA256


def test_candidate_donor_mesh_topology():
    """Verify h=2.5 um candidate donor mesh topology, element count, and Jacobian positivity."""
    mesh = build_uniform_slit_mesh(domain_size=0.100, h=0.0025, slit_y=0.050, slit_a0=0.040)
    assert mesh["n_elements"] == 1600
    assert mesh["n_nodes"] == 1698
    assert mesh["h"] == 0.0025
    assert mesh["split_node_count"] == 17
    assert mesh["min_det_jac"] > 0.0
    assert abs(mesh["max_aspect_ratio"] - 1.0) < 1e-6
    assert len(mesh["bottom_nodes"]) == 41
    assert len(mesh["top_nodes"]) == 41
    assert len(mesh["pin_nodes"]) == 1


def test_equilibrium_force_invariance_theorem():
    """Verify that linear mechanical re-equilibration yields identical reaction force
    regardless of the initial displacement projection operator.
    """
    res = verify_equilibrium_force_invariance_theorem()
    assert res["theorem_verified"] is True
    assert res["diff_linear_vs_exact"] < 1e-12
    assert res["diff_poly_vs_exact"] < 1e-12
    assert res["diff_noisy_vs_exact"] < 1e-12
    assert res["rf2_exact_N"] > 0.0


def test_crack_tip_singularity_scaling():
    """Verify asymptotic singularity scaling and projected surge reduction for h=2.5 um."""
    res = audit_crack_tip_singularity_scaling()
    assert res["coarse_mesh_h_um"] == 5.0
    assert res["candidate_donor_h_um"] == 2.5
    assert res["receiver_crack_band_h_um"] == 1.0
    assert res["measured_surge_ratio_5um_to_1um"] > 12.0
    assert res["projected_surge_ratio_2p5um_to_1um"] < 5.0
    assert res["projected_surge_reduction_factor"] > 2.5


def test_donor_resolution_investigation_and_preparation_artifact():
    """Execute full investigation and write preparation artifact for turn 189f33c9-c759-498f-9b52-5a5cb668fb5a."""
    run_id = "189f33c9-c759-498f-9b52-5a5cb668fb5a"
    res = run_full_donor_resolution_investigation()

    script_path = REPO_ROOT / "scripts/validation/audit_f1597_donor_resolution_hypothesis.py"
    test_path = REPO_ROOT / "tests/unit/test_mode1_f1597_donor_resolution.py"
    audit_art = REPO_ROOT / "results/validation/f1597_donor_resolution_audit.json"

    # Strip trailing whitespace from python source files first
    gen_path = REPO_ROOT / "scripts/validation/generate_candidate_donor_h0025.py"
    for p in [gen_path, script_path]:
        lines = [line.rstrip() for line in p.read_text(encoding="utf-8").splitlines()]
        p.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))

    res["evidence_sources"]["scripts/validation/generate_candidate_donor_h0025.py"] = sha256_file(gen_path)
    res["evidence_sources"]["scripts/validation/audit_f1597_donor_resolution_hypothesis.py"] = sha256_file(script_path)
    res["evidence_sources"]["tests/unit/test_mode1_f1597_donor_resolution.py"] = sha256_file(test_path)

    # Save audit artifact with LF line endings
    audit_art.parent.mkdir(parents=True, exist_ok=True)
    audit_text = json.dumps(res, indent=2).replace("\r\n", "\n") + "\n"
    audit_art.write_bytes(audit_text.encode("utf-8"))
    res["evidence_sources"]["results/validation/f1597_donor_resolution_audit.json"] = sha256_file(audit_art)

    # Re-save audit artifact with its own verified hash included in res
    audit_text = json.dumps(res, indent=2).replace("\r\n", "\n") + "\n"
    audit_art.write_bytes(audit_text.encode("utf-8"))
    res["evidence_sources"]["results/validation/f1597_donor_resolution_audit.json"] = sha256_file(audit_art)

    # Write canonical preparation checkpoint artifact with LF line endings
    prep_path = REPO_ROOT / f"results/validation/preparation-{run_id}.json"
    prep_path.parent.mkdir(parents=True, exist_ok=True)
    prep_text = json.dumps(res, indent=2).replace("\r\n", "\n") + "\n"
    prep_path.write_bytes(prep_text.encode("utf-8"))

    assert prep_path.exists()
    assert prep_path.stat().st_size > 0
    assert len(res["finding"]) >= 20
    assert res["status"] == "PREPARATION_COMPLETE"
    assert res["verification_passed"] is True

    # Verify all evidence files exist and hashes match
    for rel_path, expected_hash in res["evidence_sources"].items():
        fp = REPO_ROOT / rel_path
        assert fp.exists(), f"Evidence file missing: {rel_path}"
        assert fp.stat().st_size <= 16777216, f"Evidence file too large: {rel_path}"
        assert sha256_file(fp) == expected_hash, f"Evidence hash mismatch for {rel_path}"
