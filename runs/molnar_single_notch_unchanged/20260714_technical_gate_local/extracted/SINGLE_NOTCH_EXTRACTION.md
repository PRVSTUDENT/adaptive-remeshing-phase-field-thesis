# Molnar Single-Notch Extraction

Date: 2026-07-14

Classification: `technical_pass_scientific_unchecked`

## Scope

This extraction reads the unchanged Molnar single-notch ODB and records the first benchmark technical evidence plus RF-U and phase/history summaries. It does not compare the curve or crack evolution against the paper yet.

## Technical Status

- ODB readable: `True`
- Analysis completed successfully in `.sta`: `True`
- Node count: `3998`
- Element count: `11790`
- Curve rows: `72`

## Outputs

- `single_notch_rf_u_phase_summary.csv`
- `single_notch_matched_displacement_states.csv`
- `matched_state_01_Step-1_frame_0020_contour_sdv14_sdv15_sdv16.csv`
- `matched_state_02_Step-1_frame_0050_contour_sdv14_sdv15_sdv16.csv`
- `matched_state_03_Step-2_frame_0010_contour_sdv14_sdv15_sdv16.csv`
- `matched_state_04_Step-2_frame_0020_contour_sdv14_sdv15_sdv16.csv`

## Matched Displacement States

| Target abs U2 | Matched step | Frame | U2 | RF2 | Max SDV15 | Max SDV16 |
|---:|---|---:|---:|---:|---:|---:|
| 2.000000e-03 | `Step-1` | 20 | 2.000000e-03 | 2.668120e-01 | 3.597792e-02 | 2.079785e-02 |
| 5.000000e-03 | `Step-1` | 50 | 5.000000e-03 | 6.266450e-01 | 2.755390e-01 | 2.128282e-01 |
| 6.000000e-03 | `Step-2` | 10 | 6.000000e-03 | 7.214059e-01 | 5.367833e-01 | 6.453215e-01 |
| 7.000000e-03 | `Step-2` | 20 | 7.000000e-03 | 1.395231e-03 | 1.010493e+00 | 3.377802e+02 |

## Warnings

- ***WARNING: 1 elements are distorted. Either the isoparametric angles are out of the suggested limits or the triangular or tetrahedral quality
- ***WARNING: AN OUTPUT REQUEST AT EXACT TIME POINTS IS NOT SUPPORTED IN AN ANALYSIS WITH DIRECT INCREMNTATION. IT WILL BE CHANGED TO AN
- ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS
- ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS *Step, name=Step-2, nlgeom=NO, inc=2000
- ***WARNING: AN OUTPUT REQUEST AT EXACT TIME POINTS IS NOT SUPPORTED IN AN ANALYSIS WITH DIRECT INCREMNTATION. IT WILL BE CHANGED TO AN
- ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS
- ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS *Step, name=Step-1, nlgeom=NO, inc=500

## Field Outputs By Step

- `Step-1`: `RF, SDV1, SDV10, SDV11, SDV12, SDV13, SDV14, SDV15, SDV16, SDV2, SDV3, SDV4, SDV5, SDV6, SDV7, SDV8, SDV9, U`
- `Step-2`: `RF, SDV1, SDV10, SDV11, SDV12, SDV13, SDV14, SDV15, SDV16, SDV2, SDV3, SDV4, SDV5, SDV6, SDV7, SDV8, SDV9, U`

## History Outputs By Step

- `Step-1`: `none`
- `Step-2`: `none`

## Job Time Summary

```text
     JOB TIME SUMMARY
       USER TIME (SEC)      =     0.30    
       SYSTEM TIME (SEC)    =     0.10    
       TOTAL CPU TIME (SEC) =     0.40    
       WALLCLOCK TIME (SEC) =            0
1

   Abaqus 2024                                  Date 14-Jul-2026   Time 10:55:03
```

```text
     JOB TIME SUMMARY
       USER TIME (SEC)      =     8.22E+02
       SYSTEM TIME (SEC)    =      25.    
       TOTAL CPU TIME (SEC) =     8.47E+02
       WALLCLOCK TIME (SEC) =          901
```
