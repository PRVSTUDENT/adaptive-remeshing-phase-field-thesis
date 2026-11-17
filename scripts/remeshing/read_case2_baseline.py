# -*- coding: utf-8 -*-
import os, sys, odbAccess

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
odb_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "PK_HOLE_COARSE_JOB1.odb")

odb = odbAccess.openOdb(odb_path, readOnly=True)
print("Steps:", list(odb.steps.keys()))

for sname in odb.steps.keys():
    step = odb.steps[sname]
    print("Step %s: %d frames" % (sname, len(step.frames)))
    f_first = step.frames[0]
    f_last = step.frames[-1]
    print("  First frame value: %.6f, desc: %s" % (f_first.frameValue, f_first.description))
    print("  Last frame value:  %.6f, desc: %s" % (f_last.frameValue, f_last.description))

# Check RP reaction force and displacement history
print("\nHistory regions:")
for hname, hreg in odb.steps['Step-2'].historyRegions.items():
    print("  HistoryRegion:", hname)
    for p in hreg.historyOutputs.keys():
        print("    Point:", p)

# Extract RF2 and U2 if present in history
rf_history = []
u_history = []
if 'Node PART-1-1.999999' in odb.steps['Step-2'].historyRegions:
    hr = odb.steps['Step-2'].historyRegions['Node PART-1-1.999999']
    if 'RF2' in hr.historyOutputs and 'U2' in hr.historyOutputs:
        rf_data = hr.historyOutputs['RF2'].data
        u_data = hr.historyOutputs['U2'].data
        print("Found history output for N_RP: %d points" % len(rf_data))

# Also extract from field outputs across frames
print("\nExtracting FieldOutputs from Step-1 and Step-2 for N_RP (Node 999999):")
peak_rf2 = 0.0
peak_u2 = 0.0
peak_frame = None

for sname in ['Step-1', 'Step-2']:
    step = odb.steps[sname]
    for i, f in enumerate(step.frames):
        if 'RF' in f.fieldOutputs and 'U' in f.fieldOutputs:
            rf_fo = f.fieldOutputs['RF']
            u_fo = f.fieldOutputs['U']
            # Find node 999999
            for v in rf_fo.values:
                if v.nodeLabel == 999999:
                    rf2_val = float(v.data[1])
                    break
            else:
                continue
            for v in u_fo.values:
                if v.nodeLabel == 999999:
                    u2_val = float(v.data[1])
                    break
            else:
                continue
            if abs(rf2_val) > abs(peak_rf2):
                peak_rf2 = rf2_val
                peak_u2 = u2_val
                peak_frame = (sname, i, f.frameValue)

print("Peak Reaction Force in Baseline: RF2 = %.6f kN at U2 = %.6f mm in %s Frame %d (time %.4f)" % 
      (peak_rf2, peak_u2, peak_frame[0], peak_frame[1], peak_frame[2]))

# Also check terminal state of Step-2
f_term = odb.steps['Step-2'].frames[-1]
for v in f_term.fieldOutputs['RF'].values:
    if v.nodeLabel == 999999:
        term_rf2 = float(v.data[1])
        break
for v in f_term.fieldOutputs['U'].values:
    if v.nodeLabel == 999999:
        term_u2 = float(v.data[1])
        break
print("Terminal State of Step-2: RF2 = %.6f kN at U2 = %.6f mm in Frame %d (time %.4f)" % 
      (term_rf2, term_u2, len(odb.steps['Step-2'].frames)-1, f_term.frameValue))

odb.close()
