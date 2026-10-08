# Mode-II Reproduction: Current State & Active Gate Dashboard

Protocol version: 2  
Active Task: `F1320-MODE2-M2-4-MIEHE-INDEXING-REPAIR-AND-REPRODUCTION-SOLVE`  
Last Updated: `2026-10-08T01:50:00+02:00` (gemini-antigravity)  
Governing Phase: `MODE2_REPRODUCTION_ACTIVE_HUMAN_AUTHORIZED_PREMEETING`

---

## 1. Master Mode-II Gate Dashboard

| Gate ID | Description | Status | Key Evidence / Artifact |
| :--- | :--- | :---: | :--- |
| **Gate M2-0** | Source & Scope Freeze | `CLOSED_PASSED` | `MODE2_REPRODUCTION_BASELINE_MANIFEST.json` |
| **Gate M2-1** | Constitutive Split Qualification | `QUALIFIED_DATACHECK_PASSED` | `f42_mixed_uel_mode2_miehe.for` (SHA-256 `A5992452...`, Datacheck Exit 0) |
| **Gate M2-2** | Canonical Coarse Pre-Analysis | `COMPLETED_EVALUATED_PASSED` | Job `1410790.mmaster02` (4,000 incs, Exit 0, 8/8 checks PASS) |
| **Gate M2-3** | Native Adaptive Remeshing & Audit | `CLOSED_PASSED` | Clean-chain OFAT sweep completed; non-targeted audit passed ($r=-0.8202$, $98.65\%$ top-10% focus); `ET_2PCT` ($22{,}530$ FEs) classified as `INFERRED / PROJECT_SELECTED_FOR_M2_4` |
| **Gate M2-4** | Adapted Refined PFM Solve | `REPAIRED_SOLVER_SUBMITTED_AND_QUEUED` | PBS Job ID `1410807.mmaster02` (`M2_J2_ADAPTED_FRACTURE`, 1 CPU serial, 16 GB RAM, 24h walltime, queued in `normal_imfdfkmq` on `mmaster02`); physical element indexing offset repaired via dynamic `N_PHYS` |
| **Gate M2-5** | Benchmark & Accuracy Evaluation | `ON_HOLD_PENDING_M2_4_EVALUATION` | Gated on Job-2 completion |

---

## 2. Active Cluster Job Details

- **PBS Job ID:** `1410807.mmaster02`
- **Job Name:** `M2_J2_ADAPTED_FRACTURE`
- **Input Deck:** `Job-2_UEL.inp` (SHA-256 `b6de1d3b...`, 22,530 physical FEs, 67,590 layered elements, 22,642 nodes)
- **Subroutine:** `f42_mixed_uel_mode2_miehe.for` (SHA-256 `A5992452...`)
- **Queue / Nodes:** `normal_imfdfkmq` / `mmaster02` (1 CPU serial, 16 GB RAM)
- **Working Directory:** `/scratch9/pr21vyci/runs/mode2_j2_adapted_fracture/`
- **Status:** `QUEUED`
- **Audited Criteria Provenance:** [`references/derived/pandey_kumar_2025_fig13a_digitization_provenance.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/references/derived/pandey_kumar_2025_fig13a_digitization_provenance.md)
