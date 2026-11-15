# -*- coding: utf-8 -*-
import sys
import os
import re

def parse_dat_rf(dat_path):
    data = []
    if not os.path.exists(dat_path):
        print("Path not found: %s" % dat_path)
        return data

    with open(dat_path, 'r') as f:
        lines = f.readlines()

    current_inc = None
    step_time = None
    total_time = None

    for line in lines:
        inc_match = re.search(r'INCREMENT\s+(\d+)\s+SUMMARY', line)
        if inc_match:
            current_inc = int(inc_match.group(1))

        time_match = re.search(r'STEP TIME COMPLETED\s+([\d.E+-]+)\s*,\s*TOTAL TIME COMPLETED\s+([\d.E+-]+)', line)
        if time_match:
            step_time = float(time_match.group(1))
            total_time = float(time_match.group(2))

        if '999999' in line and ('E-' in line or 'E+' in line):
            parts = line.strip().split()
            if len(parts) >= 3 and parts[0] == '999999':
                try:
                    u2 = float(parts[1])
                    rf2 = float(parts[2])
                    data.append({
                        'increment': current_inc,
                        'total_time': total_time,
                        'step_time': step_time,
                        'u2_mm': u2,
                        'rf2_kN': rf2,
                        'rf2_N': rf2 * 1000.0
                    })
                except ValueError:
                    pass
    return data

def main():
    dat_base = 'results/validation/f1735_case2_fracture_evidence/PK_F1735_CASE_2_FRAC.dat'
    dat_rerun = 'models/pandey_kumar_mode1/234_f1752_case2_continuation/PK_F1752_CASE_2_CONTINUATION.dat'

    pts_base = parse_dat_rf(dat_base)
    pts_rerun = parse_dat_rf(dat_rerun)

    print("Job 1423271 (Baseline): %d points" % len(pts_base))
    print("Job 1423552 (Rerun):    %d points" % len(pts_rerun))

    print("\n--- Last 5 Points of Baseline (Job 1423271) ---")
    for p in pts_base[-5:]:
        print("  Inc %s: time=%.8f, u2=%.8e, rf2=%.8e kN (%.4f N)" % (
            p['increment'], p['step_time'], p['u2_mm'], p['rf2_kN'], p['rf2_N']))

    print("\n--- Corresponding Points in Rerun (Job 1423552) ---")
    for p in pts_rerun[-8:]:
        print("  Inc %s: time=%.8f, u2=%.8e, rf2=%.8e kN (%.4f N)" % (
            p['increment'], p['step_time'], p['u2_mm'], p['rf2_kN'], p['rf2_N']))

    p_base_final = pts_base[-1]
    matches = [p for p in pts_rerun if p['increment'] == p_base_final['increment'] and abs(p['step_time'] - p_base_final['step_time']) < 1e-6]
    if matches:
        p_rerun_match = matches[0]
        diff_f = abs(p_rerun_match['rf2_kN'] - p_base_final['rf2_kN'])
        rel_diff_pct = diff_f / p_base_final['rf2_kN'] * 100.0
        print("\nExact Match at Inc %s:" % p_base_final['increment'])
        print("  Base RF2:  %.8e kN" % p_base_final['rf2_kN'])
        print("  Rerun RF2: %.8e kN" % p_rerun_match['rf2_kN'])
        print("  Delta RF2: %.8e kN (%.6f %%)" % (diff_f, rel_diff_pct))
        print("  Parity <= 0.01%%: %s" % (rel_diff_pct <= 0.01))

if __name__ == '__main__':
    main()
