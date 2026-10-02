# Session Report: F1085 — Final Source Provenance, Line-by-Line Subroutine Mapping, and Numerical Bookkeeping Audit

**Session ID:** `2026-09-28_1225_gemini-antigravity_F1085`  
**Agent:** `gemini-antigravity`  
**Task ID:** `F1085-SUPERVISOR-PACK-FINAL-SOURCE-AND-NUMERICAL-AUDIT-20260928`  
**Parent Commit:** `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`  
**Started:** `2026-09-28T12:14:00+02:00`  
**Completed:** `2026-09-28T12:25:00+02:00`  
**Classification:** `FINAL_SOURCE_AND_NUMERICAL_AUDIT_COMPLETE`

---

## 1. Executive Summary

A final, rigorous line-by-line Fortran source and numerical bookkeeping audit was performed on the Mode-I UEL energy formulation and supervisor meeting artifacts prior to the 01-Oct-2026 meeting:

1. **Fortran Source Provenance & Hash Reconciliation**:
   - Reconciled governed production user subroutine `f42_mixed_uel.for` (SHA-256 `5CD0D2C015C9EAD91C99D7A744156CC86F5B5EA26473BBED7D6E5515FE30FA46`, 901 lines, 29,401 bytes), which is deployed across all production energy cases (`15_energy_qualification_small`, `A3`, `A4`, `S3`).
   - Reconciled diagnostic variant `f42_mixed_uel_diagnostic.for` (SHA-256 `3C1B40035E85343C8B63214D8788EC16FD77D8BB3495CF3ED34C2F60147C5C1A`, 973 lines) with file-level CSV tracking (`uel_energy_balance.csv` in `UEXTERNALDB`).
   - Historical candidate reference hash `955d9d7dd1f6305a2e99f1a265691079d39e38e8ec436a504efea44be59c3620` does not exist in current disk trees or git commit objects and is classified as **`UNRESOLVED_HISTORICAL_HASH_PROVENANCE`**. The governed production source on disk across all production batches is bit-for-bit identical to `5CD0D2C015C9EAD91C99D7A744156CC86F5B5EA26473BBED7D6E5515FE30FA46` (29,401 bytes).

2. **Line-by-Line Subroutine Array & Variable Mapping**:
   - Verified exact line numbers in governed source `5CD0D2C015...`:
     - **Quad Phase (`JTYPE = 1`)**: `ENERGY(7) = E_FRAC_ELEM` (Line 366), `SV_E_FRAC(PHYSIDX) = E_FRAC_ELEM` (Line 367), `SV_PSI_F(PHYSIDX) = E_FRAC_ELEM / VOL_ELEM` (Line 369), `SVARS(17) = E_FRAC_ELEM` (Line 382), `SVARS(18) = SV_PSI_F(PHYSIDX)` (Line 383).
     - **Quad Mech (`JTYPE = 2`)**: `ENERGY(2) = E_ELAS_ELEM` (Line 542), `SV_E_ELAS(PHYSIDX) = E_ELAS_ELEM` (Line 543), `SV_PSI_E(PHYSIDX) = E_ELAS_ELEM / VOL_ELEM` (Line 545), `SVARS(17) = E_ELAS_ELEM` (Line 558), `SVARS(18) = SV_PSI_E(PHYSIDX)` (Line 559).
     - **Tri Phase (`JTYPE = 3`)**: `ENERGY(7) = E_FRAC_ELEM` (Line 652), `SV_E_FRAC(PHYSIDX) = E_FRAC_ELEM` (Line 653), `SV_PSI_F(PHYSIDX) = E_FRAC_ELEM / VOL_ELEM` (Line 655), `SVARS(17) = E_FRAC_ELEM` (Line 663), `SVARS(18) = SV_PSI_F(PHYSIDX)` (Line 664).
     - **Tri Mech (`JTYPE = 4`)**: `ENERGY(2) = E_ELAS_ELEM` (Line 809), `SV_E_ELAS(PHYSIDX) = E_ELAS_ELEM` (Line 810), `SV_PSI_E(PHYSIDX) = E_ELAS_ELEM / VOL_ELEM` (Line 812), `SVARS(17) = E_ELAS_ELEM` (Line 823), `SVARS(18) = SV_PSI_E(PHYSIDX)` (Line 824).
     - **Shared Memory Common Block**: `COMMON /CB_STATE_TRANS/` declared in `UEXTERNALDB` (Lines 76–80), `UEL` (Lines 183–187), and `UMAT` (Lines 854–858).
     - **Companion Visualizer UMAT (Layer 3, CPE4/CPS4)**: `STATEV(17) = SV_E_FRAC(PHYSIDX)` (Line 894), `STATEV(18) = SV_E_ELAS(PHYSIDX)` (Line 895), `STATEV(19) = SV_PSI_F(PHYSIDX)` (Line 896), `STATEV(20) = SV_PSI_E(PHYSIDX)` (Line 897).

3. **Rigorous Unit Semantics Reconciliation**:
   - Element scalar energies ($E_{\text{frac}}^{(e)}, E_{\text{elas}}^{(e)}$): evaluated natively in $\text{kN}\cdot\text{mm} \equiv \text{J}$. In report presentations, converted to $\text{mJ}$ via $10^3\times$ factor.
   - Energy densities ($\psi_f, \psi_e$): raw source algebra quotient `E_..._ELEM / VOL_ELEM` has dimension $\text{kN}\cdot\text{mm} / \text{mm}^2 = \text{kN/mm} = \text{J/mm}^2$ (energy per unit in-plane 2D area). Under the explicitly stated standard Abaqus plane-strain implicit unit-thickness convention ($B = 1.0\,\text{mm}$), the 3D element volume is $V_e = A_e \cdot (1.0\,\text{mm})$, making this numerically equivalent to volumetric energy density $\text{kN/mm}^2 = \text{J/mm}^3$. The raw quotient itself is strictly $\text{J/mm}^2 = \text{kN/mm}$ and is not described as GPa without stating the $B = 1.0\,\text{mm}$ thickness convention.

4. **Authoritative Numerical Bookkeeping Verification**:
   - Synchronized and verified all numerical data against Table 4 (Uniform cases at $u = 0.010\,\text{mm}$) and Table 5 (Matched-displacement audit across $S_1$--$S_4$) in `report_main.pdf`.
   - Replaced approximate/unverified numbers with exact audited metrics:
     - Table 4: $T_1$ ($\Delta_{\text{book}} = +0.00912\,\text{mJ}, +0.3783\%$), $T_2$ / $S_1$ ($\Delta_{\text{book}} = +0.01795\,\text{mJ}, +0.7607\%$), $T_3$ ($\Delta_{\text{book}} = +0.08256\,\text{mJ}, +3.5407\%$). Pre-peak $S_1/T_2$ $|\Delta_{\text{book}}| \le 0.008\%$.
     - Table 5: Matched $u = 5.50\,\mu\text{m}$ (Pre-peak): $S_1$ ($\Delta_{\text{book}} = -0.00014\,\text{mJ}$), $S_4$ ($\Delta_{\text{book}} = -0.00004\,\text{mJ}$). Matched $u = 5.85\,\mu\text{m}$ (Near-peak): $S_1$ at peak ($\Delta_{\text{book}} = -0.00018\,\text{mJ}$), $S_2$ ($\Delta_{\text{book}} = -0.08331\,\text{mJ}$), $S_4$ ($\Delta_{\text{book}} = -0.20588\,\text{mJ}$). Matched $u = 6.20\,\mu\text{m}$ (Post-peak): $S_1$ ($\Delta_{\text{book}} = +0.01754\,\text{mJ}, +0.74\%$), $S_2$ ($\Delta_{\text{book}} = -0.08325\,\text{mJ}$), $S_3$ ($\Delta_{\text{book}} = -0.16774\,\text{mJ}$), $S_4$ ($\Delta_{\text{book}} = -0.20585\,\text{mJ}, -9.49\%$).
     - Post-peak $E_{\text{frac}}$ stability: $S_1 \to S_4$ change at $u = 6.20\,\mu\text{m}$ is $2.33886\,\text{mJ}$ ($S_1$) $\to 2.37531\,\text{mJ}$ ($S_4$) ($+1.56\%$ relative to baseline $S_1$; full $S_1$--$S_4$ range: $S_1=2.33886\,\text{mJ}, S_2=2.33022\,\text{mJ}, S_3=2.35701\,\text{mJ}, S_4=2.37531\,\text{mJ}$, min–max spread $1.93\%$), classified as `STABLE_OVER_TESTED_RANGE` across a $3.4\times$ mesh refinement.

5. **Governance & Epistemological Boundaries**:
   - Maintained `GLOBAL_ENERGY_IDENTITY — NOT_YET_CLOSED`.
   - Maintained Gate 6C state transfer energy preservation as `NOT_YET_PERFORMED / GATE_6C_PENDING`.
   - $\Delta_{\text{book}}$ designated strictly as `TWO_TERM_BOOKKEEPING_DIFFERENCE`.
   - Zero new HPC simulations or PBS jobs submitted.

---

## 2. Updated Artifacts & Hashes

| Artifact Identifier | Path | Description | SHA-256 Hash |
| :--- | :--- | :--- | :--- |
| `SUPERVISOR_REQUEST_COMPLIANCE_CHECKLIST` | `docs/supervisor_reports/01-10-2026/MA_ModeI_Supervisor_Meeting_Pack_2026-10-01/SUPERVISOR_REQUEST_COMPLIANCE_CHECKLIST.md` | Comprehensive supervisor compliance checklist with exact line mappings, source-accurate unit semantics, and verified tables | `2946E4CD7B3936E8FD577314C6521B48E435A2A3CEAA71C416770BB0E916C33D` |
| `F1085_SESSION_REPORT` | `project_coordination/sessions/2026-09-28_1225_gemini-antigravity_F1085_supervisor_pack_final_source_and_numerical_audit.md` | Session report for F1085 | *(Recorded below)* |
