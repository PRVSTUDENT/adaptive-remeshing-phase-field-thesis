"""Unit test suite for Method C Phase 4: Meeting Materials & Demo Synthesis.
Verifies existence, non-emptiness, and SHA-256 integrity of all publication figures,
as well as the completeness of the meeting report and supervisor slide deck.
"""

import os
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
FIG_DIR = os.path.join(REPO_ROOT, 'results', 'figures', 'method_c_demo')
REPORT_PATH = os.path.join(REPO_ROOT, 'docs', 'validation', 'METHOD_C_PHASE4_MEETING_MATERIALS_REPORT.md')
SLIDES_PATH = os.path.join(REPO_ROOT, 'docs', 'presentations', '2026-12-02_Method_C_Supervisor_Meeting_Slides.md')
SCRIPT_PATH = os.path.join(REPO_ROOT, 'scripts', 'postprocessing', 'plot_method_c_meeting_demo.py')


def test_figure_artifacts_exist_and_non_empty():
    assert os.path.isdir(FIG_DIR), f"Figures directory missing: {FIG_DIR}"
    
    expected_files = [
        ('fig_method_c_load_displacement.png', 100_000),
        ('fig_method_c_load_displacement.pdf', 10_000),
        ('fig_method_c_crack_extension.png', 100_000),
        ('fig_method_c_crack_extension.pdf', 10_000),
        ('fig_method_c_damage_evolution_sequence.png', 1_000_000),
        ('fig_method_c_damage_evolution_sequence.pdf', 500_000),
        ('fig_method_c_loop_synthesis.png', 1_000_000),
        ('fig_method_c_loop_synthesis.pdf', 200_000),
        ('fig_method_c_damage_evolution.gif', 1_000_000),
    ]

    for filename, min_bytes in expected_files:
        filepath = os.path.join(FIG_DIR, filename)
        assert os.path.isfile(filepath), f"Expected figure missing: {filepath}"
        sz = os.path.getsize(filepath)
        assert sz >= min_bytes, f"Figure {filename} size {sz} B is below minimum {min_bytes} B"


def test_figure_sha256_hashes():
    expected_hashes = {
        'fig_method_c_crack_extension.pdf': 'fb359466cb0f28e9db4c78027b4c6657855ad1bea4b12888278e3a7fbab6eb20',
        'fig_method_c_crack_extension.png': '62136efafe19122499ddcb1857ef46b84b0b1b34b10f2805b6fbc21f5835992c',
        'fig_method_c_damage_evolution.gif': '7836e808b47a3f36fc821682b1c0e262b7c86d9fe75325fa9743f055f65dfedd',
        'fig_method_c_damage_evolution_sequence.pdf': 'd963576f8baccc4fbe82f727493be80fb43fe52a7d93ae3bae2bd7c1c613ad7c',
        'fig_method_c_damage_evolution_sequence.png': '38a8b3cd8ce994e3a0836980cbdc6e6a6e5e440f7268c80d1adcae32a2c09eb7',
        'fig_method_c_load_displacement.pdf': '7d617d1ab4256c50bd2a4004e7b4af3b5774b2196a5f2e723ab75330fc494eb8',
        'fig_method_c_load_displacement.png': 'b6fb08115c40d80ad9b05ee8d40c7a54e4b70787d3f7f429581c7ece1a00202c',
        'fig_method_c_loop_synthesis.pdf': '5b252206473f07528ffd2b12ce3ad8745b26f9c864a8f449336ed665a6e3c86f',
        'fig_method_c_loop_synthesis.png': 'dcb69219f0d33c43fd98b2536ee1390d4f7fb3f2d2bf00bf50b9bcfed708637e',
    }

    for filename, expected_hash in expected_hashes.items():
        filepath = os.path.join(FIG_DIR, filename)
        computed_hash = hashlib.sha256(open(filepath, 'rb').read()).hexdigest()
        assert computed_hash == expected_hash, f"Hash mismatch for {filename}: {computed_hash} != {expected_hash}"


def test_meeting_materials_report_integrity():
    assert os.path.isfile(REPORT_PATH), f"Report missing: {REPORT_PATH}"
    with open(REPORT_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    assert "1424517.mmaster02" in content
    assert "1424584.mmaster02" in content
    assert "1424609.mmaster02" in content
    assert "0.648681" in content
    assert "0.262226" in content
    assert "-59.58" in content
    assert "0.3957" in content
    assert "0.650" in content
    assert "-1.37" in content
    assert "-0.77" in content
    assert "Exit 1" in content
    assert "cutback" in content


def test_supervisor_meeting_slides_integrity():
    assert os.path.isfile(SLIDES_PATH), f"Slides missing: {SLIDES_PATH}"
    with open(SLIDES_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    assert "2 December 2026" in content
    assert "Prof. Dr.-Ing. B. Kiefer" in content
    assert "Dr.-Ing. M. Roth" in content
    assert "0.648681" in content or "0.6487" in content
    assert "149 increments" in content
    assert "-59.58%" in content or "-59.6%" in content
    assert "13 December 2026" in content
    assert "13 January 2027" in content


def test_plot_script_syntax_and_integrity():
    assert os.path.isfile(SCRIPT_PATH), f"Script missing: {SCRIPT_PATH}"
    with open(SCRIPT_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    assert "plot_load_displacement" in content
    assert "plot_crack_extension" in content
    assert "plot_damage_evolution_sequence" in content
    assert "plot_loop_synthesis" in content
    assert "create_damage_animation" in content
