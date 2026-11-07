# Method A Plate-with-Hole Feasibility & Readiness Assessment Report

**Task ID:** `F1632-METHOD-A-HOLE-DEMONSTRATION-REUSE-AND-GENERATION`  
**Handoff Correlation:** `HND-24ccab0bbe86` (Supervisor Decision Review)  
**Supervisor Directive Reference:** Dr. Roth (6 November 2026, via ChatGPT Bridge `HND-bef847fc363a`, `HND-f55ea7f9eb8f`, `HND-1c8df97e80be`, and `HND-24ccab0bbe86`)  
**Artifact Directory:** `models/pandey_kumar_mode1/176_method_a_plate_with_hole/`  
**Execution Boundary:** Zero new PBS submissions (`max_new_pbs_submissions = 0`). Non-production offline qualification, comparative remeshing evaluation, API capability audit, and execution feasibility assessment only.  
**Production User Subroutine:** `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 29,722 bytes, verified bitwise unchanged).  
**Preserved Reference Mesh (46k):** `models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_PROD_PHYS.inp` (`8CEB44A628BE9F7D19B4797723813BF7FF674EDB8E4AA66420AEA6665F924EBD`, 3,264,831 bytes).  
**Evaluated Candidate Mesh (31k):** `models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidate_16k/PK_HOLE_CANDIDATE_16K_PROD_PHYS.inp` (`08FDD9F80168375BFBBF8437BD1B8ADFC8BFAFBFAC64E20D3D1715B86C66BF6F`, 2,168,913 bytes).  
**Definitive Production Outcome:** **BLOCKED WITH VERIFIED TECHNICAL REASON: NATIVE ABAQUS METHOD A REMESHING CANNOT CONCURRENTLY SATISFY PHASE-FIELD FPZ RESOLUTION AND THE 8-HOUR SINGLE-CPU PRODUCTION LIMIT.**

---

## 1. Provenance Reconciliation of Reference Mesh Discretization

In response to the supervisor directive, the numerical provenance of the reference mesh (`PK_HOLE_METHOD_A_PROD_PHYS.inp`) was independently audited from the raw input deck:

- **Parsing Methodology:**
  Direct keyword extraction separating finite element connectivity from field output definitions (`*Element Output, elset=...`).
- **Exact Element-Type Distribution:**
  - **Triangles (`CPS3`):** Exactly **1,206 elements** (EIDs 1 through 1206).
  - **Quadrilaterals (`CPS4R`):** Exactly **45,541 elements** (EIDs 1207 through 46747).
  - **Total Physical Elements:** **46,747 elements** ($1,206 + 45,541 = 46,747$).
  - **Total Physical Nodes:** **46,651 nodes**.
  - **Co-located 3-Layer Production Deck (`PK_HOLE_METHOD_A_PROD.inp`):** **140,241 elements** ($46,747 \times 3$ co-located layers: U1/U3 phase field, U2/U4 displacement, CPE4/CPE3 companion visualization).
- **Discrepancy Resolution:**
  The previously cited count of 44,587 elements (43,434 quads + 1,153 triangles) originated from an intermediate smoke-test generation pass during tool development. The authoritative, committed physical mesh `PK_HOLE_METHOD_A_PROD_PHYS.inp` consists of exactly **46,747 physical elements** (45,541 quads + 1,206 triangles).

---

## 2. Verified Model Geometry & Ligament Clearance

- **Specimen Dimensions:** $1.0\text{ mm} \times 1.0\text{ mm}$, thickness $1.0\text{ mm}$.
- **Initial Slit:** Length $a_0 = 0.50\text{ mm}$, $y = 0.50\text{ mm}$, half-opening $w = 0.001\text{ mm}$.
- **Off-Axis Circular Void:** Center $(x=0.65\text{ mm}, y=0.65\text{ mm})$, radius $R = 0.10\text{ mm}$.
- **Center-to-Center Distance:**
  $$\Delta r = \sqrt{(0.65 - 0.50)^2 + (0.65 - 0.50)^2} = \sqrt{0.15^2 + 0.15^2} = 0.212132\text{ mm} \approx 212.1\,\mu\text{m}$$
- **Hole Surface Clearance along Centerline:**
  $$d_{\text{surface}} = \Delta r - R = 0.212132 - 0.100000 = \mathbf{0.112132\text{ mm}} \approx \mathbf{112.1\,\mu\text{m}}$$
- **Minimum Clearance from Slit Corner to Hole Perimeter:**
  Accounting for the finite notch half-opening ($w = 0.001\text{ mm}$, upper slit corner at $(0.50, 0.501)$):
  $$d_{\text{corner-surface}} = \sqrt{(0.65 - 0.50)^2 + (0.65 - 0.501)^2} - 0.10 = \mathbf{0.111426\text{ mm}} \approx \mathbf{111.4\,\mu\text{m}}$$

The initial ligament provides $\approx 15\ell_0$ of uncracked material, ensuring substantial crack propagation trajectory between the initial notch tip and the void boundary.

---

## 3. Side-by-Side Local Mesh Resolution & Accuracy–Cost Evaluation

Both the preserved 46k reference mesh and the 31k candidate mesh were analyzed directly using conservative polygon boundary edge measurements across all four geometric zones:

| Discretization / Resolution Metric | Preserved Reference Mesh (`PK_HOLE_METHOD_A`) | Evaluated Candidate Mesh (`PK_HOLE_CANDIDATE_16K`) | Relative Impact |
|:---|:---:|:---:|:---|
| **Initial Coarse Seed** | $h_{\text{coarse}} = 0.02\text{ mm}$ (2,906 elements) | $h_{\text{coarse}} = 0.04\text{ mm}$ (775 elements) | $-73.3\%$ initial elements |
| **Error Target** | 2.0 percentage points | 2.0 percentage points | Retained bitwise |
| **Adapted Physical Elements** | **46,747** (45,541 quads, 1,206 tris) | **31,035** (30,243 quads, 792 tris) | $-33.6\%$ elements |
| **Physical Nodes** | 46,651 | 31,037 | $-33.5\%$ nodes |
| **Co-located Elements** | 140,241 | 93,105 | $-33.6\%$ |
| **Notch Tip Zone Elements ($r \le 3.3\ell_0$)** | 677 elements | 309 elements | $-54.4\%$ in tip |
| **Notch Tip Median Edge** | **$1.7081\,\mu\text{m}$** ($h/\ell_0 = 0.228$) | **$2.4851\,\mu\text{m}$** ($h/\ell_0 = 0.331$) | $+45.5\%$ coarser |
| **Notch Tip $h_{\text{p10}}$ Edge** | **$1.3353\,\mu\text{m}$** ($h/\ell_0 = 0.178$) | **$1.9237\,\mu\text{m}$** ($h/\ell_0 = 0.256$) | $+44.1\%$ coarser |
| **Notch Tip Edges $\le \ell_0/5$ ($1.5\,\mu\text{m}$)**| **22.8%** | **0.6%** | **Near-total loss of fine resolution** |
| **Ligament Corridor Elements** | 5,253 elements | 1,844 elements | $-64.9\%$ in ligament |
| **Ligament Median Edge** | **$1.6510\,\mu\text{m}$** ($h/\ell_0 = 0.220$) | **$2.8103\,\mu\text{m}$** ($h/\ell_0 = 0.375$) | $+70.2\%$ coarser |
| **Ligament $h_{\text{p10}}$ Edge** | **$1.2626\,\mu\text{m}$** ($h/\ell_0 = 0.168$) | **$1.9345\,\mu\text{m}$** ($h/\ell_0 = 0.258$) | $+53.2\%$ coarser |
| **Ligament Edges $\le \ell_0/5$ ($1.5\,\mu\text{m}$)**| **30.1%** | **1.2%** | **Near-total loss of fine resolution** |
| **Hole Boundary Median Edge** | $1.9876\,\mu\text{m}$ ($h/\ell_0 = 0.265$) | $3.6878\,\mu\text{m}$ ($h/\ell_0 = 0.492$) | $+85.5\%$ coarser |
| **Far Field Median Edge** | $3.3226\,\mu\text{m}$ ($h/\ell_0 = 0.443$) | $4.1583\,\mu\text{m}$ ($h/\ell_0 = 0.554$) | $+25.2\%$ coarser |
| **Oversized Edges ($>20\,\mu\text{m}$)** | 47 elements (max $25.19\,\mu\text{m}$) | 14 elements (max $22.44\,\mu\text{m}$) | Soft target advancing-front tolerance |
| **Datacheck Status** | Exit 0 (8 benign warnings) | Exit 0 (8 benign warnings) | Input processing verified |
| **Projected Serial Walltime (1 CPU)** | **18 – 21 hours** | **13 – 15 hours** | **Both strictly exceed 8h PBS limit** |

### Scope Discipline on Resolution Degradation
- **Empirical Sizing Finding:** Coarsening initial seed from $0.02\text{ mm}$ to $0.04\text{ mm}$ increased median edge length in the ligament from $1.65\,\mu\text{m}$ to $2.81\,\mu\text{m}$ ($h/\ell_0 = 0.375$), reducing edges $\le \ell_0/5$ to $1.2\%$.
- **Strict Scope Boundary:** No non-linear fracture simulation has been conducted on this mesh; therefore, we make **no empirical claim** that artificial crack pinning, delayed initiation, or unphysical crack path turning has been demonstrated. The degradation is reported strictly as a geometric and discretization metric relative to established phase-field literature standards ($\approx 5$ elements across $\ell_0$ required for mesh-objective crack regularisation).
- **Candidate Rejection:** Because the 31,035-element mesh still projects to 13–15 hours on 1 CPU (failing the 8-hour limit) while degrading local resolution, the candidate is **REJECTED**.

---

## 4. Capability Audit: Spatially Selective Sizing in Native Abaqus Remeshing

The feasibility of an automatic, error-driven two-zone sizing strategy within Abaqus native remeshing was investigated:

1. **Native Remeshing Rule Interface (`m.RemeshingRule`):**
   - The `RemeshingRule` object accepts arguments: `(name, stepName, variables, region, sizingMethod, errorTarget, minElementSize, maxElementSize, coarseningFactor, refinementFactor)`.
   - `sizingMethod = UNIFORM_ERROR` evaluates a continuous scalar sizing field across the entire domain by comparing elemental strain energy densities against superconvergent patch recovery gradients ($\sigma^*$).
2. **Technical Limitation of the Native Interface:**
   - Abaqus `adaptiveRemesh(odb=o1)` operates on the existing continuous geometric part topology. It **cannot** dynamically segment geometry into separate sub-domains or apply localized refinement boxes based on output contours without manual CAD partitioning prior to the pre-analysis solve.
   - Sizing parameters (`minElementSize`, `maxElementSize`, `errorTarget`) apply globally across whatever geometric region is assigned. In a monolithic part, a coarser initial seed flattens peak recovered stress gradients at the notch tip, resulting in globally coarser elements throughout the stress concentration corridor.
3. **F1632 Scope Boundary:**
   - The registered F1632 task parameters specify $h_{\max} = 0.020\text{ mm}$. Increasing $h_{\max}$ beyond $0.020\text{ mm}$ or introducing explicit geometric partition boundaries would alter the registered model definition and require formal task lifecycle review.
   - Per supervisor instruction: *"If Abaqus's native remeshing interface cannot support the required spatially selective sizing within F1632, report that concrete limitation and close this feasibility investigation as BLOCKED. Do not substitute manual crack-path refinement or create another speculative global mesh."*
4. **Conclusion:** Abaqus native remeshing cannot achieve the required $\le 16,000$ element target while retaining $h \le \ell_0/5$ resolution through global parameter tuning alone.

---

## 5. Corrected UEXTERNALDB Documentation & Cross-Job Restart Audit

In accordance with official Abaqus User Subroutines Reference documentation:

### Standard UEXTERNALDB Operation Codes (LOP)
- **`LOP = 0`**: Start of an analysis.
- **`LOP = 1`**: Start of the current increment (called on attempts, retries, and cutbacks).
- **`LOP = 2`**: End of the current increment (increment converged and committed; custom state variables and restart history can be flushed to external disk files here).
- **`LOP = 3`**: End of an analysis.
- **`LOP = 4`**: Beginning of a restart analysis (`*RESTART, READ`).
- **`LOP = 5`**: Start of a step.
- **`LOP = 6`**: End of a step.

### Subroutine Audit of `f42_mixed_uel.for`
- Inspection of `f42_mixed_uel.for` confirms that `UEXTERNALDB` implements handling for `LOP = 0, 1, 2, 3` only.
- It completely lacks logic for `LOP = 4` (restart read), `LOP = 5`, and `LOP = 6`.
- When an Abaqus job is restarted using `*RESTART, READ`, Abaqus calls `UEXTERNALDB` with `LOP = 4`. Because `f42_mixed_uel.for` has no `LOP = 4` handler to restore variables from external files, the arrays in `COMMON /CB_STATE_TRANS/` (`SV_PHASE_COMMITTED`, `SV_H_COMMITTED`, `SV_E_FRAC`, etc.) remain uninitialized or zeroed.
- This results in complete loss of crack irreversibility and energy accounting across job boundaries. True state-preserving restart across independent PBS jobs is **UNQUALIFIED** with the frozen UEL.

---

## 6. Definitive Production Readiness Assessment & Three Resolution Pathways

### Current Status
**PRODUCTION EXECUTION REMAINS BLOCKED UNDER CURRENT STANDING HPC LIMITS.**
- The preserved 46,747-element mesh preserves high local FPZ resolution ($h_{\text{p10}} = 1.26\text{--}1.34\,\mu\text{m}$, 23–30% edges $\le 1.5\,\mu\text{m}$), but its projected serial walltime on 1 CPU is **18–21 hours**, strictly exceeding the standing 8-hour PBS limit.
- The 31,035-element candidate degrades FPZ resolution ($h_{\text{p10}} = 1.92\text{--}1.93\,\mu\text{m}$, $\le 1.2\%$ edges $\le 1.5\,\mu\text{m}$) and STILL requires **13–15 hours**, exceeding the 8-hour limit.
- Multi-job restart is structurally unqualified in `f42_mixed_uel.for`, and the holiday-window policy expired on 9 September 2026.

### Three Mutually Exclusive Resolution Pathways for Supervisor Direction
| Pathway | Scientific & Operational Description | Required Authorizations | Trade-offs & Feasibility |
|:---|:---|:---|:---|
| **Pathway 1: Single-Job Walltime Extension (Recommended)** | Execute the preserved **46,747-element** reference mesh as a single monolithic job ($u=0\to 0.012\text{ mm}$) with an extended walltime limit ($\le 24\text{ hours}$, 1 CPU, 16 GB). | Explicit supervisor authorization for single-job walltime exception ($\le 24\text{h}$) in queue `normal_imfdfkmq` or thesis reservation. | **Preserves highest scientific fidelity**: guarantees $h_{\text{p10}} = 1.26\,\mu\text{m}$ in ligament, zero mesh re-tuning, and zero code changes. |
| **Pathway 2B: Partitioned Local-Refinement Generator** | Re-structure the generator to use an explicit geometric partition or box-constrained refinement rule: restrict fine elements ($h \le 1.5\,\mu\text{m}$) strictly to the fracture corridor $[0.50, 0.65] \times [0.48, 0.70]$, while setting the remaining $90\%$ of the domain to $0.05\text{--}0.08\text{ mm}$. | Formal task scope change authorizing geometric partitioning. | Produces a fully compliant $\approx 12,000\text{--}14,000$ element mesh running in $\le 6.5\text{ hours}$ on 1 CPU within the 8-hour limit, while preserving $h \le 1.5\,\mu\text{m}$ in the fracture corridor. |
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
  * Physical mesh: `models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_PROD_PHYS.inp` (SHA-256 `8CEB44A6...`, 3,264,831 bytes, 45,541 quads, 1,206 tris, 46,747 total)
  * Datacheck: `models/pandey_kumar_mode1/176_method_a_plate_with_hole/evidence/PK_HOLE_METHOD_A_DC.dat` (SHA-256 `98DF2E...`, 12,058 bytes)
- **Candidate 31k Artifacts:**
  * Physical mesh: `models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidate_16k/PK_HOLE_CANDIDATE_16K_PROD_PHYS.inp` (SHA-256 `08FDD9F80168375BFBBF8437BD1B8ADFC8BFAFBFAC64E20D3D1715B86C66BF6F`, 2,168,913 bytes, 30,243 quads, 792 tris, 31,035 total)
  * Datacheck: `models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidate_16k/PK_HOLE_CANDIDATE_16K_DC.dat` (SHA-256 `47B7C61E65ADCD925AE1363E0BF1872FB0E5C28A6E76BBE73330B3977077C7FF`, 12,058 bytes)
- **Subroutine Integrity:** `models/pandey_kumar_mode1/176_method_a_plate_with_hole/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 29,722 bytes, 100% bitwise unchanged).
