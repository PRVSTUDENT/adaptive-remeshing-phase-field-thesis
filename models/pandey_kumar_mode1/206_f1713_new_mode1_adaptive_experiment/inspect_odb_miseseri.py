import sys
import os
from odbAccess import openOdb

odb_path = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\206_f1713_new_mode1_adaptive_experiment\PK_F1713_JOB1_COARSE.odb"
odb = openOdb(odb_path, readOnly=True)

step = odb.steps['Step-1']
frame = step.frames[-1]

print("Fields in last frame (time = %.4f):" % frame.frameValue)
for name, fld in frame.fieldOutputs.items():
    print("  Field: %-12s | Desc: %-40s | Type: %s" % (name, fld.description, fld.type))

miseseri = frame.fieldOutputs['MISESERI']
misesavg = frame.fieldOutputs['MISESAVG']

eri_vals = [v.data for v in miseseri.values]
avg_vals = [v.data for v in misesavg.values]

print("\nMISESERI data points: %d" % len(eri_vals))
print("  min = %.6e, max = %.6e, mean = %.6e" % (min(eri_vals), max(eri_vals), sum(eri_vals)/len(eri_vals)))

print("MISESAVG data points: %d" % len(avg_vals))
print("  min = %.6e, max = %.6e, mean = %.6e" % (min(avg_vals), max(avg_vals), sum(avg_vals)/len(avg_vals)))

# Calculate normalized error: eta_e = MISESERI / MISESAVG
eta_vals = [eri / avg if avg > 0 else 0.0 for eri, avg in zip(eri_vals, avg_vals)]
print("\nNormalized error ratio eta_e = MISESERI / MISESAVG (dimensionless):")
print("  min = %.6f (%.4f%%)" % (min(eta_vals), min(eta_vals)*100))
print("  max = %.6f (%.4f%%)" % (max(eta_vals), max(eta_vals)*100))
print("  mean = %.6f (%.4f%%)" % (sum(eta_vals)/len(eta_vals), sum(eta_vals)/len(eta_vals)*100))

# Fraction of elements exceeding the 1.85% errorTarget
error_target = 0.0185 # 1.85%
exceeding = sum(1 for e in eta_vals if e > error_target)
print("Elements with eta_e > errorTarget (1.85%%): %d / %d (%.2f%%)" % (
    exceeding, len(eta_vals), exceeding * 100.0 / len(eta_vals)
))

odb.close()
