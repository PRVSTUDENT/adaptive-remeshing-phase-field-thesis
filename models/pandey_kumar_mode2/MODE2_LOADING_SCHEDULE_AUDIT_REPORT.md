# Mode-II Loading Schedule Forensic Reconciliation & Constitutive Source Audit Report

**Date:** 2026-10-07  
**Author:** Gemini Antigravity (Pair Programming Assistant)  
**Task ID:** `F1311-MODE2-LOADING-HORIZON-RECONSTRUCTION-AND-PREANALYSIS`  
**Governing Reference:** Pandey & Kumar (2025), *Computer Modeling in Engineering & Sciences* (CMES), Vol. 144, No. 3, pp. 3251–3276, Section 4.2.  
**Branch:** `mode2-pandey-kumar-reproduction`  
**Gate Status:** `GATE_M2_2_QUALIFIED_READY_TO_SUBMIT_BLOCKED_BY_DELEGATION`

---

## 1. Executive Summary

This report performs a forensic reconciliation of the Mode-II coarse pre-analysis loading schedule, addresses the conflict between published text and figures in Pandey & Kumar (2025) Section 4.2, records the creation of candidate input deck `Job-1_UEL_paper_horizon.inp`, documents remote cluster Datacheck qualification, and audits subroutine source isolation relative to the protected Mode-I baseline.

Key Findings:
1. **Publication Text vs Figures Conflict:** The statement in Section 4.2 ("median of 0.06 mm", "2100 increments of size $\Delta u_1 = 5 \times 10^{-4}$ and then at $\Delta u_2 = 10^{-5}$ for a further 5000 increments") is classified as:
   $$\mathbf{PAPER\_TEXT\_CONFLICTS\_WITH\_FIGURES}$$
   - Literal interpretation of $\Delta u_1 = 5 \times 10^{-4}\,\text{mm}$ yields $2100 \times 5 \times 10^{-4}\,\text{mm} = 1.05\,\text{mm}$, which exceeds the total $1.0\,\text{mm}$ specimen width by $105\%$.
   - The printed terminal horizon $0.0600\,\text{mm}$ ($60.0\,\mu\text{m}$) is $3\times$ to $4\times$ past complete specimen separation. Fig. 12 shows crack propagation at $u_x = 9.36\,\mu\text{m}$, $11.842\,\mu\text{m}$, and $16.26\,\mu\text{m}$. Fig. 13(a) demonstrates complete failure with reaction force dropping to $F \approx 0$ by $u_x \approx 0.016$–$0.020\,\text{mm}$.
2. **Reconciled Paper-Horizon Input Deck (`Job-1_UEL_paper_horizon.inp`):**
   - **Step 1 (Elastic / Pre-Initiation Singularity):** $T_1 = 1.0$, $\Delta t_1 = 5 \times 10^{-4}$ ($2000$ increments), $u_x = 0 \to 0.0100\,\text{mm}$, $\Delta u_1 = 5.0\,\text{nm}$.
   - **Step 2 (Fracture Propagation to Terminal Horizon):** $T_2 = 1.0$, $\Delta t_2 = 5 \times 10^{-4}$ ($2000$ increments), $u_x = 0.0100 \to 0.0200\,\text{mm}$, $\Delta u_2 = 5.0\,\text{nm}$.
   - Spans the complete physical horizon $u_x \in [0.0, 0.0200]\,\text{mm}$ with uniform $5.0\,\text{nm}$ incrementation, covering all Fig. 12 states and the complete Fig. 13(a) curve.
   - Preserves historical $u_x = 0.0600\,\text{mm}$ deck `Job-1_UEL.inp` as noncanonical evidence.
3. **Remote Cluster Datacheck Qualification:**
   - Intel Fortran compilation (`ifort 2021.13.0`) of `f42_mixed_uel_mode2_miehe.for` and Abaqus 2023 Datacheck of `Job-1_UEL_paper_horizon.inp` executed on `tu_freiberg` cluster.
   - Result: `DATACHECK_EXIT=0`, 0 errors, 10 standard UEL warnings.
4. **Submission Delegation Status:**
   - Evaluated OpenClaw submission delegation: permit consumed (`active: false`), daily delegation expired 2026-10-05.
   - Gate M2-2 status recorded as `M2-2_QUALIFIED_READY_TO_SUBMIT_BLOCKED_BY_DELEGATION`.
   - Zero solver jobs submitted.
5. **Mode-I Protection:**
   - Mode-I freeze tag `v2026.10.08-supervisor-meeting-mode1-freeze` and UEL hash `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` remain 100% untouched.

---

## 2. Four-Step Forensic Loading Reconciliation

### Step 1: Exact Published Text & Fig. 13 Physical Horizon
- **Published Text (Section 4.2, p. 3271):**
  > *"The pre-adaptive ‘Job-1_UEL.inp’ is submitted for 2100 increments of size $\Delta u_1 = 5 \times 10^{-4}$ and then at $\Delta u_2 = 10^{-5}$ for a further 5000 increments. The initial mesh with the global mesh size of 0.02 mm is analyzed for the MISESERI error indicator values."*
- **Mathematical Impossibility of Literal Physical Increments:**
  $$\text{Literal Step-1 Displacement} = 2100 \times 5 \times 10^{-4}\,\text{mm} = 1.050\,\text{mm}$$
  Since the specimen dimension is $L = 1.0\,\text{mm}, H = 1.0\,\text{mm}$, a shear displacement of $1.05\,\text{mm}$ corresponds to a shear strain $\gamma = 105\%$, vastly beyond elastic or fracture limits.
- **Physical Response Curve (Fig. 13a) & Contour Sequence (Fig. 12):**
  - Linear elastic range: $u_x \in [0.000, 0.008]\,\text{mm}$.
  - State 1 (Fig. 12a): $u_x = 9.36 \times 10^{-3}\,\text{mm}$ ($9.36\,\mu\text{m}$).
  - Peak shear load: $F_{\max} \approx 0.58\,\text{kN}$ at $u_x \approx 0.012$–$0.014\,\text{mm}$.
  - State 2 (Fig. 12b): $u_x = 11.842 \times 10^{-3}\,\text{mm}$ ($11.842\,\mu\text{m}$).
  - State 3 (Fig. 12c): $u_x = 16.26 \times 10^{-3}\,\text{mm}$ ($16.26\,\mu\text{m}$).
  - Complete structural softening: $F \to 0$ by $u_x \approx 0.017$–$0.020\,\text{mm}$.
- **Resolution:** The printed text "median of 0.06 mm" and increment definitions conflate pseudo-time $\Delta t$ with physical displacement and overshoot the physical failure horizon by $300\%$. The physical failure occurs within $u_x \in [0.0, 0.0200]\,\text{mm}$.

### Step 2: Paper Code Listings & Amplitude Definitions
- Listings 1, 2, 3, and 4 in the publication were checked line-by-line:
  - `Listing 1`: `create_remeshing_rule_assembly_instance(model_name, instance_name, step_name, maxSize, minSize)`
  - `Listing 2`: Facsimile set `All_elem` creation matching `umatelem`
  - `Listing 3`: Output requests (`MISESERI, MISESAVG, S, EVOL`, `RF, U`, `SDV`)
  - `Listing 4`: `implement_remesh(odb_path, model_name)`
- No explicit `*AMPLITUDE` curves or tabular time-displacement pairs are specified in the paper's script listings for Mode-II.

### Step 3: Exact Keywords & Cards in `Job-1_UEL.inp` vs `Job-1_UEL_paper_horizon.inp`
The historical deck `Job-1_UEL.inp` implemented:
- Step 1: $u_x = 0.0105\,\text{mm}$, $\Delta t = 5 \times 10^{-4}$ ($2000$ incs).
- Step 2: $u_x = 0.0600\,\text{mm}$, $\Delta t = 2 \times 10^{-4}$ ($5000$ incs).

The canonical paper-horizon candidate deck `Job-1_UEL_paper_horizon.inp` implements:
- Step 1: $u_x = 0.0100\,\text{mm}$, $\Delta t = 5 \times 10^{-4}$ ($2000$ incs, $\Delta u_1 = 5.0\,\text{nm}$).
- Step 2: $u_x = 0.0200\,\text{mm}$, $\Delta t = 5 \times 10^{-4}$ ($2000$ incs, $\Delta u_2 = 5.0\,\text{nm}$).

### Step 4: Survey of Surviving Repository Mode-II Decks
- Historical H0/H1/H2 decks tested fixed amplitude tables (`Amp-1: 0.0 -> 0.005 mm`, `Amp-2: 0.005 -> 0.010 mm`) or single continuous steps (`0.050 mm` over 20,000 increments).
- `Job-1_UEL_paper_horizon.inp` aligns the two-step structure directly with the publication's physical fracture horizon.

---

## 3. Authoritative Forensic Loading Table

| Step | Parameter | Symbol | Historical Deck (`Job-1_UEL.inp`) | Reconciled Deck (`Job-1_UEL_paper_horizon.inp`) | Literature Text Specification | Classification & Physical Meaning |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Step 1** | Step Time | $T_{\text{step}}$ | $1.0$ | $1.0$ | Unspecified (Abaqus default $1.0$) | `INFERRED` standard Abaqus pseudo-time |
| | Initial / Max Increment | $\Delta t$ | $5.0 \times 10^{-4}$ | $5.0 \times 10^{-4}$ | $\Delta u_1 = 5 \times 10^{-4}$ | `PAPER_TEXT_CONFLICTS_WITH_FIGURES` (dimensionless $\Delta t$) |
| | Increment Count | $N_{\text{inc}}$ | $2,000$ | $2,000$ | $2,100$ increments | $T / \Delta t = 1.0 / (5.0\times 10^{-4}) = 2,000$ |
| | Boundary Displacement Start | $u_x(0)$ | $0.0000\,\text{mm}$ | $0.0000\,\text{mm}$ | $0.0\,\text{mm}$ | `PAPER_VERIFIED` zero initial displacement |
| | Boundary Displacement End | $u_x(T_1)$ | $0.0105\,\text{mm}$ | $0.0100\,\text{mm}$ ($10.0\,\mu\text{m}$) | Unspecified in text | `INFERRED` pre-damage elastic limit ($d < 0.20$) |
| | Amplitude Type | - | Linear RAMP | Linear RAMP | Not specified | Default Abaqus linear ramping |
| | Physical $\Delta u_x$ per inc | $\Delta u_x$ | $5.25\,\text{nm}$ | $5.00\,\text{nm}$ | Conflated with $\Delta u_1 = 5\times 10^{-4}$ | Uniform $\Delta u_x = 5.00\,\text{nm}$ |
| **Step 2** | Step Time | $T_{\text{step}}$ | $1.0$ | $1.0$ | Unspecified (Abaqus default $1.0$) | `INFERRED` standard Abaqus pseudo-time |
| | Initial / Max Increment | $\Delta t$ | $2.0 \times 10^{-4}$ | $5.0 \times 10^{-4}$ | $\Delta u_2 = 10^{-5}$ | $\Delta t = 5.0 \times 10^{-4}$ ($2000$ incs) |
| | Increment Count | $N_{\text{inc}}$ | $5,000$ | $2,000$ | $5,000$ increments | Covers full fracture to $F \approx 0$ |
| | Boundary Displacement Start | $u_x(0)$ | $0.0105\,\text{mm}$ | $0.0100\,\text{mm}$ | Inherited from Step 1 | Continuity from Step 1 |
| | Boundary Displacement End | $u_x(T_2)$ | $0.0600\,\text{mm}$ ($60.0\,\mu\text{m}$) | $0.0200\,\text{mm}$ ($20.0\,\mu\text{m}$) | $0.06\,\text{mm}$ (Sec. 4.2 text) | `PAPER_TEXT_CONFLICTS_WITH_FIGURES` ($0.020\,\text{mm}$ matches Fig 12 & 13a) |
| | Amplitude Type | - | Linear RAMP | Linear RAMP | Not specified | Default Abaqus linear ramping |
| | Physical $\Delta u_x$ per inc | $\Delta u_x$ | $9.90\,\text{nm}$ | $5.00\,\text{nm}$ | $\Delta u_2 = 10^{-5}$ | Uniform $\Delta u_x = 5.00\,\text{nm}$ |

---

## 4. Reconstructed Input Deck: `Job-1_UEL_paper_horizon.inp`

The candidate deck `Job-1_UEL_paper_horizon.inp` (SHA-256 `BCFC850EDD07B9DC0BEC36FA8A795A5A0F55EFA4CA75A584784862F41D3F04F5`) contains:
- **Geometry & Mesh:** 2,960 elements (2,860 CPE4 + 100 CPE3), 3,036 nodes.
- **Layering:** Layer 1 (U1/U3 phase), Layer 2 (U2/U4 mechanical), Layer 3 (CPE4/CPE3 companion). Total 8,880 element cards.
- **Boundary Conditions:** Bottom $u_x = u_y = 0$, Top $u_y = 0$, Top $u_x$ coupled via `*EQUATION` to RP 999999.
- **Loading:** Uniform $\Delta u_x = 5.0\,\text{nm}$ across 4,000 total increments reaching $u_x = 0.0200\,\text{mm}$ ($20.0\,\mu\text{m}$).

---

## 5. Subroutine Source Diff: `f42_mixed_uel_mode2_miehe.for` vs `f42_mixed_uel.for`

A line-by-line comparison between `f42_mixed_uel_mode2_miehe.for` and `models/pandey_kumar_mode1/f42_mixed_uel.for` confirms:

| Architectural Component | Mode-I Reference (`f42_mixed_uel.for`) | Mode-II Implementation (`f42_mixed_uel_mode2_miehe.for`) | Source Diff Verdict |
| :--- | :--- | :--- | :---: |
| **Protected File Hash** | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | Unchanged (separate file) | **100% UNTOUCHED** |
| **Element Types & DOFs** | Quad Phase (`JTYPE=1`, DOF 3), Quad Mech (`JTYPE=2`, DOFs 1,2), Tri Phase (`JTYPE=3`, DOF 3), Tri Mech (`JTYPE=4`, DOFs 1,2) | Quad Phase (`JTYPE=1`, DOF 3), Quad Mech (`JTYPE=2`, DOFs 1,2), Tri Phase (`JTYPE=3`, DOF 3), Tri Mech (`JTYPE=4`, DOFs 1,2) | **EXACT MATCH** |
| **State Exchange Architecture** | `COMMON /CB_STATE_TRANS/ SV_PHASE_TRIAL, SV_H_TRIAL, SV_PSI_E_TRIAL` | `COMMON /CB_STATE_TRANS/ SV_PHASE_TRIAL, SV_H_TRIAL, SV_PSI_E_TRIAL` | **EXACT MATCH** |
| **Phase-Field Weak Form & RHS** | $\int [G_c l_0 \nabla\phi\cdot\nabla\delta\phi + (G_c/l_0 + 2H)\phi\delta\phi - 2H\delta\phi] d\Omega$ | $\int [G_c l_0 \nabla\phi\cdot\nabla\delta\phi + (G_c/l_0 + 2H)\phi\delta\phi - 2H\delta\phi] d\Omega$ | **EXACT MATCH** |
| **Material Units & PROPS ABI** | `PROPS(1..6) = (l0, Gc, E, nu, k, N_phys)` with $E=210.0\,\text{kN/mm}^2, G_c=0.0027\,\text{kN/mm}$ | `PROPS(1..6) = (l0, Gc, E, nu, k, N_phys)` with $E=210.0\,\text{kN/mm}^2, G_c=0.0027\,\text{kN/mm}$ | **EXACT MATCH** |
| **History Semantics** | $H = \max(\psi_0^+, H_{\text{old}})$ monotonically irreversible | $H = \max(\psi_0^+, H_{\text{old}})$ monotonically irreversible | **EXACT MATCH** |
| **Constitutive Formulation** | Isotropic degradation: $\boldsymbol{\sigma} = g(d) \mathbf{C} : \boldsymbol{\varepsilon}$ | **2D Plane-Strain Miehe Spectral Split:** $\boldsymbol{\sigma} = g(d) \boldsymbol{\sigma}_0^+ + \boldsymbol{\sigma}_0^-$ with symmetric analytical tangent $\mathbf{D}_{\text{mech}} = g(d) \mathbf{D}_0^+ + \mathbf{D}_0^-$ | **INTENDED CHANGE ONLY** |
| **Layering Semantics** | Layer 1 (Phase), Layer 2 (Mech), Layer 3 (UMAT Facsimile) | Layer 1 (Phase), Layer 2 (Mech), Layer 3 (UMAT Facsimile) | **EXACT MATCH** |

---

## 6. Governed Gate Status & Conclusions

- **Gate M2-2 Status:** `M2-2_QUALIFIED_READY_TO_SUBMIT_BLOCKED_BY_DELEGATION`
- **Remote Datacheck:** PASSED with `DATACHECK_EXIT=0`, 0 errors, 10 UEL-expected warnings on `tu_freiberg` cluster.
- **Submission Boundary:** OpenClaw submission permit is consumed and daily delegation expired 2026-10-05. Zero solver jobs submitted. No execution will occur until fresh explicit human authorization is granted.
- **Lineage Integrity:** Tag `v2026.10.08-supervisor-meeting-mode1-freeze` and Mode-I UEL hash `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` remain completely unmodified.
