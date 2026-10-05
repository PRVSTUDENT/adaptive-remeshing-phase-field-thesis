# Mode-I Length-Scale Resolution Adequacy, Clean $l_0$ Sensitivity Audit, and Gate-6B Multi-Quantity Synthesis Schema

**Document ID:** `DOC-M1-L0-ADEQUACY-GATE6B-SYNTHESIS-001`  
**Governing Task:** `F1249-MODE1-CLEAN-L0-SENSITIVITY-AND-ADEQUACY-CONSISTENCY-CORRECTION`  
**Protocol Version:** 2  
**Date:** October 5, 2026  
**Status:** FROZEN & GOVERNED  

---

## 1. Executive Summary & Audit Scope

A comprehensive audit was performed across all historical and active Mode-I phase-field simulation packages to resolve key scientific questions for thesis defense:
1. **Clean Single-Variable Length-Scale ($l_0$) Sensitivity:** Audit Jobs `1406017.mmaster02` ($l_0 = 7.5\,\mu\text{m}$), `1406895.mmaster02` ($l_0 = 11.25\,\mu\text{m}$), and `1406896.mmaster02` ($l_0 = 15.0\,\mu\text{m}$) on the fixed structured $S_3$ mesh to establish whether they constitute true single-variable sweeps on bitwise identical discretizations.
2. **Length-Scale Resolution Adequacy:** Rigorously evaluate whether all governed meshes (Fixed Reference $S_1$, Adaptive Candidates ET1, ET2, ET3, ET5, and Spatial Fine 58k) satisfy continuum regularization requirements, separating local minimum, notch root, and corridor median element metrics.
3. **Reconciliation of Node-Count Conventions:** Explain the $+1$ discrepancy across input deck node listings (e.g. $15{,}522$ vs $15{,}521$; $14{,}457$ vs $14{,}456$; $42{,}492$ vs $42{,}491$).
4. **Governed Energy Bookkeeping & Multi-Quantity Synthesis:** Establish standardized terminology ($\mathcal{E}_{\text{elas}}$, $\mathcal{E}_{\text{frac}}$, $\mathcal{E}_{\text{model}}$, $\mathcal{W}_{\text{ext}}$, $\Delta_{\text{book}}$, $\varepsilon_{\text{book}}$) and qualify energy reporting boundaries.

---

## 2. Clean Single-Variable $l_0$ Twin Verification & Scaling Results

### 2.1 Mesh Identity & Provenance
Bitwise inspection of the input decks for Jobs `1406017`, `1406895`, and `1406896` confirms 100% spatial twin identity:
- **Node Coordinate SHA-256:** `7599c30f9bb6c4d605ec1cb570b9ce90268b69c07b01257c9cba84cd06345531` (identical across all three decks).
- **Element Connectivity SHA-256:** `96d085b28ca825296cfa636e4a9c2ea50dd1aff91eef0dd236ebeca315185903` (identical across all three decks).
- **FE Mesh Nodes:** $42{,}491$ continuum finite element nodes.
- **Reference Point Node:** $1$ auxiliary Reference Point Node `999999` ($42{,}492$ total input nodes).
- **Continuum Elements:** $41{,}912$ base quadrilateral elements ($125{,}736$ across the 3-layer UEL formulation).
- **Boundary Sets:** Exactly $404$ nodes on `N_BOTTOM` and $404$ nodes on `N_TOP`.
- **Material Constants:** $E = 210.0\,\text{GPa}$, $\nu = 0.30$, $G_c = 0.0027\,\text{kN/mm}$ ($2.7\,\text{N/mm}$), $k_{\text{res}} = 1.0\times 10^{-7}$, $N_{\text{base}} = 41912.0$.
- **Step Loading & Solver Controls:** Step 1 ($2{,}500$ incs, $u = 5.0\,\mu\text{m}$), Step 2 ($6{,}000$ incs, $u = 10.0\,\mu\text{m}$, initial $\Delta t = 2.0\times 10^{-4}$, min $\Delta t = 1.0\times 10^{-14}$).
- **Sole Intended Physical Difference:** The regularizing phase-field length scale $l_0 \in \{7.50, 11.25, 15.00\}\,\mu\text{m}$.

### 2.2 Multi-Quantity Comparison over Common Reached Domain ($u \in [0.0, 5.839]\,\mu\text{m}$)
Because the three jobs reached different terminal displacements ($u_{\text{term}} = 7.836\,\mu\text{m}$ for $l_0=7.5\,\mu\text{m}$, $5.839\,\mu\text{m}$ for $l_0=11.25\,\mu\text{m}$, and $6.473\,\mu\text{m}$ for $l_0=15.0\,\mu\text{m}$), quantitative comparison is strictly restricted to their common reached domain $u \in [0.0, 5.839]\,\mu\text{m}$ with zero unphysical forward-filling.

| Metric | $l_0 = 7.50\,\mu\text{m}$ (Job 1406017) | $l_0 = 11.25\,\mu\text{m}$ (Job 1406895) | $l_0 = 15.00\,\mu\text{m}$ (Job 1406896) | Relative Change | Sensitivity Classification |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Initial Stiffness $K_0$** | $137.858\,\text{kN/mm}$ | $137.766\,\text{kN/mm}$ | $137.676\,\text{kN/mm}$ | $-0.13\%$ | `L0_RESPONSE_STABLE` |
| **Peak Force $F_{\max}$** | $0.7322\,\text{kN}$ | $0.7084\,\text{kN}$ | $0.6895\,\text{kN}$ | $-5.83\%$ | `L0_RESPONSE_SENSITIVE` |
| **Peak Disp. $u_{\text{peak}}$** | $5.633\,\mu\text{m}$ | $5.590\,\mu\text{m}$ | $5.579\,\mu\text{m}$ | $-0.96\%$ | `L0_RESPONSE_SENSITIVE` |
| **Terminal Disp. $u_{\text{term}}$** | $7.836\,\mu\text{m}$ | $5.839\,\mu\text{m}$ | $6.473\,\mu\text{m}$ | N/A (censored) | Solver cutback limit |
| **Terminal $d_{\max}$** | $1.0000$ | $0.99965$ | $0.99971$ | $d \approx 1.0$ | Saturated crack |
| **Localization Width $w_{0.5}$** | $20.79\,\mu\text{m}$ | $34.41\,\mu\text{m}$ | $45.44\,\mu\text{m}$ | $+118.6\%$ | `L0_RESPONSE_SENSITIVE` |
| **Bandwidth Ratio $w_{0.5}/l_0$** | $2.77$ | $3.06$ | $3.03$ | $w_{0.5} \approx 3.04\,l_0$ | Linear regularizing scaling |
| **Centroid Offset $|y_c - 0.5|$** | $0.00\,\mu\text{m}$ | $2.12\,\mu\text{m}$ | $0.82\,\mu\text{m}$ | $< 2.2\,\mu\text{m}$ | Horizontal symmetry preserved |
| **Increments / Iterations** | $4{,}125$ / $13{,}917$ | $2{,}814$ / $9{,}621$ | $3{,}217$ / $10{,}842$ | Coarser $l_0$ reaches peak faster |

### 2.3 Physical Interpretation & Overall Classification
1. **Linear Elastic Regime ($u \le 4.0\,\mu\text{m}$):** Initial stiffness $K_0$ varies by only $0.13\%$ across a doubling of $l_0$, confirming that structural elastic response is unaffected by length-scale regularization when damage is negligible ($d \approx 0$).
2. **Fracture Initiation & Softening:** Peak reaction force decreases monotonically ($-5.83\%$) and peak displacement shifts earlier as $l_0$ increases. A larger regularizing length spreads the damage profile over a wider volume, reducing the effective peak stress required for macroscopic localization.
3. **Regularization Width Scaling:** Localization bandwidth scales linearly with $l_0$ ($w_{0.5} \approx 3.0\,l_0$), confirming correct theoretical gradient regularization.
4. **Historical Energy Status:** Because Jobs `1406017`, `1406895`, and `1406896` utilized Fortran source `5CD0D2C0...` prior to Gate-6B energy qualification and reached unequal displacements, their energy availability is formally classified as **`ENERGY_NOT_YET_QUALIFIED_UNEQUAL_ENDPOINTS_AND_PRE_GATE6B_SOURCE`**.
5. **Study Classification:** **`L0_SENSITIVITY_QUALIFIED_ON_FIXED_S3_MESH`**.

---

## 3. Separation of Resolution Adequacy Metrics

In general 2D planar meshes, claiming resolution adequacy based solely on global $h_{\min}$ can be misleading. Resolution metrics must be explicitly separated into:
1. **Core Minimum Element Size ($h_{\text{area},\min}$):** Smallest element area square-root along the active fracture process line.
2. **Notch-Root Element Size ($h_{\text{notch}}$):** Discretization size directly at the crack-initiating notch root $(0.5, 0.5)\,\text{mm}$.
3. **Median Corridor Element Size ($h_{\text{area},\text{median}}$):** Median element size within the propagation corridor $\Omega_{\text{corridor}} = [0.48, 1.02] \times [0.40, 0.60]\,\text{mm}$.

### 3.1 Governed Meshes Evaluation ($l_0 = 7.5\,\mu\text{m}$)

| Mesh Name | Base Elements | FE Mesh Nodes | Total Nodes (+RP) | $h_{\text{area},\min}$ [$\mu\text{m}$] | $h_{\text{notch}}$ [$\mu\text{m}$] | $h_{\text{area},\text{median}}$ [$\mu\text{m}$] | $\frac{h_{\text{area},\min}}{l_0}$ | $\frac{h_{\text{notch}}}{l_0}$ | $\frac{h_{\text{area},\text{median}}}{l_0}$ | Core Adequacy ($2l_0 / h_{\min}$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fixed Reference ($S_1$)** | 15,192 | 15,521 | 15,522 | 2.899 | 2.899 | 2.931 | **0.387** | **0.387** | **0.391** | $5.2$ elements |
| **Adaptive ET1 (14k)** | 14,483 | 14,456 | 14,457 | 0.760 | 1.988 | 2.068 | **0.101** | **0.265** | **0.276** | $19.7$ elements |
| **Adaptive ET2 (6k)** | 6,112 | 6,181 | 6,182 | 0.956 | 2.632 | 4.016 | **0.127** | **0.351** | **0.535** | $15.7$ elements |
| **Adaptive ET3 (5k)** | 5,189 | 5,262 | 5,263 | 1.339 | 2.769 | 4.898 | **0.179** | **0.369** | **0.653** | $11.2$ elements |
| **Adaptive ET5 (4k)** | 4,692 | 4,759 | 4,760 | 1.230 | 3.109 | 5.907 | **0.164** | **0.415** | **0.788** | $12.2$ elements |
| **Spatial Fine (58k)** | 57,929 | 57,491 | 57,492 | 0.553 | 1.896 | 1.947 | **0.074** | **0.253** | **0.260** | $27.1$ elements |

### 3.2 Key Adequacy Insights:
- **Core Crack Path Resolution:** Along the crack trajectory, all adaptive candidates provide $h_{\text{area},\min}/l_0 \le 0.179$, placing between $11.2$ and $27.1$ elements across $2l_0$, surpassing the classic continuum requirement ($h \le l_0 / 2$, or $h/l_0 \le 0.50$).
- **Notch Root Initiation Resolution:** Notch root element sizing satisfies $h_{\text{notch}}/l_0 \in [0.253, 0.415]$, ensuring accurate initiation stress concentration.
- **Corridor Transition Gradation:** In coarser candidates (ET2, ET3, ET5), the mesh transitions to $h_{\text{area},\text{median}}/l_0 \approx 0.54\text{--}0.79$ away from the core line, concentrating DOFs along the active path while economizing background elements.

---

## 4. Reconciliation of Node-Count Conventions

A persistent source of apparent $+1$ discrepancies in Abaqus node counts is the presence of the auxiliary **Reference Point (RP) Node `999999`**:
- **Continuum FE Mesh Nodes:** Nodes attached to solid/UEL elements ($15{,}521$ for $S_1$; $14{,}456$ for ET1; $6{,}181$ for ET2; $5{,}262$ for ET3; $4{,}759$ for ET5; $42{,}491$ for $S_3$; $57{,}491$ for 58k candidate).
- **Total Input Deck Nodes:** Includes $+1$ Reference Point Node `999999` used for kinematic MPC coupling ($15{,}522$ for $S_1$; $14{,}457$ for ET1; $6{,}182$ for ET2; $5{,}263$ for ET3; $4{,}760$ for ET5; $42{,}492$ for $S_3$; $57{,}492$ for 58k candidate).
- **Standardized Project Convention:** All future project documents and ledgers MUST explicitly label whether reported node counts represent pure continuum **`fe_mesh_nodes`** or **`total_input_deck_nodes`** (with RP).

---

## 5. Post-Peak Softening & Prescribed Loading Horizon

Mode-I boundary conditions prescribe a maximum horizon displacement $u \le 0.010\,\text{mm}$ ($10\,\mu\text{m}$) across Step 1 ($5\,\mu\text{m}$) and Step 2 ($10\,\mu\text{m}$). Any historical reference to $u > 0.015\,\text{mm}$ was an editorial artifact and is corrected.

In the deep post-peak softening regime ($u > 0.006\,\text{mm}$):
- The specimen is substantially fractured across the ligament.
- Absolute reaction forces drop below $F < 0.002\,\text{kN}$ ($<0.3\%$ of $F_{\max}$).
- Relative percentage differences $\Delta F / F$ become mathematically elevated due to the near-zero denominator, whereas absolute physical force discrepancy $\Delta F < 0.0015\,\text{kN}$ remains negligible.

---

## 6. Governed Multi-Quantity Energy Bookkeeping Terminology

In accordance with Gate-6B qualification, energy bookkeeping is strictly defined as follows:
- **Elastic Strain Energy ($\mathcal{E}_{\text{elas}}$ / `E_elas`):** Stored strain energy in the bulk continuum elements.
- **Fracture Dissipation Energy ($\mathcal{E}_{\text{frac}}$ / `E_frac`):** Regularized phase-field crack surface dissipation energy accumulated in UEL elements:
  $$\mathcal{E}_{\text{frac}} = \int_{\Omega} G_c \left[ \frac{(d - d_0)^2}{2 l_0} + \frac{l_0}{2} |\nabla d|^2 \right] \mathrm{d}\Omega$$
- **Internal Model Energy ($\mathcal{E}_{\text{model}}$ / `E_model`):** $\mathcal{E}_{\text{model}} = \mathcal{E}_{\text{elas}} + \mathcal{E}_{\text{frac}}$.
- **External Work ($\mathcal{W}_{\text{ext}}$ / `W_ext`):** Boundary work computed via trapezoidal integration of reaction force over displacement: $\mathcal{W}_{\text{ext}} = \int F \,\mathrm{d}u$.
- **Absolute Bookkeeping Discrepancy ($\Delta_{\text{book}}$ / `delta_book`):**
  $$\Delta_{\text{book}} = |\mathcal{W}_{\text{ext}} - \mathcal{E}_{\text{model}}|$$
- **Relative Bookkeeping Error ($\varepsilon_{\text{book}}$ / `epsilon_book`):**
  $$\varepsilon_{\text{book}} = \frac{|\mathcal{W}_{\text{ext}} - \mathcal{E}_{\text{model}}|}{\max(|\mathcal{W}_{\text{ext}}|, |\mathcal{E}_{\text{model}}|)}$$

The terms `E_strain` and `E_diss` are officially retired from the Gate-6B synthesis schema in favor of the governed symbols above.
