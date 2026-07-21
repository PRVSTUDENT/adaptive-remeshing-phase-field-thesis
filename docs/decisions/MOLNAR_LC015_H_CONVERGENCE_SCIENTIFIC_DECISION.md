# Scientific Decision — Molnar lc = 0.015 mm RF–U h-Convergence

Status: `recorded_from_formal_analysis`

Analysis commit: `db4c1fadfb3a4f7b33b6b653c261e6da90036c48`  
Review: `runs/hpc/molnar_lc015_h_convergence/comparison/H_CONVERGENCE_SCIENTIFIC_REVIEW.md`

## Defensible conclusion

```text
Peak and pre-peak RF–U h-convergence: supported
Post-peak h-convergence: not fully demonstrated
Crack-path convergence: not assessed
Publication agreement: provisional
```

## Safest wording (use in thesis/report)

> The force–displacement response is effectively mesh-independent between H1
> and H2-PUB for the elastic, pre-peak and peak-load regimes. A noticeable
> post-peak mesh dependence remains and must be retained as a limitation.

Do **not** claim unrestricted full-curve mesh independence. Full-curve NRMSE
(~6.0%) is driven by post-peak residual (~20.2%).

## Key successive-mesh numbers (H1 → H2-PUB)

| Metric | Value |
|---|---:|
| Peak force change | 0.47% |
| Peak displacement change | 0% |
| Initial stiffness change | 0.06% |
| Pre-peak curve NRMSE | 0.11% |
| Full-curve NRMSE | 6.01% |
| Post-peak curve NRMSE | 20.2% |

H0 → H1 remains clearly mesh-dependent (peak force ~4.0%, peak displacement ~5.2%).

## Mesh selection

| Use | Selected mesh | Basis |
|---|---|---|
| Fine RF–U validation reference (Decision **1A**) | **H2-PUB**, h = 0.001 mm | Publication local resolution; finest tested mesh; not default production |
| Production / thesis / report mesh (Decision **1A**) | **H1**, h = 0.0025 mm | Nearly identical peak/pre-peak at much lower cost (~35% of H2 walltime) |
| Development / testing / debug (Decision **1A**) | **H0**, h ≈ 0.00494 mm | Fast testing only; clear H0→H1 mesh dependence; not an RF–U reference |

Supervisor recording document:
`docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_DECISION_1A_2B.md`

## Gate A3 status (precise)

RF–U validation use is **conditionally accepted** after supervisor Decisions **1A**
and **2B**. Full unconditional Gate A3 closure for every Stage A narrative is
still not claimed; the historical label `reference_data_insufficient` may remain
for other incomplete items (e.g. absolute paper-curve tolerances).

Internal descriptive status for the RF–U component:

```text
gate_a3_conditionally_accepted_rf_u
rf_u_reference_accepted_contour_deferred
contour_validation_deferred
stage_c_miseseri_preparation_authorized
```

Component breakdown:

```text
Gate A3:
  RF–U benchmark component: complete
  RF–U reference mesh: H2-PUB (supervisor Decision 1A)
  Production/report mesh: H1 (supervisor Decision 1A)
  Development/testing mesh: H0 (supervisor Decision 1A)
  Publication comparison: completed provisionally (lc=0.015 approx. digitization)
  Matched-state crack-path/SDV15 evidence: deferred (Decision 2B; does not block Stage C prep)
  Stage C MISESERI preparation: authorized
  Stage C HPC submission: not authorized without explicit new approval
  Overall unconditional Stage A closure: not claimed
```

## Supervisor summary (ready to send)

> The controlled mesh-convergence study at \(l_c=0.015\) mm has been completed
> using the exact supplementary mesh, an intermediate mesh, and the
> publication-scale local resolution \(h=0.001\) mm. The H1 and H2-PUB solutions
> differ by only 0.47% in peak force, 0% in peak displacement, and 0.11% in the
> pre-peak force–displacement curve. This supports convergence of the pre-peak
> and peak response. The full-curve difference is approximately 6%, mainly due
> to a 20% post-peak residual, so post-peak mesh independence is not yet claimed.
> H2-PUB is recommended as the conservative uniform reference, while H1 is
> suitable for intermediate development studies. Crack-path convergence remains
> unassessed because matched-state contour exports are incomplete.

## Project boundary

```text
RF–U h-convergence analysis: complete
H2-PUB fine validation reference: accepted (Decision 1A)
H1 production/report mesh: accepted (Decision 1A)
H0 development/testing mesh: accepted (Decision 1A)
Contour convergence: deferred (Decision 2B)
Gate A3 RF–U use: conditionally accepted
Stage C MISESERI preparation: authorized
Further PBS/Abaqus/CAE submission: not authorized without explicit new approval
MISESERI execution: preparation only until qsub authorization
```

Do **not** submit PBS/Abaqus/CAE MISESERI jobs until explicit submission
authorization. Preparation of preprocessing automation and campaign plans is
authorized.
