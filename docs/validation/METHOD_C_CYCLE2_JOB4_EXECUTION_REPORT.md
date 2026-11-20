# Method C Cycle 2: Job-4 Re-Equilibration and Forward Propagation Execution Report (Re-Issue 2)

**Task ID:** `METHOD-C-CYCLE2-JOB4-SOLVE`  
**Scientific Operation:** `method_c_cycle2_remesh_transfer_propagate`  
**Correlation ID:** `HND-METHOD-C-CYCLE2-JOB4-002`  
**PBS Job ID:** `1424702.mmaster02` (predecessor attempt `1424700.mmaster02` preserved in ledger and archive)  
**Solver:** Abaqus/Standard 2023 with Frozen User Element Subroutine `f42_mixed_uel.for` (`CE8D5EDC...`)  
**Hardware & Resources:** 16 CPUs SMP on `mnode100`, 48 GB RAM, queue `normal_imfdfkmq` (via `entry_imfdfkmq`)  
**Execution Timestamp:** 2026-11-20 01:19:47 CET to 2026-11-20 01:22:20 CET  
**Solver Walltime:** 74.0 s | **Solver CPU Time:** 204.0 s (151.0 s user, 52.0 s sys)  
**Termination Status:** `CUTBACK_TERMINATION` (Exit Code 1, `TIME_INCREMENT_LESS_THAN_MINIMUM`)  
**Cumulative PBS Submissions:** 62 (exactly 1 new PBS job consumed against authorization: cumulative 61 -> 62)  

---

## 1. Executive Summary & Resolution of Review Gap GAP-MC-C2J4-01

Following independent structured review `HND-METHOD-C-CYCLE2-JOB4-001`, the supervisory verdict identified that Job-4 attempt 1 (`1424700.mmaster02`) did not perform a true fixed-load re-equilibration because the top reference point displacement ramped from $u_2 \sim 0$ to $0.006525\,\text{mm}$ (due to default ramp amplitude and lack of displacement initial conditions). 

### 1.1 Root-Cause Resolution and Deck Correction
1. **Initial Displacement Mechanism Investigation:**
   - Evaluated `*INITIAL CONDITIONS, TYPE=DISPLACEMENT` in Abaqus/Standard 2023. Confirmed via fatal pre-processor error 144 and Abaqus header `ads_CoreInitialConditionsC.h` that Abaqus/Standard static steps do not support displacement initial condition cards.
   - Formulated and verified the alternative authorized by the review: creating a constant amplitude table `*AMPLITUDE, NAME=CONST_HOLD` (`0.0, 1.0, 1.0, 1.0`) and applying it to Step 1 boundary conditions (`*BOUNDARY, AMPLITUDE=CONST_HOLD`, `N_RP, 2, 2, 0.008756`).
   - Verified on local Abaqus tests and confirmed on the cluster that this forces $u_2 = 0.008756\,\text{mm}$ **immediately at the very first increment (Increment 1)** and holds $u_2$ strictly constant across the entire step duration.

2. **Corrected Production Deck Staged:**
   - Regenerated `PK_METHOD_C_CYCLE2_REFINED_JOB4.inp` (SHA-256 `3A9F32BAEB5D1F4D810F60872897C443558E61569CFB1B58C60DD9FB24F5E688`) with 42,012 layered elements.
   - Uploaded to isolated cluster scratch directory `/scratch9/pr21vyci/runs/mode1_289_method_c_demo_job4_r1` (bypassing stale PanFS lease locks on previous directory).
   - Executed cluster datacheck with Exit 0, confirming `ANALYSIS DATACHECK COMPLETE` with zero errors.

3. **Cluster Execution & Key Findings:**
   - PBS accepted job `1424702.mmaster02` in queue `entry_imfdfkmq` routing to `normal_imfdfkmq`.
   - **True Fixed-Load Hold Demonstrated:** All 6 converged increments executed at strictly constant displacement $u_2 = 0.008756\,\text{mm}$ (verified from `dat_rp_history` and ODB field outputs).
   - **Re-Equilibration Force Continuity Passed ($\le 5\%$ Gate):** In Increment 1 (Frame 1), the initial re-equilibrated reaction force is $RF_2 = 0.249323\,\text{kN}$ vs Job-3 donor end state $0.262226\,\text{kN}$, giving an initial force continuity delta of **$-4.92\%$** (`step1_init_force_continuity_pass = True`).
   - **Spontaneous Forward Crack Growth Across Second Ligament:** Under the fixed displacement hold ($u_2 = 0.008756\,\text{mm}$), the crack tip spontaneously advanced forward from $x_{\text{tip}} = 0.895686\,\text{mm}$ to $x_{\text{tip}} = 0.923302\,\text{mm}$ ($\Delta x = +27.62\,\mu\text{m}$ of forward crack growth through the second ligament, total extension $\Delta a = 0.423302\,\text{mm}$ from initial notch).
   - **Load Relaxation and Softening:** Accompanying crack advance, the reaction force relaxed from $0.249323\,\text{kN}$ down to $0.199318\,\text{kN}$ ($-20.06\%$ softening load drop under fixed displacement).
   - **Zero Artificial Healing:** Phase-field damage across the pre-existing crack wake was preserved strictly at $d_{\max} = 1.002061$ (no healing).
   - **Exact Rupture History Preservation:** The extreme localized history variable from Job 3 was preserved identically at $H_{\max} = 4629.688965\,\text{MPa}$.
   - **Cutback Termination:** At Increment 6, as the remaining ligament of only $\sim 76.7\,\mu\text{m}$ underwent rapid localization and dynamic snap-through, the Newton solver required increments smaller than $dt_{\min} = 1.0 \times 10^{-7}$, resulting in physical cutback termination (`TIME_INCREMENT_LESS_THAN_MINIMUM`).

---

## 2. Quantitative Observables & Multi-Stage Evolution

| Metric / Observable | Job-1 Baseline (Coarse) | Job-2 Re-Equilibration | Job-3 Forward Propagation | Job-4 Attempt 1 (Ramping) | Job-4 Resubmission (Fixed Hold) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **PBS Job ID** | `1424517.mmaster02` | `1424584.mmaster02` | `1424609.mmaster02` | `1424700.mmaster02` | `1424702.mmaster02` |
| **Exit Code / Status** | Exit 0 (`COMPLETED_EXIT0`) | Exit 0 (`COMPLETED_EXIT0`) | Exit 1 (`CUTBACK_TERMINATION`) | Exit 1 (`CUTBACK_TERMINATION`) | Exit 1 (`CUTBACK_TERMINATION`) |
| **Termination Reason** | Normal Completion | Normal Completion | `TIME_INC_LESS_THAN_MIN` | `TIME_INC_LESS_THAN_MIN` | `TIME_INC_LESS_THAN_MIN` |
| **Physical Elements** | 2,920 (96.92% quads) | 10,299 (96.84% quads) | 10,299 (96.84% quads) | 14,004 (96.86% quads) | 14,004 (96.86% quads) |
| **Layered Elements** | 8,760 | 30,897 | 30,897 | 42,012 | 42,012 |
| **Mesh Nodes** | 3,017 | 10,298 | 10,298 | 14,011 | 14,011 |
| **Solver Walltime (s)** | 1,511 s | 41 s | 2,938 s | 394 s | 74.0 s |
| **Solver CPU Time (s)** | 909 s | 175 s | 1,780 s | 473 s | 204.0 s |
| **Step 1 Displacement Mode** | Ramp $0 \to 0.0050\,\text{mm}$ | Hold $0.0050\,\text{mm}$ | Hold $0.0050\,\text{mm}$ | Ramp $0 \to 0.0065\,\text{mm}$ | **Fixed Hold $0.008756\,\text{mm}$** |
| **Step 1 Increments** | 50 | 24 | 24 | 29 | 6 |
| **Automatic Cutbacks** | 0 | 0 | 18 (in S2) | 12 | 8 |
| **Total Equil. Iterations** | ~150 | 66 (mean 2.75/inc) | 713 (mean 4.79/inc) | 142 | 63 (mean 10.5/inc) |
| **Initial Re-Equil. Force** | 0.556024 kN | 0.548386 kN | 0.548386 kN | 0.002493 kN (ramp) | **0.249323 kN** |
| **Initial Force Continuity $\Delta$** | Baseline | **-1.37% (PASS)** | **0.00% (PASS)** | -99.0% (ramp defect) | **-4.92% (PASS $\le 5\%$)** |
| **Final Step 1 Force** | 0.556024 kN | 0.548386 kN | 0.548386 kN | 0.160389 kN | 0.199318 kN (softened) |
| **Peak Damage $d_{\max}$** | 0.169178 (notch tip) | 0.408571 (notch tip) | 1.005501 (severed wake) | 1.002061 (severed wake) | **1.002061 (severed wake)** |
| **Damage Healing?** | None (intact) | None ($0.409 \ge 0.169$) | None ($1.006 \ge 0.409$) | None ($1.002 \ge 1.000$) | **None ($1.002 \ge 1.000$)** |
| **Peak History $H_{\max}$** | 0.249872 MPa | 1.930477 MPa | 4629.688965 MPa | 4629.688965 MPa | **4629.688965 MPa** |
| **Initial Crack Tip $x$** | 0.5000 mm | 0.5000 mm | 0.5000 mm | 0.895686 mm | **0.895686 mm** |
| **Final Crack Tip $x$** | 0.5000 mm | 0.5000 mm | 0.895686 mm (hole captured) | 0.920247 mm | **0.923302 mm** |
| **Forward Crack Advance $\Delta x$**| 0.0 mm | 0.0 mm | +0.395686 mm | +24.56 $\mu$m | **+27.62 $\mu$m** |
| **Total Extension $\Delta a$** | 0.0 mm | 0.0 mm | 0.395686 mm | 0.420247 mm | **0.423302 mm** |
| **Post-Peak Softening?** | N/A | N/A | Yes (-59.58%) | Yes (-4.3%) | **Yes (-20.06% under hold)** |
| **Fracture Energy $E_{\text{frac}}$** | 0.0 kN*mm | ~0.0 kN*mm | 1.592853e-3 kN*mm | 1.632072e-3 kN*mm | **1.685754e-3 kN*mm** |
| **Total Energy $E_{\text{total}}$** | 1.423398e-3 kN*mm | 1.412443e-3 kN*mm | 1.595914e-3 kN*mm | 2.155364e-3 kN*mm | **2.558367e-3 kN*mm** |

---

## 3. Physical Analysis & Review Notes Clarification

### 3.1 Dual Fracture Energy Baselines (`NOTE-MC-C2J4-04`)
As highlighted in supervisory note `NOTE-MC-C2J4-04`, the energy growth baseline must be distinguished between the donor end state and the receiver post-transfer state:
1. **Donor (Job-3 End State) Baseline:** $E_{\text{fracture}}^{\text{Job-3}} = 1.592853 \times 10^{-3}\,\text{kN}\cdot\text{mm}$.
   - Relative to the Job-3 donor, Job-4 final fracture energy grew by **$+5.83\%$** ($\Delta E_{\text{frac}} = +0.0929 \times 10^{-3}\,\text{kN}\cdot\text{mm}$).
2. **Receiver (Post-Transfer Initial) Baseline:** $E_{\text{fracture}}^{\text{Receiver, init}} = 1.562855 \times 10^{-3}\,\text{kN}\cdot\text{mm}$.
   - The slight discretization difference ($-1.88\%$) between Job-3 mesh (10,299 elements) and Job-4 receiver mesh (14,004 elements) reflects the local integration on the finer mesh.
   - Relative to this post-transfer receiver state, fracture energy grew by **$+7.86\%$** ($\Delta E_{\text{frac}} = +0.1229 \times 10^{-3}\,\text{kN}\cdot\text{mm}$).

Both baselines independently confirm positive, monotonic thermodynamic energy dissipation accompanying physical crack advance across the second ligament.

### 3.2 Post-Peak Softening Under Fixed Hold (`NOTE-MC-C2J4-05`)
In this corrected run, `post_peak_softening_demonstrated = True` is unequivocally demonstrated:
- At Increment 1 ($u_2 = 0.008756\,\text{mm}$), the structure supported $F = 0.249323\,\text{kN}$.
- As the crack tip localized and propagated from $x = 0.895686\,\text{mm}$ to $x = 0.923302\,\text{mm}$, the load dropped monotonically:
  * Inc 2: $0.235469\,\text{kN}$
  * Inc 3: $0.222907\,\text{kN}$
  * Inc 4: $0.210962\,\text{kN}$
  * Inc 5–6: $0.199318\,\text{kN}$
- This represents a substantial **$-20.06\%$ structural load relaxation** strictly under fixed kinematic displacement, characteristic of unstable crack propagation through a narrow remaining ligament.

### 3.3 Cause of Termination & Step 2 Status (`GAP-MC-C2J4-02`)
Step 2 was not reached because the specimen underwent dynamic crack propagation and localization failure during Step 1's fixed-load hold. Because the initial state transferred from Job 3 was already at the point of ligament severance ($d > 0.95$ past the hole), holding $u_2 = 0.008756\,\text{mm}$ constant provided sufficient elastic strain energy to drive the crack further into the remaining ligament. At $x_{\text{tip}} = 0.9233\,\text{mm}$, the intact ligament length was reduced to only $76.7\,\mu\text{m}$, where quasi-static equilibrium cannot be maintained without dynamic inertia or artificial viscosity. The solve exited cleanly via Exit 1 cutback termination after capturing $+27.62\,\mu\text{m}$ of autonomous crack growth.

---

## 4. Cryptographic Provenance & Artifact Hashes

All deliverables, inputs, subroutines, scripts, and logs are cryptographically tracked via SHA-256:

| Artifact Description | Repository Path | SHA-256 Digest |
| :--- | :--- | :--- |
| **Receiver Physical Mesh** | `models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_PHYS.inp` | `3B011D47869A31D4CEC4C941342248C915A2C31181A8DC20C022EC4D8F7022FC` |
| **Corrected Production Deck** | `models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_REFINED_JOB4.inp` | `3A9F32BAEB5D1F4D810F60872897C443558E61569CFB1B58C60DD9FB24F5E688` |
| **Frozen UEL Subroutine** | `models/pandey_kumar_mode1/289_method_c_demo_case/f42_mixed_uel.for` | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` |
| **PBS Submission Script** | `models/pandey_kumar_mode1/289_method_c_demo_case/submit_demo_cycle2_job4.pbs` | `F891FB5689F7243537F234427CA5C3223984563D884C02ACA6326415C346E7D5` |
| **Job-4 Authorization Manifest**| `models/pandey_kumar_mode1/289_method_c_demo_case/METHOD_C_DEMO_JOB4_AUTHORIZATION.json` | `0E543A25611F81E9776E1855E77CEC4A0B27094B8E1621CB24232222A5D56758` |
| **Job-4 Completion Receipt** | `models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_REFINED_JOB4_RECEIPT.json` | `1D6A70A4C94AC2883B5DFD605201DB1CD1CAA1FFA287EF0B4851F919884146B6` |
| **Job-4 Observables Summary** | `models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_REFINED_JOB4_SUMMARY.json` | `CC0C44F809061A89041F5FF0733671E8BABB3F5A7B29A60F165B345CC3C6C36A` |
| **Observable Extractor Script** | `models/pandey_kumar_mode1/289_method_c_demo_case/extract_job4_observables.py` | `BE8127C123F9C4B894626C65B53938ADC72AF90C20B2B9732C70BB0E57770F79` |
| **Unit Test Suite** | `tests/unit/test_method_c_cycle2_job4_execution.py` | `B036A41819FEE49633A675DEBF6337503B26E131EACA16631CF23D6D65183622` |

---

## 5. Verification Status & Conclusion

1. **Fixed-Load Re-Equilibration:** Demonstrated successfully at $u_2 = 0.008756\,\text{mm}$. Increment 1 reaction force $RF_2 = 0.249323\,\text{kN}$ matches donor end force $0.262226\,\text{kN}$ within $-4.92\%$, satisfying the $\le 5\%$ continuity gate (`step1_init_force_continuity_pass = True`).
2. **Forward Crack Growth:** Autonomous crack tip advance $+27.62\,\mu\text{m}$ ($x = 0.895686 \to 0.923302\,\text{mm}$) across the second ligament toward the right boundary.
3. **Irreversibility & Non-Negativity:** Phase-field damage strictly preserved at $d_{\max} = 1.002061$ (zero healing); extreme history preserved identically at $H_{\max} = 4629.688965\,\text{MPa}$.
4. **PBS Accounting:** Exactly 1 new PBS job consumed against authorization (`1424702.mmaster02`), cumulative 62.
5. **Master Goal Status:** `MASTER_GOAL_STATUS = OPEN`.
