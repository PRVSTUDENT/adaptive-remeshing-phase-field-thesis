# Scientific Research Report — Task F1629 Overnight Execution Evaluation & R12 Driver API Remediation

## 1. Current Task & Governance State
- **Current Task ID**: `F1629-METHOD-C-C6-R12-OVERNIGHT-CONTROLLED-PAIR`
- **Task Status**: `COMPLETED` (`EVALUATED_DRIVER_API_REGRESSION_REPAIRED`, `remaining_pbs_submissions = 0`)
- **Prepared Successor Candidate**: `F1630-METHOD-C-C6-R12-REPAIRED-DRIVER-PAIRED-EXECUTION` (`status = prepared_pending_independent_review`, `remaining_pbs_submissions = 0` pending independent review approval)
- **Frozen Production UEL (`f42_mixed_uel.for`) SHA-256**: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (29,722 bytes, strictly unchanged)

## 2. Actual PBS Status & Authentic Scheduler Evidence
Live scheduler (`qstat -u pr21vyci`) and terminal accounting (`qstat -xf 1420391.mmaster02 1420392.mmaster02`) were queried via `Invoke-GuardedSsh.ps1`:
- **Active/Queued User Jobs on Cluster**: `0` running, `0` queued.
- **Arm A — Picard Baseline (`M1_C6_R12_PICARD_BASELINE`, Package 174)**:
  - **PBS Job ID**: `1420391.mmaster02`
  - **Execution Node / Queue**: `mnode097` / `normal_imfdfkmq`
  - **Terminal State**: `job_state = F`, `Exit_status = 1`, `resources_used.walltime = 00:00:03`, `resources_used.cput = 00:00:02`
  - **Completed Coupled Outer Iterations**: `0` (terminated prior to outer iteration 1)
  - **Archived Authentic Evidence**:
    - `models/pandey_kumar_mode1/174_c6_r12_picard_baseline/evidence/1420391.mmaster02/pbs_execution.log` (SHA-256: `3719627B40F8EC5C3377A2FBACEA3AA507885DD89340E62FC01626F4E3A046E0`)
    - `models/pandey_kumar_mode1/174_c6_r12_picard_baseline/evidence/1420391.mmaster02/qstat_xf.txt` (SHA-256: `F508523DEF133B923BC6C92E3EDFED99D05C94FAEEA339367F8BF8381602E07C`)
- **Arm B — Safeguarded Anderson M2 (`M1_C6_R12_ANDERSON_M2`, Package 175)**:
  - **PBS Job ID**: `1420392.mmaster02`
  - **Execution Node / Queue**: `mnode097` / `normal_imfdfkmq`
  - **Terminal State**: `job_state = F`, `Exit_status = 1`, `resources_used.walltime = 00:00:03`, `resources_used.cput = 00:00:02`
  - **Completed Coupled Outer Iterations**: `0` (terminated prior to outer iteration 1)
  - **Archived Authentic Evidence**:
    - `models/pandey_kumar_mode1/175_c6_r12_anderson_m2/evidence/1420392.mmaster02/pbs_execution.log` (SHA-256: `B4AD60B05B805CF5B75BFE730A1F7729F21B07FCE7C6E8BD917645C966765B16`)
    - `models/pandey_kumar_mode1/175_c6_r12_anderson_m2/evidence/1420392.mmaster02/qstat_xf.txt` (SHA-256: `91ADBB649FCC8772F7BB955073C169CC5821FF8FB002A38A596D665E11E715F1`)

## 3. Forensic Root-Cause Diagnosis & Numerical Findings
Neither job reached outer iteration 1; therefore, no Abaqus subproblem solves were executed and no C6 checkpoint was produced. Inspection of `pbs_execution.log` and line-by-line comparison of `scripts/state_transfer/driver_package171_r12_c6_coupled_pdas.py` (`282690AB...`) against the verified R11 driver `scripts/state_transfer/driver_package171_r11_c6_coupled_pdas.py` isolated a **4-point technical API regression** in `solve_coupled_equilibration()` introduced when R12 was constructed:
1. **Defect 1 — `PDASReEquilibrationSolver.__init__` Keyword Mismatch (Immediate Crash Cause)**:
   - At line 778, `driver_package171_r12_c6_coupled_pdas.py` called `PDASReEquilibrationSolver(mesh=self.mesh, history=history, d_init=dict(self.damage), d_lower_bounds=dict(self.d_lower_bounds), penalty_active=1e9, penalty_free=0.0)`.
   - `PDASReEquilibrationSolver.__init__` in `scripts/state_transfer/pdas_reequilibration_solver.py` has signature `(self, mesh, history, d_init, d_lower_bounds, c_pdas=1.0e3, max_iters=50)`, causing immediate `TypeError: PDASReEquilibrationSolver.__init__() got an unexpected keyword argument 'penalty_active'` at startup.
2. **Defect 2 — Staggered Subproblem Ordering & `PDASReEquilibrationSolver` Attribute/Method Mismatch**:
   - Inside the outer loop, the unverified R12 rewrite inverted the staggered subproblem order (running Phase before Mechanical) and called `solver.h = history` (instead of `solver.h_gp = history`) and nonexistent `solver.solve(...)` (instead of `solver._update_active_set(self.damage)` + `self.solve_subproblem(...)` + `solver.check_kkt_residuals(d_abaqus, active_set)`).
3. **Defect 3 — `AndersonAccelerator` Method Name Mismatch**:
   - At line 811, the R12 rewrite called nonexistent `self.accelerator.step(...)` instead of `self.accelerator.compute_step(d_k=d_prev, g_d_k=d_kkt, active_set=active_set)`.
4. **Defect 4 — Raw Displacement Residual Reference**:
   - Computed `delta_u_raw` against `previous_u_abaqus` instead of `previous_u_trial` (the actual displacement state entering the mechanical subproblem).

Why the previous qualification tests missed this: `tests/unit/test_package171_r12_qualification.py` previously mocked `PDASReEquilibrationSolver` and `AndersonAccelerator` or tested `load()`, `_deck()`, and `finalize_coupled_acceptance()` in isolation without executing `solve_coupled_equilibration()` against the real `PDASReEquilibrationSolver` and `AndersonAccelerator` classes.

## 4. Deterministic Remediation & Qualification Evidence
In accordance with the Immediate-Failure Recovery Policy, all four technical regressions in `scripts/state_transfer/driver_package171_r12_c6_coupled_pdas.py` were repaired and verified locally and on cluster scratch without consuming any PBS submissions:
- **Repaired Driver**: `scripts/state_transfer/driver_package171_r12_c6_coupled_pdas.py`
  - **New SHA-256**: `17C064184A569019E7A2BC72B7880C7F3404B0A9E92C37B2D04F4BE3BAAC7166` (67,304 bytes)
  - Restores the exact R11 `solve_coupled_equilibration()` implementation (`c_pdas = 1.0e3`, `solver.h_gp = history`, proper Mechanical -> Phase staggered subproblem sequence, `self.accelerator.compute_step(d_k=d_prev, g_d_k=d_kkt, active_set=active_set)`, `if self.previous_active_set is not None:`, `delta_u_raw` against `previous_u_trial`, and Stage 2 rollback logic) while preserving all R12 hardening (`*Node Print, frequency=1\nU\n` in `_deck()`, fail-closed `finalize_coupled_acceptance()` with `rf2_kN`/`total_energy_kNmm` keys, and raw healing telemetry before irreversibility projection).
- **Expanded Unit & Qualification Test Suites (38/38 Passed)**:
  - `tests/unit/test_package171_r12_qualification.py` (SHA-256: `4DB389557919587AED81DEF8D26E7D6CEB9DC2EBCEB8EA7CD071286D9B165516`, 19,894 bytes) expanded to **10 tests (`10/10 PASS` in 7.45s)**:
    - `test_09_production_path_solve_coupled_equilibration_picard_and_anderson`: executes `solve_coupled_equilibration()` across 4 outer iterations for both Arm A (`anderson_enabled=False`) and Arm B (`anderson_enabled=True`) using the **real, un-mocked** `PDASReEquilibrationSolver` and `AndersonAccelerator` classes (mocking only the external Abaqus subprocess call `solve_subproblem`), and proves **exact numerical parity** with `Package171R11CoupledPDASDriver`.
    - `test_10_real_package_load_and_unmocked_solver_execution`: loads the real 15,252-element, 15,559-node, 61,008-GP C6 package (`171_c6_package171_r12_c3_0_adaptive_reequilibration`) and executes 2 outer iterations of `solve_coupled_equilibration()` with un-mocked `PDASReEquilibrationSolver` and `AndersonAccelerator`.
  - `tests/unit/test_package171_r11_c6_coupled_driver.py`: **`21/21 PASS` in 2.63s**.
  - `tests/unit/test_f1629_paired_controlled_execution.py` (SHA-256: `9E82518676C82A7A79BEBAE639C952850827FC63A87960C50396518D2B31936A`, 6,861 bytes): **`7/7 PASS` in 2.61s**.
- **Updated Package Manifests & Evaluation Artifacts**:
  - `models/pandey_kumar_mode1/174_c6_r12_picard_baseline/PACKAGE_MANIFEST.json`: SHA-256 `54A5BC86CD0470C7263094CCB288378F33824FD713C15EF7456D45955AAB5C58` (3,928 bytes)
  - `models/pandey_kumar_mode1/175_c6_r12_anderson_m2/PACKAGE_MANIFEST.json`: SHA-256 `7E600AB59FBEBC9F1647FE95B329A3B207262FBCD71874B8F46F900EEF4D6FB7` (3,912 bytes)
  - `results/validation/f1629_paired_execution_summary.json`: SHA-256 `7B573A9FAA3FB9FD3DAC5BD90D94D250A3A759B35A345E584FD2B34C13B44E99` (4,483 bytes)
  - `results/validation/f1629_paired_execution_report.md`: SHA-256 `279124E75D691554DDB8DD7334C3516E1ED6635A0BA02D3F2A55150A511C08AC` (4,602 bytes)
- **Remote Cluster Scratch Re-Staging & Un-Mocked Smoke Verification**:
  - Re-staged Packages 174 & 175 and runtime tarball to `/scratch9/pr21vyci/runs/mode1_c6_r12_picard_baseline` and `/scratch9/pr21vyci/runs/mode1_c6_r12_anderson_m2` via `scripts/validation/stage_f1629_packages.py` (preserving prior `pbs_execution_1420391.mmaster02.log` and `pbs_execution_1420392.mmaster02.log`).
  - Verified remote SHA-256 of `runtime/scripts/state_transfer/driver_package171_r12_c6_coupled_pdas.py` on both scratch directories matches `17C064184A569019E7A2BC72B7880C7F3404B0A9E92C37B2D04F4BE3BAAC7166`.
  - Both remote PBS `bash -n` checks and upgraded remote `smoke_import.py` checks (which execute a 2-iteration un-mocked `PDASReEquilibrationSolver` + `AndersonAccelerator` run via `solve_coupled_equilibration()`) passed with Exit 0.
  - Note: All Abaqus input decks (`*.inp`), boundary includes (`*.inc`), initial field CSVs (`*.csv`), and frozen UEL (`f42_mixed_uel.for`) are 100% unchanged from the 4/4 Exit-0 Abaqus 2023 datachecks recorded in `results/validation/package171_r12_datacheck_receipt.json` (`9102E900...`).

## 5. Unresolved Scientific Question
Because Jobs `1420391.mmaster02` and `1420392.mmaster02` terminated at outer iteration 0 due to the Python driver API regression before invoking Abaqus, the core scientific question of `F1629`—whether gradient-preserving isoparametric bilinear GP history transfer combined with damped Picard (Arm A) or safeguarded Anderson M2 acceleration (Arm B) achieves coupled re-equilibration ($\Delta d \le 10^{-5}$, $\Delta u \le 10^{-9}\text{ mm}$, $\Delta H \le 10^{-4}\text{ MPa}$, KKT $\le 10^{-6}$, force/energy drift $\le 2\%$) on the 15,252-element C6 adaptive receiver mesh—remains untested on the solver.

## 6. Single Proposed Next Action
Approve and activate successor task **`F1630-METHOD-C-C6-R12-REPAIRED-DRIVER-PAIRED-EXECUTION`** (`project_coordination/task_definitions/F1630-METHOD-C-C6-R12-REPAIRED-DRIVER-PAIRED-EXECUTION.json`, SHA-256: `195DF3FB2ED5B5E7BC80447C352820C47C209DAA349BC40E77108F693450924E`) authorizing **two once-only serial production PBS submissions** (`max_new_pbs_submissions = 2`, 1 CPU, 16 GB RAM, 08:00:00 walltime, max 140 outer iterations each) using the repaired and unmocked-solver-qualified driver (`17C064184A569019E7A2BC72B7880C7F3404B0A9E92C37B2D04F4BE3BAAC7166`):
1. **Job A (`M1_C6_R12_PICARD_BASELINE`, Package 174)**: C6 R12 isoparametric GP transfer re-equilibration with Anderson acceleration DISABLED (`anderson_enabled = False`).
2. **Job B (`M1_C6_R12_ANDERSON_M2`, Package 175)**: C6 R12 isoparametric GP transfer re-equilibration with safeguarded Anderson acceleration ENABLED ($m=2, \beta=0.85, \text{reg}=10^{-6}, \gamma_{\max}=200, \text{step\_cap}=0.045$).
