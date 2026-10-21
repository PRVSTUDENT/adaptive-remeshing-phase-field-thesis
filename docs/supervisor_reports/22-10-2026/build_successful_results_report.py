"""Render a standalone report from existing evidence, without solver execution."""
from pathlib import Path
import hashlib, json, sys
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

fig,ax=plt.subplots(figsize=(10.2,1.65)); ax.set(xlim=(0,1),ylim=(0,1)); ax.axis('off')
labels=['Coarse Mode-I\nsolve to chosen\npre-analysis point','Native MISESERI\nadaptive mesh\nrefinement','Fresh solve on\nrefined mesh\nfrom zero load','Compare with\nfixed fine-mesh\nreference']
for i,t in enumerate(labels):
    x=.12+i*.255
    ax.add_patch(Rectangle((x-.112,.34),.224,.44,facecolor='#e7eff4',edgecolor=BLUE,lw=1))
    ax.text(x,.56,t,ha='center',va='center',fontsize=10.5,linespacing=1.05)
    if i<3: ax.annotate('',xy=(x+.140,.56),xytext=(x+.115,.56),arrowprops=dict(arrowstyle='->',color=BLUE,lw=1.5))
ax.text(.5,.08,'CONCEPTUAL METHOD B PROCESS | final evaluated mesh includes retrospective ligament refinement',ha='center',fontsize=10,color=BLUE)
save(fig,'method_b_workflow.png','CONCEPTUAL method explanation',['docs/reports/MODE1_METHOD_B_SCIENTIFIC_VALIDATION_AND_ADAPTIVE_LIMITATION_REPORT.md',eval_path],
     'Method B schematic, not solver imagery. Fresh refined-mesh solve without state transfer. The corrected configuration uses retrospective ligament information; this does not establish fully predictive native automatic crack tracking.')

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
fig,axs=plt.subplots(1,3,figsize=(10.2,3.7),layout='constrained')
mesh(axs[0],coarse_path,'Coarse pre-analysis | 2,906 FE')
_,count=mesh(axs[1],corrected_mesh_path,'Corrected refined mesh | 14,483 FE'); assert count==14483
mesh(axs[2],corrected_mesh_path,'Corrected crack-tip zoom',(.475,.54,.47,.53))
fig.suptitle('AUTHENTIC INPUT GEOMETRY | before pre-refinement and final evaluated configuration',fontsize=12)
save(fig,'mesh_artifacts.png','AUTHENTIC input-deck geometry',[coarse_path,corrected_mesh_path],
     'Figure 2. Coarse pre-analysis and final corrected Method B mesh with actual tip zoom. Before/after includes retrospective ligament refinement, not a purely automatic native remesh transition or loaded state-preserving handoff.')
fig,ax=plt.subplots(figsize=(6.5,4.5),layout='constrained'); mesh(ax,corrected_mesh_path,'Corrected Method B: actual crack-tip mesh',(.475,.54,.47,.53))
save(fig,'native_crack_tip.png','AUTHENTIC input-deck geometry',[corrected_mesh_path],
     'Companion close-up of corrected 14,483-FE configuration; filename retained. Not evidence for predictive native crack tracking.')

fig,axs=plt.subplots(1,5,figsize=(10.2,4.8)); fig.subplots_adjust(top=.77,bottom=.28,left=.03,right=.98,wspace=.25)
for i,ax in enumerate(axs):
    ax.set(xlim=(0,1),ylim=(0,1),aspect='equal'); ax.set_xticks([]); ax.set_yticks([])
    for t in np.linspace(0,1,9): ax.axhline(t,color='#b9ccd7',lw=.6); ax.axvline(t,color='#b9ccd7',lw=.6)
    tip=.45+.1*i; ax.plot([0,tip],[.5,.5],color=INK,lw=2)
    if i:
        ax.add_patch(Rectangle((tip-.13,.34),.26,.32,facecolor='#c9e8dd',edgecolor=GREEN,lw=1.2))
        for xx in np.linspace(tip-.13,tip+.13,9): ax.plot([xx,xx],[.34,.66],color=GREEN,lw=.5)
        for yy in np.linspace(.34,.66,9): ax.plot([tip-.13,tip+.13],[yy,yy],color=GREEN,lw=.5)
    ax.set_title('Step 0\nInitial mesh' if not i else f'Step {i}\nRemesh cycle {i}',fontsize=11)
    ax.text(.5,-.22,'Solve + monitor' if not i else 'Extract > remesh\ntransfer > continue',transform=ax.transAxes,ha='center',va='top',fontsize=11)
    if i<4: ax.annotate('',xy=(1.24,.5),xytext=(1.03,.5),xycoords='axes fraction',annotation_clip=False,arrowprops=dict(arrowstyle='->',color=BLUE,lw=1.5))
fig.suptitle('CONCEPTUAL TARGET | four sequential remeshing cycles',fontsize=14,color=INK,y=.96)
fig.text(.5,.86,'Refinement follows the active fracture process zone as loading continues',ha='center',fontsize=11)
fig.text(.5,.09,'At every handoff: transfer displacement u, damage d and committed history H;\naccept force, energy and irreversibility checks before continuing.',ha='center',fontsize=11)
fig.text(.5,.015,'Illustrative meshes and crack positions only. No numerical cycle, displacement or crack-path result is implied.',ha='center',fontsize=9,color=BLUE)
save(fig,'method_c_planned_workflow.png','CONCEPTUAL intended workflow and mesh progression',['docs/reports/MODE1_METHOD_C1_CONTINUATION_FEASIBILITY_AND_PLAN.md'],
     'Figure 3. User-requested target of Step 0 plus four future cycles. All five meshes, refinement boxes and crack positions are conceptual. No accepted multi-mesh trajectory or cycle displacement is asserted. No wake coarsening is represented.')

candidate_paths=['models/pandey_kumar_mode1/candidate_intermediate_mesh_c1.inp','models/pandey_kumar_mode1/candidate_crack_band_mesh_c2.inp']
fig,axs=plt.subplots(2,2,figsize=(9.5,5.6),layout='constrained')
for col,(p,label) in enumerate(zip(candidate_paths,['C1 | 840 quads / 910 nodes','C2 | 2,300 quads / 2,413 nodes'])):
    assert mesh(axs[0,col],p,label)==[(910,840),(2413,2300)][col]
    mesh(axs[1,col],p,'Actual crack tip at x = 0.040 mm',(.032,.056,.044,.056))
    for row in (0,1):
        axs[row,col].plot([0,.040],[.050,.050],color=INK,lw=1.8)
        axs[row,col].plot(.040,.050,'o',color=INK,ms=3)
fig.suptitle('AUTHENTIC RECEIVER MESHES | separate offline candidates, not sequential cycles',fontsize=12)
save(fig,'candidate_c1_c2_meshes.png','AUTHENTIC input-deck geometry',candidate_paths+['scripts/remeshing/generate_crack_band_mesh.py','scripts/validation/evaluate_candidate_meshes.py'],
     'Figure 4. Actual C1/C2 receiver geometries with common-scale tip close-ups. The slit is y=0.050 mm, ending at x=0.040 mm as defined in the mesh generator and evaluator; dark line/dot identify this geometry, not a simulated evolving crack. Coordinates in mm. Distinct transfer-test candidates, not successive full-plate Method C cycles.')
cp='results/validation/mesh_convergence_prototype.json'; data=read_json(cp)['comparisons']
c1,c2=data['candidate_1_intermediate'],data['candidate_2_crack_band_resolved']
assert abs(c2['equilibrated_RF_N']-.3662)<1e-6 and c2['max_damage_healing']>0
fig,axs=plt.subplots(1,2,figsize=(9.5,2.6),layout='constrained')
for ax,key,title,limit in [(axs[0],'elastic_stiffness_discrepancy_pct','Elastic stiffness error [%]',5),(axs[1],'fracture_energy_discrepancy_pct','Mapped fracture-energy error [%]',2)]:
    vals=[c1[key],c2[key]]; ax.bar(['C1','C2'],vals,color=[BLUE,GREEN]); ax.axhline(limit,color='#965137',ls='--',label=f'{limit}% acceptance limit')
    ax.set_title(title); ax.legend(fontsize=9,loc='upper right'); ax.set_ylim(-.5,limit*1.5)
    for i,v in enumerate(vals): ax.text(i,v+.10,f'{v:+.2f}%',ha='center',fontsize=11)
save(fig,'candidate_c2_passing_checks.png','AUTHENTIC offline numerical diagnostics',[cp,'scripts/validation/evaluate_candidate_meshes.py'],
     'Figure 5. Passing undamaged elastic-stiffness and mapped fracture-energy checks. Not damaged-state compliance or solver continuation conservation. C2 healing and force-continuity failures are retained in report text.')

# Shared blocks keep Markdown and PDF claims identical.
pages=[[
('h1','Mode-I adaptive remeshing: validated results'),
('p','Technical progress report | 22 October 2026'),
('h2','1. Objective and demonstrated progress'),
('p','Preserve phase-field fracture accuracy while concentrating resolution where needed. Corrected Method B is successful within its verified displacement range. Method C has verified building blocks, but a physically continuous nonmatching handoff remains incomplete.'),
('h2','2. Method B: pre-refine, then solve afresh'),
('p','Start with a coarse Mode-I analysis and evaluate MISESERI at the chosen pre-analysis point. Native Abaqus remeshing generates a refined mesh; Method B then runs a fresh phase-field solve from zero load. It does not transfer a loaded fracture state between meshes.'),
('img',('method_b_workflow.png','Method B process schematic. A fresh refined-mesh solve is distinct from Method C state-preserving continuation.',500)),
('img',('mesh_artifacts.png','Figure 2. Authentic coarse and corrected refined meshes, with the crack-tip region. Final ligament refinement uses retrospective crack-path information; this is not a purely predictive automatic remeshing demonstration.',500)),
('h2','What the final evaluated configuration establishes'),
('p','The 14,483-element configuration resolves the expected propagation ligament using retrospective refinement. Its comparison with the fine fixed mesh tests the resulting fracture response. Predictive remeshing that follows an evolving crack remains a Method C target.'),
('h2','Independent pre-analysis reproducibility result'),
('p','At fixed displacement resolution, preliminary loading split into 1, 2 or 4 steps produced identical recovered MISESERI fields (maximum difference zero) and identical native 14,677-element meshes. This establishes invariance for the tested pre-peak window, separately from the corrected 14,483-element evaluation.')
],[
('h1','3. Method B: final quantitative comparison'),
('p','Corrected Method B (serial job 1412465) versus canonical fixed-mesh reference (job 1398090). Results are restricted to the common displacement horizon.'),
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
('h1','4. Method C: intended sequential adaptation'),
('p','Method C aims to retain the current fracture state while changing the mesh. The target is four genuine adaptive remeshing cycles, with refinement following the active crack-tip/process-zone region rather than a preselected full propagation ligament.'),
('img',('method_c_planned_workflow.png','Figure 3. Conceptual Step 0 plus four intended remeshing cycles. Every panel is illustrative: no authentic four-cycle solver trajectory has yet been qualified.',480)),
('h2','Intended sequence: Step 0 and cycles 1-4'),
('p','Step 0: solve on the coarse mesh and monitor damage and the error indicator. Cycle 1: at a chosen remeshing point, extract displacement, damage and committed history; remesh around the active region; transfer and re-equilibrate; continue loading. Cycles 2, 3 and 4 repeat that sequence from the newly continued solution. Remeshing points must be selected and validated; no cycle displacements are claimed here.'),
('table',([
['Building block','Achieved evidence','Remaining target'],
['Native mesh generation','Authentic refined input meshes','Adapt repeatedly to evolving crack'],
['Same-mesh continuation','-0.0264% endpoint force error','Preserve state on a new mesh'],
['Nonmatching transfer','Offline components evaluated','Force/energy continuity; no healing'],
['Sequential loading cycles','No qualified complete cycle','Four accepted remesh/continue cycles']],[128,176,181])),
('h2','Successful continuation control and current boundary'),
('p','The experimental same-mesh control reaches 5.2881993 N versus 5.2895973 N at u=0.00270 mm with the guarded predictor: -0.0264% endpoint difference. This is endpoint agreement for a specific same-mesh control, not whole-trajectory or nonmatching-transfer equivalence.'),
('p','Nonmatching transfer remains unqualified because force continuity, energy and pointwise damage irreversibility must all survive re-equilibration. Separate mesh-generation and continuation controls do not yet form a validated multi-cycle solution. Candidate C2 isolates the current limitation below.')
],[
('h1','5. Method C - Candidate C2: Crack-Band-Resolved Receiver Mesh'),
('p','Candidate C2 is a small receiver mesh developed for Method C: 2,300 quadrilateral elements, 2,413 physical nodes and 0.001 mm crack-band element size. Its minimum Jacobian is positive (3.125e-7). C1 is a separate intermediate candidate.'),
('img',('candidate_c1_c2_meshes.png','Figure 4. Authentic C1/C2 receiver geometries and common-scale crack-tip close-ups. These are separate offline transfer candidates, not successive remeshing cycles.',475)),
('img',('candidate_c2_passing_checks.png','Figure 5. Authentic passing offline checks: C2 elastic stiffness error 4.58% (limit 5%) and mapped fracture-energy error +0.79% (limit 2%). These do not qualify loaded continuation.',475)),
('h2','Remaining limitation: physical state continuity'),
('p','C2 equilibrated force is 0.366 N versus donor 7.851 N (-95.34%, FAIL). The evaluated C2 prototype also reports maximum damage healing 0.0021837. Thus C2 is a successful mesh-generation and partial verification result, not qualified Method C continuation. Zero healing in the separate constrained 650-element prototype must not be attributed to C2.'),
('h2','Scientific decision and immediate next work'),
('p','Retain corrected Method B as the retrospectively refined baseline within 0.007889 mm. For Method C, prioritize one transfer hypothesis preserving the damaged profile and committed history under consistent boundary conditions. Check force, energy, residuals and irreversibility offline before a distinct qualified serial single-handoff test. Require physical acceptance before any four-cycle demonstration.')
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
references=[eval_path,ref_path,corr_path,'docs/reports/MODE1_METHOD_B_EVIDENCE_AUDIT_AND_SUPERVISOR_DECISION_PACKAGE.md','docs/reports/MODE1_METHOD_B_SCIENTIFIC_VALIDATION_AND_ADAPTIVE_LIMITATION_REPORT.md','models/pandey_kumar_mode1/experimental_offset_uel/evidence_f1575/F1575_SAME_MESH_CONTINUATION_RESOLUTION.json',cp,'results/validation/mode1_f1597/correction_prototype.json']
md.extend(['## Evidence references']+['- `'+p+'`' for p in references]+['- Figure classes and hashes: [FIGURE_SOURCES.md](FIGURE_SOURCES.md).'])
text=''
for i,line in enumerate(md): text+=line+ ('\n' if line.startswith('|') and i+1<len(md) and md[i+1].startswith('|') else '\n\n')
(OUT/'SUPERVISOR_REPORT_SUCCESSFUL_RESULTS_ONLY.md').write_text(text.rstrip()+'\n',encoding='utf-8',newline='\n')
prov=['# Figure sources and evidence boundaries','Authentic solver outputs, input geometry, offline diagnostics and conceptual figures are separate evidence classes. Actual mesh images come from input connectivity. Conceptual meshes do not represent completed cycles.']
for name,kind,paths,desc in sources:
    prov.extend([f'## {name}',f'**Type: {kind}.** {desc}',f'Output SHA-256: `{hashlib.sha256((FIG/name).read_bytes()).hexdigest()}`'])
    for p in paths: prov.append(f'- `{p}` | SHA-256 `{hashlib.sha256((ROOT/p).read_bytes()).hexdigest()}`')
prov.append('## Numerical claim sources')
for p in references:
    assert (ROOT/p).is_file(),p
    prov.append(f'- `{p}` | SHA-256 `{hashlib.sha256((ROOT/p).read_bytes()).hexdigest()}`')
prov.extend(['## Rebuild and scope','Run `python docs/supervisor_reports/22-10-2026/build_successful_results_report.py`. No solver, scheduler or controller execution. Stable output names are reused; native_crack_tip.png is a companion corrected-mesh close-up. All other generated figures are embedded.','## Comparison convention','Both curves are cropped to 0.007889 mm without extrapolation. The reference has authentic later records to 0.010 mm, excluded here. Corrected Method B does not complete 0.010 mm. kN-mm work is converted to mJ with factor 1000. Retrospective ligament refinement is not equated with fully predictive native automatic refinement.'])
(OUT/'FIGURE_SOURCES.md').write_text('\n\n'.join(prov)+'\n',encoding='utf-8',newline='\n')
print(f'Built report and {len(sources)} figures. Matched work: {wc[-1]:.9f}, {wr[-1]:.9f} mJ; error {work_error:.5f}%.')
