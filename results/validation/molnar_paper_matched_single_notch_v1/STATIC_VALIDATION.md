# Static Validation - Molnar Paper-Matched Single-Notch v1

Classification: `static_validation_fail`

| Check | Result |
|---|---|
| `deck_exists` | `pass` |
| `no_duplicate_element_ids` | `pass` |
| `node_ids_unique` | `pass` |
| `connectivity_references_valid_nodes` | `pass` |
| `layered_element_count` | `pass` |
| `element_offsets_present` | `pass` |
| `umat_material_blocks_present` | `pass` |
| `uel_property_blocks_present` | `fail` |
| `notch_geometry_represented` | `fail` |
| `boundary_conditions_present` | `pass` |
| `inplane_rigid_body_constraint_present` | `fail` |
| `rf_node_set_present` | `pass` |
| `sdv_requested` | `pass` |
| `loading_increments_present` | `pass` |
| `config_coarse_increment_consistent` | `fail` |
| `config_fine_increment_consistent` | `pass` |
| `deck_step1_increment_matches_config` | `fail` |
| `deck_step2_increment_matches_config` | `pass` |
| `deck_final_displacement_matches_config` | `pass` |
| `local_h_over_l_declared` | `pass` |
| `paper_count_check` | `pass` |
| `no_windows_paths` | `pass` |
| `no_hpc_paths` | `pass` |

Notes:

- Static validation does not authorize Abaqus execution.
- Failure means the generated deck or configuration must be revised before any run request.
- Current structural blockers include missing notch representation, missing UEL property blocks, and the inconsistent coarse loading increment representation.
