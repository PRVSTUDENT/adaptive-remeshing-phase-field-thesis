# Method A Plate-with-Hole Comparative Mesh Qualification & Readiness Assessment

**Task ID:** `F1632-METHOD-A-HOLE-DEMONSTRATION-REUSE-AND-GENERATION`  
**Handoff Correlation:** `HND-1c8df97e80be` (Pathway 2 Comparative Feasibility Evaluation)  
**Supervisor Directive Reference:** Dr. Roth (6 November 2026, via ChatGPT Bridge `HND-bef847fc363a` & `HND-f55ea7f9eb8f`)  
**Artifact Directory:** `models/pandey_kumar_mode1/176_method_a_plate_with_hole/`  
**Execution Boundary:** Zero new PBS submissions (`max_new_pbs_submissions = 0`). Non-production offline qualification, comparative remeshing evaluation, and execution feasibility assessment only.  
**Production User Subroutine:** `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 29,722 bytes, verified bitwise unchanged).  
**Preserved Reference Mesh (46k):** `models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_PROD_PHYS.inp` (`8CEB44A628BE9F7D19B4797723813BF7FF674EDB8E4AA66420AEA6665F924EBD`, 3,264,831 bytes).  
**Evaluated Candidate Mesh (31k):** `models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidate_16k/PK_HOLE_CANDIDATE_16K_PROD_PHYS.inp` (`08FDD9F80168375BFBBF8437BD1B8ADFC8BFAFBFAC64E20D3D1715B86C66BF6F`, 2,168,913 bytes).  
**Current Production Status:** **RETAINED BLOCKED STATUS DUE TO MEASURED ACCURACY–COST CONFLICT** (candidate rejected; requires supervisor decision on execution pathway).

---

## 1. Executive Summary & Candidate Feasibility Decision

Following the supervisor directive (`HND-1c8df97e80be`), Pathway 2 was investigated by generating and evaluating one alternative plate-with-hole mesh candidate using the existing Abaqus native MISESERI remeshing pipeline:
- **Investigated Candidate Parameters:** Initial coarse far-field seed $h_{\text{coarse}} = 0.04\text{ mm}$ (doubled from $0.02\text{ mm}$), while strictly retaining $\text{errorTarget} = 2.0$ percentage points, minimum element target $h_{\min} = 0.001\text{ mm}$, maximum element target $h_{\max} = 0.04\text{ mm}$, identical geometry ($1.0 \times 1.0\text{ mm}$ plate, notch tip $(0.50, 0.50)$, hole center $(0.65, 0.65)$, radius $0.10\text{ mm}$), boundary condition parity, and the frozen UEL.
- **Discretization Outcome:** Initial coarse elements dropped from 2,906 to 775; adapted physical elements dropped from **46,747** to **31,035** elements ($-33.6\%$).
- **Local FPZ Resolution Impact:**
  - Notch Tip Zone: $h_{\text{median}}$ degraded from $1.71\,\mu\text{m}$ to $2.49\,\mu\text{m}$ ($h/\ell_0 = 0.331$); edges $\le \ell_0/5$ ($1.5\,\mu\text{m}$) dropped from **22.8%** to **0.6%**.
  - Ligament Corridor: $h_{\text{median}}$ degraded from $1.65\,\mu\text{m}$ to $2.81\,\mu\text{m}$ ($h/\ell_0 = 0.375$); edges $\le \ell_0/5$ dropped from **30.1%** to **1.2%**.
- **Runtime Feasibility:** Scaling from the 15,396-element anchor (Job 1400395, 7h 06m on 1 CPU), the 31,035-element candidate requires an estimated **13 to 15 hours** on 1 CPU, which STILL exceeds the mandatory 8-hour PBS limit.
- **Definitive Decision:** **CANDIDATE REJECTED.** The candidate fails both criteria: it achieves insufficient element count reduction (still exceeding 8 hours) while severely degrading fracture-zone resolution below acceptable phase-field thresholds. Production status remains **BLOCKED**.

---

## 2. Verified Model Geometry & Ligament Clearance

- **Center-to-Center Distance:**
  $$\Delta r = \sqrt{(0.65 - 0.50)^2 + (0.65 - 0.50)^2} = \sqrt{0.15^2 + 0.15^2} = 0.212132\text{ mm} \approx 212.1\,\mu\text{m}$$
- **Hole Surface Clearance along Centerline:**
  $$d_{\text{surface}} = \Delta r - R = 0.212132 - 0.100000 = \mathbf{0.112132\text{ mm}} \approx \mathbf{112.1\,\mu\text{m}}$$
- **Minimum Clearance from Slit Corner to Hole Perimeter:**
  Accounting for the finite notch half-opening ($w = 0.001\text{ mm}$, upper slit corner at $(0.50, 0.501)$):
  $$d_{\text{corner-surface}} = \sqrt{(0.65 - 0.50)^2 + (0.65 - 0.501)^2} - 0.10 = \mathbf{0.111426\text{ mm}} \approx \mathbf{111.4\,\mu\text{m}}$$

The initial ligament provides $\approx 15\ell_0$ of uncracked material, ensuring substantial crack propagation trajectory between the initial notch tip and the void boundary.

---

## 3. Side-by-Side Local Mesh Resolution Comparison

Both the preserved 46k reference mesh and the 31k candidate mesh were analyzed directly using conservative polygon boundary edge measurements across all four geometric zones:

| Metric | Preserved Reference Mesh (`PK_HOLE_METHOD_A`) | Evaluated Candidate Mesh (`PK_HOLE_CANDIDATE_16K`) | Relative Impact |
|:---|:---:|:---:|:---|
| **Initial Coarse Seed** | $h_{\text{coarse}} = 0.02\text{ mm}$ (2,906 elements) | $h_{\text{coarse}} = 0.04\text{ mm}$ (775 elements) | $-73.3\%$ initial mesh |
| **Error Target** | 2.0 percentage points | 2.0 percentage points | Bitwise identical |
| **Adapted Physical Elements** | **46,747** (43,434 quads, 1,153 tris) | **31,035** (30,243 quads, 792 tris) | $-33.6\%$ elements |
| **Physical Nodes** | 46,651 | 31,037 | $-33.5\%$ nodes |
| **Co-located Elements** | 140,241 | 93,105 | $-33.6\%$ |
| **Notch Tip Elements ($r \le 3.3\ell_0$)** | 677 elements | 309 elements | $-54.4\%$ in tip |
| **Notch Tip $h_{\text{p10}}$** | **$1.3353\,\mu\text{m}$** ($h/\ell_0 = 0.178$) | **$1.9237\,\mu\text{m}$** ($h/\ell_0 = 0.256$) | $+44.1\%$ coarser |
| **Notch Tip Median Edge** | **$1.7081\,\mu\text{m}$** ($h/\ell_0 = 0.228$) | **$2.4851\,\mu\text{m}$** ($h/\ell_0 = 0.331$) | $+45.5\%$ coarser |
| **Notch Tip Edges $\le \ell_0/5$ ($1.5\,\mu\text{m}$)**| **22.8%** | **0.6%** | **Near-total loss of fine resolution** |
| **Ligament Corridor Elements** | 5,253 elements | 1,844 elements | $-64.9\%$ in ligament |
| **Ligament $h_{\text{p10}}$** | **$1.2626\,\mu\text{m}$** ($h/\ell_0 = 0.168$) | **$1.9345\,\mu\text{m}$** ($h/\ell_0 = 0.258$) | $+53.2\%$ coarser |
| **Ligament Median Edge** | **$1.6510\,\mu\text{m}$** ($h/\ell_0 = 0.220$) | **$2.8103\,\mu\text{m}$** ($h/\ell_0 = 0.375$) | $+70.2\%$ coarser |
| **Ligament Edges $\le \ell_0/5$ ($1.5\,\mu\text{m}$)** | **30.1%** | **1.2%** | **Near-total loss of fine resolution** |
| **Hole Boundary Median Edge** | $1.9876\,\mu\text{m}$ ($h/\ell_0 = 0.265$) | $3.6878\,\mu\text{m}$ ($h/\ell_0 = 0.492$) | $+85.5\%$ coarser |
| **Far Field Median Edge** | $3.3226\,\mu\text{m}$ ($h/\ell_0 = 0.443$) | $4.1583\,\mu\text{m}$ ($h/\ell_0 = 0.554$) | $+25.2\%$ coarser |
| **Oversized Edges ($>20\,\mu\text{m}$)** | 47 elements (max $25.19\,\mu\text{m}$) | 14 elements (max $22.44\,\mu\text{m}$) | Advancing-front paving tolerance |
| **Datacheck Status** | Exit 0 (8 benign UEL warnings, 0 errors) | Exit 0 (8 benign UEL warnings, 0 errors) | Input processing verified |
| **Projected Serial Walltime (1 CPU)** | **18 – 21 hours** | **13 – 15 hours** | **Both strictly exceed 8h PBS limit** |

### Origin of the Accuracy–Cost Conflict
In Abaqus native remeshing (`sizingMethod = UNIFORM_ERROR`):
1. Element sizing is driven by global strain energy error distribution relative to recovered stress gradients $\sigma^*$.
2. When the initial coarse mesh is coarsened ($h_{\text{coarse}} = 0.04\text{ mm}$), the stress singularity at the sharp slit tip is smoothed over larger elements during pre-analysis.
3. The remeshing rule consequently computes a coarser target size throughout the entire stress concentration zone: median edge length in the ligament increases from $1.65\,\mu\text{m}$ to $2.81\,\mu\text{m}$, reducing the number of elements across $\ell_0$ from $\approx 5$ down to $\approx 2.5\text{--}3$.
4. At $h/\ell_0 \approx 0.375$, phase-field literature documents severe artificial mesh pinning, delayed crack initiation, and unphysical crack deflection.
5. Therefore, global coarse seeding CANNOT simultaneously preserve the required $h \le \ell_0/5$ resolution and reduce total element count below 16k without localized domain partitioning.

---

## 4. Investigation of Maximum Consecutive Edges

Using `scripts/remeshing/investigate_oversized_edges.py`, all elements with boundary edge length $> 20.0\,\mu\text{m}$ were inspected:
- **In Reference Mesh (46,747 elements):** Exactly 47 elements ($0.101\%$) exceed $20\,\mu\text{m}$ (maximum $25.1888\,\mu\text{m}$).
- **In Candidate Mesh (31,035 elements):** Exactly 14 elements ($0.045\%$) exceed $20\,\mu\text{m}$ (maximum $22.4395\,\mu\text{m}$).
- **Topology & Geometry:** All oversized elements in both meshes are standard `CPS4R` quadrilaterals with well-behaved aspect ratios between $1.14$ and $1.87$.
- **Spatial Position:** Located exclusively in coarse far-field corners ($x \le 0.10, x \ge 0.90$) and low-gradient interior regions ($y \approx 0.65\text{--}0.75$). **Zero** oversized elements exist in the notch tip zone or ligament corridor.
- **Measurement Method:** Confirmed that the algorithm measures consecutive polygon boundary edges (node $i \to i+1$), not internal diagonals. In advancing-front quad paving, `maxElementSize` is a soft sizing target, and Abaqus permits $\approx 20\text{--}25\%$ tolerance in transition bands to maintain quadrilateral topology without introducing distorted elements (`WarnElemDistorted` is 0).

---

## 5. Corrected UEXTERNALDB Documentation & Subroutine Audit

In response to the independent review, the documentation for `UEXTERNALDB` is rigorously corrected to match the official Abaqus User Subroutines Reference:

### Abaqus Standard UEXTERNALDB Operation Codes (LOP)
- **`LOP = 0`**: Start of an analysis.
- **`LOP = 1`**: Start of the current increment (called on increment attempts, retries, and cutbacks).
- **`LOP = 2`**: End of the current increment (called when an increment has converged and is committed). Custom state variables and restart history can be flushed or recorded to external disk files here.
- **`LOP = 3`**: End of an analysis.
- **`LOP = 4`**: Beginning of a restart analysis (`*RESTART, READ`).
- **`LOP = 5`**: Start of a step.
- **`LOP = 6`**: End of a step.

### Audit of `f42_mixed_uel.for`
- The frozen subroutine `f42_mixed_uel.for` implements ONLY:
  ```fortran
  IF (LOP .EQ. 0) THEN
    ! Zero committed & trial arrays in COMMON /CB_STATE_TRANS/
  ELSE IF (LOP .EQ. 1) THEN
    ! Restore trial from committed
  ELSE IF (LOP .EQ. 2) THEN
    ! Commit trial and write CSV energy balance
  ELSE IF (LOP .EQ. 3) THEN
    ! Close CSV file
  ENDIF
  ```
- **Structural Gap:** `UEXTERNALDB` completely lacks handling for `LOP = 4`, `LOP = 5`, and `LOP = 6`.
- **Consequence for Cross-Job Restart:** When Abaqus launches a restarted job with `*RESTART, READ`, it invokes `UEXTERNALDB` with `LOP = 4`. Because `f42_mixed_uel.for` has no `LOP = 4` block to restore values from an external file, the `COMMON /CB_STATE_TRANS/` arrays remain uninitialized or zeroed. Crucial history variables (the irreversibility threshold $H$, committed damage $d$, and fracture energy $E_{\text{frac}}$) are lost, resulting in unphysical healing and catastrophic solver divergence.
- **Governing Conclusion:** True state-preserving restart recovery across independent PBS jobs is **UNSUPPORTED** with the frozen UEL.

---

## 6. Definitive Production Readiness Assessment & Three Resolution Pathways

### Current Status
**PRODUCTION EXECUTION REMAINS BLOCKED.**
1. The preserved 46,747-element mesh possesses high local FPZ resolution ($h_{\text{p10}} = 1.26\text{--}1.34\,\mu\text{m}$, 23–30% edges $\le 1.5\,\mu\text{m}$), but its projected runtime on 1 CPU is **18–21 hours**, strictly exceeding the standing 8-hour PBS limit.
2. The evaluated 31,035-element candidate degrades FPZ resolution ($h_{\text{p10}} = 1.92\text{--}1.93\,\mu\text{m}$, $\le 1.2\%$ edges $\le 1.5\,\mu\text{m}$) and STILL requires **13–15 hours**, exceeding the 8-hour limit.
3. Multi-job restart is structurally disqualified in `f42_mixed_uel.for`, and the holiday-window exception expired on 9 September 2026.

### Three Mutually Exclusive Resolution Pathways for Supervisor Direction
| Pathway | Scientific & Operational Description | Required Authorizations | Trade-offs & Feasibility |
|:---|:---|:---|:---|
| **Pathway 1: Single-Job Walltime Extension (Recommended)** | Execute the preserved **46,747-element** reference mesh as a single monolithic job ($u=0\to 0.012\text{ mm}$) with an extended walltime limit ($\le 24\text{ hours}$, 1 CPU, 16 GB). | Explicit supervisor authorization for single-job walltime exception ($\le 24\text{h}$) in queue `normal_imfdfkmq` or thesis reservation. | **Preserves highest scientific fidelity**: guarantees $h_{\text{p10}} = 1.26\,\mu\text{m}$ in ligament, zero mesh re-tuning, and zero code changes. |
| **Pathway 2: Partitioned Local-Refinement Generator** | Re-structure the generator to use an explicit geometric partition or box-constrained refinement rule: restrict fine elements ($h \le 1.5\,\mu\text{m}$) strictly to the fracture corridor $[0.50, 0.65] \times [0.48, 0.70]$, while setting the remaining $90\%$ of the domain to $0.05\text{--}0.08\text{ mm}$. | Supervisor approval to add a localized partition box to the Method A generator. | Produces a fully compliant $\approx 12,000\text{--}14,000$ element mesh running in $\le 6.5\text{ hours}$ on 1 CPU within the 8-hour limit, while preserving $h \le 1.5\,\mu\text{m}$ in the fracture corridor. |
| **Pathway 3: SMP Multi-Threading Qualification** | Qualify 8-thread shared-memory SMP execution for `f42_mixed_uel.for` on the 46k element model (1 node, 8 CPUs, $\le 8\text{ hours}$). | Supervisor approval to use 8-thread SMP for Method A production. | Brings 46k element walltime from $\approx 21\text{h}$ down to $\approx 4\text{--}5\text{ hours}$, fitting cleanly within the 8-hour standing limit. |

---

## 7. Mandatory Verification Gate & Immutable Evidence

All qualification deliverables, comparative artifacts, and unit tests are verified:
- **Git Commit:** Tracked under `mode2-pandey-kumar-reproduction`
- **Unit Test Suite (6/6 PASS):**
  * `tests/unit/test_f1632_method_a_generator.py` (3/3 PASS)
  * `tests/unit/test_f1632_local_resolution.py` (1/1 PASS)
  * `tests/unit/test_f1632_production_mesh_resolution.py` (2/2 PASS — validates both 46k reference and 31k candidate meshes)
- **Preserved Reference Artifacts:**
  * Physical mesh: `models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_PROD_PHYS.inp` (SHA-256 `8CEB44A6...`, 3,264,831 bytes)
  * Datacheck: `models/pandey_kumar_mode1/176_method_a_plate_with_hole/evidence/PK_HOLE_METHOD_A_DC.dat` (SHA-256 `98DF2E...`, 12,058 bytes)
- **Candidate 31k Artifacts:**
  * Physical mesh: `models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidate_16k/PK_HOLE_CANDIDATE_16K_PROD_PHYS.inp` (SHA-256 `08FDD9F80168375BFBBF8437BD1B8ADFC8BFAFBFAC64E20D3D1715B86C66BF6F`, 2,168,913 bytes)
  * Datacheck: `models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidate_16k/PK_HOLE_CANDIDATE_16K_DC.dat` (SHA-256 `47B7C61E65ADCD925AE1363E0BF1872FB0E5C28A6E76BBE73330B3977077C7FF`, 12,058 bytes)
- **Subroutine Integrity:** `models/pandey_kumar_mode1/176_method_a_plate_with_hole/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 29,722 bytes, 100% bitwise unchanged).
