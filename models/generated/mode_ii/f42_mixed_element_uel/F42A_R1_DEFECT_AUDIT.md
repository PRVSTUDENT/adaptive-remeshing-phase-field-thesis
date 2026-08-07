# F42A-R1 Mixed-Element UEL Defect Audit Report

Date: 2026-08-07  
Agent: Gemini Antigravity  
Status: `complete`  
Classification: `f42a_r1_defects_audited_and_documented`  

---

## 1. Executive Summary

An audit of the initial F42A prototype (`5efa78e6ece595141da5437db6cb5005cb8470ea`) revealed four critical implementation defects that prevented execution in Abaqus/CAE and solver runtime. These defects did not fail the preliminary offline mathematical unit tests because those tests exercised shape function calculus rather than Abaqus Fortran `JTYPE` dispatch, complete displacement branches, and multi-layer element label uniqueness rules.

All four defects have been documented below and will be systematically corrected in **Task F42A-R1**.

---

## 2. Identified Implementation Defects

### Defect A: Invalid `JTYPE` Dispatch Mapping
- **Observed Behavior**: Input deck declared `type=U11, type=U12, type=U21, type=U22`, while `f42_mixed_uel.for` checked `IF (JTYPE.EQ.1)`, `IF (JTYPE.EQ.2)`, `IF (JTYPE.EQ.3)`, `IF (JTYPE.EQ.4)`.
- **Abaqus Mechanism**: Abaqus passes the integer portion of `type=Un` into `JTYPE`. Thus, `U11` $\rightarrow$ `JTYPE=11`, `U12` $\rightarrow$ `JTYPE=12`, `U21` $\rightarrow$ `JTYPE=21`, `U22` $\rightarrow$ `JTYPE=22`.
- **Impact**: The solver would never enter any UEL branch in `f42_mixed_uel.for`.

### Defect B: Missing Quad & Triangle Displacement Branches
- **Observed Behavior**: `f42_mixed_uel.for` implemented only phase-field UEL branches (`JTYPE=1` and `JTYPE=3`), leaving displacement branches (`JTYPE=2` and `JTYPE=4`) unimplemented or stubbed.
- **Impact**: Unable to solve mechanical displacement fields or compute elastic strain history $H$.

### Defect C: Uninitialized Variable `GC` & Phase Equation Divergence
- **Observed Behavior**: Triangle phase subroutine contained an uninitialized variable `GC` (instead of `GCPAR = PROPS(2)`), causing garbage values or floating-point exceptions. The reaction term also diverged from Molnár's validated $(G_c/l + 2H)$ formulation.
- **Impact**: Unstable or incorrect phase-field residual and stiffness calculations.

### Defect D: Deck Rebuilder Layering & Element Label Collisions
- **Observed Behavior**:
  1. `f42_deck_rebuilder.py` declared `U12` and `U22` displacement UEL cards but omitted `*Element, type=U12` and `*Element, type=U22` element blocks.
  2. Reused physical element IDs ($1..N_{phys}$) across phase, displacement, and facsimile layers without label offsets. Abaqus requires element labels to be unique across the entire part.
  3. Constructed `All_elem` and `umatelem` sets from phase element sets (`Phase_Quad`, `Phase_Tri`) instead of the facsimile (`CPE4`/`CPE3`) layer.
- **Impact**: Abaqus input processor error due to duplicate element labels and invalid `MISESERI` facsimile set association.

---

## 3. Machine-Readable Defect Audit Summary (`F42A_R1_DEFECT_AUDIT.json`)

```json
{
  "protocol_version": 1,
  "audit_type": "f42a_r1_defect_audit",
  "starting_commit": "5efa78e6ece595141da5437db6cb5005cb8470ea",
  "defects": {
    "defect_a_invalid_jtype_dispatch": {
      "deck_types": ["U11", "U12", "U21", "U22"],
      "fortran_jtype_checked": [1, 2, 3, 4],
      "actual_abaqus_jtype_passed": [11, 12, 21, 22],
      "status": "confirmed_invalid"
    },
    "defect_b_missing_displacement_branches": {
      "quad_displacement_executable": false,
      "triangle_displacement_executable": false,
      "status": "confirmed_missing"
    },
    "defect_c_uninitialized_gc_and_equation_divergence": {
      "uninitialized_variable": "GC",
      "molnar_formulation_divergence": true,
      "status": "confirmed_bug"
    },
    "defect_d_deck_rebuilder_layering_and_duplicate_labels": {
      "displacement_blocks_generated": false,
      "element_label_offsets_used": false,
      "duplicate_element_labels_present": true,
      "umatelem_set_uses_facsimile_layer": false,
      "status": "confirmed_bug"
    }
  }
}
```
