param(
    [switch]$Publish = $false
)

$sourceRoot = "D:\Master thesis\Adaptive remeshing\.agents\scripts"
if (-not (Test-Path -LiteralPath $sourceRoot)) { $sourceRoot = $PSScriptRoot }

. (Join-Path $sourceRoot "Bridge-ResearchContract.ps1")
. (Join-Path $sourceRoot "Invoke-ChatGPTBridge.ps1")

$prompt = @'
[BRIDGE_HANDOFF_ID=HND-METHOD-C-COMPLEX-002]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "HND-METHOD-C-COMPLEX-002",
  "predecessor_correlation_id": "HND-METHOD-C-COMPLEX-001",
  "task_id": "METHOD-C-COMPLEX-MODELS",
  "title": "Method C Complex Problem 1 (Inclined Notch + Two Holes in Series) Completion Verification",
  "goal_id": "METHOD_C_COMPLEX_MODELS_V1",
  "canonical_rules_sha256": "7642D247E6EDEF468454563F96711A470869D5CCBA48E1EDEF7BE06F1E7BB1EC",
  "artifact_commit": "94ebc3ab04e5dcaef6ef79707297ddb2f5670867",
  "checkpoint_artifact": "docs/validation/METHOD_C_COMPLEX_PROBLEM1_TWO_HOLE_REPORT.md",
  "checkpoint_artifact_sha256": "BAD1B40E2D94628C15CE00EE0CD12A1BB3B92009D31035029BFAECF49374FBD2",
  "research_contract": {
    "goal_id": "METHOD_C_MODE2_LPANEL_V1",
    "method": "METHOD_C",
    "operation": "method_c_complex_models_sequential",
    "numerical_uncertainty": "Can the Method C narrow damage-following band framework handle three harder cases in sequence: (1) a crack that must re-initiate past a first hole and reach a second hole, (2) two cracks growing toward each other and coalescing, and (3) a curving crack under combined tension and shear, each maintaining 100% transfer gate compliance (<=5%)?",
    "expected_numerical_result": "Three complex models completed in sequence (two-hole, double-notch, mixed-loading), each with a narrow damage-following band, cKDTree transfer, all transfer gates <=5%, no healing, and a handoff per problem; the goal is achieved when all three are independently reviewed and approved.",
    "indicator_type": "DAMAGE_INFORMED_SIZING",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_sha256": "ACF8EEE369E22D16C7990F8B6606A43DA0324B1283D66B8CE14FE01641C6B3F8",
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
    "crack_1_status": "ENTERED_HOLE1_AT_CYCLE4",
    "crack_1_tip_mm": [0.6250, 0.7468],
    "crack_2_status": "ENTERED_HOLE2_AT_CYCLE5",
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
    "unit_test_status": "11/11 PASS (100%) in tests/unit/test_method_c_complex_two_hole.py",
    "master_goal_status": "OPEN",
    "next_step": "Awaiting independent structured review approval of Problem 1 before starting Problem 2 (Double Notch)"
  },
  "evidence_manifest": {
    "validation_report": {
      "path": "docs/validation/METHOD_C_COMPLEX_PROBLEM1_TWO_HOLE_REPORT.md",
      "sha256": "BAD1B40E2D94628C15CE00EE0CD12A1BB3B92009D31035029BFAECF49374FBD2",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/94ebc3ab04e5dcaef6ef79707297ddb2f5670867/docs/validation/METHOD_C_COMPLEX_PROBLEM1_TWO_HOLE_REPORT.md"
    },
    "progression_grid": {
      "path": "models/complex_two_hole/campaign_results/fig_two_hole_progression_grid.png",
      "sha256": "F0C06EE05772D331C6C025FA227CB036373FDAD8F9144C6C3AA0DDE92EA0E8C8",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/94ebc3ab04e5dcaef6ef79707297ddb2f5670867/models/complex_two_hole/campaign_results/fig_two_hole_progression_grid.png"
    },
    "synthesis_figure": {
      "path": "models/complex_two_hole/campaign_results/fig_two_hole_synthesis.png",
      "sha256": "84AF3F5135C2647E5EEC9E4EEB525F1696B028210ED6798FA26DA3B96278D0D0",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/94ebc3ab04e5dcaef6ef79707297ddb2f5670867/models/complex_two_hole/campaign_results/fig_two_hole_synthesis.png"
    },
    "progression_gif": {
      "path": "models/complex_two_hole/campaign_results/two_hole_progression.gif",
      "sha256": "A5AC477373B64577930720A231A7F475C464B51D495877A23BA9BB76209C8CFE",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/94ebc3ab04e5dcaef6ef79707297ddb2f5670867/models/complex_two_hole/campaign_results/two_hole_progression.gif"
    },
    "image_manifest": {
      "path": "models/complex_two_hole/campaign_results/image_manifest.json",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/94ebc3ab04e5dcaef6ef79707297ddb2f5670867/models/complex_two_hole/campaign_results/image_manifest.json"
    },
    "coarse_job_summary": {
      "path": "models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_COARSE_JOB1_SUMMARY.json",
      "sha256": "DA871878006906391FD7958B64785DB035EB87E6F559296A4D1325FEC7A17AC3",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/b62077d52c24e0a2c7596f55a525f95d3f6001c8/models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_COARSE_JOB1_SUMMARY.json"
    },
    "cycle1_summary": {
      "path": "models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE1_SUMMARY.json",
      "sha256": "0CFAE44A2E058653F19F08D679D93ABBEB7FD5BC1F273E0AF876D9D08F267492",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/b62077d52c24e0a2c7596f55a525f95d3f6001c8/models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE1_SUMMARY.json"
    },
    "cycle2_summary": {
      "path": "models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE2_SUMMARY.json",
      "sha256": "AF038C5FD118207864AD9C75E91703E7933EDC511349FEB51774EF7A6CCB2CA7",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/b62077d52c24e0a2c7596f55a525f95d3f6001c8/models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE2_SUMMARY.json"
    },
    "cycle3_summary": {
      "path": "models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE3_SUMMARY.json",
      "sha256": "76E5D80AF034C1EE673450B4B7E510456BD3F1A2C0A04E98DD53C29F4CEC9700",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/b62077d52c24e0a2c7596f55a525f95d3f6001c8/models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE3_SUMMARY.json"
    },
    "cycle4_summary": {
      "path": "models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE4_SUMMARY.json",
      "sha256": "17ECA0B7158765D1C62911DDA1B7FFE8388299A0EE0566AD55BD62B8C65386A1",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/91648a962d12e157089c28d742d766ed7208415d/models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE4_SUMMARY.json"
    },
    "cycle5_summary": {
      "path": "models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE5_SUMMARY.json",
      "sha256": "9B2D1CA34D4B336B13E5A5BCA92C85B7B943F22B4347419B090B9FC895EA3266",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/58810ddeba9abbbe5441f9b010ee27688c09b540/models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE5_SUMMARY.json"
    },
    "canonical_frozen_uel": {
      "path": "models/pandey_kumar_mode1/f42_mixed_uel.for",
      "sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/94ebc3ab04e5dcaef6ef79707297ddb2f5670867/models/pandey_kumar_mode1/f42_mixed_uel.for"
    },
    "unit_tests": {
      "path": "tests/unit/test_method_c_complex_two_hole.py",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/94ebc3ab04e5dcaef6ef79707297ddb2f5670867/tests/unit/test_method_c_complex_two_hole.py"
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
    Write-Host "[Bridge] Publishing handoff HND-METHOD-C-COMPLEX-002..." -ForegroundColor Green
    $response = Invoke-ChatGPTBridge -PromptText $prompt -HandoffId "HND-METHOD-C-COMPLEX-002" -LaunchPad
    return $response
} else {
    Write-Host "[Bridge] Running dry-run validation for HND-METHOD-C-COMPLEX-002..." -ForegroundColor Cyan
    $assembled = Invoke-ChatGPTBridge -PromptText $prompt -HandoffId "HND-METHOD-C-COMPLEX-002" -DryRun
    Write-Host "[Bridge] Dry-run passed. Ready to publish with -Publish." -ForegroundColor Green
    return $assembled
}
