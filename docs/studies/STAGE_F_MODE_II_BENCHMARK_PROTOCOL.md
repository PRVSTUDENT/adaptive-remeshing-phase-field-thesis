# Stage F — Mode-II pure-shear benchmark protocol

Classification: `stage_f_mode_ii_h0_prepared`  
Date: 2026-07-25

## Scientific purpose

After scoped Mode-I pre-refinement closeout, the next scientific stage tests
whether the accepted Molnar staggered UEL/UMAT workflow and later MISESERI
pipeline remain usable when the crack path is not the simple straight Mode-I
ligament path. Stage F begins with pure shear (Mode II, Molnar Fig. 6,
\(\alpha=0^\circ\)).

## Formulation boundary

- Retain the accepted Molnar staggered formulation only.
- Do not mix Msekh monolithic or Pandey formulation changes into the UEL.
- F0 changes only geometry role (same mesh), pure-shear BCs/loading, and
  output requests.
- No MISESERI remeshing in F0/F1-J0.

## F0 freeze summary

| Item | Value |
|---|---|
| Geometry | 1×1 mm plate, left notch 0.5 mm at mid-height |
| Mesh | Mode-I H0 supplementary: 3930 physical / 11790 layered / 3998 nodes |
| E, ν, Gc, lc | 210 kN/mm², 0.3, 0.0027 kN/mm, 0.015 mm |
| Plane model | plane strain, thickness 1 mm |
| Phase convention | d=0 intact, d=1 broken |
| Loading | top U1 via RP; bottom fully fixed; top U2 fixed |
| Endpoint schedule | provisional Mode-I H0 amplitudes to 0.010 mm |
| RF component | RF1 |
| RF reference | insufficient (Fig. 7 is tension) |
| Crack reference | qualitative curved shear path (Fig. 6c) |
| Path threshold | provisional SDV15 ≥ 0.5 |

## Package

```text
models/generated/mode_ii/h0_serial/
scripts/model_generation/build_mode_ii_h0_serial.py
scripts/validation/validate_mode_ii_h0_static.py
configs/studies/mode_ii_molnar_shear.yaml
```

## Fail-closed lane

```text
runs/hpc/stage_f/mode_ii_h0/
scripts/hpc/stage_f/
```

Authorization prepared with all execution flags false.

## F1-J0 datacheck (not authorized yet)

- Job: `mode_ii_h0_dc`
- 1 CPU, 1 rank, 1 thread, 16 GB, 00:30:00, `entry_imfdfkmq`
- Abaqus 2023, Intel 2024.2
- Pass marker: `MODE_II_H0_DATACHECK.ok`
- Maximum submissions: 1; automatic retry: false

## Later jobs (not prepared for submission)

- F1-J1 serial baseline after F1-J0 pass
- F2 H1 uniform reference
- F3 MISESERI pre-analysis
- F4 refined fracture comparison
- F5 interrupted transfer only after F4

## Excluded from Stage F entry

- Stage-P reopening
- threaded/MPI production
- D3D reopening
- thesis-submission packaging work
