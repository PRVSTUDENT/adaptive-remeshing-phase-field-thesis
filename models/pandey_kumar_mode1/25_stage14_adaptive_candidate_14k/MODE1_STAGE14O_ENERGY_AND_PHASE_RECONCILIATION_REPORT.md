# Mode-I Gate-6B Stage 14O: Energy-Unit and Phase-Field Anchor Reconciliation Report

**Protocol Version:** 2  
**Task ID:** `F1192-GATE6B-STAGE14O-ENERGY-UNIT-AND-PHASE-FIELD-ANCHOR-RECONCILIATION-20261003`  
**Evaluation Date:** 2026-10-03  
**Evaluated By:** Gemini Antigravity  
**Governing Verdict:** `STAGE14_ENERGY_AND_PHASE_ANCHOR_RECONCILED`  

---

## 1. Executive Summary & Root Cause Forensics

During Stage 14N closeout, an audit of the initial elasticity comparison table at $u = 0.0010\,\text{mm}$ (Increment 400) revealed two presentation and extraction discrepancies:
1. **Energy Factor-of-1000 Omission:** The reference and adaptive elastic energies were reported as $E_{\text{elas}} \approx 0.000069\,\text{mJ}$ instead of the established reference bundle value $E_{\text{elas}} \approx 0.068962\,\text{mJ}$.
2. **Phase-Field Nominal Zero vs Field Evaluation:** The phase field was reported as $d_{\max} = 0.000000$ ("intact $d=0$") instead of extracting the non-zero singular notch-tip micro-damage field ($d_{\max} = 0.00910334$ in reference, $d_{\max} = 0.00953182$ in adaptive candidate).

### 1.1 Root Cause #1: Solver Energy Unit Scaling ($1\,\text{kN}\cdot\text{mm} = 1\,\text{J} = 1000\,\text{mJ}$)
In `f42_mixed_uel.for`, all whole-element energy integrals (`SV_FRACTURE_ENERGY`, `SV_ELASTIC_ENERGY`) are integrated in consistent Abaqus solver units:
$$\text{Force} \times \text{Displacement} = \text{kN} \times \text{mm} = \text{kN}\cdot\text{mm} \equiv \text{J}$$
In Stage 14N's summary script, the raw values ($6.896208 \times 10^{-5}$) were inserted directly into fields named `_mJ` without multiplying by $1000$. Converting to millijoules yields:
$$E_{\text{elas}} = 6.89620813 \times 10^{-5}\,\text{kN}\cdot\text{mm} \times 1000\,\frac{\text{mJ}}{\text{kN}\cdot\text{mm}} = \mathbf{0.068962081\,\text{mJ}}$$
$$E_{\text{frac}} = 5.55344167 \times 10^{-8}\,\text{kN}\cdot\text{mm} \times 1000\,\frac{\text{mJ}}{\text{kN}\cdot\text{mm}} = \mathbf{5.5534417 \times 10^{-5}\,\text{mJ}}$$

### 1.2 Root Cause #2: Micro-Damage Field State at Singular Notch Tip
In Stage 14N, $d_{\max}$ was described qualitatively as "intact $d=0$" because macroscopic crack propagation had not initiated ($d < 0.01$, crack tip $x_{\text{tip}} = 0.500\,\text{mm}$). Exact extraction from Layer 3 companion elements confirms that `SDV14` and `SDV1` match bit-for-bit, reflecting the smooth diffusive regularized damage field around the sharp crack tip ($r \to 0$ stress concentration):
- Fixed Reference 1409734: $d_{\max} = \mathbf{0.00910334}$
- Corrected Adaptive 1409953: $d_{\max} = \mathbf{0.00953182}$

---

## 2. Definitive Reconciliation Table at $u = 0.001000\,\text{mm}$ (Increment 400)

The following authoritative table compares the qualified fixed reference solve (Job `1409734.mmaster02`, 15,192 elements) with the live corrected adaptive solve (Job `1409953.mmaster02`, 14,483 elements) at the canonical elasticity endpoint $u = 0.001000\,\text{mm} = 1.0\,\mu\text{m}$.

| Physical Quantity / Metric | Unit | Fixed Reference (`1409734.mmaster02`) | Corrected Adaptive (`1409953.mmaster02`) | Absolute Difference ($\Delta$) | Relative Error ($\%$) | Governance Classification |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Displacement $u$** | $\text{mm}$ | $0.001000$ | $0.001000$ | $0.0$ | $0.000\%$ | Synchronized State |
| **Displacement $u$** | $\mu\text{m}$ | $1.000$ | $1.000$ | $0.0$ | $0.000\%$ | Synchronized State |
| **Increment Index** | $-$ | $400$ | $400$ | $0$ | $-$ | Matched Step Schedule |
| **Reaction Force $F$** | $\text{kN}$ | $0.13792416$ | $0.13788816$ | $-0.00003600$ | $\mathbf{-0.0261\%}$ | `STABLE` |
| **Raw UEL $E_{\text{elas}}$** | $\text{kN}\cdot\text{mm}$ | $6.89620813 \times 10^{-5}$ | $6.89440827 \times 10^{-5}$ | $-1.79986 \times 10^{-8}$ | $\mathbf{-0.0261\%}$ | `STABLE` |
| **Reconciled $E_{\text{elas}}$** | $\text{mJ}$ | $\mathbf{0.068962081}$ | $\mathbf{0.068944083}$ | $\mathbf{-0.0000179986}$ | $\mathbf{-0.0261\%}$ | `STABLE` |
| **Raw UEL $E_{\text{frac}}$** | $\text{kN}\cdot\text{mm}$ | $5.55344167 \times 10^{-8}$ | $5.56075948 \times 10^{-8}$ | $+7.31781 \times 10^{-10}$ | $\mathbf{+0.1318\%}$ | `STABLE` |
| **Reconciled $E_{\text{frac}}$** | $\text{mJ}$ | $\mathbf{0.0000555344}$ | $\mathbf{0.0000556076}$ | $\mathbf{+7.31781 \times 10^{-7}}$ | $\mathbf{+0.1318\%}$ | `STABLE` |
| **Total Model Energy $E_{\text{model}}$** | $\text{mJ}$ | $0.069017616$ | $0.068999690$ | $-0.000017926$ | $-0.0260\%$ | `STABLE` |
| **External Work $W_{\text{ext}}$** | $\text{mJ}$ | $0.069017512$ | $0.068999510$ | $-0.000018002$ | $-0.0261\%$ | `STABLE` |
| **Bookkeeping Residual $\Delta_{\text{book}}$** | $\text{mJ}$ | $+1.03508 \times 10^{-7}$ | $+1.80000 \times 10^{-7}$ | $+7.6492 \times 10^{-8}$ | $-$ | Internal UEL Residual |
| **Bookkeeping Residual $\varepsilon_{\text{book}}$** | $\%$ | $0.000150\%$ | $0.000261\%$ | $+0.000111\%$ | $-$ | $\ll 0.01\%$ (`PASS`) |
| **Max Phase Field $d_{\max}$** | $-$ | $\mathbf{0.00910334}$ | $\mathbf{0.00953182}$ | $+0.00042848$ | $\mathbf{+4.7068\%}$ | Micro-Damage Parity |
| **Crack Tip Position $x_{\text{tip}}(d \ge 0.90)$** | $\text{mm}$ | $0.5000$ | $0.5000$ | $0.0$ | $0.000\%$ | Undamaged Ligament |
| **Structural Stiffness $K_0$** | $\text{kN/mm}$ | $\mathbf{137.945520}$ | $\mathbf{137.909558}$ | $\mathbf{-0.035962}$ | $\mathbf{-0.0261\%}$ | `STABLE` ($R^2 = 0.99999960$) |

---

## 3. Key Findings & Scientific Governance

1. **Exact Elastic Energy Parity:**
   The relative difference between adaptive and reference elastic strain energy at $u = 0.0010\,\text{mm}$ is $-0.0261\%$, identical to the force discrepancy ($-0.0261\%$). This mathematically satisfies the linear elastic relationship $E_{\text{elas}} \propto F \cdot u$.
2. **Fracture Functional Consistency:**
   The implemented phase-field crack functional $E_{\text{frac}}$ at $u = 0.0010\,\text{mm}$ is $0.0000556\,\text{mJ}$ ($5.56 \times 10^{-5}\,\text{mJ}$), which accounts for only $0.08\%$ of the total stored energy ($0.069\,\text{mJ}$). The $+0.13\%$ difference vs reference reflects the slight mesh sizing variations around the notch tip.
3. **Internal Energy Balance Integrity:**
   Both models maintain near-perfect internal energy balance with bookkeeping residuals $\varepsilon_{\text{book}} = 0.00015\%$ (reference) and $0.00026\%$ (adaptive), demonstrating excellent solver precision.
4. **Phase-Field Companion Parity:**
   Extraction from Layer 3 companion CPE4/CPE3 elements confirmed that `SDV14` and `SDV1` match to 16 decimal places (`SV_PHASE_TRIAL(PHYSIDX)`).
5. **Structural Stiffness $K_0$:**
   Canonical stiffness $K_0 = 137.909558\,\text{kN/mm}$ across all 400 increments ($R^2 = 0.99999960$, intercept $4.471205 \times 10^{-5}\,\text{kN}$) remains the official structural stiffness anchor.
