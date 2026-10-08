import os
import sys
import glob

def parse_sta_file(sta_path):
    if not os.path.exists(sta_path):
        return None
    last_line = ""
    total_incs = 0
    with open(sta_path, "r") as f:
        for line in f:
            line_str = line.strip()
            if line_str and not line_str.startswith("STEP") and not line_str.startswith("SUMMARY"):
                parts = line_str.split()
                if len(parts) >= 8 and parts[0].isdigit() and parts[1].isdigit():
                    last_line = line_str
                    total_incs += 1
    if not last_line:
        return None
    p = last_line.split()
    return {
        "step": int(p[0]),
        "inc": int(p[1]),
        "att": int(p[2]),
        "severe_discon": int(p[3]),
        "eq_iters": int(p[4]),
        "total_iters": int(p[5]),
        "step_time": float(p[6]),
        "total_time": float(p[7]),
        "dt": float(p[8]) if len(p) > 8 else 0.0,
        "total_incs": total_incs
    }

def parse_dat_file(dat_path):
    if not os.path.exists(dat_path):
        return None
    rf_history = []
    d_max_seen = 0.0
    h_max_seen = 0.0
    
    with open(dat_path, "r") as f:
        for line in f:
            if "999999" in line:
                parts = line.split()
                if len(parts) == 3 and parts[0] == "999999":
                    try:
                        u1 = float(parts[1])
                        rf1 = float(parts[2])
                        rf_history.append((u1, rf1))
                    except ValueError:
                        pass
            if "SDV14" in line or "SDV1" in line:
                pass
    
    return {
        "rf_history": rf_history,
        "count": len(rf_history)
    }

def main():
    jobs = [
        {
            "name": "M2_J2_ADAPT_RETEST (22,530 FEs Adapted Mesh)",
            "job_id": "1411103.mmaster02",
            "dir": "/scratch9/pr21vyci/runs/mode2_j2_adapted_fracture_retest",
            "prefix": "Job-2_UEL"
        },
        {
            "name": "M2_J1_COARSE_RETEST (2,960 FEs Coarse Mesh)",
            "job_id": "1411104.mmaster02",
            "dir": "/scratch9/pr21vyci/runs/mode2_j1_coarse_retest",
            "prefix": "Job-1_UEL"
        }
    ]

    print("=" * 75)
    print("MODE-II GATE M2-4 CONCURRENT RETEST SOLVER TELEMETRY & PROGRESS")
    print("=" * 75)

    for j in jobs:
        print("\n--- %s [%s] ---" % (j["name"], j["job_id"]))
        sta_path = os.path.join(j["dir"], j["prefix"] + ".sta")
        dat_path = os.path.join(j["dir"], j["prefix"] + ".dat")
        msg_path = os.path.join(j["dir"], j["prefix"] + ".msg")
        lck_path = os.path.join(j["dir"], j["prefix"] + ".lck")

        is_running = os.path.exists(lck_path)
        print("  Status: %s (Lock: %s)" % ("RUNNING" if is_running else "TERMINATED / FINISHED", os.path.exists(lck_path)))
        
        sta_info = parse_sta_file(sta_path)
        if sta_info:
            print("  Step: %d | Inc: %d | Total Incs: %d" % (sta_info["step"], sta_info["inc"], sta_info["total_incs"]))
            print("  Step Time: %.6f | Total Time: %.6f | dt: %.6f" % (sta_info["step_time"], sta_info["total_time"], sta_info["dt"]))
            print("  Iterations: %d eq / %d total | Severe Discon: %d | Att: %d" % (sta_info["eq_iters"], sta_info["total_iters"], sta_info["severe_discon"], sta_info["att"]))
        else:
            print("  No .sta telemetry available yet.")

        dat_info = parse_dat_file(dat_path)
        if dat_info and dat_info["rf_history"]:
            rf_hist = dat_info["rf_history"]
            f_max = max(rf[1] for rf in rf_hist)
            u_fmax = [rf[0] for rf in rf_hist if rf[1] == f_max][0]
            curr_u, curr_rf = rf_hist[-1]
            print("  Reaction Force Telemetry (N = %d points):" % len(rf_hist))
            print("    Current: u_x = %.6f mm (%.2f um), RF = %.6f kN (%.2f N)" % (curr_u, curr_u * 1000.0, curr_rf, curr_rf * 1000.0))
            print("    Peak so far: F_max = %.6f kN (%.2f N) at u_x = %.6f mm (%.2f um)" % (f_max, f_max * 1000.0, u_fmax, u_fmax * 1000.0))
            if curr_u > 0.001:
                k0 = curr_rf / curr_u
                print("    Secant Stiffness: K = %.4f kN/mm" % k0)
        else:
            print("  No DAT RF points extracted yet.")

    print("\n" + "=" * 75)

if __name__ == "__main__":
    main()
