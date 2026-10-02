# Session Log: Guarded Replacement Submission of Diagnostic Source-State Extraction Job (Task F160SUB)

- **Date**: 15 August 2026
- **Agent**: `gemini-antigravity`
- **Task ID**: `F160SUB-M2-PK10R1-SOURCE-EXTRACTION-REPLACEMENT-SUBMIT1`
- **Starting Commit**: `b6e9b4ea5d4b3d012b2500a52b069a6a3423e37c`
- **Context**: Executed the user-authorized single replacement submission of diagnostic source-state extraction job `M2CORR_PK10R1_SOURCE_EXTRACTION_INC29` (`1389703.mmaster02`) replacing failed pre-solver job `1389702.mmaster02`.

## Execution & Submission Record

1. **User Authorization & Parameters**:
   - **Replacement Job ID**: **`1389703.mmaster02`** (replacing failed pre-solver job `1389702.mmaster02`).
   - **Source Reference**: Unchanged source job `1389684.mmaster02`, `ShearStep`, Increment 29 ($u_1 = 0.000507165\text{ mm}$).
   - **Technical Repair Applied**: `oldjob=../M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050` in `run_extraction.pbs`.
   - **Scientific Load Advance**: **0** (Immediate exit after state vector serialization).
   - **Resources**: 1 CPU, 4 GB RAM, 00:15:00 walltime, queue `entry_imfdfkmq`.

2. **Verified Replacement Hashes**:
   - `replacement_INP_SHA256`: **`5dcac0df2cd8bfab94a344039ba1172799fb77267d2c8c35d0faeca65c6a1561`**
   - `replacement_PBS_SHA256`: **`76e0d59c9e85c39b39843e90db02357131894f66712810ea60b2ced2628ae27e`**
   - `replacement_manifest_SHA256`: **`c3bf3b503478bbafb83d55fed746da709c12f1f9028c0fa8c9bd8821f4d73ea6`**
   - `replacement_UEL_SHA256`: **`5e26c6ecaf1f6b0df53944a6f7964bc442cbd6b4d05d2b9648f482a05fcd31eb`**

3. **Governance & Execution Invariants**:
   - `qsub_called` = **`true`** (Executed via guarded replacement submission wrapper).
   - `qdel_called` = **`false`**.
   - `qmove_called` = **`false`**.
   - `automatic_retry` = **`false`**.
   - `new_submission_authorized` = **`false`** (Single replacement authorization consumed).
