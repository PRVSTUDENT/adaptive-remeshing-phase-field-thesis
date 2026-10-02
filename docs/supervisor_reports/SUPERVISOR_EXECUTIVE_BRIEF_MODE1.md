# Mode-I Phase-Field Fracture Benchmark: Supervisor Executive Brief

**Document Identifier**: `docs/supervisor_reports/SUPERVISOR_EXECUTIVE_BRIEF_MODE1.md`  
**Date**: September 10, 2026  
**Author**: Pruthviraja Reddy Vandavagali (Matriculation No. 68865)  
**Supervisors**: Prof. Dipl.-Ing. Björn Kiefer, Ph.D., and Dr.-Ing. Stephan Roth  
**Institution**: Institute of Mechanics and Fluid Dynamics (IMFD), TU Bergakademie Freiberg  
**Governing Directive**: *"We need to have understood everything related to the first model before we increase complexity."*  
**Authoritative Verdict**: `GATE6_REFERENCE_REPRODUCTION_PARTIALLY_QUALIFIED`  

---

## 1. Benchmark Boundary Value Problem
- **Domain & Boundary Conditions**: 2D square plate $\Omega = [0, 1]\times[0, 1]\,\text{mm}$ with a sharp horizontal slit seam $a_0 = 0.500\,\text{mm}$ along $y = 0.500\,\text{mm}$. Bottom edge roller supported ($u_y = 0$) with origin pinned ($u_x=0, u_y=0$); top edge pulled monotonically in tensile displacement ($u_y = \bar{u}$).
- **Constitutive Constants**: $E = 210.0\,\text{GPa}$ ($210\,\text{kN/mm}^2$), $\nu = 0.30$, $G_c = 2.70\times 10^{-3}\,\text{kN/mm}$ ($2.7\,\text{kJ/m}^2$), $\ell_0 = 0.0075\,\text{mm}$ ($7.5\,\mu\text{m}$).

---

## 2. Quantitative Reference Anchor vs Adaptive Performance Summary

| Case Description | PBS Job ID | FE Count | Canonical $K_0$ ($\text{kN/mm}$) | $\Delta K_0$ (%) | Peak Load $F_{\max}$ ($\text{kN}$) | $\Delta F_{\max}$ (%) | Peak Displ $u(F_{\max})$ ($\text{mm}$) | Pre-Peak $\epsilon_{L_2}$ (%) | Full-Curve $\epsilon_{L_2}$ (%) | External Work $W_{\text{ext}}$ | Serial Walltime | Authoritative Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Fixed Ref Anchor** | `1398090` | $15,192$ | $137.9455$ | **Anchor** | $0.757778$ | **Anchor** | $0.005857$ | **Anchor** | **Anchor** | $2.3584\,\text{mJ}$ | $06\text{h }31\text{m}$ | **`SCIENTIFIC_ANCHOR`** |
| **Harmonized Ref** | `1401091` | $15,192$ | $134.3241$ | $-2.63\%$ | $0.764998$ | $+0.95\%$ | $0.006072$ | $2.37\%$ | $28.76\%$ | $2.4625\,\text{mJ}$ | $06\text{h }32\text{m}$ | **`QUALIFIED_ROLLER_REF`** |
| **Nominal 1% Adaptive** | `1399632` | $71,320$ | $122.3785$ | **$-11.28\%$** | $0.478203$ | **$-36.89\%$** | $0.004150$ | **$12.14\%$** | **$34.55\%$** | $2.0069\,\text{mJ}$ | $35\text{h }08\text{m}$ | **`NOMINAL1PCT_71320_REFERENCE_REPRODUCTION_FAILED`** |
| **Empirical 2% Adaptive**| `1400395` | $15,396$ | $137.8437$ | **$-0.07\%$** | $0.748197$ | **$-1.26\%$** | $0.005775$ | **$0.095\%$** | **$53.32\%$** | $2.9465\,\text{mJ}$ | $07\text{h }51\text{m}$ | **`EMPIRICAL_2PCT_PARTIAL_RESPONSE_AGREEMENT_ONLY`** |
| **Empirical 5% Adaptive**| `1400396` | $4,194$ | $137.9662$ | $+0.01\%$ | $0.764964$ | $+0.95\%$ | $0.007060$ | **$0.021\%$** | **$69.05\%$** | $3.1544\,\text{mJ}$ | $02\text{h }16\text{m}$ | **`COARSE_DELAYED_PEAK`** |

---

## 3. Key Scientific Findings & Diagnostic Truths

1. **Fixed Reference Baseline Qualified**:
   - Reconstructs published literature metrics to within $-0.029\%$ peak force and $-0.051\%$ peak displacement with $K_0 = 137.945520\,\text{kN/mm}$ and $W_{\text{ext}} = 2.3584\,\text{mJ}$ ($2,358.39\,\mu\text{J}$).
2. **Nominal 1% Method Fails Reproduction**:
   - Literal execution of published `errorTarget=1.0` produces $71,320$ finite elements and prematurely fails under severe load under-prediction ($-36.89\%$ peak drop) and compliance softening ($-11.28\%$ initial stiffness drop).
3. **Empirical 2% Branch Achieves Partial Agreement**:
   - Matches initial stiffness within $-0.07\%$ ($137.8437\,\text{kN/mm}$), peak load within $-1.26\%$ ($0.748197\,\text{kN}$), peak displacement within $-1.40\%$ ($0.005775\,\text{mm}$), and pre-peak trajectory with **$0.095\%$ relative $L_2$ error** ($0.33\,\text{N}$ mean absolute force error, accumulating only $0.0003\%$ of squared-error numerator).
   - Sustains a $0.50–0.60\,\text{kN}$ softening plateau across $\Delta u \approx 0.0010\,\text{mm}$ post-peak, explaining why essentially all error is accumulated post-peak ($\eta_{\text{post}} = 99.9997\%$).
4. **Physical Understanding of \texttt{MISESERI} Established**:
   - \texttt{MISESERI} is strictly a recovered von Mises stress discretization error indicator on the linear-elastic continuum pre-analysis, **not** phase-field or damage error.
5. **2D Crack Path & Phase-Field Localization Verified**:
   - Transverse ridge search independently locates $y_{\text{ridge}} = 0.500000\,\text{mm}$ along the ligament with $\Delta y_{\max} = 0.000\,\text{mm}$ within spatial mesh resolution ($3.33\,\mu\text{m}$), classified as `CRACK_PATH_2D_RIDGE_CONSISTENCY_VERIFIED_WITHIN_SAMPLING_RESOLUTION`.
6. **Frozen-Intact Linear Diagnostics Isolated**:
   - $2\times 2$ factorial proves the linear compliance shift ($\Delta K_{\text{int}} = -15.421423\,\text{kN/mm}$) requires both `UNSYMM=ON` and the multi-layer companion mesh **strictly within the tested frozen-intact 71,320-element context**. The uniform fixed mesh is a counterexample.

---

## 4. Open Scientific Questions & Defensible Boundaries

1. **71,320 vs 13,941 Element Count Discrepancy**: Why the literal setting `errorTarget=1.0` produces $71,320$ finite elements in Abaqus CAE while the paper reported $\approx 13,941$ remains unresolved due to undocumented internal sizing details in the publication (`GATE5_UNRESOLVED_DUE_TO_INSUFFICIENT_PUBLISHED_REMESHING_DETAILS`).
2. **Internal Solver Compliance Shift Mechanism**: The exact equation-solver graph modification in Abaqus' unsymmetric direct sparse solver that causes stiffness loss on graded adaptive companion meshes while leaving uniform structured meshes unaffected remains unisolated (`INTERNAL_MECHANISM_NOT_YET_ESTABLISHED`).

---

## 5. Supervisor Recommendation & Next Gate Action
- Mode-I Gates 0–6 evidence is completely audited, mathematically reconciled, and packaged in a lightweight self-contained format ($47.90\,\text{MB}$, NO multi-GB ODB transfers required).
- In accordance with the supervisor directive, **Mode-II (Gate 8) and multi-step state transfer remain strictly ON HOLD** until the Mode-I evidence is formally reviewed and closed.
