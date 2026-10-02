"""
postprocess_external_work.py
Reconstructs external work from signed RP displacement U2 and reaction force RF2.
Explicitly handles duplicate Step 1 -> Step 2 step-boundary states.
Computes Left Riemann sum, Trapezoidal sum, Right Riemann sum, and integration sensitivity.
"""
import sys
import json

def reconstruct_external_work(u_rf_points):
    """
    u_rf_points: list of tuples (step_name, u2, rf2)
    """
    if len(u_rf_points) < 2:
        return {
            "status": "FAIL_INSUFFICIENT_POINTS",
            "w_trap": 0.0,
            "w_left": 0.0,
            "w_right": 0.0,
            "delta_w": 0.0,
            "points_count": len(u_rf_points)
        }

    # Deduplicate step boundary states: if point i has exact same u and rf as point i-1
    dedup = [u_rf_points[0]]
    for i in range(1, len(u_rf_points)):
        prev = dedup[-1]
        curr = u_rf_points[i]
        if abs(curr[1] - prev[1]) < 1e-15 and abs(curr[2] - prev[2]) < 1e-15:
            # Duplicate boundary state detected
            continue
        dedup.append(curr)

    w_trap = 0.0
    w_left = 0.0
    w_right = 0.0
    trajectory = []

    for i in range(1, len(dedup)):
        du = dedup[i][1] - dedup[i-1][1]
        f_left = dedup[i-1][2]
        f_right = dedup[i][2]
        f_avg = 0.5 * (f_left + f_right)

        inc_w_trap = f_avg * du
        inc_w_left = f_left * du
        inc_w_right = f_right * du

        w_trap += inc_w_trap
        w_left += inc_w_left
        w_right += inc_w_right

        trajectory.append({
            "step": dedup[i][0],
            "u": dedup[i][1],
            "rf": dedup[i][2],
            "du": du,
            "w_trap": w_trap,
            "w_left": w_left,
            "w_right": w_right
        })

    delta_w = abs(w_right - w_left) * 0.5

    return {
        "status": "SUCCESS",
        "raw_points_count": len(u_rf_points),
        "dedup_points_count": len(dedup),
        "w_trap_kNmm": w_trap,
        "w_left_kNmm": w_left,
        "w_right_kNmm": w_right,
        "delta_w_kNmm": delta_w,
        "delta_w_pct": (delta_w / w_trap * 100.0) if w_trap > 0 else 0.0,
        "trajectory": trajectory
    }

if __name__ == "__main__":
    print("External Work Reconstruction Module loaded successfully.")
