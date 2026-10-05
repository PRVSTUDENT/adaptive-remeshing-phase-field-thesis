# Pre-Job Anti-Deviation Card: Package 30 (Stage 14U-AM Spatial Fine Candidate)

## 1. Job Metadata
- **Package ID:** PKG-30-STAGE14-ADAPTIVE-SPATIAL-FINE-FRACTURE
- **Task ID:** F1222-GATE6B-STAGE14UAM-CONTROLLED-SPATIAL-CONVERGENCE-20261004
- **Directory:** `models/pandey_kumar_mode1/30_stage14_adaptive_candidate_spatial_fine`
- **Job Name:** `PK_M1_14AM_SOLVE`
- **Queue:** `normal_imfdfkmq` (1 CPU, 16 GB, 24:00:00 walltime)
- **Target Deck:** `PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_FRACTURE.inp`

## 2. Frozen Invariant Verification
- [x] **Pre-Analysis Source:** `PK_M1_JOB1_INF_COMPANION_2906.odb` (Package 93, Step 1 Inc 880 / final frame)
- [x] **Remeshing Sizing Contract:**
  - `errorTarget = 1.0%` (FROZEN)
  - `refinementFactor = 10` (FROZEN)
  - `coarseningFactor = NOT_ALLOWED` (FROZEN)
  - `maxElementSize = 0.020 mm` (FROZEN)
  - `region = ALL_ELEM` (FROZEN)
- [x] **Isolated Refinement Parameter:**
  - `minElementSize = 0.0005 mm` (reduced by factor of 2 from baseline 0.001 mm)
  - Realized $h_{\min} = 0.000553\,\text{mm}$ ($h_{\min}/l_0 = 0.0738$)
- [x] **Physical Constants:**
  - $E = 210.0\,\text{GPa}$
  - $\nu = 0.3$
  - $G_c = 0.0027\,\text{kN/mm}$
  - $l_0 = 0.0075\,\text{mm}$
  - $\eta = 1.0\times 10^{-7}$
- [x] **Fortran Subroutine:** Authoritative `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)
- [x] **Solver Controls:** Stage-14U Step 2 parameters (`4,10,9,20,10,4,0,10`, $\Delta t_{\min} = 1.0\times 10^{-9}$)
- [x] **Dual-Channel Notifications:** PBS Mail (`pr21vyci@mailserver.tu-freiberg.de`) + Telegram terminal traps active.

## 3. Discretization Telemetry
- **Base Elements:** 57,929 (56,339 quads [97.26%], 1,590 tris [2.74%])
- **Base Nodes:** 57,491
- **Total 3-Layer Elements:** 173,787
- **Seam Duplicate Node Pairs:** 97 pairs along $y = 0.5\,\text{mm}, x \in [0.0, 0.5]\,\text{mm}$
- **Crack Tip Node:** 1 singleton at $(0.5, 0.5)$
- **Corridor Elements (5% domain height):** 8,435 (14.56%)
- **Localization Classification:** `DIFFUSE_REFINEMENT` / `TOWARD_TARGET_LOCALIZATION`
