# F1641: single offline local-sizing hypothesis

**Current verdict: reject this particular support rule before generating a mesh.** It covers every tested tip-zone centroid, but leaves mapped ligament and hole-band centroids outside its 1.5µm cap. No new mesh, solver run, datacheck or PBS submission occurred.

## Hypothesis and parameter provenance

For each authentic coarse cell K, define normalized statistical weight

`w_K = A_K * e_K^2 / sum_J(A_J * e_J^2)`, where `e_K=MISESERI_K`.

Sort contributions descending; select the smallest prefix reaching the predeclared bulk mass0.90, including every exact cutoff tie. Set S to the union of those original cell polygons. Propose

`h_resolution(x)=min(0.020,0.0015+0.25*distance(x,S)) mm`,

`h_target(x)=min(h_native_MISESERI(x),h_resolution(x))`.

The cap is a maximum characteristic size, not the Abaqus minElementSize parameter. The0.25 slope gives a0.074mm transition from the cap to the existing far-field maximum. Both0.90 and0.25 were declared before the calculation and were not fitted to diagnostic coverage.0.90 retains90%of this squared stress-error proxy with a small selected set; it is a testable design choice,not a qualified tolerance. Raw MISESERI is not percent error. Its area-weighted square is a proxy,not a certified phase-field estimator or energy balance.

Bulk marking has a mathematical literature, but its convergence claims for other PDEs do not qualify this application. For example,[Diening and Storn](https://arxiv.org/html/2610.39719v1) analyze conforming FEM for Poisson,not this elastic-preanalysis/phase-field/UEL workflow. We borrow the deterministic marking pattern only.

## Authentic source and measured support

The unchanged source ODB hash is `0A108C6A8404F1AF9D8F5DDC03223E9D8D051AB08587F841D9F5799970AE93B1`; the source-verified2,906-cell extraction supplies original polygons,centroids and unambiguous MISESERI. All cell weights,selection flags,distances and cap values are preserved in `f1641_local_size_support.json`. Diagnostic regions are evaluated AFTER marking; no region,corridor or crack trajectory is an input to selection.

Selected180/2,906cells account for0.0625112144mm²,6.4591%of the coarse polygon area,and90.0253%of proxy mass. Coarse polygon area0.9677987440mm² differs from exact CAD area because the coarse hole boundary is faceted; these are coarse-mesh area calculations,not exact-CAD integrals.

For coverage,we test actual rejected-candidate centroids against containing authentic source polygons with point-in-polygon checks. No nearest-neighbor substitution is allowed across hole chords or the slit. All9,712diagnostic centroids mapped successfully (24nearest centers were used only to shortlist polygons;containment was then required).

| Diagnostic check | Tested centroids | Within selected support | Selected area fraction |
|---|---:|---:|---:|
| Tip zone | 663 | 663(100%) | 100% |
| Ligament | 6,250 | 5,581(89.296%) | 89.211% |
| Hole band | 2,799 | 2,482(88.675%) | 88.063% |

There are669mapped ligament and317mapped hole-band counterexamples;original candidate/source labels and coordinates are retained. Centroid coverage alone could not prove full polygon coverage even if all passed. The uncovered mapped points are sufficient to fail the declared conservative diagnostic coverage check. This does not prove every uncovered point lies in the eventual physical FPZ,nor that no different indicator criterion could work. It rejects this ONE support rule and prevents an unsupported full-resolution claim. Do not silently tune theta or append a geometric corridor.

## Refinement burden and backend boundary

Selected area divided by(0.0015mm)² is27,782.8square-cell equivalents. Source-centroid quadrature of the graded cap gives33,051.7square-cell equivalents. These are approximate area/size proxies,not bounds,actual generated counts,triangular-mesh counts,solver costs or runtime predictions. Taking the minimum with the native sizing field can further increase the count. No8h rejection is applied;the verified longer queues remain available to a future exact qualified execution scope.

The exact native2023 path exercised previously is `Model.RemeshingRule(...region=faces,maxElementSize=...)` then `Model.adaptiveRemesh(odb=...)`. It accepts size constraints on geometric regions;the existing script has no arbitrary spatial-field parameter. An indicator-selected cap would need a demonstrated mapping to geometric subregions and interior constraints,not merely `seedEdgeBySize` on the outer boundary. We have NOT verified that this can enforce a strict longest-edge maximum with smooth grading. [Current official Abaqus documentation](https://docs.software.vt.edu/abaqusv2026/English/SIMACAEANLRefMap/simaanl-c-adpover.htm) describes region rules and requires geometry-backed parts;it is2026documentation and does not independently establish a2023API capability. Direct2023web references were inaccessible.

No backend was installed or new meshing infrastructure built because the support prerequisite already fails. If a revised support hypothesis is independently accepted,first verify a native region-partition/local-seeding implementation against the actual2023API. Only if that lacks the required interior maximum-size control should an explicit background-field backend be considered. That is a conditional implementation gate,not a claim that native implementation is impossible.

## Falsification, acceptance and review request

Predeclared falsification:required diagnostic regions have mapped points outside the cap support,or coverage is unproven. This condition is met. **Do not generate this candidate.**

A later corrected candidate would still require full declared h/l0≤0.2coverage in scientifically justified fracture-resolution regions;positive triangle area and all quad Gauss-point Jacobians;no nonmanifold edges;unchanged notch/hole geometry and traction-free hole contract;quantified aspect/angles/gradation;and accepted quantitative quality limits before generation. Previous descriptors must not be turned into retrospective thresholds. No existing scalar angle/aspect/gradation acceptance limit was found in the scoped Method A reports,so that numerical acceptance specification remains a separate review predicate.

Request independent review of the exact rejection evidence and sizing-rule definition. The authenticated dispatcher must bind author=codex,operation,correlation,fingerprint and immutable evidence hashes. A planning reply cannot approve a new mesh or solver. Preserve this failed hypothesis unchanged;next action must be scientifically distinct,not a hidden theta sweep. Method C remains paused,F1641 open,zero-PBS scope intact.
