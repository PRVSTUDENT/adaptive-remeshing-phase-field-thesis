from odbAccess import openOdb
import math

odb_path = "M1_CANDIDATE_DONOR_H0025.odb"
odb = openOdb(odb_path, readOnly=True)
step = odb.steps["Step-1"]
hr = step.historyRegions["Node PART-1-1.999999"]
u2_series = hr.historyOutputs["U2"].data
rf2_series = hr.historyOutputs["RF2"].data

print("Number of history points: %d" % len(u2_series))

# Target: u_top = 0.00254 mm
target_u = 0.00254
best_idx = 0
min_diff = 1e9

for i in range(len(u2_series)):
    t, u = u2_series[i]
    diff = abs(u - target_u)
    if diff < min_diff:
        min_diff = diff
        best_idx = i

t_best, u_best = u2_series[best_idx]
_, rf_best = rf2_series[best_idx]

print("TARGET u_top = %.6f mm" % target_u)
print("CLOSEST POINT: idx=%d, time=%.6f, u2=%.8f mm, RF2=%.8f N (diff=%.2e mm)" % (
    best_idx, t_best, u_best, rf_best, min_diff
))

# Interpolate exactly to target_u
if best_idx > 0 and best_idx < len(u2_series) - 1:
    i0 = best_idx if u2_series[best_idx][1] <= target_u else best_idx - 1
    i1 = i0 + 1
    t0, u0 = u2_series[i0]
    t1, u1 = u2_series[i1]
    rf0 = rf2_series[i0][1]
    rf1 = rf2_series[i1][1]
    frac = (target_u - u0) / (u1 - u0) if u1 != u0 else 0.0
    rf_interp = rf0 + frac * (rf1 - rf0)
    t_interp = t0 + frac * (t1 - t0)
    print("LINEAR INTERPOLATION AT u_top=%.6f mm: t=%.6f, RF2=%.8f N" % (target_u, t_interp, rf_interp))

# Print surrounding 5 points
print("Surrounding points:")
for i in range(max(0, best_idx-2), min(len(u2_series), best_idx+3)):
    print("  idx %3d: t=%.6f, u2=%.8f mm, RF2=%.8f N" % (i, u2_series[i][0], u2_series[i][1], rf2_series[i][1]))

odb.close()
