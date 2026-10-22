from odbAccess import openOdb
import csv

odb_path = "M1_CANDIDATE_DONOR_H0025.odb"
odb = openOdb(odb_path, readOnly=True)
step = odb.steps["Step-1"]
hr = step.historyRegions["Node PART-1-1.999999"]
u2_series = hr.historyOutputs["U2"].data
rf2_series = hr.historyOutputs["RF2"].data

max_rf = -1e9
max_rf_u = 0.0
max_rf_idx = -1

points = []
for i in range(len(u2_series)):
    t = u2_series[i][0]
    u = u2_series[i][1]
    rf_kN = rf2_series[i][1]
    rf_N = rf_kN * 1000.0  # convert kN to N if needed or check magnitude
    points.append((i, t, u, rf_kN, rf_N))
    if rf_N > max_rf:
        max_rf = rf_N
        max_rf_u = u
        max_rf_idx = i

print("Total history points: %d" % len(points))
print("PEAK FORCE: idx=%d, u_top=%.6f mm, RF2_kN=%.6e, RF2_N=%.6f" % (max_rf_idx, max_rf_u, max_rf/1000.0, max_rf))

# Save full RF2 curve to CSV
with open("donor_h0025_rf_curve.csv", "w") as f:
    f.write("inc,step_time,u_top_mm,rf2_kN,rf2_N\n")
    for pt in points:
        f.write("%d,%.8e,%.8e,%.8e,%.8e\n" % pt)

print("Saved donor_h0025_rf_curve.csv")

# Print curve every 10 increments
print("Decimated RF curve:")
for i in range(0, len(points), 10):
    pt = points[i]
    print("  Inc %3d: t=%.4f, u=%.6f mm, RF2_N=%.4f (kN=%.6e)" % (pt[0], pt[1], pt[2], pt[4], pt[3]))

odb.close()
