# Mode-II PK10R2 Frozen Mesh Identity and Authorization Consistency Audit Record

**Task ID**: `F203AUDIT-M2-PK10R2-FROZEN-MESH-IDENTITY-AND-AUTHORIZATION-CONSISTENCY1`  
**Date**: 16 August 2026  
**Status**: `AUDIT COMPLETED / MESH METRICS VERIFIED / DOCUMENTATION HARMONIZED / MANIFEST UPDATED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

This record provides the rigorous offline audit of the frozen `M2CORR_PK10R2_TOPOLOGY_CORRECTED` mesh. All metric discrepancies between earlier records and F202 have been completely resolved from actual node coordinates and element connectivity in the frozen INP deck (`667897fc...`). The generator was proven to reproduce the frozen INP byte-identically.

---

## 2. Quantitative Mesh Metrics Reconciliation

| Metric Description | Exact Audited Value | Prior Conflicting Report | Classification |
| :--- | :--- | :--- | :--- |
| **Local Process-Zone Size ($h_{\text{local}}$)** | `0.005000 mm` | `0.010 mm` (in F202) | `0.005 mm` is **`CORRECT_MESH_METRIC`** (`0.010` was **`DOCUMENTATION_ERROR`**) |
| **Global Coarse Size ($h_{\text{global}}$)** | `0.025000 mm` | `0.050 mm` (in F202) | `0.025 mm` is **`CORRECT_MESH_METRIC`** (`0.050` was **`DOCUMENTATION_ERROR`**) |
| **Coarse/Fine Ratio ($h_{\text{max}}/h_{\text{min}}$)** | `5.000000` | `5.0` (in F202) | **`CORRECT_BUT_DIFFERENT_DEFINITION`** (Global domain grading ratio) |
| **Max Adjacent Neighbor Size Ratio** | `1.224745` | `<= 1.5` | **`CORRECT_MESH_METRIC`** ($1.2247 \le 1.5$) |
| **Maximum Element Aspect Ratio** | `5.000000` | `~5` | **`CORRECT_MESH_METRIC`** |
| **Physical Nodes** | `6249` | `6249` | **`CORRECT_MESH_METRIC`** |
| **Auxiliary RP Nodes** | `1` (Node 99999) | `0` | **`CORRECT_MESH_METRIC`** (Total *NODE records = 6250) |
| **Physical Quad Elements** | `6048` | `6048` | **`CORRECT_MESH_METRIC`** |
| **Total Layered Elements** | `18144` | `18144` | **`CORRECT_MESH_METRIC`** (6048 U1 + 6048 U2 + 6048 CPE4) |
| **Slit Split Stations ($x < 0, y = 0$)** | `26` | `26` | **`CORRECT_MESH_METRIC`** ($52$ duplicate nodes) |
| **Crack Tip Node at $x = 0$** | `1` (Node 3101) | `1` | **`CORRECT_MESH_METRIC`** |
| **Slit Cross-Connectivity** | `NO` | `NO` | **`CORRECT_MESH_METRIC`** (Proper physical open slit) |
| **Intact Ligament ($x > 0$)** | `Continuous` | `Continuous` | **`CORRECT_MESH_METRIC`** (Single-node connected across all 100 stations) |

---

## 3. Generator Reproducibility Audit

- **Generator Script**: `scripts/model_generation/build_pk10r2_corrected_topology_candidate.py`
- **Reproduction Output**: `M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp` generated into `/tmp/pk10r2_test`
- **Frozen Hash**: `667897fc42ee134be434cb5bc543796ce47ffd2024ec4d6c01d20e0abbd987be`
- **Generated Hash**: `667897fc42ee134be434cb5bc543796ce47ffd2024ec4d6c01d20e0abbd987be`
- **Status**: **`BYTE_IDENTICAL`**

---

## 4. Frozen Hashes Post-Correction

- `INP` (`M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp`): `667897fc42ee134be434cb5bc543796ce47ffd2024ec4d6c01d20e0abbd987be` (**100% UNCHANGED**)
- `UEL` (`f42_mixed_uel.for`): `e0865b5eba43c14d21a733e72717e157d65c778319e6556e5eca8ab222364e58` (**100% UNCHANGED**)
- `Launcher` (`submit_job.sh`): `3532540a3c56c5e2a1baaf43d46c33ec71fc31f76dffde5eb9c7602291bffea4` (**100% UNCHANGED**)
- `Manifest` (`manifest.json`): `dbf20366ab9ad5aed4f5fc67c1d646d1480376e787b819098666d7fdbfa3f426` (**DOCUMENTATION_METADATA_ONLY**)
