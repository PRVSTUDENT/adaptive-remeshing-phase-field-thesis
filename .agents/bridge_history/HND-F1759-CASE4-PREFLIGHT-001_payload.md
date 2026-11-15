# Task F1759 Case 4 Five-Hole Plate Technical Preflight Qualification Payload

```json
{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "HND-F1759-CASE4-PREFLIGHT-001",
  "predecessor_correlation_id": "HND-F1758-CASE1-PREFLIGHT-001",
  "task_id": "F1759-CASE4-FIVE-HOLE-FRACTURE-QUALIFICATION-PREFLIGHT",
  "benchmark": "Pandey & Kumar (2025) Section 4.5: Tensile Failure of a Square Plate with Five Holes",
  "geometry": {
    "dimensions": "1.0 mm x 1.0 mm square plate",
    "thickness": "1.0 mm (plane strain)",
    "holes": [
      {"name": "h1", "center": [0.0, 0.5], "radius": 0.1, "type": "semi-circle left boundary"},
      {"name": "h2", "center": [0.35, 0.45], "radius": 0.1, "type": "interior circle"},
      {"name": "h3", "center": [0.6, 0.55], "radius": 0.05, "type": "interior circle"},
      {"name": "h4", "center": [0.75, 0.5], "radius": 0.075, "type": "interior circle"},
      {"name": "h5", "center": [1.0, 0.45], "radius": 0.075, "type": "semi-circle right boundary"}
    ]
  },
  "physical_discretization": {
    "mesh_inp": "models/pandey_kumar_mode1/217_f1725_physics_study/F1725_S2_COARSEN_ET315.inp",
    "mesh_sha256": "47196C9DC8017B0358E210CF39994F80949F032EEBA7FE3FA599863EC904323A",
    "num_physical_elements": 13017,
    "num_physical_nodes": 13230,
    "num_quads": 12696,
    "num_tris": 321,
    "quad_percentage": 97.53,
    "positive_jacobians": true,
    "aspect_ratio_mean": 1.261,
    "aspect_ratio_max": 2.595,
    "published_element_count": 12944,
    "parity_percentage": 0.563968
  },
  "production_deck_qualification": {
    "deck_inp": "models/pandey_kumar_mode1/235_f1759_case4_adapted_fracture/PK_F1759_CASE_4_PROD.inp",
    "deck_sha256": "7F2AEE34D592E5C31677C4144FB8EC57359490117B2B484560B4F13BADA31C29",
    "total_layered_elements": 39051,
    "layer_1_uel_phase": "Elements 1-13017 (U1 quads, U3 tris; active DOF 3)",
    "layer_2_uel_mech": "Elements 13018-26034 (U2 quads, U4 tris; active DOFs 1, 2)",
    "layer_3_companion": "Elements 26035-39051 (CPE4 quads, CPE3 tris; DUMMY_MAT with DEPVAR=16)",
    "sdv_output_coverage": "*ELEMENT OUTPUT, ELSET=All_elem: S, SDV with FREQUENCY=1 across both steps",
    "max_nset_line_wrapping": 16,
    "material_parameters": {
      "E_GPa": 210.0,
      "nu": 0.3,
      "Gc_kN_per_mm": 0.0027,
      "l0_mm": 0.0080,
      "k": 1.0e-7
    }
  },
  "frozen_uel_subroutine": {
    "source_file": "f42_mixed_uel.for",
    "sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
    "constitutive_split": "Volumetric-deviatoric Amor et al."
  },
  "cluster_datacheck_receipt": {
    "job_name": "PK_F1759_CASE_4_DC",
    "cluster_path": "/scratch9/pr21vyci/runs/mode1_pk_f1759_case4_preflight/",
    "cluster_modules": "gcc/11.4.0 intel/2024.2.0 abaqus/2023",
    "exit_code": 0,
    "receipt_text": "Abaqus JOB PK_F1759_CASE_4_DC COMPLETED. Datacheck Finished with Exit Code 0."
  },
  "unit_test_suite": {
    "test_file": "tests/unit/test_f1759_case4_preflight.py",
    "tests_passed": 5,
    "tests_failed": 0,
    "runtime_seconds": 0.37
  },
  "staged_pbs_script": {
    "script_file": "models/pandey_kumar_mode1/235_f1759_case4_adapted_fracture/submit_f1759_case4_fracture.pbs",
    "sha256": "1E1FAEEFC58137C16BCF93767CF2AD77C8206350849C3A55F83E17A1B50AD793",
    "queue": "entry_imfdfkmq",
    "resources": "1 CPU, 16 GB RAM, 8 h walltime (Serial 1-CPU mode)",
    "duplicate_guard": "PK_F1759_C4_FRAC.lck trap active",
    "notification_integration": "job_notifications.sh trap active (abe to pr21vyci@mailserver.tu-freiberg.de + Telegram)"
  },
  "governance_and_budget": {
    "task_pbs_allowance": 0,
    "task_pbs_consumed": 0,
    "cumulative_historical_submissions": 26,
    "requested_pbs_authorization": 1,
    "prospective_cumulative_submission": 27
  },
  "predeclared_acceptance_gates": {
    "Gate_G1_Elastic_Stiffness": "Initial stiffness K0 evaluated in elastic regime u <= 0.001 mm",
    "Gate_G2_Peak_Load": "Peak reaction force F_max compared quantitatively against Fig. 24a",
    "Gate_G3_Post_Peak_Softening": "Post-peak load drop > 50% demonstrating macroscopic crack propagation",
    "Gate_G4_Damage_Irreversibility": "Pointwise irreversibility min Delta d >= -1.0e-5 across all 39,051 elements",
    "Gate_G5_History_Monotonicity": "Strain history monotonicity min Delta H >= 0.0 MPa globally (100% PASS)",
    "Gate_G6_Thermodynamic_Energy_Balance": "Global energy balance Delta E / E_total <= 5.0%",
    "Gate_G7_Multi_Void_Crack_Path": "Observe progressive crack nucleation from h5/h4 and propagation into h3/h2 matching Fig. 23b"
  }
}
```
