# dispatch_hnd_004.ps1
# Dispatches HND-METHOD-C-COMPLEX-004 for Problem 2 independent structured review.

param(
    [switch]$DryRun = $false
)

$commitSha = "24839a57e9c58994f18765252e0fce7c434cb03e"
$rulesSha = "B1117C2B72931DEF23CA2C626F8F3469395906CC2878555467B648306BA44190"

$requestObj = [ordered]@{
    "protocol" = "INDEPENDENT_STRUCTURED_REVIEW_V1"
    "correlation_id" = "HND-METHOD-C-COMPLEX-004"
    "predecessor_correlation_id" = "HND-METHOD-C-COMPLEX-003"
    "task_id" = "METHOD-C-COMPLEX-MODELS"
    "title" = "Method C Complex Problem 2 (Double Notch Symmetrical Crack Coalescence) Completion Verification"
    "goal_id" = "METHOD_C_COMPLEX_MODELS_V1"
    "canonical_rules_sha256" = $rulesSha
    "artifact_commit" = $commitSha
    "checkpoint_artifact" = "docs/validation/METHOD_C_COMPLEX_PROBLEM2_DOUBLE_NOTCH_REPORT.md"
    "checkpoint_artifact_sha256" = "9DF9293264449AF9E7E1EBF0BDDC23893FAD388B2745C82EF4A7F394838F29D8"
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
            "donor_sha256" = "069CA21EEFA9C35FA11291774F0782F1D4FA0D95204DAA00020E8C0740632A77"
            "donor_step" = "Step-2"
            "indicator_frame_range" = "Cycle 5 terminal increment"
            "held_out_later_solution" = "Cycle 6 forward step used strictly for post-transfer crack coalescence evaluation, never donor sizing"
            "uses_future_frames" = $false
            "remesh_time" = 1.0
            "maximum_indicator_time" = 1.0
        }
    }
    "closeout_statement" = [ordered]@{
        "problem_index" = 2
        "problem_name" = "DOUBLE_NOTCH_SYMMETRICAL_CRACK_COALESCENCE"
        "geometry" = "1.0x1.0 mm plate, left notch (0, 0.50) to (0.3536, 0.8536), right notch (1.0, 0.50) to (0.6464, 0.8536), initial tip separation 0.2929 mm at y=0.8536 mm"
        "loading" = "EDGE_PULL vertical uniaxial tension"
        "terminal_cycle" = 6
        "crack_status" = "SYMMETRICAL_CRACKS_COALESCED_ACROSS_LIGAMENT"
        "crack_1_tip_mm" = @(0.4939, 0.8499)
        "crack_2_tip_mm" = @(0.5061, 0.8499)
        "crack_1_arc_length_s1_mm" = 0.3023
        "crack_2_arc_length_s2_mm" = 0.3042
        "stopping_criterion" = "CONNECTED_DAMAGE_COALESCENCE"
        "coalescence_verified" = $true
        "peak_reaction_force_kn" = 0.6645
        "terminal_reaction_force_kn" = 0.000395
        "post_peak_load_drop_pct" = 99.94
        "transfer_gate_pass_rate" = "6/6 (100%)"
        "transfer_force_jumps" = "Cycle 1: -0.0020%, Cycle 2: -0.0154%, Cycle 3: -0.0673%, Cycle 4: -0.6832%, Cycle 5: -1.3723%, Cycle 6: -3.0649% (all <= 5.0%)"
        "hold_energy_continuity" = "Delta SDV17 <= +5.06%, Delta SDV18 >= -3.06%"
        "damage_nonhealing" = "Monotonic d_max: 0.2468 -> 0.4503 -> 0.6633 -> 0.9105 -> 0.9735 -> 0.9896 -> 0.9990 (PASS)"
        "mesh_scaling" = "16,847 -> 20,038 elements (<35,000 ceiling, quads >= 97.4%, min det(J) > 0, aspect ratio <= 4.49)"
        "bridged_corridor_architecture" = "Dual narrow bands (w=0.025 mm) during initiation; unified bridged ligament band at tip distance <= 0.25 mm (area fraction 1.48% < 3.0% of domain)"
        "unit_test_status" = "13/13 PASS (100%) in tests/unit/test_method_c_complex_double_notch.py"
        "master_goal_status" = "OPEN"
        "next_step" = "Awaiting independent structured review approval of Problem 2 before starting Problem 3 (Notch + Hole under Combined Tension + Shear)"
    }
    "evidence_manifest" = [ordered]@{
        "validation_report" = [ordered]@{
            "path" = "docs/validation/METHOD_C_COMPLEX_PROBLEM2_DOUBLE_NOTCH_REPORT.md"
            "sha256" = "9DF9293264449AF9E7E1EBF0BDDC23893FAD388B2745C82EF4A7F394838F29D8"
            "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/docs/validation/METHOD_C_COMPLEX_PROBLEM2_DOUBLE_NOTCH_REPORT.md"
        }
        "progression_grid" = [ordered]@{
            "path" = "models/complex_double_notch/campaign_results/fig_double_notch_progression_grid.png"
            "sha256" = "9C31967C85D5F03B43FF91DD71840AF93DB4245E8A020E5AD6B0A64E86BD8375"
            "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_double_notch/campaign_results/fig_double_notch_progression_grid.png"
        }
        "f_u_response" = [ordered]@{
            "path" = "models/complex_double_notch/campaign_results/fig_double_notch_f_u_response.png"
            "sha256" = "113CBC3FDEE547E5F32683ECC215E25EEA406ECB8C0760B9BAB3D3DDEEC1A340"
            "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_double_notch/campaign_results/fig_double_notch_f_u_response.png"
        }
        "synthesis_figure" = [ordered]@{
            "path" = "models/complex_double_notch/campaign_results/fig_double_notch_synthesis.png"
            "sha256" = "DF36B43B28B5D3886A2D3CC5D743E6DEE696AC5C8CF0A250D395A734136F0884"
            "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_double_notch/campaign_results/fig_double_notch_synthesis.png"
        }
        "progression_gif" = [ordered]@{
            "path" = "models/complex_double_notch/campaign_results/double_notch_progression.gif"
            "sha256" = "EBFB3CB6538D8983ED43E5D2A12EC327F400A570ADF7D897349F09FEB5823E76"
            "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_double_notch/campaign_results/double_notch_progression.gif"
        }
        "cycle_summaries" = @(
            [ordered]@{ "cycle" = 0; "path" = "models/complex_double_notch/campaign_results/PK_METHOD_C_DOUBLE_NOTCH_COARSE_JOB1_SUMMARY.json"; "sha256" = "05F1F467C0156F8E5582F719CAAF8DE8CEDF86B75BAB194A0C4D16A253F76FC4"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_double_notch/campaign_results/PK_METHOD_C_DOUBLE_NOTCH_COARSE_JOB1_SUMMARY.json" },
            [ordered]@{ "cycle" = 1; "path" = "models/complex_double_notch/campaign_results/PK_METHOD_C_DOUBLE_NOTCH_CYCLE1_SUMMARY.json"; "sha256" = "1307F5C0F0669D96E04BD5104AB0DFD3C8D62A3F0D81CB89251D60FA36EA74A1"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_double_notch/campaign_results/PK_METHOD_C_DOUBLE_NOTCH_CYCLE1_SUMMARY.json" },
            [ordered]@{ "cycle" = 2; "path" = "models/complex_double_notch/campaign_results/PK_METHOD_C_DOUBLE_NOTCH_CYCLE2_SUMMARY.json"; "sha256" = "95869931CE70B2EDD08C2FC5A1BF88A50DF3AEA5E82BF8B948A6BEE943758A8B"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_double_notch/campaign_results/PK_METHOD_C_DOUBLE_NOTCH_CYCLE2_SUMMARY.json" },
            [ordered]@{ "cycle" = 3; "path" = "models/complex_double_notch/campaign_results/PK_METHOD_C_DOUBLE_NOTCH_CYCLE3_SUMMARY.json"; "sha256" = "246DA5E38CD6C2E251D51D66A53029A24BB8B9AF9F9B381E086F7D98D679BA32"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_double_notch/campaign_results/PK_METHOD_C_DOUBLE_NOTCH_CYCLE3_SUMMARY.json" },
            [ordered]@{ "cycle" = 4; "path" = "models/complex_double_notch/campaign_results/PK_METHOD_C_DOUBLE_NOTCH_CYCLE4_SUMMARY.json"; "sha256" = "A201834BBC75E93F8429082D43ABA72A245FDEB3F6D9549B49D3FFA61BC01C91"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_double_notch/campaign_results/PK_METHOD_C_DOUBLE_NOTCH_CYCLE4_SUMMARY.json" },
            [ordered]@{ "cycle" = 5; "path" = "models/complex_double_notch/campaign_results/PK_METHOD_C_DOUBLE_NOTCH_CYCLE5_SUMMARY.json"; "sha256" = "C217AA3166099CA0528F09A9183B8F95EC559331DCD9ADAA371020480990F640"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_double_notch/campaign_results/PK_METHOD_C_DOUBLE_NOTCH_CYCLE5_SUMMARY.json" },
            [ordered]@{ "cycle" = 6; "path" = "models/complex_double_notch/campaign_results/PK_METHOD_C_DOUBLE_NOTCH_CYCLE6_SUMMARY.json"; "sha256" = "5E61BF279A39C8B802985E2796A28679C1CCD1445E36FA32A98819244C2D1D10"; "github_url" = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/complex_double_notch/campaign_results/PK_METHOD_C_DOUBLE_NOTCH_CYCLE6_SUMMARY.json" }
        )
    }
}

$jsonText = $requestObj | ConvertTo-Json -Depth 10

$promptText = @"
[BRIDGE_HANDOFF_ID=HND-METHOD-C-COMPLEX-004]
INDEPENDENT_STRUCTURED_REVIEW_V1

$jsonText
"@

Write-Host "[Dispatch] Prepared prompt for HND-METHOD-C-COMPLEX-004 ($($promptText.Length) chars)"

. .\.agents\scripts\Invoke-ChatGPTBridge.ps1

if ($DryRun) {
    Write-Host "[Dispatch] Running in DryRun mode..."
    Invoke-ChatGPTBridge -PromptText $promptText -HandoffId "HND-METHOD-C-COMPLEX-004" -DryRun
} else {
    Write-Host "[Dispatch] Dispatching via PAD ChatGPT Bridge..."
    Invoke-ChatGPTBridge -PromptText $promptText -HandoffId "HND-METHOD-C-COMPLEX-004"
}
