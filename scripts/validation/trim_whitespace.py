from pathlib import Path

target_files = [
    Path("project_coordination/sessions/2026-10-23_gemini-antigravity_F1597_776abb79-d620-41f2-8fe5-5245e29f45f8.md"),
    Path("scripts/validation/run_remote_helper.py"),
    Path("scripts/validation/run_cluster_startup_wrapper.py"),
    Path("scripts/validation/test_cluster_pdas_startup.py"),
    Path("tests/unit/test_mode1_f1597_turn71_cluster_env_and_pdas_adapter.py"),
    Path("scripts/validation/run_cluster_pdas_startup.sh"),
    Path("scripts/validation/inspect_cluster_python.sh"),
    Path("scripts/validation/check_python_module.sh"),
    Path("scripts/validation/test_coload_modules.sh"),
    Path("scripts/validation/generate_preparation_artifact.py")
]

for p in target_files:
    if p.exists():
        content = p.read_text(encoding="utf-8")
        lines = [line.rstrip() for line in content.splitlines()]
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Trimmed: {p}")
