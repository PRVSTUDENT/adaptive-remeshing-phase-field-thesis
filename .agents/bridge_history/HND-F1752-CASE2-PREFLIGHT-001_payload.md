# Review Payload: Task F1752 Case 2 Method A Controlled Continuation Execution Preflight & Datacheck

- **Correlation ID:** `HND-F1752-CASE2-PREFLIGHT-001`
- **Predecessor Review:** `HND-F1751-CASE2-READINESS-001` (Decision: `APPROVE` with qualifications)
- **Task ID:** `F1752-CASE2-CONTROL-ONLY-CONTINUATION-EXECUTION-PREFLIGHT`
- **Assigned Agent:** `gemini-antigravity`
- **Cumulative PBS Submissions Consumed:** Exactly 25 (0 consumed under F1752)
- **Requested Execution Allowance:** Exactly 1 bounded PBS job for continuation rerun

---

## 1. Fulfillment of Predecessor Directives (HND-F1751-CASE2-READINESS-001)

| Directive ID | Requirement | Preflight Implementation & Provenance Basis |
| :--- | :--- | :--- |
| **F1751-D01** | Bounded zero-PBS execution-readiness preparation | Completed with exactly 0 PBS jobs consumed. Preflight and cluster datacheck executed offline. |
| **F1751-D02** | Investigate restart feasibility vs. full rerun | Evaluated Job 1423271 `.res`, `.stt`, `.mdl`. Discovered frozen UEL line 132 `COMMON /CB_STATE_TRANS/` initialization is restricted to `KSTEP==1 && KINC<=1`. Restart at Step 2 leaves state arrays zeroed in memory (history loss defect). Full rerun on unchanged 23,965-element mesh selected as sole valid continuation route. |
| **F1751-D03** | Isolated solver-parameter relaxation | Deck `PK_F1752_CASE_2_CONTINUATION.inp` differs from baseline `PK_F1728_CASE_2_PROD.inp` by strictly 1 line (line 96209: `min_increment` relaxed from `1.0e-8` to `1.0e-11`). Initial $\Delta t = 0.002$, max $\Delta t = 0.002$, boundary conditions, material constants, geometry, and mesh are 100% bitwise preserved. |
| **F1751-D04** | Cluster compilation & datacheck receipt | Executed Abaqus 2023 datacheck with frozen UEL `f42_mixed_uel.for` (`CE8D5EDC...`) on cluster. Completed with **Exit Code 0**, 0 errors, and 8 standard benign element notices. |
| **F1751-D05** | Predeclared quantitative stop conditions | Four conditions: >50 cutbacks, $\Delta u_y < 1.0\times 10^{-7}\,\text{mm}$ across 10 increments, walltime > 10,800s, nonphysical damage $d < -1.0\times 10^{-5}$ or $d > 1.02$. |
| **F1751-D06** | Predeclared physical acceptance gates | Five gates: thermodynamic monotonicity ($E_{\text{frac}}$), damage bounds ($0 \le d \le 1.0004$), secondary crack extension ($d \ge 0.90$ past $x = 0.9031$), load drop $\ge 75\%$, and formal secondary front resolution classification (`PARTIAL` vs `FULL` vs `SPATIALLY_QUALIFIED`). |
| **F1751-D07** | Empirical resource allocation basis | Based on Job 1423271 (252 increments in 2,472s wallclock on 1 CPU, peak memory $< 2\,\text{GB}$), full rerun through Step 2 completion estimated at 3,600–5,400s. Requested 1 node, 1 CPU, 8 GB RAM, walltime 10,800s (3 hours) in queue `normal_imfdfkmq`. |

---

## 2. Review Request & Actionable Decision Boundary

The independent reviewer is requested to:
1. Verify that Task F1752 has satisfied all technical preflight requirements without consuming PBS jobs.
2. Formally approve Task F1752 preflight closeout as `CASE2_CONTINUATION_PREFLIGHT_COMPLETE_DATACHECK_EXIT0`.
3. Authorize exactly **1 bounded PBS submission** for the controlled continuation execution of `PK_F1752_CASE_2_CONTINUATION.inp` with frozen UEL `f42_mixed_uel.for` under the predeclared stop conditions and physical acceptance gates.
