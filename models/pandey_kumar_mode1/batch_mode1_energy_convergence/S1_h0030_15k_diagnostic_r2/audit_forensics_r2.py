import os
import sys
import csv
import json

workdir = "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/batch_mode1_energy_convergence/S1_h0030_15k_diagnostic_r2"
sta_path = os.path.join(workdir, "PK_M1_S1_DIAG_R2.sta")
dat_path = os.path.join(workdir, "PK_M1_S1_DIAG_R2.dat")
eb_path = os.path.join(workdir, "uel_energy_balance.csv")
disc_path = os.path.join(workdir, "uel_discrete_diagnostic.csv")
trace_path = os.path.join(workdir, "uel_call_order_trace.csv")
harv_log = os.path.join(workdir, "harvester.log")
out_path = os.path.join(workdir, "PK_M1_S1_DIAG_R2.out")
err_path = os.path.join(workdir, "PK_M1_S1_DIAG_R2.err")

print("================================================================================")
print("COMPREHENSIVE FORENSIC AUDIT OF JOB 1406839.mmaster02 (S1 DIAGNOSTIC R2)")
print("================================================================================")

# 1. STA File Analysis
sta_incs = []
if os.path.exists(sta_path):
    with open(sta_path, "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 10:
                try:
                    step = int(parts[0])
                    inc = int(parts[1])
                    att = int(parts[2])
                    sev = int(parts[3])
                    eq = int(parts[4])
                    tot_t = float(parts[8])
                    step_t = float(parts[9])
                    inc_t = float(parts[10]) if len(parts) > 10 else 0.0
                    sta_incs.append({
                        "step": step, "inc": inc, "att": att,
                        "tot_time": tot_t, "step_time": step_t, "inc_time": inc_t
                    })
                except ValueError:
                    pass

print("\n1. STA FILE PARSING (" + sta_path + "):")
print("   Total accepted increments in .sta: " + str(len(sta_incs)))
if sta_incs:
    s1_incs = [x for x in sta_incs if x['step'] == 1]
    s2_incs = [x for x in sta_incs if x['step'] == 2]
    print("   Step 1 accepted increments: " + str(len(s1_incs)) + " (Incs " + str(s1_incs[0]['inc']) + " to " + str(s1_incs[-1]['inc']) + ")")
    print("   Step 2 accepted increments: " + str(len(s2_incs)) + " (Incs " + str(s2_incs[0]['inc']) + " to " + str(s2_incs[-1]['inc']) + ")")
    print("   Terminal time: TotalTime = " + str(sta_incs[-1]['tot_time']) + ", StepTime = " + str(sta_incs[-1]['step_time']))

# 2. DAT File Analysis
dat_points = []
if os.path.exists(dat_path):
    with open(dat_path, "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) == 3 and parts[0] == "999999":
                try:
                    u = float(parts[1])
                    rf = float(parts[2])
                    dat_points.append((u, rf))
                except ValueError:
                    pass

print("\n2. DAT FILE PARSING (" + dat_path + "):")
print("   Total (u, RF) pairs extracted: " + str(len(dat_points)))
if dat_points:
    print("   First DAT point: u = " + str(dat_points[0][0]) + ", RF = " + str(dat_points[0][1]))
    print("   Last DAT point:  u = " + str(dat_points[-1][0]) + ", RF = " + str(dat_points[-1][1]))

# 3. Unit 105 (uel_energy_balance.csv) Analysis
eb_rows = []
if os.path.exists(eb_path):
    with open(eb_path, "r") as f:
        reader = csv.reader(f)
        eb_header = next(reader, None)
        for row in reader:
            if len(row) >= 7:
                try:
                    step = int(row[0].strip())
                    inc = int(row[1].strip())
                    t_tot = float(row[2].strip())
                    t_step = float(row[3].strip())
                    e_elas = float(row[4].strip())
                    e_frac = float(row[5].strip())
                    e_tot = float(row[6].strip())
                    eb_rows.append({
                        "step": step, "inc": inc, "t_tot": t_tot, "t_step": t_step,
                        "e_elas": e_elas, "e_frac": e_frac, "e_tot": e_tot
                    })
                except ValueError:
                    pass

print("\n3. UNIT 105 (uel_energy_balance.csv) RECONCILIATION:")
print("   Header: " + str(eb_header))
print("   Total valid data rows: " + str(len(eb_rows)))
if eb_rows:
    eb_s1 = [x for x in eb_rows if x['step'] == 1]
    eb_s2 = [x for x in eb_rows if x['step'] == 2]
    print("   Step 1 rows: " + str(len(eb_s1)) + " (Incs " + str(eb_s1[0]['inc']) + " to " + str(eb_s1[-1]['inc']) + ")")
    print("   Step 2 rows: " + str(len(eb_s2)) + " (Incs " + str(eb_s2[0]['inc']) + " to " + str(eb_s2[-1]['inc']) + ")")
    print("   First row: Step " + str(eb_rows[0]['step']) + ", Inc " + str(eb_rows[0]['inc']) + ", t_tot = " + str(eb_rows[0]['t_tot']) + ", E_tot = " + str(eb_rows[0]['e_tot']))
    print("   Last row:  Step " + str(eb_rows[-1]['step']) + ", Inc " + str(eb_rows[-1]['inc']) + ", t_tot = " + str(eb_rows[-1]['t_tot']) + ", E_tot = " + str(eb_rows[-1]['e_tot']))

    s1_expected = set(range(1, 2001))
    s1_found = set(x['inc'] for x in eb_s1)
    s1_missing = sorted(list(s1_expected - s1_found))
    print("   Step 1 missing increments (out of 2000): " + str(len(s1_missing)) + " -> " + str(s1_missing[:10]))

    s2_expected = set(range(1, 5001))
    s2_found = set(x['inc'] for x in eb_s2)
    s2_missing = sorted(list(s2_expected - s2_found))
    print("   Step 2 missing increments (out of 5000): " + str(len(s2_missing)) + " -> " + str(s2_missing))

    seen = set()
    duplicates = []
    for x in eb_rows:
        key = (x['step'], x['inc'])
        if key in seen:
            duplicates.append(key)
        seen.add(key)
    print("   Duplicate (Step, Inc) pairs: " + str(len(duplicates)) + " -> " + str(duplicates))

# 4. Unit 106 (uel_discrete_diagnostic.csv) Analysis
disc_rows = []
if os.path.exists(disc_path):
    with open(disc_path, "r") as f:
        reader = csv.reader(f)
        disc_header = next(reader, None)
        for row in reader:
            if len(row) >= 14:
                try:
                    disc_rows.append({
                        "step": int(row[0].strip()),
                        "inc": int(row[1].strip()),
                        "t_tot": float(row[2].strip()),
                        "t_step": float(row[3].strip()),
                        "e_elas": float(row[4].strip()),
                        "e_frac": float(row[5].strip()),
                        "e_int": float(row[6].strip()),
                        "inc_t_hist": float(row[7].strip()),
                        "inc_t_avg": float(row[8].strip()),
                        "inc_t_split": float(row[9].strip()),
                        "cum_t_hist": float(row[10].strip()),
                        "cum_t_avg": float(row[11].strip()),
                        "cum_t_split": float(row[12].strip()),
                        "cum_t_sum": float(row[13].strip()),
                    })
                except ValueError:
                    pass

print("\n4. UNIT 106 (uel_discrete_diagnostic.csv) RECONCILIATION:")
print("   Header: " + str(disc_header))
print("   Total valid data rows: " + str(len(disc_rows)))
if disc_rows:
    disc_s1 = [x for x in disc_rows if x['step'] == 1]
    disc_s2 = [x for x in disc_rows if x['step'] == 2]
    print("   Step 1 rows: " + str(len(disc_s1)) + " (Incs " + str(disc_s1[0]['inc']) + " to " + str(disc_s1[-1]['inc']) + ")")
    print("   Step 2 rows: " + str(len(disc_s2)) + " (Incs " + str(disc_s2[0]['inc']) + " to " + str(disc_s2[-1]['inc']) + ")")
    print("   First row: Step " + str(disc_rows[0]['step']) + ", Inc " + str(disc_rows[0]['inc']) + ", t_tot = " + str(disc_rows[0]['t_tot']))
    print("   Last row:  Step " + str(disc_rows[-1]['step']) + ", Inc " + str(disc_rows[-1]['inc']) + ", t_tot = " + str(disc_rows[-1]['t_tot']))

    s2_disc_missing = sorted(list(set(range(1, 5001)) - set(x['inc'] for x in disc_s2)))
    print("   Step 2 missing increments: " + str(len(s2_disc_missing)) + " -> " + str(s2_disc_missing))

    t_hist_vals = [x['inc_t_hist'] for x in disc_rows]
    t_avg_vals = [x['inc_t_avg'] for x in disc_rows]
    t_split_vals = [x['inc_t_split'] for x in disc_rows]
    cum_hist_vals = [x['cum_t_hist'] for x in disc_rows]
    cum_avg_vals = [x['cum_t_avg'] for x in disc_rows]
    cum_split_vals = [x['cum_t_split'] for x in disc_rows]
    cum_sum_vals = [x['cum_t_sum'] for x in disc_rows]

    print("   Diagnostic Terms Extrema:")
    print("     Inc_T_hist:  min = " + str(min(t_hist_vals)) + ", max = " + str(max(t_hist_vals)) + ", final = " + str(t_hist_vals[-1]))
    print("     Inc_T_avg:   min = " + str(min(t_avg_vals)) + ", max = " + str(max(t_avg_vals)) + ", final = " + str(t_avg_vals[-1]))
    print("     Inc_T_split: min = " + str(min(t_split_vals)) + ", max = " + str(max(t_split_vals)) + ", final = " + str(t_split_vals[-1]))
    print("     Cum_T_hist:  min = " + str(min(cum_hist_vals)) + ", max = " + str(max(cum_hist_vals)) + ", final = " + str(cum_hist_vals[-1]))
    print("     Cum_T_avg:   min = " + str(min(cum_avg_vals)) + ", max = " + str(max(cum_avg_vals)) + ", final = " + str(cum_avg_vals[-1]))
    print("     Cum_T_split: min = " + str(min(cum_split_vals)) + ", max = " + str(max(cum_split_vals)) + ", final = " + str(cum_split_vals[-1]))
    print("     Cum_T_sum:   min = " + str(min(cum_sum_vals)) + ", max = " + str(max(cum_sum_vals)) + ", final = " + str(cum_sum_vals[-1]))

# 5. Unit 107 (uel_call_order_trace.csv) Analysis
print("\n5. UNIT 107 (uel_call_order_trace.csv) ANALYSIS:")
if os.path.exists(trace_path):
    trace_sz = os.path.getsize(trace_path)
    print("   File size: " + str(trace_sz) + " bytes (" + str(round(trace_sz / 1e6, 2)) + " MB)")
    first_few = []
    last_few = []
    line_count = 0
    with open(trace_path, "r") as f:
        reader = csv.reader(f)
        trace_header = next(reader, None)
        for row in reader:
            line_count += 1
            if line_count <= 5:
                first_few.append(row)
            if len(last_few) < 5:
                last_few.append(row)
            else:
                last_few.pop(0)
                last_few.append(row)

    print("   Trace Header: " + str(trace_header))
    print("   Total sampled call rows: " + str(line_count))
    print("   First sampled calls:")
    for r in first_few:
        print("     " + str(r))
    print("   Last sampled calls:")
    for r in last_few:
        print("     " + str(r))

# 6. Harvester Log Analysis
print("\n6. HARVESTER LOG (" + harv_log + "):")
if os.path.exists(harv_log):
    with open(harv_log, "r") as f:
        lines = f.readlines()
    print("   Total log lines: " + str(len(lines)))
    for l in lines[:5]:
        print("     [START] " + l.strip())
    for l in lines[-10:]:
        print("     [END]   " + l.strip())

# 7. PBS Out / Err Analysis
print("\n7. PBS STDOUT / STDERR:")
if os.path.exists(out_path):
    with open(out_path, "r") as f:
        out_lines = f.readlines()
    print("   Stdout lines: " + str(len(out_lines)))
    for l in out_lines[-15:]:
        print("     [STDOUT] " + l.strip())

if os.path.exists(err_path):
    with open(err_path, "r") as f:
        err_lines = f.readlines()
    print("   Stderr lines: " + str(len(err_lines)))
    for l in err_lines:
        print("     [STDERR] " + l.strip())
