import json

def main():
    with open("models/pandey_kumar_mode1/290_method_c_case3/job3_spatial_crack.json", "r") as f:
        sc = json.load(f)

    obs = {
        "benchmark": "Pandey & Kumar (2025) Section 4.3 - Case 3 Cycle 2",
        "job": "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3",
        "steps": {}
    }

    for sname, frames in sc.get("steps", {}).items():
        obs["steps"][sname] = []
        for fr in frames:
            obs["steps"][sname].append({
                "frame": fr["frame_index"],
                "time": fr["step_time"],
                "u2_rp": fr["u2_rp_mm"],
                "rf2_rp": fr["rf2_rp_kn"],
                "max_d": fr["peak_damage"],
                "tip_x_d095": fr["spatial_metrics"]["d_ge_0.95"]["tip_x"],
                "delta_a_x_d095": fr["spatial_metrics"]["d_ge_0.95"]["delta_a_x_mm"],
                "description": fr["description"]
            })

    out_path = "models/pandey_kumar_mode1/290_method_c_case3/job3_observables.json"
    with open(out_path, "w") as f:
        json.dump(obs, f, indent=2)
    print("Wrote job3_observables.json successfully.")

if __name__ == "__main__":
    main()
