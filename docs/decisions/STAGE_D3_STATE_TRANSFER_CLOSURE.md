# Stage D3 State-Transfer Gate Closure

**Classification:** `stage_d3a3_state_transfer_gate_closed`  
**Scientific result class:** `stage_d3a3_r4_compatible_release_pass`  
**Date:** 2026-07-23  

## Decision

The **D3A3 compatibility-ingestion/release-hold gate is closed**.

Accepted solver job: `1377471.mmaster02`  
Solver commit: `9aba51064f1025da61c578457c810f52900ef8a4`  
Evidence commit: `b7b500c80009a2aaad6a485eff4fdab55af68ba9`  
Accepted package: `package_compatible_r2`  
Canonical marker: `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r4_compatible/D3A3.ok`  
R4 marker: `runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r4_compatible/D3A3_R4.ok`  

Further D3A4/D3A5-style compatibility cycles are **not justified** unless a later
continuation run changes the history field enough to fail a newly declared gate.

## Accepted chain

| Stage | Job / product | Result |
|------|----------------|--------|
| R3 datacheck staging failure | `1377404.mmaster02` | pre-Abaqus staging fail (untracked runtime H) |
| R3 R1 datacheck | `1377409.mmaster02` | pass |
| Post-Python qualification | `1377416.mmaster02` | Python 3.11 + NumPy/SciPy pass |
| R3 full hold | `1377417.mmaster02` | Abaqus pass; active/free builder fail under Abaqus Python |
| Architectural replay | no PBS | closed M-071; free residual scientific finding |
| Actual-history KKT finding | residual `1.20e-8` | package H vs actual R3 F1 SDV16 |
| D3A5 reprojection | offline | `D3A5.ok`; free residual `2.12e-21` |
| package_compatible_r2 | offline | 6446 active / 155 free |
| R4 datacheck | `1377468.mmaster02` | pass |
| R4 full hold | `1377471.mmaster02` | pass; canonical `D3A3.ok` |

## Proved (bounded pre-peak scope)

- nonmatching target-state ingestion  
- compatible phase/history initialization  
- mechanical checkpoint equilibration  
- actual-history KKT consistency  
- irreversible active-set release  
- small RF and reconstructed-energy discontinuities  
- state retention through the release hold  

## Not proved

- continued loading to peak  
- peak-force or peak-displacement agreement  
- post-peak agreement  
- crack-path agreement  
- production-mesh transfer  
- online/evolving remeshing  

Do **not** claim `fracture_continuation_validated`.

## Accepted R4 metrics

| Quantity | Accepted R4 value |
|----------|------------------:|
| Target nodes/elements/IPs | 6601 / 6400 / 25600 |
| Active/free nodes | 6446 / 155 |
| SDV15 max transfer error | \(1.3878\times10^{-17}\) |
| SDV16 max transfer error | \(0\) |
| F1 free residual norm | \(1.9449\times10^{-10}\) |
| Minimum active multiplier | \(-9.9619\times10^{-13}\) |
| Active phase drift | \(6.9389\times10^{-18}\) |
| Phase/H irreversibility violations | \(0\) / \(0\) |
| RF release jump | \(2.2926\times10^{-4}\) |
| Energy release jump | \(1.2746\times10^{-5}\) |
| Maximum phase adjustment | \(0.0051714\) |
| Final classification | `stage_d3a3_r4_compatible_release_pass` |

## Evidence integrity

- Closure JSON: `runs/hpc/stage_d3/interrupted_transfer/D3A3_ACCEPTED_CLOSURE.json`  
- Evidence hashes: `runs/hpc/stage_d3/interrupted_transfer/D3A3_ACCEPTED_EVIDENCE_HASHES.json`  
- Scratch ODB path recorded with size and SHA-256; **not** copied into Git (`odb_repository_copy_created=false`).

## Authorization boundary after closure

```text
D3A3 compatibility gate: closed
Stage D3 closure documentation: complete
D3D: blocked pending explicit authorization
D3E: blocked pending explicit authorization
New PBS submission: not authorized by this closure
```

## Next item

Prepare the scoped D3D/D3E fracture-continuation decision package.  
No continuation submission without explicit authorization.
