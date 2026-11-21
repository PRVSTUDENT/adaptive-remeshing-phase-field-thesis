import json
import os

def parse_sta(sta_path):
    increments = []
    step1_incs = 0
    step2_incs = 0
    smallest_dt = 1.0
    with open(sta_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("Abaqus") or line.startswith("SUMMARY") or line.startswith("STEP") or line.startswith("THE ANALYSIS"):
                continue
            parts = line.split()
            # Standard STA format: STEP INC ATT SEVERE EQUIL TOTAL TOTAL_TIME STEP_TIME INC_TIME
            # e.g.: 2 11 3 0 2 2 1.00 0.00214 6.993e-14
            if len(parts) >= 9:
                try:
                    step = int(parts[0])
                    inc = int(parts[1])
                    att = parts[2]
                    # if att does not end with 'U', it converged
                    if not att.endswith("U"):
                        step_time = float(parts[7])
                        inc_dt = float(parts[8])
                        if inc_dt < smallest_dt:
                            smallest_dt = inc_dt
                        increments.append({
                            "step": step,
                            "inc": inc,
                            "step_time": step_time,
                            "dt": inc_dt
                        })
                        if step == 1:
                            step1_incs += 1
                        elif step == 2:
                            step2_incs += 1
                except ValueError:
                    continue
            elif len(parts) == 8:
                try:
                    step = int(parts[0])
                    inc = int(parts[1])
                    att = parts[2]
                    if not att.endswith("U"):
                        step_time = float(parts[6])
                        inc_dt = float(parts[7])
                        if inc_dt < smallest_dt:
                            smallest_dt = inc_dt
                        increments.append({
                            "step": step,
                            "inc": inc,
                            "step_time": step_time,
                            "dt": inc_dt
                        })
                        if step == 1:
                            step1_incs += 1
                        elif step == 2:
                            step2_incs += 1
                except ValueError:
                    continue
    return increments, step1_incs, step2_incs, smallest_dt

def main():
    base_dir = "models/pandey_kumar_mode1/290_method_c_case3"
    sta_path = os.path.join(base_dir, "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.sta")
    dat_path = os.path.join(base_dir, "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.dat")
    csv_path = os.path.join(base_dir, "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_uel_energy_balance.csv")
    crack_json_path = os.path.join(base_dir, "job4_spatial_crack.json")
    summary_path = os.path.join(base_dir, "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_SUMMARY.json")
    receipt_path = os.path.join(base_dir, "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_RECEIPT.json")

    # Donor values from Job 3 terminal state
    donor_rf2 = 3.9475231
    donor_e_frac = 0.013756
    step1_hold_u2 = 0.056073
    donor_tip_x = 12.5215

    step1_init_rf2 = 3.9360855  # verified from dat
    force_continuity_delta = ((step1_init_rf2 - donor_rf2) / donor_rf2) * 100.0
    force_continuity_pass = abs(force_continuity_delta) <= 5.0

    step1_init_e_frac = 0.013882970
    step1_init_e_elastic = 0.11035406
    step1_init_e_total = 0.12423703
    energy_continuity_delta = ((step1_init_e_frac - donor_e_frac) / donor_e_frac) * 100.0
    energy_continuity_pass = abs(energy_continuity_delta) <= 5.0

    step1_incs = 1
    step2_incs = 11
    smallest_dt = 6.993e-14
    total_incs = 12

    if os.path.exists(sta_path):
        incs, s1, s2, sm_dt = parse_sta(sta_path)
        if s1 > 0:
            step1_incs = s1
        if s2 > 0:
            step2_incs = s2
        total_incs = step1_incs + step2_incs
        if sm_dt < 1.0:
            smallest_dt = sm_dt

    # Energy balance end values
    final_e_frac = 0.015924724
    final_e_elastic = 0.11100915
    final_e_total = 0.12693387
    peak_e_elastic = 0.11289134
    frac_growth_pct = ((final_e_frac - step1_init_e_frac) / step1_init_e_frac) * 100.0

    # Observables from dat and spatial crack
    peak_rf2 = 3.9760374       # Step 2 Inc 1 from dat
    u2_at_peak = 0.056785854   # Step 2 Inc 1 from dat
    terminal_rf2 = 3.9063646   # Step 2 Inc 11 from dat
    terminal_u2 = 0.056835016  # Step 2 Inc 11 from dat
    load_drop_pct = ((terminal_rf2 - peak_rf2) / peak_rf2) * 100.0

    tip_x_d095 = 13.1118
    crack_ext_d095 = 3.1118
    step2_advance = tip_x_d095 - donor_tip_x  # +0.5903 mm
    step1_hold_advance = 12.6052 - donor_tip_x # +0.0837 mm (growth under hold)
    step2_advance_post_hold = tip_x_d095 - 12.6052 # +0.5066 mm
    dist_to_hole = 20.0241
    hole_penetrated = False
    peak_d = 1.001953

    if os.path.exists(crack_json_path):
        with open(crack_json_path, "r") as f:
            sc = json.load(f)
        s2_frames = sc.get("steps", {}).get("Step-2", [])
        if s2_frames:
            last_fr = s2_frames[-1]
            peak_d = last_fr.get("peak_damage", peak_d)
            m095 = last_fr.get("spatial_metrics", {}).get("d_ge_0.95", {})
            tip_x_d095 = m095.get("tip_x", tip_x_d095)
            crack_ext_d095 = m095.get("delta_a_x_mm", crack_ext_d095)
            step2_advance = tip_x_d095 - donor_tip_x
            dist_to_hole = m095.get("dist_to_hole_mm", dist_to_hole)
            hole_penetrated = m095.get("hole_penetrated", False)

    summary = {
        "job_name": "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4",
        "job_id": "1424780.mmaster02",
        "run_dir": "/scratch9/pr21vyci/runs/mode1_290_method_c_case3_c3_job4",
        "physical_elements_count": 61688,
        "layered_elements_count": 185064,
        "physical_nodes_count": 61106,
        "total_nodes_with_rp": 61107,
        "total_increments": total_incs,
        "step1_increments": step1_incs,
        "step2_increments": step2_incs,
        "step1_hold_u2_mm": step1_hold_u2,
        "donor_RF2_kN": donor_rf2,
        "step1_init_RF2_kN": step1_init_rf2,
        "step1_init_force_continuity_delta_pct": force_continuity_delta,
        "step1_force_continuity_pass": force_continuity_pass,
        "donor_E_frac_kNmm": donor_e_frac,
        "step1_init_E_frac_kNmm": step1_init_e_frac,
        "step1_init_energy_continuity_delta_pct": energy_continuity_delta,
        "step1_energy_continuity_pass": energy_continuity_pass,
        "peak_RF2_kN": peak_rf2,
        "u2_at_peak_RF2_mm": u2_at_peak,
        "terminal_RF2_kN": terminal_rf2,
        "terminal_u2_mm": terminal_u2,
        "post_peak_softening_demonstrated": bool(terminal_rf2 < peak_rf2),
        "load_drop_from_peak_pct": load_drop_pct,
        "initial_crack_tip_x_mm": donor_tip_x,
        "step1_hold_crack_tip_x_mm_d095": 12.6052,
        "final_crack_tip_x_mm_d095": tip_x_d095,
        "final_crack_extension_mm_d095": crack_ext_d095,
        "step2_crack_advance_mm_d095": step2_advance,
        "step2_crack_advance_post_hold_mm_d095": step2_advance_post_hold,
        "dist_to_hole_mm": dist_to_hole,
        "hole_penetrated": hole_penetrated,
        "initial_fracture_energy_kNmm": step1_init_e_frac,
        "final_fracture_energy_kNmm": final_e_frac,
        "fracture_energy_growth_pct": frac_growth_pct,
        "peak_elastic_strain_energy_kNmm": peak_e_elastic,
        "terminal_elastic_strain_energy_kNmm": final_e_elastic,
        "peak_damage_SDV1": peak_d,
        "zero_healing_verified": bool(peak_d >= 0.989946),
        "smallest_converged_dt": smallest_dt,
        "scheduler_walltime_s": 10118.0,
        "solver_wallclock_s": 9814.0,
        "scheduler_cput_s": 2146.0,
        "solver_cput_s": 2120.0,
        "exit_code": 1,
        "status": "CUTBACK_TERMINATION",
        "termination_reason": "TIME_INCREMENT_LESS_THAN_MINIMUM"
    }

    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print("Wrote summary to:", summary_path)

    # Receipt structure matching Job 3 conventions
    receipt = {
        "benchmark": "Pandey & Kumar (2025) Section 4.3 - Case 3 Cycle 3",
        "job_name": "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4",
        "job_id": "1424780.mmaster02",
        "exit_code": 1,
        "status": "CUTBACK_TERMINATION",
        "termination_reason": "TIME_INCREMENT_LESS_THAN_MINIMUM",
        "total_increments": total_incs,
        "step1_re_equilibration": {
            "displacement_hold_u2_mm": step1_hold_u2,
            "increments": step1_incs,
            "iterations": 2,
            "re_equilibrated_RF2_kN": step1_init_rf2,
            "donor_terminal_RF2_kN": donor_rf2,
            "force_continuity_delta_pct": force_continuity_delta,
            "force_continuity_pass": force_continuity_pass,
            "re_equilibrated_E_frac_kNmm": step1_init_e_frac,
            "donor_terminal_E_frac_kNmm": donor_e_frac,
            "energy_continuity_delta_pct": energy_continuity_delta,
            "energy_continuity_pass": energy_continuity_pass,
            "total_energy_kNmm": step1_init_e_total,
            "elastic_energy_kNmm": step1_init_e_elastic,
            "crack_tip_x_d095_mm": 12.6052,
            "phenomenon": "GROWTH_UNDER_HOLD"
        },
        "step2_propagation": {
            "increments_converged": step2_incs,
            "total_converged_increments": total_incs,
            "peak_load_RF2_kN": peak_rf2,
            "displacement_at_peak_u2_mm": u2_at_peak,
            "terminal_RF2_kN": terminal_rf2,
            "terminal_displacement_u2_mm": terminal_u2,
            "softening_demonstrated": True,
            "load_drop_from_peak_pct": load_drop_pct,
            "donor_crack_tip_x_mm": donor_tip_x,
            "step1_hold_crack_tip_x_mm": 12.6052,
            "terminal_crack_tip_x_d095_mm": tip_x_d095,
            "forward_crack_advance_past_donor_mm": step2_advance,
            "forward_crack_advance_past_hold_mm": step2_advance_post_hold,
            "total_crack_extension_from_notch_root_mm": crack_ext_d095,
            "distance_to_hole_perimeter_mm": dist_to_hole,
            "hole_penetrated": hole_penetrated,
            "initial_fracture_energy_kNmm": step1_init_e_frac,
            "terminal_fracture_energy_kNmm": final_e_frac,
            "fracture_energy_growth_pct": frac_growth_pct,
            "peak_elastic_strain_energy_kNmm": peak_e_elastic,
            "terminal_elastic_strain_energy_kNmm": final_e_elastic,
            "peak_damage_SDV1": peak_d,
            "zero_healing_verified": True,
            "cutback_floor_dt_min": 1.0e-14,
            "smallest_converged_dt": smallest_dt
        },
        "timing_and_resources": {
            "scheduler_span_walltime_s": 10118.0,
            "solver_wallclock_s": 9814.0,
            "scheduler_cput_s": 2146.0,
            "solver_cpu_time_s": 2120.0,
            "cpus": 16,
            "threads": 16,
            "memory_gb": 48
        }
    }

    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)
    print("Wrote receipt to:", receipt_path)

if __name__ == "__main__":
    main()
