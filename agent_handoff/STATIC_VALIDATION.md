# Molnar v2 SDV15 Diagnostic Static Validation

Result: `diagnostic_static_validation_pass`
diagnostic_runnable: `true`

## Checks

- candidate_v2_preserved: `True`
- scientific_deck_keywords_identical: `True`
- nodes_and_connectivity_identical: `True`
- material_property_loading_order_identical: `True`
- deterministic_target_generation: `True`
- valid_u1_u2_cps4_mappings: `True`
- diagnostic_source_syntax_static_check: `pass`
- no_unbounded_logging: `True`
- no_absolute_windows_paths: `True`
- no_heavy_copy_to_home: `True`
- diagnostic_output_paths_resolve_to_scratch: `True`

## Notes

- Candidate v2 is preserved; all generated diagnostic files are in the separate diagnostic variant directory.
- The deck equivalence check removes Abaqus comments and compares the scientific keyword/data stream byte-for-byte.
- Logging is target-gated by `diagnostic_targets.inc` and writes to the Abaqus scratch working directory through `GETOUTDIR`.
- The PBS script keeps ODB and temporary compile/solver outputs on scratch and copies only lightweight evidence to the repository evidence directory.
