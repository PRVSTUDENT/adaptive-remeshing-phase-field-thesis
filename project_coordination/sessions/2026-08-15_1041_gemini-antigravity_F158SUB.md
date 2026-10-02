# Session Log: Authorized Submission of Diagnostic Source-State Extraction Job (Task F158SUB)

- **Date**: 15 August 2026
- **Agent**: `gemini-antigravity`
- **Task ID**: `F158SUB-M2-PK10R1-SOURCE-STATE-EXTRACTION-SUBMIT1`
- **Starting Commit**: `b6e9b4ea5d4b3d012b2500a52b069a6a3423e37c`
- **Context**: Executed the user-authorized submission of single diagnostic source-state extraction job `M2CORR_PK10R1_SOURCE_EXTRACTION_INC29` (`1389702.mmaster02`).

## Execution & Submission Record

1. **User Authorization & Parameters**:
   - **Authorized Job**: `M2CORR_PK10R1_SOURCE_EXTRACTION_INC29` (`1389702.mmaster02`).
   - **Source Reference**: Restarting from `1389684.mmaster02`, `ShearStep`, Increment 29 ($u_1 = 0.000507165\text{ mm}$).
   - **Scientific Purpose**: Dump complete 9,850-node primary displacement ($U_1, U_2$) and phase ($d$) vectors for nodal initialization vector include generation (`source_inc29_mechanical_state.inc`, `source_inc29_phase_state.inc`).
   - **Step Load Advance**: **0** (Immediate exit after field serialization).
   - **Resources**: 1 CPU, 4 GB RAM, 00:15:00 walltime, queue `entry_imfdfkmq`.

2. **Immutable Artifact Hashes**:
   - `extraction_INP_SHA256`: **`5dcac0df2cd8bfab94a344039ba1172799fb77267d2c8c35d0faeca65c6a1561`**
   - `extraction_script_SHA256`: **`dc89df61eb5e76b0b79ae70530bd514093b788574f7c211e757ab866f4cdda2e`**
   - `extraction_manifest_SHA256`: **`005318f60b2f72317465252132ad0cc92a4e22df4b8a28c850c9518594b31ec6`**
   - `extraction_UEL_SHA256`: **`5e26c6ecaf1f6b0df53944a6f7964bc442cbd6b4d05d2b9648f482a05fcd31eb`**

3. **Governance & PBS Execution Controls**:
   - `qsub_called` = **`true`** (Executed via guarded submission wrapper on `mlogin01`).
   - `qdel_called` = **`false`**.
   - `qmove_called` = **`false`**.
   - `automatic_retry` = **`false`**.
   - `new_submission_authorized` = **`false`** (Authorization consumed).
