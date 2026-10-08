# Mode-II Native Adaptive Remeshing Frame Selection and Target Hierarchy Decision

**Date**: `2026-10-08`  
**Status**: `APPROVED / ACTIVE (AUDITED & SCIENTIFICALLY RECONCILED)`  
**Governing Gate**: `Gate M2-3 (Native Adaptive Remeshing Reproduction & Forensic Audit)` / `Gate M2-4 (Mode-II Adapted Fracture Simulation)`  
**Author**: Gemini Antigravity  
**Literature Reference**: Pandey, V., & Kumar, S. (2025). *Computer Modeling in Engineering & Sciences*, 144(3), 3255–3283. DOI: [10.32604/cmes.2025.067858](https://doi.org/10.32604/cmes.2025.067858).

---

## 1. Context & Scientific Audit

In Gate M2-2 and Gate M2-3, the Mode-II coarse pre-analysis (`Job-1_UEL_paper_horizon.odb`, $2{,}960$ physical elements, $3{,}042$ nodes) was executed over the full 2-step loading schedule ($u_x = 0 \to 10\,\mu\text{m}$ in Step-1; $u_x = 10 \to 20\,\mu\text{m}$ in Step-2).

A forensic audit (Tasks F1335–F1342) rigorously investigated:
1. The mathematical and spatial differences between targeting Step-1 ($u_x = 10.0\,\mu\text{m}$) vs Step-2 ($u_x = 20.0\,\mu\text{m}$).
2. The effect of tightening the error tolerance from $\text{errorTarget} = 2.0\%$ to $1.0\%$.
3. The authoritative Mode-II phase-field length scale ($l_0 = 15.0\,\mu\text{m} = 0.015\,\text{mm}$ in Section 4.2 Page 3267 vs $l_0 = 7.5\,\mu\text{m}$ in Mode-I Section 4.1).

### Key Empirical & Forensic Findings:

1. **Mathematical Scale-Invariance (`VERIFIED`)**:
   Because the pre-analysis is strictly linear elastic ($d \equiv 0$), both stresses $\mathbf{\sigma}$ and the stress-recovery error indicator $\text{MISESERI}$ scale linearly with prescribed displacement $u_x$:
   $$\text{MISESERI}(\mathbf{x}, 20\,\mu\text{m}) = 2 \times \text{MISESERI}(\mathbf{x}, 10\,\mu\text{m})$$
   $$\text{MISESAVG}(20\,\mu\text{m}) = 2 \times \text{MISESAVG}(10\,\mu\text{m})$$
   Consequently, the relative error indicator is **100% bit-for-bit scale-invariant**:
   $$\eta_e = \frac{\text{MISESERI}_e}{\text{MISESAVG}} \equiv \text{constant across all increments}$$

2. **Topological Equivalence at 2% (`VERIFIED`)**:
   Native Abaqus CAE `adaptiveRemesh` produces $22{,}530$ elements ($22{,}642$ nodes) from Step-1 and $22{,}405$ elements ($22{,}512$ nodes) from Step-2 at $\text{errorTarget} = 2.0\%$. The difference is only $-125$ elements ($-0.55\%$). Quantitative area-weighted corridor analysis proves:
   - Area with $h \le l_0/2 = 7.5\,\mu\text{m}$ along the propagation corridor is $40.55\%$ (Step-1) vs $39.72\%$ (Step-2).
   - Area-weighted mean element size across the domain is $8.96\,\mu\text{m}$ (Step-1) vs $8.99\,\mu\text{m}$ (Step-2).
   - Therefore, selecting Step-2 does **NOT** materially alter the spatial refinement corridor compared to Step-1.

3. **Step-2 Superiority Status (`NOT YET PROVEN`)**:
   The hypothesis that Step-2 pre-analysis yields superior fracture fidelity over Step-1 is **NOT YET SCIENTIFICALLY PROVEN**. While Step-2 represents the full pre-analysis loading horizon ($u_x = 20.0\,\mu\text{m}$), the scale-invariance of the linear-elastic error field means both frames yield practically identical initial adapted discretizations. Any claim of fracture superiority remains a working hypothesis subject to empirical validation in Gate M2-4/M2-5.

4. **Error Target 1.0% vs 2.0% Effect (`VERIFIED`)**:
   Tightening $\text{errorTarget}$ to $1.0\%$ produces $80{,}474$ elements ($80{,}136$ nodes, $+259\%$ increase). Quantitative area-weighted analysis reveals:
   - **Near-Global Overrefinement**: $93.09\%$ of the entire $1.0\,\text{mm}^2$ specimen area is refined to $h \le l_0/2 = 7.5\,\mu\text{m}$ ($95.45\%$ area $h \le 8.0\,\mu\text{m}$).
   - **Suppression of Far-Field Coarsening**: Exactly $0.00\%$ of the domain retains coarse sizing $h \ge l_0 = 15.0\,\mu\text{m}$ ($h_{\max} = 12.62\,\mu\text{m}$).
   - Consequently, $\text{ET}=1.0\%$ functions as a quasi-uniform fine mesh rather than a selective adaptive mesh.

---

## 2. Formal Project Governance Decision

### Decision 2.1: Discretization Hierarchy & Roles
- **Active Production Fracture Baseline**: **Step-1 Final Frame ($u_x = 10.0\,\mu\text{m}$, $\text{ET} = 2.0\%$)** mesh (`M2_3_ADAPTED_RAW_2PCT.inp`, $22{,}530$ FEs, $22{,}642$ nodes).
  - *Role*: Currently solving in PBS Job `1411103.mmaster02` (Step 1 Inc 1443+, $u_x = 7.215\,\mu\text{m}$, 0 cutbacks, 3 iters/inc).
- **Equivalent Primary Candidate**: **Step-2 Final Frame ($u_x = 20.0\,\mu\text{m}$, $\text{ET} = 2.0\%$)** mesh (`M2_3_ADAPTED_STEP2_RAW_2PCT.inp`, $22{,}405$ FEs, $22{,}512$ nodes).
  - *Role*: Represents the full-horizon pre-analysis model; equivalent in spatial resolution ($-0.55\%$ FE delta); classified as `NOT YET PROVEN` superior to Step-1.
- **High-Cost Diagnostic Candidate**: **Step-2 Final Frame ($u_x = 20.0\,\mu\text{m}$, $\text{ET} = 1.0\%$)** mesh (`M2_3_ADAPTED_STEP2_RAW_1PCT.inp`, $80{,}474$ FEs, $80{,}136$ nodes).
  - *Role*: High-resolution reference diagnostic to assess global vs selective refinement; **strictly unqualified for unrequested production fracture runs** due to high computational overhead ($80.5\text{k}$ FEs).

---

## 3. Discretization Specification Matrix (Mode-II, $l_0 = 15.0\,\mu\text{m}$)

| Mesh Designation | Source Frame | Prescribed $u_x$ | Error Target | Finite Elements | $h_{\min}$ ($\mu\text{m}$) | $h_{\min}/l_0$ | Area $h \le l_0/2$ | Domain Coarse Area ($h \ge l_0$) | Governed Role |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `M2_3_ADAPTED_RAW_2PCT` | `Step-1` | $10.0\,\mu\text{m}$ | $2.0\%$ | $22{,}530$ | $0.73$ | $0.049$ | $31.54\%$ | $3.45\%$ | Active Fracture Retest Baseline (Job `1411103.mmaster02`) |
| `M2_3_ADAPTED_STEP2_RAW_2PCT` | `Step-2` | $20.0\,\mu\text{m}$ | $2.0\%$ | $22{,}405$ | $0.76$ | $0.051$ | $30.96\%$ | $3.70\%$ | Equivalent Full-Horizon Candidate (`NOT YET PROVEN` superior) |
| `M2_3_ADAPTED_STEP2_RAW_1PCT` | `Step-2` | $20.0\,\mu\text{m}$ | $1.0\%$ | $80{,}474$ | $0.60$ | $0.040$ | $93.09\%$ | $0.00\%$ | High-Cost Diagnostic Reference (Near-Global Refinement) |

---

## 4. Invariance & Preservation Constraints
1. **Mode-I Baseline Freeze**: Tag `v2026.10.08-supervisor-meeting-mode1-freeze` and Fortran UEL hash `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` remain strictly untouched.
2. **Active Cluster Retest**: PBS Job `1411103.mmaster02` ($22{,}530$ FEs) remains undisturbed in `normal_imfdfkmq`.
3. **Execution Guardrails**: Guarded SSH wrapper `Invoke-GuardedSsh.ps1` used for all remote operations; 100% scratch directory compliance on HPC.
