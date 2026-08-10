# Session Log: F43STATE-M2-OVERNIGHT-PREP1 Mode-II State-Transfer Restart Package Preparation

- **Date**: 2026-08-10
- **Agent**: `gemini-antigravity`
- **Task ID**: `F43STATE-M2-OVERNIGHT-PREP1`
- **Status**: `preparation_complete_not_authorized`

---

## 1. Executive Summary & Objective

Prepared a deterministic, qualified execution package for `M2STATE_FRACFIX_RESTART1`, the Mode-II evolving-remesh / state-transfer restart job using the completed `M2ADAPT_MM_FRACFIX_PROD` checkpoint ($u_1 = 0.005000\,\text{mm}$, Step-1 frame 500) transferred onto the nonmatching `PK5` remeshed grid ($N_{\text{phys}} = 4,894$, $14,682$ layered elements).

---

## 2. Rapid Scientific Extraction & Source Selection

1. **Candidate Comparison**:
   - **MM** ($N_{\text{phys}} = 2,206$, $164\,\text{s}$ CPU, peak $RF_1 = 0.17849\,\text{kN}$): $88.1\times$ CPU speedup vs fine $H_2$.
   - **PK5** ($N_{\text{phys}} = 4,894$, $366\,\text{s}$ CPU, peak $RF_1 = 0.17865\,\text{kN}$): $39.5\times$ CPU speedup vs fine $H_2$.
   - Max relative $RF_1$ difference across loading history: **0.158%** (Mean: **0.089%**), well within the 2.0% global-response gate.

2. **Source Selection Rationale**:
   - Following the preferred rule, **`MM` ($N_{\text{phys}} = 2,206$) was selected as the state-transfer source mesh** because it is lower cost ($164\,\text{s}$ vs $366\,\text{s}$) and agrees with PK5 within $0.16\%$ max difference without any material defect.

---

## 3. Transfer Checkpoint & Target Mesh

- **Source Checkpoint**: `M2ADAPT_MM_FRACFIX_PROD` at $u_1 = 0.005000\,\text{mm}$ (Step-1 frame 500, pre-peak damage initiation endpoint, $d_{\text{max}} = 0.1245$).
- **Target Mesh**: `PK5` nonmatching remeshed mesh ($4,894$ physical elements: $4,766$ quads + $128$ tris, $4,998$ nodes, $14,682$ layered elements).
- **Transfer Validation**:
  - Phase field $d$ L2 error: $0.048\%$ ($< 1.0\%$ gate)
  - History field $H$ L2 error: $0.052\%$ ($< 1.0\%$ gate)
  - Phase bound violations: $0$
  - Healing count: $0$
  - Energy jump immediately across transfer: **0.421%** ($< 1.0\%$ gate)

---

## 4. Execution Package & Raw SHA256 Hashes

- **Job Name**: `M2STATE_FRACFIX_RESTART1`
- **Location**: `models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1`
- **Resource Request**: `select=1:ncpus=1:mem=8gb`, `walltime=08:00:00`, `queue=entry_imfdfkmq`
- **Raw Hashes**:
  - **Input** (`M2STATE_FRACFIX_RESTART1.inp`): `211bcbc7aeade414818b1127656b054e16c1425d02321a474a8b63d5afdb181b`
  - **UEL** (`f42_mixed_uel.for`): `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
  - **Transfer Artifact** (`STATE_TRANSFER_ARTIFACT.json`): `71b62a941abfa702aa7a327789fcbc4ffe158ec3bdba1a1fcbb0c6e9515b238e`
  - **Transfer Manifest** (`TRANSFER_MANIFEST.json`): `b60ab220605da5a4583149a725a53a7bc79f812b3dccee8e6d2c79f08aa7dfb8`
  - **PBS Script** (`M2STATE_FRACFIX_RESTART1.pbs`): `e0177e8f80a70aaec263b6b5bd34624b48b7e6b53d9133c4fb26e65dd42b5209`
  - **Submit Wrapper** (`submit_m2state_fracfix_restart1.sh`): `a2ec9bea11499c60e6eb5b31c00ad5918e77a739054ec8be59c2f441732b709f`
  - **Package Manifest** (`PACKAGE_MANIFEST.json`): `3893604892e982abc8f188223430dc6d674752a77b8342e117e3949a0b258bc7`
  - **Acceptance Contract** (`RESTART_ACCEPTANCE_CONTRACT.json`): `5e8e3d6428784d0b1be125a25e6488d754ea8f20a442ef5efbdffad4fb425db0`

---

## 5. Immutable Anchor Lineage (P/Q)

- **Candidate Commit SHA**: `c4256bc1fc3d1dc1e9576a475a25fa3938b530a3`
- **Candidate P Tag**: `P43STATE1-FINAL1` (Tag object SHA: `b8b79e238d03383246b3f26ab59d09990b66498f`)
- **Pre-Anchor Rehearsal**: PASS (`7 passed in 0.10s`)
- **Exact-P Qualification**: PASS (`7 passed in 0.09s`)
