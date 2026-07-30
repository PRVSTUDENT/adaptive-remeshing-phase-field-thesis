# Stage F4 official corrected MISESERI pre-analysis

Date: 2026-07-30  
Job: `1379893.mmaster02` (`M2MISER1`)  
Classification: `official_corrected_pbs_validation_pass`

## Result boundary

The PBS solver passed (`ABAQUS_RC=0`) and the PBS exporter passed
(`EXT_RC=0`). The original PBS validator remains recorded as `VAL_RC=1`
because its syntax was incompatible with the older Abaqus Python runtime.
That historical result is not rewritten. The same preserved lightweight
evidence passed an isolated, syntax-corrected offline validation
(`offline_repaired_validation_rc=0`, 18/18 checks).

## Frozen evidence

- ODB SHA-256:
  `bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac`
- exported CSV SHA-256:
  `49b0c5f7a784f361e846a7100370d5909e4e9e3faaa9c40694a40375c2e43ac5`
- 3,930 physical element rows; every MISESERI value finite and positive
- required fields: `MISESERI`, `MISESAVG`, `S`, `E`, `EVOL`, `U`, `RF`
- final U1: `0.0010000000474974513 mm`
- final RF1: `0.046069372445344925`
- MISESERI min/max/mean:
  `6.865544128231704e-05 / 0.18701137602329254 / 0.001633144879951595`
- true slit topology retained by the accepted source package

Canonical lightweight evidence:
`runs/hpc/stage_f/stage_f4_replacement/evidence/1379893.mmaster02/`.

## Scientific conclusion

The official corrected PBS MISESERI pre-analysis gate is passed and the
Pandey-Kumar error-indicator field is usable for preprocessing. Native Abaqus
remeshing, refined-deck generation, mesh-integrity qualification and the final
refined phase-field comparison have not been performed or validated.
