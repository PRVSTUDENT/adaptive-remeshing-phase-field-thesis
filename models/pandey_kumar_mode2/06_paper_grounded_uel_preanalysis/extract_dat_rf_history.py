import os
import sys

dat_path = os.path.join("models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "Job-2_UEL.dat")
print("DAT Path: %s (Exists: %s)" % (dat_path, os.path.exists(dat_path)))

rf_history = []
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

print("Total extracted points: %d" % len(rf_history))
if rf_history:
    f_max = max(rf[1] for rf in rf_history)
    u_fmax = [rf[0] for rf in rf_history if rf[1] == f_max][0]
    final_u, final_rf = rf_history[-1]
    drop = (f_max - final_rf) / f_max * 100.0

    print("=" * 65)
    print("MODE-II ADAPTED FRACTURE (JOB-2_UEL) REACTION FORCE SUMMARY:")
    print("  Peak Force F_max = %.6f kN (%.2f N)" % (f_max, f_max * 1000.0))
    print("  Displacement at Peak u(F_max) = %.6f mm (%.2f um)" % (u_fmax, u_fmax * 1000.0))
    print("  Final Displacement u_x = %.6f mm (%.2f um)" % (final_u, final_u * 1000.0))
    print("  Final Reaction Force RF = %.6f kN (%.2f N)" % (final_rf, final_rf * 1000.0))
    print("  Softening Load Drop = %.2f%%" % drop)
    print("=" * 65)

    csv_out = os.path.join("models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "mode2_j2_rf_history.csv")
    with open(csv_out, "w") as out:
        out.write("step_name,frame_time,ux_mm,rf1_kN\n")
        for u, rf in rf_history:
            step_str = "Step-1" if u <= 0.010000000001 else "Step-2"
            out.write("%s,0.0,%.8e,%.8e\n" % (step_str, u, rf))
    print("Saved -> %s" % csv_out)
