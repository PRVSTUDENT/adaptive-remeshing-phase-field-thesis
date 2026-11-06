# Method A Plate-with-Hole Geometry & Production Readiness Assessment

**Task ID:** `F1632-METHOD-A-HOLE-DEMONSTRATION-REUSE-AND-GENERATION`  
**Handoff Correlation:** `HND-2f0d43508f97` (Review Re-Evaluation)  
**Supervisor Directive Reference:** Dr. Roth (6 November 2026, via ChatGPT Bridge `HND-bef847fc363a` & `HND-f55ea7f9eb8f`)  
**Artifact Directory:** `models/pandey_kumar_mode1/176_method_a_plate_with_hole/`  
**Execution Boundary:** Zero new PBS submissions (`max_new_pbs_submissions = 0`). Non-production offline qualification, local resolution audit, and execution feasibility assessment only.  
**Production User Subroutine:** `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 29,722 bytes, verified bitwise unchanged).  
**Production Physical Mesh:** `PK_HOLE_METHOD_A_PROD_PHYS.inp` (`8CEB44A628BE9F7D19B4797723813BF7FF674EDB8E4AA66420AEA6665F924EBD`, 3,264,831 bytes).  
**Current Production Status:** **BLOCKED UNDER CURRENT STANDING HPC LIMITS** (requires supervisor decision on execution pathway).

---

## 1. Verified Model Geometry & Ligament Clearance

The geometry and discretization parameters for the Mode-I plate with off-axis circular hole were generated using the general, parameterized script `scripts/remeshing/generate_plate_with_hole_method_a.py`:

```json
{
  "specimen": {
    "plate_width_mm": 1.0,
    "plate_height_mm": 1.0,
    "thickness_mm": 1.0,
    "initial_notch_length_mm": 0.50,
    "notch_y_mm": 0.50,
    "notch_half_opening_mm": 0.001
  },
  "hole_geometry": {
    "center_x_mm": 0.65,
    "center_y_mm": 0.65,
    "radius_mm": 0.10,
    "center_to_center_distance_mm": 0.212132,
    "surface_clearance_along_centerline_mm": 0.112132,
    "minimum_ligament_corner_to_hole_mm": 0.111426,
    "boundary_type": "traction_free_interior_void"
  },
  "material_and_phase_field": {
    "elastic_modulus_GPa": 210.0,
    "poisson_ratio": 0.30,
    "fracture_energy_Gc_kN_per_mm": 0.0027,
    "length_scale_l0_mm": 0.0075,
    "viscous_damping_eta_kN_s_per_mm2": 1.0e-7
  },
  "adaptive_remeshing_rule": {
    "error_indicator": "MISESERI",
    "sizing_method": "UNIFORM_ERROR",
    "error_target_percentage": 2.0,
    "refinement_factor": 10,
    "coarsening_factor": "NOT_ALLOWED",
    "h_min_mm": 0.001,
    "h_max_mm": 0.020,
    "initial_coarse_seed_mm": 0.020
  }
}
```

### Ligament Geometry & Clearance Reconciliation
- **Center-to-Center Distance:**
  $$\Delta r = \sqrt{(0.65 - 0.50)^2 + (0.65 - 0.50)^2} = \sqrt{0.15^2 + 0.15^2} = 0.212132\text{ mm} \approx 212.1\,\mu\text{m}$$
- **Hole Surface Clearance along Centerline:**
  $$d_{\text{surface}} = \Delta r - R = 0.212132 - 0.100000 = \mathbf{0.112132\text{ mm}} \approx \mathbf{112.1\,\mu\text{m}}$$
- **Minimum Clearance from Slit Corner to Hole Perimeter:**
  Accounting for the finite notch half-opening ($w = 0.001\text{ mm}$, upper slit corner at $(0.50, 0.501)$):
  $$d_{\text{corner-surface}} = \sqrt{(0.65 - 0.50)^2 + (0.65 - 0.501)^2} - 0.10 = \mathbf{0.111426\text{ mm}} \approx \mathbf{111.4\,\mu\text{m}}$$

The initial ligament provides $\approx 15\ell_0$ of uncracked material, ensuring substantial crack propagation trajectory between the initial notch tip and the void boundary.

---

## 2. Boundary Condition Parity & Energy Diagnostic DEPVAR Reconciliation

Boundary conditions maintain exact physical parity with the published production anchor (Job `1400395.mmaster02`):

1. **Pre-Analysis Model (`Step-1` Elastic Solve):**
   - Bottom edge: $u_2 = 0$ on set `Bottom` (`RollBottom`).
   - Pin support: $u_1 = 0$ at the single bottom-left vertex $(0.0, 0.0)$ (`PinBottom`).
   - Top edge: $u_1 = 0$ on set `Top` (`FixTopX`) and prescribed tensile displacement $u_2 = 0.005\text{ mm}$ (`TensionTop`).
   - Lateral edges and circular hole boundary: strictly traction-free.
2. **Generated 3-Layer UEL Production Deck (`PK_HOLE_METHOD_A_PROD.inp`):**
   - Bottom roller: `N_BOTTOM, 2, 2, 0.0`.
   - Single bottom pin: `N_PIN, 1, 1, 0.0` at vertex $(0.0, 0.0)$.
   - Top horizontal restraint: `N_TOP, 1, 1, 0.0`.
   - Top tensile pull: Rigid tensile displacement applied to master Reference Point `N_RP` (node 999999), tied to all `N_TOP` nodes via `*EQUATION` ($u_{2,i} - u_{2,\text{RP}} = 0$).
   - Multi-line `*NSET` cards: reformatted to wrap at 16 items per line, strictly adhering to the Abaqus data line item limit and eliminating all line truncation warnings.
3. **Visualization & Energy State Variables (`*DEPVAR`):**
   - `f42_mixed_uel.for` companion UMAT elements store energy balance quantities in $\text{STATEV}(17:20)$:
     * `STATEV(17)`: $E_{\text{frac}}$ (accumulated fracture energy)
     * `STATEV(18)`: $E_{\text{elas}}$ (elastic strain energy)
     * `STATEV(19)`: $\psi_f$ (crack surface energy density)
     * `STATEV(20)`: $\psi_e$ (elastic energy density)
   - Deck generator updated from `*DEPVAR\n16` to `*DEPVAR\n20` and verified in `PK_HOLE_METHOD_A_PROD.inp` line 186955.

---

## 3. Empirical Local Mesh Resolution Analysis & Objective Assessment

The adapted physical mesh (`PK_HOLE_METHOD_A_PROD_PHYS.inp`, 46,747 physical elements, 46,651 nodes) was analyzed directly via `scripts/remeshing/analyze_local_fpz_resolution.py` and independently validated in `tests/unit/test_f1632_production_mesh_resolution.py`:

### Measured Edge-Length Distributions per Zone
| Metric | Notch Tip Zone ($r \le 3.3\ell_0$) | Ligament Corridor | Hole Boundary Annulus ($|r-R| \le 2\ell_0$) | Far Field |
|:---|:---:|:---:|:---:|:---:|
| **Elements** | 677 | 5,253 | 2,232 | 38,585 |
| **Total Edges** | 2,692 | 20,889 | 8,927 | 153,274 |
| **Min Edge** | $0.8543\,\mu\text{m}$ | $0.7250\,\mu\text{m}$ | $1.0639\,\mu\text{m}$ | $0.2600\,\mu\text{m}$ |
| **p01 Edge** | $1.0248\,\mu\text{m}$ | $0.9602\,\mu\text{m}$ | $1.5241\,\mu\text{m}$ | $1.2315\,\mu\text{m}$ |
| **p10 Edge** | $1.3353\,\mu\text{m}$ | $1.2626\,\mu\text{m}$ | $1.6223\,\mu\text{m}$ | $1.6709\,\mu\text{m}$ |
| **Median Edge** | $1.7081\,\mu\text{m}$ | $1.6510\,\mu\text{m}$ | $1.9876\,\mu\text{m}$ | $3.3226\,\mu\text{m}$ |
| **p90 Edge** | $1.9925\,\mu\text{m}$ | $2.2727\,\mu\text{m}$ | $2.8143\,\mu\text{m}$ | $8.3476\,\mu\text{m}$ |
| **p95 Edge** | $2.0947\,\mu\text{m}$ | $2.6633\,\mu\text{m}$ | $3.2307\,\mu\text{m}$ | $9.8620\,\mu\text{m}$ |
| **Max Edge** | $2.8742\,\mu\text{m}$ | $4.8341\,\mu\text{m}$ | $4.4571\,\mu\text{m}$ | $25.1888\,\mu\text{m}$ |
| **Edges $\le \ell_0/5$ ($1.5\,\mu\text{m}$)** | **22.8%** | **30.1%** | **0.8%** | **5.0%** |
| **Resolution $h_{\text{p10}}/\ell_0$** | **0.178** | **0.168** | **0.216** | **0.223** |
| **Resolution $h_{\text{median}}/\ell_0$** | **0.228** | **0.220** | **0.265** | **0.443** |

### Corrected Mesh-Resolution Interpretation (No A Priori Sufficiency Guarantee)
1. **Measured Threshold Adherence:**
   - In the notch tip zone, **22.8%** of edges satisfy $h \le \ell_0/5 = 1.5\,\mu\text{m}$.
   - In the ligament corridor, **30.1%** of edges satisfy $h \le \ell_0/5$.
   - Along the circular hole boundary, only **0.8%** of edges satisfy $h \le \ell_0/5$.
2. **Removal of Resolution Guarantee:**
   - A 10th-percentile edge length of $1.26\text{--}1.34\,\mu\text{m}$ confirms that the finest sub-regions approach $\ell_0/5$, but does **NOT** guarantee that the entire fracture process zone throughout the ligament is resolved by six or more elements.
   - Because 69.9% of ligament edges and 77.2% of notch tip edges have $h > 1.5\,\mu\text{m}$, the mesh cannot be declared a priori sufficient for full regularized fracture propagation. Mesh adequacy must be evaluated via physical convergence verification during simulation.

### Investigation of Maximum Consecutive Edge Lengths (25.1888 µm)
A dedicated script (`scripts/remeshing/investigate_oversized_edges.py`) analyzed every element in `PK_HOLE_METHOD_A_PROD_PHYS.inp` whose consecutive-node edge length exceeds $20.0\,\mu\text{m}$:
- **Number of Elements with Edge $> 20\,\mu\text{m}$:** Exactly **47** out of 46,747 ($0.101\%$).
- **Element Topology:** All 47 elements are standard quadrilateral elements (`CPS4R`).
- **Aspect Ratios:** All 47 elements have well-behaved aspect ratios between **1.14** and **1.87** (mean $1.41$).
- **Spatial Distribution:**
  * Far-left boundary ($x \le 0.10$): 13 elements
  * Far-right boundary ($x \ge 0.90$): 2 elements
  * Far-top boundary ($y \ge 0.90$): 2 elements
  * Coarse interior ($x \in [0.12, 0.22], y \in [0.28, 0.62]$): 30 elements
  * **Notch Tip Zone & Ligament Corridor:** **0 elements** (maximum edge in notch tip is $2.87\,\mu\text{m}$, in ligament is $4.83\,\mu\text{m}$).
- **Algorithmic Origin:** In Abaqus advancing-front quadrilateral paving (`refinementFactor = 10, coarseningFactor = NOT_ALLOWED`), `maxElementSize` is a soft sizing target. The paving algorithm allows consecutive element edges up to $\approx 25\,\mu\text{m}$ ($\approx 25\%$ above nominal $20\,\mu\text{m}$) in low-gradient transition zones to avoid forced triangular splitting or skewed quad shapes, resulting in zero distorted elements (`WarnElemDistorted` count is 0).

---

## 4. Production Resource Sizing & Standing Limits Analysis

### Standing Project Restrictions
Under the mandatory project execution policy (`AGENTS.md`):
- **Walltime:** $\le 8\text{ hours}$ per job.
- **Memory:** $\le 16\text{ GB}$ per job.
- **CPUs:** $1\text{ CPU}$ per job (serial Mode-I execution).
- **Active Jobs:** $\le 4\text{ active user jobs}$.

### Status of the Holiday-Window Concurrency Policy
- The holiday-window policy documented in historical project notes explicitly stated: *"Active until September 9, 2026"*.
- As of 6 November 2026, the holiday-window policy is **EXPIRED**.
- The previously proposed 16-hour / 32-GB single job is **DISQUALIFIED** under active standing rules.

### Production Walltime Scaling for 46,747 Elements
- **Empirical Reference Anchor (Job 1400395.mmaster02):**
  * Discretization: 15,396 physical elements (46,188 co-located elements).
  * Increments: 7,028 increments.
  * Measured Walltime: **07:06:46** on 1 CPU (7.11 hours).
- **Scaling to Package 176 Mesh:**
  * Discretization: 46,747 physical elements (140,241 co-located elements), a **$3.03\times$** element increase.
  * Projected Single-Job Walltime: $7.11\text{ hours} \times 3.03 \approx \mathbf{21.5\text{ hours}}$ on 1 CPU.
  * **Conclusion:** A single serial job on 46,747 elements will terminate with walltime limit exceeded (Walltime Exceeded at 8h, reaching only $\approx 35\text{--}40\%$ of the displacement schedule).

---

## 5. Restart Architecture & Storage Overhead Audit

### Subroutine Audit of `f42_mixed_uel.for`
A complete audit of `f42_mixed_uel.for` subroutines `UEXTERNALDB` and `UEL` reveals:
1. `UEXTERNALDB(LOP, LRESTART, ...)` handles only four operation codes:
   - `LOP = 0`: Start of analysis — initializes all arrays in `COMMON /CB_STATE_TRANS/` to zero.
   - `LOP = 1`: Start of increment — copies committed state to trial state.
   - `LOP = 2`: End of increment — commits trial state and appends energies to CSV.
   - `LOP = 3`: End of analysis — closes CSV file.
2. **Missing Restart Logic:**
   - Subroutine `UEXTERNALDB` completely lacks `LOP = 4` (restart write callback) and `LOP = 5` (restart read callback).
   - If an Abaqus job is restarted using `*RESTART, READ`, Abaqus issues `LOP = 0` at the start of the restart analysis, which **zeroes out all arrays** in `COMMON /CB_STATE_TRANS/` (`SV_PHASE_COMMITTED`, `SV_H_COMMITTED`, `SV_E_FRAC`, etc.).
   - Consequently, cross-job restart causes complete loss of the crack history field $H$ and fracture energy, causing unphysical healing and numerical failure.
3. **Distinction between Checkpoint Writing and State-Preserving Recovery:**
   - Setting `*RESTART, WRITE` in the input deck writes standard Abaqus restart blocks (`.res`, `.mdl`) for displacement and native variables.
   - It does **NOT** serialize custom Fortran `COMMON` blocks. Therefore, true state-preserving restart recovery across independent PBS jobs is **UNSUPPORTED** with the frozen UEL.

### Restart Disk Storage Overhead
- For 140,241 co-located elements, writing restart state at `FREQUENCY = 1` across $\approx 7,000$ increments:
  - Restart file size per increment: $\approx 10\text{--}15\text{ MB}$.
  - Total projected `.res` file size: **$70\text{ to }105\text{ GB}$**.
  - This creates significant risk of cluster scratch quota exhaustion.
  - **Remediation:** If restart writing is retained for crash diagnostics, it must use `FREQUENCY = 10` or `*RESTART, WRITE, OVERLAY` to bound disk usage to $< 2\text{ GB}$.

---

## 6. Production Readiness Conclusion & Execution Pathways

### Definitive Production Readiness Status
**PRODUCTION EXECUTION IS CURRENTLY BLOCKED.**
The 46,747-element Method A plate-with-hole model cannot be executed to completion under active standing rules (8h / 16GB / 1 CPU), because single-job execution exceeds 8 hours and multi-job restart is structurally unqualified in `f42_mixed_uel.for`.

### Three Mutually Exclusive Resolution Pathways for Supervisor Direction
| Pathway | Description | Required Authorizations / Actions | Scientific / Operational Trade-off |
|:---|:---|:---|:---|
| **Pathway 1: Walltime Extension Exception** | Execute 46k element model as a single monolithic job ($u=0\to 0.012\text{ mm}$) with extended walltime ($\le 24\text{ hours}$, 1 CPU, 16 GB). | Explicit supervisor approval for single-job walltime exception ($\le 24\text{h}$) in queue `normal_imfdfkmq`. | Preserves current 46k mesh and highest FPZ resolution ($h_{\text{p10}}=1.26\,\mu\text{m}$); requires scheduler waiver. |
| **Pathway 2: Mesh Re-tuning to $\le 16\text{k}$ Elements** | Re-run `generate_plate_with_hole_method_a.py` with coarser far-field seeding ($h_{\text{coarse}} = 0.04\text{ mm}$, `errorTarget = 3.5\%`) to produce $\le 16,000$ physical elements. | Zero special authorization needed. Fully compliant with 8h / 16GB / 1 CPU standing limit. | Matches proven runtime of Job 1400395 (7h 06m); slightly lower resolution in far field ($h_{\text{far}} \approx 30\text{--}40\,\mu\text{m}$), but preserves $h \approx 1.5\text{--}2.0\,\mu\text{m}$ at tip. |
| **Pathway 3: SMP Multi-Threading Qualification** | Qualify 8-thread SMP execution for Method A (`f42_mixed_uel.for` in shared-memory mode, 1 node, 8 CPUs, $\le 8\text{ hours}$). | Supervisor approval to use 8-thread SMP for Method A production. | Brings 46k element walltime from $\approx 21\text{h}$ down to $\approx 4\text{--}5\text{ hours}$, fitting cleanly within the 8-hour limit. |

---

## 7. Mandatory Verification Gate & Immutable Evidence

All qualification artifacts and regression tests are verified:
- **Git Commit:** `mode2-pandey-kumar-reproduction`
- **Generator Script:** `scripts/remeshing/generate_plate_with_hole_method_a.py`
- **Resolution Script:** `scripts/remeshing/analyze_local_fpz_resolution.py`
- **Oversized Edge Script:** `scripts/remeshing/investigate_oversized_edges.py`
- **Test Suites (5/5 PASS):**
  * `tests/unit/test_f1632_method_a_generator.py` (3/3 PASS)
  * `tests/unit/test_f1632_local_resolution.py` (1/1 PASS)
  * `tests/unit/test_f1632_production_mesh_resolution.py` (1/1 PASS)
- **Immutable Evidence File:** `models/pandey_kumar_mode1/176_method_a_plate_with_hole/evidence/PK_HOLE_METHOD_A_DC.dat` (tracked via `git add -f`, 12,058 bytes, 8 benign warnings, 0 errors).
- **Physical Mesh:** `models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_PROD_PHYS.inp` (`8CEB44A628BE9F7D19B4797723813BF7FF674EDB8E4AA66420AEA6665F924EBD`, 3,264,831 bytes).
- **Subroutine Integrity:** `models/pandey_kumar_mode1/176_method_a_plate_with_hole/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 29,722 bytes, 100% bitwise unchanged).
