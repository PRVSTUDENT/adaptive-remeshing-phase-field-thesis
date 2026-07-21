# Mesh Use Policy — Molnar lc = 0.015 mm Family

Status: `frozen_after_supervisor_decision_1A_2B`  
Recorded: 2026-07-21  
Authority: `docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_DECISION_1A_2B.md`

## Operating policy

| Role | Mesh | \(h\) [mm] | Physical elements (frozen study) |
|---|---|---:|---:|
| Fast testing and debugging | **H0** | ≈ 0.00494 | 3930 |
| Final simulations for thesis/report | **H1** | 0.0025 | 12064 |
| Fine convergence evidence only | **H2-PUB** | 0.001 | 33852 |

## Stage-specific use

| Stage / activity | Mesh | Notes |
|---|---|---|
| Preprocessing automation development | H0 (primary), H1 (parity check) | Gate P1 determinism on H0 |
| MISESERI first implementation | H0 coarse → remesh toward H1 local size | Comparison reference: existing uniform H1 |
| Thesis/report final RF–U production runs | H1 | Default production mesh |
| Fine RF–U validation reference | H2-PUB | Not default production |
| Crack-path reproducibility study | deferred | Tools may be prepared now; execution later |
| Multicore qualification | separate H1 campaign after serial workflow stable | Not mixed with first MISESERI implementation |

## Explicit non-uses

- Do **not** treat H0 as an RF–U validation or thesis production reference.
- Do **not** treat H2-PUB as the default production mesh for every report figure.
- Do **not** use crack-path appearance alone as the Stage C acceptance gate.
- Do **not** retune remeshing `errorTarget` after viewing the final crack result; define, record, then assess.

## Scientific comparison for Stage C

Primary:

```text
Uniform H1 reference
versus
MISESERI-refined model targeting H1 local resolution
```

Secondary (optional fine check):

```text
H2-PUB available as fine RF–U reference
```

Primary metrics:

- relative peak-force error \(e_{\mathrm{peak}}\)
- force–displacement curve NRMSE \(e_{\mathrm{curve}}\)
- element counts, walltime, CPU time, memory
- refinement distribution and min/median \(h/l_c\)
