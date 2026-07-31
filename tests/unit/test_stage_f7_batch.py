from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_f7_orchestrator_exact_allowlist_and_two_calls():
    text = (ROOT / "scripts/hpc/stage_f/submit_stage_f7_two_job_batch.sh").read_text()
    assert '["M2H2IRR1","M2RMAPI2"]' in text
    assert text.count('submit_one "$JOB_') == 2
    assert 'status="consumed_monitoring"' in text
    assert "retry_authorized=False" in text
    assert "replacement_authorized=False" in text


def test_f7_jobs_contain_no_solver_launch():
    for rel in [
        "scripts/hpc/stage_f/10_h2_irreversibility_forensic_f7.pbs",
        "scripts/hpc/stage_f/11_miseseri_remesh_api_f7.pbs",
        "scripts/postprocessing/extract_h2_irreversibility_forensic_odb.py",
        "scripts/remeshing/qualify_mode_ii_native_miseseri_api.py",
    ]:
        text = (ROOT / rel).read_text()
        assert "mdb.Job.submit(" not in text
        assert "waitForCompletion(" not in text
        executable_lines = [
            line for line in text.splitlines()
            if not line.lstrip().startswith("grep ")
        ]
        assert all("abaqus job=" not in line for line in executable_lines)


def test_f7_interpreter_contracts_are_explicit():
    job = (ROOT / "scripts/hpc/stage_f/10_h2_irreversibility_forensic_f7.pbs").read_text()
    assert "abaqus python runtime/scripts/postprocessing" in job
    assert "python3 runtime/scripts/validation" in job
    api = (ROOT / "scripts/remeshing/qualify_mode_ii_native_miseseri_api.py").read_text()
    for name in ["F7_SOURCE_ODB", "F7_SOURCE_DECK", "F7_CONFIG_PATH", "F7_OUTPUT_DIRECTORY"]:
        assert name in api
