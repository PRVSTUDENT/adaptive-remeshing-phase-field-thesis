# Session Log: Guarded Replacement Submission of Diagnostic Source-State Extraction Job (Task F161SUB)

- **Date**: 15 August 2026
- **Agent**: `gemini-antigravity`
- **Task ID**: `F161SUB-M2-PK10R1-SOURCE-EXTRACTION-REPLACEMENT2-SUBMIT1`
- **Starting Commit**: `b6e9b4ea5d4b3d012b2500a52b069a6a3423e37c`
- **Context**: Executed the user-authorized single replacement submission of diagnostic source-state extraction job `M2CORR_PK10R1_SOURCE_EXTRACTION_INC29` (`1389705.mmaster02`) replacing failed pre-solver job `1389703.mmaster02` after properly escaping Powershell/Bash shell variables (`$PBS_O_WORKDIR`, `$HOME`, `$EXIT_CODE`, `$?`).

## Execution & Submission Record

1. **User Authorization & Parameters**:
   - **Replacement Job ID**: **`1389705.mmaster02`** (replacing failed pre-solver job `1389703.mmaster02`).
   - **Source Reference**: Unchanged source job `1389684.mmaster02`, `ShearStep`, Increment 29 ($u_1 = 0.000507165\text{ mm}$).
   - **Technical Repair Applied**: Escaped Powershell shell variables so `$PBS_O_WORKDIR` and `$HOME` are written literally into `run_extraction.pbs` on cluster.
   - **Scientific Load Advance**: **0** (Immediate exit after state vector serialization).
   - **Resources**: 1 CPU, 4 GB RAM, 00:15:00 walltime, queue `entry_imfdfkmq`.

2. **Verified Replacement Hashes**:
   - `replacement_INP_SHA256`: **`5dcac0df2cd8bfab94a344039ba1172799fb77267d2c8c35d0faeca65c6a1561`**
   - `replacement_PBS_SHA256`: **`2268b7b64c50caf7c3b2438f9a28e05b292f149137541fa570c0e0be03244aee`**
   - `replacement_manifest_SHA256`: **`fdbaf200a95676c79eb9e1dfa36a112e3cdb365f2bec58e84f927801840b8946`**
   - `replacement_UEL_SHA256`: **`5e26c6ecaf1f6b0df53944a6f7964bc442cbd6b4d05d2b9648f482a05fcd31eb`**

3. **Governance & Execution Invariants**:
   - `qsub_called` = **`true`** (Executed via guarded replacement submission wrapper).
   - `qdel_called` = **`false`**.
   - `qmove_called` = **`false`**.
   - `automatic_retry` = **`false`**.
   - `new_submission_authorized` = **`false`** (Single replacement authorization consumed).
