"""Cheap causal field-integration audit; no solve, future field used only to evaluate."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import mode2_single_job_orchestrator as api
from mode2_runtime import load_transfer


def integral(nodes,quads,tris,damage,history,recipient=False):
    h_total=d_total=area_total=0.
    for eid,conn in {**quads,**tris}.items():
        xy=[nodes[n] for n in conn]
        area=abs(sum(xy[i][0]*xy[(i+1)%len(xy)][1]-xy[(i+1)%len(xy)][0]*xy[i][1]
                     for i in range(len(xy))))/2
        values=[history.get((eid,g),0.) for g in range(1,5 if len(conn)==4 else 4)]
        if len(conn)==4:
            hv=sum(values)/4
        elif recipient:
            hv=history.get((eid,1),0.)
        else:
            hv=sum(values[:3])/3
        h_total+=area*hv
        d_total+=area*sum(damage[n] for n in conn)/len(conn)
        area_total+=area
    return {'area_mm2':area_total,'integral_H_kn':h_total,'integral_averaged_damage_mm2':d_total}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--donor-checkpoint',required=True)
    parser.add_argument('--recipient-mesh',required=True)
    parser.add_argument('--cycle-checkpoint',required=True)
    a=parser.parse_args()
    donor=json.loads(Path(a.donor_checkpoint).read_text())
    dn,dq,dt,_=api.parse_physical_mesh(donor['mesh_path'])
    rn,rq,rt,_=api.parse_physical_mesh(a.recipient_mesh)
    fields=donor['fields']['terminal']
    d={int(n):v for n,v in fields['damage'].items()}
    h={tuple(map(int,k.split('_'))):v for k,v in fields['history'].items()}
    rd,rh=load_transfer()(dn,dq,dt,d,h,rn,rq,rt)
    before=integral(dn,dq,dt,d,h)
    after=integral(rn,rq,rt,rd,rh,True)
    evaluation=json.loads(Path(a.cycle_checkpoint).read_text())['fields']
    result={'classification':'OFFLINE_CAUSAL_TRANSFER_AUDIT_NO_NEW_SOLVE',
        'donor_checkpoint_sha256':api.compute_sha256(a.donor_checkpoint),
        'recipient_mesh_sha256':api.compute_sha256(a.recipient_mesh),
        'donor':before,'transferred_initial_fields':after,
        'H_integral_change_pct':100*(after['integral_H_kn']/before['integral_H_kn']-1),
        'damage_integral_change_pct':100*(after['integral_averaged_damage_mm2']/before['integral_averaged_damage_mm2']-1),
        'donor_max_damage':max(d.values()),'transferred_max_damage':max(rd.values()),
        'donor_max_H':max(h.values()),'transferred_max_H':max(rh.values()),
        'donor_u1_mm':fields['u1'],'hold_u1_mm':evaluation['hold']['u1'],
        'donor_rf1_kn':fields['rf1'],'hold_rf1_kn':evaluation['hold']['rf1'],
        'hold_max_damage':max(evaluation['hold']['damage'].values()),
        'terminal_max_damage':max(evaluation['terminal']['damage'].values()),
        'causal_cutoff':'Coarse Step-1, increment 200, time 1.0; cycle fields are held-out evaluation only',
        'limitations':['Areal integration of averaged fields is a diagnostic, not a new acceptance threshold.',
                      'This audit does not establish whether history interpolation or refinement-induced instability caused the force loss.',
                      'Global max-damage nonhealing does not establish pointwise irreversibility.']}
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
