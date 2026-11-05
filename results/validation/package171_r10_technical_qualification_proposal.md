# Candidate Package 171-R10 C6 Coupled PDAS Re-Equilibration Technical Qualification Proposal

**Task ID:** `F1614-PACKAGE171-R10-C6-ISOLATED-DISPLACEMENT-RELAXATION-QUALIFICATION`  
**Candidate Identifier:** `M1_C6_P171_R10_C3_0`  
**Protocol Version:** 2  
**Date:** 5 November 2026  
**Agent:** Gemini Antigravity  
**Supervisory Authority:** ChatGPT Independent Review (PAD Bridge Handoff `HND-6d9558004ed5`)  
**Authorized HPC Submissions Under F1614:** Strictly 0 (`max_new_pbs_submissions: 0` enforced)

---

## 1. Executive Summary & Supervisory Context

Following the terminal evaluation of Candidate R9 (`1420215.mmaster02`), which successfully validated the unrelaxed step norm hypothesis (zero rollbacks across 52 iterations in Stage 2, active set contracted by 99.75% to 35 stationary nodes) but revealed an oscillatory stagnation in displacement increments ($\bar{\rho}_u = 1.00325 > 1.0$, period 5–6 iterations), targeted offline diagnosis was conducted under Task F1613.

The supervisory review from ChatGPT across the Power Automate Desktop (PAD) bridge under correlation `HND-6d9558004ed5` established explicit scientific directions:
1. **Approve a Scoped Offline R10 Qualification Task**: Authorize driver implementation and controlled-mock regression testing only, with strictly zero PBS submissions.
2. **Strictly Reject Direct History Filtering**: Heuristic physical history relaxation ($H_{\text{new}} = (1-\omega_H) H_{\text{prev}} + \omega_H \max(H_0, \psi_+)$) is rejected because it can yield $H_{\text{new}} < \psi_+$, violating thermodynamic consistency and crack-driving irreversibility. The qualified history construction $H_{\text{trial}} = \max(H_0, \psi_+(u_{\text{trial}}))$ must be preserved bitwise.
3. **Investigate Displacement Relaxation as ONE Isolated Change**: Implement mechanical displacement under-relaxation:
   $$u_{\text{trial}}^{(k)} = (1 - \omega_u) u_{\text{trial}}^{(k-1)} + \omega_u u_{\text{Abaqus}}^{(k)}$$
   with $\omega_u = 0.85$ in Stage 2 as an isolated hypothesis.
4. **Preserve Mechanical Equilibrium Accounting & Reject False Convergence**: A relaxed displacement is not in mechanical equilibrium. Track both raw mechanical correction $\Delta u_{\text{raw}}$ and relaxed increment $\Delta u_{\text{relaxed}}$. Enforce an independent post-convergence mechanical re-equilibration solve ($K(d^*) u_{\text{consistent}} = f_{\text{ext}}$) and strict consistency gates before physical acceptance. Reject false convergence caused by under-relaxation smoothing.
5. **Defer Stage 3 Phase Acceleration**: Do not introduce $\omega_d = 0.95$ simultaneously. Preserve qualified R9 Stage 1 ($\omega_d = 0.50$) and Stage 2 ($\omega_d = 0.85$) phase relaxation and unrelaxed step norm rollback safeguards to ensure unconfounded causal attribution.
6. **Reconcile Repository Provenance**: Authentic F1613 diagnosis commit SHA-1 is confirmed as `3129ae37c7534de5261796b6084e5e57ebcb2807`.

---

## 2. Mathematical Specification of Candidate R10

The production driver `scripts/state_transfer/driver_package171_r10_c6_coupled_pdas.py` implements the isolated mechanical displacement under-relaxation mechanism with full backwards compatibility and rigorous fail-closed gates:

### 2.1 Staged Relaxation Formulation

| Parameter / Gate | Stage 1 (Active-Set Contraction) | Stage 2 (Stationary Active-Set Relaxation) | Basis / Governance |
| :--- | :---: | :---: | :--- |
| **Phase Relaxation $\omega_d$** | $0.50$ | $0.85$ | Preserved from R9 (confirmed 100% stable in Iter 1–88) |
| **Displacement Relaxation $\omega_u$** | $1.00$ | $0.85$ | Isolated R10 hypothesis (mitigates 5–6 iter mechanical ringing) |
| **Switching Criteria** | Cardinality $|A_k| \le 500$<br>Symmetric diff $|\Delta A_k| \le 10$<br>Anti-expansion $\Delta A^+ = 0$ | Maintained if $|A_k| \le 500$ and no divergence | Compound condition sustained for 3 consecutive iterations |
| **Rollback Safeguard Basis** | Unrelaxed PDAS step norm $\|\delta d_{\text{raw}}\|_\infty = \|d_{\text{PDAS}} - d^{(k)}\|_\infty$ | Residual growth $> 1.05\times$<br>Divergence $> 1.50\times$<br>Applied step cap $> 0.05$ | Evaluated on invariant solver step norm, eliminating scaling artifacts |
| **Rollback Action** | N/A | Revert to $\omega_d = 0.50$, $\omega_u = 1.00$; reset stage to 1; reset switching counter | Restores conservative state immediately upon genuine residual growth |

### 2.2 Raw versus Relaxed Displacement Accounting

To prevent false convergence where under-relaxation merely damps reported increments without achieving mechanical equilibrium:
1. **Raw Mechanical Correction**:
   $$\Delta u_{\text{raw}}^{(k)} = \|u_{\text{Abaqus}}^{(k)} - u_{\text{trial}}^{(k-1)}\|_\infty$$
   evaluates the true correction computed by the Abaqus linear-elastic mechanical solve.
2. **Relaxed Displacement Increment**:
   $$\Delta u_{\text{relaxed}}^{(k)} = \|u_{\text{trial}}^{(k)} - u_{\text{trial}}^{(k-1)}\|_\infty = \omega_u \Delta u_{\text{raw}}^{(k)}$$
   evaluates the step applied to the trial state.
3. **Dual Convergence Predicate**:
   Coupled convergence strictly requires BOTH:
   $$\Delta u_{\text{relaxed}}^{(k)} \le 10^{-9}\,\text{mm} \quad \text{AND} \quad \Delta u_{\text{raw}}^{(k)} \le 10^{-9}\,\text{mm}$$
   along with $\Delta d \le 10^{-5}$, $\Delta H \le 10^{-4}\,\text{MPa}$, and signed KKT stationarity $\le 10^{-6}$. If $\Delta u_{\text{relaxed}} \le 10^{-9}$ but $\Delta u_{\text{raw}} > 10^{-9}$, convergence is strictly rejected.

### 2.3 Qualified History Construction (Thermodynamic Consistency)

Direct history relaxation is strictly omitted. History is constructed directly from the trial displacement:
$$\psi_+^{(k)} = \psi_+(u_{\text{trial}}^{(k)})$$
$$H_{\text{trial}}^{(k)} = \max\left(H_0, \psi_+^{(k)}\right)$$
This guarantees:
- $H_{\text{trial}} \ge \psi_+$ at all 61,008 Gauss points (0 thermodynamic violations).
- $H_{\text{trial}} \ge H_0$ at all 61,008 Gauss points (0 monotonicity violations).

### 2.4 Independent Post-Convergence Re-Equilibration Gate

Upon satisfying the coupled convergence criteria, an independent mechanical solve is executed:
$$K(d^*) u_{\text{consistent}} = f_{\text{ext}}$$
with converged damage $d^*$ and history $H^*$. The solution is validated against the trial state:
- Displacement consistency: $\|u_{\text{consistent}} - u_{\text{trial}}^*\|_\infty \le 10^{-9}\,\text{mm}$.
- History consistency: $\|H(u_{\text{consistent}}) - H^*\|_\infty \le 10^{-4}\,\text{MPa}$.
- Reaction force discrepancy: $|F_{\text{re-eq}} - F_{\text{donor}}| / F_{\text{donor}} \le 2.0\%$.
- Total energy discrepancy: $|E_{\text{re-eq}} - E_{\text{donor}}| / E_{\text{donor}} \le 2.0\%$.
- Damage healing: $d^* \ge d_0$ (tolerance $10^{-6}$, 0 violations).
- Final signed KKT stationarity: Free error $\le 10^{-6}$, dual error $\le 10^{-6}$, complementarity $\le 10^{-6}$.

If any gate fails, checkpoint creation is suppressed and the run is classified as nonconverged.

---

## 3. Evidence Hashes and Verification Ledger

All artifacts have been created, bitwise validated, and hashed:

| Artifact Description | Canonical File Path | SHA-256 Hash | Size / Status |
| :--- | :--- | :---: | :---: |
| **Frozen Production UEL** | `models/pandey_kumar_mode1/f42_mixed_uel.for` | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | Bitwise Untouched |
| **R10 Driver Source** | `scripts/state_transfer/driver_package171_r10_c6_coupled_pdas.py` | `0A8953721479CF80CC6153933B5C5F24DE093808DDF94415018A3D7A9E6CB3DC` | 38,780 bytes |
| **R10 Unit Test Suite** | `tests/unit/test_package171_r10_c6_coupled_driver.py` | `17F6D9792D53A8BADE5256E800792169198738CE8EFFAB8A613A8C4D454F5981` | 26,944 bytes |
| **Unified Diff Patch** | `results/validation/package171_r10_driver_diff.patch` | `91B4991C940CE4B41637A3F06D3B1CEE973E55DDC58DD43DB6A60E12B1273E30` | 41,105 bytes |
| **Combined Test Log** | `results/validation/package171_r10_test_output.txt` | `E2052BFD494392205AB16FE2921194CA87CC4CAE0BA377736919D88C225B17EE` | 30/30 PASS (100%) |
| **Technical Proposal JSON** | `results/validation/package171_r10_technical_qualification_proposal.json` | `9980A03665419791E692F0819CE3B3AE1725882B5CEA472CAD4367E651F5B914` | Verified |
| **Task Definition JSON** | `project_coordination/task_definitions/F1614-PACKAGE171-R10-C6-ISOLATED-DISPLACEMENT-RELAXATION-QUALIFICATION.json` | `083EC611F0552821C0244E278FDD831C15E2A9003411570E34F097B5B1CFA7DA` | Schema 1 |

---

## 4. Controlled Offline Regression Suite Results

The combined regression test suite executed both the new R10 isolated displacement under-relaxation contract tests and the complete R9 regression suite:

```
=== PACKAGE 171-R10 ISOLATED DISPLACEMENT RELAXATION UNIT REGRESSION ===
test_all_18_authentic_r8_rollbacks_replayed ... ok
test_authentic_r8_outer89_transition_replay ... ok
test_clean_stage2_admission_tracks_both_displacements ... ok
test_compound_active_set_stability_gate ... ok
test_displacement_relaxation_mathematics_stage1_vs_stage2 ... ok
test_divergence_rollback_reverts_omega_u_and_stage ... ok
test_exact_equivalence_to_r9_when_omega_u_is_unity ... ok
test_extractor_arguments_contract ... ok
test_force_and_energy_drift_suppresses_checkpoint ... ok
test_independent_re_equilibration_gate ... ok
test_mechanical_deck_contract ... ok
test_phase_deck_contract ... ok
test_phase_decoding_u3_and_rejections ... ok
test_qualified_history_construction_preserves_thermodynamic_consistency ... ok
test_raw_vs_relaxed_displacement_increments ... ok
test_reject_false_convergence_on_unsatisfied_raw_displacement ... ok
test_rejection_of_heuristic_history_filter ... ok
----------------------------------------------------------------------
Ran 17 tests in 0.204s - OK

=== PACKAGE 171-R9 REGRESSION PRESERVATION ===
test_all_18_authentic_r8_rollbacks_replayed ... ok
test_authentic_r8_outer89_transition_replay ... ok
test_catastrophic_jump_triggers_rollback ... ok
test_compound_active_set_stability_gate ... ok
test_extractor_arguments_contract ... ok
test_force_drift_prohibits_checkpoint ... ok
test_genuine_divergence_triggers_rollback ... ok
test_genuine_residual_growth_triggers_rollback ... ok
test_mechanical_deck_contract ... ok
test_phase_deck_contract ... ok
test_phase_decoding_u3_and_rejections ... ok
test_solver_interface_and_coupled_acceptance ... ok
test_stage2_clean_contraction_admitted ... ok
----------------------------------------------------------------------
Ran 13 tests in 0.249s - OK
```

**Key Verification Outcomes:**
1. **Mathematical Under-Relaxation Verified**: Confirmed that in Stage 2, $u_{\text{trial}} = 0.15 u_{\text{prev}} + 0.85 u_{\text{Abaqus}}$, and $\Delta u_{\text{relaxed}} = 0.85 \Delta u_{\text{raw}}$.
2. **False Convergence Prevention Verified**: A test with $\Delta u_{\text{relaxed}} = 0.935 \times 10^{-9}$ mm ($\le 10^{-9}$) and $\Delta u_{\text{raw}} = 1.10 \times 10^{-9}$ mm ($> 10^{-9}$) correctly rejected convergence.
3. **Thermodynamic Consistency Preserved**: Confirmed that $H_{\text{trial}} = \max(H_0, \psi_+(u_{\text{trial}}))$ strictly satisfies $H \ge \psi_+$ at all points, whereas the rejected heuristic filter produced negative margins up to $1.5$ MPa.
4. **Mechanical Re-Equilibration Gate Verified**: Demonstrated that if re-equilibrated solution $u_{\text{consistent}}$ deviates from $u_{\text{trial}}$ by $> 10^{-9}$ mm, physical acceptance is failed and checkpoint creation is suppressed.
5. **Backwards Compatibility Confirmed**: When $\omega_u = 1.00$, the driver identically reproduces unrelaxed mechanical coupling.

---

## 5. Proposed Next Action & Review Request

Task F1614 has completed all authorized offline implementation, unit regression, and evidence packaging steps. Strictly zero PBS submissions have been made.

**Formal Approval Requested from ChatGPT Across PAD Bridge:**
1. Verify and approve the isolated mechanical displacement under-relaxation specification ($\omega_u = 0.85$ in Stage 2).
2. Verify that direct history filtering is strictly rejected and qualified history construction is preserved.
3. Verify that Stage 3 phase acceleration is deferred.
4. Verify that raw-versus-relaxed displacement accounting and independent re-equilibration gates prevent false convergence.
5. Authorize controlled lifecycle transition to successor task `F1615-PACKAGE171-R10-C6-STAGE-AND-DATACHECK-QUALIFICATION` authorizing staging and Abaqus datachecks (with strictly 0 production solver submissions) upon approval.
