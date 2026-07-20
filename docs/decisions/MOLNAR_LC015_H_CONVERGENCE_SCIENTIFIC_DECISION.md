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
| Conservative uniform RF–U reference | **H2-PUB**, h = 0.001 mm | Publication local resolution; finest tested mesh |
| Intermediate development studies | **H1**, h = 0.0025 mm | Nearly identical peak/pre-peak at much lower cost (~35% of H2 walltime) |
| Final reference | **H0 not recommended** | Clear H0→H1 mesh dependence |

## Gate A3 status (precise)

Overall gate remains **open**. The historical label `reference_data_insufficient`
remains defensible for full Gate A3 closure.

Internal descriptive status for the RF–U component:

```text
rf_u_reference_supported_contour_evidence_pending
```

Component breakdown:

```text
Gate A3:
  RF–U benchmark component: complete
  RF–U reference mesh: selected provisionally (H2-PUB)
  Publication comparison: completed provisionally (lc=0.015 approx. digitization)
  Supervisor-approved tolerances: pending
  Matched-state crack-path/SDV15 evidence: pending
  Overall benchmark gate: not yet closed
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
H2-PUB reference recommendation: supported
H1 intermediate recommendation: supported
Contour convergence: pending
Gate A3: open
Further PBS/Abaqus/CAE runs: not authorized
MISESERI/remeshing/state transfer: blocked pending supervisor decision
```

Do **not** start MISESERI or adaptive remeshing solely on the RF–U result unless
the supervisor explicitly accepts or waives missing contour evidence.
