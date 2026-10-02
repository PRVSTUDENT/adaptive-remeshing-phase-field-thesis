# Mode-I Gate-6 & Gate-5 Scientific Provenance and Integrity Correction Ledger

**Document Identifier**: `docs/supervisor_reports/CORRECTION_LEDGER_20260911.md`  
**Author**: Pruthviraja Reddy Vandavagali (Matriculation No. 68865)  
**Supervisors**: Prof. Dipl.-Ing. Björn Kiefer, Ph.D., and Dr.-Ing. Stephan Roth  
**Date**: September 11, 2026  
**Governing Directive**: *"We need to have understood everything related to the first model before we increase complexity."*  
**Scope**: Authoritative provenance correction and synchronization across all Mode-I deliverables, reproduction package assets, supervisor report documents, figures, manifests, and tracking states.

---

## 1. Executive Summary of Audit

During the final pre-submission provenance audit for the Mode-I benchmark deliverables, rigorous verification against the raw TUBAF HPC cluster solver logs (`PK_M1_NOM1_FULL_FRACTURE_WRAPPED.msg`, `.sta`, `.dat`, `.odb` from Job `1404306.mmaster02`) and source code repositories identified several epistemic and bookkeeping discrepancies:
1. An obsolete quad-only Fortran UEL had been copied into the reproduction package directory instead of the true authoritative mixed quad/triangle formulation.
2. Increment counts in working notes cited preliminary/attempted figures rather than authoritative converged increment counts.
3. Cutback counts derived from `.sta` attempt line counting differed from the official Abaqus `.msg` summary statement.
4. Work integrals lacked explicit common-overlap baseline comparison against the fixed-mesh reference anchor.
5. Solver cutback telemetry was at risk of being conflated with verified physical damage-field evolution before field-qualification Job `1404454` finishes.
6. A retired exploratory plane-stress test was clarified to prevent causal misattribution.
7. Claims regarding full-trajectory recovery were refined to maintain strict distinction between pre-peak response agreement and post-peak softening divergence.

All deliverables have been systematically audited, corrected, synchronized, and cryptographically verified.

---

## 2. Itemized Correction Ledger

### Item 1: Authoritative Mixed-Element UEL Source File (`f42_mixed_uel.for`)
- **Target Deliverable**: `ModeI_Supervisor_Report_Reproduction_Package/03_miseseri_native_refinement/nominal_1pct_requalification_71320/f42_mixed_uel.for`
- **Prior Defective State**:
  * File contained the legacy quad-only (`CPE4`, `JTYPE 1,2`) UEL formulation from the structured fixed-mesh model.
  * Size: 13,597 bytes (421 lines).
  * SHA-256: `ed1586d6427a4b1a01d99f7e219891ec7be9fe911e066d9360724942e7d27720`.
  * Defect Impact: Attempting to solve the 71,320-element mesh (which contains 1,877 linear triangles `CPE3` along refinement transition boundaries) with this UEL causes solver failure due to missing `JTYPE 3,4` formulations.
- **Corrected Authoritative State**:
  * File replaced with the true production mixed quad (`JTYPE 1,2`) and triangle (`JTYPE 3,4`) UEL formulation identical to the cluster execution runtime file.
  * Size: 21,138 bytes (664 lines).
  * SHA-256: `5abf77b570c67283f082e02d8ba2fd0111db843ad9c4cd3501eb9aaaf149dfdd`.
  * Supporting Evidence: Matches byte-for-byte with cluster runtime file `/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/82_gate6_adaptive_nominal_1pct_fracture/f42_mixed_uel.for`.

---

### Item 2: Converged Increment Bookkeeping (Job 1404306.mmaster02)
- **Target Deliverables**:
  * `CONDENSED_MODE1_BENCHMARK_SUPERVISOR_REPORT.md` (Section 5.3)
  * `nominal_1pct_requalification_71320/README.md` (Section 2)
  * `commands.txt` (Section 2.8)
  * `CURRENT_STATE.md` (Section 2.1)
  * `ACTIVE_TASK.json`
  * `fig5_computational_cost_and_convergence_summary.png` (Panel c)
- **Prior Ambiguous State**: Working notes occasionally cited "3,804 increments" or conflated the `.msg` statement `TOTAL OF 3784 INCREMENTS` as 3,784 converged increments.
- **Corrected Authoritative State**:
  * Step 1 (monotonic displacement to $u = 0.0050\,\text{mm}$): **2,000 converged increments**.
  * Step 2 (fracture propagation): **1,783 converged increments**.
  * Total successfully converged increments: **3,783 increments**.
  * Increment 1784 of Step 2 was attempted but never converged.
  * Distinction Clarified: The Abaqus `.msg` summary statement "TOTAL OF 3784 INCREMENTS" designates the total number of increment numbers opened/attempted, not the converged count.

---

### Item 3: Cutbacks in Automatic Incrementation (Job 1404306.mmaster02)
- **Target Deliverables**:
  * `CONDENSED_MODE1_BENCHMARK_SUPERVISOR_REPORT.md` (Section 5.3)
  * `nominal_1pct_requalification_71320/README.md` (Section 2)
  * `commands.txt` (Section 2.8)
  * `CURRENT_STATE.md` (Section 2.1)
  * `ACTIVE_TASK.json`
  * `fig5_computational_cost_and_convergence_summary.png` (Panel d)
- **Prior Preliminary State**: Cited "30 cutbacks" derived from counting attempt lines in the `.sta` file.
- **Corrected Authoritative State**: Exactly **21 cutbacks in automatic incrementation** per the authoritative solver `.msg` summary statement (`21 CUTBACKS IN AUTOMATIC INCREMENTATION`).

---

### Item 4: Common-Overlap External Boundary Work Comparison
- **Target Deliverables**:
  * `CONDENSED_MODE1_BENCHMARK_SUPERVISOR_REPORT.md` (Section 5.1 table footnote & Section 5.3)
  * `nominal_1pct_requalification_71320/README.md` (Section 2)
  * `commands.txt` (Section 2.8)
  * `CURRENT_STATE.md` (Section 2.1)
  * `ACTIVE_TASK.json`
- **Prior State**: $W_{\text{ext}} = 2.5726\,\text{mJ}$ was stated in isolation without comparing against the fixed reference anchor over the exact common displacement interval.
- **Corrected Authoritative State**:
  * Evaluated over the identical common overlap window $0 \le u \le 0.006774069\,\text{mm}$:
    - Corrected Nominal 1% (Job `1404306`): $W_{\text{ext}} = \mathbf{2.5726\,\text{mJ}}$
    - Fixed Reference Anchor (Job `1398090`): $W_{\text{ext}} = \mathbf{2.3583\,\text{mJ}}$
    - Difference: $\mathbf{+9.09\%}$ ($+0.2143\,\text{mJ}$).

---

### Item 5: Solver Observation vs. Physical Damage Cause Distinction
- **Target Deliverables**:
  * `CONDENSED_MODE1_BENCHMARK_SUPERVISOR_REPORT.md` (Section 5.3)
  * `nominal_1pct_requalification_71320/README.md` (Section 2)
  * `CURRENT_STATE.md` (Section 2.1)
  * `ACTIVE_TASK.json`
- **Prior Risk**: Framing terminal non-convergence at Step 2 Increment 1784 as an established physical damage mechanism.
- **Corrected Authoritative State**: Telemetry in `.msg` recording large displacement corrections to DOF 3 ($d$) at crack-tip node 61805 (largest correction $\Delta c_i = 0.05386$, increment $0.121$, residual force $-1.561 \times 10^{-3}\,\text{kN}$) during automatic cutback to $\Delta t < 10^{-14}\,\text{s}$ is strictly classified as a **numerical solver observation/symptom**. Physical damage-field evolution remains unresolved pending terminal completion of field-qualification Job `1404454`.

---

### Item 6: Pre-Peak Response Recovery vs. Full Trajectory Scope
- **Target Deliverables**:
  * `CONDENSED_MODE1_BENCHMARK_SUPERVISOR_REPORT.md` (Section 5.3 & Chapter 6 Figure 1)
  * `nominal_1pct_requalification_71320/README.md` (Section 2)
  * `fig1_full_fu_requalification_comparison.png`
  * `ACTIVE_TASK.json`
- **Prior Ambiguity**: Describing the requalification result as "trajectory alignment" without explicitly demarcating the post-peak divergence.
- **Corrected Authoritative State**: Explicitly states that Job `1404306` achieves **outstanding recovery of the pre-peak elastic and hardening branch** ($K_0$ within $-0.09\%$, $F_{\max}$ within $-1.64\%$, pre-peak $L_2$ error $0.000625\,\text{kN}$), but does **not** achieve full-trajectory recovery due to post-peak softening divergence and premature convergence termination at $u = 0.006774\,\text{mm}$.

---

### Item 7: Gate 5 Causal Exclusions & Formal Epistemic Status
- **Target Deliverables**:
  * `CONDENSED_MODE1_BENCHMARK_SUPERVISOR_REPORT.md` (Section 5.4 & Chapter 7)
  * `CURRENT_STATE.md` (Sections 1 & 3)
  * `ACTIVE_TASK.json`
- **Prior State**: Preliminary exploratory `CPS4` Plane Stress test was noted without clarifying that it had been retired/confounded.
- **Corrected Authoritative State**:
  * `CPS4` test is retired and excluded as an active causal explanation because the physical BVP is strictly plane strain `CPE4`. Software release invariance is verified solely by the clean `CPE4` exact-twin (Job `1404373`: 71,320 elements in both 2022 and 2023).
  * Gate 5 status is formally classified as `LITERATURE_EFFECTIVE_ERROR_TARGET_NOT_ESTABLISHED`.
  * The 4 missing literature facts (numerical errorTarget, free meshing algorithm, coarse mesh seed, element count limit) constitute the definitive external-information boundary; unstated parameters cannot be assumed without author confirmation.

---

### Item 8: Cryptographic Manifest Regeneration
- **Target Deliverable**: `ModeI_Supervisor_Report_Reproduction_Package/MANIFEST.sha256`
- **Audit Action**: Regenerated complete SHA-256 checksums across all 130 files in the reproduction package.
- **Verification**: All hashes verified with zero discrepancies.

---

## 3. Authoritative Cryptographic Checksum Reference

| Package File Path | File Description | Size (bytes) | SHA-256 Checksum |
| :--- | :--- | :---: | :--- |
| `03_miseseri_native_refinement/nominal_1pct_requalification_71320/f42_mixed_uel.for` | Mixed Quad/Triangle UEL | 21,138 | `5abf77b570c67283f082e02d8ba2fd0111db843ad9c4cd3501eb9aaaf149dfdd` |
| `03_miseseri_native_refinement/nominal_1pct_requalification_71320/PK_M1_NOM1_FULL_FRACTURE_WRAPPED.inp` | Wrapped Requalification Input Deck | 23,248,398 | `63580130f87803185c73b436779894361795856f1e4e931d76c6df8015c7b5eb` |
| `03_miseseri_native_refinement/nominal_1pct_requalification_71320/extract_terminal_requalification_1404306.py` | Extraction Pipeline Script | 8,829 | `55304f979805e48e1b0542208debd2948a64b29e5f07d38af1afe2884d72f579` |
| `03_miseseri_native_refinement/nominal_1pct_requalification_71320/curve_1404306_extracted.csv` | Reaction Force-Displacement Data | 158,565 | `95ec44c36d26956b0f47c4836a34bc81933ca998f59592e788c0051deb64634b` |
| `03_miseseri_native_refinement/nominal_1pct_requalification_71320/requalification_summary_1404306.json` | Mechanical Metrics Summary JSON | 2,746 | `87e18729a85c23d04f69065c682338c37fc7262ccca1b9fb14777347a270219d` |
| `03_miseseri_native_refinement/nominal_1pct_requalification_71320/README.md` | Requalification Package Guide | 6,114 | `b6548b7b28c2e2fac116832e617cd344e35c36a109d9bbe1bc1136293fce6d00` |
| `commands.txt` | Master Reproduction Commands | 20,096 | `182593778e91508f01f9a367ded8a2d97b2f8c13f50a95699b3c67b9ebff7fb6` |
| `MANIFEST.sha256` | Master Cryptographic Checksum Table | 16,967 | Generated across 130 files |

---

## 4. Preservation Invariant Status

- **Cluster Job `1404454.mmaster02` (`PK_M1_NOM1_FQ_SOLVE`)**:
  * Continues to execute undisturbed on `mnode097/0`.
  * Zero reads, writes, modifications, or duplicate executions were performed during this audit.
  * Field qualification post-processing will occur strictly after job reaches terminal state.
