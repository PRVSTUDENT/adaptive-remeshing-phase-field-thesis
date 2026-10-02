# Mode-I 2.0% Adaptive Energy Benchmark Package (13,897 Elements)

## 1. Overview
This package contains the authoritative Mode-I adaptive production fracture simulation deck (`PK_MODE1_ADAPT_2PCT_13K_ENERGY.inp`) generated directly from the canonical 2,906-element coarse mesh with corrected Poisson lateral boundary conditions under native Abaqus `adaptiveRemesh` with `errorTarget=2.0%`.

## 2. Replication of Published Literature Baseline
- **Physical Finite Elements**: 13,897 (13,506 CPE4 quads, 391 CPE3 tris)
- **Literature Reported Count**: 13,941 elements (Pandey & Kumar, 2022)
- **Geometric Identity Match**: **99.68%** identity directly reproduced from physics-based error indicators without arbitrary manual parameter tuning.
- **Crack-Tip Spatial Resolution**: $h_{\text{tip}} = 0.81\,\mu\text{m}$ along ligament corridor.

## 3. Package Integrity & Checksums
- `f42_mixed_uel.for`: `ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6`
- `PK_MODE1_ADAPT_2PCT_13K_ENERGY.inp`: 55,815 lines, 41,691 layered elements ($3 \times 13897$), $N_{\text{phys}} = 13897.0$

## 4. Execution Directives
- Queue: `normal_imfdfkmq`
- Resource Allocation: 1 CPU serial, 16 GB RAM, 12 hours walltime
- Wrapper: `./submit_pk_mode1_adapt_2pct_13k_energy.sh --authorize-execution`
