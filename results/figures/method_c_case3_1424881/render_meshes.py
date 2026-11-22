"""Render preserved PBS 1424881 physical meshes; no solver or remote writes."""
import base64, hashlib, json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
ROOT=Path(__file__).resolve().parent
acquired=json.loads(Path('.git/acquired.json').read_bytes())
records={r['name']:r for r in acquired}
sha=lambda b:hashlib.sha256(b).hexdigest()
meshes=[]
for k in range(1,8):
    name=f'PK_METHOD_C_CASE3_CYCLE{k}_PHYS.inp'
    r=records[name]; data=base64.b64decode(r['data']); assert sha(data)==r['sha256']
    nodes={}; elements={}; mode=None; types={}
    for line in data.decode().splitlines():
        line=line.strip()
        if not line or line.startswith('**'): continue
        if line.startswith('*'):
            mode=line.split(',')[0].upper()
            if mode=='*ELEMENT': et=line.upper().split('TYPE=')[1].split(',')[0]
            continue
        v=[x.strip() for x in line.split(',') if x.strip()]
        if mode=='*NODE':
            label=int(v[0]); assert label not in nodes; nodes[label]=tuple(map(float,v[1:3]))
        elif mode=='*ELEMENT':
            label=int(v[0]); assert label not in elements; elements[label]=list(map(int,v[1:])); types[et]=types.get(et,0)+1
    edges=set()
    for conn in elements.values():
        assert len(conn) in (3,4), len(conn)
        for a,b in zip(conn,conn[1:]+conn[:1]): edges.add(tuple(sorted((a,b))))
    segments=np.array([[nodes[a],nodes[b]] for a,b in sorted(edges)])
    state_name=f'PK_METHOD_C_CASE3_CYCLE{k}_state.json'; sr=records[state_name]
    state=json.loads(base64.b64decode(sr['data'])) if sr['exists'] else None
    meshes.append(dict(cycle=k,nodes=len(nodes),element_count=len(elements),element_types=types,segments=segments,source=name,source_sha256=r['sha256'],source_mtime_ns=r['mtime_ns'],state=state,state_name=state_name,state_sha256=sr['sha256']))
allxy=np.concatenate([m['segments'].reshape(-1,2) for m in meshes]); low=allxy.min(axis=0); high=allxy.max(axis=0)
full=[float(low[0]-2),float(high[0]+2),float(low[1]-2),float(high[1]+2)]
manifest={'protocol':'INDEPENDENT_STRUCTURED_REVIEW_V1','goal':'METHOD-C-CASE3-RENDER-1424881-CYCLE-MESHES','master_goal_status':'OPEN','new_pbs_jobs':0,'cumulative_pbs_submissions':71,'scratch_access':'read-only; source bytes and mtime checked before/after','full_view_bounds_mm':full,'zoom_half_width_mm':4,'zoom_half_height_mm':4,'files':[],'cycles':[],'limitations':['CYCLE7_state.json missing: no authentic Cycle 7 tip zoom can be rendered.','Deck element counts differ from the user-provided counts; parsed deck counts are authoritative.','Images show mesh geometry, not damage or proof of convergence/propagation.']}
def draw(ax,m,zoom=False):
    if zoom and m['state'] is None:
        ax.text(.5,.5,'Cycle 7 tip zoom unavailable\nMatching CYCLE7_state.json missing\nNo crack-tip position inferred',ha='center',va='center',transform=ax.transAxes); ax.set_axis_off(); return
    ax.add_collection(LineCollection(m['segments'],colors='#263b4a',linewidths=.24 if not zoom else .55,rasterized=True))
    bounds=full
    if zoom:
        x=float(m['state']['tip_x']); bounds=[x-4,x+4,66,74]; ax.plot(x,70,'+',color='#dc5028',ms=10,mew=1.5); ax.set_title(f"Cycle {m['cycle']} | tip x={x:.4f} mm, y=70 mm",fontsize=10)
    else: ax.set_title(f"Cycle {m['cycle']} | {m['element_count']:,} elements",fontsize=11)
    ax.set_xlim(bounds[:2]); ax.set_ylim(bounds[2:]); ax.set_aspect('equal'); ax.set_xlabel('x [mm]'); ax.set_ylabel('y [mm]')
def save(fig,name,m=None,kind=None):
    p=ROOT/name; fig.savefig(p,dpi=220,facecolor='white'); plt.close(fig)
    manifest['files'].append({'path':p.relative_to(Path.cwd()).as_posix(),'sha256':sha(p.read_bytes()),'cycle':m['cycle'] if m else None,'element_count_in_source':m['element_count'] if m else [x['element_count'] for x in meshes],'view':kind,'status':'MISSING_STATE_PLACEHOLDER' if m and kind=='tip_zoom' and m['state'] is None else 'RENDERED','note':'Full view draws every element edge; zoom clips the same mesh to the viewport.'})
for m in meshes:
    for zoom in (False,True):
        fig,ax=plt.subplots(figsize=(7,8) if not zoom else (7,7)); draw(ax,m,zoom); fig.tight_layout(); save(fig,f"cycle_{m['cycle']:02d}_{'tip_zoom' if zoom else 'full'}.png",m,'tip_zoom' if zoom else 'full')
    manifest['cycles'].append({key:value for key,value in m.items() if key not in ('segments','state')} | {'tip_x_mm':m['state']['tip_x'] if m['state'] else None,'zoom_y_mm':70,'state_status':'PRESENT' if m['state'] else 'MISSING'})
fig,axs=plt.subplots(2,4,figsize=(20,12))
for ax,m in zip(axs.flat,meshes): draw(ax,m)
axs.flat[-1].axis('off'); axs.flat[-1].text(.05,.7,'PBS 1424881 physical meshes\nCommon framing and scale\nCounts parsed from *ELEMENT records\nCycle 7 state file missing\nMesh views do not show damage',transform=axs.flat[-1].transAxes,fontsize=14,va='top')
fig.tight_layout(); save(fig,'seven_cycle_overview.png',kind='overview')
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'counts':[m['element_count'] for m in meshes],'tips':[m['state']['tip_x'] if m['state'] else None for m in meshes],'bounds':full,'images':len(manifest['files'])}))
