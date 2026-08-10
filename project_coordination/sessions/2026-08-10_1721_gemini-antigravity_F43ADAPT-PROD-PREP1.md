# Session Log: F43ADAPT-PROD-PREP1 Preparation Closeout

- **Date**: 2026-08-10
- **Agent**: `gemini-antigravity`
- **Task ID**: `F43ADAPT-PROD-PREP1`
- **Status**: `preparation_complete_not_authorized`

---

## 1. Executive Summary & Objective

Prepared and validated the two-job Mode-II adaptive fracture production pair (`M2ADAPT_MM_FRACFIX_PROD` and `M2ADAPT_PK5_FRACFIX_PROD`) under the frozen censoring-corrected comparison contract. No solver execution (`qsub`) was performed. All governance rules and byte freeze contracts were strictly enforced.

---

## 2. Key Audit & Validation Findings

1. **Threshold Provenance Audit (1.5% Work-Error Gate)**:
   - Primary provenance search confirmed no earlier approved/frozen decision record defined 1.5% as a work/area gate.
   - Reverted to the established **2.0%** curve/area gate (`work_area_gate_value = 2.0%`, `work_area_gate_source = inherited_from_established_2pct_curve_difference_gate`).
   - Separately preserved: RF-U curve gate $\le 2.0\%$, energy gate $\le 1.0\%$, matched-state crack Hausdorff $\le 0.00375\,\text{mm}$.

2. **NPHYS Producer-Consumer Contract**:
   - `MM` ($N_{\text{phys}} = 2206$): 2,137 CPE4 quads + 69 CPE3 tris ($N_{\text{nodes}} = 2294$). Layered element count = 6,618. 5-property UEL card on U2/U4 with true $N_{\text{phys}}$ passed in 5th property slot. Pointwise $p \to p$ mapping PASS.
   - `PK5` ($N_{\text{phys}} = 4894$): 4,766 CPE4 quads + 128 CPE3 tris ($N_{\text{nodes}} = 4998$). Layered element count = 14,682. 5-property UEL card on U2/U4 with true $N_{\text{phys}}$ passed in 5th property slot. Pointwise $p \to p$ mapping PASS.
   - Added MM and PK5 production decks to `validate_nphys_producer_consumer_contract.py` (`Status: PASS`).

3. **Subroutine SHA256 Match**:
   - Both candidates use qualified subroutine `f42_mixed_uel.for` (`0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`).

4. **Output Sufficiency Audit**:
   - Field output `time interval=0.01`, node `U, RF`, RP `RF, U`, `UMATELEM SDV, S, EVOL`, global energy `ALLAE, ALLCD, ALLIE, ALLKE, ALLPD, ALLSE, ALLWK, ETOTAL`.
   - Fracture energy extraction definition: Whole-model work `ALLWK` minus elastic strain energy `ALLSE` from global history output, supplemented by spatial integration of element fracture energy density $G_c \left[ \frac{d^2}{2 l_0} + \frac{l_0}{2} |\nabla d|^2 \right]$ over element volume `EVOL` using `SDV14` ($d$) and `EVOL` field outputs.
   - `adaptive_energy_gate_ready = true`.

5. **Execution Raw-Byte SHA256 Hashes**:
   - **MM Candidate** (`M2ADAPT_MM_FRACFIX_PROD`):
     - Input (`M2ADAPT_MM_FRACFIX_PROD.inp`): `774c1385c111649b66dcc18e3990cef3b14c76acc64fc6809c586de3f1cfffb7`
     - Subroutine (`f42_mixed_uel.for`): `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
     - PBS Script (`M2ADAPT_MM_FRACFIX_PROD.pbs`): `6409ff55a3af0b9bfbc8520aacc5b8d492d7f78c5768e308954392f2548e8010`
     - Submit Wrapper (`submit_m2adapt_mm_fracfix_prod.sh`): `3f3711663a97e5a2fc1cf0054464bddeead8213ab130513bf4a30760bef6eb8d`
     - Manifest (`PACKAGE_MANIFEST.json`): `eb44f05282a3c06edc2f0456027ba0ca583ac6e5b451cb0bf7edc0a752e1435d`
   - **PK5 Candidate** (`M2ADAPT_PK5_FRACFIX_PROD`):
     - Input (`M2ADAPT_PK5_FRACFIX_PROD.inp`): `32e67a70cce767c6d2f914f1f121bbfac421a9807a21256a645bf2406a339356`
     - Subroutine (`f42_mixed_uel.for`): `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`
     - PBS Script (`M2ADAPT_PK5_FRACFIX_PROD.pbs`): `316140e61e90f45e506b4eec7d19f921886213da803306acbaadd4b03f8311cb`
     - Submit Wrapper (`submit_m2adapt_pk5_fracfix_prod.sh`): `76fdd18e9809f8a7ca8ef34297b7ad4ba5d0039784364ebe6fd7f237f65084db`
     - Manifest (`PACKAGE_MANIFEST.json`): `f03a73511fd7683a42a9177e82cb277ed26456de5ea80b41028ce0eba0608b70`

6. **P/Q Lineage & Qualification**:
   - P Tag: `P43ADAPT1-FINAL1` on candidate commit `99e40bf4ed5e64687cdd41c13ceba7c545a4f237` (Tag object SHA: `c70088af88a950295895774dc6a4335e377effa6`). Created once, pushed once, force pushed = false.
   - Pre-anchor / Exact-P full unit test suite: **619 passed, 0 failures, 0 errors (100% OK)**.
   - Q Tag: `Q43ADAPT1-FINAL1` on provenance-only commit descending from P. Execution bytes 100% unchanged ($P \to Q$ byte identity PASS).

---

## 3. Authority State & Governance Boundary

- `authorization_ready_for_adaptive_production`: `true`
- `execution_authorized`: `false`
- `submission_approved`: `false`
- `maximum_jobs_now`: `0`
- `qsub_called`: `false`
- `HPC_submissions`: `0`
