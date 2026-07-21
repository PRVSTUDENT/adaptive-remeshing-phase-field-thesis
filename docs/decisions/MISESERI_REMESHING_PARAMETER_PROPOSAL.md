# MISESERI Remeshing Parameter Proposal (Initial Freeze)

Status: `initial_proposal_frozen_no_execution`  
Recorded: 2026-07-21  
Authority: Stage C preparation after Decisions 1A + 2B  
Claim boundary: **pre-refinement only** (not online evolving adaptivity)

```text
Do not retune errorTarget after viewing the final crack result.
Define -> record -> assess consequences.
No remeshing CAE/PBS job is authorized by this document alone.
```

## Campaign context

| Item | Value |
|---|---|
| Coarse source mesh | **H0** (development/testing) |
| Target refined local size | approximately **H1**, \(h = 0.0025\) mm |
| Comparison reference | existing uniform **H1** RF–U result |
| Remeshing passes | **1** |
| Coarsening | **disabled** |
| Solver mode (first campaign) | serial |
| Pre-analysis load level | **undecided** — pending supervisor clarification (elastic vs partial fracture) |

---

## Parameter table

### 1. `errorTarget`

| Field | Content |
|---|---|
| **Abaqus definition** | Target value for the stress-discretization error indicator used by adaptive remeshing (MISESERI-based sizing). Elements with indicator above the target are candidates for refinement according to the remeshing rule. |
| **Value proposed** | `0.05` (5%) — **initial proposal only** |
| **Reason** | Common order-of-magnitude starting point for relative von Mises recovery-error indicators in engineering remeshing studies; intended to mark a minority of high-error elements near the notch/ligament without immediately refining the entire plate. Not taken from a Pandey–Kumar table without confirmation; must be confirmed or replaced before Job 3. |
| **Expected mesh effect** | Concentrated refinement near the notch-tip / high-stress ligament corridor; limited far-field refinement if MISESERI is physically reasonable. |
| **Falsification check** | If >50% of elements refine, or refinement is dominated by irrelevant boundary artifacts, the target is too strict (or pre-analysis field is wrong). If almost no elements refine and corridor \(h\) remains near H0, the target is too loose. |

### 2. `refinementFactor`

| Field | Content |
|---|---|
| **Abaqus definition** | Factor controlling how aggressively element size is reduced relative to the current size when the error indicator exceeds the target (implementation-specific sizing law in the Abaqus adaptive remeshing rule). |
| **Value proposed** | `2.0` — **initial proposal only** |
| **Reason** | One-pass refinement aiming to move local size from H0 corridor (~0.005 mm) toward H1 (0.0025 mm) is roughly a factor-of-two size reduction; matches the intended H0→H1 local resolution step without multi-pass cascading. |
| **Expected mesh effect** | Local size approximately halved in marked regions after one pass. |
| **Falsification check** | If refined corridor median \(h\) remains ≫ 0.0025 mm, increase aggressiveness or add a second pass (only with new authorization). If overshoot to \(h \ll 0.0025\) mm or element explosion, reduce factor. |

### 3. `minElementSize`

| Field | Content |
|---|---|
| **Abaqus definition** | Hard lower bound on element size after remeshing. |
| **Value proposed** | `0.0025` mm |
| **Reason** | Supervisor production mesh local resolution (H1). Prevents overshoot below the Stage C comparison target in a one-pass H0→H1 pre-refinement. |
| **Expected mesh effect** | Floors refined elements at H1 resolution. |
| **Falsification check** | If many elements sit exactly at the floor while MISESERI remains high, the floor is active and acceptable for this campaign; do not lower to H2 without a separate study. |

### 4. `maxElementSize`

| Field | Content |
|---|---|
| **Abaqus definition** | Hard upper bound on element size after remeshing. |
| **Value proposed** | `0.025` mm |
| **Reason** | Tied to the H0/H1 study far-field / global element size used in the graded family (`global_element_size_mm: 0.025`). Coarsening is disabled, so this mainly prevents unintended growth and documents the far-field scale. |
| **Expected mesh effect** | Far-field elements remain at or below the existing global size. |
| **Falsification check** | If remeshing increases far-field size above the H0 far-field scale, the rule is misconfigured. |

### 5. Remeshing passes

| Field | Content |
|---|---|
| **Abaqus definition** | Number of adaptive remeshing iterations applied. |
| **Value proposed** | `1` |
| **Reason** | First implementation simplicity; one controlled change relative to uniform H0. |
| **Expected mesh effect** | Single sizing update from the pre-analysis MISESERI field. |
| **Falsification check** | If one pass cannot approach H1 local size under the frozen min size, document failure; do not silently add passes. |

### 6. Coarsening

| Field | Content |
|---|---|
| **Abaqus definition** | Whether elements may enlarge when the error indicator is low. |
| **Value proposed** | `disabled` (`false`) |
| **Reason** | Pre-refinement study should not remove resolution from the coarse model in low-error regions in a way that confounds cost/accuracy comparison. |
| **Expected mesh effect** | Only refinement (or hold) occurs. |
| **Falsification check** | Any element enlargement in the exported refined mesh is a configuration failure. |

### 7. Pre-analysis load level

| Field | Content |
|---|---|
| **Abaqus definition** | Load / step state at which MISESERI is evaluated for sizing. |
| **Value proposed** | **undecided** — `elastic` *or* `partial_fracture` pending supervisor clarification |
| **Reason** | Elastic pre-analysis is cleaner and cheaper; partial fracture may mark a more crack-relevant error field. This choice changes scientific interpretation and must be explicit. |
| **Expected mesh effect** | Elastic: refinement driven by elastic concentration at the notch. Partial fracture: may track the process zone more closely but risks circularity with the final crack path. |
| **Falsification check** | Boundary-dominated MISESERI or refinement far from the ligament invalidates the load-level choice for Stage C. |

---

## JSON freeze snapshot

```json
{
  "remeshing_id": "miseseri_pre_refinement_h0_to_h1_initial",
  "method": "miseseri_pre_refinement",
  "coarse_source_mesh": "H0",
  "target_refined_local_h_mm": 0.0025,
  "comparison_reference": "uniform_H1",
  "passes": 1,
  "coarsening": false,
  "preanalysis_load_mode": "undecided_pending_supervisor",
  "rule": {
    "errorTarget": 0.05,
    "refinementFactor": 2.0,
    "minElementSize_mm": 0.0025,
    "maxElementSize_mm": 0.025
  },
  "status": "initial_proposal_frozen_no_execution",
  "retune_after_final_crack": false
}
```

Canonical machine-readable copy: `configs/remeshing/miseseri_h0_to_h1_initial.json`

## Explicit non-claims

- These values are **not** supervisor-approved until confirmed in the short meeting.
- These values are **not** validated by a completed remesh job.
- Pandey–Kumar paper values, if extracted later, may replace this proposal only with a new recorded decision.
