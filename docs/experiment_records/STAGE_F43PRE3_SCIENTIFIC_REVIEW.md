# STAGE F43PRE3 Scientific Review & Reference ODB Comparison Report

**Date**: 2026-08-08  
**Task ID**: `F43PRE3-SCI2` / `F43PRE3_GEOM`  
**PRE3 Job ID**: `1385461.mmaster02`  
**Reference PRE2 Job ID**: `1385392.mmaster02`  
**PRE3 ODB SHA256**: `9a5262931675d2780ccc8b6e6060dd20b817917df7cdf6e499a7a0a2d0d06eb1`  
**PRE2 ODB SHA256**: `85339f45937cf5d2c57f169fa71b3e55f066082e6525aa3c20a370f058c4cf72`  
**Scientific Classification**: `provisional_pass`  

---

## 1. Executive Scientific Summary

A comprehensive read-only ODB extraction and scientific review was conducted comparing the Abaqus-2023 geometry lineage preanalysis run `1385461.mmaster02` (`F43PRE3_GEOM.odb`) against the reference run `1385392.mmaster02` (`F43PRE2_GEOM.odb`). Both runs reached the full target prescribed displacement ($U = 0.0010\text{ mm}$) over 17 increments to step time 1.00.

An explicit reaction force extraction audit was performed resolving the absolute physical resultant force definition:
- **Physical Reaction Force Definition**: The physical applied shear force magnitude is the resultant force on the loaded top boundary ($R_{\text{top}}$). In the previous SCI1 report, summing the absolute value of all reactions across all nodes double-counted the action ($R_{\text{top}} \approx +46.13\text{ N}$) and reaction ($R_{\text{bottom}} \approx -46.13\text{ N}$), reporting $\approx 92.26\text{ N}$.
- **Audited Physical Endpoints**:
  - PRE2 corrected final $RF$: **$46.129372\text{ N}$** (matching the historical baseline $\approx 46.12937\text{ N}$).
  - PRE3 corrected final $RF$: **$46.141109\text{ N}$**.
  - Equilibrium check: $|R_{\text{top}} + R_{\text{bottom}}| = 0.0\text{ N}$ (**PASS**).
- **Relative Comparison Invariant**:
  - $RF-U$ Normalized $L_2$ Relative Error: **$0.025441\%$** ($\le 5.0\%$, **PASS**).
  - Final Reaction Force Relative Error: **$0.025444\%$** ($\le 5.0\%$, **PASS**).
  - Peak Reaction Force Relative Error: **$0.025444\%$** ($\le 5.0\%$, **PASS**).
  - The relative comparison is mathematically unaffected by the factor-of-two scalar double-count.
- **Domain Volume ($EVOL$) Relative Error**: **$2.47 \times 10^{-8}\%$** ($1.0000000005\text{ mm}^3$ vs $1.0000000002\text{ mm}^3$).
- **$MISESERI$ Spatial Correlation**: **$98.95\%$** ($R = 0.98945$).

---

## 2. Field Output & Completeness Audit

All required field outputs are present and verified in `1385461.mmaster02/F43PRE3_GEOM.odb`:
- `U` (Displacement vector): PASS
- `RF` (Reaction force vector): PASS
- `S` (Stress tensor): PASS
- `MISESAVG` (Abaqus averaged Mises stress): PASS
- `MISESERI` (Abaqus stress-discretization error indicator): PASS
- `EVOL` (Element integration volume): PASS

---

## 3. Force-Displacement ($RF-U$) Metrics (Audited Physical Values)

| Metric | Reference PRE2 (`1385392`) | Preanalysis PRE3 (`1385461`) | Relative Error (%) | Gate / Status |
| :--- | :--- | :--- | :--- | :--- |
| **Final Displacement ($U$)** | $0.001000\text{ mm}$ | $0.001000\text{ mm}$ | $0.00\%$ | PASS (Target $0.001\text{ mm}$) |
| **Final Reaction Force ($RF$)** | $46.129372\text{ N}$ | $46.141109\text{ N}$ | $0.0254\%$ | PASS ($\le 5\%$) |
| **Peak Reaction Force ($RF_{\text{peak}}$)** | $46.129372\text{ N}$ | $46.141109\text{ N}$ | $0.0254\%$ | PASS ($\le 5\%$) |
| **$RF-U$ Normalized $L_2$ Error** | - | - | **$0.0254\%$** | PASS ($\le 5\%$) |
| **Equilibrium Residual $|R_{\text{top}}+R_{\text{bot}}|$** | $0.0\text{ N}$ | $0.0\text{ N}$ | - | PASS ($< 10^{-4}\text{ N}$) |

---

## 4. Element Volume ($EVOL$) & Domain Measure

| Field | PRE2 (`1385392`) | PRE3 (`1385461`) | Relative Difference (%) |
| :--- | :--- | :--- | :--- |
| **Summed $EVOL$ ($A \cdot t$)** | $1.000000000225\text{ mm}^3$ | $1.000000000473\text{ mm}^3$ | $2.47 \times 10^{-8}\%$ |

- Both meshes accurately model the exact $1.000\text{ mm} \times 1.000\text{ mm} \times 1.000\text{ mm}$ continuum domain without volume distortion.

---

## 5. Stress Error Indicator ($MISESERI$) Statistics

| Statistic | PRE2 (`1385392`, 3707 elements) | PRE3 (`1385461`, 3716 elements) |
| :--- | :--- | :--- |
| **Finite Count / Total** | 3707 / 3707 | 3716 / 3716 |
| **NaN / Inf Count** | 0 / 0 | 0 / 0 |
| **Minimum** | 0.03486 | 0.04504 |
| **Maximum** | 118.2829 | 126.1344 |
| **Mean** | 1.50259 | 1.50789 |
| **Median** | 1.01690 | 1.04392 |
| **90th Percentile (p90)** | 2.21053 | 2.17445 |
| **95th Percentile (p95)** | 2.92630 | 2.84043 |
| **99th Percentile (p99)** | 11.37550 | 10.08095 |

---

## 6. Spatial $MISESERI$ Distribution Comparison

- **Spatial Correlation Coefficient ($R$)**: **0.98945** (98.95% correlation).
- **Peak $MISESERI$ Location**:
  - PRE2: $(-0.009327, -0.009567)\text{ mm}$
  - PRE3: $(-0.007421, +0.009366)\text{ mm}$
- **Peak Location Spatial Distance**: $0.0190\text{ mm}$ (approx $1.27 l_0$ for $l_0 = 0.015\text{ mm}$). Both peak indicator regions lie at the notch root stress-concentration zone as expected theoretically.

---

## 7. Remeshing Configuration Reconciliation

- **`errorTarget`**: `0.05` (5% relative error threshold).
- **`refinementFactor`**: `0.5`.
- **`minElementSize`**: `0.0075 mm` ($h_{\text{min}}/l_0 = 0.5$ for $l_0 = 0.015\text{ mm}$, working resolution target).
- **`maxElementSize`**: `0.03 mm`.
- **`coarsening_policy`**: **`DISALLOW_COARSENING`** (Coarsening disabled for first irreversible-fracture baseline per project policy).
- **`remesh_passes`**: **`1`** (Single native remeshing pass executed on frozen predecessor ODB).

---

## 8. Decision Gate & Next Actions

- **Scheduler Result**: `PASS`
- **Technical Result**: `PASS`
- **Scientific Result**: **`provisional_pass`**
- **Decision Gate Outcome**: **CASE A** (Proceed to offline native adaptive remeshing preparation `F43REM3_NATIVE`).
- **Authorization Boundary**: `execution_authorized: false`, `submission_approved: false`, `maximum_jobs_now: 0`.
