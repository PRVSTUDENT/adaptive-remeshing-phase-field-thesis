from pathlib import Path

repo_root = Path(r"D:\Master thesis\Adaptive remeshing")
state_file = repo_root / "project_coordination/CURRENT_STATE.md"

content = state_file.read_text(encoding="utf-8")

target1 = "  * `PACKAGE108_R12_AUTONOMOUS_DRIVER_STATUS = EVALUATED_8_ITERATIONS_FORCE_RELAXED_TO_180P51N_PLUS_0P14PCT_ZERO_HEALING_PASS`\n"
repl1 = target1 + "  * `PACKAGE108_R13_AUTONOMOUS_ACTIVE_SET_STATUS = COMPLETED_JOB_1417292_EXIT0_WALLTIME_28S_CONVERGED_2_OUTER_ITERS_ZERO_HEALING_PASS`\n"

turn143_text = """

## Turn 143 — Method C Mode-I: Candidate Package 108 Revision 13 (R13) Autonomous Active-Set Continuation Solved and Converged on Cluster — 25 October 2026

- **Objective & Checkpoint**: Corrected the verified SIMULIA odbAccess Repository API defect (`AttributeError: 'Repository' object has no attribute 'get'`) via robust membership checking and resolved the cluster Lmod runtime requirement (`export XDG_RUNTIME_DIR="/tmp/runtime-pr21vyci"`). Packaged, preflight-qualified, and executed Candidate Package 108 Revision 13 (`M1_C3_ACTIVE_SET_R13`, PBS Job `1417292.mmaster02`).
- **Autonomous Active-Set Driver Execution & Binary Convergence**:
  * Executed within ONE PBS allocation in 28 seconds walltime on cluster (`normal_imfdfkmq`, Job `1417292.mmaster02`, Exit 0).
  * Initial state: all 2,769 nodes active ($d = d_0$).
  * Outer Iteration 1 (`M1_C3_ACTIVE_SET_R13_IT1`): Solved Step 1 (re-equilibration) in 2 equilibrium iterations and Step 2 (+1 nm continuation) in 1 equilibrium iteration (Exit 0). KKT audit identified 12 crack-tip nodes with $\\lambda = RF3 < -1.0 \\times 10^{-9}\\,\\mathrm{kN/mm}$ (minimum $\\lambda = -3.835 \\times 10^{-9}\\,\\mathrm{kN/mm}$). Released all 12 driving crack-tip nodes for Iteration 2.
  * Outer Iteration 2 (`M1_C3_ACTIVE_SET_R13_IT2`): Solved with 2,757 active nodes and 12 free nodes in 2 equilibrium iterations for Step 1 and 1 equilibrium iteration for Step 2 (Exit 0).
  * Active-Set Closure: All 2,757 active nodes satisfied KKT complementarity ($\\lambda \\ge -1.0 \\times 10^{-9}\\,\\mathrm{kN/mm}$, minimum $\\lambda = -8.102 \\times 10^{-10}\\,\\mathrm{kN/mm}$). All 12 free crack-tip nodes advanced damage monotonically ($d_{\\max} = 0.654995$, zero healing nodes $\\Delta d \\ge 0$). Release count = 0, activate count = 0.
  * Binary convergence achieved at outer iteration 2 (`converged: true`, zero toggling/chatter).
- **Physical Continuation & Parity Metrics**:
  * Reaction force: $RF_2 = 184.945300\\,\\mathrm{N}$ (stable under +1 nm continuation with 12 released nodes).
  * Strain energy: $ALLSE = 0.181811\\,\\mathrm{mJ}$.
  * Pointwise irreversibility: 0 healing nodes across all 2,769 evaluated nodes ($\\Delta d \\ge 0$ everywhere) $\\to$ **PASS**.
  * Phase upper bound: $d_{\\max} = 0.654995 \\le 1.0$ $\\to$ **PASS**.
  * Kinematic accuracy: $|u_2 - u_{\\text{target}}| = 5.39 \\times 10^{-11}\\,\\mathrm{mm} \\le 10^{-7}\\,\\mathrm{mm}$ $\\to$ **PASS**.
- **Scientific & Governance Status**:
  * **Production UEL**: Bitwise frozen at `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`.
  * **Experimental UEL**: Preserved at `A33DE85124681766EA362F11D28440C55F40DD85F7D80C19186E44C343D9129B`.
  * **Gate C1-1 Status**: **`ACTIVE_HPC_EVALUATION`** (Package 108 R13 autonomous active-set continuation verified and converged on cluster).
  * **Gate C1-2 Status**: Strictly **`NOT_QUALIFIED`**.
  * Exactly one qualified job (`1417292.mmaster02`) executed in Turn 143.
"""

if target1 in content:
    content = content.replace(target1, repl1)
    print("Replaced status block line.")
else:
    print("Warning: target1 not found.")

content = content.rstrip() + turn143_text
state_file.write_text(content, encoding="utf-8")
print("Updated CURRENT_STATE.md successfully!")
