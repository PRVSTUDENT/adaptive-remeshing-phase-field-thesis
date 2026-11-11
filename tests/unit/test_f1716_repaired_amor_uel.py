"""
Unit test suite for Task F1716 Repaired Amor Volumetric-Deviatoric Split Subroutine.
Verifies f42_amor_split_uel_v2.for architectural separation, Fortran SAVE attributes,
dummy visualizer UMAT stiffness, bounded capacity energy loops, and IEEE NaN protection.
"""

import os
import hashlib
import re
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
V2_FOR_PATH = os.path.join(
    REPO_ROOT,
    "models",
    "pandey_kumar_mode1",
    "208_f1716_five_hole_production",
    "f42_amor_split_uel_v2.for",
)
V1_FOR_PATH = os.path.join(
    REPO_ROOT,
    "models",
    "pandey_kumar_mode1",
    "207_f1714_five_hole_benchmark",
    "f42_amor_split_uel.for",
)
CANONICAL_MIXED_PATH = os.path.join(
    REPO_ROOT,
    "models",
    "pandey_kumar_mode1",
    "f42_mixed_uel.for",
)


def compute_sha256(filepath):
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest().upper()


def test_01_file_existence_and_hashes():
    """Verify all subroutines exist and canonical files remain bitwise frozen."""
    assert os.path.exists(V2_FOR_PATH), f"Missing v2 subroutine: {V2_FOR_PATH}"
    assert os.path.exists(V1_FOR_PATH), f"Missing v1 subroutine: {V1_FOR_PATH}"
    assert os.path.exists(CANONICAL_MIXED_PATH), f"Missing canonical mixed subroutine: {CANONICAL_MIXED_PATH}"

    # Verify canonical mixed UEL is bitwise frozen
    canonical_hash = compute_sha256(CANONICAL_MIXED_PATH)
    assert canonical_hash == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6", (
        f"Canonical f42_mixed_uel.for hash mismatch: {canonical_hash}"
    )

    # Verify v1 amor split UEL is bitwise frozen
    v1_hash = compute_sha256(V1_FOR_PATH)
    assert v1_hash.startswith("6778B685"), f"V1 f42_amor_split_uel.for hash mismatch: {v1_hash}"

    # Verify v2 has distinct hash
    v2_hash = compute_sha256(V2_FOR_PATH)
    assert v2_hash != v1_hash
    assert v2_hash != canonical_hash


def test_02_dummy_visualizer_umat_stiffness():
    """Verify Layer 3 UMAT in v2 is a pure dummy visualizer without duplicate stiffness."""
    with open(V2_FOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract UMAT body
    umat_match = re.search(r"SUBROUTINE UMAT\b.*?\bEND\b", content, re.DOTALL)
    assert umat_match is not None, "SUBROUTINE UMAT not found in v2"
    umat_body = umat_match.group(0)

    # Verify dummy stiffness DDSDDE(I,I) = 1.D-11
    assert "DDSDDE(I,I) = 1.D-11" in umat_body or "DDSDDE(I,I) = 1.0D-11" in umat_body
    assert "STRESS(I) = 0.D0" in umat_body

    # Verify constitutive matrix equations are NOT in UMAT
    assert "E_K_BULK + (FOUR/THREE)*E_MU" not in umat_body, (
        "Fatal: UMAT still contains physical bulk/shear stiffness assembly! Duplicate stiffness defect."
    )
    assert "DDSDDE(1,1)" not in umat_body, "Explicit DDSDDE(1,1) assignment found in visualizer UMAT"
    assert "DDSDDE(2,2)" not in umat_body, "Explicit DDSDDE(2,2) assignment found in visualizer UMAT"


def test_03_fortran_save_attribute_persistence():
    """Verify SAVE /CB_STATE_TRANS/ and SAVE /CB_CONFIG/ are present in all subroutines."""
    with open(V2_FOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Check for UEXTERNALDB
    uexternaldb = re.search(r"SUBROUTINE UEXTERNALDB\b.*?\bEND\b", content, re.DOTALL).group(0)
    assert "SAVE /CB_STATE_TRANS/" in uexternaldb
    assert "SAVE /CB_CONFIG/" in uexternaldb

    # Check for UEL
    uel = re.search(r"SUBROUTINE UEL\b.*?\bEND\b", content, re.DOTALL).group(0)
    assert "SAVE /CB_STATE_TRANS/" in uel
    assert "SAVE /CB_CONFIG/" in uel

    # Check for UMAT
    umat = re.search(r"SUBROUTINE UMAT\b.*?\bEND\b", content, re.DOTALL).group(0)
    assert "SAVE /CB_STATE_TRANS/" in umat
    assert "SAVE /CB_CONFIG/" in umat


def test_04_bounded_capacity_energy_integration():
    """Verify UEXTERNALDB LOP=2 bounds energy integration to active elements."""
    with open(V2_FOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    uexternaldb = re.search(r"SUBROUTINE UEXTERNALDB\b.*?\bEND\b", content, re.DOTALL).group(0)

    # In LOP=2, loop should be over N_ACTIVE, not N_CAPACITY
    lop2_match = re.search(r"ELSE IF \(LOP \.EQ\. 2\).*?RETURN", uexternaldb, re.DOTALL)
    assert lop2_match is not None
    lop2_body = lop2_match.group(0)

    assert "DO I=1, N_ACTIVE" in lop2_body
    assert "DO I=1, N_CAPACITY" not in lop2_body

    # Check IEEE NaN detection on energy accumulation (fail-closed, not silent)
    assert "FATAL_NAN_GUARD: NaN E_ELAS" in lop2_body
    assert "FATAL_NAN_GUARD: NaN E_FRAC" in lop2_body


def test_05_ieee_nan_and_bounds_clamping():
    """Verify state variable clamping and fail-closed NaN protection in UMAT and UEL."""
    with open(V2_FOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    umat = re.search(r"SUBROUTINE UMAT\b.*?\bEND\b", content, re.DOTALL).group(0)

    # Fail-closed NaN guard in UMAT (rejection with PNEWDT cutback, not silent clamping)
    assert "FATAL_NAN_GUARD: NaN phase in UMAT" in umat
    assert "PNEWDT = 0.25D0" in umat
    assert "D_VAL = -999.D0" in umat
    assert "D_VAL .GT. 1.D0" in umat

    # History variable clamping H >= 0 with NaN rejection
    assert "FATAL_NAN_GUARD: NaN history in UMAT" in umat
    assert "H_VAL = -999.D0" in umat

    # Energy projections expose -999.D0 sentinel on NaN
    assert "STATEV(17) = -999.D0" in umat
    assert "STATEV(18) = -999.D0" in umat


def test_06_amor_constitutive_split_in_uel():
    """Verify that UEL retains full volumetric-deviatoric split for Quad and Tri."""
    with open(V2_FOR_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    uel = re.search(r"SUBROUTINE UEL\b.*?\bEND\b", content, re.DOTALL).group(0)

    # Tension case
    assert "D_ELAS(1,1) = (E_K_BULK + (FOUR/THREE)*E_MU) * DEG" in uel
    assert "D_ELAS(1,2) = (E_K_BULK - (TWO/THREE)*E_MU) * DEG" in uel
    # Compression case: bulk modulus undegraded!
    assert "D_ELAS(1,1) = E_K_BULK + (FOUR/THREE)*E_MU * DEG" in uel
    assert "D_ELAS(1,2) = E_K_BULK - (TWO/THREE)*E_MU * DEG" in uel

    # Crack driving energy has positive volumetric strain energy + deviatoric strain energy
    assert "POS_M = HALF * E_K_BULK * (TR_E**2) + E_MU * EPS_DEV_SQ" in uel
    assert "POS_M = E_MU * EPS_DEV_SQ" in uel


def test_07_fortran77_fixed_form_line_length():
    """Verify all lines conform to standard Fortran 77 fixed-form length (<= 72 chars)."""
    with open(V2_FOR_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    long_lines = []
    for idx, line in enumerate(lines, start=1):
        line_clean = line.rstrip("\r\n")
        if len(line_clean) > 72:
            long_lines.append((idx, len(line_clean), line_clean))

    assert len(long_lines) == 0, f"Found {len(long_lines)} lines exceeding 72 chars in {V2_FOR_PATH}: {long_lines[:5]}"


def test_08_pilot_solver_completion_and_equilibrium():
    """Verify authentic cluster pilot completed with Exit 0, finite disp, and exact equilibrium."""
    val_dir = os.path.join(REPO_ROOT, "results", "validation")
    sta_path = os.path.join(val_dir, "PK_F1716_PILOT.sta")
    dat_path = os.path.join(val_dir, "PK_F1716_PILOT.dat")

    assert os.path.exists(sta_path), f"Missing {sta_path}"
    assert os.path.exists(dat_path), f"Missing {dat_path}"

    with open(sta_path, "r") as f:
        sta_text = f.read()

    assert "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in sta_text
    # 5 incs in step 1, 10 incs in step 2 = 15 total incs
    step1_incs = len(re.findall(r"^\s+1\s+\d+\s+1\s+0\s+\d+", sta_text, re.MULTILINE))
    step2_incs = len(re.findall(r"^\s+2\s+\d+\s+1\s+0\s+\d+", sta_text, re.MULTILINE))
    assert step1_incs == 5, f"Expected 5 increments in Step 1, got {step1_incs}"
    assert step2_incs == 10, f"Expected 10 increments in Step 2, got {step2_incs}"

    # Parse node tables from DAT
    with open(dat_path, "r") as f:
        dat_text = f.read()

    # Verify no NaN or Inf strings in entire dat text
    assert "NaN" not in dat_text
    assert "Infinity" not in dat_text

    # Extract N_RP and N_BOTTOM tables
    rp_matches = re.findall(
        r"FOR NODES BELONGING TO NODE SET N_RP.*?100\s+([\d\.E\+\-]+)\s+([\d\.E\+\-]+)",
        dat_text,
        re.DOTALL,
    )
    assert len(rp_matches) == 15, f"Expected 15 N_RP output frames, got {len(rp_matches)}"

    # Check terminal displacement and force
    u2_final, rf2_final = float(rp_matches[-1][0]), float(rp_matches[-1][1])
    assert abs(u2_final - 0.020) < 1e-6, f"Terminal displacement mismatch: {u2_final}"
    assert rf2_final > 2.80, f"Terminal reaction force too low: {rf2_final}"

    # Verify reaction force equilibrium between top and bottom
    bottom_sections = re.findall(
        r"FOR NODES BELONGING TO NODE SET N_BOTTOM.*?NODE FOOT-.*?\n\s*\n(.*?)\n\s*MAXIMUM",
        dat_text,
        re.DOTALL,
    )
    assert len(bottom_sections) == 15

    for idx, (rp_frame, bot_frame) in enumerate(zip(rp_matches, bottom_sections)):
        rf_top = float(rp_frame[1])
        bot_lines = bot_frame.strip().splitlines()
        rf_bot_sum = 0.0
        for line in bot_lines:
            parts = line.split()
            if len(parts) >= 2 and parts[0].isdigit():
                rf_bot_sum += float(parts[1])

        # Equilibrium: F_top + sum(RF_bot) == 0 (to within tolerance)
        discrepancy = abs(rf_top + rf_bot_sum)
        assert discrepancy < 1e-6, f"Frame {idx+1} equilibrium violation: top={rf_top}, bot_sum={rf_bot_sum}, diff={discrepancy}"


def test_09_pilot_state_variables_and_damage_bounds():
    """Verify visualizer SDVs are finite, non-NaN, and strictly bounded."""
    val_dir = os.path.join(REPO_ROOT, "results", "validation")
    dat_path = os.path.join(val_dir, "PK_F1716_PILOT.dat")

    with open(dat_path, "r") as f:
        dat_text = f.read()

    # Find element tables
    el_sections = re.findall(
        r"ELEMENT\s+PT FOOT-.*?SDV1\s+SDV2\s+SDV15\s+SDV17\s+SDV18.*?\n\s*\n(.*?)(?=\n\s*(?:ELEMENT|\*|MAXIMUM|THE FOLLOWING|\Z))",
        dat_text,
        re.DOTALL,
    )
    assert len(el_sections) >= 15

    for section in el_sections:
        for line in section.strip().splitlines():
            parts = line.split()
            if len(parts) >= 7 and parts[0].isdigit():
                d_val = float(parts[2])
                h_val = float(parts[3])
                deg_val = float(parts[4])
                e_frac = float(parts[5])
                e_elas = float(parts[6])

                assert 0.0 <= d_val <= 1.0, f"Damage bound violation: d = {d_val}"
                assert h_val >= 0.0, f"History negativity: H = {h_val}"
                assert 0.0 < deg_val <= 1.0, f"Degradation bound violation: g(d) = {deg_val}"
                assert e_frac >= 0.0, f"Negative fracture energy: {e_frac}"
                assert e_elas >= 0.0, f"Negative elastic energy: {e_elas}"


def test_10_pilot_energy_balance_monotonicity():
    """Verify uel_energy_balance.csv has zero NaNs and monotonic energy evolution."""
    val_dir = os.path.join(REPO_ROOT, "results", "validation")
    csv_path = os.path.join(val_dir, "f1716_pilot_uel_energy_balance.csv")
    assert os.path.exists(csv_path), f"Missing {csv_path}"

    with open(csv_path, "r") as f:
        lines = f.readlines()

    assert len(lines) == 16  # header + 15 increments

    prev_e_tot = 0.0
    for idx, line in enumerate(lines[1:], start=1):
        parts = [p.strip() for p in line.split(",")]
        assert len(parts) == 7
        step = int(parts[0])
        inc = int(parts[1])
        tot_time = float(parts[2])
        e_elas = float(parts[4])
        e_frac = float(parts[5])
        e_tot = float(parts[6])

        # No NaNs
        assert not (e_elas != e_elas), f"NaN in E_elas at row {idx}"
        assert not (e_frac != e_frac), f"NaN in E_frac at row {idx}"
        assert not (e_tot != e_tot), f"NaN in E_tot at row {idx}"

        # Non-negative energies
        assert e_elas >= 0.0
        assert e_frac >= 0.0
        assert e_tot >= 0.0

        # Total energy must increase monotonically with applied displacement
        assert e_tot >= prev_e_tot - 1e-12, f"Total energy decreased at row {idx}: prev={prev_e_tot}, curr={e_tot}"
        prev_e_tot = e_tot
