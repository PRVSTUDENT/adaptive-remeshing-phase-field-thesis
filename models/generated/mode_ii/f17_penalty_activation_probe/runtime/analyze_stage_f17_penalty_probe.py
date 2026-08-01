from __future__ import print_function
import argparse, json, math, os

def classify(calls, tables_present):
    active = []
    for row in calls:
        finite_tangent = not math.isnan(row['penalty_tangent']) and not math.isinf(row['penalty_tangent'])
        if (row['trial_phase'] < row['committed_phase'] - row['tolerance'] and
                abs(row['penalty_residual']) > 0.0 and row['penalty_energy'] > 0.0 and
                finite_tangent and not row.get('bounds_guard', False)):
            active.append(row)
    if not tables_present:
        return 'penalty_activation_evidence_incomplete', active
    return ('penalty_activation_probe_passed' if active else 'penalty_activation_not_observed'), active

def read_calls(path):
    rows=[]
    with open(path) as stream:
        lines=stream.readlines()
    index=0
    while index < len(lines):
        if 'F16_CALL' not in lines[index]:
            index += 1
            continue
        head=lines[index].split(); values=[]; index += 1
        while index < len(lines) and 'F16_CALL' not in lines[index]:
            values.extend(float(item) for item in lines[index].split()); index += 1
        if len(values) != 17:
            continue
        rows.append({'kstep':int(head[1]),'kinc':int(head[2]),'element':int(head[3]),'integration_point':int(head[4]),
                     'time':values[0],'total_time':values[1],'dtime':values[2],
                     'trial_phase':values[3],'phase_before_increment':values[4],
                     'svars_before':values[5],'committed_phase':values[6],
                     'sdv16':values[7],'sdv15':values[8],'penalty_active_flag':values[9],
                     'pnewdt_before':values[10],'pnewdt_returned':values[11],
                     'call_sequence':int(values[12]),'gap':values[13],
                     'penalty_energy':values[14],'penalty_residual':values[15],
                     'penalty_tangent':values[16],'tolerance':1.0e-8,'bounds_guard':False,
                     'accepted_status':'not_determinable_at_uel_call'})
    return rows

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--log'); parser.add_argument('--extracted'); parser.add_argument('--output'); args=parser.parse_args()
    required=['response_curve.csv','phase_history.csv','energy_history.csv','accepted_increments.csv']
    tables=all(os.path.getsize(os.path.join(args.extracted,n)) > 0 for n in required if os.path.exists(os.path.join(args.extracted,n))) and all(os.path.exists(os.path.join(args.extracted,n)) for n in required)
    calls=read_calls(args.log)
    classification,active=classify(calls,tables)
    trigger=None
    if active:
        first=active[0]
        trigger=dict((key,first[key]) for key in ('kstep','kinc','element','integration_point','time','dtime','committed_phase','trial_phase','gap'))
    with open(args.output,'w') as stream: json.dump({'classification':classification,'penalty_active_call_count':len(active),'first_penalty_active_call':active[0] if active else None,'deterministic_trigger':trigger,'rollback_qualified':False,'response_tables_retained':tables},stream,indent=2,sort_keys=True)
    return 0 if classification in ('penalty_activation_probe_passed','penalty_activation_not_observed') else 1
if __name__=='__main__': raise SystemExit(main())
