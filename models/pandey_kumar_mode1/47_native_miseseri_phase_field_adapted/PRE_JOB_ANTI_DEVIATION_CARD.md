# Pre-Job Anti-Deviation Card: Package 47 (PK_M1_NATIVE_ADAPTED_2PCT)

**Task**: F1585-QUALIFY-NATIVE-ADAPTIVE-MESH-AND-SUBMIT-MODE1-PHASE-FIELD  
**Date**: 2026-10-18  
**Agent**: Gemini Antigravity  
**Gate**: Gate 6B (Adaptive Mode-I Full-Scale Fracture Simulation) / Method B Native Verification  

---

## 1. Scientific Objective
Execute the full-scale Mode-I phase-field fracture simulation on the 12,369-element adapted mesh produced by native Abaqus/CAE 2023 `adaptiveRemesh` driven by the linear-elastic `MISESERI` error indicator field from Job 1415074 (`PK_M1_COARSE_FINE_CONT.odb`). Contrast mechanical compliance ($K_0$), peak load ($F_{\max}$), crack-tip localization, and global energy balance against the 15,192-element structured baseline (Job 1398090) and the 71,320-element fine benchmark (Job 1404933/1405044).

## 2. Hypothesis & Predeclared Criteria
- **Physical Hypothesis**: A native MISESERI-guided mesh with 2.0% error target (12,369 elements, $h_{\mathrm{tip}} = 45.96\,\mu\mathrm{m}$, 67 duplicate node pairs along the sharp slit) will recover the correct Mode-I initial structural compliance ($K_0 \approx 138\,\mathrm{kN/mm}$ within $\pm 3\%$), achieve stable crack initiation, and propagate a horizontal crack along $y = 0.5\,\mathrm{mm}$ with monotonic fracture energy dissipation without non-physical stiffness loss.
- **Pass Criteria**:
  1. Abaqus 2023 datacheck completes with Exit 0 and zero errors (verified: `PK_M1_NATIVE_ADAPTED_2PCT.dat` SHA256: `76C66192...`).
  2. Solves monotonic tensile loading across Step 1 ($u \to 0.0050\,\mathrm{mm}$) and Step 2 ($u \to 0.0100\,\mathrm{mm}$) with 1 CPU serial in queue `entry_imfdfkmq`.
  3. Linear-elastic stiffness $K_0$ matches reference ($137.95\,\mathrm{kN/mm}$) within $\pm 3.0\%$.
  4. Global energy balance satisfies bookkeeping consistency ($\Delta_{\mathrm{book}} / W_{\mathrm{ext}} \le 2.0\%$ pre-peak).
  5. Peak reaction force $F_{\max}$ and displacement $u(F_{\max})$ align with Mode-I benchmark trends.

## 3. HPC Execution Safeguards
- **Queue**: `entry_imfdfkmq` (1 CPU, 16 GB RAM, 08:00:00 walltime).
- **Execution Mode**: Single-rank serial (1 CPU) under bitwise-frozen production UEL `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
- **Dedicated Directory**: `/scratch9/pr21vyci/runs/mode1_package47_native_adapted_pfm`.
- **Preflight**: Technical preflight verifies unchanged input hash, UEL hash, notification traps, live queue capacity (< 4 active jobs), and input-bound datacheck pass.
