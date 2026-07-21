# Analytical Benchmark Assessment (Task V2)

Status: `assessment_scaffold`  
Does not block Stage C preparation.

## Principle

Use analytical (or semi-analytical) checks only where closed-form or asymptotic solutions are defensible.  
A full analytical solution for nonlinear post-peak crack evolution of the Molnár single-notch PFF model is **not** an appropriate target.

## Quantity assessment

| Quantity | Defensible? | Approach | Status | Notes |
|---|---|---|---|---|
| Initial elastic stiffness (global RF–U slope) | **yes** | Compare early-slope of RF–U to elastic plate under far-field tension with notch compliance estimate; also one-element stiffness from WP1 | partial evidence exists (H0/H1/H2 K0 ≈ 134.2–134.7 kN/mm) | Use for order-of-magnitude / mesh-to-mesh consistency, not exact handbook match without a verified analytical model |
| Homogeneous one-element phase-field response | **yes** | Source-defined relations already used in WP1 | provisional pass under working tolerances | Keep as formulation smoke check |
| Uncracked elastic stress field near notch (pre-peak, low load) | **partial** | LEFM mode-I notch/crack asymptotic field for comparison of stress concentration pattern (not absolute PFF peak load) | not yet executed | Contours deferred (Decision 2B); elastic pre-analysis MISESERI job can support qualitative stress pattern checks |
| Energy release rate before propagation | **partial** | LEFM \(G\) estimates for edge crack of length \(a\) in a strip under tension | not yet executed | Requires consistent plane-stress/strain assumption and crack-length definition; PFF length-scale regularisation means exact LEFM criticality is approximate |
| Critical-load estimate | **partial** | Order-of-magnitude from \(G_c\), geometry factor, and ligament | not yet executed | Useful sanity bound only; do not gate Stage C on analytical peak-load match |
| Full nonlinear post-peak RF–U evolution | **no** | — | out of scope | No defensible closed form for staggered PFF post-peak on this geometry |
| Crack path angle (Mode I symmetry) | **qualitative** | Expect straight horizontal ligament path by symmetry | deferred tools | Reproducibility study later; not Stage C acceptance gate |

## Recommended analytical package (when executed)

1. Report H0/H1/H2 initial tangent \(K_0\) from frozen RF–U CSVs (already tabulated).  
2. One-element degraded-stress and history checks (existing WP1).  
3. Optional LEFM strip estimate of initiation load band with explicit assumptions listed.  
4. Never present LEFM peak-load estimate as a Gate A3 pass criterion.

## Explicit non-claims

- No analytical validation of post-peak mesh dependence.  
- No claim that MISESERI is a mathematical phase-field error estimator.  
- No claim that geometry-similar literature RF–U curves are interchangeable without formulation match.
