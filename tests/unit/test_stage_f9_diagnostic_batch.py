import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


def load_matrix_module():
    path = ROOT / "scripts/validation/run_stage_f9_datacheck_matrix.py"
    spec = importlib.util.spec_from_file_location("f9_matrix", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_label_offsets_and_common_bounds():
    module = load_matrix_module()
    deck = read("models/generated/mode_ii/f8_irreversibility_baseline/M2IRR_PATCH.inp")
    audit = module.label_audit(deck)
    assert audit["u1_labels"] == list(range(1, 24))
    assert audit["jelem_minus_n_elem"] == list(range(1, 24))
    assert audit["noel_minus_2_n_elem"] == list(range(1, 24))
    assert audit["minimum_common_index"] == 1
    assert audit["maximum_common_index"] == 23
    assert audit["all_active_indices_in_bounds"]


def test_matrix_is_bounded_datacheck_only_and_nonaborting():
    source = read("scripts/validation/run_stage_f9_datacheck_matrix.py")
    assert "MAX_CASES = 6" in source
    assert '"datacheck", "interactive"' in source
    assert "check=False" in source
    assert "analysis" not in source.split("command = [", 1)[1].split("]", 1)[0]
    assert "environment_file_sha256" in source
    assert "json.loads(path.read_text" in source


def test_remeshing_matrix_records_unicode_and_byte_types_without_solver():
    source = read("scripts/remeshing/qualify_stage_f9_remeshing_variable_type.py")
    assert '"unicode_tuple_control"' in source
    assert '"byte_string_tuple"' in source
    assert "nested_element_types" in source
    assert "MAX_ATTEMPTS = 6" in source
    assert "mdb.Job" not in source
    assert "waitForCompletion" not in source
    assert ".submit(" not in source


def test_independent_eligibility_and_exact_allowlist():
    source = read("scripts/hpc/stage_f/submit_stage_f9_two_job_batch.sh")
    assert '["M2DKMAT1", "M2RMTYPE1"]' in source
    assert source.count('["eligible"]') == 2
    assert 'test "$attempts" -le 2' in source
    assert "replacement_authorized" in source
    assert "depend=" not in source


def test_pbs_boundaries():
    job_a = read("scripts/hpc/stage_f/15_datacheck_matrix_f9.pbs")
    job_b = read("scripts/hpc/stage_f/16_remesh_type_f9.pbs")
    assert "#PBS -N M2DKMAT1" in job_a
    assert "#PBS -N M2RMTYPE1" in job_b
    assert "run_stage_f9_datacheck_matrix.py" in job_a
    assert "abaqus cae noGUI=" in job_b
    assert "abaqus job=" not in job_b


def test_manifests_are_valid_json_and_analysis_disabled():
    for relative in (
        "models/generated/mode_ii/f9_minimal_patch_datacheck_matrix/PACKAGE_MANIFEST.json",
        "models/generated/mode_ii/f9_miseseri_remesh_type_qualification/PACKAGE_MANIFEST.json",
    ):
        data = json.loads(read(relative))
        assert not data.get("analysis_authorized", False)
        assert not data.get("solver_analysis_authorized", False)
