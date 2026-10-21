"""Render a standalone report from existing evidence, without solver execution."""
from pathlib import Path
import hashlib, json, sys, re
from xml.sax.saxutils import escape
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle
from PIL import Image as PILImage
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
FIG=OUT/'figures'; FIG.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'scripts/visualization'))
from plot_mode1_method_b_adaptive_mesh import parse_abaqus_mesh
plt.rcParams.update({'font.size':11,'axes.titlesize':12,'axes.labelsize':11,'legend.fontsize':9,'font.family':'DejaVu Sans'})
BLUE,GREEN,INK='#245773','#238579','#19354a'
sources=[]
def read_json(p):
    assert (ROOT/p).is_file(),p
    return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def save(fig,name,kind,paths,description):
    fig.savefig(FIG/name,dpi=220,bbox_inches='tight',facecolor='white'); plt.close(fig)
    for p in paths: assert (ROOT/p).is_file(),p
    sources.append((name,kind,paths,description))

ref_path='results/pandey_kumar_mode1/master_fracture_curves/curve_standard_1398090.csv'
base='models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k'
corr_path=base+'/evidence_1412465/corrected_method_b_load_displacement.csv'
eval_path=base+'/evidence_1412465/corrected_method_b_evaluation.json'
evaluation=read_json(eval_path)
for p in (ref_path,corr_path): assert (ROOT/p).is_file(),p
ref,corr=pd.read_csv(ROOT/ref_path),pd.read_csv(ROOT/corr_path)
horizon=float(corr.u_mm.max())
assert abs(horizon-.007889)<1e-10
assert evaluation['mesh_refinement_audit']['total_finite_elements']==14483
def matched(frame,xcol,ycol):
    x,y=frame[xcol].to_numpy(),frame[ycol].to_numpy()
    assert np.all(np.diff(x)>=0) and x[0]<=horizon<=x[-1]
    xx,yy=x[x<=horizon],y[x<=horizon]
    if xx[-1]<horizon:
        xx=np.r_[xx,horizon]; yy=np.r_[yy,np.interp(horizon,x,y)]
    # Established evaluation convention: work zero at first recorded row.
    w=np.r_[0.,np.cumsum((yy[1:]+yy[:-1])*.5*np.diff(xx))]*1000
    return xx,yy,w
xr,yr,wr=matched(ref,'u2_mm','rf2_kN'); xc,yc,wc=matched(corr,'u_mm','f_kN')
work_error=(wc[-1]/wr[-1]-1)*100
assert abs(wc[-1]-2.267379222)<1e-8
assert abs(wr[-1]-2.358732)<2e-5
assert abs(work_error+3.87)<.01
assert abs(yc.max()*1000-743.70082)<.001
fig,axs=plt.subplots(1,2,figsize=(10.2,4.6),layout='constrained')
for x,y,w,label,color in [(xr,yr,wr,'Fixed reference | 15,192 FE',INK),(xc,yc,wc,'Corrected Method B | 14,483 FE',GREEN)]:
    axs[0].plot(x*1000,y*1000,label=label,color=color,lw=2)
    axs[1].plot(x*1000,w,label=label,color=color,lw=2)
for ax in axs:
    ax.set_xlim(0,horizon*1000); ax.set_xlabel('Applied displacement [micrometres]'); ax.grid(alpha=.18); ax.legend(loc='upper left',fontsize=11)
axs[0].set(ylabel='Reaction force [N]',ylim=(0,950),title='Final force-displacement response')
axs[1].set(ylabel='Cumulative external work [mJ]',ylim=(0,3),title='Same integration horizon for both curves')
axs[1].text(.04,.60,f'At u = 7.889 micrometres\nMethod B: {wc[-1]:.4f} mJ\nReference: {wr[-1]:.4f} mJ\nDifference: {work_error:.2f}%',transform=axs[1].transAxes,fontsize=12,bbox=dict(facecolor='white',edgecolor='#ccd7df',boxstyle='round,pad=.5'))
fig.suptitle('AUTHENTIC SOLVER OUTPUTS | matched horizon: 0 to 0.007889 mm',fontsize=12)
save(fig,'method_b_response.png','AUTHENTIC simulation outputs',[ref_path,corr_path,eval_path],
     'Figure 1. Only corrected Method B and canonical fixed reference. Both end at 0.007889 mm. Reference endpoint is interpolated within its recorded range, not extrapolated. Work uses trapezoidal integration of kN versus mm multiplied by 1000 to mJ. Zero is at the first recorded row, u=0.0000025 mm, matching the established evaluation convention. Reintegrated work: %.9f versus %.9f mJ (%.5f%%). Prior summary reference 2.3586 mJ differs by about 0.0001 mJ; the CSV value rounds to 2.3587 mJ.'%(wc[-1],wr[-1],work_error))

partition_result_path='runs/mode1/method_b_inf_companion/inf_companion_method_b_results.json'
partition_result=read_json(partition_result_path)
partition_manifest_path='models/pandey_kumar_mode1/method_b_preflight_manifest.json'
partition_manifest=read_json(partition_manifest_path)['primary_matrix']['configurations']
decision_path='docs/decisions/SUPERVISOR_DECISION_METHOD_B_MODE1_LOAD_PARTITIONING.md'
deck_paths=[f'models/pandey_kumar_mode1/method_b_inf_companion_decks/M1_MB_INF_{n}S.inp' for n in (1,2,4)]
wrapper_paths=[f'runs/mode1/method_b_inf_companion/{i:02d}_pre_{n}s/submit_M1_PRE_INF_{n}S.pbs' for i,n in enumerate((1,2,4),1)]
schedules=[]
for n,p,wrapper in zip((1,2,4),deck_paths,wrapper_paths):
    assert (ROOT/p).is_file() and (ROOT/wrapper).is_file()
    deck=(ROOT/p).read_text(); assert '*AMPLITUDE' not in deck.upper()
    assert Path(p).name in (ROOT/wrapper).read_text()
    blocks=re.findall(r'^\*STEP\s*,([^\n]*)\n(.*?)^\*END STEP',deck,re.I|re.M|re.S)
    assert len(blocks)==n
    steps=[]; t=0.; prev_u=0.
    for header,block in blocks:
        name=re.search(r'NAME=([^,\s]+)',header,re.I).group(1)
        static=re.search(r'^\*STATIC\s*\n([^\n]+)',block,re.I|re.M).group(1)
        dt,duration,dt_min,dt_max=[float(s) for s in static.split(',')]
        end_u=float(re.search(r'^N_RP\s*,\s*2\s*,\s*2\s*,\s*([\d.Ee+-]+)',block,re.M).group(1))
        assert re.search(r'^\*OUTPUT, FIELD, FREQUENCY=1',block,re.I|re.M)
        assert 'MISESERI, MISESAVG' in block and 'AMPLITUDE=' not in block.upper()
        nominal=int(round(duration/dt_max))
        assert abs((end_u-prev_u)*dt_max/duration-1e-5)<1e-12
        steps.append(dict(name=name,start_time=t,end_time=t+duration,start_u_mm=prev_u,end_u_mm=end_u,dt_initial=dt,dt_max=dt_max,nominal_increments=nominal,field_frequency=1))
        t+=duration; prev_u=end_u
    config=partition_manifest[f'M1-MB-{n}S']
    assert config['remesh_target_step']==steps[-1]['name'] and config['remesh_frame_rule']=='LAST_INCREMENT'
    assert abs(prev_u-.005)<1e-12
    archived=partition_result['extraction'][f'{n}S']; native=partition_result['native_remeshing'][f'{n}S']
    assert abs(archived['u2']-prev_u)<1e-8 and native['adapted_element_count']==14677
    assert native['status']=='SUCCESS'
    schedules.append(dict(partitions=n,deck=p,steps=steps,total_step_time=t,endpoint_u_mm=prev_u,indicator_step=steps[-1]['name'],indicator_frame_rule='LAST_INCREMENT',indicator_nominal_increment=steps[-1]['nominal_increments'],remesh_count=1,native_elements=14677))
assert partition_result['error_field_comparison']['max_diff_1s_2s']==0
assert partition_result['error_field_comparison']['max_diff_1s_4s']==0
assert partition_result['mesh_topology_comparison']['step_partition_mesh_invariance_verified']

fig,ax=plt.subplots(figsize=(10.2,2.7)); ax.set(xlim=(0,1),ylim=(0,1)); ax.axis('off')
for row,label,text in [(0,'A','One preliminary\nsimulation'),(1,'B','Pre-analysis split\ninto 1 / 2 / 4 steps')]:
    y=.72-row*.40
    ax.text(.02,y,label,ha='center',va='center',fontsize=14,fontweight='bold',color=BLUE)
    labels=[text,'Select / evaluate\nMISESERI field','One native\nadaptive remesh','Fresh final solve\nfrom zero load']
    for i,txt in enumerate(labels):
        x=.16+i*.235
        ax.add_patch(Rectangle((x-.102,y-.135),.204,.27,facecolor='#e7eff4' if not row else '#deefe9',edgecolor=BLUE,lw=1))
        ax.text(x,y,txt,ha='center',va='center',fontsize=11,linespacing=1.1)
        if i<3: ax.annotate('',xy=(x+.130,y),xytext=(x+.105,y),arrowprops=dict(arrowstyle='->',color=BLUE,lw=1.5))
ax.text(.5,.04,'CONCEPTUAL A/B COMPARISON | both: one remesh, two passes, no loaded-state transfer',ha='center',fontsize=11,color=BLUE)
save(fig,'method_b_workflow.png','CONCEPTUAL method explanation',[decision_path,'docs/methods/MODE1_LOAD_PARTITION_EXPERIMENT_SPECIFICATION.md'],
     'A and B share one-remesh/two-pass architecture. B parameterizes preliminary loading and field selection; it is not sequential adaptation. The 1-step B case reduces to the same architecture as A at the same controls.')

fig,axs=plt.subplots(3,1,figsize=(10.2,5.4)); fig.subplots_adjust(left=.09,right=.73,top=.89,bottom=.1,hspace=.65)
for ax,schedule in zip(axs,schedules):
    n=schedule['partitions']
    for step in schedule['steps']:
        ax.plot([step['start_time'],step['end_time']],[step['start_u_mm']*1000,step['end_u_mm']*1000],color=BLUE,lw=2)
        ax.axvline(step['end_time'],ls=':',color='#839aaa',lw=1)
        ax.text((step['start_time']+step['end_time'])/2,5.5,step['name'],ha='center',fontsize=10)
        ax.plot(step['end_time'],step['end_u_mm']*1000,'o',color=BLUE,ms=3)
        label_offset=(-4,-14) if step is schedule['steps'][-1] else (-4,6)
        ax.annotate(f"{step['end_u_mm']:.5f} mm",(step['end_time'],step['end_u_mm']*1000),xytext=label_offset,textcoords='offset points',ha='right',fontsize=10)
    ax.plot(schedule['total_step_time'],5,'*',color=GREEN,ms=12,clip_on=False)
    ax.set(xlim=(0,n),ylim=(0,6.5),xticks=list(range(n+1)),yticks=[0,2.5,5],ylabel=f'{n}-step\nu [micrometres]')
    ax.tick_params(labelsize=10); ax.grid(axis='y',alpha=.15)
    ax.text(1.04,.72,f"Select {schedule['indicator_step']}, last frame\ninc {schedule['indicator_nominal_increment']} at u = 0.005 mm",transform=ax.transAxes,fontsize=10,color=GREEN,va='center')
    ax.text(1.04,.13,'Then ONE native remesh\n(no remesh at earlier boundaries)',transform=ax.transAxes,fontsize=9,va='center')
    ax.set_xlabel('Accumulated Abaqus static step-time [model units]',fontsize=10)
fig.suptitle('VERIFIED DECK-DERIVED LOADING SCHEDULES | 1 / 2 / 4 partitions',fontsize=13)
save(fig,'method_b_loading_schedules.png','VERIFIED DECK-DERIVED diagram, not measured solver history',deck_paths+wrapper_paths+[partition_manifest_path,partition_result_path,decision_path],
     'Figure 3. Prescribed RP-U2 ramps reconstructed by parsing actual infinitesimal-companion execution decks. Each step duration is 1; accumulated step-times total 1, 2 and 4. End displacements are absolute BC values, not increments to add. Equal displacement partitions are verified, not assumed. Field output is every increment; remesh selection is the last frame of Step-1/2/4 at u=0.005 mm. Increment labels 500/250/125 follow deck time controls and archived zero-cutback completion. Remeshing occurs once after selection. Static pseudo-time is not walltime. Manifest supplies selection rule; archived result supplies endpoint/field comparison; no ODB is opened or new solver execution claimed.')

coarse_path='models/pandey_kumar_mode1/method_b_preflight_decks/M1-MB-1S.inp'
corrected_mesh_path=base+'/M1_MB_CORRECTED_PROPAGATION_14K.inp'
def mesh(ax,p,title,zoom=None):
    assert (ROOT/p).is_file(),p
    nodes,quads,tris=parse_abaqus_mesh(ROOT/p)
    polys=[[nodes[n] for n in ns] for _,ns in quads+tris]
    ax.add_collection(PolyCollection(polys,facecolors='none',edgecolors=BLUE,linewidths=.26))
    ax.autoscale(); ax.set_aspect('equal'); ax.set_title(title,fontsize=11); ax.set_xlabel('x [mm]'); ax.set_ylabel('y [mm]'); ax.tick_params(labelsize=10)
    if zoom: ax.set_xlim(*zoom[:2]); ax.set_ylim(*zoom[2:])
    return len(nodes),len(quads)+len(tris)
native_mesh_path='models/pandey_kumar_mode1/38_method_b_native_final_14k/M1_MB_NATIVE_FINAL_1S.inp'
fig,axs=plt.subplots(2,2,figsize=(10.2,5.4),layout='constrained')
mesh(axs[0,0],coarse_path,'Coarse pre-analysis | 2,906 FE')
_,count=mesh(axs[0,1],native_mesh_path,'Automatically generated native\nMethod B mesh | 14,677 FE'); assert count==14677
mesh(axs[1,0],native_mesh_path,'Native B: actual crack-tip zoom',(.475,.54,.47,.53))
_,count=mesh(axs[1,1],corrected_mesh_path,'Separate retrospective mesh | 14,483 FE'); assert count==14483
fig.suptitle('AUTHENTIC INPUT GEOMETRY | native partition result and separate corrected mesh',fontsize=12)
save(fig,'mesh_artifacts.png','AUTHENTIC input-deck geometry',[coarse_path,native_mesh_path,corrected_mesh_path,partition_result_path],
     'Figure 2. Coarse mesh, automatically generated native Method B mesh (14,677 FE) and its tip zoom, plus separate retrospective 14,483-FE verification mesh. The native deck reconstructs the native adapted geometry in UEL layers. The retrospective mesh is not a consequence of choosing 1, 2 or 4 steps.')
fig,ax=plt.subplots(figsize=(6.5,4.5),layout='constrained'); mesh(ax,native_mesh_path,'Automatically generated native Method B: crack-tip mesh',(.475,.54,.47,.53))
save(fig,'native_crack_tip.png','AUTHENTIC input-deck geometry',[native_mesh_path],
     'Companion close-up of genuine native 14,677-FE Method B geometry. Separate from retrospective 14,483-FE verification mesh.')

method_c_sources=['docs/reports/MODE1_METHOD_C_CONTINUATION_ARCHITECTURE_VALIDATION.md','docs/reports/MODE1_METHOD_C_EXPERIMENTAL_PREFLIGHT_AND_GATE_6C_READINESS.md','docs/reports/MODE1_METHOD_C1_CONTINUATION_FEASIBILITY_AND_PLAN.md']
fig,axs=plt.subplots(5,2,figsize=(10.2,7.2))
fig.subplots_adjust(top=.84,bottom=.16,left=.04,right=.96,wspace=.22,hspace=.65)
def fine_box(ax,x0,x1,y0,y1,color=GREEN,fill='#c9e8dd'):
    if x1<=x0: return
    ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,facecolor=fill,edgecolor=color,lw=.8))
    for xx in np.arange(x0,x1,.035): ax.plot([xx,xx],[y0,y1],color=color,lw=.45)
    for yy in np.arange(y0,y1,.035): ax.plot([x0,x1],[yy,yy],color=color,lw=.45)
for i in range(5):
    tip=.35+.12*i
    for col in range(2):
        ax=axs[i,col]; ax.set(xlim=(0,1),ylim=(0,.35),aspect='equal'); ax.set_xticks([]); ax.set_yticks([])
        for xx in np.linspace(0,1,9): ax.axvline(xx,color='#b9ccd7',lw=.6)
        for yy in np.linspace(0,.35,4): ax.axhline(yy,color='#b9ccd7',lw=.6)
        if i and col==0:
            fine_box(ax,.28,tip+.10,.05,.30)
        elif i:
            # Coarsening is only a proposed option outside a protected damaged band.
            for y0,y1 in ((.05,.15),(.20,.30)):
                x0,x1=.28,tip-.14
                if x1>x0:
                    ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,facecolor='#f4dfb2',edgecolor='#ac7c34',lw=.8))
                    for xx in np.arange(x0,x1,.10): ax.plot([xx,xx],[y0,y1],color='#ac7c34',lw=.6)
            fine_box(ax,.28,tip-.14,.15,.20,color=BLUE,fill='#dce9ef')
            fine_box(ax,tip-.14,tip+.10,.05,.30)
        ax.plot([0,tip],[.175,.175],color=INK,lw=1.5)
        label='Step 0: initial' if not i else f'Step {i}: remesh cycle {i}'
        ax.set_title(label+' | CONCEPTUAL',fontsize=10,pad=3)
fig.suptitle('PLANNED METHOD C STRATEGIES | all panels conceptual',fontsize=14,color=INK,y=.985)
fig.text(.27,.91,'Method C1: forward refinement\nEarlier refined zones remain fine',ha='center',fontsize=12,color=BLUE)
fig.text(.75,.91,'Method C2: refinement + selective coarsening\nMoving active fine zone; damage band protected',ha='center',fontsize=12,color=BLUE)
fig.text(.5,.105,'Green: fine active/retained zones. Blue: protected damaged corridor.\nAmber: possible coarsening only where physical preservation is demonstrated.',ha='center',fontsize=11)
fig.text(.5,.045,'Schematic ligament strips: no physical dimensions, FE counts or accepted crack path.\nBoth strategies transfer u, d and committed H, re-equilibrate, and continue loading at every cycle.',ha='center',fontsize=10,color=BLUE)
save(fig,'method_c_planned_workflow.png','CONCEPTUAL C1/C2 strategy comparison and future mesh progression',method_c_sources,
     'Figure 4. Side-by-side Step 0 plus four proposed cycles for Method C1 (accumulating forward refinement) and Method C2 (moving active fine zone with conditional selective coarsening). Every strip and crack position is conceptual. The blue damaged corridor stays protected; amber regions illustrate potential coarsening outside it, not blanket coarsening of damaged wake or a qualified rule. No physical dimensions, counts, measured savings, cycle displacements or accepted solver trajectory are implied. Both strategies remain unqualified; coarsening is an additional proposed extension after a physically accepted refinement handoff.')

candidate_paths=['models/pandey_kumar_mode1/candidate_intermediate_mesh_c1.inp','models/pandey_kumar_mode1/candidate_crack_band_mesh_c2.inp']
fig,axs=plt.subplots(2,2,figsize=(9.5,5.6),layout='constrained')
for col,(p,label) in enumerate(zip(candidate_paths,['Intermediate receiver | 840 quads / 910 nodes','CB-2300 | 2,300 quads / 2,413 nodes'])):
    assert mesh(axs[0,col],p,label)==[(910,840),(2413,2300)][col]
    xy=np.array(list(parse_abaqus_mesh(ROOT/p)[0].values()))
    assert np.allclose(xy.min(axis=0),[0,0]) and np.allclose(xy.max(axis=0),[.1,.1])
    mesh(axs[1,col],p,'Actual crack tip at x = 0.040 mm',(.032,.056,.044,.056))
    for row in (0,1):
        axs[row,col].plot([0,.040],[.050,.050],color=INK,lw=1.8)
        axs[row,col].plot(.040,.050,'o',color=INK,ms=3)
fig.suptitle('AUTHENTIC OFFLINE RECEIVER MESHES | neither denotes a Method C strategy',fontsize=12)
save(fig,'candidate_c1_c2_meshes.png','AUTHENTIC input-deck geometry',candidate_paths+['scripts/remeshing/generate_crack_band_mesh.py','scripts/validation/evaluate_candidate_meshes.py'],
     'Figure 5. Actual intermediate 840-element receiver and crack-band receiver test mesh CB-2300 (formerly Candidate C2), with common-scale tip close-ups. Both are offline test meshes, not Method C1/C2 strategies. Slit y=0.050 mm ends at x=0.040 mm; dark line/dot mark input geometry, not a simulated evolving crack. Original input filenames and scientific identifiers are unchanged.')
cp='results/validation/mesh_convergence_prototype.json'; data=read_json(cp)['comparisons']
c1,c2=data['candidate_1_intermediate'],data['candidate_2_crack_band_resolved']
assert abs(c2['equilibrated_RF_N']-.3662)<1e-6 and c2['max_damage_healing']>0
fig,axs=plt.subplots(1,2,figsize=(9.5,2.6),layout='constrained')
for ax,key,title,limit in [(axs[0],'elastic_stiffness_discrepancy_pct','Elastic stiffness error [%]',5),(axs[1],'fracture_energy_discrepancy_pct','Mapped fracture-energy error [%]',2)]:
    vals=[c1[key],c2[key]]; ax.bar(['Receiver 840','CB-2300'],vals,color=[BLUE,GREEN]); ax.axhline(limit,color='#965137',ls='--',label=f'{limit}% acceptance limit')
    ax.set_title(title); ax.legend(fontsize=9,loc='upper right'); ax.set_ylim(-.5,limit*1.5)
    for i,v in enumerate(vals): ax.text(i,v+.10,f'{v:+.2f}%',ha='center',fontsize=11)
save(fig,'candidate_c2_passing_checks.png','AUTHENTIC offline numerical diagnostics',[cp,'scripts/validation/evaluate_candidate_meshes.py'],
     'Figure 6. Passing undamaged elastic-stiffness and mapped fracture-energy checks of offline receiver meshes. CB-2300 is the report-only alias of historical Candidate C2, not the Method C2 coarsening strategy. These checks are not damaged-state compliance or solver continuation conservation. Force and healing failures are retained.')

# Shared blocks keep Markdown and PDF claims identical.
pages=[[
('h1','Mode-I adaptive remeshing: validated results'),
('p','Technical progress report | 22 October 2026'),
('h2','1. Method A and Method B: what changes?'),
('p','Method A: one preliminary simulation, one native adaptive remesh, then a fresh final simulation from zero load. Method B extends that same two-pass approach by partitioning preliminary loading into configurable 1, 2 or 4 steps and selecting/evaluating the relevant MISESERI field before one remesh and a fresh final solve.'),
('p','B varies the loading schedule and field-selection opportunities. It does not preserve a loaded fracture state across meshes or perform multiple remeshing cycles. With one step and the same controls, its architecture reduces to Method A.'),
('img',('method_b_workflow.png','Conceptual A/B workflow. The shared architecture has two simulation passes and exactly one remesh; only the pre-analysis schedule and field-selection flexibility differ.',500)),
('img',('mesh_artifacts.png','Figure 2. Authentic coarse mesh, automatically generated native Method B mesh (14,677 FE) and tip zoom, and separate retrospectively corrected ligament-resolution verification mesh (14,483 FE). Partition choice did not cause the latter correction.',475)),
('note','Keep two findings separate: A - the partition study produced equivalent native 14,677-element meshes; B - a distinct retrospective ligament-resolution study evaluated the corrected 14,483-element fracture response.')
],[
('h1','2. Finding A: Method B loading-partition study'),
('p','The executed infinitesimal-companion decks prescribe cumulative RP displacements of 0.005 mm (1 step); 0.0025, 0.005 mm (2 steps); and 0.00125, 0.0025, 0.00375, 0.005 mm (4 steps). Equal divisions are verified from these decks, not assumed.'),
('img',('method_b_loading_schedules.png','Figure 3. Verified deck-derived prescribed histories, not measured solver curves. Each step lasts 1.0 static step-time unit; total times are 1, 2 and 4. Stars mark the selected terminal MISESERI frames; one native remesh follows each complete pre-analysis.',500)),
('table',([
['Partitions','Endpoint [mm]','MISESERI comparison','Native FE','Observed difference'],
['1','0.005000','Reference terminal field','14,677','Baseline'],
['2','0.005000','Max |difference| = 0','14,677','No field/mesh change'],
['4','0.005000','Max |difference| = 0','14,677','No field/mesh change']],[65,95,140,80,105])),
('p','Field output is requested every increment. The compared selections are the last frames of Step-1, Step-2 and Step-4 respectively (increments 500, 250 and 125). The physical displacement increment is 0.000010 mm in every schedule. Archived verification reports identical recovered fields and native mesh identity, with 14,646 nodes in each case.'),
('h2','What did B add beyond A?'),
('p','B made preliminary loading and field selection configurable, and tested whether step boundaries alone alter the native mesh. For this common pre-peak endpoint, they did not. This is consistent with linear-elastic companion-layer stress recovery: at the same mesh and endpoint state, subdividing a monotonic load schedule adds no new spatial error information.'),
('p','This is an observed invariance result, not an accuracy advantage. Companion-layer elasticity does not make the physical phase-field model globally linear. Benefits of selecting intermediate frames were not tested. Different frames, evolving damage, unloading or other controls could change the result. No final fracture-response improvement is attributed to partition count; B remains a one-remesh/two-pass extension, not a demonstrated sequential adaptive algorithm.')
],[
('h1','3. Finding B: corrected ligament-resolution study'),
('p','The separate retrospectively refined 14,483-element verification mesh (serial job 1412465) is compared with canonical fixed reference job 1398090. It uses prior crack-path/ligament information. Its improved brittle fracture response is a mesh-resolution finding, not a benefit caused by choosing 1, 2 or 4 loading partitions.'),
('table',([
['Quantity','Corrected Method B','Fixed reference','Difference'],
['Base elements','14,483','15,192','-4.67%'],
['Initial stiffness [kN/mm]','137.9096','137.9455','-0.026%'],
['Peak force [N]','743.701','757.778','-1.86%'],
['Matched external work [mJ]','2.2674',f'{wr[-1]:.4f}','-3.87%'],
['Comparison endpoint [mm]','0.007889','0.007889','Same horizon']],[166,122,113,84])),
('img',('method_b_response.png','Figure 1. Authentic corrected Method B and fixed-reference histories, both ending at 0.007889 mm. Force is in N; work is in mJ; plotted displacement is in micrometres. No corrected data are extrapolated.',500)),
('h2','Validated range and interpretation'),
('p','Initial stiffness and peak-force differences meet the reported 0.5% and 2% criteria. Matched-horizon external work differs by -3.87%. This supports the corrected mesh as a useful pre-refinement baseline within the verified range.'),
('p','The corrected solve reached 0.007889 mm; the full 0.010 mm horizon was not completed. The reference is deliberately cropped to the same endpoint. Retrospective ligament refinement does not establish that native automatic remeshing independently predicted the whole crack path.'),
('note','Work provenance: direct CSV re-integration gives 2.267379 mJ and 2.358732 mJ (approximately -3.87%). The earlier summary listed reference 2.3586 mJ; 2.3587 mJ is the reproducible rounded CSV value. Work follows the established first-recorded-row zero convention; see FIGURE_SOURCES.md.')
],[
('h1','4. Method C: shared workflow and current evidence'),
('p','Step 0 solves on a coarse mesh and monitors the crack region. Each of four proposed cycles then extracts displacement u, damage d and committed history H; remeshes; transfers and re-equilibrates the state; and continues loading. C1/C2 differ in whether earlier refinement is retained or selectively coarsened (Section 5).'),
('h2','Verified building blocks; nonmatching handoff still unqualified'),
('p','Native mesh generation and a same-mesh continuation control are demonstrated. At u=0.00270 mm, that control gives 5.2881993 N versus 5.2895973 N (-0.0264% endpoint difference). It establishes neither whole-trajectory agreement nor nonmatching-transfer qualification.'),
('p','Crack-band receiver test mesh CB-2300 (formerly Candidate C2) is an unrelated offline test: 2,300 quads, 2,413 nodes, 0.1 x 0.1 mm domain, 0.001 mm band spacing and positive minimum Jacobian 3.125e-7. Its equilibrated force is 0.366 N versus donor 7.851 N (-95.34%, FAIL); maximum damage healing is 0.0021837.'),
('img',('candidate_c1_c2_meshes.png','Figure 5. Authentic intermediate receiver and CB-2300 test meshes with actual slit-tip close-ups. Neither mesh is a Method C1/C2 strategy or an accepted adaptive cycle.',400)),
('img',('candidate_c2_passing_checks.png','Figure 6. Authentic offline checks: CB-2300 elastic stiffness discrepancy 4.58% (limit 5%) and fracture-energy discrepancy +0.79% (limit 2%). Passing subchecks do not qualify continuation.',400)),
('note','CB-2300 is only a report label; scientific filenames and checkpoints are unchanged. Zero healing in the separate constrained 650-element prototype is not a CB-2300 result. Neither this test nor the continuation control demonstrates wake coarsening. No complete nonmatching remesh-and-continue cycle is qualified.')
],[
('h1','5. Planned Method C1 and Method C2 strategies'),
('p','Both strategies target four state-preserving cycles following the evolving crack. C1 - Sequential forward refinement generally retains earlier fine regions. C2 - Sequential refinement with selective wake coarsening investigates removing unnecessary wake resolution while protecting active and damaged regions, potentially limiting mesh growth.'),
('img',('method_c_planned_workflow.png','Figure 4. Side-by-side conceptual progressions: C1 accumulates refinement; C2 could limit mesh growth through conditional coarsening while protecting the damaged corridor. All ten panels are illustrative, not completed solver cycles.',475)),
('table',([
['Comparison','Method C1','Method C2'],
['Earlier fine regions','Generally retain refinement','Selective coarsening only after physical checks'],
['Qualification','Not validated for complete nonmatching cycles','Not validated; coarsening not verified']],[118,184,183])),
('p','Coarsening must preserve damage irreversibility, fracture energy, displacement compatibility, crack opening and mechanical compliance. The active process zone and damaged regions need sufficient resolution; a relaxed wake is not automatically safe to coarsen. No cost saving is claimed.'),
('h2','Scientific decision and immediate next work'),
('p','First qualify one physically continuous C1 nonmatching handoff, then sequential refinement. Method C2 coarsening is an additional proposed extension after that dependency passes. Preserve the validated Method B findings; do not treat CB-2300 as a Method C2 implementation.')
]]

styles=getSampleStyleSheet()
for name,size,leading,color in [('MainTitle',17,21,INK),('SubTitle',11.5,15,BLUE),('ReportBody',10.2,14,'#111111'),('Caption',9,12,'#465b68'),('Note',8.3,10.8,'#465b68'),('Cell',9,12,'#111111')]:
    styles.add(ParagraphStyle(name=name,fontName='Helvetica-Bold' if name in ('MainTitle','SubTitle') else 'Helvetica',fontSize=size,leading=leading,textColor=colors.HexColor(color),spaceAfter=7,spaceBefore=8 if name=='SubTitle' else 0))
story,md=[],[]
for i,blocks in enumerate(pages):
    if i: story.append(PageBreak())
    for kind,value in blocks:
        if kind in ('h1','h2','p','note'):
            style={'h1':'MainTitle','h2':'SubTitle','p':'ReportBody','note':'Note'}[kind]
            story.append(Paragraph(escape(value),styles[style])); md.append(('# ' if kind=='h1' else '## ' if kind=='h2' else '')+value)
        elif kind=='img':
            name,caption,width=value; w,h=PILImage.open(FIG/name).size
            story.extend([Image(str(FIG/name),width=width,height=h/w*width),Paragraph(escape(caption),styles['Caption'])]); md.extend([f'![{caption}](figures/{name})',caption])
        else:
            rows,widths=value; table=Table([[Paragraph(escape(c),styles['Cell']) for c in row] for row in rows],colWidths=widths,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eff4')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor(BLUE)),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f3f6f8')]),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
            story.extend([table,Spacer(1,10)]); md.extend(['| '+' | '.join(rows[0])+' |','| '+' | '.join(['---']*len(rows[0]))+' |']+['| '+' | '.join(r)+' |' for r in rows[1:]])
def footer(canvas,doc):
    canvas.setStrokeColor(colors.HexColor('#cbd7df')); canvas.line(40,32,555,32)
    canvas.setFont('Helvetica',8); canvas.setFillColor(colors.HexColor('#465b68')); canvas.drawString(40,20,'Mode-I adaptive remeshing | Technical progress | 22 October 2026'); canvas.drawRightString(555,20,str(doc.page))
SimpleDocTemplate(str(OUT/'SUPERVISOR_REPORT_SUCCESSFUL_RESULTS_ONLY.pdf'),pagesize=(595.28,841.89),leftMargin=40,rightMargin=40,topMargin=35,bottomMargin=42,title='Mode-I adaptive remeshing: validated results',author='Pruthviraja Reddy Vandavagali').build(story,onFirstPage=footer,onLaterPages=footer)
references=[eval_path,ref_path,corr_path,partition_result_path,partition_manifest_path,decision_path,*deck_paths,*wrapper_paths,*method_c_sources,'docs/reports/MODE1_METHOD_B_EVIDENCE_AUDIT_AND_SUPERVISOR_DECISION_PACKAGE.md','docs/reports/MODE1_METHOD_B_SCIENTIFIC_VALIDATION_AND_ADAPTIVE_LIMITATION_REPORT.md','models/pandey_kumar_mode1/experimental_offset_uel/evidence_f1575/F1575_SAME_MESH_CONTINUATION_RESOLUTION.json',cp,'results/validation/mode1_f1597/correction_prototype.json']
md.extend(['## Evidence references']+['- `'+p+'`' for p in references]+['- Figure classes and hashes: [FIGURE_SOURCES.md](FIGURE_SOURCES.md).'])
text=''
for i,line in enumerate(md): text+=line+ ('\n' if line.startswith('|') and i+1<len(md) and md[i+1].startswith('|') else '\n\n')
(OUT/'SUPERVISOR_REPORT_SUCCESSFUL_RESULTS_ONLY.md').write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')
prov=['# Figure sources and evidence boundaries','Authentic solver outputs, input geometry, offline diagnostics and conceptual figures are separate evidence classes. Actual mesh images come from input connectivity. Conceptual meshes do not represent completed cycles.','## Nomenclature used in this report','Method C1 is the planned sequential forward-refinement strategy. Method C2 is the planned sequential refinement with selective wake-coarsening extension. Neither is qualified. CB-2300 is the report-only alias of the separate historical Candidate C2 crack-band receiver test mesh (2,300 quads). The 840-element intermediate receiver is also not the Method C1 strategy. Original files, identifiers and checkpoints are unchanged. Stable report figure filenames containing candidate_c1_c2 or candidate_c2 refer to those original test artifacts, not to the planned strategies. No external illustrative images from the pasted request are used.']
for name,kind,paths,desc in sources:
    prov.extend([f'## {name}',f'**Type: {kind}.** {desc}',f'Output SHA-256: `{hashlib.sha256((FIG/name).read_bytes()).hexdigest()}`'])
    for p in paths: prov.append(f'- `{p}` | SHA-256 `{hashlib.sha256((ROOT/p).read_bytes()).hexdigest()}`')
prov.append('## Numerical claim sources')
for p in references:
    assert (ROOT/p).is_file(),p
    prov.append(f'- `{p}` | SHA-256 `{hashlib.sha256((ROOT/p).read_bytes()).hexdigest()}`')
prov.extend(['## Verified schedule and field selection','The build parses the actually executed M1_MB_INF_1S/2S/4S decks, verifies their input filenames against PBS wrappers, reads *STATIC and absolute N_RP U2 boundary values, and verifies MISESERI output every increment. No amplitude override is present. The preflight manifest specifies LAST_INCREMENT of Step-1/2/4; its endpoint matches the executed deck and archived result. Decision record Section 8.6 reports 500 total increments and zero cutbacks per case, supporting terminal increment labels 500/250/125. These are step-local increments, not guessed global ODB frame indices. The build does not reopen the historical ODBs or recompute absent cross-partition arrays. Mesh/field identity is the archived verified observation, not a new three-ODB comparison.'])
for sch in schedules:
    prov.append(f"- {sch['partitions']}S: total static step-time {sch['total_step_time']:g}; select {sch['indicator_step']} last frame (step-local increment {sch['indicator_nominal_increment']}); one remesh after the pre-analysis.")
    for step in sch['steps']:
        prov.append(f"  - {step['name']}: time {step['start_time']:g} to {step['end_time']:g}; prescribed U2 {step['start_u_mm']:.6f} to {step['end_u_mm']:.6f} mm; initial/max dt={step['dt_max']:.6f}; {step['nominal_increments']} nominal increments; field frequency=1.")
prov.extend(['## Rebuild and scope','Run `python docs/supervisor_reports/22-10-2026/build_successful_results_report.py`. No solver, scheduler or controller execution. Stable output names are reused; native_crack_tip.png is a companion genuine native 14,677-element mesh close-up. All other generated figures are embedded.','## Comparison convention','Both response curves are cropped to 0.007889 mm without extrapolation. The reference has authentic later records to 0.010 mm, excluded here. The corrected 14,483-element study does not complete 0.010 mm. kN-mm work is converted to mJ with factor 1000. Partition invariance (native 14,677 FE) and retrospective ligament resolution (14,483 FE) are separate findings; no fracture-response advantage is attributed to loading partition count.'])
(OUT/'FIGURE_SOURCES.md').write_text('\n\n'.join(prov)+'\n',encoding='utf-8',newline='\n')
print(f'Built report and {len(sources)} figures. Matched work: {wc[-1]:.9f}, {wr[-1]:.9f} mJ; error {work_error:.5f}%.')
