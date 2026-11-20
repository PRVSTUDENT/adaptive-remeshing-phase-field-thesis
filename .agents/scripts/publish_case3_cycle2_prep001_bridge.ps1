param(
    [switch]$Publish = $false
)

. 'C:\Users\pruth\OpenClawPAD\ChatGPTBridge\Bridge-ResearchContract.ps1'
. 'C:\Users\pruth\OpenClawPAD\ChatGPTBridge\Invoke-ChatGPTBridge.ps1'

$prompt = @'
[BRIDGE_HANDOFF_ID=HND-METHOD-C-CASE3-CYCLE2-PREP-001]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "HND-METHOD-C-CASE3-CYCLE2-PREP-001",
  "predecessor_correlation_id": "HND-METHOD-C-CASE3-JOB2-DIAG-001",
  "task_id": "METHOD-C-CASE3-CYCLE2-REFINEMENT-PACKAGE",
  "title": "Method C Case 3: Cycle-2 Refinement Package Preparation from Job-2 Donor",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "E7B62C984B2468025F9F8184BFD54D55BE0512F3FCEB78A31BF590376D48138B",
  "artifact_commit": "901747c875ca989b8b645c7bef5ce89844371da5",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_CYCLE2_PREPARATION_REPORT.md",
  "checkpoint_artifact_sha256": "F76CED5A460F415A4FEEBF6319729CA368A2BBE604A7CDD0B179C0B15AC2D6BC",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_case3_cycle2_refinement_package",
    "numerical_uncertainty": "Can the Cycle-2 adapted receiver physical mesh (39,312 elements, 97.43% quads) track the crack forward from the measured tip (x=10.1529 mm) toward the central hole, achieve valid state and history transfer with zero healing and strict non-negativity H >= 0, and assemble the Job-3 production deck with diagnosed solver mitigations (dt_min=1.0e-14 and line search) with 0 new PBS jobs consumed?",
    "expected_numerical_result": "Cycle-2 refinement package prepared with verified FE quality gates (min det(J) > 0, quad frac >= 85%, AR <= 2.5), transfer receipt passing all non-negativity/non-healing gates, and Job-3 deck with dt_min=1e-14 and *CONTROLS, PARAMETERS=LINE SEARCH line 4; exactly 0 new PBS jobs consumed (cumulative 64 preserved); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "package_deliverables": {
    "donor_state_ingestion": {
      "source_odb": "/scratch9/pr21vyci/runs/mode1_290_method_c_case3_c1_job2/PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2.odb",
      "terminal_hold_u2_mm": 0.052451,
      "terminal_reaction_force_kn": 4.033296,
      "donor_max_damage_gp": 0.976822,
      "donor_max_damage_nodal": 0.947233,
      "donor_max_history_mpa": 1.107216,
      "spatial_crack_advance_mm": 0.1529,
      "spatial_crack_tip_x_mm": 10.1529
    },
    "adapted_physical_mesh": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_PHYS.inp",
      "sha256": "58466F66E1D9E41E73C5E5233DD748B5237193E225407320DB4288A8DB38081F",
      "size_bytes": 3090607,
      "total_physical_elements": 39312,
      "quad_elements": 38301,
      "tri_elements": 1011,
      "quad_fraction_pct": 97.43,
      "total_nodes": 39034,
      "refinement_corridor": "x in [8.5, 26.0] mm, y in [55.0, 77.0] mm, href=0.140 mm < l0/2=0.1425 mm",
      "quality_gates": {
        "gate_01_jacobian": "PASS (min det(J) = 5.720120e-4 > 0, 0 non-positive)",
        "gate_02_quad_fraction": "PASS (97.43% >= 85.0%)",
        "gate_03_aspect_ratio": "PASS (mean 1.263 <= 2.5)"
      }
    },
    "state_and_history_transfer": {
      "receipt_path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_TRANSFER_RECEIPT.json",
      "sha256": "3CECE05852FBFA7B5CBDA525156553F4F938B0B651ACC3E964F070CBC045BCFE",
      "size_bytes": 3817,
      "transfer_operator": "isoparametric_gp_transfer.py (convex_clamp)",
      "transferred_gp_entries": 154215,
      "non_negativity_verified": true,
      "min_gp_history_mpa": 9.837631e-12,
      "min_deck_svar_history_mpa": 0.0,
      "max_transferred_damage": 0.947233,
      "zero_healing_verified": true,
      "slit_flank_isolation_verified": true
    },
    "assembled_production_deck": {
      "deck_path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.inp",
      "sha256": "8DDE4D8B762C3019C90D4876A9558AACCB7EF4150CB37E5002E9E0305D68A890",
      "size_bytes": 17373879,
      "total_layered_elements": 117936,
      "phase_uel_elements": 39312,
      "disp_uel_elements": 39312,
      "companion_cpe_elements": 39312,
      "loading_schedule": {
        "step1_hold_u2_mm": 0.052451,
        "step1_amplitude": "CONST_HOLD",
        "step1_dt_min": 1.0e-14,
        "step2_propagation_u2_mm": 0.4125,
        "step2_dt_min": 1.0e-14,
        "line_search": "*CONTROLS, PARAMETERS=LINE SEARCH with data line 4 (both steps)"
      }
    }
  },
  "evidence_manifest": {
    "preparation_report": {
      "path": "docs/validation/METHOD_C_CASE3_CYCLE2_PREPARATION_REPORT.md",
      "sha256": "F76CED5A460F415A4FEEBF6319729CA368A2BBE604A7CDD0B179C0B15AC2D6BC",
      "size_bytes": 16402,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/901747c875ca989b8b645c7bef5ce89844371da5/docs/validation/METHOD_C_CASE3_CYCLE2_PREPARATION_REPORT.md"
    },
    "donor_state": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/donor_case3_cycle1_state.json",
      "sha256": "08A87E41202A2EA40F4E87D4450EF55EDADA7EFBEDEA25A8AFD689B8D1176955",
      "size_bytes": 7971298,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/901747c875ca989b8b645c7bef5ce89844371da5/models/pandey_kumar_mode1/290_method_c_case3/donor_case3_cycle1_state.json"
    },
    "physical_mesh": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_PHYS.inp",
      "sha256": "58466F66E1D9E41E73C5E5233DD748B5237193E225407320DB4288A8DB38081F",
      "size_bytes": 3090607,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/901747c875ca989b8b645c7bef5ce89844371da5/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_PHYS.inp"
    },
    "mesh_audit": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/method_c_case3_cycle2_mesh_audit.json",
      "sha256": "B7184CBF115A76D9B365F143EC0B1BE061A9B9CE98350F6041DBCE4549E7DBDC",
      "size_bytes": 1006,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/901747c875ca989b8b645c7bef5ce89844371da5/models/pandey_kumar_mode1/290_method_c_case3/method_c_case3_cycle2_mesh_audit.json"
    },
    "assembled_deck": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.inp",
      "sha256": "8DDE4D8B762C3019C90D4876A9558AACCB7EF4150CB37E5002E9E0305D68A890",
      "size_bytes": 17373879,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/901747c875ca989b8b645c7bef5ce89844371da5/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.inp"
    },
    "transfer_receipt": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_TRANSFER_RECEIPT.json",
      "sha256": "3CECE05852FBFA7B5CBDA525156553F4F938B0B651ACC3E964F070CBC045BCFE",
      "size_bytes": 3817,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/901747c875ca989b8b645c7bef5ce89844371da5/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_TRANSFER_RECEIPT.json"
    },
    "submit_pbs": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/submit_case3_cycle2_job3.pbs",
      "sha256": "C01C3E9445C4276EE6CD27C1C1E9EEE7B5C10C1265B1D532917B5EFB7BD66BA7",
      "size_bytes": 1268,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/901747c875ca989b8b645c7bef5ce89844371da5/models/pandey_kumar_mode1/290_method_c_case3/submit_case3_cycle2_job3.pbs"
    },
    "datacheck_sh": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/run_case3_cycle2_datacheck.sh",
      "sha256": "507450B4BF5E279556E89CAFFEC94CA20D62DEAB297F519B029F192EE0C8CDC5",
      "size_bytes": 511,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/901747c875ca989b8b645c7bef5ce89844371da5/models/pandey_kumar_mode1/290_method_c_case3/run_case3_cycle2_datacheck.sh"
    },
    "canonical_frozen_uel": {
      "path": "models/pandey_kumar_mode1/f42_mixed_uel.for",
      "sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
      "size_bytes": 29722,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/901747c875ca989b8b645c7bef5ce89844371da5/models/pandey_kumar_mode1/f42_mixed_uel.for"
    },
    "unit_tests": {
      "path": "tests/unit/test_method_c_case3_cycle2_package.py",
      "sha256": "87C2D91AAF67D55ABD9B7F78AB5A0540BE8362EE2811D3AD71B9D16D637F6640",
      "size_bytes": 7421,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/901747c875ca989b8b645c7bef5ce89844371da5/tests/unit/test_method_c_case3_cycle2_package.py"
    }
  },
  "budget_declaration": {
    "budget_plan": "Fix Option A: 5-Job Total Allocation (Cumulative PBS 62 to 67)",
    "jobs": [
      {"name": "M1_MC_C3_JOB1", "pbs_id": "1424711.mmaster02", "status": "CONSUMED", "cumulative_index": 63},
      {"name": "M1_MC_C3_JOB2", "pbs_id": "1424772.mmaster02", "status": "CONSUMED", "cumulative_index": 64},
      {"name": "M1_MC_C3_JOB3", "pbs_id": null, "status": "STAGED_READY", "cumulative_index": 65},
      {"name": "M1_MC_C3_JOB4", "pbs_id": null, "status": "PENDING", "cumulative_index": 66},
      {"name": "M1_MC_C3_JOB5", "pbs_id": null, "status": "PENDING", "cumulative_index": 67}
    ],
    "current_cumulative_submissions": 64,
    "new_pbs_jobs_consumed_this_package": 0
  }
}
'@

if ($Publish) {
    Write-Host "[Bridge] Executing guarded Invoke-ChatGPTBridge for HND-METHOD-C-CASE3-CYCLE2-PREP-001..." -ForegroundColor Cyan
    $res = Invoke-ChatGPTBridge -PromptText $prompt -HandoffId 'HND-METHOD-C-CASE3-CYCLE2-PREP-001' -TaskId 'METHOD-C-CASE3-CYCLE2-REFINEMENT-PACKAGE' -LaunchPad
    Write-Host "[Bridge] Handshake completed successfully. Response length: $($res.Length)" -ForegroundColor Green
    return $res
} else {
    Write-Host "[Bridge] DryRun mode: Validating policy without publishing..." -ForegroundColor Yellow
    $res = Invoke-ChatGPTBridge -PromptText $prompt -HandoffId 'HND-METHOD-C-CASE3-CYCLE2-PREP-001' -TaskId 'METHOD-C-CASE3-CYCLE2-REFINEMENT-PACKAGE' -DryRun
    Write-Host "[Bridge] DryRun policy validation: PASS" -ForegroundColor Green
    return $res
}
