#!/usr/bin/env python3
"""
Audit all INGEST_TRACE records across all log files in M2STATE_FRACFIX_RESTART1R1R5 execution directory.
Determines if any finite numerical U or SVARS records exist.
"""

import os
import glob
import re
import json

def audit_trace_records():
    trace_files = sorted(list(set(glob.glob('*.trace') + glob.glob('*.dat') + glob.glob('*.msg') + glob.glob('*.log') + glob.glob('*.pbs.log'))))
    pattern = re.compile(r'\[INGEST_TRACE\]\s+KSTEP=(\d+)\s+KINC=(\d+)\s+JELEM=\s*(\d+)\s+JTYPE=(\d+)\s+PHYSIDX=\s*(\d+)\s+U123=\s*(\S+)\s+(\S+)\s+(\S+)\s+SVARS1-4=\s*(\S+)\s+(\S+)\s+(\S+)\s+(\S+)')

    records = []
    nan_count = 0
    finite_u_count = 0
    finite_svars_count = 0

    for fname in trace_files:
        if not os.path.isfile(fname):
            continue
        try:
            with open(fname, 'r') as f:
                for lno, line in enumerate(f, 1):
                    if '[INGEST_TRACE]' in line:
                        m = pattern.search(line)
                        if m:
                            kstep = int(m.group(1))
                            kinc = int(m.group(2))
                            jelem = int(m.group(3))
                            jtype = int(m.group(4))
                            physidx = int(m.group(5))
                            u1_s, u2_s, u3_s = m.group(6), m.group(7), m.group(8)
                            sv1_s, sv2_s, sv3_s, sv4_s = m.group(9), m.group(10), m.group(11), m.group(12)
                            
                            has_nan = 'NaN' in [u1_s, u2_s, u3_s, sv1_s, sv2_s, sv3_s, sv4_s]
                            u_finite = ('NaN' not in u1_s) and ('NaN' not in u2_s) and ('NaN' not in u3_s)
                            sv_finite = ('NaN' not in sv1_s) and ('NaN' not in sv2_s) and ('NaN' not in sv3_s) and ('NaN' not in sv4_s)
                            
                            if has_nan:
                                nan_count += 1
                            if u_finite:
                                finite_u_count += 1
                            if sv_finite:
                                finite_svars_count += 1
                                
                            records.append({
                                'file': fname, 'line': lno, 'kstep': kstep, 'kinc': kinc,
                                'jelem': jelem, 'jtype': jtype, 'physidx': physidx,
                                'u1': u1_s, 'u2': u2_s, 'u3': u3_s,
                                'sv1': sv1_s, 'sv2': sv2_s, 'sv3': sv3_s, 'sv4': sv4_s,
                                'has_nan': has_nan
                            })
        except Exception as e:
            print("Error reading {}: {}".format(fname, e))

    summary = {
        'trace_record_count': len(records),
        'trace_finite_U_record_count': finite_u_count,
        'trace_finite_SVARS_record_count': finite_svars_count,
        'trace_NaN_record_count': nan_count,
        'records_sample': records[:10]
    }
    
    print(json.dumps(summary, indent=2))
    return summary

if __name__ == "__main__":
    audit_trace_records()
