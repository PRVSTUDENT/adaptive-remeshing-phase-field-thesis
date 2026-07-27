# Molnar Single-Notch Extraction

Date: 2026-07-26

Classification: `technical_pass_scientific_unchecked`

## Scope

This extraction reads the Molnar single-notch ODB and records benchmark technical evidence plus RF-U and phase/history summaries.

## Technical Status

- ODB readable: `True`
- Analysis completed successfully in `.sta`: `True`
- Node count: `3998`
- Element count: `11790`
- Curve rows: `72`

## Outputs

- `rf1_u1_curve.csv`
- `matched_states.csv`
- `matched_state_01_Step-1_frame_0020_contour_sdv14_sdv15_sdv16.csv`
- `matched_state_02_Step-1_frame_0050_contour_sdv14_sdv15_sdv16.csv`
- `matched_state_03_Step-2_frame_0010_contour_sdv14_sdv15_sdv16.csv`
- `matched_state_04_Step-2_frame_0020_contour_sdv14_sdv15_sdv16.csv`

## Matched Displacement States

| Target abs U | Matched step | Frame | U | RF | Max SDV15 | Max SDV16 |
|---:|---|---:|---:|---:|---:|---:|
| 2.000000e-03 | `Step-1` | 20 | 2.000000e-03 | 9.212781e-02 | 1.824176e-02 | 1.069451e-02 |
| 5.000000e-03 | `Step-1` | 50 | 5.000000e-03 | 2.253338e-01 | 1.268854e-01 | 8.570705e-02 |
| 6.000000e-03 | `Step-2` | 10 | 6.000000e-03 | 2.669526e-01 | 1.972338e-01 | 1.477963e-01 |
| 7.000000e-03 | `Step-2` | 20 | 7.000000e-03 | 3.062959e-01 | 2.992290e-01 | 2.654522e-01 |

## Warnings

- ***WARNING: 1 elements are distorted. Either the isoparametric angles are out of the suggested limits or the triangular or tetrahedral quality
- ***WARNING: AN OUTPUT REQUEST AT EXACT TIME POINTS IS NOT SUPPORTED IN AN ANALYSIS WITH DIRECT INCREMNTATION. IT WILL BE CHANGED TO AN
- ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS
- ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS *Step, name=Step-2, nlgeom=NO, inc=2000
- ***WARNING: AN OUTPUT REQUEST AT EXACT TIME POINTS IS NOT SUPPORTED IN AN ANALYSIS WITH DIRECT INCREMNTATION. IT WILL BE CHANGED TO AN
- ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS
- ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS *Step, name=Step-1, nlgeom=NO, inc=500

## Field Outputs By Step

- `Step-2`: `EVOL, RF, S, SDV1, SDV10, SDV11, SDV12, SDV13, SDV14, SDV15, SDV16, SDV2, SDV3, SDV4, SDV5, SDV6, SDV7, SDV8, SDV9, U`
- `Step-1`: `EVOL, RF, S, SDV1, SDV10, SDV11, SDV12, SDV13, SDV14, SDV15, SDV16, SDV2, SDV3, SDV4, SDV5, SDV6, SDV7, SDV8, SDV9, U`

## History Outputs By Step

- `Step-2`: `ALLAE, ALLAE (Repeated: key = Step-2, 15), ALLCCDW, ALLCCE, ALLCCEN, ALLCCET, ALLCCSD, ALLCCSDN, ALLCCSDT, ALLCD, ALLCD (Repeated: key = Step-2, 12), ALLDMD, ALLDTI, ALLEE, ALLFD, ALLIE, ALLIE (Repeated: key = Step-2, 18), ALLJD, ALLKE, ALLKE (Repeated: key = Step-2, 8), ALLKL, ALLPD, ALLPD (Repeated: key = Step-2, 11), ALLQB, ALLSD, ALLSE, ALLSE (Repeated: key = Step-2, 9), ALLVD, ALLWK, ALLWK (Repeated: key = Step-2, 10), ETOTAL, ETOTAL (Repeated: key = Step-2, 19)`
- `Step-1`: `ALLAE, ALLAE (Repeated: key = Step-1, 15), ALLCCDW, ALLCCE, ALLCCEN, ALLCCET, ALLCCSD, ALLCCSDN, ALLCCSDT, ALLCD, ALLCD (Repeated: key = Step-1, 12), ALLDMD, ALLDTI, ALLEE, ALLFD, ALLIE, ALLIE (Repeated: key = Step-1, 18), ALLJD, ALLKE, ALLKE (Repeated: key = Step-1, 8), ALLKL, ALLPD, ALLPD (Repeated: key = Step-1, 11), ALLQB, ALLSD, ALLSE, ALLSE (Repeated: key = Step-1, 9), ALLVD, ALLWK, ALLWK (Repeated: key = Step-1, 10), ETOTAL, ETOTAL (Repeated: key = Step-1, 19)`

## Job Time Summary

```text
     JOB TIME SUMMARY
       USER TIME (SEC)      =     0.30    
       SYSTEM TIME (SEC)    =     5.00E-02
       TOTAL CPU TIME (SEC) =     0.35    
       WALLCLOCK TIME (SEC) =            1
1

   Abaqus 2023                                  Date 27-Jul-2026   Time 08:07:59
```

```text
     JOB TIME SUMMARY
       USER TIME (SEC)      =     8.16E+02
       SYSTEM TIME (SEC)    =      19.    
       TOTAL CPU TIME (SEC) =     8.35E+02
       WALLCLOCK TIME (SEC) =          919
```
