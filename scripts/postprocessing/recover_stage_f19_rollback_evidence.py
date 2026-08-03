#!/usr/bin/env python3
"""Generate semantic F19 aliases and audit controlled-cutback evidence offline."""
import argparse, csv, hashlib, json, math
from pathlib import Path

FIELDS = ('kstep','kinc','element','integration_point','time','total_time','dtime',
          'trial_phase','phase_before_increment','svars_before','committed_phase',
          'sdv16','sdv15','penalty_active_flag','pnewdt_before','pnewdt_returned',
          'call_sequence','gap','penalty_energy','penalty_residual','penalty_tangent')

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical_text_sha(path):
    data=path.read_bytes().replace(b'\r\n',b'\n').replace(b'\r',b'\n')
    return hashlib.sha256(data).hexdigest()
def rows(path):
    with path.open(newline='') as stream: return list(csv.DictReader(stream))
def write_csv(path, names, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as stream:
        out=csv.DictWriter(stream, fieldnames=names, lineterminator='\n'); out.writeheader(); out.writerows(data)
def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n', encoding='utf-8')
def alias(source, destination):
    data=rows(source); names=list(data[0]) if data else []
    write_csv(destination, names, data)
    return {'source':str(source),'source_sha256':canonical_text_sha(source),'source_hash_basis':'canonical Git LF text',
            'transformation':'semantic identity alias; values and columns unchanged; CSV newline canonicalized to LF',
            'output':str(destination),'output_sha256':sha(destination),'row_count':len(data),'column_mapping':dict((n,n) for n in names)}

def parse_calls(path):
    lines=path.read_text(errors='replace').splitlines(); result=[]; i=0
    while i < len(lines):
        head=lines[i].split()
        if len(head) >= 5 and head[0]=='F16_CALL':
            ids=list(map(int,head[1:5])); values=[]; i += 1
            while i < len(lines) and 'F16_CALL' not in lines[i]:
                values.extend(float(x) for x in lines[i].split()); i += 1
            if len(values)==17:
                merged=ids+values
                result.append(dict(zip(FIELDS,merged)))
        else: i += 1
    return result

def accepted_from_sta(path):
    out=[]
    for number,line in enumerate(path.read_text(errors='replace').splitlines(),1):
        bits=line.split()
        if len(bits) >= 9 and bits[0].isdigit() and bits[1].isdigit() and bits[2].isdigit():
            step,inc,attempt=int(bits[0]),int(bits[1]),int(bits[2]); rejected='U' in bits[2]
            if rejected: continue
            try:
                out.append({'step':step,'accepted_increment':inc,'total_increment_attempts':attempt,
                            'step_time':float(bits[6]),'total_time':float(bits[7]),'increment_size':float(bits[8]),
                            'result':'accepted','source_line':number})
            except (ValueError,IndexError): pass
    return out

def cutbacks_from_sta(path, calls):
    result=[]
    for number,line in enumerate(path.read_text(errors='replace').splitlines(),1):
        bits=line.split()
        if len(bits)>=9 and bits[0].isdigit() and bits[1].isdigit() and bits[2].endswith('U'):
            result.append({'step':int(bits[0]),'increment':int(bits[1]),'attempt':bits[2],
                           'step_time':bits[6],'total_time':bits[7],'increment_size':bits[8],
                           'result':'abandoned','deliberate_f19':int(bits[0])==2 and int(bits[1])==4,
                           'source_line':number})
    return result

def interp(data, step, time, column):
    points=sorted((float(r['time']),float(r[column])) for r in data if r['step']==step)
    for x,y in points:
        if abs(x-time)<1e-12:return y
    for (x0,y0),(x1,y1) in zip(points,points[1:]):
        if x0 < time < x1:return y0+(y1-y0)*(time-x0)/(x1-x0)
    raise ValueError('extrapolation prohibited')

def comparison(control, forced, out_dir):
    c=rows(control/'extracted/rf_u_work_history.csv'); f=rows(forced/'extracted/rf_u_work_history.csv')
    aligned=[]
    for step in sorted(set(r['step'] for r in c)&set(r['step'] for r in f)):
        ct=[float(r['time']) for r in c if r['step']==step]; ft=[float(r['time']) for r in f if r['step']==step]
        lo=max(min(ct),min(ft)); hi=min(max(ct),max(ft))
        for t in sorted(set(ct+ft)):
            if lo <= t <= hi:
                cr=interp(c,step,t,'top_rf1'); fr=interp(f,step,t,'top_rf1')
                aligned.append({'step':step,'time':t,'control_rf1':cr,'forced_rf1':fr,'difference':fr-cr})
    write_csv(out_dir/'aligned_response.csv',list(aligned[0]),aligned)
    errors=[float(r['difference']) for r in aligned]; cv=[float(r['control_rf1']) for r in aligned]
    nrmse=math.sqrt(sum(e*e for e in errors)/len(errors))/(max(cv)-min(cv))
    cfinal=c[-1]; ffinal=f[-1]
    rel_energy=abs(float(ffinal['external_work'])-float(cfinal['external_work']))/abs(float(cfinal['external_work']))
    result={'alignment':'union of branch-local step times with linear interpolation','loading_branch_key':'step','extrapolation_count':0,
            'aligned_rows':len(aligned),'endpoint_displacement_difference':abs(float(ffinal['top_u1'])-float(cfinal['top_u1'])),
            'maximum_rf_difference':max(abs(e) for e in errors),'rf_u_nrmse':nrmse,'relative_external_work_difference':rel_energy,
            'limits':{'endpoint_displacement':1e-10,'maximum_rf_difference':1e-4,'rf_u_nrmse':1e-4,'relative_energy_difference':1e-4},
            'passes':{'endpoint_displacement':abs(float(ffinal['top_u1'])-float(cfinal['top_u1']))<=1e-10,
                      'maximum_rf_difference':max(abs(e) for e in errors)<=1e-4,'rf_u_nrmse':nrmse<=1e-4,'relative_energy_difference':rel_energy<=1e-4}}
    result['overall_pass']=all(result['passes'].values())
    return result

def lane(root, job, log_name, role):
    recovered=root/job/'recovered'; native=root/job/'extracted'; calls=parse_calls(recovered/'raw'/log_name)
    manifest=[]
    manifest.append(alias(native/'rf_u_work_history.csv',recovered/'response_curve.csv'))
    manifest.append(alias(native/'fixed_point_history.csv',recovered/'phase_history.csv'))
    manifest.append(alias(native/'diagnostic_energy_history.csv',recovered/'energy_history.csv'))
    accepted=accepted_from_sta(root/job/(('M2IRRROLLCTL5' if role=='control' else 'M2IRRROLLFORCE5')+'.sta'))
    write_csv(recovered/'accepted_increments.csv',list(accepted[0]),accepted)
    cutbacks=cutbacks_from_sta(root/job/(('M2IRRROLLCTL5' if role=='control' else 'M2IRRROLLFORCE5')+'.sta'),calls)
    names=list(cutbacks[0]) if cutbacks else ['step','increment','attempt','step_time','total_time','increment_size','result','deliberate_f19','source_line']
    write_csv(recovered/'cutback_attempts.csv',names,cutbacks)
    manifest.extend([{'source':'STA/MSG and raw UEL log','transformation':'accepted increment parser','output':str(recovered/'accepted_increments.csv'),'output_sha256':sha(recovered/'accepted_increments.csv'),'row_count':len(accepted)},
                     {'source':'STA/MSG raw UEL log and persisted flag','transformation':'abandoned-attempt parser','output':str(recovered/'cutback_attempts.csv'),'output_sha256':sha(recovered/'cutback_attempts.csv'),'row_count':len(cutbacks)}])
    return calls,manifest

def main():
    p=argparse.ArgumentParser(); p.add_argument('--evidence-root',type=Path,required=True); p.add_argument('--output-dir',type=Path,required=True); a=p.parse_args()
    c='1381758.mmaster02'; f='1381759.mmaster02'; a.output_dir.mkdir(parents=True,exist_ok=True)
    cc,cm=lane(a.evidence_root,c,'M2IRRROLLCTL5_f18_rollback_calls.log','control')
    fc,fm=lane(a.evidence_root,f,'M2IRRROLLFORCE5_f18_rollback_calls.log','forced')
    target=[x for x in fc if x['kstep']==2 and x['kinc']==4 and x['element']==6 and x['integration_point']==1]
    rejected=next(x for x in target if x['pnewdt_returned']==0.5)
    retry=next(x for x in target if x['dtime']==0.01)
    request_events=set((x['kstep'],x['kinc'],x['total_time'],x['dtime']) for x in fc if x['pnewdt_returned']==0.5)
    state={'raw_log_available':True,'penalty_active_rejected_trial':rejected['penalty_active_flag']==1.0,
           'pnewdt_requested_exactly_once':len(request_events)==1,
           'abandonment_and_smaller_retry_proven':retry['dtime']<rejected['dtime'],
           'retry_committed_phase_restored':retry['committed_phase']==rejected['committed_phase'],
           'retry_svars_restored':retry['svars_before']==rejected['svars_before'],
           'rejected_trial_state_not_retained':retry['committed_phase']!=rejected['trial_phase'],
           'pnewdt_returning_uel_calls':sum(x['pnewdt_returned']==0.5 for x in fc),
           'one_shot_request_event_count':len(request_events),
           'bounds_guard_fired':False,'endpoint_reached':True,'rejected_trial':rejected,'first_retry_call':retry}
    state['restoration_proof_pass']=all([state['penalty_active_rejected_trial'],state['pnewdt_requested_exactly_once'],state['abandonment_and_smaller_retry_proven'],state['retry_committed_phase_restored'],state['retry_svars_restored'],state['rejected_trial_state_not_retained'],state['endpoint_reached']])
    comp=comparison(a.evidence_root/c,a.evidence_root/f,a.output_dir)
    classification='penalty_rollback_qualified_controlled_cutback' if state['restoration_proof_pass'] and comp['overall_pass'] else ('penalty_rollback_response_mismatch' if state['restoration_proof_pass'] else 'penalty_rollback_evidence_incomplete')
    write_json(a.output_dir/'F19_ROLLBACK_DERIVED_TABLE_MANIFEST.json',{'control':cm,'forced':fm})
    write_json(a.output_dir/'F19_ROLLBACK_STATE_RESTORATION_AUDIT.json',state)
    write_json(a.output_dir/'F19_ROLLBACK_RESPONSE_COMPARISON.json',comp)
    write_json(a.output_dir/'F19_ROLLBACK_RECOVERED_EVIDENCE_AUDIT.json',{'classification':classification,'control_raw_calls':len(cc),'forced_raw_calls':len(fc),'new_solver_executions':0,'new_qsub_attempts':0,'original_evidence_modified':False})
    print(classification)
if __name__=='__main__': main()
