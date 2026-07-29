# Molnar Single-Notch Extraction

Date: 2026-07-26

Classification: `technical_pass_scientific_unchecked`

## Scope

This extraction reads the Molnar single-notch ODB and records benchmark technical evidence plus RF-U and phase/history summaries.

## Technical Status

- ODB readable: `True`
- Analysis completed successfully in `.sta`: `True`
- Node count: `12381`
- Element count: `36192`
- Curve rows: `112`

## Outputs

- `rf1_u1_curve.csv`
- `matched_states.csv`
- `matched_state_01_Step-1_frame_0020_contour_sdv14_sdv15_sdv16.csv`
- `matched_state_02_Step-1_frame_0050_contour_sdv14_sdv15_sdv16.csv`
- `matched_state_03_Step-2_frame_0004_contour_sdv14_sdv15_sdv16.csv`
- `matched_state_04_Step-2_frame_0008_contour_sdv14_sdv15_sdv16.csv`

## Matched Displacement States

| Target abs U | Matched step | Frame | U | RF | Max SDV15 | Max SDV16 |
|---:|---|---:|---:|---:|---:|---:|
| 2.000000e-03 | `Step-1` | 20 | 2.000000e-03 | 2.561931e-02 | 8.589348e-03 | 1.672547e-02 |
| 5.000000e-03 | `Step-1` | 50 | 5.000000e-03 | 6.337489e-02 | 5.600499e-02 | 1.160963e-01 |
| 6.000000e-03 | `Step-2` | 4 | 6.000000e-03 | 7.560866e-02 | 8.271292e-02 | 1.779763e-01 |
| 7.000000e-03 | `Step-2` | 8 | 7.000000e-03 | 8.759730e-02 | 1.157809e-01 | 2.612400e-01 |

## Warnings

- ***WARNING: AN OUTPUT REQUEST AT EXACT TIME POINTS IS NOT SUPPORTED IN AN ANALYSIS WITH DIRECT INCREMNTATION. IT WILL BE CHANGED TO AN
- ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS
- ***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS *Step, name=Step-2, nlgeom=NO, inc=6000
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
       USER TIME (SEC)      =     0.62    
       SYSTEM TIME (SEC)    =     8.00E-02
       TOTAL CPU TIME (SEC) =     0.70    
       WALLCLOCK TIME (SEC) =            1
1

   Abaqus 2023                                  Date 28-Jul-2026   Time 12:53:29
```

```text
     JOB TIME SUMMARY
       USER TIME (SEC)      =     6.76E+03
       SYSTEM TIME (SEC)    =     1.49E+02
       TOTAL CPU TIME (SEC) =     6.91E+03
       WALLCLOCK TIME (SEC) =         7123
```
