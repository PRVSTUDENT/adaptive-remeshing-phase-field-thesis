# Session Log: Replay Package Final Integrity Audit (Task F164AUDIT)

- **Date**: 15 August 2026
- **Agent**: `gemini-antigravity`
- **Task ID**: `F164AUDIT-M2-PK10R1-STATECAPTURE-R1-FINAL-INTEGRITY1`
- **Starting Commit**: `b6e9b4ea5d4b3d012b2500a52b069a6a3423e37c`
- **Context**: Executed final integrity audit of replay package `M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1`.

## Diagnostic Findings & Audit Results

1. **User Subroutine Byte Identity Audit**:
   - `original_executed_UEL_SHA256`: **`e3b373253069f9b36085ee426568ce002a7f195a4d5356c6c6a5549c97767138`**
   - `candidate_UEL_SHA256_FINAL`: **`e3b373253069f9b36085ee426568ce002a7f195a4d5356c6c6a5549c97767138`**
   - `UEL_byte_identical`: **`true`**

2. **RP Displacement Semantics Audit**:
   - `ODB_frame_index`: `29`
   - `ODB_incrementNumber`: `29`
   - `ODB_frameValue`: `0.010143300518393517`
   - `ODB_RP_U1_raw`: `0.010143300518393517`
   - `DAT_RP_U1`: `0.000507165` mm
   - `BC_terminal_magnitude`: `0.050000` mm
   - `authoritative_RP_U1`: `0.0005071650259196759` mm
   - `ODB_U1_is_physical_displacement`: **`false`**
   - `RP_displacement_interpretation`: `In Abaqus ODB for this model configuration, the U1 field at RP Node 99999 represents normalized step time fraction t/Tstep rather than physical length; multiplying by prescribed total displacement magnitude 0.050000 mm yields exact physical displacement 0.000507165 mm.`

3. **Topology Node Set Union & Coverage Audit**:
   - `physical_UEL_unique_node_count`: `9850`
   - `physical_UEL_label_min`: `1`
   - `physical_UEL_label_max`: `9850`
   - `physical_UEL_labels_contiguous`: **`true`**
   - `RP_99999_in_physical_UEL_union`: **`false`**
   - `GENERATE_set_exactly_matches_physical_UEL_union`: **`true`**
   - `complete_U1_capture_expected`: **`true`**
   - `complete_U2_capture_expected`: **`true`**
   - `complete_DOF3_capture_expected`: **`true`**

4. **Candidate Package Hashes & Preflight Status**:
   - `candidate_INP_SHA256`: **`45fc96addaa63aa4155482c883e9dfc818d77f8f6ea50fc1008f28563ea6c225`**
   - `candidate_PBS_SHA256`: **`5f70d166ba5ce5aea2aab9b614c67472db44b5a6618e30038d44505d88e88830`**
   - `candidate_manifest_SHA256`: **`10056a8518defc9b3ce44e2e597a4ebd0c7db992b2d089d4b9e8a290c7f8f9ba`**
   - `datacheck_result`: **`PASS`**
   - `resources_match_1389684`: **`true`**
   - `replay_ready_for_authorization`: **`true`**

5. **Governance Invariants**:
   - `new_submission_authorized` = **`false`**.
   - `qsub_called` = **`false`**.
   - `qdel_called` = **`false`**.
   - `qmove_called` = **`false`**.
