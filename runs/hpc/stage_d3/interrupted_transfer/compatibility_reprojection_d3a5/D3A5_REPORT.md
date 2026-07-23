# D3A5 Actual-History Compatibility Reprojection Report

- Classification: `stage_d3a5_actual_history_reprojection_pass`
- D3A5.ok: `True`

Offline sparse active-set obstacle solve using recovered R3 F1 phase as lower bound
and actual R3 F1 SDV16 history. No Abaqus job, ODB reread, Fortran, or new mesh.

## History change

- max |H_actual - H_old|: `0.00024847913211770677`
- normalized L2 H difference: `0.002048864763115822`
- H increase / decrease counts: `138` / `0`
- H_old sum / H_actual sum: `15.502653225304272` / `15.50319131427252`

## Causal residual at d_F1

- actual free residual: `1.2035463824381645e-08`
- old free residual: `1.1011428314305904e-20`
- max free residual node: `3200`

## KKT

- active / free nodes: `6446` / `155`
- free residual inf: `2.117582368135751e-21`
- min active multiplier: `-9.96194330970534e-13`
- active bound error: `0.0`
- max phase increase: `0.0001363565791405036`
- normalized L2 phase increase: `0.00034526314431873096`
- functional reduction: `1.9312385146478574e-12`
- changed active-set count vs D3A4: `4566`
- iterations: `9`

## Failures

- none

## package_compatible_r2

- classification: `stage_d3a5_compatible_package_r2_pass`
- nodes / IPs: `6601` / `25600`
- active nodes: `6446`
