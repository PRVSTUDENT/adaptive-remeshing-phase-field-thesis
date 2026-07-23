# Stage D3E Uninterrupted Target-Mesh Reference Protocol

**Classification:** `stage_d3e_uninterrupted_target_reference_protocol_prepared`  
**Status:** Conditional protocol only — **blocked** until D3D segment passes  
**Depends on:** `stage_d3d_active_set_segment_pass` on the same mesh and load range  

## Scientific objective

Provide a **virgin, uninterrupted** calculation on the **same 6400-element
target mesh** used by accepted D3A3-R4 / proposed D3D, so that transfer effects
can be isolated **without** a mesh difference.

D3E is **not**:

- a production-mesh H1/H2 comparison,
- a source-mesh H0 remake with different discretization,
- a peak/post-peak campaign,
- a substitute for D3D active-set validity.

## Conditional trigger

D3E preparation and submission are blocked until:

1. D3D completes with classification **`stage_d3d_active_set_segment_pass`**, and  
2. Explicit user authorization for **one** D3E job is given.

If D3D returns `stage_d3d_active_set_update_required`, D3E is **not** opened;
the active-set policy must be resolved first.

## Model identity requirements

When later authorized, D3E must match the accepted D3D segment on:

| Item | Requirement |
|------|-------------|
| Mesh | Same 6400-element target mesh as R4 / D3D |
| Material | Same |
| UEL/UMAT | Same Fortran lineage as accepted R4 (byte-identity policy as declared at execution) |
| Mechanical BCs | Bottom \(U_2=0\), anchor \(U_1=0\), top \(U_2\) ramp |
| Displacement range | Same final \(U_2=0.0031\) mm as the accepted D3D segment |
| Outputs | Same field requests needed for RF–U, phase, history, energy reconstruction |
| Initialization | Virgin (no transferred state) |

## Comparison window

Compare D3D continuation segment vs D3E virgin response over:

\[
U_2 \in [0.0030,\ 0.0031]\ \mathrm{mm}
\]

(using the accepted checkpoint \(U_2=0.003000000026077032\) as the left endpoint
of the transfer-aware path and the common right endpoint \(0.0031\)).

## Predeclared comparison metrics

| Metric | Definition (summary) |
|--------|----------------------|
| RF–U NRMSE | Normalized RMS difference of TOP RF–U curves over the window |
| Endpoint RF relative difference | \(\lvert RF_2^{\mathrm{D3D}}-RF_2^{\mathrm{D3E}}\rvert / \max(\lvert RF_2^{\mathrm{D3E}}\rvert,\varepsilon)\) at \(U_2=0.0031\) |
| Nodal phase L2 / max | Normalized L2 and max \(\lvert d^{\mathrm{D3D}}-d^{\mathrm{D3E}}\rvert\) |
| IP history L2 / max | Normalized L2 and max \(\lvert H^{\mathrm{D3D}}-H^{\mathrm{D3E}}\rvert\) |
| Reconstructed energy relative difference | Relative difference of total reconstructed internal energy |
| Irreversibility | Phase/H decrease violation counts on both solutions |

## Predeclared diagnostic tolerances

**Must be accepted before execution. Must not be adjusted after results.**

| Metric | Tolerance |
|--------|-----------|
| RF–U NRMSE | \(\le 1\%\) |
| Endpoint RF relative difference | \(\le 1\%\) |
| Energy relative difference | \(\le 1\%\) |
| Phase normalized L2 difference | \(\le 5\%\) |
| History normalized L2 difference | \(\le 5\%\) |
| Phase decrease violations | \(= 0\) |
| H decrease violations | \(= 0\) |

## Outcome guidance (conceptual)

| Outcome | Interpretation |
|---------|----------------|
| All tolerances met | Transfer-aware segment agrees with virgin target response within predeclared bounds |
| RF/energy out of tolerance | Transfer path may still carry residual incompatibility or path dependence |
| Phase/H L2 out of tolerance | Field-level transfer discrepancy even if global RF is close |
| Irreversibility violations | Scientific/technical blocker; do not reopen peak work |

## Prohibitions

- D3E preparation before D3D segment pass  
- Changing mesh relative to D3D  
- Peak/post-peak extension in the first D3E job  
- Tolerance retuning after observation  
- Parameter sweeps  

## Authorization

```text
D3E protocol documentation: prepared
D3E preparation and submission: blocked until D3D segment passes
Peak/post-peak continuation: blocked
```
