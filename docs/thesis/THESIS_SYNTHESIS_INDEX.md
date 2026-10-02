# Thesis Synthesis Master Index & Evidence Manifest

## Stage-G Production Adaptive Validation Campaign

- **Status**: `SIMULATION_CAMPAIGN_CLOSED`
- **Governed Milestone**: `VALIDATED_PRODUCTION_ADAPTIVE_ACCURACY_AND_EFFICIENCY_VALIDATED`
- **Date**: 2026-08-21
- **Agent**: `gemini-antigravity`

---

## 1. Primary HPC Evidence & Frozen Provenance

| Package / Job Name | Planning Role | Original Failed Job | Replacement Job ID | Exit Status | Total CPU (s) | Final $U_1$ (mm) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `M2ADAPT_MM_FRACFIX_PROD` | Recommended Primary Efficiency Candidate | `1394254.mmaster02` | **`1394260.mmaster02`** | 0 | 1,180.0 | 0.010000 |
| `M2ADAPT_PK5_FRACFIX_PROD`| Recommended Corridor Sensitivity Reference | `1394255.mmaster02` | **`1394261.mmaster02`** | 0 | 2,600.0 | 0.010000 |

- **Original Failed Jobs**: `1394254.mmaster02` and `1394255.mmaster02` are preserved as terminal pre-solver failure evidence (`ErrElemAreaSmallNegZero`).
- **Bit-for-Bit Provenance**:
  - `M2ADAPT_MM_FRACFIX_PROD.inp`: `5b8cb39b08d594953d884212167b8a9578349cc397352e52f253dedd819d326d`
  - `M2ADAPT_PK5_FRACFIX_PROD.inp`: `402f6b61f59a31bd1ebee77019e47a3a7da0557296660c20ddc8aaab30b847f4`
  - `f42_mixed_uel.for`: `0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8`

---

## 2. Machine-Readable Tables (in `docs/thesis/tables/`)

1. **`validation_ladder_a_to_g.csv`**: Comprehensive multi-stage validation ladder from Stage A (baseline) through Stage G (production adaptive).
2. **`stage_g_mesh_and_runtime_table.csv`**: Discretization statistics, exact element counts, CPU/walltimes, and scheduler diagnostic ratios for $H_1$, $H_2$, MM, and PK5.
3. **`stage_g_domain_a_accuracy_table.csv`**: Normalized $L_2$ errors, relative work errors, and stiffness errors evaluated against $H_1$ reference, $H_2$ baseline, and mutual comparisons.
4. **`stage_g_hard_invariants_table.csv`**: Field bounds ($0 \le d \le 0.984$), irreversibility (0 violations), history non-negativity, and history temporal monotonicity across all 72 saved ODB frames.
5. **`stage_g_damage_initiation_table.csv`**: Saved-frame damage initiation observations ($d \ge 0.5$) and continuous crossing brackets ($\Delta U_1 = 0.25\,\mu\text{m}$).
6. **`stage_g_provenance_and_job_mapping.csv`**: Replacement mappings, failure classifications, and frozen artifact SHA-256 hashes.
7. **`stage_g_summary_metrics.json`**: Master JSON dataset for automated script ingestion.

---

## 3. Publication-Ready Figures (in `docs/thesis/figures/`)

1. **`fig_stage_g_rf1_u1_curves.pdf` / `.png`**: Mode-II reaction force vs. displacement comparison showing $H_1$ reference, $H_2$ baseline, Candidate 1 (MM), and Candidate 2 (PK5). Inset annotations mark $H_2$ walltime censoring at $U_1 = 0.00925\,\text{mm}$, $H_1$ termination at $U_1 = 0.00963\,\text{mm}$, and discrete saved-frame damage initiation observations.
2. **`fig_stage_g_efficiency_speedup.pdf` / `.png`**: Dual-axis bar chart comparing physical element counts (log scale) against scheduler CPU execution time and diagnostic speedup ratios.
3. **`fig_stage_g_domain_a_error.pdf` / `.png`**: Pointwise relative force discrepancy vs. $H_1$ reference over Domain A ($0 \le U_1 \le 0.00925\,\text{mm}$), highlighting adherence to the $\pm 2.0\%$ provisional envelope.

---

## 4. Manuscript Integration (in `docs/thesis/`)

- **`STAGE_G_PRODUCTION_ADAPTIVE_VALIDATION_CHAPTER.tex`**: Complete LaTeX chapter section drafted with conservative scientific phrasing, full table/figure cross-references, and explicit three-layer validation boundaries.
- **`FINAL_CLAIM_MATRIX.md`**: Updated to reflect complete validation across all 7 stages.

---

## 5. Decision & Closure

- **Governed Status**: `VALIDATED_PRODUCTION_ADAPTIVE_ACCURACY_AND_EFFICIENCY_VALIDATED`
- **Further HPC Simulations**: `false` (None scientifically required).
- **Active Task**: Thesis manuscript assembly, faculty build verification, and final submission packaging.
