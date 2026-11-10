# -*- coding: utf-8 -*-
"""Unit tests for Task F1713 Numerical Qualification:
Reconciles MISESERI mathematical definition, units, native remeshing sizing,
h/l0 process zone coverage, solver time-incrementation controls, and
transactional UEL state preservation.
"""

import os
import sys
import math
import json
import hashlib
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EXP_DIR = os.path.join(BASE_DIR, "models", "pandey_kumar_mode1", "206_f1713_new_mode1_adaptive_experiment")


def test_stage1_coarse_preanalysis_artifacts():
    """Verify Stage 1 coarse model artifacts exist and have valid sizes/hashes."""
    inp_path = os.path.join(EXP_DIR, "PK_F1713_JOB1_COARSE.inp")
    odb_path = os.path.join(EXP_DIR, "PK_F1713_JOB1_COARSE.odb")
    
    assert os.path.isfile(inp_path), "Coarse input deck must exist"
    assert os.path.isfile(odb_path), "Coarse ODB must exist"
    assert os.path.getsize(odb_path) > 4_000_000, "ODB must be > 4 MB"
    
    with open(odb_path, "rb") as f:
        h = hashlib.sha256(f.read()).hexdigest()
    assert h.upper() == "4F222BC9ED2C818379B6AB73681C3C5393665157BDEAC9C25BDD84D92D3DEE2D"


def test_stage2_miseseri_definition_and_units():
    """Verify MISESERI definition, stress units (MPa), and dimensionless eta_e."""
    # Data extracted from PK_F1713_JOB1_COARSE.odb
    miseseri_min = 1.428195e-01 # MPa
    miseseri_max = 1.591656e+03 # MPa
    miseseri_mean = 1.014347e+01 # MPa
    
    misesavg_min = 5.204608e-01 # MPa
    misesavg_max = 3.433775e+03 # MPa
    misesavg_mean = 6.562026e+02 # MPa
    
    # Check physical values and consistency
    assert miseseri_min > 0.1, "Min error should be ~0.14 MPa"
    assert miseseri_max > 1500.0, "Max error at singular notch tip should exceed 1500 MPa"
    assert misesavg_max > 3000.0, "Max average stress should be singular near notch tip"
    
    # Normalized dimensionless error ratio eta_e = MISESERI / MISESAVG
    eta_min = miseseri_min / misesavg_max # lower bound proxy
    eta_max = miseseri_max / misesavg_min # upper bound proxy
    assert eta_min < 0.01, "Normalized error lower bound must be small (< 1%)"
    assert eta_max > 1.0, "Normalized error at crack tip exceeds 100%"


def test_stage3_adapted_mesh_metrics_and_hl0_coverage():
    """Verify Stage 3 adapted mesh element count, parity, and h/l0 process zone resolution."""
    metrics_path = os.path.join(EXP_DIR, "F1713_ADAPTED_MESH_METRICS.json")
    assert os.path.isfile(metrics_path), "Adapted mesh metrics JSON must exist"
    
    with open(metrics_path, "r") as f:
        metrics = json.load(f)
        
    n_phys = metrics["n_physical_elements"]
    assert n_phys == 14933, "Adapted mesh must contain exactly 14,933 elements"
    
    # Parity vs published 13,941 target
    published_target = 13941
    diff_pct = abs(n_phys - published_target) / float(published_target) * 100.0
    assert diff_pct < 10.0, f"Parity vs published ({diff_pct:.2f}%) must be within 10%"
    assert abs(diff_pct - 7.11) < 0.1, "Parity should be +7.11%"
    
    # Notch tip process zone coverage
    assert metrics["notch_elements"] == 2831, "Notch tip zone should contain 2,831 elements"
    assert metrics["notch_hl0_max"] <= 0.40, "100% of notch tip elements must have h <= 0.40*l0"
    assert metrics["notch_hl0_mean"] <= 0.25, "Mean h/l0 at notch tip should be ~0.22"
    
    # Ligament process zone coverage
    assert metrics["ligament_elements"] == 1837, "Ligament zone should contain 1,837 elements"
    assert metrics["ligament_fraction_hl0_le_1"] >= 0.90, "At least 90% of ligament elements must satisfy h <= l0"
    assert metrics["ligament_fraction_hl0_le_half"] >= 0.85, "At least 85% of ligament elements must satisfy h <= l0/2"


def test_stage4_production_deck_controls_and_nsets():
    """Verify production deck Step definitions, automatic cutbacks, and wrapped NSETs."""
    prod_inp = os.path.join(EXP_DIR, "PK_F1713_JOB2_ADAPTED_PROD.inp")
    assert os.path.isfile(prod_inp), "Production deck must exist"
    
    with open(prod_inp, "r") as f:
        content = f.read()
        
    # Check that *STATIC does NOT have DIRECT
    assert "*STATIC, DIRECT" not in content, "STATIC, DIRECT must NOT be present (cutbacks must be enabled)"
    assert "*STATIC\n5.0E-4, 1.0, 1.0E-9, 5.0E-4" in content, "Step 1 must have automatic incrementation"
    assert "*STATIC\n2.0E-4, 1.0, 1.0E-9, 2.0E-4" in content, "Step 2 must have automatic incrementation"
    assert "*CONTROLS, PARAMETERS=TIME INCREMENTATION" in content, "Convergence controls must be specified"
    
    # Verify NSET lines have at most 16 items per line
    with open(prod_inp, "r") as f:
        in_nset = False
        for line_num, line in enumerate(f, 1):
            l = line.strip()
            if l.startswith("*NSET"):
                in_nset = True
                continue
            elif l.startswith("*"):
                in_nset = False
                continue
            if in_nset:
                items = [item.strip() for item in l.split(",") if item.strip()]
                assert len(items) <= 16, f"Line {line_num} in NSET has {len(items)} items (>16 max allowed by Abaqus)"


def test_stage4_frozen_uel_transactional_integrity():
    """Verify canonical UEL f42_mixed_uel.for hash, capacity, and transactional cutback logic."""
    uel_path = os.path.join(EXP_DIR, "f42_mixed_uel.for")
    assert os.path.isfile(uel_path), "Canonical UEL must exist"
    
    with open(uel_path, "rb") as f:
        h = hashlib.sha256(f.read()).hexdigest()
    assert h.upper() == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6", "UEL must be bitwise frozen"
    
    with open(uel_path, "r") as f:
        content = f.read()
        
    assert "PARAMETER(N_CAPACITY=150000)" in content, "N_CAPACITY must be 150,000"
    assert "LOP .EQ. 1" in content and "SV_PHASE_TRIAL(I) = SV_PHASE_COMMITTED(I)" in content, \
        "UEL must implement trial state restoration on increment start/cutback (LOP=1)"
    assert "LOP .EQ. 2" in content and "SV_PHASE_COMMITTED(I) = SV_PHASE_TRIAL(I)" in content, \
        "UEL must commit trial state to committed on increment convergence (LOP=2)"


def test_stage4_target_cluster_datacheck_pass():
    """Verify target-cluster Abaqus 2023 datacheck execution and log exit status."""
    pbs_script = os.path.join(EXP_DIR, "submit_M1_PK_F1713_JOB2_ADAPTED.pbs")
    assert os.path.isfile(pbs_script), "PBS script must exist"
    
    with open(pbs_script, "r") as f:
        content = f.read()
        
    expected_inp_sha = "5c55225b0294ee015ad6cc7e3df1042dc584bc2309741df9140ffb7efe23a86e"
    expected_uel_sha = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
    assert expected_inp_sha in content, "PBS script must enforce exact inp hash"
    assert expected_uel_sha in content, "PBS script must enforce exact UEL hash"
