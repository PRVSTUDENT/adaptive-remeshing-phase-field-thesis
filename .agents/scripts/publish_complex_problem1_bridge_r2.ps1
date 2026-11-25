param(
    [switch]$Publish = $false
)

$sourceRoot = "D:\Master thesis\Adaptive remeshing\.agents\scripts"
if (-not (Test-Path -LiteralPath $sourceRoot)) { $sourceRoot = $PSScriptRoot }

. (Join-Path $sourceRoot "Bridge-ResearchContract.ps1")
. (Join-Path $sourceRoot "Invoke-ChatGPTBridge.ps1")

$prompt = @'
[BRIDGE_HANDOFF_ID=HND-METHOD-C-COMPLEX-003]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "HND-METHOD-C-COMPLEX-003",
  "predecessor_correlation_id": "HND-METHOD-C-COMPLEX-002",
  "task_id": "METHOD-C-COMPLEX-MODELS",
  "title": "Method C Complex Problem 1 (Inclined Notch + Two Holes in Series) Completion Verification Re-Submission R2",
  "goal_id": "METHOD_C_COMPLEX_MODELS_V1",
  "canonical_rules_sha256": "B1117C2B72931DEF23CA2C626F8F3469395906CC2878555467B648306BA44190",
  "artifact_commit": "3381cbdb861d940a7a6e57f513198cb8a6556201",
  "checkpoint_artifact": "docs/validation/METHOD_C_COMPLEX_PROBLEM1_TWO_HOLE_REPORT.md",
  "checkpoint_artifact_sha256": "B49C26F75D10034177D2DBD572C41BD09D9F568F56EFB4D6F9AEE220E6498C45",
  "research_contract": {
    "goal_id": "METHOD_C_COMPLEX_MODELS_V1",
    "method": "METHOD_C",
    "operation": "method_c_complex_models_sequential",
    "numerical_uncertainty": "Can the Method C narrow damage-following band framework handle three harder cases in sequence: (1) a crack that must re-initiate past a first hole and reach a second hole, (2) two cracks growing toward each other and coalescing, and (3) a curving crack under combined tension and shear, each maintaining 100% transfer gate compliance (<=5%)?",
    "expected_numerical_result": "Three complex models completed in sequence (two-hole, double-notch, mixed-loading), each with a narrow damage-following band, cKDTree transfer, all transfer gates <=5%, no healing, and a handoff per problem; the goal is achieved when all three are independently reviewed and approved.",
    "indicator_type": "DAMAGE_INFORMED_SIZING",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_sha256": "F8E5C0EC90DC655EE373D694D24954AEF6888C082B3297C067FF8CC35B1ADE52",
      "donor_step": "Step-2",
      "indicator_frame_range": "Cycle 4 terminal increment",
      "held_out_later_solution": "Cycle 5 forward step used strictly for post-transfer crack advance evaluation, never donor sizing",
      "uses_future_frames": false,
      "remesh_time": 1.0,
      "maximum_indicator_time": 1.0
    }
  },
  "closeout_statement": {
    "problem_index": 1,
    "problem_name": "INCLINED_NOTCH_TWO_HOLES_IN_SERIES",
    "geometry": "1.0x1.0 mm plate, +45 deg notch tip (0.3536, 0.8536), Hole 1 (0.65, 0.65) R=0.10 mm, Hole 2 (0.87, 0.62) R=0.06 mm, inter-hole ligament = 0.0620 mm",
    "loading": "EDGE_PULL vertical uniaxial tension",
    "terminal_cycle": 5,
    "crack_1_status": "PROPAGATED_HORIZONTALLY_AND_ARRESTED_AT_X_0.50_MISSING_HOLE1",
    "crack_1_tip_mm": [0.4987, 0.8410],
    "crack_2_status": "NUCLEATED_AT_HOLE1_AND_ENTERED_HOLE2_AT_CYCLE5",
    "crack_2_tip_mm": [0.8103, 0.6138],
    "distance_to_hole2_center_mm": 0.0600,
    "hole2_radius_mm": 0.0600,
    "stopping_criterion": "CONNECTED_DAMAGE_ENTERED_HOLE2",
    "peak_reaction_force_kn": 0.7178,
    "terminal_reaction_force_kn": 0.2664,
    "post_peak_load_drop_pct": 62.89,
    "transfer_gate_pass_rate": "5/5 (100%)",
    "transfer_force_jumps": "Cycle 1: -0.0088%, Cycle 2: -0.0296%, Cycle 3: -0.2285%, Cycle 4: -0.3224%, Cycle 5: -4.0788% (all <= 5.0%)",
    "hold_energy_continuity": "Delta SDV17 <= +6.26%, Delta SDV18 >= -4.08%",
    "damage_nonhealing": "Monotonic d_max: 0.2854 -> 0.4154 -> 0.7359 -> 0.9708 -> 0.9877 -> 0.9962 (PASS)",
    "mesh_scaling": "6,348 -> 10,182 elements (<35,000 ceiling, quads >= 97.2%, min det(J) > 0, aspect ratio <= 4.88)",
    "refined_domain_area_pct": "< 2.5%",
    "unit_test_status": "12/12 PASS (100%) in tests/unit/test_method_c_complex_two_hole.py",
    "master_goal_status": "OPEN",
    "next_step": "Awaiting independent structured review approval of Problem 1 before starting Problem 2 (Double Notch)"
  },
  "evidence_manifest": {
    "validation_report": {
      "path": "docs/validation/METHOD_C_COMPLEX_PROBLEM1_TWO_HOLE_REPORT.md",
      "sha256": "B49C26F75D10034177D2DBD572C41BD09D9F568F56EFB4D6F9AEE220E6498C45",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/3381cbdb861d940a7a6e57f513198cb8a6556201/docs/validation/METHOD_C_COMPLEX_PROBLEM1_TWO_HOLE_REPORT.md"
    },
    "progression_grid": {
      "path": "models/complex_two_hole/campaign_results/fig_two_hole_progression_grid.png",
      "sha256": "F0C06EE05772D331C6C025FA227CB036373FDAD8F9144C6C3AA0DDE92EA0E8C8",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/3381cbdb861d940a7a6e57f513198cb8a6556201/models/complex_two_hole/campaign_results/fig_two_hole_progression_grid.png"
    },
    "synthesis_figure": {
      "path": "models/complex_two_hole/campaign_results/fig_two_hole_synthesis.png",
      "sha256": "84AF3F5135C2647E5EEC9E4EEB525F1696B028210ED6798FA26DA3B96278D0D0",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/3381cbdb861d940a7a6e57f513198cb8a6556201/models/complex_two_hole/campaign_results/fig_two_hole_synthesis.png"
    },
    "progression_gif": {
      "path": "models/complex_two_hole/campaign_results/two_hole_progression.gif",
      "sha256": "A5AC477373B64577930720A231A7F475C464B51D495877A23BA9BB76209C8CFE",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/3381cbdb861d940a7a6e57f513198cb8a6556201/models/complex_two_hole/campaign_results/two_hole_progression.gif"
    },
    "image_manifest": {
      "path": "models/complex_two_hole/campaign_results/image_manifest.json",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/3381cbdb861d940a7a6e57f513198cb8a6556201/models/complex_two_hole/campaign_results/image_manifest.json"
    },
    "cycle4_checkpoint": {
      "path": "models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE4_checkpoint.json",
      "sha256": "F8E5C0EC90DC655EE373D694D24954AEF6888C082B3297C067FF8CC35B1ADE52",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/3381cbdb861d940a7a6e57f513198cb8a6556201/models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE4_checkpoint.json"
    },
    "coarse_job_summary": {
      "path": "models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_COARSE_JOB1_SUMMARY.json",
      "sha256": "280B0B56E6A98DF01792FA43C1837AFC3289F66F7BB16620A71807B1E0F0572B",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/3381cbdb861d940a7a6e57f513198cb8a6556201/models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_COARSE_JOB1_SUMMARY.json"
    },
    "cycle1_summary": {
      "path": "models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE1_SUMMARY.json",
      "sha256": "1986490CAB6CBDA5DA22799F03ACB650883B7E48907B4165A171BE8B4E89025B",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/3381cbdb861d940a7a6e57f513198cb8a6556201/models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE1_SUMMARY.json"
    },
    "cycle2_summary": {
      "path": "models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE2_SUMMARY.json",
      "sha256": "1C8CDD1EFF9809E39FF721DCA72BD6EE1286761F930D72F7BAA11F30CEACE660",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/3381cbdb861d940a7a6e57f513198cb8a6556201/models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE2_SUMMARY.json"
    },
    "cycle3_summary": {
      "path": "models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE3_SUMMARY.json",
      "sha256": "6A630950E0459C31227194B6E9A95C2BDAAD467051AF7C683F2418806C68E7BD",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/3381cbdb861d940a7a6e57f513198cb8a6556201/models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE3_SUMMARY.json"
    },
    "cycle4_summary": {
      "path": "models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE4_SUMMARY.json",
      "sha256": "EE123F8B17F8006CD46CDCD7FD72148646E42E7ACA2B3728531DD1E9C857D0CD",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/3381cbdb861d940a7a6e57f513198cb8a6556201/models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE4_SUMMARY.json"
    },
    "cycle5_summary": {
      "path": "models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE5_SUMMARY.json",
      "sha256": "B9CE2B1725162F9902BF04E6F00D3D5806065A9CBF5C6E32325C28DFCFB945E4",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/3381cbdb861d940a7a6e57f513198cb8a6556201/models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE5_SUMMARY.json"
    },
    "canonical_frozen_uel": {
      "path": "models/pandey_kumar_mode1/f42_mixed_uel.for",
      "sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/3381cbdb861d940a7a6e57f513198cb8a6556201/models/pandey_kumar_mode1/f42_mixed_uel.for"
    },
    "unit_tests": {
      "path": "tests/unit/test_method_c_complex_two_hole.py",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/3381cbdb861d940a7a6e57f513198cb8a6556201/tests/unit/test_method_c_complex_two_hole.py"
    }
  },
  "budget_declaration": {
    "execution_mode": "LOCAL_WORKSTATION_ONLY",
    "pbs_jobs_consumed": 0,
    "cumulative_pbs_jobs": 73,
    "frozen_uel_preserved": true,
    "hpc_job_1424916_untouched": true
  }
}
'@

if ($Publish) {
    Write-Output "Publishing HND-METHOD-C-COMPLEX-003 to ChatGPT bridge..."
    $result = Invoke-ChatGPTBridge -PromptText $prompt -HandoffId "HND-METHOD-C-COMPLEX-003" -TaskId "METHOD-C-COMPLEX-MODELS" -LaunchPad
    Write-Output "Bridge publication complete."
    $result
} else {
    Write-Output "Validating prompt against canonical bridge policy..."
    $result = Invoke-ChatGPTBridge -PromptText $prompt -HandoffId "HND-METHOD-C-COMPLEX-003" -TaskId "METHOD-C-COMPLEX-MODELS" -DryRun
    Write-Output "Validation PASS. Ready to publish with -Publish."
}
