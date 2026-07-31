# Stage F7 H2 irreversibility forensic audit

## Result

PBS job `1380084.mmaster02` completed the read-only Abaqus/ODB extraction and
failed only in the downstream Python 3.11 report step (`Exit_status=12`).
The extracted fixed-material-point evidence is complete for SDV15: 102 frames,
101 adjacent-frame pairs, and stable keys formed from instance, element,
integration point, section point, and position.

- Minimum fixed-point increment: `-5.853176116943359e-4`
- Strict negative increments: `1120`
- Increments below `-1e-4`: `62`
- Affected material points: `126`
- Affected elements: `75`
- Targeted event frame pairs: `26`

The earlier framewise-maximum decreases are therefore not only a
maximum-location switching artifact. Genuine local SDV15 decreases occur at
fixed material points. The H2 result remains a scientific irreversibility
failure and is not accepted as a converged fracture reference.

SDV14 was present and showed a similar minimum decrement
(`-5.866885185241699e-4`, 1119 strict decreases), but its role as a history
variable requires source-level verification before it is used as an
authoritative acceptance field.

## Wrapper failure boundary

The analyzer attempted to convert every response-curve CSV field to `float`
and stopped on the string `Step-1`. Consequently, the combined status and
H1--H2 comparison report were not generated. This reporting defect does not
invalidate the already written fixed-point ODB evidence.

No solver or datacheck was executed. The source ODB remained scratch-only.
Evidence is retained under
`runs/hpc/stage_f/f7_h2_irreversibility_and_miseseri_api_batch/evidence/1380084.mmaster02/`.

