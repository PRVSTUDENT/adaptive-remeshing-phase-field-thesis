# Stage F43 Experiment Record: Mode-II FRACFIX Uniform Grid Refinement & Censoring Claim Audit

**Task ID:** `F43MODEREF13-PAIR2-CENSORING-CLAIMAUDIT1`  
**Stage:** Stage F (Mode-II Pure-Shear Benchmark)  
**Package:** `models/generated/mode_ii/reference_convergence/M2REF_H1_FRACFIX`, `M2REF_H2_FRACFIX`, `M2REF_H0_NPHYSFIX_REPRO`  
**Submission SHA:** `20462bdc692f4459ae9885d6f4c18128f873c253`  
**Execution Host:** `tu_freiberg` cluster (`normal_imfdfkmq` via `entry_imfdfkmq`)  

---

## 1. Executive Summary & Censoring Audit

Jobs `1386447.mmaster02` ($H_1$) and `1386448.mmaster02` ($H_2$) constitute the Mode-II FRACFIX uniform grid refinement batch. This experiment tests phase-field fracture under pure shear loading across three uniform mesh levels:
- **$H_0$ Baseline:** $N_{\text{phys}} = 3,930$ physical elements ($h \approx 0.030\text{ mm}$, $h/l_0 = 2.0$), Job `1386372.mmaster02` (completed prescribed loading to $u_1 = 0.0100\,\text{mm}$).
- **$H_1$ Refinement:** $N_{\text{phys}} = 12,064$ physical elements ($h \approx 0.015\text{ mm}$, $h/l_0 = 1.0$), Job `1386447.mmaster02` (terminated at Step-2 inc 1854, $u_1 = 0.009632\,\text{mm}$, due to fixed-increment solver divergence).
- **$H_2$ Ultra-Fine:** $N_{\text{phys}} = 33,852$ physical elements ($h \approx 0.0075\text{ mm}$, $h/l_0 = 0.5$), Job `1386448.mmaster02` (terminated at Step-2 inc 1743, $u_1 = 0.009250\,\text{mm}$, due to 4-hour PBS limit).

### Peak Censoring Classification
Both $H_1$ and $H_2$ terminated while their reaction force curves were still monotonically rising (positive terminal slopes: $+15.81\,\text{kN/mm}$ for $H_1$, $+18.41\,\text{kN/mm}$ for $H_2$). Therefore:
- The maximum observed forces ($361.66\,\text{N}$ for $H_1$, $354.08\,\text{N}$ for $H_2$) are **censored by termination**, not completed interior maximum peaks.
- `global_peak_force_convergence = UNRESOLVED_CENSORED_BY_TERMINATION`
- `full_postpeak_uniform_convergence = UNRESOLVED`
- Valid like-for-like comparison is strictly conducted over the common evaluation window:
  $$0 \le u_1 \le 0.009250\,\text{mm} \quad (9.25\,\mu\text{m}).$$

---

## 2. Scheduler Performance & Primary Cost Provenance

| Metric | $H_0$ Baseline (`1386372`) | $H_1$ Job (`1386447`) | $H_2$ Job (`1386448`) | Status |
| :--- | :--- | :--- | :--- | :--- |
| **PBS State** | `F` (Finished) | `F` (Finished) | `F` (Finished) | Terminal |
| **Exit Status** | `0` (Completed $10\,\mu\text{m}$) | `1` (Solver divergence at $9.63\,\mu\text{m}$) | `-29` (Walltime 4h at $9.25\,\mu\text{m}$) | Audited |
| **Execution Host** | `mnode099/0` | `mnode099/0` | `mnode099/1` | Recorded |
| **Allocated Resources** | 1 CPU, 8 GB, 01:00:00 | 1 CPU, 8 GB, 02:00:00 | 1 CPU, 8 GB, 04:00:00 | Matched |
| **Walltime Used** | 2004.0 s (00:33:24) | 5453.0 s (01:30:53) | 14501.0 s (04:01:41) | Exact Scheduler |
| **CPU Time Used** | 2000.0 s (00:33:20) | 5434.0 s (01:30:34) | 14455.0 s (04:00:55) | Exact Solver |
| **Peak RAM / VMEM** | 2048.0 MB / --- | 955.8 MB / 3337.0 MB | 1783.0 MB / 7551.0 MB | Recorded |
| **CPU Cost Ratio vs $H_0$** | $1.00\times$ | $2.72\times$ | $7.23\times$ | Reconciled |
| **CPU Cost Ratio ($H_2/H_1$)** | --- | --- | $2.66\times$ | Reconciled |

---

## 3. Reconciled Linear Elastic and Damage Initiation Metrics

| Scientific Metric | $H_0$ Baseline (`1386372`) | $H_1$ Refinement (`1386447`) | $H_2$ Refinement (`1386448`) | Convergence / Parity |
| :--- | :--- | :--- | :--- | :--- |
| **Physical Elements ($N_{\text{phys}}$)** | 3,930 | 12,064 | 33,852 | Refinement ratio $3.07\times$ / $8.61\times$ |
| **Mesh Density ($h/l_0$)** | $2.0$ | $1.0$ | $0.5$ | Fine zone |
| **Initial Stiffness $K_0$ (Origin OLS)** | $46.1396\text{ kN/mm}$ | $45.9035\text{ kN/mm}$ | $45.8741\text{ kN/mm}$ | $\mathbf{-0.064\%}$ ($H_2$ vs $H_1$), $-0.575\%$ ($H_2$ vs $H_0$) |
| **Linear Fit Linearity ($R^2$)** | $0.999996$ | $0.999996$ | $0.999996$ | Unified fit on $u_1 \le 2\,\mu\text{m}$ |
| **Initiation Displ. $u_1(d \ge 0.5)$** | $0.008250\text{ mm}$ | $0.007750\text{ mm}$ | $0.007750\text{ mm}$ | **Exact match** between $H_1$ & $H_2$ ($7.75\,\mu\text{m}$) |
| **Broken Displ. $u_1(d \ge 0.9)$** | $0.008750\text{ mm}$ | $0.008500\text{ mm}$ | $0.008000\text{ mm}$ | Sharper localization on fine mesh |
| **Matched Endpoint Force $RF_1(9.25\,\mu\text{m})$** | $0.359812\text{ kN}$ | $0.355641\text{ kN}$ | $0.354084\text{ kN}$ | $\mathbf{-0.44\%}$ ($H_2$ vs $H_1$), $-1.59\%$ ($H_2$ vs $H_0$) |
| **Matched Endpoint Damage $d_{\max}(9.25\,\mu\text{m})$** | $0.97815$ | $0.99553$ | $0.99847$ | Localized crack state |
| **Matched Crack Hausdorff ($H_2$ vs $H_1$)** | --- | --- | $0.005443\text{ mm}$ | Computed at $u_1 = 9.25\,\mu\text{m}$ |

---

## 4. Common-Window Quantitative Convergence ($0 \le u_1 \le 0.00925\text{ mm}$)

- **Common-Window Normalized $L_2$ Error:**
  - $H_1$ vs $H_0$: $1.363\%$ (`PASS` $\le 2.0\%$)
  - $H_2$ vs $H_1$: $\mathbf{0.518\%}$ (`PASS` $\le 2.0\%$)
  - $H_2$ vs $H_0$: $1.802\%$ (`PASS` $\le 2.0\%$)
- **Common-Window Curve Area (Work) Error:**
  - $H_1$ vs $H_0$: $0.943\%$
  - $H_2$ vs $H_1$: $\mathbf{0.263\%}$
  - $H_2$ vs $H_0$: $1.203\%$

---

## 5. Scoped Scientific Resolutions

```text
pre_peak_mesh_refinement_consistency = PASS
damage_initiation_mesh_consistency = PASS
H1_as_minimum_prepeak_comparison_mesh = SUPPORTED
full_postpeak_uniform_convergence = UNRESOLVED
global_peak_force_convergence = UNRESOLVED_CENSORED_BY_TERMINATION
energy_convergence = UNRESOLVED
full_crack_path_convergence = UNRESOLVED
adaptive_remeshing_computational_motivation = STRONGLY_SUPPORTED
recommended_reference_resolution_for_prepeak = H1
recommended_reference_resolution_for_complete_fracture = UNRESOLVED
```
