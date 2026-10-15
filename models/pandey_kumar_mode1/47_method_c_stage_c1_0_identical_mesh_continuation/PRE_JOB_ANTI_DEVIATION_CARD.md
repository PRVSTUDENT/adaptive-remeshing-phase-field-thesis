# Pre-Job Anti-Deviation Qualification Card: Package 47
## Stage C1-0: Mode-I Method C Identical-Mesh State Transfer & Continuation

- **Task ID:** F1482
- **Agent:** Gemini Antigravity
- **Date:** 2026-10-15
- **Input Deck:** `M1_MC_STAGE_C1_0_RECONSTRUCT.inp` (SHA-256: `8B417E7FC5F5612DD6C8E128036CC5799E074BCA5E7191E9324789A91D700A67`)
- **User Subroutine:** `f42_mixed_uel.for` (SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)
- **Discretization:** Canonical 2,906-element Mode-I mesh (identical-mesh control)
- **Handoff Point:** $u_{handoff} = 0.0050\,\text{mm}$ (from Job 1411891 / Package 40 Step 1)
- **Stage C1-0A (Equilibration):** Instantaneous static solve at $u = 0.0050\,\text{mm}$ ($\Delta u = 0$)
- **Stage C1-0B (Continuation):** Fracture propagation solve from $u = 0.0050\,\text{mm}$ to $0.0100\,\text{mm}$
- **Expected Step 1 Reaction Force:** $653.0886\,\text{N}$ ($|\Delta RF| < 0.1\,\text{N}$ target)
- **Expected Step 1 Internal Energy:** $1.66338\,\text{mJ}$ ($|\Delta E_{int}| / E_{int} < 0.1\%$ target)
- **Expected Step 1 Iterations:** 1 iteration (exact equilibrium)
- **HPC Configuration:** 1 CPU serial, 16 GB RAM, 12h walltime in `normal_imfdfkmq`
- **Execution Target:** `/scratch9/pr21vyci/runs/mode1_stage_c1_0_continuation/`
