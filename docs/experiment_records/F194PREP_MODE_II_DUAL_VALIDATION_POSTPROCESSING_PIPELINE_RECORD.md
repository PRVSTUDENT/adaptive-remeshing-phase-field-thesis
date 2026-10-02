# Mode-II Dual Validation Postprocessing Pipeline Preparation & Offline Software Qualification Record

**Task ID**: `F194PREP-M2-DUAL-VALIDATION-POSTPROCESSING-PIPELINE1`  
**Date**: 16 August 2026  
**Status**: `QUALIFIED / READY FOR PRODUCTION VALIDATION JOBS`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

This record documents the preparation, verification, and deterministic offline qualification of the scientific postprocessing and evaluation pipeline for the two upcoming validation jobs in the Mode-II dual validation batch:
1. **`M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6`** (4-stage same-mesh restart mechanics validation)
2. **`M2CORR_PK10R2_TOPOLOGY_CORRECTED`** (Restored physical notch topology validation)

The evaluation tools operate deterministically without requiring live HPC submissions or altering frozen input packages. Offline software qualification confirmed **0.00% reproduction error** against accepted historical benchmarks (`1389686.mmaster02`, `1389687.mmaster02`, and `1389684.mmaster02`).

---

## 2. Authoritative Reference Provenance & Superseded Lineage Exclusion

### 2.1 Accepted Ground-Truth References (The ~0.29 kN Lineage)
- **H1 Reference**: `1389686.mmaster02` (`M2CORR_H1_FREEU2_FULL_U050`)
  - Minimum mesh size: $h_{\min} = 0.0020\text{ mm}$ (12,064 physical elements)
  - Initial elastic stiffness: $K_0 = \mathbf{529.67\text{ kN/mm}}$
  - Peak reaction force: $RF_{1,\max} = \mathbf{0.29957\text{ kN}}$ ($299.57\text{ N}$)
  - Peak displacement: $U_{1,\text{peak}} = \mathbf{0.000627\text{ mm}}$
  - Boundary Condition: `top U2 FREE`
- **H2 Reference**: `1389687.mmaster02` (`M2CORR_H2_FREEU2_FULL_U050`)
  - Minimum mesh size: $h_{\min} = 0.0010\text{ mm}$ (33,852 physical elements)
  - Initial elastic stiffness: $K_0 = \mathbf{529.01\text{ kN/mm}}$
  - Peak reaction force: $RF_{1,\max} = \mathbf{0.29483\text{ kN}}$ ($294.83\text{ N}$)
  - Peak displacement: $U_{1,\text{peak}} = \mathbf{0.000616\text{ mm}}$
  - Boundary Condition: `top U2 FREE`
- **Spatial Mesh Convergence**: Relative stiffness difference between H1 and H2 is $\mathbf{0.12\%}$; peak reaction force difference is $\mathbf{1.58\%}$. Formally accepted in Task `F136DIAG` as the sole authoritative Mode-II reference baseline.

### 2.2 Replay Ground-Truth Reference for Restart
- **Replay Run**: `1389707.mmaster02` (`M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1`)
- **Canonical Primary-State CSV SHA256**: `5a2313e1ed15834d933e7cd12808681bd554394ad64d58419ad85f6f2bf6cf69`
- **Committed Source-State Binary SHA256**: `28e0fc1c6b02a4e6013cea23f38dacfea0e2afaf52d92239d9d694bb2e55e66e`
- **Handoff Displacement**: $u_{1,\text{handoff}} = 0.010143300518393517\text{ mm}$
- **Accepted Handoff Reaction Force**: $RF_{1,\text{handoff}} = 0.30542629957199097\text{ kN}$
- **Continuous Terminal Reaction Force ($u_1 = 0.050\text{ mm}$)**: $RF_{1,\text{term}} = 0.003639\text{ kN}$

### 2.3 Exclusion of Superseded ~0.859 kN Lineage
- **Superseded Lineage**: Jobs `1389351.mmaster02`, `1389352.mmaster02`, and `1389685.mmaster02` ($RF_1 \approx 0.859\text{ kN}, K_0 \approx 1839\text{ kN/mm}$).
- **Provenance**: Incurred artificial stiffness and force inflation from clamped vertical boundary conditions (`top U2 fixed to 0`) and obsolete degraded driving energy.
- **Scientific Protocol**: **Explicitly excluded**. All scientific evaluations for `M2CORR_PK10R2_TOPOLOGY_CORRECTED` must be conducted strictly against `1389686` (H1) and `1389687` (H2).

---

## 3. Tooling Architecture & Methodology

### 3.1 Evaluator Tools
1. **`scripts/postprocessing/evaluate_m2corr_pk10r2_topology.py`**:
   - Evaluates PK10R2 against H1 and H2.
   - Computes initial stiffness $K_0$ via the standard project definition: Frame 1 linear elastic secant $K_0 = RF_1(1) / U_1(1)$ with auxiliary linear regression.
   - Determines peak reaction force, peak displacement, terminal values, and comparative differences.
   - Categorizes topology outcome into:
     - `TOPOLOGY_DEFECT_CLEARLY_REDUCED`
     - `TOPOLOGY_DEFECT_NOT_REDUCED`
     - `TOPOLOGY_RESULT_AMBIGUOUS`
     - `UNRESOLVED`
2. **`scripts/postprocessing/evaluate_m2corr_pk10r1_samemesh_r6.py`**:
   - Evaluates R6 restart mechanics across four distinct stages:
     - Stage 1: `STATE_INSTALL` (Handoff equilibrium at $u_1 = 0.010143\text{ mm}$, threshold $\le 1.0\%$)
     - Stage 2: `MECH_EQUILIBRATION` (Mechanical clamp release jump, threshold $\le 1.0\%$)
     - Stage 3: `PHASE_RELEASE` (Phase clamp release jump $\le 1.0\%$, pointwise phase healing $\Delta d \ge -10^{-6}$)
     - Stage 4: `CONTINUATION` (Terminal post-peak force at $u_1 = 0.050\text{ mm}$, threshold $\le 2.0\%$)
3. **`scripts/postprocessing/extract_validation_odb.py`**:
   - Abaqus Python script extracting reaction force $RF_1$, reference displacement $U_1$, and max phase damage $d_{\max}$ directly from `.odb` into structured CSV.
4. **`scripts/postprocessing/dual_validation_pipeline.py`**:
   - Unified command-line dispatcher.

### 3.2 Standard Units & Interpolation Rules
- **Units**:
  - Length / Displacement: $\text{mm}$
  - Force: $\text{kN}$ ($1\text{ kN} = 1000\text{ N}$)
  - Stiffness: $\text{kN/mm}$
  - Stress / Modulus: $\text{kN/mm}^2$ ($1\text{ kN/mm}^2 = 1\text{ GPa} = 1000\text{ MPa}$)
  - Energy / Toughness: $\text{kN/mm}$ ($1\text{ kN/mm} = 1\text{ kJ/m}^2 = 1000\text{ J/m}^2 = 1\text{ N/mm}$)
- **Interpolation Rules**:
  - Piecewise linear interpolation between exact discrete frames.
  - Evaluation restricted strictly to the overlapping displacement domain $[u_{\min}, u_{\max}]$.
  - **Zero extrapolation**: Trajectories outside the recorded domain are marked `UNRESOLVED`.

---

## 4. Offline Software Qualification Results

The evaluation pipeline was qualified against historical evidence on the cluster:

| Test ID | Target Historical Job | Metric | Extracted Value | Expected Reference | Relative Error | Qualification Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TEST_01` | `1389686.mmaster02` (H1) | $K_0$ | $529.67\text{ kN/mm}$ | $529.67\text{ kN/mm}$ | $\mathbf{0.00\%}$ | **PASS** |
| `TEST_01` | `1389686.mmaster02` (H1) | $RF_{1,\max}$ | $0.29957\text{ kN}$ | $0.29957\text{ kN}$ | $\mathbf{0.00\%}$ | **PASS** |
| `TEST_02` | `1389687.mmaster02` (H2) | $K_0$ | $529.01\text{ kN/mm}$ | $529.01\text{ kN/mm}$ | $\mathbf{0.00\%}$ | **PASS** |
| `TEST_02` | `1389687.mmaster02` (H2) | $RF_{1,\max}$ | $0.29483\text{ kN}$ | $0.29483\text{ kN}$ | $\mathbf{0.00\%}$ | **PASS** |
| `TEST_03` | `1389684.mmaster02` (PK10R1) | $K_0$ | $639.80\text{ kN/mm}$ | $639.80\text{ kN/mm}$ | $\mathbf{0.00\%}$ | **PASS** |
| `TEST_03` | `1389684.mmaster02` (PK10R1) | $RF_{1,\max}$ | $0.38324\text{ kN}$ | $0.38324\text{ kN}$ | $\mathbf{0.00\%}$ | **PASS** |
| `TEST_04` | `1389715.mmaster02` (R2 Restart) | Handoff $RF_1$ | $0.30630\text{ kN}$ | $0.30543\text{ kN}$ | $+0.29\%$ | **PASS** |
| `TEST_04` | `1389715.mmaster02` (R2 Restart) | Mech Release Jump | $+5.93\%$ | $> 5.0\%$ (Defect) | $\text{Detected}$ | **PASS** |
| `TEST_04` | `1389715.mmaster02` (R2 Restart) | Phase Healing | $\text{Detected}$ | $\text{True}$ (Defect) | $\text{Detected}$ | **PASS** |

---

## 5. Artifact Hashes

| Artifact Path | SHA256 Hash |
| :--- | :--- |
| `scripts/postprocessing/evaluate_m2corr_pk10r2_topology.py` | `710fa35b2a193ffa8ae94924b5ada664ab954600695df7e731dc9cdf285e95b6` |
| `scripts/postprocessing/evaluate_m2corr_pk10r1_samemesh_r6.py` | `dd139ec6b3368f2a0f100dddf65661be0084c956bd033b8048a2fb2ff3ee7e63` |
| `scripts/postprocessing/extract_validation_odb.py` | `8f5dd4bd8479818b9ca3e591fd55a561ae29a37f4d8bd9abd65a9f2a09b1bc59` |
| `scripts/postprocessing/dual_validation_pipeline.py` | `19b878fbd444776f2e84025f987612bf920bbd8c4b26d5cfe22cee1b3908e31e` |
| `scripts/postprocessing/offline_qualify_pipeline.py` | `f1885835e002359bbf3fcbcc664eef550502d7bfd2377628fa03e6248c68e505` |
| `runs/hpc/mode_ii_control_batch/evidence/QUALIFICATION_H1_1389686_TOPOLOGY_REPORT.json` | `8d70a8f07c1169f81b13cd2114daab5736f28d10b2b9a2a4c6b57aabb24ccff2` |
| `runs/hpc/mode_ii_control_batch/evidence/QUALIFICATION_H2_1389687_TOPOLOGY_REPORT.json` | `0829d3e5f21b7ab2f40083ca69e1684367622fca94cf6c806fb6b5a9451fffc5` |
| `runs/hpc/mode_ii_control_batch/evidence/QUALIFICATION_PK10R1_1389684_TOPOLOGY_REPORT.json` | `5f3dd5cf00162c29a8fe8e9855b488a6a261faa1681df7237a1bb976eb520f4d` |
| `runs/hpc/mode_ii_control_batch/evidence/QUALIFICATION_RESTART_R2_1389715_REPORT.json` | `dd27857da0d03cbd70a0effa2a0bfe2c2ea1d2aa03a067ea649a46294d3731cf` |
| `runs/hpc/mode_ii_control_batch/evidence/DUAL_VALIDATION_PIPELINE_SOFTWARE_QUALIFICATION_SUMMARY.json` | `5c2c830e21f83c5a0e9886f036c9fea4c0b44c36b981ef06bf708fb4af104101` |

---

## 6. Execution Instructions for Future Validation Jobs

Once jobs are completed on the HPC cluster:

### For R6 Same-Mesh Restart:
```bash
python3 scripts/postprocessing/evaluate_m2corr_pk10r1_samemesh_r6.py \
  --candidate-dir models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6 \
  --output-json runs/hpc/mode_ii_control_batch/evidence/R6_SAMEMESH_EVALUATION_REPORT.json
```

### For PK10R2 Corrected Topology:
```bash
python3 scripts/postprocessing/evaluate_m2corr_pk10r2_topology.py \
  --candidate-dir models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED \
  --output-json runs/hpc/mode_ii_control_batch/evidence/PK10R2_TOPOLOGY_EVALUATION_REPORT.json
```

### Or using Unified Pipeline Dispatcher:
```bash
python3 scripts/postprocessing/dual_validation_pipeline.py \
  --job-dir <JOB_DIRECTORY_PATH> \
  --output-json <OUTPUT_JSON_PATH>
```
