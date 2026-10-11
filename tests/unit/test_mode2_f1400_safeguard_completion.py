"""
Unit Test Suite for Task F1400:
Verification of Terminal Completion and Complete-History Parity of Mode-II 72k Safeguard Job 1411557.mmaster02.

Author: Gemini Antigravity
Task: F1400
Date: 2026-10-11
"""

import os
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SAFEGUARD_DIR = os.path.join(REPO_ROOT, 'runs', 'mode2', 'fixed_convergence', 'evidence', '04_fine_72h')
PRIMARY_DIR = os.path.join(REPO_ROOT, 'runs', 'mode2', 'fixed_convergence', 'evidence', '04_fine_72k')

SAFEGUARD_DAT = os.path.join(SAFEGUARD_DIR, 'M2_FIX_FINE_72H.dat')
SAFEGUARD_STA = os.path.join(SAFEGUARD_DIR, 'M2_FIX_FINE_72H.sta')
PRIMARY_DAT = os.path.join(PRIMARY_DIR, 'M2_FIX_FINE_72K.dat')
PRIMARY_STA = os.path.join(PRIMARY_DIR, 'M2_FIX_FINE_72K.sta')
HPC_LEDGER = os.path.join(REPO_ROOT, 'project_coordination', 'HPC_JOB_LEDGER.csv')


def parse_dat_rp(path):
    pts = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if line.strip().startswith('999999'):
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        u_mm = float(parts[1])
                        rf_kn = float(parts[2])
                        pts.append((u_mm * 1000.0, rf_kn * 1000.0, line.strip()))
                    except ValueError:
                        pass
    return pts


def test_safeguard_files_exist():
    assert os.path.exists(SAFEGUARD_DAT), f"Missing {SAFEGUARD_DAT}"
    assert os.path.exists(SAFEGUARD_STA), f"Missing {SAFEGUARD_STA}"
    assert os.path.getsize(SAFEGUARD_DAT) == 2619711, "DAT size mismatch"
    assert os.path.getsize(SAFEGUARD_STA) == 270043, "STA size mismatch"


def test_safeguard_completed_4022_increments():
    pts = parse_dat_rp(SAFEGUARD_DAT)
    assert len(pts) == 4022, f"Expected 4,022 increments, got {len(pts)}"


def test_safeguard_terminal_displacement():
    pts = parse_dat_rp(SAFEGUARD_DAT)
    term_u, term_rf, _ = pts[-1]
    assert pytest.approx(term_u, abs=1e-5) == 20.0000, f"Expected terminal displacement 20.0 um, got {term_u}"


def test_safeguard_peak_reaction_force():
    pts = parse_dat_rp(SAFEGUARD_DAT)
    peak = max(pts, key=lambda x: x[1])
    peak_u, peak_rf, _ = peak
    assert pytest.approx(peak_rf, abs=1e-4) == 415.9895, f"Expected peak force 415.9895 N, got {peak_rf}"
    assert pytest.approx(peak_u, abs=1e-5) == 9.4700, f"Expected peak displacement 9.4700 um, got {peak_u}"


def test_safeguard_terminal_reaction_force():
    pts = parse_dat_rp(SAFEGUARD_DAT)
    term_u, term_rf, _ = pts[-1]
    assert pytest.approx(term_rf, abs=1e-4) == 387.4692, f"Expected terminal force 387.4692 N, got {term_rf}"


def test_safeguard_vs_primary_history_reproducibility():
    s_pts = parse_dat_rp(SAFEGUARD_DAT)
    p_pts = parse_dat_rp(PRIMARY_DAT)
    assert len(s_pts) == len(p_pts) == 4022

    max_du = 0.0
    max_drf = 0.0
    mismatched_lines = 0

    for s, p in zip(s_pts, p_pts):
        du = abs(s[0] - p[0])
        drf = abs(s[1] - p[1])
        if du > max_du:
            max_du = du
        if drf > max_drf:
            max_drf = drf
        if s[2] != p[2]:
            mismatched_lines += 1

    assert max_du == 0.0, f"Displacement differences detected: max_du = {max_du}"
    assert max_drf == 0.0, f"Force differences detected: max_drf = {max_drf}"
    assert mismatched_lines == 0, f"Text line mismatches in node output: {mismatched_lines}"


def test_safeguard_sta_completion_status():
    with open(SAFEGUARD_STA, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    assert "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in content
    # Check that Step 2 reached 1.00 (total 2.00)
    lines = [l.strip() for l in content.splitlines() if l.strip()]
    assert any("2  2000" in l and "2.00" in l for l in lines[-10:])


def test_governance_hpc_ledger():
    with open(HPC_LEDGER, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    hpc_557_lines = [l for l in lines if '1411557.mmaster02' in l]
    assert len(hpc_557_lines) == 1, "Expected exactly 1 entry for 1411557 in HPC_JOB_LEDGER.csv"
    line = hpc_557_lines[0]
    parts = line.split(',')
    assert parts[6] == 'F', f"Expected status F in ledger, got {parts[6]}"
    assert parts[7] == '0', f"Expected exit code 0 in ledger, got {parts[7]}"
