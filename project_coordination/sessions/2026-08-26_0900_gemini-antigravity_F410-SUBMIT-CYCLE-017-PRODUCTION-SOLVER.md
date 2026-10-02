# Session Report: 2026-08-26_0900_gemini-antigravity_F410-SUBMIT-CYCLE-017-PRODUCTION-SOLVER.md

Agent: gemini-antigravity
Task: F410-SUBMIT-CYCLE-017-PRODUCTION-SOLVER
Target Package: models/generated/adaptive_online/real_pilot_cycle_017/
Submission Script: submit_m2adapt_real_pilot_cycle_017_restart.sh
Lineage: 1397992.mmaster02 (Cycle-016 Frame 58 donor) -> 1397995.mmaster02 (Cycle-017 datacheck PASS) -> 1397996.mmaster02 (Cycle-017 production restart RUNNING)

## 1. Preflight Verification & Governance
- **Fail-Closed Cryptographic Hash Verification:**
  - `M2ADAPT_REAL_PILOT_CYCLE_017_RESTART.inp`: `5b5e765d132ed8c20899c140e09843cacf9ea3fce83576ab32b5c63cd7e3c3e9`
  - `f44_mixed_uel_restart_stateinit.for`: `942003c5882b5598e81b471d87840e0dce2a639179cc24c87662dcf53eaef946`
  - `M2ADAPT_REAL_PILOT_CYCLE_017_RESTART.pbs`: `60fd156c363ae74b05f9e761dec1df4051e941b3983f14e85a4ab32bef682919`
  - `submit_m2adapt_real_pilot_cycle_017_restart.sh`: `018e1c3c17ca78f7f8d4e099197f183891393491ac3c850fa9597d6108de03df`
  - `STAGE_D_COMMITTED_STATE.bin`: `6a1e3657a43b73ca00be2a245441a36bde8458a16ae58209c16aa171d7a9eaff`
- **Predecessor Datacheck Qualification:**
  - Datacheck predecessor `1397995.mmaster02` confirmed `SCIENTIFIC_DATACHECK_PASS` with `Exit_status = 0` on `mnode100/0`.
- **Notification Directives:**
  - PBS email directives `#PBS -m abe` and `#PBS -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de` active.
  - Telegram notification helper hooks (`notify_submitted`, `notify_start`, `notify_completed`) active.

## 2. Production Solver Submission & Scheduler State
- **PBS Job ID:** `1397996.mmaster02`
- **Job Name:** `M2ADAPT_REAL_PIL`
- **Execution Host:** `mnode100/0` (`mnode100[0]:ncpus=1:mem=16777216kb`)
- **Queue / Routing:** `entry_imfdfkmq` -> `normal_imfdfkmq`
- **Allocated Resources:** `select=1:ncpus=1:mem=16gb`, `walltime=01:00:00`
- **Fresh Scheduler State:** `RUNNING` (`job_state = R`)
- **Continuation Segment:** $U_1 = 0.05051289\text{ mm} \to 0.05301289\text{ mm}$ ($\Delta U_1 = 0.0025\text{ mm}$).
- **Controls Applied:**
  - Step 3: $R_n = 0.01$, $C_n^u = 10.0$ for displacement and temperature, time incrementation `25, 25, 25, 25, 25, 4, 50, 25`, $dt_{\min} = 1.0\times 10^{-14}$.
  - Step 4: $R_n = 0.05$, $C_n^u = 10.0$ for displacement and temperature, time incrementation `25, 25, 25, 25, 25, 4, 50, 25`, $dt_{\min} = 1.0\times 10^{-14}$.

## 3. Governance Invariants
- Exactly **1** datacheck job (`1397995.mmaster02`) and exactly **1** production restart solver job (`1397996.mmaster02`) submitted.
- Package not modified after datacheck pass.
- Non-polling supervision protocol enforced.
