# F1641: physics-based resolution-domain assessment

**Verdict C — evidence insufficient to establish a selective required fracture-resolution domain.** This is neither full fracture-mesh acceptance nor a proof that every diagnostic-box centroid must have h/l0≤0.2. No new mesh, solver run, datacheck or PBS submission occurred.

## Actual frozen formulation

The unchanged frozen UEL SHA256 is `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`. Both mechanical element branches compute

`psi_driver = (lambda/2)*max(e11+e22,0)^2 + mu*(e11^2+e22^2+gamma12^2/2)`,

with plane-strain lambda=E*nu/((1+nu)*(1−2nu)) and mu=E/(2*(1+nu)), E=210kN/mm² and nu=0.3. The source locations are lines524–525 and795–796. This is the actual implemented trace split; it is not a spectral positive-principal-strain split. The full strain-norm term remains nonzero under negative in-plane trace. No constitutive formulation was changed or relabeled as independently corrected.

History is updated by `H_trial=max(H_trial,psi_driver)` at mechanical Gauss points. UEXTERNALDB restores committed values at increment start and commits trial values at accepted increment end (lines111–128). This preserves the intended history maximum across rollback. There is no explicit nodal `d>=d_old` inequality/clamp in the inspected phase branches. History monotonicity is not substituted for measured nodal damage irreversibility in a future run.

The phase residual and tangent give

`−Gc*l0*Laplacian(d)+(Gc/l0+2H)*d=2H`,

and the recorded fracture density is `Gc*(d²/(2*l0)+l0*|grad(d)|²/2)` (quad assembly lines341–359; triangle lines629–633 and660–670). For homogeneous d, `d=2H/(Gc/l0+2H)`. Thus every H>0 gives d>0:there is **no finite positive homogeneous damage-initiation threshold** in these equations. Introducing a critical tensile-energy threshold to label the FPZ would therefore require a distinct, justified hypothesis; it cannot be inferred from Gc/l0 alone. Spatial gradients and coupled mechanics remain essential; this algebra does not predict crack initiation, instability or the final crack path.

The documented near-fracture mesh criterion remains maximum consecutive-edge h/l0≤0.2,l0=0.0075mm. The algebraic nonzero-damage region is not automatically the region requiring that fine mesh. Its numerical adequacy still requires localization/gradient and convergence evidence.

An additional true technical bound is present:`N_CAPACITY=150000` and the checked PHYSIDX range (lines65 and244–249). The frozen implementation cannot execute more than150,000physical elements unchanged. This is a code-array bound,not an invented mesh-count or queue limit. Both existing meshes fit it; an arbitrarily fine whole-domain replacement may not.

## Authentic additional fields and constitutive distinction

The prior extraction had only displacement extrema and no per-node U or element S. This action extracted those specifically missing fields once from the SAME existing ODB,without rerunning analysis. Read-only extraction verified the source hash before/after:

`0A108C6A8404F1AF9D8F5DDC03223E9D8D051AB08587F841D9F5799970AE93B1`.

The actual source input hash is `D1D75D3807C3EF27A9BEF4717421DF3AB1491ECC931A17170F46591233031665`; its elastic constants are210000,0.3. Abaqus/Standard2023 final Step-1 frame1.0 has3,010nodes and2,906elements (2,832CPS4R,74CPS3). Recorded S components are S11,S22,S33,S12;S33 is exactlyzero. Duplicate stress samples were required to be identical.

The source is an intact linear **plane-stress** preanalysis,while the production UEL uses **plane-strain** stiffness. This does not invalidate its use as a provisional error-indicator preanalysis,but it prevents treating its U/S field as a converged production strain/history state. Strain was reconstructed from nodal U with the actual frozen UEL gradient/quadrature formula. At source element centers,it was independently checked against inversion of the recorded plane-stress elastic stress law using the actual source E,nu. Relative error median1.11e-6,p90=1.08e-5,max0.003446;finite-precision small-gradient cancellation contributes to the relative maximum. No missing strain output was fabricated.

The frozen-law energy was then evaluated on those intact displacement gradients at four quad Gauss points and one triangular point. Production E=210kN/mm² was used for energy evaluation;the stress inversion uses source E=210000 in native source units,so strains do not depend on a guessed conversion. These are **counterfactual frozen-law evaluations**,not converged production H,d,or crack fields.

## Measured driving-energy evidence

All2,906source cells have positive evaluated driving energy. Cellwise Gauss-point peak psi spans8.364e-8to0.808818kN/mm²;median0.000830592,p90=0.00369756. The homogeneous-diagnostic d spans4.647e-7to0.817964,median0.004593. The latter is not an observed damage solution;it shows why a pointwise zero/nonzero threshold is not a selective localization criterion.

Spearman correlation between original MISESERI and this cellwise psi peak is0.459685. The rejected90%bulk-MISESERI support leaves74.7996%of the integrated frozen-law energy proxy outside it;maximum psi outside is0.0107636kN/mm². Stress-error concentration and energy concentration are different quantities. This finding does not make either one a certified phase-field localization estimator.

## Existing mesh comparison

Each existing-mesh centroid was assigned only after containment in an authentic source polygon;24nearest centroids merely shortlist polygons. All46,747and130,435centroids mapped,with zero unmapped points. Since every source cell has positive driver,the positive-driver diagnostic spans each whole mesh. It is explicitly NOT asserted to be the actual FPZ.

| Positive-driver diagnostic | Existing46,747mesh | Native1%130,435control |
|---|---:|---:|
| h/l0 min | 0.05182 | 0.04998 |
| h/l0 median | 0.41475 | 0.29379 |
| h/l0 p90 | 1.15398 | 0.60702 |
| h/l0 max | 3.35850 | 2.08747 |
| Elements with longest-edge h/l0≤0.2 | 2.768% | 3.560% |
| Energy-proxy-weighted median h/l0 | 0.60328 | 0.29933 |
| Proxy energy associated with h/l0>0.2 | 98.869% | 97.560% |

These do not prove that the corresponding whole-domain fractions must be refined. Low diffuse damage/energy does not automatically require five elements per l0 everywhere. A converged physical phase field and a scientifically justified localization/convergence criterion are needed to distinguish the required regions. The earlier broad tip/ligament/hole diagnostic-box results remain unchanged in `f1641_native_mesh_metrics.json`;no coverage requirement was waived or replaced by a favorable percentile.

Hole geometry is a separate measurement:the existing1%mesh has maximum boundary-node radial error4.10e-8mm and maximum chord-midpoint error6.744e-6mm,with preserved slit-tip corners. Those geometry results do not establish adequate phase-field resolution or a traction-free solver response. See the preceding native-mesh report for full geometric/shape metrics.

## Nearest numerical milestone and exact missing predicate

The hypothesis that the available intact indicator/energy field alone establishes a defensible selective fracture-resolution domain is **not established**. No threshold is invented to make it succeed. Existing mesh fracture accuracy and full production readiness remain unqualified. A specifically bounded diagnostic pilot could be proposed for operator compatibility and physical-state acquisition,but this assessment does not approve it or establish an endpoint/acceptance contract.

The exact missing evidence is an accepted **coupled frozen-UEL off-axis-hole equilibrium state**,including spatial d,H,grad(d),reaction/load history,elastic/fracture energy and irreversibility/bounds diagnostics,under the intended plane-strain law. A mathematically justified alternative localization/error criterion would also need independent scientific acceptance. The smallest legitimate follow-up is a distinct reviewed physical-state-acquisition pilot using an existing hole mesh and the frozen UEL,with a predeclared bounded load/checkpoint and objectives;its endpoint,expected outputs,failure criteria and scope must be defined before qualification. It must not be presented as a mesh-converged final fracture demonstration. No completed no-hole/central-hole or Method C state can substitute for this geometry.

Future execution still needs a distinct execution-qualified task,exact frozen-source Abaqus2023datacheck,queue-aware resources/notifications,once-only accounting and genuine independent-review provenance. The scratch UEL hash mismatch remains preserved;the old datacheck cannot qualify a changed frozen-source candidate. The verified168h/336hqueue maxima remain available;no8hcluster-wide rejection is applied. No pilot is currently ready for immediate submission under F1641's zero-PBS scope.

Five independent algebra/kinematics tests pass. An initial serialization failure on a NumPy int64 count was repaired by returning native float from the scalar driver;the same calculation then completed and tests passed again. Original sources,existing meshes and frozen UEL remain unchanged.
