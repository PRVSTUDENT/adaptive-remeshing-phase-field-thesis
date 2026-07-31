import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "models/generated/mode_ii/f11_irreversibility_baseline_instrumented"
C = ROOT / "models/generated/mode_ii/f11_irreversibility_candidate_instrumented"


def text(path):
    return path.read_text(encoding="utf-8")


def test_f10_frozen_hashes_and_f11_decks():
    frozen = json.loads(text(ROOT / "runs/hpc/stage_f/f11_instrumented_irreversibility_and_remesh_type_batch/F10_FROZEN_HASHES.json"))
    assert frozen["decks_byte_identical"]
    assert (B / "M2IRR_PATCH.inp").read_bytes() == (C / "M2IRR_PATCH.inp").read_bytes()


def test_mapping_and_diagnostic_layout():
    for package in (B, C):
        src = text(package / "M2IRR_PATCH.for")
        deck = text(package / "M2IRR_PATCH.inp")
        assert "N_ELEM=23" in src
        assert "NSTV=28" in src
        assert "*Depvar\n28" in deck
        for index in range(19, 29):
            assert "USRVAR(JELEM,%d,INPT)" % index in src
        assert "math.isfinite" not in text(ROOT / "scripts/postprocessing/extract_stage_f11_instrumented_pair.py")


def test_baseline_zero_penalty_candidate_active_penalty():
    baseline = text(B / "M2IRR_PATCH.for")
    candidate = text(C / "M2IRR_PATCH.for")
    assert "USRVAR(JELEM,22,INPT)=ONE" not in baseline
    assert "PENEDEN=HALF*PENALTY*GAP*GAP" not in baseline
    assert "USRVAR(JELEM,22,INPT)=ONE" in candidate
    assert "PENEDEN=HALF*PENALTY*GAP*GAP" in candidate


def test_energy_contract_and_no_invalid_global_request():
    decision = text(ROOT / "docs/decisions/STAGE_F11_ENERGY_DEFINITION_AND_ACCEPTANCE.md")
    assert "diagnostic balance" in decision
    assert "2% of maximum absolute external work" in decision
    assert "*Energy Output" not in text(B / "M2IRR_PATCH.inp")


def test_prior_state_load_precedes_write():
    source = text(C / "M2IRR_PATCH.for")
    assert source.index("PHASEOLD=SDV(1)") < source.index("SVARS(NSTVTO*(INPT-1)+I)=SDV(I)")
    assert "STEPITER.LE.20" in source


def test_remesh_wrapper_explicit_runtime_and_no_dunder_file():
    wrapper = text(ROOT / "scripts/remeshing/qualify_stage_f11_remeshing_variable_type.py")
    core = text(ROOT / "scripts/remeshing/qualify_stage_f11_remeshing_variable_type_core.py")
    assert "F11_RUNTIME_DIR" in wrapper and "__file__" not in wrapper
    assert "__file__" not in core
    assert "abaqus job=" not in wrapper + core
    assert "MAX_ATTEMPTS = 6" in core


def test_submission_contract():
    shell = text(ROOT / "scripts/hpc/stage_f/submit_stage_f11_three_job_batch.sh")
    assert '["M2IRRBAS3", "M2IRRCAN3", "M2RMTYPE3"]' in shell
    assert 'attempts=$((attempts+1))' in shell
    assert 'test "$attempts" -le 3' in shell
    assert "depend=" not in shell
    assert shell.count("qsub ") == 1
