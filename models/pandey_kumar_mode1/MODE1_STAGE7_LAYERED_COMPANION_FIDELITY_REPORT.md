# Gate-6B Mode-I Adaptive-Localization Stage 7: Layered Companion-Element Reference-Fidelity Forensic Report (Corrected)

Protocol Version: 2  
Active Coordination Authority: `project_coordination/`  
Date: `2026-10-03`  
Author: Gemini Antigravity  
Task ID: `F1183-GATE6B-ADAPTIVE-LOCALIZATION-STAGE7-LAYERED-COMPANION-DIAGNOSTIC-20261003`  
Status: `STAGE7_COMPLETE_LAYERED_COMPANION_EVALUATED_CORRECTED`  
Formal Verdict: **`PROJECT_SOURCE_VERIFIED_ZERO_STRESS_LAYERED_COMPANION`**  
Directional Classification: **`LAYERED_COMPANION_INVALID_OR_UNRESOLVED`**  

---

## 1. Executive Summary & Epistemic Governance

The objective of Stage 7 was to evaluate the behavior of the 3-layer coupled UEL/UMAT architecture on the canonical 2,906-element mesh (`PK_M1_JOB1_LAYERED_COMPANION_2906`, Package 92) using our governed `f42_mixed_uel.for` subroutine, and to determine whether it evaluated a non-zero `MISESERI` error field on `All_elem`.

### Core Epistemic Findings & Distinctions:
1. **`PROJECT_SOURCE_VERIFIED` (Our Governed Implementation):**
   - In our governed `f42_mixed_uel.for` (Package 92), the companion UMAT subroutine explicitly sets `STRESS(I) = 0.D0` with a diagonal dummy stiffness `DDSDDE(I,I) = 1.D-11`.
   - Consequently, Cauchy stress on `All_elem` is identically zero throughout the domain, and Abaqus evaluates $\text{MISESERI} \equiv 0.000000$ across all 2,906 elements.
2. **`UNRESOLVED_REFERENCE_DETAIL` (Literature Reference Mechanism):**
   - Pandey & Kumar (2025) explicitly state in Section 3 that `Job-1_UEL.inp` is submitted along with the user subroutine to obtain the requested `MISESERI` values for the facsimile set `All_elem`, followed by native `adaptiveRemesh`.
   - Their exact companion-UMAT constitutive equations are not printed in the paper text. However, their cited foundational baseline (Molnár & Gravouil 2017 [72]) implements an infinitesimal elastic constitutive update ($\mathbf{\sigma}_{n+1} = \mathbf{\sigma}_n + \mathbf{C}_{\text{dummy}} : \Delta \mathbf{\varepsilon}$ with $E_{\text{dummy}} = 10^{-11}$), producing stresses and `MISESERI` on the order of $10^{-12}$.
3. **Corrected Published Fig. 6(a) Legend Scale:**
   - The contour legend in Pandey & Kumar (2025) Fig. 6(a) reports values on the order of **$10^{-12}$**, spanning approximately from $1.47 \times 10^{-19}$ to $3.00 \times 10^{-12}$ (dimensionless or unscaled stress indicator), **NOT $0 \to 95\,\text{MPa}$**.
   - This $10^{-12}$ magnitude directly aligns with the infinitesimal companion elasticity hypothesis ($E_{\text{dummy}} = 10^{-11}$).

---

## 2. 3-Layer UEL/UMAT Subroutine Mechanics (`f42_mixed_uel.for` Package 92)

| Architectural Layer | Element Set | Subroutine Handler | Implemented Mechanics in Package 92 | Cauchy Stress on All_elem |
| :--- | :--- | :--- | :--- | :---: |
| **Layer 1** | `uelem_phase` (2,906 UELs) | `UEL` (f42) | Phase-field Helmholtz equation, trial $d$ written to `/CB_STATE_TRANS/` | N/A (UEL) |
| **Layer 2** | `uelem_mech` (2,906 UELs) | `UEL` (f42) | Degraded linear elasticity, full system stiffness `AMATRX` and force `RHS` | N/A (UEL) |
| **Layer 3** | `All_elem` / `umatelem` (2,906 elements) | `UMAT` (f42) | `STRESS(I) = 0.D0`, `DDSDDE(I,I) = 1.D-11`, SDV transfer from `/CB_STATE_TRANS/` | **$\mathbf{\sigma} \equiv \mathbf{0}$** |

Because `STRESS(I) = 0.D0` in Package 92, Abaqus Superconvergent Patch Recovery (SPR) on `All_elem` evaluates:
$$\text{MISESERI}_e = \sqrt{\frac{3}{2}(\mathbf{s}^* - \mathbf{s}_h) : (\mathbf{s}^* - \mathbf{s}_h)} \equiv 0.0$$

---

## 3. Quantitative Comparison: Package 92 vs Control vs Fig. 6(a)

| Diagnostic Metric | Governed Zero-Stress Layered (Package 92) | Standard Continuum Control (Package 90) | Published Fig. 6(a) (Digitized Literature) |
| :--- | :---: | :---: | :---: |
| **Mesh Elements** | 2,906 | 2,906 | $\sim 2,900$ |
| **Subroutine** | `f42_mixed_uel.for` (STRESS=0) | None (Standard Abaqus FE) | `Job-1_UEL.inp` with User Subroutine |
| **Peak Cauchy Stress $\sigma$** | **$0.000000$** | **$37.954\,\text{MPa}$** | Not reported |
| **Max $\text{MISESERI}$** | **$0.000000$** | **$0.950009\,\text{MPa}$** | **$\approx 3.00 \times 10^{-12}$** |
| **Min $\text{MISESERI}$** | **$0.000000$** | **$0.000215\,\text{MPa}$** | **$\approx 1.47 \times 10^{-19}$** |
| **Step 1 End RF ($u=0.005\,\text{mm}$)** | **$0.653089\,\text{kN}$** | **$0.675452\,\text{kN}$** | $\sim 0.69\,\text{kN}$ |

---

## 4. Transition to Stage 8: Infinitesimal Companion Elasticity Audit

Stage 7 demonstrated that setting `STRESS = 0` produces zero error indicator. The next scientific investigation (Stage 8) evaluates the hypothesis that the companion UMAT in the literature implemented constitutively consistent infinitesimal elasticity ($\mathbf{\sigma} = \mathbf{C}_{\text{dummy}} : \mathbf{\varepsilon}$ with $E_{\text{dummy}} = 10^{-11}$), which yields non-zero stresses matching the $10^{-12}$ scale of Fig. 6(a).
