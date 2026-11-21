import json
import os

def main():
    json_path = "models/pandey_kumar_mode1/290_method_c_case3/job4_spatial_crack.json"
    if not os.path.exists(json_path):
        print("Waiting for job4_spatial_crack.json to be generated...")
        return

    with open(json_path, "r") as f:
        sc = json.load(f)

    obs = {
        "benchmark": "Pandey & Kumar (2025) Section 4.3 - Case 3 Cycle 3",
        "job": "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4",
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
                "dist_to_hole": fr["spatial_metrics"]["d_ge_0.95"]["dist_to_hole_mm"],
                "hole_penetrated": fr["spatial_metrics"]["d_ge_0.95"]["hole_penetrated"],
                "description": fr["description"]
            })

    out_path = "models/pandey_kumar_mode1/290_method_c_case3/job4_observables.json"
    with open(out_path, "w") as f:
        json.dump(obs, f, indent=2)
    print("Wrote job4_observables.json successfully.")

if __name__ == "__main__":
    main()
