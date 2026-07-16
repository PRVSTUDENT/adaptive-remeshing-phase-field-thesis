# Molnar Single-Notch Extraction

Date: 2026-07-14

Classification: `technical_pass_scientific_unchecked`

## Scope

This extraction reads the unchanged Molnar single-notch ODB and records the first benchmark technical evidence plus RF-U and phase/history summaries. It does not compare the curve or crack evolution against the paper yet.

## Technical Status

- ODB readable: `True`
- Analysis completed successfully in `.sta`: `True`
- Node count: `34507`
- Element count: `101556`
- Curve rows: `202`

## Outputs

- `single_notch_rf_u_phase_summary.csv`
- `single_notch_matched_displacement_states.csv`
- `matched_state_01_Step-1_frame_0040_contour_sdv14_sdv15_sdv16.csv`
- `matched_state_02_Step-1_frame_0100_contour_sdv14_sdv15_sdv16.csv`
- `matched_state_03_Step-2_frame_0058_contour_sdv14_sdv15_sdv16.csv`
- `matched_state_04_Step-2_frame_0100_contour_sdv14_sdv15_sdv16.csv`

## Matched Displacement States

| Target abs U2 | Matched step | Frame | U2 | RF2 | Max SDV15 | Max SDV16 |
|---:|---|---:|---:|---:|---:|---:|
| 2.000000e-03 | `Step-1` | 40 | 2.000000e-03 | 2.672886e-01 | 3.874145e-02 | 1.228316e-01 |
| 5.000000e-03 | `Step-1` | 100 | 5.000000e-03 | 6.462895e-01 | 3.119879e-01 | 1.398572e+00 |
| 6.000000e-03 | `Step-2` | 58 | 5.990000e-03 | 7.555778e-01 | 7.178758e-01 | 8.048712e+00 |
| 6.700000e-03 | `Step-2` | 100 | 6.700000e-03 | 7.491105e-01 | 1.004140e+00 | 1.933705e+03 |

## Warnings

- ***WARNING: AN OUTPUT REQUEST AT EXACT TIME POINTS IS NOT SUPPORTED IN AN ANALYSIS WITH DIRECT INCREMNTATION. IT WILL BE CHANGED TO AN
- ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS
- ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS *Step, name=Step-2, nlgeom=NO, inc=170
- ***WARNING: AN OUTPUT REQUEST AT EXACT TIME POINTS IS NOT SUPPORTED IN AN ANALYSIS WITH DIRECT INCREMNTATION. IT WILL BE CHANGED TO AN
- ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS
- ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS *Step, name=Step-1, nlgeom=NO, inc=500

## Field Outputs By Step

- `Step-2`: `RF, SDV1, SDV10, SDV11, SDV12, SDV13, SDV14, SDV15, SDV16, SDV2, SDV3, SDV4, SDV5, SDV6, SDV7, SDV8, SDV9, U`
- `Step-1`: `RF, SDV1, SDV10, SDV11, SDV12, SDV13, SDV14, SDV15, SDV16, SDV2, SDV3, SDV4, SDV5, SDV6, SDV7, SDV8, SDV9, U`

## History Outputs By Step

- `Step-2`: `none`
- `Step-1`: `none`

## Job Time Summary

```text
     JOB TIME SUMMARY
       USER TIME (SEC)      =      1.5    
       SYSTEM TIME (SEC)    =     0.17    
       TOTAL CPU TIME (SEC) =      1.6    
       WALLCLOCK TIME (SEC) =            2
1

   Abaqus 2023                                  Date 16-Jul-2026   Time 07:40:07
```

```text
     JOB TIME SUMMARY
       USER TIME (SEC)      =     2.08E+03
       SYSTEM TIME (SEC)    =      57.    
       TOTAL CPU TIME (SEC) =     2.14E+03
       WALLCLOCK TIME (SEC) =         2299
```
