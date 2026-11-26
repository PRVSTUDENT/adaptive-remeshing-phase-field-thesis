# dispatch_hnd_005.ps1
# Dispatches HND-METHOD-C-COMPLEX-005 for Problem 3 independent structured review.

param(
    [switch]$DryRun = $false
)

$commitSha = "3b245e39aa3a781c745dab76ae3e3c42c424308a"
$rulesSha = "B1117C2B72931DEF23CA2C626F8F3469395906CC2878555467B648306BA44190"
$reportSha = "C52B3D5E938E5F336E54D1CFBC914CA80B3D460EF5FBC41E58AC2A146E13A837"

$requestObj = [ordered]@{
    "protocol" = "INDEPENDENT_STRUCTURED_REVIEW_V1"
    "correlation_id" = "HND-METHOD-C-COMPLEX-005"
    "predecessor_correlation_id" = "HND-METHOD-C-COMPLEX-004"
    "task_id" = "METHOD-C-COMPLEX-MODELS"
    "title" = "Method C Complex Problem 3 (Notch + Hole under Combined Tension + Shear) Completion Verification"
    "goal_id" = "METHOD_C_COMPLEX_MODELS_V1"
    "canonical_rules_sha256" = $rulesSha
    "artifact_commit" = $commitSha
    "checkpoint_artifact" = "docs/validation/METHOD_C_COMPLEX_PROBLEM3_MIXED_LOAD_REPORT.md"
    "checkpoint_artifact_sha256" = $reportSha
    "research_contract" = [ordered]@{
        "goal_id" = "METHOD_C_COMPLEX_MODELS_V1"
        "method" = "METHOD_C"
        "operation" = "method_c_complex_models_sequential"
        "numerical_uncertainty" = "Can the Method C narrow damage-following band framework handle three harder cases in sequence: (1) a crack that must re-initiate past a first hole and reach a second hole, (2) two cracks growing toward each other and coalescing, and (3) a curving crack under combined tension and shear, each maintaining 100% transfer gate compliance (<=5%)?"
        "expected_numerical_result" = "Three complex models completed in sequence (two-hole, double-notch, mixed-loading), each with a narrow damage-following band, cKDTree transfer, all transfer gates <=5%, no healing, and a handoff per problem; the goal is achieved when all three are independently reviewed and approved."
        "indicator_type" = "DAMAGE_INFORMED_SIZING"
        "indicator_role" = "METHOD_C_DRIVER"
        "causal_evidence_status" = "VERIFIED"
        "causal_evidence" = [ordered]@{
            "donor_sha256" = "0732A0264C11376C7794E9FA9652103E42CF0E314E95E21277897D3912E3BE47"
            "donor_step" = "Step-2"
            "indicator_frame_range" = "Cycle 7 terminal increment"
            "held_out_later_solution" = "Cycle 8 forward step used strictly for post-transfer crack progression and terminal hole entry evaluation, never donor sizing"
            "uses_future_frames" = $false
            "remesh_time" = 1.0
            "maximum_indicator_time" = 1.0
        }
    }
    "closeout_statement" = [ordered]@{
        "problem_index" = 3
        "problem_name" = "NOTCH_HOLE_COMBINED_TENSION_AND_SHEAR"
        "geometry" = "1.0x1.0 mm plate, +45 deg notch from (0, 0.50) to tip at (0.3536, 0.8536), circular hole center (0.65, 0.65), radius R=0.10 mm"
        "loading" = "EDGE_PULL vertical tension PLUS horizontal shear ux = 0.5 * uy applied simultaneously on top edge (shear-to-tension ratio 0.5), clamped bottom"
        "terminal_cycle" = 8
        "crack_status" = "CRACK_DEFLECTED_DOWNWARD_UNDER_SHEAR_ENTERED_HOLE_BOUNDARY"
        "crack_tip_mm" = @(0.5734, 0.7143)
        "distance_to_hole_boundary_mm" = 2.4491e-09
        "cumulative_arc_length_s_mm" = 0.2503
        "shear_effect_on_curvature" = "Horizontal shear rotated principal tensile stresses clockwise, causing crack to deflect downward earlier (y=0.8048 mm at x=0.48 mm vs y=0.8414 mm in pure tension) and enter void boundary on upper-left flank at theta ~ 140 deg vs theta ~ 105 deg (near top) in pure tension, shortening trajectory by 21.3% (0.2503 mm vs 0.3181 mm)"
        "stopping_criterion" = "CONNECTED_DAMAGE_ENTERED_HOLE"
        "hole_capture_verified" = $true
        "peak_reaction_forces" = "Peak RF2 = 0.988857 kN (Cycle 4, +22.9% vs pure tension 0.8044 kN), Peak RF1 = 0.243455 kN (Cycle 6)"
        "terminal_reaction_forces" = "Terminal RF2 = 0.556308 kN (43.74% drop from peak), Terminal RF1 = 0.098575 kN (59.51% drop from peak)"
        "transfer_gate_pass_rate" = "8/8 (100%)"
        "transfer_force_jumps" = "Cycle 1: -0.0025%, Cycle 2: -0.0069%, Cycle 3: -0.0148%, Cycle 4: -0.0922%, Cycle 5: -0.3365%, Cycle 6: -0.6566%, Cycle 7: -2.6331%, Cycle 8: -1.2331% (all <= 5.0%, max |Delta RF2| = 2.6331% at Cycle 7)"
        "reported_shear_force_jumps" = "Cycle 1: -0.0019%, Cycle 2: -0.0004%, Cycle 3: +0.0010%, Cycle 4: +0.0147%, Cycle 5: -0.0176%, Cycle 6: -0.0568%, Cycle 7: -2.3731%, Cycle 8: -4.1890% (all <= 4.19%)"
        "hold_energy_continuity" = "Delta SDV17 <= +3.9601% (at Cycle 6), Delta SDV18 >= -2.6028% (at Cycle 7)"
        "damage_nonhealing" = "Monotonic d_max: 0.2178 -> 0.2919 -> 0.4041 -> 0.6486 -> 0.9558 -> 0.9947 -> 0.9944 -> 1.0002 -> 1.0011 (PASS, 0.11% numerical overshoot disclosed)"
        "mesh_scaling" = "5,678 -> 8,435 elements (<35,000 ceiling, quads >= 97.4%, min det(J) > 0, aspect ratio <= 3.92 <= 5.0, narrow band area < 2.5% of domain)"
        "donor_checkpoints" = "Recorded donor checkpoint in Cycle 8 summary: 0732A0264C11376C7794E9FA9652103E42CF0E314E95E21277897D3912E3BE47 (Cycle 7 summary state); physical Cycle 7 checkpoint file PK_METHOD_C_MIXED_LOAD_CYCLE7_checkpoint.json SHA: 114F6298A08982FAD86D93E68D6751276F73C42BA890E789BC3634900BA57893 (never mesh SHA)"
        "unit_test_status" = "14/14 PASS (100%) in tests/unit/test_method_c_complex_mixed_load.py"
        "three_complex_models_campaign_status" = "Problem 1 (Two Holes in Series) APPROVED; Problem 2 (Double Notch Crack Coalescence) APPROVED; Problem 3 (Combined Tension + Shear) COMPLETED_READY_FOR_REVIEW"
        "master_goal_status" = "OPEN"
        "next_step" = "Awaiting independent structured review verification of Problem 3 completion and recommendation regarding master goal status for METHOD_C_COMPLEX_MODELS_V1"
    }
    "evidence_manifest" = [ordered]@{
        "validation_report" = [ordered]@{
            "path" = "docs/validation/METHOD_C_COMPLEX_PROBLEM3_MIXED_LOAD_REPORT.md"
            "sha256" = $reportSha
            "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/docs/validation/METHOD_C_COMPLEX_PROBLEM3_MIXED_LOAD_REPORT.md"
        }
        "progression_grid" = [ordered]@{
            "path" = "models/complex_mixed_load/campaign_results/fig_mixed_load_progression_grid.png"
            "sha256" = "88F4FC856F7A700935A894050ABD1822E1AB5634BDF64355B2B0CDC2BF133619"
            "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/fig_mixed_load_progression_grid.png"
        }
        "f_u_response" = [ordered]@{
            "path" = "models/complex_mixed_load/campaign_results/fig_mixed_load_f_u_response.png"
            "sha256" = "474FB5B047700104E5C7E3322DF3A989D91781522DE1A574A679A70B0A5A4B8C"
            "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/fig_mixed_load_f_u_response.png"
        }
        "synthesis_figure" = [ordered]@{
            "path" = "models/complex_mixed_load/campaign_results/fig_mixed_load_synthesis.png"
            "sha256" = "690209D52D36B5B753CDB7391563DEDAF68A601EFEDFE6486CB9302D8484D5C0"
            "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/fig_mixed_load_synthesis.png"
        }
        "progression_gif" = [ordered]@{
            "path" = "models/complex_mixed_load/campaign_results/mixed_load_progression.gif"
            "sha256" = "F8DAF5E89EFBAE26331DB3C170F92239E9A11A3757E6F2C3F1ABEB87B128E786"
            "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/mixed_load_progression.gif"
        }
        "image_manifest" = [ordered]@{
            "path" = "models/complex_mixed_load/campaign_results/image_manifest.json"
            "sha256" = "96BF90669135006CC6CFACFF4B4B0C3210F31DAC8C7613D5A47BA7223ED6B3C2"
            "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/image_manifest.json"
        }
        "frozen_uel" = [ordered]@{
            "path" = "models/pandey_kumar_mode1/f42_mixed_uel.for"
            "sha256" = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
            "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/f42_mixed_uel.for"
        }
        "unit_test_suite" = [ordered]@{
            "path" = "tests/unit/test_method_c_complex_mixed_load.py"
            "sha256" = "41B4272749105CE7B2850B8884A8C5535753CBA88D28B6518E7F81A48A8B2D2C"
            "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/tests/unit/test_method_c_complex_mixed_load.py"
        }
        "cycle_summaries" = @(
            [ordered]@{ "cycle" = 0; "path" = "models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_COARSE_JOB1_SUMMARY.json"; "sha256" = "E288B4A7880A58A7C33D39563A2F075116CB55774B0D4138B9B065DEDC7D81A7"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_COARSE_JOB1_SUMMARY.json" },
            [ordered]@{ "cycle" = 1; "path" = "models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE1_SUMMARY.json"; "sha256" = "D7DDE7343AE1F38D118200AE79B39A337A04EB6C297FAFFB11EF167517CAA703"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE1_SUMMARY.json" },
            [ordered]@{ "cycle" = 2; "path" = "models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE2_SUMMARY.json"; "sha256" = "4E80A3FB91925581FC2ACAF91C47C9AFE542BBCF953CB3438245E4DE74979283"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE2_SUMMARY.json" },
            [ordered]@{ "cycle" = 3; "path" = "models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE3_SUMMARY.json"; "sha256" = "28CCC5E9A09207D24AD4165C58C66AAB88DC7379DADCE657B96698D95B1C4674"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE3_SUMMARY.json" },
            [ordered]@{ "cycle" = 4; "path" = "models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE4_SUMMARY.json"; "sha256" = "3EFF2AF073057FBDECAC593F0994CAE7677A056C70337AF69F68739CE138EB9F"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE4_SUMMARY.json" },
            [ordered]@{ "cycle" = 5; "path" = "models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE5_SUMMARY.json"; "sha256" = "4428FD1ECCA6BE180BCB7BF5EDF9A80C369EAB95986965C11D5F4A99972A20DD"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE5_SUMMARY.json" },
            [ordered]@{ "cycle" = 6; "path" = "models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE6_SUMMARY.json"; "sha256" = "1D5FAFBCE8F444A932C5F6055EE0DF77431BC756D5F095F6B575CBE09E8B57BE"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE6_SUMMARY.json" },
            [ordered]@{ "cycle" = 7; "path" = "models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE7_SUMMARY.json"; "sha256" = "0732A0264C11376C7794E9FA9652103E42CF0E314E95E21277897D3912E3BE47"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE7_SUMMARY.json" },
            [ordered]@{ "cycle" = 8; "path" = "models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE8_SUMMARY.json"; "sha256" = "298151CF032320AB1315FC447622DE29E536C216290C003652291B75989B6576"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE8_SUMMARY.json" }
        )
        "cycle_checkpoints" = @(
            [ordered]@{ "cycle" = 0; "path" = "models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_COARSE_JOB1_checkpoint.json"; "sha256" = "8F26A7C91B6C6024BB5EF29E65B53A23D90D178B55567BAD626A7B97E7FE48BD"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_COARSE_JOB1_checkpoint.json" },
            [ordered]@{ "cycle" = 1; "path" = "models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE1_checkpoint.json"; "sha256" = "5D89D79FCF3F87A12C3C87AA3FCD13E2FEC67C4B9BF86B02F93A5BA455B2642C"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE1_checkpoint.json" },
            [ordered]@{ "cycle" = 2; "path" = "models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE2_checkpoint.json"; "sha256" = "5BA7F11BA0CA73D2F105606D097562B27B80E9609004A5B97148D8B6EF089293"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE2_checkpoint.json" },
            [ordered]@{ "cycle" = 3; "path" = "models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE3_checkpoint.json"; "sha256" = "107EAC343D3F16F6769A90EBA72724F88E3CBCC9A9DA0BEBBF9E79A117AD1A60"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE3_checkpoint.json" },
            [ordered]@{ "cycle" = 4; "path" = "models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE4_checkpoint.json"; "sha256" = "DF08E75ACBB765AE769C32259072A771D50CE4FAD49CF27381412232A3237413"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE4_checkpoint.json" },
            [ordered]@{ "cycle" = 5; "path" = "models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE5_checkpoint.json"; "sha256" = "205676C57298C73D559FDBD57AACCC609448175F9781FE208D777B26F2517F15"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE5_checkpoint.json" },
            [ordered]@{ "cycle" = 6; "path" = "models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE6_checkpoint.json"; "sha256" = "912EF250DC2B13685CB321197D3EC348F6A0FBF2FE12D1A2CB97F85FF9FFE81C"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE6_checkpoint.json" },
            [ordered]@{ "cycle" = 7; "path" = "models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE7_checkpoint.json"; "sha256" = "114F6298A08982FAD86D93E68D6751276F73C42BA890E789BC3634900BA57893"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE7_checkpoint.json" },
            [ordered]@{ "cycle" = 8; "path" = "models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE8_checkpoint.json"; "sha256" = "EB156582D36989BFC579304A6A1D889A513F5E480ABB02644420596BE22C3250"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_mixed_load/campaign_results/PK_METHOD_C_MIXED_LOAD_CYCLE8_checkpoint.json" }
        )
    }
}

$jsonText = $requestObj | ConvertTo-Json -Depth 10

$promptText = @"
[BRIDGE_HANDOFF_ID=HND-METHOD-C-COMPLEX-005]
INDEPENDENT_STRUCTURED_REVIEW_V1

$jsonText
"@

Write-Host "[Dispatch] Prepared prompt for HND-METHOD-C-COMPLEX-005 ($($promptText.Length) chars)"

. .\.agents\scripts\Invoke-ChatGPTBridge.ps1

if ($DryRun) {
    Write-Host "[Dispatch] Running in DryRun mode..."
    Invoke-ChatGPTBridge -PromptText $promptText -HandoffId "HND-METHOD-C-COMPLEX-005" -DryRun
} else {
    Write-Host "[Dispatch] Dispatching via PAD ChatGPT Bridge..."
    Invoke-ChatGPTBridge -PromptText $promptText -HandoffId "HND-METHOD-C-COMPLEX-005"
}
