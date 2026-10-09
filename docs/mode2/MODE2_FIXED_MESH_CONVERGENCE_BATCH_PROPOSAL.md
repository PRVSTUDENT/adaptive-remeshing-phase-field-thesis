# Mode-II Fixed-Mesh Spatial Convergence Batch Proposal (Gate M2-1B)

**Date:** 2026-10-09  
**Task ID:** `F1377-MODE2-FIXED-MESH-CONVERGENCE-BATCH-PREPARATION`  
**Author:** Gemini Antigravity  
**Status:** `PROPOSAL_AWAITING_EXPLICIT_HUMAN_AUTHORIZATION`  
**Branch:** `mode2-pandey-kumar-reproduction`  

---

## 1. Executive Summary & Epistemological Purpose

This proposal presents the formal specification and execution plan for the **Mode-II Fixed-Mesh Spatial Convergence Suite**, establishing the foundational benchmark required by **Gate M2-1B (Fixed-Mesh Fracture Reference Qualified)**.

### The Problem Addressed
In Mode-II shear fracture, the repository transitioned directly from a single coarse pre-analysis ($2{,}960$ FEs, $h \approx 20\text{--}25\,\mu\text{m} > l_0 = 15\,\mu\text{m}$) into native adaptive remeshing sweeps (ET3: $21{,}063$ FEs, ET2: $37{,}575$ FEs). While adaptive remeshing produced stable crack propagation and high corridor selectivity ($77.8\%$), the resulting peak force ($F_{\max} = 412.21\,\text{N}$) exceeded the published value of Pandey & Kumar (2025) ($F_{\max} \approx 365.74\,\text{N}$) by $+12.71\%$.

As proved in `MODE2_FIXED_MESH_REFERENCE_AUDIT_AND_CONVERGENCE_ROADMAP.md`:
- Historical Stage F runs (H0, H1, H2) were unconstrained in the vertical direction (`FREEU2`, $K_0 \approx 12.8\,\text{kN/mm}$) and cannot serve as reference anchors for the active constrained benchmark ($u_y = 0$, $K_0 \approx 45.68\,\text{kN/mm}$).
- Without an independent, mesh-converged fixed-mesh reference solution for the exact paper-grounded boundary value problem, it is mathematically impossible to determine whether:
  * **Possibility A (Solver Concurrence):** The continuum formulation under constrained shear converges to $F_{\max} \approx 410\text{--}415\,\text{N}$ (proving adaptive remeshing is fully accurate and the difference with literature lies in external reporting or boundary modeling details); or
  * **Possibility B (Adaptive Discretization Failure):** The formulation converges to $F_{\max} \approx 360\text{--}370\,\text{N}$ (proving that current adaptive remeshing is failing to capture localized softening).

### 3-Layer Thesis Architecture Alignment
This suite establishes **Layer 1: Verified Fracture Solver & Fixed Benchmark**, providing the permanent reference anchor against which Layer 2 (General Adaptive Refinement Controller) and Layer 3 (Sequential Adaptive Driver) can be rigorously and quantitatively evaluated.

---

## 2. Fixed-Mesh Suite Discretization Matrix

To eliminate any potential geometric bias, corridor-width artifacts, transition slivers, or element aspect ratio distortions, the suite utilizes **100% structured uniform quadrilateral meshes** across the entire $1.0\,\text{mm} \times 1.0\,\text{mm}$ domain.

| Case ID | Job Name | Grid ($N_x \times N_y$) | Element Size $h$ | $h / l_0$ | Physical Quads | Layered Elements | Mesh Nodes | Active Solver Equations | Scientific Role |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `01_coarse_2p5k_h20um` | `M2_FIX_COARSE_2P5K` | $50 \times 50$ | $20.00\,\mu\text{m}$ | $1.333$ | $2{,}500$ | $7{,}500$ | $2{,}626$ | $7{,}827$ | Pure uniform coarse baseline; comparison against coarse pre-analysis Job 1411104 ($2{,}960$ FEs). |
| `02_medium_18k_h7p5um` | `M2_FIX_MED_18K` | $134 \times 134$ | $7.46\,\mu\text{m}$ | $0.498$ | $17{,}956$ | $53{,}868$ | $18{,}292$ | $54{,}741$ | Sub-lengthscale anchor ($h \approx l_0 / 2$); comparable element scale to ET3 ($21{,}063$ FEs). |
| `03_intermediate_40k_h5um` | `M2_FIX_INT_40K` | $200 \times 200$ | $5.00\,\mu\text{m}$ | $0.333$ | $40{,}000$ | $120{,}000$ | $40{,}501$ | $121{,}302$ | Classical phase-field resolution threshold ($h = l_0 / 3$); comparable to ET2 ($37{,}575$ FEs). |
| `04_fine_72k_h3p75um` | `M2_FIX_FINE_72K` | $268 \times 268$ | $3.73\,\mu\text{m}$ | $0.249$ | $71{,}824$ | $215{,}472$ | $72{,}495$ | $217{,}216$ | Definitive high-resolution reference anchor ($h = l_0 / 4$); resolves Possibility A vs B. |

### Mesh Topology Verification
1. **Domain:** Exactly $[0.0, 1.0] \times [0.0, 1.0]\,\text{mm}$.
2. **Initial Slit:** Sharp horizontal slit at $y = 0.5\,\text{mm}$ extending from $x = 0.0$ to $x = 0.5\,\text{mm}$.
3. **Flank Disconnection:** Independent duplicate nodes along the slit flanks ($x < 0.5\,\text{mm}$, $y = 0.5\,\text{mm}$):
   - Case 1: 25 duplicate pairs ($50$ nodes)
   - Case 2: 67 duplicate pairs ($134$ nodes)
   - Case 3: 100 duplicate pairs ($200$ nodes)
   - Case 4: 134 duplicate pairs ($268$ nodes)
4. **Crack Tip:** Exactly one single shared node at $(0.5, 0.5)\,\text{mm}$ connecting top and bottom halves.
5. **Intact Ligament:** Shared nodes for $x \in (0.5, 1.0]\,\text{mm}$ along $y = 0.5\,\text{mm}$.
6. **Jacobian Determinants:** $det(\mathbf{J}) > 0$ and element aspect ratio $\text{AR} = 1.000000$ everywhere.

---

## 3. Boundary-Value Problem & Loading Schedule

The boundary value problem is mathematically identical across all 4 models:

1. **Constitutive Model:** 2D Phase-Field Fracture with Miehe spectral strain energy decomposition (`f42_mixed_uel_mode2_miehe.for`, SHA-256 `699B05D6C430FCE6242F8C603B45BB0783CF376451EFD52C56BC984B0CE71188`).
2. **Material Constants:**
   - Young's modulus: $E = 210.0\,\text{kN/mm}^2$ ($210\,\text{GPa}$)
   - Poisson's ratio: $\nu = 0.3$
   - Fracture energy: $G_c = 0.0027\,\text{kN/mm}$ ($2.7\,\text{N/mm}$)
   - Regularization length: $l_0 = 0.015\,\text{mm}$ ($15.0\,\mu\text{m}$)
   - Artificial residual stiffness: $k = 1.0\times 10^{-7}$
3. **Boundary Conditions:**
   - Bottom surface ($y = 0.0\,\text{mm}$): $u_x = 0, u_y = 0$ (`N_BOTTOM`).
   - Top surface ($y = 1.0\,\text{mm}$): $u_y = 0$ (`N_TOP`), $u_x$ coupled to Reference Point 999999 (`N_RP`) via linear constraint cards (`*EQUATION`: $u_1(\text{node}) - u_1(\text{RP}) = 0$).
4. **Loading Schedule (Standardized 4,000-Increment Paper Horizon):**
   - **Step 1:** Monotonic shear loading to $u_x = 0.0100\,\text{mm}$ ($10.0\,\mu\text{m}$):
     * Time: $\Delta t = 5.0\times 10^{-4}$, 2000 increments, $\Delta u_x = 5.0\,\text{nm}$/inc.
   - **Step 2:** Monotonic shear loading to $u_x = 0.0200\,\text{mm}$ ($20.0\,\mu\text{m}$, full paper horizon):
     * Time: $\Delta t = 5.0\times 10^{-4}$, 2000 increments, $\Delta u_x = 5.0\,\text{nm}$/inc.

---

## 4. HPC Resources & Scheduler Policy

1. **Execution Architecture:**
   - Single-rank serial shared-memory mode (`cpus=1`, `double=both`).
   - Serial execution serves as the authoritative scientific reference anchor, eliminating thread-scheduling indeterminacy.
2. **Resource Requests per Job:**
   - CPUs: 1 CPU
   - Memory: 16 GB RAM
   - Walltime: 24:00:00
   - Queue: `normal_imfdfkmq`
3. **Scratch Compliance:**
   - Execution strictly under `/scratch9/pr21vyci/runs/mode2_fixed_convergence/<case_id>/`.
   - Zero bulky binary solver output in `/home/pr21vyci/`.
4. **Scheduler Concurrency Policy:**
   - Active Holiday-Window Concurrency Policy (demonstrated capacity $\ge 10$ concurrent jobs in `normal_imfdfkmq`).
   - Per-user limit: 640 CPUs / 4 TB RAM.
   - Running this 4-job batch consumes 4 CPUs and 64 GB RAM (with Job 1411414 consuming 1 CPU and 16 GB, total active utilization = 5 CPUs / 80 GB, well within the 640-CPU limit).
5. **Dual-Channel Notification Integration:**
   - PBS directives: `#PBS -m abe`, `#PBS -M pr21vyci@mailserver.tu-freiberg.de`.
   - Traps: `job_notifications.sh` sourced with `notify_start` and terminal exit trap (`notification_install_terminal_trap`).
   - Submission wrapper: `notify_submitted` issued upon successful `qsub`.

---

## 5. Pre-Declared Acceptance Criteria for Gate M2-1B

Before declaring Gate M2-1B closed and proceeding to benchmark adaptive remeshing:

1. **Initial Elastic Parity:**
   Initial structural stiffness $K_0$ on all meshes must satisfy:
   $$K_0 = 45.68 \pm 0.50\,\text{kN/mm} \quad (\Delta K_0 \le 1.1\%)$$
2. **Convergence of Macro-Mechanical Response:**
   - Peak force $F_{\max}(h)$ and peak displacement $u(F_{\max})$ must exhibit monotonic or asymptotic spatial convergence as $h \to 0$.
   - Establish whether the converged peak force is $F_{\max} \approx 410\text{--}415\,\text{N}$ (Possibility A) or $F_{\max} \approx 360\text{--}370\,\text{N}$ (Possibility B).
3. **Crack Trajectory & Invariant Geometry:**
   - Crack initiation angle $\theta(h)$ must converge asymptotically toward the observed range $\theta \in [-58^\circ, -59^\circ]$.
   - Terminal intact ligament $h_{\text{lig}}(h)$ at $u_x = 20.0\,\mu\text{m}$ must stabilize.
4. **Thermodynamic Energy & External Work:**
   - External work $W_{\text{ext}} = \int F \, du$ on the published domain $[0, 16.0]\,\mu\text{m}$ must demonstrate spatial convergence.

---

## 6. Authorization Boundary

- **Current Status:** `PREPARATION_COMPLETE_NOT_AUTHORIZED`.
- **Execution Authorized:** `false`.
- **Submission Approved:** `false`.
- **Maximum Permitted Submissions:** 0.
- **qsub Invocations:** 0.

Per `AGENTS.md` and repository rules:
*Explicit human authorization stating the maximum permitted jobs is strictly mandatory before any cluster execution or submission.*
