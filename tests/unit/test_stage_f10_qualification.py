import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "models/generated/mode_ii/f10_irreversibility_baseline_corrected"
C = ROOT / "models/generated/mode_ii/f10_irreversibility_candidate_corrected"


def text(path):
    return path.read_text(encoding="utf-8")


def test_compact_runtime_mapping_and_equal_decks():
    assert (B / "M2IRR_PATCH.inp").read_bytes() == (C / "M2IRR_PATCH.inp").read_bytes()
    deck = text(B / "M2IRR_PATCH.inp")
    assert "24, 1, 2, 9, 8" in deck and "46, 27, 28, 35, 34" in deck
    assert "47, 1, 2, 9, 8" in deck and "69, 27, 28, 35, 34" in deck


def test_sources_have_mapping_and_guards():
    for path in (B / "M2IRR_PATCH.for", C / "M2IRR_PATCH.for"):
        source = text(path)
        assert source.count("N_ELEM=23") == 2
        assert source.count("F10 BOUNDS") == 4
        assert "USRVAR(JELEM-N_ELEM," not in source


def test_candidate_difference_and_math_gate():
    base = text(B / "M2IRR_PATCH.for")
    candidate = text(C / "M2IRR_PATCH.for")
    assert "PENALTY*GAP" not in base and "PENALTY*GAP" in candidate
    assert "PHASEOLD=SDV(1)" in candidate
    audit = json.loads(text(ROOT / "runs/hpc/stage_f/f10_corrected_minimal_irreversibility_and_remesh_type_batch/CANDIDATE_MATH_AUDIT.json"))
    assert audit["passed"] and audit["checks"]["finite_difference_pass"]


def test_remesh_helper_contract_and_no_solver():
    pbs = text(ROOT / "scripts/hpc/stage_f/19_remesh_type_f10.pbs")
    assert "runtime/no_solver_audit.py" in pbs
    assert "qualify_stage_f10_remeshing_variable_type.py" in pbs
    assert "abaqus job=" not in pbs


def test_parent_shell_accounting_and_allowlist():
    source = text(ROOT / "scripts/hpc/stage_f/submit_stage_f10_three_job_batch.sh")
    assert '["M2IRRBAS2", "M2IRRCAN2", "M2RMTYPE2"]' in source
    assert "attempts=$((attempts+1))" in source
    assert "successes=$((successes+1))" in source
    assert 'test "$attempts" -le 3' in source
    assert "depend=afterany" in source
