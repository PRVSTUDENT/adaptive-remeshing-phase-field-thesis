# Pre-Job Anti-Deviation Card: Package 46 (PK_M1_COARSE_FINE_CONT)

**Task**: F1481-ADVANCE-PROSPECTIVE-REMESHING-AND-MONITOR-TRIPLE-HPC  
**Date**: 2026-10-15  
**Agent**: Gemini Antigravity  
**Gate**: Gate 6B (Active Prospective Remeshing & Pre-Analysis Exploration)  

---

## 1. Scientific Objective
Evaluate whether increasing spatial resolution in the preliminary coarse linear-elastic pre-analysis mesh ($h = 14.3\,\mu\text{m}$, 4,900 CPE4 quads vs canonical $h = 33.0\,\mu\text{m}$, 2,906 quads/tris) sharpens MISESERI localization or extends prospective adaptive refinement into the uncracked ligament ($x \in [0.5, 1.0]\,\text{mm}$).

## 2. Hypothesis & Predeclared Criteria
- **Physical Hypothesis**: In linear elasticity, the stress singularity is strictly confined to the crack tip $r^{-1/2}$ at $(0.5, 0.5)\,\text{mm}$. Refining the coarse pre-analysis mesh will sharpen the crack-tip error peak and decrease far-field error, but will NOT create prospective refinement along the uncracked ligament ($x > 0.55\,\text{mm}$), because linear elasticity contains no constitutive damage mechanism ahead of the crack tip.
- **Pass Criteria**:
  1. Abaqus solves linear static Step-1 to $u = 0.0050\,\text{mm}$ with Exit 0 in 1-CPU serial.
  2. ODB contains exact `MISESERI` and `MISESAVG` whole-element field outputs.
  3. Crack tip node 2521 $(0.5, 0.5)$ exhibits peak stress and error indicator.
  4. Ligament error decay rate and regional shares extracted and directly contrasted against Package 90 baseline.

## 3. HPC Execution Safeguards
- **Queue**: `entry_imfdfkmq` (1 core, 16 GB RAM, 30 min walltime).
- **Concurrent Job Floor**: Existing 3 jobs (1413217, 1413278, 1413296) remain running untouched.
- **No Overwrite**: Dedicated directory `/scratch9/pr21vyci/runs/mode1_package46_coarse_fine_preanalysis`.
- **Zero UEL Changes**: Pure built-in Abaqus linear elasticity (no UEL required; production UEL remains `CE8D5EDC...`).
