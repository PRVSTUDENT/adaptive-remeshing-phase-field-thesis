# Gate M2-4 Terminal Evaluation Report: Mode-II Adapted Refined PFM Fracture Simulation

**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  
**Benchmark Reference:** Pandey & Kumar (2025) *CMES*, Vol. 144, No. 3, Section 4.2 (pp. 3270–3272).  
**Primary Digitization Provenance:** [`references/derived/pandey_kumar_2025_fig13a_digitization_provenance.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/references/derived/pandey_kumar_2025_fig13a_digitization_provenance.md) and [`pandey_kumar_2025_fig13a_digitized.csv`](file:///D:/Master%20thesis/Adaptive%20remeshing/references/derived/pandey_kumar_2025_fig13a_digitized.csv).  
**Target Analysis:** Mode-II Edge-Cracked Plate under Pure Shear on 22,530-FE Adapted Mesh (`Job-2_UEL.inp`).  
**Constitutive Split:** 2D Plane Strain Miehe Anisotropic Spectral Split (`f42_mixed_uel_mode2_miehe.for`).  
**HPC Job ID:** `1410797.mmaster02` (1 CPU serial, 16 GB RAM, `normal_imfdfkmq`, mmaster02).  
**Evaluation Status:** `AWAITING_SOLVER_TERMINAL_COMPLETION` (Evaluation package & audited primary criteria frozen).

---

## 1. Executive Summary

| Quantity / Metric | Governed Requirement | Primary Paper Benchmark | Evaluated Result | Verdict |
| :--- | :--- | :--- | :--- | :---: |
| **Physical Mesh Sizing** | $N_{\text{FE}} \le 40{,}000$, $h_{\min} \le l_0/2$ | $22{,}530$ FEs ($21{,}962$ quads, $568$ tris), $h_{\min}=0.73\,\mu\text{m}$ | $22{,}530$ FEs, $22{,}642$ nodes | **PASS** |
| **Constitutive Source** | Miehe spectral split, Mode-I frozen | SHA-256 `75029EF7...`, Tag `v2026.10.08...` | Verified bitwise identical | **PASS** |
| **Loading Schedule** | Step 1 ($u_x \to 0.0100\,\text{mm}$) + Step 2 ($u_x \to 0.0200\,\text{mm}$) | $4{,}000$ increments, $\Delta u_x = 5.0\,\text{nm}$/inc | Full paper horizon ($0 \to 20.0\,\mu\text{m}$) | `RUNNING` |
| **Initial Shear Stiffness $K_{0,\text{shear}}$** | Linear shear compliance | Fig. 13(a) reference $= 12.80\,\text{kN/mm}$ | *Pending ODB completion* | `PENDING` |
| **Peak Shear Force $F_{\max}$** | Physical peak before softening | Fig. 13(a) reference $= 0.1455\,\text{kN}$ ($145.5\,\text{N}$) | *Pending ODB completion* | `PENDING` |
| **Peak Displacement $u(F_{\max})$** | Displacement at peak load | Fig. 13(a) reference $= 0.0128\,\text{mm}$ ($12.8\,\mu\text{m}$) | *Pending ODB completion* | `PENDING` |
| **Softening Load Drop ($u=20\,\mu\text{m}$)** | Post-peak structural softening | Fig. 13(a) reference: $F=0.0380\,\text{kN}$ ($73.9\%$ drop) | *Pending ODB completion* | `PENDING` |
| **Crack Trajectory Direction** | Oblique path toward bottom-right | Fig. 6(b)/12(b): $\theta_{\text{chord}} \approx -49.3^\circ$, $x_{\text{exit}} \approx 0.930\,\text{mm}$ | *Pending ODB completion* | `PENDING` |
| **Numerical Stability** | Monotonic convergence, 0 abnormal cutbacks | Exit code 0, 0 cutbacks | *Pending ODB completion* | `PENDING` |

---

## 2. Predeclared Acceptance Criteria Audit

*Predeclared in `M2_4_PREDECLARED_ACCEPTANCE_CRITERIA.md` with explicit primary literature grounding:*

- **`M2_4_CHK1_BASE_MESH_PROVENANCE`**: [ ] PASS — $22{,}530$ FEs ($21{,}962$ quads + $568$ tris) across $22{,}642$ nodes from `M2_3_ADAPTED_RAW_2PCT.inp`.
- **`M2_4_CHK2_CONSTITUTIVE_INTEGRITY`**: [ ] PASS — `f42_mixed_uel_mode2_miehe.for` SHA-256 `75029EF7...` unchanged; Mode-I freeze tag intact.
- **`M2_4_CHK3_PHYSICAL_PARAMETERS`**: [ ] PASS — $E=210\,\text{GPa}, \nu=0.3, G_c=2.7\,\text{N/mm}, l_0=15.0\,\mu\text{m}, k=10^{-7}$, virgin intact start ($u=0, d=0$).
- **`M2_4_CHK4_FULL_HORIZON_COMPLETION`**: [ ] PENDING — $4{,}000/4{,}000$ increments across Step-1 and Step-2 to $u_x = 0.0200\,\text{mm}$.
- **`M2_4_CHK5_NUMERICAL_STABILITY`**: [ ] PENDING — 0 cutbacks, smooth Newton convergence across crack initiation and softening.
- **`M2_4_CHK6_PEAK_FORCE_AND_SOFTENING`**: [ ] PENDING — Primary paper $F_{\max} = 0.1455\,\text{kN} \in [0.125, 0.165]\,\text{kN}$, $u(F_{\max}) = 0.0128\,\text{mm} \in [0.0110, 0.0145]\,\text{mm}$, and $F(0.020\,\text{mm}) \le 0.060\,\text{kN}$ (load drop $\ge 60\%$).
- **`M2_4_CHK7_CRACK_TRAJECTORY_OBLIQUENESS`**: [ ] PENDING — Oblique crack path from $(0.5, 0.5)$ toward bottom exit $x_{\text{exit}} \in [0.85, 1.00]\,\text{mm}$ (paper $\sim 0.930\,\text{mm}$), mean chord angle $\theta_{\text{chord}} \in [-60^\circ, -40^\circ]$, peak damage $d_{\max} \ge 0.95$.
- **`M2_4_CHK8_EPISTEMIC_DISCIPLINE`**: [ ] PASS — Exact paper `errorTarget` maintained `UNRESOLVED`; candidate `ET_2PCT` maintained `INFERRED / PROJECT_SELECTED_FOR_M2_4`.

---

## 3. Evaluation Deliverables & Figure Structure

1. **Figure Artifacts:**
   - [`results/figures/mode2/mode2_m2_4_adapted_fracture_evaluation.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode2/mode2_m2_4_adapted_fracture_evaluation.png)
   - [`results/figures/mode2/mode2_m2_4_adapted_fracture_evaluation.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode2/mode2_m2_4_adapted_fracture_evaluation.pdf)
2. **Panels:**
   - **(a) Force-Displacement Response:** Global $F_x - u_x$ curve compared with Pandey & Kumar (2025) Fig. 13(a) (both Adaptive $19{,}963$ and Standard $37{,}155$ curves).
   - **(b) Damage Evolution:** Maximum phase field $d_{\max}(u_x)$ evolution from intact to full fracture ($d \to 1.0$).
   - **(c) Crack Trajectory:** Quantitative $(x, y)$ path from phase field overlaid on Fig. 6(b) corridor and bottom exit $x \approx 0.930\,\text{mm}$.
   - **(d) Snapshot Damage Profiles:** Percentile damage progression across key horizons ($u_x = 9.36, 10.0, 11.84, 16.26, 20.0\,\mu\text{m}$).
