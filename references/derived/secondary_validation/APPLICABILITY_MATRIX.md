# Secondary Literature Applicability Matrix (Task V1)

Status: `in_progress_parallel`  
Priority: parallel lower-priority; does **not** block Stage C preparation  
Plan: `docs/studies/STAGE_C_SECONDARY_VALIDATION_AND_CRACK_PATH_PLAN.md`

## Screening rule

Do **not** use a reference merely because the geometry looks similar. Record differences in:

- formulation (staggered UEL vs monolithic, AT1/AT2, history variable)
- length scale \(l_c\)
- degradation law
- energy split
- loading and BC
- plane strain / plane stress / thickness
- mesh resolution \(h\) and \(h/l_c\)
- reported RF–U vs qualitative contours only

## Priority order

1. Same single-notch geometry and material  
2. Same \(l_c\) and degradation law  
3. Same staggered formulation  
4. Published force–displacement data  
5. Published crack path or contour data  

## Matrix

| reference | geometry | material | length scale | phase-field formulation | energy split | loading | mesh size | reported RF–U data | reported crack path | compatibility with current Molnár model | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Molnár & Gravouil (2017) | single-notch Mode I, 1×1 mm | E=210 GPa, ν=0.3, Gc=0.0027 kN/mm | 0.015 mm (study); paper also 0.0075 mm | staggered dual UEL (U1/U2) + CPS4 UMAT | as in source UEL | tension via RP | pub. local h≈0.001 mm | yes (Fig. 7) | yes (Fig. 6) | **high** — primary baseline | frozen H0/H1/H2 family |
| Pandey & Kumar (2025) | PFF benchmarks per paper | per paper | per paper | Abaqus adaptive remeshing + MISESERI class | per paper | per paper | MISESERI-driven | method-focused | method-focused | **method source** for Stage C pre-refinement | not a Molnár RF–U digitization target; extract remesh parameters carefully |
| Msekh et al. (2015) | various brittle fracture | various | various | monolithic Abaqus UEL/UMAT path | various | various | various | some cases | some cases | **formulation reference only** | different solution strategy; not default Stage C RF–U reference |
| Diddige, Roth, Kiefer (2025) | thesis-related adaptive/remesh context | TBD on full read | TBD | TBD | TBD | TBD | TBD | TBD | TBD | **to classify after detailed read** | do not claim compatibility without formulation table |
| Author-supplied Molnár supplement decks | one-element, single-notch, double-notch | as in `.inp` | as in `.for`/props | staggered UEL | as implemented | as in decks | as in decks | solver-reproducible | ODB-derived | **high technical** | H0 exact path; not always exact Fig. 7 mesh |

## Screening log (add rows; never delete rejected candidates)

| candidate | decision | reason |
|---|---|---|
| Generic “single edge notch” LEFM handbook solutions | limited | elastic singularity useful for uncracked/elastic checks only; not full PFF post-peak |
| Unrelated mixed-mode L-panel without RF–U | deferred | geometry mismatch; Stage C is Mode I single-notch first |

## Next extraction tasks

1. From Pandey–Kumar: document MISESERI rule parameters **only if explicitly stated**; otherwise keep project initial proposal (`docs/decisions/MISESERI_REMESHING_PARAMETER_PROPOSAL.md`).  
2. Digitize only curves with clear axis scales and same unit system.  
3. Mark plane-stress vs plane-strain mismatches as hard incompatibility for quantitative RF–U.
