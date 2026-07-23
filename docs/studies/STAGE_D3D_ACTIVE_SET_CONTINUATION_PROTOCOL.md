# Stage D3D Active-Set Continuation Protocol

**Classification:** `stage_d3d_active_set_continuation_protocol_prepared`  
**Status:** Decision package only — **no** deck, PBS, or submission authorized  
**Depends on:** accepted D3A3-R4 hold (`1377471.mmaster02`), `package_compatible_r2`

## Scientific objective

Determine whether the **accepted R4 obstacle active set** (6446 lower-bound nodes /
155 free nodes) remains a **valid** constrained set over **one small pre-peak load
segment**, using the **actual** phase and history fields along that segment.

This is **not**:

- a peak-force experiment,
- a crack-path experiment,
- an automatic multi-segment remeshing workflow,
- a free release of all active nodes.

## Why this design

The accepted R4 state is KKT-constrained. Direct peak continuation cannot
scientifically keep all 6446 nodes fixed (would block new damage) or release
them all at once (multipliers imply constrained, not free, equilibrium).

D3D therefore tests **active-set validity over a tiny load increment** before any
broader continuation.

## Proposed segment (Route B)

| Quantity | Value |
|----------|------:|
| Start \(U_2\) | \(0.003000000026077032\) mm |
| End \(U_2\) | \(0.0031\) mm |
| \(\Delta U_2\) | \(\approx 0.0001\) mm |
| CPUs | 1 |
| Memory | 16 GB (proposed; finalize at deck authorization) |
| Walltime | finalize at deck authorization (serial; expect short if R4-like) |
| Mode | serial, `mp_mode=threads`, `OMP_NUM_THREADS=1` |
| MPI | prohibited |

Peak context (reference only): H0 peak near \(0.0061\) mm; H1/H2-PUB near
\(0.0058\) mm. The proposed segment is deliberately **far inside** the pre-peak
range.

## Executable requirements (when later authorized)

When D3D deck preparation is explicitly authorized, the executable must:

1. **Reproduce** accepted R4 Steps 1–3 **byte-for-byte in BC logic and package
   inputs** (package_compatible_r2, same Fortran lineage, same runtime H as R4
   unless a separately reviewed package change is authorized).
2. **Prefix verification:** confirm the R4 checkpoint and release state are
   reproduced within the same scientific gates as the accepted hold
   (transfer, TOP \(U_2\), KKT at F1 if re-evaluated, no healing).
3. **One continuation step only:** load TOP \(U_2\) from checkpoint to
   \(0.0031\) mm.
4. **Retain** the current 6446/155 active/free set for this diagnostic segment
   only (no simultaneous free release of active nodes).
5. **Frame output:** enough converged frames along the segment to reassemble
   \(r=K(H)d-f(H)\) at each extracted frame.
6. **No second segment** in the same job or automatic retry loop.

## Per-frame KKT and state gates

At every extracted continuation frame:

\[
r = K(H)\,d - f(H)
\]

| Gate | Requirement |
|------|-------------|
| Node coverage | \(= 6601\) |
| IP coverage | \(= 25600\) |
| Non-positive detJ | \(= 0\) |
| Free residual ∞-norm | \(\le 10^{-8}\) |
| Minimum active multiplier | \(\ge -10^{-8}\) |
| Active bound error | \(\le 10^{-10}\) |
| Phase decrease violations | \(= 0\) |
| H decrease violations | \(= 0\) |
| TOP \(U_2\) | within \(10^{-8}\) of prescribed frame value |
| TOP RF2 | finite |
| State reset | false |
| Spatial variation retained | true |

**Do not relax tolerances after observing results.**

## Outcome classes

| Class | Type | Meaning |
|-------|------|---------|
| `stage_d3d_active_set_segment_pass` | Scientific pass | Active set remains valid over the segment; D3E may be considered |
| `stage_d3d_active_set_update_required` | **Scientific result** | One or more currently active nodes developed sufficiently negative multipliers; offline active-set update must be reviewed before another segment — **not** an implementation failure |
| `stage_d3d_solver_fail` | Technical fail | Abaqus / compiler / staging / PBS failure |
| `stage_d3d_postprocessing_fail` | Technical fail | Extraction / assembly / validator pipeline failure |

## Post-segment actions (conceptual only)

| Outcome | Next |
|---------|------|
| Segment pass | Optional authorization of D3E virgin reference on the same mesh |
| Active-set update required | Offline update protocol (new decision); no automatic re-submit |
| Solver / postprocess fail | Preserve evidence; no automatic retry |

## Prohibitions

- Automatic multi-segment loop  
- Parameter sweep  
- Peak/post-peak jump in the first D3D job  
- Simultaneous release of all active nodes  
- Deck/PBS generation in this decision-package task  

## Authorization

```text
D3D protocol documentation: prepared
D3D deck/PBS preparation: blocked pending decision
D3D submission: blocked pending explicit authorization
```
