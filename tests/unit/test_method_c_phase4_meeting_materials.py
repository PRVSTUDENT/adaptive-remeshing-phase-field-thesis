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
        'fig_method_c_crack_extension.pdf': '0a16622b1e9b1a5c7c992a8978091d4d828112e8234223ce113bc1c7a349678f',
        'fig_method_c_crack_extension.png': 'bdb9bad6126f51476093f86b4269274473c3f1560d5d4fdb4163afc78b61fe92',
        'fig_method_c_damage_evolution.gif': '70dacbcd94aa48d8ebb69f9c83e1544bbdf7a84dff71055ab1982540861dcaf8',
        'fig_method_c_damage_evolution_sequence.pdf': '68f992dfd4b6f296f1440a510a603d819d73d3bfa846caf24a432983237542fa',
        'fig_method_c_damage_evolution_sequence.png': 'f2e0e1abf9678e98d33f69e7d88f61adc06b80da05119a2c9b7e574e18865205',
        'fig_method_c_load_displacement.pdf': '3c690e4d79206404ee827c539fbbef5ed9e9edfc59820249526116c364b0207c',
        'fig_method_c_load_displacement.png': '293e8d2080e2797731ea9e5a1d577f4040ec2cfe087b3c8f667bb61d2c9ca577',
        'fig_method_c_loop_synthesis.pdf': 'fedf6a986f51bdf64c29ce6751ffe33eec3ad32441dcca82cf4d24fa812a6dc7',
        'fig_method_c_loop_synthesis.png': '6300dea166b4bd62efbfdbbc1b712c8900999f12991e3d5d4b8dbd93e0b5b00c',
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
    assert "0.8957" in content
    assert "x_tip = 0.8957" in content
