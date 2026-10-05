# Task 6 Re-Entry Checklist: Authentic IMFD ABAQUSER Tool Integration

**Purpose:** This document defines the immediate, non-disruptive protocol to resume and finalize Thesis Task 6 as soon as the authentic ABAQUSER tool is supplied by IMFD.  
**Prerequisite State:**  
- Task 5 quantitative reproduction: **`PASSED`** (Authoritative Job: `1400395.mmaster02`).
- Task 5 nominal-1% preprocessing discrepancy: **`DOCUMENTED_UNRESOLVABLE_FROM_PUBLISHED_INFORMATION`** (Supervisor-accepted reproduction limitation).
- Task 6 companion bridge: **`COMPANION_VISUALIZATION_BRIDGE_FULLY_VERIFIED`** (Job: `1400408.mmaster02`).
- Task 6 governance status: **`BLOCKED_ON_AUTHENTIC_IMFD_ABAQUSER_ACCESS`**.
- Existing verified benchmark models: Available on cluster at `/home/pr21vyci/projects/adaptive-remeshing/models/`.

---

## Re-Entry Execution Sequence

### Phase 1: Ingestion, Cryptographic Provenance & Isolation
- [ ] **Step 1.1: Archive and Checksum Ingestion**
  - Place supplied ABAQUSER package into an isolated directory: `src/abaquser/upstream/`.
  - Compute SHA256 checksums of all source files, executables, and scripts using `Get-FileHash -LiteralPath '<file>' -Algorithm SHA256`.
  - Record origin metadata (sender, delivery date, commit/version identifier).
- [ ] **Step 1.2: Environment Setup & Build Check**
  - Follow supplied IMFD instructions to build/configure the tool in an isolated test environment.
  - Test command-line availability (`abaquser --version` or Python module import check).

---

### Phase 2: Benchmark Qualification on Verified Tiny Model
- [ ] **Step 2.1: Tiny UEL Test Run**
  - Execute the authentic ABAQUSER workflow on the existing verified 4-element benchmark model (`models/abaquser_visualization/qual_tiny/`).
  - Verify that the tool processes the tiny UEL output and produces reconstructed visualization output without error.
- [ ] **Step 2.2: Field Comparison on Tiny Model**
  - Extract the reconstructed phase field from the ABAQUSER visualization output.
  - Compare point-by-point against the raw UEL nodal displacement ($U3 \equiv d$) and companion `SDV14` ($d$) and `SDV15` ($g(d)$).
  - Verify that difference $\Delta d \le 10^{-6}$.

---

### Phase 3: Integration and Benchmark Application
- [ ] **Step 3.1: Application to Verified Benchmark Model**
  - Execute ABAQUSER according to documented interface instructions on the verified Mode-I benchmark:
    - Primary candidate: `PK_MODE1_PROPOSED_PFM_VIS` (Job `1400408.mmaster02`).
    - Alternative candidate: `PK_MODE1_PROPOSED_PFM` (Job `1400395.mmaster02`).
  - Verify that no unnecessary solver re-execution is launched.
- [ ] **Step 3.2: Runtime Telemetry Capture**
  - Record execution walltime, memory utilization, and log output.

---

### Phase 4: Quantitative Verification & CAE Visualization
- [ ] **Step 4.1: Multi-Frame Field Equivalence Audit**
  - Extract phase field from ABAQUSER-reconstructed model across matched benchmark frames:
    - $u = 0.0020\,\mathrm{mm}$ (linear elastic)
    - $u = 0.0050\,\mathrm{mm}$ (pre-peak localization)
    - $u = 0.005775\,\mathrm{mm}$ (peak load)
    - $u = 0.0070\,\mathrm{mm}$ (crack propagation)
    - $u = 0.0100\,\mathrm{mm}$ (complete specimen separation)
  - Quantify maximum and RMS differences between ABAQUSER field, raw UEL $U3$, and companion `SDV14` ($d$), and verify history field $\mathcal{H}$ against companion `SDV16` ($\mathrm{kN/mm^2} = \mathrm{J/mm^3}$).
- [ ] **Step 4.2: Abaqus/CAE Viewport Export**
  - Render viewport contour plots using identical color maps and camera viewpoints.
  - Compare visual clarity and boundary smoothness between ABAQUSER and companion UMAT renderings.

---

### Phase 5: Final Task-6 Acceptance Decision & Thesis Closeout
- [ ] **Step 5.1: Update Decision Record**
  - Update `docs/decisions/TASK6_VISUALIZATION_WORKFLOW_AND_INTERFACE_DECISION.md` from `TASK6_BLOCKED_EXTERNAL_ABAQUSER_DEPENDENCY` / `BLOCKED_ON_AUTHENTIC_IMFD_ABAQUSER_ACCESS` to `SCIENTIFICALLY_ACCEPTED`.
- [ ] **Step 5.2: Synchronize Repositories**
  - Update `ACTIVE_TASK.json`, `HPC_JOB_LEDGER.csv`, `TASK6_IMFD_ABAQUSER_INTEGRATION_REPORT.md`, and supervisor reports.
- [ ] **Step 5.3: Authorization to Transition to Task 7**
  - Formally unblock Task 7 (mesh and load increment sensitivity) upon human authorization.
