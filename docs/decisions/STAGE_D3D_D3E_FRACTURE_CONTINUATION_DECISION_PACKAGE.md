# Stage D3D/D3E Fracture-Continuation Decision Package

**Classification:** `stage_d3d_d3e_decision_package_prepared`  
**Date:** 2026-07-23  
**Prerequisite gate:** `stage_d3a3_state_transfer_gate_closed` (accepted R4 hold `1377471.mmaster02`)  

## Purpose

This package prepares a **decision** on whether and how to leave the accepted
D3A3 compatibility-ingestion/release-hold state and enter a **bounded** fracture
continuation segment. It does **not** authorize decks, PBS scripts, or
submissions.

Machine-readable companion:

- `runs/hpc/stage_d3/fracture_continuation_decision/D3D_D3E_DECISION_PACKAGE.json`
- `configs/state_transfer/d3d_d3e_continuation_options.yaml`
- `docs/studies/STAGE_D3D_ACTIVE_SET_CONTINUATION_PROTOCOL.md`
- `docs/studies/STAGE_D3E_UNINTERRUPTED_TARGET_REFERENCE_PROTOCOL.md`

## Critical scientific constraint from accepted R4

The accepted R4 state is an **obstacle-constrained KKT state**:

| Quantity | Accepted value |
|----------|---------------:|
| Active lower-bound phase nodes | **6446** |
| Free phase nodes | **155** |
| F1 free residual ∞-norm | \(1.9449\times10^{-10}\) |
| Minimum active multiplier | \(-9.9619\times10^{-13}\) |
| Checkpoint top \(U_2\) | \(0.003000000026077032\) mm |

Therefore a direct continuation to peak **cannot scientifically**:

1. **Keep all 6446 active nodes fixed** for further loading — most of the phase
   field would be prevented from developing new damage.
2. **Release all 6446 nodes simultaneously** — their active KKT multipliers show
   they are not generally in unconstrained equilibrium; abrupt free release
   could reintroduce healing and large RF/energy jumps.

**Inference:** D3D must first establish whether the **current** active set
remains valid over **one small load segment**. It must **not** immediately
attempt peak or post-peak fracture.

## What D3A3 already proved (not re-proved by D3D)

- Nonmatching target-state ingestion  
- Compatible phase/history initialization  
- Mechanical checkpoint equilibration  
- Actual-history KKT consistency at the release hold  
- Irreversible active-set release over the hold  
- Small RF and reconstructed-energy discontinuities  
- State retention through the release hold  

## What D3A3 did **not** prove

- Continued loading toward peak  
- Peak-force / peak-displacement agreement  
- Post-peak agreement  
- Crack-path agreement  
- Production-mesh transfer  
- Online/evolving remeshing  

## Decision routes

| Route | Scope | Current recommendation |
|-------|--------|------------------------|
| **A** | Stop at the accepted D3A3 compatibility gate | Scientifically valid closure; no further solver work |
| **B** | One bounded D3D active-set-validity segment | **Recommended next experiment** |
| **C** | Segmented continuation toward peak with repeated active-set updates | Broader workflow; **not yet authorized** |

**D3E** remains **conditional** on a successful D3D segment (`stage_d3d_active_set_segment_pass`).

### Route A — stop at D3A3

- **Valid** if the thesis only needs controlled state-transfer proof.  
- No deck/PBS preparation.  
- No D3D/D3E submission.

### Route B — recommended next experiment

One serial, pre-peak active-set-validity segment only:

| Item | Value |
|------|------:|
| Start \(U_2\) | \(0.003000000026077032\) mm (accepted R4 checkpoint) |
| End \(U_2\) | \(0.0031\) mm |
| \(\Delta U_2\) | \(\approx 0.0001\) mm |
| Mesh | Same 6400-element target as accepted R4 |
| Active/free set | Retain current **6446 / 155** for this diagnostic segment only |
| Peak context | Accepted H0 peak near \(U_2=0.0061\) mm; H1/H2-PUB near \(0.0058\) mm → segment is **far inside** pre-peak |

Eventual D3D executable (when authorized to prepare) must:

1. Reproduce accepted R4 Steps 1–3 **unchanged**.  
2. Verify the prefix reproduces the accepted R4 checkpoint and release state.  
3. Add **one** continuation step to \(U_2=0.0031\) mm.  
4. Retain the current 6446/155 set only for this bounded diagnostic.  
5. Save enough converged frames for KKT reconstruction over the segment.  
6. Include **no** automatic second segment.

### Route C — multi-segment continuation

- Requires successful Route B **and** a separately reviewed active-set update
  policy when D3D returns `stage_d3d_active_set_update_required`.  
- **Not authorized** by this package.  
- Automatic multi-segment loops and parameter sweeps remain **prohibited**.

## D3D acceptance framework (predeclared)

At every extracted continuation frame, assemble:

\[
r = K(H)\,d - f(H)
\]

using the **actual** phase and history at that frame.

Require:

| Gate | Tolerance |
|------|-----------|
| Node coverage | \(= 6601\) |
| IP coverage | \(= 25600\) |
| Non-positive detJ | \(= 0\) |
| Free residual ∞-norm | \(\le 10^{-8}\) |
| Minimum active multiplier | \(\ge -10^{-8}\) |
| Active bound error | \(\le 10^{-10}\) |
| Phase decrease violations | \(= 0\) |
| H decrease violations | \(= 0\) |
| TOP \(U_2\) | exact within \(10^{-8}\) of the prescribed frame value |
| TOP RF2 | finite |
| State reset | false |
| Spatial variation retained | true |

### Outcome classes

| Class | Meaning |
|-------|---------|
| `stage_d3d_active_set_segment_pass` | Segment KKT/irreversibility/reaction gates pass; D3E may be considered |
| `stage_d3d_active_set_update_required` | **Scientific result** (not implementation failure): one or more active nodes developed sufficiently negative multipliers; offline active-set update must be reviewed before another segment |
| `stage_d3d_solver_fail` | Abaqus/environment/staging failure |
| `stage_d3d_postprocessing_fail` | Extraction/KKT/validation pipeline failure |

## Conditional D3E proposal

D3E is a **virgin uninterrupted** calculation on the **same 6400-element target
mesh**, with the same material, UEL/UMAT, mechanical BCs, outputs, and final
displacement as the accepted D3D segment.

**Purpose:** isolate transfer effects without a mesh difference.

**Compare** over \(U_2 \in [0.0030, 0.0031]\) mm:

- RF–U NRMSE  
- Endpoint RF relative difference  
- Nodal phase normalized L2 / max difference  
- IP history normalized L2 / max difference  
- Reconstructed-energy relative difference  
- State and irreversibility violations  

### Predeclared diagnostic tolerances (must be accepted before execution)

| Metric | Tolerance |
|--------|-----------|
| RF–U NRMSE | \(\le 1\%\) |
| Endpoint RF difference | \(\le 1\%\) |
| Energy difference | \(\le 1\%\) |
| Phase normalized L2 difference | \(\le 5\%\) |
| History normalized L2 difference | \(\le 5\%\) |
| Phase/H decrease violations | \(= 0\) |

These tolerances **must not** be adjusted after results are observed.

## Authorization boundary

```text
D3D/D3E decision-package preparation: authorized (this package)
D3D deck/PBS preparation: blocked pending decision
D3D submission: blocked pending explicit authorization
D3E preparation and submission: blocked until D3D segment passes
Peak/post-peak continuation: blocked
Automatic multi-segment loop: prohibited
Parameter sweep: prohibited
```

## Recommendation

1. Accept this package as the decision record.  
2. Choose Route **A** (stop) or **B** (one D3D segment).  
3. If Route B is chosen, authorize **separately**:
   - D3D deck/PBS preparation, then  
   - exactly one D3D serial submission.  
4. Only if D3D returns `stage_d3d_active_set_segment_pass`, authorize D3E
   preparation and one reference submission under the predeclared tolerances.

## Evidence anchors

| Item | Path / ID |
|------|-----------|
| D3A3 closure | `docs/decisions/STAGE_D3_STATE_TRANSFER_CLOSURE.md` |
| Canonical marker | `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r4_compatible/D3A3.ok` |
| Accepted package | `package_compatible_r2` |
| Accepted job | `1377471.mmaster02` |
| Checkpoint \(U_2\) | `0.003000000026077032` mm |
| Active / free | 6446 / 155 |
