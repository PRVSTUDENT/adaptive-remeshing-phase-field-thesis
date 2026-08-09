import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / 'models/generated/mode_ii'
RUN = ROOT / 'runs/hpc/stage_f/f19_f18_failure_closeout_and_three_job_repair_preparation'

PACKAGES = [
    ('f19_penalty_active_rollback_control', 'M2IRRROLLCTL5', 'control', '01:00:00'),
    ('f19_penalty_active_rollback_forced', 'M2IRRROLLFORCE5', 'forced', '01:00:00'),
    ('f19_native_adaptive_region_repair', 'M2RMREG6', 'adaptive', '00:30:00'),
]

def dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def package(name: str, job: str, kind: str, walltime: str) -> None:
    base = MODEL / name
    runtime = sorted(p.name for p in (base / 'runtime').iterdir() if p.is_file() and p.name != '.gitignore')
    dump(base / 'F19_MANIFEST_ALLOWLIST.json', {'runtime_files': runtime})
    common = {'job': job, 'kind': kind, 'classification': 'prepared_not_authorized', 'queue': 'entry_imfdfkmq',
              'execution_authorized': False, 'submission_approved': False, 'cpus': 1, 'memory_gb': 8, 'walltime': walltime}
    dump(base / 'PACKAGE_MANIFEST.json', common)
    dump(base / 'F19_RUNTIME_MANIFEST.json', {'job': job, 'runtime_files': runtime})
    zero = {'qsub_attempts': 0, 'successful_submissions': 0, 'failed_qsub_attempts': 0, 'PBS_jobs': [],
            'solver_executions': 0, 'datacheck_executions': 0, 'CAE_executions': 0,
            'adaptivity_process_submissions': 0, 'model_adaptiveRemesh_calls': 0, 'native_remesh_calls': 0,
            'candidates_generated': 0, 'refined_analyses': 0, 'execution_authorized': False,
            'submission_approved': False, 'maximum_jobs_now': 0}
    dump(base / 'F19_NO_EXECUTION_AUDIT.json', zero)
    dump(base / 'STATUS.json', {'classification': 'prepared_not_authorized', **zero})
    files = sorted([p for p in base.rglob('*') if p.is_file() and p.name not in {'F19_SHA256SUMS', 'SHA256SUMS'}
                    and '__pycache__' not in p.parts and p.suffix not in {'.pyc', '.o', '.so'}])
    lines = ''.join(f'{digest(p)}  {p.relative_to(base).as_posix()}\n' for p in files)
    (base / 'F19_SHA256SUMS').write_text(lines, encoding='ascii', newline='\n')
    (base / 'SHA256SUMS').write_text(lines, encoding='ascii', newline='\n')

def main() -> None:
    for args in PACKAGES:
        package(*args)
    RUN.mkdir(parents=True, exist_ok=True)
    dump(RUN / 'F19_THREE_JOB_REPAIR_PLAN.json', {'jobs': [p[1] for p in PACKAGES], 'submission_order': [p[1] for p in PACKAGES],
         'maximum_qsub_invocations': 3, 'maximum_successful_submissions': 3, 'maximum_simultaneously_running_project_jobs': 2,
         'prepared_not_authorized': True})
    dump(RUN / 'F19_ROLLBACK_FLAG_IO_CONTRACT.json', {'required_files': ['<JOBNAME>_f19_force_mode.flag', '<JOBNAME>_f19_cutback_state.flag'],
         'control_values': [0, 0], 'forced_values': [1, 0], 'integer_only': True, 'final_lf': True,
         'inquire_before_open': True, 'checked_operations': ['INQUIRE', 'OPEN', 'READ', 'WRITE', 'CLOSE'],
         'latch_outside_svars': True, 'missing_or_invalid_is_controlled_failure': True})
    dump(RUN / 'F19_ROLLBACK_ACCEPTANCE.json', {'control_deliberate_pnewdt_requests': 0, 'forced_pnewdt': 0.5,
         'forced_request_count': 1, 'trigger': {'KSTEP': 2, 'KINC': 4, 'JELEM': 6, 'integration_point': 1,
         'step_time': 0.08, 'total_time': 1.08, 'time_tolerance': 1e-10, 'healing_tolerance': 1e-8},
         'endpoint_displacement_mm': 1e-10, 'matched_phase': 1e-7, 'final_phase': 1e-6,
         'maximum_RF_difference': 1e-4, 'RF_U_NRMSE': 1e-4, 'relative_energy_difference': 1e-4})
    dump(RUN / 'F19_ADAPTIVE_EVIDENCE_LIFECYCLE_CONTRACT.json', {'work_evidence_dir': '$WORK_ROOT/generated_evidence',
         'final_evidence_dir': '$EVIDENCE_DIR', 'preserve_first_command_return_code': True,
         'exit_priority': ['environment_contract', 'compatibility_helper', 'CAE', 'missing_evidence', 'manifest_validation', 'success'],
         'partial_evidence_staged_on_failure': True})
    dump(RUN / 'F19_ADAPTIVE_ACCEPTANCE.json', {'allowed_classifications': ['native_adaptive_region_contract_qualified',
         'native_adaptive_geometry_reconstruction_required', 'native_adaptive_region_api_unresolved',
         'native_adaptive_region_construction_failed', 'native_adaptive_region_rule_association_failed',
         'native_adaptive_region_source_integrity_failed', 'native_adaptive_region_evidence_incomplete'], 'zero_execution_required': True})
    dump(RUN / 'F19_DEPENDENCIES.json', {'M2IRRROLLCTL5': {'scientific_dependency': 'F17 penalty activation passed'},
         'M2IRRROLLFORCE5': {'scientific_dependency': 'F17 penalty activation passed'},
         'M2RMREG6': {'scientific_dependency': 'none', 'scheduler_concurrency_dependency': 'afterany:<M2IRRROLLCTL5_PBS_ID>'}})
    dump(RUN / 'F19_RESOURCES.json', {'queue': 'entry_imfdfkmq', 'expected_routed_queue': 'normal_imfdfkmq',
         'M2IRRROLLCTL5': {'cpus': 1, 'memory_gb': 8, 'walltime': '01:00:00'},
         'M2IRRROLLFORCE5': {'cpus': 1, 'memory_gb': 8, 'walltime': '01:00:00'},
         'M2RMREG6': {'cpus': 1, 'memory_gb': 8, 'walltime': '00:30:00'}})
    dump(RUN / 'F19_NOTIFICATION_CONTRACT.json', {'telegram': 'mandatory_start_and_terminal', 'pbs_email': 'best_effort', 'redaction_required': True})
    dump(RUN / 'F19_NO_EXECUTION_AUDIT.json', {'qsub_attempts': 0, 'successful_submissions': 0, 'failed_qsub_attempts': 0,
         'PBS_jobs': [], 'solver_executions': 0, 'CAE_executions': 0, 'native_remesh_calls': 0,
         'execution_authorized': False, 'submission_approved': False, 'approved_submissions_now': 0, 'maximum_jobs_now': 0})

if __name__ == '__main__':
    main()
