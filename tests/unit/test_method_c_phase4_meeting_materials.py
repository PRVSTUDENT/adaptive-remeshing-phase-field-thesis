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
        'fig_method_c_crack_extension.pdf': '7bb0c7d3203db319a29d899b72366244dca21a26e13e9686685bb8206c12bb46',
        'fig_method_c_crack_extension.png': '4ffa94694c4b0050fea3afc66866086a12abfdc05ea6161842a340b403c999b6',
        'fig_method_c_damage_evolution.gif': '70dacbcd94aa48d8ebb69f9c83e1544bbdf7a84dff71055ab1982540861dcaf8',
        'fig_method_c_damage_evolution_sequence.pdf': '0060b0befd69b985c17fefe4fc70636d4b0759a696abc38aa98d4d1966d67602',
        'fig_method_c_damage_evolution_sequence.png': 'f2e0e1abf9678e98d33f69e7d88f61adc06b80da05119a2c9b7e574e18865205',
        'fig_method_c_load_displacement.pdf': '81514ed1c50ec0e56afa7d6943b50a48f7a8ac6ec72bc690eb4f30c5a05f7059',
        'fig_method_c_load_displacement.png': 'e1586bd2cf4b0e0c6d5b7a267649e18d5960b19d35b4fe7254ce405191fa6c4e',
        'fig_method_c_loop_synthesis.pdf': 'a3ca7a3b019eb520f72dcc0e4d249be9daf023d210ab289799dc40e89b9a450b',
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
