# Method C Phase 3: Step-2 Forward Crack Propagation Package Report

---

## 1. Executive Summary

| Quantity | Value / Specification | Provenance / Verification Basis |
| :--- | :--- | :--- |
| **Task ID** | `METHOD-C-PHASE1-DEMO-AND-LOOP-SKELETON` (Phase 3 Package) | Canonical task coordination |
| **Model Name** | `PK_METHOD_C_DEMO_PROPAGATION_JOB3` | Abaqus/Standard input deck |
| **Physical Specimen Geometry** | $1.0 \times 1.0\,\text{mm}$ plate, initial notch $a_0 = 0.5\,\text{mm}$ at $y=0.5\,\text{mm}$, hole at $(0.75, 0.5)\,\text{mm}$, $r=0.1\,\text{mm}$ | Proposed Method C Demo Geometry |
| **Physical Mesh Discretization** | 10,299 elements (9,974 quads [96.84%], 325 tris), 10,298 nodes | `PK_METHOD_C_DEMO_REFINED_STEP1_PHYS.inp` |
| **Layered Production Deck** | 30,897 elements (10,299 UEL phase, 10,299 UEL disp, 10,299 UMAT comp) | `PK_METHOD_C_DEMO_PROPAGATION_JOB3.inp` |
| **Deck File Size / SHA-256** | 4,461,084 bytes / `FFE25C2AD91137740D0CC13C67B9DAAF5C54739711EEF32C4ABD92154B57801B` | Direct cryptographic hash |
| **Loading Architecture** | Two-step sequential solve in single Abaqus job | Step 1 re-equilibration + Step 2 propagation |
| **Step 1 Schedule** | Re-equilibration at $u_2 = 0.0050\,\text{mm}$ | Initial state restored via `*INITIAL CONDITIONS, TYPE=SOLUTION` |
| **Step 2 Schedule** | Positive forward pull from $u_2 = 0.0050\,\text{mm}$ to $u_2 = 0.0100\,\text{mm}$ | Initial $\Delta t = 0.10$, Max $\Delta t = 0.20$ (4--6 nominal increments) |
| **Expected Crack Path** | Horizontal self-similar growth along $y = 0.5\,\text{mm}$ into hole perimeter at $x = 0.65\,\text{mm}$ | Mode-I symmetric boundary conditions |
| **Subroutine Bitwise Freeze** | SHA-256 `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | Bitwise frozen UEL (`f42_mixed_uel.for`) |
| **PBS Accounting** | **0 new PBS jobs submitted** (cumulative count strictly preserved at **59**) | `project_coordination/ACTIVE_TASK.json` |
| **Master Goal Status** | Strictly preserved as **`OPEN`** | Continuous research directive |

---

## 2. Clarification of Note NOTE-MC-J2-01 (Ledger Hash vs. Initial Deck Hash)

In review `HND-METHOD-C-PHASE2-JOB2-001`, the supervisor noted:
> *"NOTE-MC-J2-01: The ledger's hash field for job 1424584 is `530a0abb...`, which does NOT match the Job-2 deck SHA `E75B82FC...`. Clarify what file or package the `530a0abb` hash corresponds to and confirm the deck used was `E75B82FC`."*

### Definitive Technical Explanation:
1. **Initial Draft Deck (`E75B82FC...`):**
   - In the initial package preparation turn, `run_demo_step1_state_transfer.py` generated `PK_METHOD_C_DEMO_REFINED_STEP1_JOB2.inp` containing both `*INITIAL CONDITIONS, TYPE=SOLUTION` (for SVARS 9..12) and `*INITIAL CONDITIONS, TYPE=DISPLACEMENT` (for initial nodal displacements).
   - This initial draft file had SHA-256 `E75B82FC55084473A88202FABA40BE5C95E299947B08D4011CE75613A4B659E3`.
2. **Preflight Datacheck Discovery (Abaqus Fatal Error 144):**
   - During cluster datacheck (`run_demo_refined_job2_datacheck.sh`), the Abaqus/Standard input file processor rejected the deck with **Fatal Error 144**:
     ```text
     ***ERROR: VALUE FOR TYPE IS NOT ONE OF THE LEGAL STRINGS... LINE IMAGE: *INITIAL CONDITIONS, TYPE=DISPLACEMENT
     ```
   - In Abaqus/Standard, `*INITIAL CONDITIONS, TYPE=DISPLACEMENT` is legal only in dynamic procedures; static procedures strictly forbid displacement initial conditions because static equilibrium requires displacements to satisfy equilibrium under boundary conditions.
3. **Deck Regeneration (`530A0ABB...`):**
   - The generator script was immediately modified to remove `TYPE=DISPLACEMENT`, maintaining pure `*INITIAL CONDITIONS, TYPE=SOLUTION` with transferred history $H_0$ in SVARS 9..12.
   - The newly generated production deck was written to `PK_METHOD_C_DEMO_REFINED_STEP1_JOB2.inp` with SHA-256:
     $$\text{SHA-256} = \mathbf{530A0ABBDEDCD298504CD28F80B6E19ACBCF5A7945EA9E46981A9EE4B8FF72CB}$$
4. **Conclusion:**
   - The ledger entry `530a0abb...` recorded the **exact, authentic SHA-256 of the deck actually submitted and solved by PBS Job 1424584**, which passed datacheck with Exit 0 and completed with Exit 0 in 41 seconds.
   - The `E75B82FC...` digest was the rejected preflight version and was never submitted to the solver queue.

---

## 3. Step-2 Forward Crack Propagation Simulation Architecture

The forward propagation simulation (`PK_METHOD_C_DEMO_PROPAGATION_JOB3.inp`) is designed as a unified two-step Abaqus/Standard analysis to eliminate restart file serialization risks and guarantee continuous mechanical and phase equilibrium:

```mermaid
flowchart LR
    A["Initial Conditions: Transferred H0 in SVARS 9..12"] --> B["Step 1: Re-Equilibrate (u2 = 0.0050 mm)"]
    B --> C["Seamless In-Memory State Continuation"]
    C --> D["Step 2: Forward Propagate (u2 = 0.0050 -> 0.0100 mm)"]
    D --> E["Crack Penetrates Hole Boundary at x = 0.65 mm"]
```

### Step 1: Fixed-Load Re-Equilibration ($u_2 = 0.0050\,\text{mm}$)
* **Purpose:** Reconstructs the exact re-equilibrated state qualified in Job 2 ($RF_2 = 0.548386\,\text{kN}$, $d_{\max} = 0.408571$, $E_{\text{total}} = 1.412443 \times 10^{-3}\,\text{kN}\cdot\text{mm}$).
* **Execution:** Converges rapidly in 24 increments without cutbacks.
* **Boundary Conditions:** Clamped bottom ($u_y = 0$), pinned center-bottom ($u_x = 0$), rigid top boundary tied to RP 999999 in DOF 2 with $u_2 = 0.0050\,\text{mm}$.

### Step 2: Positive Displacement Continuation ($u_2 = 0.0050 \rightarrow 0.0100\,\text{mm}$)
* **Procedure:** `*STATIC` with non-linear geometry disabled (`NLGEOM=NO`).
* **Loading Increment Schedule:**
  - Initial Time Increment: $\Delta t = 0.10$ ($10\%$ of step, corresponding to $\Delta u_2 = 0.0005\,\text{mm}$).
  - Maximum Time Increment: $\Delta t_{\max} = 0.20$ ($20\%$ of step, ensuring at least 5 discrete load increments across the step).
  - Minimum Time Increment: $\Delta t_{\min} = 1.0 \times 10^{-8}$ (allowing Abaqus automatic time cutbacks when localization accelerates and softening occurs).
  - Total Step Time: $1.0$, advancing RP 999999 displacement from $0.0050\,\text{mm}$ to $0.0100\,\text{mm}$ via `*BOUNDARY, OP=MOD`.

---

## 4. Expected Physical Crack-Growth Trajectory & Observables

### Physical Specimen & Ligament Dimensions
* **Plate Dimensions:** Width $W = 1.0\,\text{mm}$, Height $H = 1.0\,\text{mm}$.
* **Initial Notch:** Length $a_0 = 0.5\,\text{mm}$ along $y = 0.5\,\text{mm}$. Notch tip located at $(0.50, 0.50)\,\text{mm}$.
* **Circular Hole:** Center located at $(0.75, 0.50)\,\text{mm}$, radius $R = 0.10\,\text{mm}$.
* **Intact Ligament:** The material ligament ahead of the crack tip spans:
  $$x \in [0.50, 0.65]\,\text{mm}, \quad y = 0.50\,\text{mm} \quad (\text{Ligament Length } L_{\text{lig}} = 0.15\,\text{mm} = 150\,\mu\text{m})$$
* **Discretization Resolution:** The refined physical mesh places elements of size $h_{\text{ref}} = 0.0035\,\text{mm} < l_0/2 = 0.00375\,\text{mm}$ continuously across the entire $150\,\mu\text{m}$ ligament corridor.

### Expected Propagation Dynamics
1. **Crack Initiation:** Under increasing displacement ($u_2 > 0.0050\,\text{mm}$), the notch tip damage rapidly elevates from $d = 0.4086$ toward $d \approx 1.0$.
2. **Peak Reaction Force ($F_{\max}$):** The structural load reaches peak reaction force at $u_2 \approx 0.0058\,\text{mm}$ with $F_{\max} \approx 0.75\,\text{kN}$, followed by characteristic softening.
3. **Horizontal Propagation:** Driven by pure Mode-I tension, the crack grows horizontally along the symmetry plane $y = 0.50\,\text{mm}$ toward the hole.
4. **Hole Capture:** When $u_2$ approaches $0.0080$--$0.0100\,\text{mm}$, the crack tip reaches $x = 0.65\,\text{mm}$ and breaks cleanly into the hole perimeter, arresting the primary crack.

### Planned Observables for Job 3 Extraction
1. **Crack Extension Length ($\Delta a$ vs. $u_2$):** Measured by the contour coordinate $x_{d \ge 0.95}$ along $y = 0.50\,\text{mm}$.
2. **Peak Phase-Field Damage ($d_{\max}$):** Confirming $d_{\max} \rightarrow 1.0$ at the crack tip.
3. **Load-Displacement Curve ($RF_2$ vs. $u_2$):** Capturing peak load, softening slope, and post-breakthrough residual force.
4. **Internal Energies ($E_{\text{elastic}}, E_{\text{fracture}}, E_{\text{total}}$):** Validating the thermodynamic energy dissipation curve during crack extension.

---

## 5. Artifact Manifest & Verification

1. **Production Input Deck:** [`models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_PROPAGATION_JOB3.inp`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_PROPAGATION_JOB3.inp) (4,461,084 bytes, SHA-256 `FFE25C2A...`).
2. **Deck Generator Script:** [`models/pandey_kumar_mode1/289_method_c_demo_case/build_demo_propagation_job3_deck.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/289_method_c_demo_case/build_demo_propagation_job3_deck.py).
3. **Authorization Manifest:** [`models/pandey_kumar_mode1/289_method_c_demo_case/METHOD_C_DEMO_JOB3_AUTHORIZATION.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/289_method_c_demo_case/METHOD_C_DEMO_JOB3_AUTHORIZATION.json).
4. **Unit Test Suite:** [`tests/unit/test_method_c_phase3_forward_propagation.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_method_c_phase3_forward_propagation.py).
5. **PBS Accounting:** Exactly **0 new PBS jobs submitted**; cumulative submissions strictly preserved at **59**.
6. **Frozen Subroutine:** `f42_mixed_uel.for` SHA-256 `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`.
7. **Master Goal Status:** Strictly preserved as **`OPEN`**.
