"""Bounded local Mode-II shear demonstration using the unchanged frozen UEL.

This runner reuses Case 1's transfer implementation unchanged. A two-step job
is audited after completion; a failed transfer gate forbids donor acceptance
and further cycles. It does not claim Miehe constitutive reproduction.
"""
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def load_transfer():
    path = ROOT / 'models/pandey_kumar_mode1/291_method_c_case1/case1_single_job_orchestrator.py'
    spec = importlib.util.spec_from_file_location('method_c_case1_transfer', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.transfer_state_fields


def connected_tip(nodes, elements, damage, threshold=.95):
    """Find the damaged component attached to the notch, without path seeding."""
    active = {n for n in nodes if damage.get(n, 0.) >= threshold}
    graph = {n: set() for n in active}
    for conn in elements.values():
        selected = [n for n in conn if n in active]
        for n in selected:
            graph[n].update(selected)
    seen = {n for n in active if math.hypot(nodes[n][0]-.5, nodes[n][1]-.5) <= .04}
    todo = list(seen)
    while todo:
        for n in graph[todo.pop()] - seen:
            seen.add(n)
            todo.append(n)
    if not seen:
        return (.5, .5), False
    tip = max(seen, key=lambda n: math.hypot(nodes[n][0]-.5, nodes[n][1]-.5))
    boundary = any(nodes[n][1] <= 1e-6 or nodes[n][0] >= 1.-1e-6 for n in seen)
    return nodes[tip], boundary


def completion(peak, force, boundary):
    if peak > 0 and abs(force)/peak < .05:
        return True, 'REACTION_FORCE_BELOW_5PCT_PEAK'
    if boundary:
        return True, 'CONNECTED_DAMAGE_REACHED_BOTTOM_OR_RIGHT_BOUNDARY'
    return False, 'IN_PROGRESS'


def geometry_audit(nodes, elements):
    """Actual signed Jacobians at quadrature points; never a hardcoded PASS."""
    determinants=[]
    max_ratio=0.
    q=1/math.sqrt(3)
    for conn in elements.values():
        xy=[nodes[n] for n in conn]
        lengths=[math.dist(xy[i],xy[(i+1)%len(xy)]) for i in range(len(xy))]
        max_ratio=max(max_ratio,max(lengths)/min(lengths) if min(lengths)>0 else float('inf'))
        if len(conn)==3:
            (x0,y0),(x1,y1),(x2,y2)=xy
            determinants.append((x1-x0)*(y2-y0)-(x2-x0)*(y1-y0))
        else:
            for xi,eta in [(-q,-q),(q,-q),(q,q),(-q,q)]:
                dx=[-(1-eta)/4,(1-eta)/4,(1+eta)/4,-(1+eta)/4]
                dy=[-(1-xi)/4,-(1+xi)/4,(1+xi)/4,(1-xi)/4]
                xx=sum(a*p[0] for a,p in zip(dx,xy));xy1=sum(a*p[1] for a,p in zip(dx,xy))
                yx=sum(a*p[0] for a,p in zip(dy,xy));yy=sum(a*p[1] for a,p in zip(dy,xy))
                determinants.append(xx*yy-xy1*yx)
    return {'minimum_quadrature_jacobian':min(determinants),'max_edge_length_ratio':max_ratio,
            'positive_jacobians_pass':min(determinants)>0,'edge_ratio_le_5_pass':max_ratio<=5}


def validate_uel_properties(path, nphys):
    """Reject a semantically wrong deck even when Abaqus datacheck accepts it."""
    lines=Path(path).read_text().splitlines()
    cards=[]
    for i,line in enumerate(lines):
        if line.strip().upper().startswith('*UEL PROPERTY'):
            cards.append([float(v) for v in lines[i+1].split(',') if v.strip()])
    expected=[.015,.0027,210.,.3,1e-7,float(nphys)]
    if not cards or any(len(c)!=6 or any(not math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-14)
                                         for x,y in zip(c,expected)) for c in cards):
        raise ValueError('UEL properties must match frozen source order l0,Gc,E,nu,k,N_PHYS: '+str(cards))


def write_json(path, value):
    temp = Path(str(path)+'.tmp')
    temp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    os.replace(temp, path)


class LocalRunner:
    def __init__(self, api, run_dir, cpus=1, max_cycles=7, donor_checkpoint=None):
        self.api = api
        self.run = Path(run_dir).resolve()
        self.run.mkdir(parents=True, exist_ok=True)
        self.cpus = cpus
        self.max_cycles = max_cycles
        self.abaqus = shutil.which('abaqus') or r'C:\SIMULIA\Commands\abaqus.bat'
        self.transfer = load_transfer()
        self.watch = api.StallWatchdog()
        self.published = []
        self.peak = 0.
        self.tips = []
        self.donor_checkpoint = Path(donor_checkpoint).resolve() if donor_checkpoint else None

    def command(self, args, name, solver=False, timeout=300):
        log = self.run/(name+'_command.log')
        if log.exists():
            raise RuntimeError('Preserving existing command evidence: '+str(log))
        started = time.time()
        if solver:
            self.watch.start_cycle()
        with log.open('w') as stream:
            p = subprocess.Popen(args, cwd=self.run, stdin=subprocess.DEVNULL,
                                 stdout=stream, stderr=subprocess.STDOUT)
            while p.poll() is None:
                time.sleep(5)
                if solver:
                    stalled, reason, details = self.watch.check_simulation_stall(str(self.run/(name+'.sta')))
                    if stalled:
                        write_json(self.run/(name+'_blocker.json'),
                                   {'reason': reason, 'details': details, 'pid': p.pid,
                                    'retry': False, 'master_goal_status': 'OPEN'})
                        subprocess.run([self.abaqus, 'terminate', 'job='+name], cwd=self.run,
                                       stdin=subprocess.DEVNULL, stdout=stream, stderr=stream, timeout=30)
                        raise RuntimeError('Stall preserved; guarded bridge review required: '+reason)
                elif time.time()-started > timeout:
                    p.terminate()
                    raise RuntimeError('Preparation subprocess timed out: '+name)
        if p.returncode:
            raise RuntimeError('Command failed; preserved '+str(log))
        return time.time()-started

    def extract(self, job):
        # Only companion UMAT fields are used. Their element labels map to
        # physical IDs by the validated N_PHYS offset convention.
        script = self.run/(job+'_extract.py')
        target = self.run/(job+'_fields.json')
        code = '''import odbAccess,json,sys
odb=odbAccess.openOdb(sys.argv[1],readOnly=True)
inst=list(odb.rootAssembly.instances.values())[0]
nphys=len(inst.elements)//3
def state(frame):
 dgp={};hgp={};energies={}
 for v in frame.fieldOutputs['SDV1'].values:
  dgp.setdefault((v.elementLabel-1)%nphys+1,[]).append(float(v.data))
 for v in frame.fieldOutputs['SDV2'].values:
  hgp[str((v.elementLabel-1)%nphys+1)+'_'+str(v.integrationPoint)]=float(v.data)
 for key in ['SDV17','SDV18']:
  if key in frame.fieldOutputs:
   by={}
   for v in frame.fieldOutputs[key].values:by[v.elementLabel]=float(v.data)
   energies[key]=sum(by.values())
 nd={}
 for e in inst.elements:
  eid=(e.label-1)%nphys+1
  if eid in dgp:
   d=sum(dgp[eid])/len(dgp[eid])
   for n in e.connectivity:nd.setdefault(n,[]).append(d)
 damage={str(n):sum(v)/len(v) for n,v in nd.items()}
 def rp(key):
  vals=[v for v in frame.fieldOutputs[key].values if v.nodeLabel==999999]
  if len(vals)!=1:raise ValueError('Missing or ambiguous RP '+key)
  return float(vals[0].data[0])
 return dict(damage=damage,history=hgp,u1=rp('U'),rf1=rp('RF'),energies=energies,
             step_frame=frame.incrementNumber,frame_time=frame.frameValue)
steps=list(odb.steps.values())
result={'hold':state(steps[0].frames[-1]),'terminal':state(steps[-1].frames[-1]),
        'steps':[s.name for s in steps]}
result['peak_rf1']=max(abs(float(v.data[0])) for s in steps for f in s.frames
 for v in f.fieldOutputs['RF'].values if v.nodeLabel==999999 and f.incrementNumber>0)
with open(sys.argv[2],'w') as f:json.dump(result,f)
odb.close()
'''
        script.write_text(code, encoding='utf-8')
        self.command([self.abaqus, 'python', str(script), str(self.run/(job+'.odb')), str(target)], job+'_extract', timeout=300)
        return json.loads(target.read_text())

    def plot(self, job, mesh, fields, summary):
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.collections import PolyCollection
        from matplotlib.tri import Triangulation
        import numpy as np
        nodes, quads, tris, _ = mesh
        ids = sorted(nodes)
        ix = {n:i for i,n in enumerate(ids)}
        xy = np.array([nodes[n] for n in ids])
        polygons = [xy[[ix[n] for n in e]] for e in list(quads.values())+list(tris.values())]
        triangles = []
        for e in list(quads.values())+list(tris.values()):
            q = [ix[n] for n in e]
            triangles.append(q[:3])
            if len(q)==4:
                triangles.append([q[0],q[2],q[3]])
        d = [fields['damage'][str(n)] for n in ids]
        fig, (a,b) = plt.subplots(1,2,figsize=(12,5.5),layout='constrained')
        a.add_collection(PolyCollection(polygons,facecolors='white',edgecolors='#435568',linewidths=.18))
        a.set_title('Mesh | '+str(len(polygons))+' elements')
        im=b.tripcolor(Triangulation(xy[:,0],xy[:,1],np.array(triangles)),d,cmap='inferno',vmin=0,vmax=1,shading='gouraud')
        b.set_title('Spatial damage (averaged companion SDV1)')
        fig.colorbar(im,ax=b,label='Damage d')
        for ax in (a,b):
            ax.set(xlim=(-.02,1.02),ylim=(-.02,1.02),xlabel='x [mm]',ylabel='y [mm]')
            ax.set_aspect('equal')
        fig.suptitle('Frozen-UEL shear demonstration | Cycle %d | u1=%.6f mm\n%s' %
                     (summary['cycle'],summary['terminal_u1_mm'],summary['status']))
        image=self.run/(job+'_mesh_damage.png')
        fig.savefig(image,dpi=180)
        plt.close(fig)
        return image

    def publish(self, job, summary, mesh, image):
        folder=HERE/'local_windows_full_run'
        folder.mkdir(exist_ok=True)
        files=[]
        for path in (self.run/(job+'_SUMMARY.json'),self.run/(job+'.sta'),
                     self.run/(job+'.dat'),self.run/(job+'.inp'),mesh,image):
            dest=folder/path.name
            if dest.exists():
                raise RuntimeError('Preserving existing published evidence: '+str(dest))
            shutil.copy2(path,dest)
            files.append(str(dest.relative_to(ROOT)))
        index=subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT,stdin=subprocess.DEVNULL)
        if index.returncode:
            raise RuntimeError('Pre-existing staged changes preserved; reconcile before evidence commit')
        subprocess.run(['git','add','-f','--']+files,cwd=ROOT,stdin=subprocess.DEVNULL,check=True)
        subprocess.run(['git','commit','-m','feat(mode2): record audited shear demonstration cycle '+str(summary['cycle'])],
                       cwd=ROOT,stdin=subprocess.DEVNULL,check=True)
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,stdin=subprocess.DEVNULL,text=True).strip()
        relative=str((folder/image.name).relative_to(ROOT)).replace('\\','/')
        subprocess.run(['git','cat-file','-e',commit+':'+relative],cwd=ROOT,stdin=subprocess.DEVNULL,check=True)
        manifest=folder/'image_manifest.json'
        entries=json.loads(manifest.read_text()) if manifest.exists() else []
        entries.append({'cycle':summary['cycle'],'u1_mm':summary['terminal_u1_mm'],
            'path':relative,'commit':commit,'image_sha256':self.api.compute_sha256(image),
            'url':'https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/'+commit+'/'+relative,
            'mesh_sha256':summary['mesh_sha256'],'source_sha256':summary['source_sha256']})
        write_json(manifest,entries)
        subprocess.run(['git','add','--',str(manifest.relative_to(ROOT))],cwd=ROOT,stdin=subprocess.DEVNULL,check=True)
        subprocess.run(['git','commit','-m','docs(mode2): pin cycle image provenance'],cwd=ROOT,stdin=subprocess.DEVNULL,check=True)
        # A failed push stops the sequence; no later cycle can hide unsynced evidence.
        subprocess.run(['git','push','origin','main'],cwd=ROOT,stdin=subprocess.DEVNULL,check=True,timeout=120)
        self.watch.record_agent_progress()

    def execute(self):
        lock=self.run/'execution_state.json'
        if lock.exists():
            raise RuntimeError('Existing run requires checkpoint reconciliation, never an automatic retry: '+str(lock))
        write_json(lock,{'active':True,'pid':os.getpid(),'started_at':time.time(),'max_cycles':self.max_cycles,
                         'cpus':self.cpus,'pbs_submissions':0,'formulation':'frozen UEL, not Miehe spectral'})
        source=ROOT/'models/pandey_kumar_mode1/f42_mixed_uel.for'
        if self.api.compute_sha256(source)!=self.api.FROZEN_UEL_SHA256:
            raise RuntimeError('Frozen source mismatch')
        shutil.copy2(source,self.run/source.name)
        donor=None
        donor_mesh=None
        first_cycle=0
        if self.donor_checkpoint:
            checkpoint=json.loads(self.donor_checkpoint.read_text())
            previous=checkpoint['summary']
            phys=Path(checkpoint['mesh_path'])
            previous_input=Path(checkpoint['odb_path']).with_suffix('.inp')
            sta=Path(checkpoint['odb_path']).with_suffix('.sta')
            if (previous['source_sha256'] != self.api.FROZEN_UEL_SHA256 or
                previous['status'] != 'CONVERGED_AUDITED' or
                self.api.compute_sha256(phys) != previous['mesh_sha256'] or
                self.api.compute_sha256(previous_input) != previous['input_sha256'] or
                'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' not in sta.read_text(errors='replace')):
                raise RuntimeError('Donor evidence, hash or convergence mismatch; refusing resume')
            donor=checkpoint['fields']['terminal']
            donor_mesh=self.api.parse_physical_mesh(str(phys))
            self.peak=previous['peak_rf1_kn']
            self.tips=checkpoint.get('tip_history', [previous['tip_mm']] if previous['cycle']==0 else [])
            if not self.tips:
                raise RuntimeError('Historical tip path missing; cannot invent resumed arc length')
            first_cycle=previous['cycle']+1
            write_json(self.run/'donor_receipt.json',{'checkpoint':str(self.donor_checkpoint),
                'sha256':self.api.compute_sha256(self.donor_checkpoint),'cycle':previous['cycle'],
                'cutoff':{'increment':donor['step_frame'],'frame_time':donor['frame_time']}})
        if first_cycle>self.max_cycles:
            raise ValueError('Cycle cap precedes the supplied donor; no run started')
        for cycle in range(first_cycle,self.max_cycles+1):
            stalled,reason,details=self.watch.check_agent_stall()
            if stalled:
                raise RuntimeError('Agent progress guard: '+reason+'; '+details)
            job='PK_METHOD_C_MODE2_COARSE_JOB1' if cycle==0 else 'PK_METHOD_C_MODE2_CYCLE%d'%cycle
            inp=self.run/(job+'.inp')
            phys=self.run/(job+'_PHYS.inp')
            if cycle==0:
                shutil.copy2(HERE/'PK_METHOD_C_MODE2_COARSE_JOB1.inp',inp)
                shutil.copy2(HERE/'PK_METHOD_C_MODE2_COARSE_PHYS.inp',phys)
            else:
                self.command([self.abaqus,'cae','noGUI='+str(HERE/'generate_mode2_adaptive_corridor_mesh.py'),
                              '--',str(phys),str(self.tips[-1][0]),str(self.tips[-1][1])],job+'_mesh',timeout=600)
                if not phys.exists():
                    raise RuntimeError('Mesh generator did not create expected file')
            mesh=self.api.parse_physical_mesh(str(phys))
            nodes,quads,tris,_=mesh
            if not nodes or not quads or len(quads)+len(tris)>=35000:
                raise RuntimeError('Mesh missing or outside bounded element scope')
            qa=geometry_audit(nodes,{**quads,**tris})
            if not qa['positive_jacobians_pass'] or not qa['edge_ratio_le_5_pass']:
                write_json(self.run/(job+'_mesh_audit.json'),qa)
                raise RuntimeError('Physical mesh Jacobian or edge ratio failed')
            if cycle:
                from generate_mode2_adaptive_corridor_mesh import evaluate_corridor_audit
                audit=evaluate_corridor_audit(nodes,{**quads,**tris},
                    {**{e:'QUAD' for e in quads},**{e:'TRI' for e in tris}},
                    tip_x=self.tips[-1][0],tip_y=self.tips[-1][1])
                audit.update(qa)
                write_json(self.run/(job+'_mesh_audit.json'),audit)
                if not all(audit['gates'].values()):
                    raise RuntimeError('Receiver mesh quality audit failed')
            if cycle:
                dn,dq,dt,_=donor_mesh
                d={int(n):v for n,v in donor['damage'].items()}
                h={tuple(map(int,k.split('_'))):v for k,v in donor['history'].items()}
                rd,rh=self.transfer(dn,dq,dt,d,h,nodes,quads,tris)
                self.api.assemble_mode2_coupled_deck(str(inp),nodes,quads,tris,donor['u1'],
                    min(.0200,donor['u1']+.0015),rd,rh)
            validate_uel_properties(inp,len(quads)+len(tris))
            self.command([self.abaqus,'job='+job+'_DATACHECK','input='+job,'user='+source.name,
                          'cpus='+str(self.cpus),'datacheck','interactive'],job+'_DATACHECK',timeout=600)
            elapsed=self.command([self.abaqus,'job='+job,'input='+job,'user='+source.name,
                                  'cpus='+str(self.cpus),'interactive'],job,solver=True)
            sta=self.run/(job+'.sta')
            if not sta.exists() or 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' not in sta.read_text(errors='replace'):
                raise RuntimeError('Solve incomplete; do not treat partial frame as completed cycle')
            fields=self.extract(job)
            terminal=fields['terminal']
            tip,boundary=connected_tip(nodes,{**quads,**tris},{int(n):v for n,v in terminal['damage'].items()})
            self.tips.append(tip)
            self.peak=max(self.peak,fields['peak_rf1'])
            max_damage=max(terminal['damage'].values())
            gates={}
            if cycle:
                if abs(donor['rf1'])<1e-12:
                    raise RuntimeError('Cannot qualify relative force continuity against zero donor reaction')
                delta=100*(abs(fields['hold']['rf1'])-abs(donor['rf1']))/abs(donor['rf1'])
                gates={'force_continuity_delta_pct':delta,'force_continuity_pass':abs(delta)<=5.,
                       'global_max_damage_nonhealing_pass':max_damage>=max(donor['damage'].values())-1e-4,
                       'evaluation_timing':'after two-step job; failure forbids donor acceptance and further cycles',
                       'hold_energies':fields['hold']['energies'],'donor_energies':donor['energies']}
            accepted=not cycle or (gates['force_continuity_pass'] and gates['global_max_damage_nonhealing_pass'])
            done,reason=completion(self.peak,terminal['rf1'],boundary)
            summary={'cycle':cycle,'job_name':job,'status':'CONVERGED_AUDITED' if accepted else 'TRANSFER_GATE_FAILED',
                     'formulation':'Frozen UEL shear demonstration; not Miehe spectral reproduction',
                     'donor_u1_mm':donor['u1'] if cycle else 0.,'terminal_u1_mm':terminal['u1'],
                     'terminal_rf1_kn':terminal['rf1'],'peak_rf1_kn':self.peak,'tip_mm':tip,
                     'tip_history_chord_sum_mm':self.api.compute_cumulative_crack_arc_length(self.tips),
                     'max_damage':max_damage,'mesh_elements':len(quads)+len(tris),'mesh_nodes':len(nodes),
                     'gate_results':gates,'elapsed_seconds':elapsed,'completion':done and accepted,
                     'completion_reason':reason if accepted else 'TRANSFER_GATE_FAILED',
                     'input_sha256':self.api.compute_sha256(inp),'mesh_sha256':self.api.compute_sha256(phys),
                     'source_sha256':self.api.FROZEN_UEL_SHA256,'donor_cutoff':
                     {'frame':donor['step_frame'],'time':donor['frame_time']} if cycle else None,
                     'pbs_submissions':0,'cumulative_pbs_submissions':73}
            summary['transfer_implementation_sha256']=self.api.compute_sha256(
                ROOT/'models/pandey_kumar_mode1/291_method_c_case1/case1_single_job_orchestrator.py')
            summary['transfer_implementation']='Unchanged Case 1 spatial nearest-neighbour damage/history transfer'
            summary['donor_checkpoint_sha256']=self.api.compute_sha256(self.donor_checkpoint) if self.donor_checkpoint else None
            write_json(self.run/(job+'_SUMMARY.json'),summary)
            write_json(self.run/(job+'_checkpoint.json'),{'summary':summary,'fields':fields,
                       'mesh_path':str(phys),'odb_path':str(self.run/(job+'.odb')),
                       'tip_history':self.tips})
            image=self.plot(job,mesh,terminal,summary)
            self.publish(job,summary,phys,image)
            if not accepted:
                raise RuntimeError('Scientific transfer gate failed; preserved cycle requires independent review')
            if done:
                write_json(lock,{'active':False,'completed':True,'last_cycle':cycle,'reason':reason})
                return summary
            donor,donor_mesh=terminal,mesh
        write_json(lock,{'active':False,'completed':False,'last_cycle':self.max_cycles,
                         'reason':'COARSE_QUALIFICATION_COMPLETE' if self.max_cycles==0 else
                         'BOUNDED_CYCLE_CAP_REACHED; independent review required'})
        return summary
