import json

def main():
    summary = {
        "job_name": "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3",
        "job_id": "1424778.mmaster02",
        "run_dir": "/scratch9/pr21vyci/runs/mode1_290_method_c_case3_c2_job3",
        "physical_elements_count": 39312,
        "layered_elements_count": 117936,
        "physical_nodes_count": 39034,
        "total_nodes_with_rp": 39035,
        "total_increments": 29,
        "step1_increments": 1,
        "step2_increments": 28,
        "step1_hold_u2_mm": 0.052451,
        "donor_RF2_kN": 4.0332960,
        "step1_init_RF2_kN": 4.0484387,
        "step1_init_force_continuity_delta_pct": 0.375442,
        "step1_force_continuity_pass": True,
        "donor_E_frac_kNmm": 0.0034562,
        "step1_init_E_frac_kNmm": 0.0034895,
        "step1_init_energy_continuity_delta_pct": 0.963486,
        "step1_energy_continuity_pass": True,
        "peak_RF2_kN": 4.101037,
        "u2_at_peak_RF2_mm": 0.053284,
        "terminal_RF2_kN": 3.947500,
        "terminal_u2_mm": 0.056073,
        "post_peak_softening_demonstrated": True,
        "load_drop_from_peak_pct": -3.743858,
        "initial_crack_tip_x_mm": 10.1529,
        "step1_crack_tip_x_mm_d095": 10.1566,
        "final_crack_tip_x_mm_d095": 12.5215,
        "final_crack_extension_mm_d095": 2.5215,
        "step2_crack_advance_mm_d095": 2.3649,
        "final_crack_tip_x_mm_d080": 12.7932,
        "final_crack_extension_mm_d080": 2.7932,
        "final_crack_tip_x_mm_d050": 13.0767,
        "final_crack_extension_mm_d050": 3.0767,
        "initial_fracture_energy_kNmm": 0.0034895,
        "final_fracture_energy_kNmm": 0.013756,
        "fracture_energy_growth_pct": 294.2112,
        "peak_elastic_strain_energy_kNmm": 0.113310,
        "terminal_elastic_strain_energy_kNmm": 0.110674,
        "peak_damage_SDV1": 0.999750,
        "zero_healing_verified": True,
        "inc11_milestone_surpassed": True,
        "smallest_converged_dt": 6.728e-14,
        "walltime_s": 4602.0,
        "cpu_time_s": 2918.0,
        "exit_code": 1,
        "status": "CUTBACK_TERMINATION",
        "termination_reason": "TIME_INCREMENT_LESS_THAN_MINIMUM"
    }

    out_path = "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_SUMMARY.json"
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print("Wrote PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_SUMMARY.json successfully.")

if __name__ == "__main__":
    main()
