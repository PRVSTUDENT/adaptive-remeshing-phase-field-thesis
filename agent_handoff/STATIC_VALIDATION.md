# Static Validation - Molnar Paper-Matched Single-Notch v2

Classification: `static_validation_pass`

| Check | Result |
|---|---|
| `deck_exists` | `pass` |
| `deck_hash_matches_manifest` | `pass` |
| `user_subroutine_exists` | `pass` |
| `user_subroutine_hash_matches_manifest` | `pass` |
| `user_subroutine_n_elem_matches_physical` | `pass` |
| `preserved_source_not_modified_in_place` | `pass` |
| `generator_determinism_pass` | `pass` |
| `domain_is_1mm_by_1mm` | `pass` |
| `notch_length_is_0p5mm` | `pass` |
| `notch_tip_coordinates_represented` | `pass` |
| `opposing_notch_faces_not_tied` | `pass` |
| `no_physical_elements_bridge_notch_faces` | `pass` |
| `visualization_layer_count_matches_physical` | `pass` |
| `no_duplicate_element_ids` | `pass` |
| `node_ids_unique` | `pass` |
| `connectivity_references_valid_nodes` | `pass` |
| `positive_physical_element_area` | `pass` |
| `acceptable_aspect_ratio` | `pass` |
| `actual_local_h_near_target` | `pass` |
| `actual_global_h_near_target` | `pass` |
| `actual_graded_transition_present` | `pass` |
| `neighboring_size_ratio_within_limit` | `pass` |
| `refined_region_physically_present` | `pass` |
| `u1_declaration_complete` | `pass` |
| `u2_declaration_complete` | `pass` |
| `uel_property_blocks_complete` | `pass` |
| `property_ordering_matches_source` | `pass` |
| `non_overlapping_element_offsets` | `pass` |
| `expected_layer_counts` | `pass` |
| `top_and_bottom_sets_exist` | `pass` |
| `rigid_body_motion_removed` | `pass` |
| `horizontal_overconstraint_absent` | `pass` |
| `vertical_loading_consistent` | `pass` |
| `rf_extraction_set_valid` | `pass` |
| `loading_step1_arithmetic` | `pass` |
| `loading_step2_arithmetic` | `pass` |
| `loading_final_sum` | `pass` |
| `deck_final_displacement_matches_config` | `pass` |
| `required_outputs_exist` | `pass` |
| `contour_state_plan_exists` | `pass` |
| `source_hashes_recorded` | `pass` |
| `no_windows_paths` | `pass` |
| `no_hpc_paths` | `pass` |
| `candidate_v1_preserved` | `pass` |

## Metrics

- Physical elements: `33852`
- Layered elements: `101556`
- h/l: `0.13333333333333333`
- Maximum aspect ratio: `25`
- Notch face nodes per side: `46`

Static validation does not include Abaqus execution or PBS submission.
