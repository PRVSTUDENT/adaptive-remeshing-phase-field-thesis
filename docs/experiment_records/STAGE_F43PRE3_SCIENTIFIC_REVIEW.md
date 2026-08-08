# STAGE F43PRE3 Scientific Review & Reference ODB Comparison Report

**Date**: 2026-08-08  
**Task ID**: `F43PRE3-SCI1` / `F43PRE3_GEOM`  
**PRE3 Job ID**: `1385461.mmaster02`  
**Reference PRE2 Job ID**: `1385392.mmaster02`  
**PRE3 ODB SHA256**: `9a5262931675d2780ccc8b6e6060dd20b817917df7cdf6e499a7a0a2d0d06eb1`  
**PRE2 ODB SHA256**: `85339f45937cf5d2c57f169fa71b3e55f066082e6525aa3c20a370f058c4cf72`  
**Scientific Classification**: `provisional_pass`  

---

## 1. Executive Scientific Summary

A comprehensive read-only ODB extraction and scientific review was conducted comparing the Abaqus-2023 geometry lineage preanalysis run `1385461.mmaster02` (`F43PRE3_GEOM.odb`) against the reference run `1385392.mmaster02` (`F43PRE2_GEOM.odb`). Both runs reached the full target prescribed displacement ($U = 0.0010\text{ mm}$) over 17 increments to step time 1.00. 

The mechanical reaction force curve ($RF-U$), element domain volume ($EVOL$), and stress error indicator statistics ($MISESERI$) demonstrate exceptional consistency across mesher lineages:
- **$RF-U$ Normalized $L_2$ Relative Error**: **$0.0254\%$** (well within provisional gate $\le 5\%$).
- **Final Reaction Force Relative Error**: **$0.0254\%$** ($92.2822\text{ N}$ vs $92.2587\text{ N}$).
- **Domain Volume ($EVOL$) Relative Error**: **$2.47 \times 10^{-8}\%$** ($1.0000000005\text{ mm}^2$ vs $1.0000000002\text{ mm}^2$).
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

## 3. Force-Displacement ($RF-U$) Metrics

| Metric | Reference PRE2 (`1385392`) | Preanalysis PRE3 (`1385461`) | Relative Error (%) | Gate / Status |
| :--- | :--- | :--- | :--- | :--- |
| **Final Displacement ($U$)** | $0.001000\text{ mm}$ | $0.001000\text{ mm}$ | $0.00\%$ | PASS (Target $0.001\text{ mm}$) |
| **Final Reaction Force ($RF$)** | $92.2587\text{ N}$ | $92.2822\text{ N}$ | $0.0254\%$ | PASS ($\le 5\%$) |
| **Peak Reaction Force ($RF_{\text{peak}}$)** | $92.2587\text{ N}$ | $92.2822\text{ N}$ | $0.0254\%$ | PASS ($\le 5\%$) |
| **$RF-U$ Normalized $L_2$ Error** | - | - | **$0.0254\%$** | PASS ($\le 5\%$) |

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

## 7. Decision Gate & Next Actions

- **Scheduler Result**: `PASS`
- **Technical Result**: `PASS`
- **Scientific Result**: **`provisional_pass`**
- **Decision Gate Outcome**: **CASE A** (Proceed to offline native adaptive remeshing preparation `F43REM3_NATIVE`).
