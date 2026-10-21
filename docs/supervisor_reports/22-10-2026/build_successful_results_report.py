"""Rebuild the evidence-scoped 22 October meeting pack (no solver execution)."""
from pathlib import Path
import json, hashlib, shutil, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
FIG=OUT/'figures'; FIG.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'scripts/visualization'))
from plot_mode1_method_b_adaptive_mesh import parse_abaqus_mesh
sources=[]
def record(name,kind,paths,description):
    paths=[Path(p) for p in paths]
    for p in paths:
        assert (ROOT/p).is_file(), p
    sources.append((name,kind,paths,description))
def save(fig,name):
    fig.savefig(FIG/name,dpi=190,bbox_inches='tight'); plt.close(fig)

curves=[('Reference', 'results/pandey_kumar_mode1/master_fracture_curves/curve_standard_1398090.csv','u2_mm','rf2_kN'),('Method B original','runs/mode1/harvest_results_f1416/m1_mb_native_14k_1s_load_displacement.csv','u_mm','f_kN'),('Method B corrected','models/pandey_kumar_mode1/40_method_b_corrected_propagation_14k/evidence_1412465/corrected_method_b_load_displacement.csv','u_mm','f_kN')]
fig,axs=plt.subplots(1,2,figsize=(10,3.3))
for label,p,u,f in curves:
    d=pd.read_csv(ROOT/p); x=d[u].to_numpy(); y=d[f].to_numpy()
    axs[0].plot(x*1000,y*1000,label=label,lw=1.5)
    work=np.r_[0,np.cumsum((y[1:]+y[:-1])/2*np.diff(x))]*1000
    axs[1].plot(x*1000,work,label=label,lw=1.5)
axs[0].set(xlabel='Displacement [micrometres]',ylabel='Reaction force [N]')
axs[1].set(xlabel='Displacement [micrometres]',ylabel='External work [mJ]')
for ax in axs: ax.grid(alpha=.2); ax.legend(fontsize=7)
fig.suptitle('AUTHENTIC SIMULATION DATA | recorded horizons only',fontsize=10)
save(fig,'method_b_response.png')
record('method_b_response.png','AUTHENTIC simulation outputs',[c[1] for c in curves],'Replotted recorded force histories and trapezoidal external work; no extrapolation beyond recorded endpoints. Reference is truncated at its available horizon. Corrected run also has a finite recorded horizon; no full-horizon completion claim.')

meshpaths=['models/pandey_kumar_mode1/method_b_preflight_decks/M1-MB-1S.inp','models/pandey_kumar_mode1/38_method_b_native_final_14k/M1_MB_NATIVE_FINAL_1S.inp','models/pandey_kumar_mode1/candidate_crack_band_mesh_c2.inp']
fig,axs=plt.subplots(1,3,figsize=(10,3.4))
for ax,p,title in zip(axs,meshpaths,['Coarse pre-analysis','Native adapted mesh','Candidate C2 (offline)']):
    nodes,quads,tris=parse_abaqus_mesh(ROOT/p)
    polys=[[nodes[n] for n in ns] for _,ns in quads+tris]
    ax.add_collection(PolyCollection(polys,facecolors='none',edgecolors='#245773',linewidths=.18)); ax.autoscale(); ax.set_aspect('equal'); ax.set_title(title,fontsize=9); ax.set_xlabel('x [mm]'); ax.set_ylabel('y [mm]')
fig.suptitle('AUTHENTIC INPUT GEOMETRY | separate artifacts, not sequential accepted cycles',fontsize=10)
save(fig,'mesh_artifacts.png'); record('mesh_artifacts.png','AUTHENTIC input-deck geometry',meshpaths,'Actual mesh geometry. Candidate C2 is a separate small transfer-test mesh, not a later accepted full-plate cycle or a solver result.')
candidate_paths=['models/pandey_kumar_mode1/candidate_intermediate_mesh_c1.inp',meshpaths[2]]
fig,axs=plt.subplots(2,2,figsize=(9,5.5))
for col,(p,label) in enumerate(zip(candidate_paths,['C1: 840 quads / 910 nodes','C2: 2,300 quads / 2,413 nodes'])):
    nodes,quads,tris=parse_abaqus_mesh(ROOT/p)
    polys=[[nodes[n] for n in ns] for _,ns in quads+tris]
    for row in range(2):
        ax=axs[row,col]; ax.add_collection(PolyCollection(polys,facecolors='none',edgecolors='#245773',linewidths=.35)); ax.autoscale(); ax.set_aspect('equal'); ax.set_title(label if row==0 else 'Crack-tip region (geometry)',fontsize=9); ax.set_xlabel('x [mm]'); ax.set_ylabel('y [mm]')
        if row==1: ax.set_xlim(.042,.066); ax.set_ylim(.044,.056)
fig.suptitle('AUTHENTIC C1/C2 INPUT MESHES | full views and common-scale close-ups',fontsize=11); fig.tight_layout()
save(fig,'candidate_c1_c2_meshes.png'); record('candidate_c1_c2_meshes.png','AUTHENTIC input-deck geometry',candidate_paths,'Full receiver meshes and common-scale crack-tip close-ups. Offline geometry, not solver-evolved sequential stages.')
src='results/figures/mode1_method_b_mesh/fig_mode1_method_b_native_crack_tip_zoom.png' 
shutil.copyfile(ROOT/src,FIG/'native_crack_tip.png'); record('native_crack_tip.png','AUTHENTIC input-deck geometry',[src,meshpaths[1],'scripts/visualization/plot_mode1_method_b_adaptive_mesh.py'],'Existing native adapted crack-tip zoom, copied unchanged.')

fig,ax=plt.subplots(figsize=(10,2.7)); ax.axis('off')
steps=['Coarse solve','Extract state\nand indicator','Native remesh','Transfer u, d, H\nand equilibrate','Continue load','Repeat']
for i,t in enumerate(steps):
    x=.075+i*.17; ax.text(x,.68,t,ha='center',va='center',fontsize=9,bbox=dict(boxstyle='round,pad=.6',fc='#e4eef5',ec='#245773'))
    if i<5: ax.annotate('',xy=(x+.105,.68),xytext=(x+.065,.68),arrowprops=dict(arrowstyle='->',color='#245773'))
ax.text(.5,.19,'Achieved: mesh generation + controlled same-mesh continuation\nUnqualified: nonmatching handoff -> genuine repeated loaded cycles',ha='center',fontsize=10,color='#9a3d26')
ax.set_title('CONCEPTUAL PLANNED METHOD C WORKFLOW | arrows do not imply completed cycles',fontsize=11)
save(fig,'method_c_planned_workflow.png'); record('method_c_planned_workflow.png','CONCEPTUAL planned workflow',['docs/reports/MODE1_METHOD_C1_CONTINUATION_FEASIBILITY_AND_PLAN.md','project_coordination/ACTIVE_TASK.json'],'Reporting schematic. Achieved-versus-planned comparison is evidence status, not simulated mesh evolution.')

cp='results/validation/mesh_convergence_prototype.json'; data=json.loads((ROOT/cp).read_text())['comparisons']
c1=data['candidate_1_intermediate']; c2=data['candidate_2_crack_band_resolved']
fig,axs=plt.subplots(1,2,figsize=(9,2.8))
for ax,key,title,limit in [(axs[0],'elastic_stiffness_discrepancy_pct','Undamaged elastic stiffness error [%]',5),(axs[1],'fracture_energy_discrepancy_pct','Mapped fracture-energy error [%]',2)]:
    vals=[c1[key],c2[key]]; ax.bar(['Candidate C1','Candidate C2'],vals,color=['#477d9e','#3b9a8e']); ax.axhline(limit,color='#a33',ls='--',label=f'{limit}% criterion'); ax.set_title(title,fontsize=10); ax.legend(fontsize=8)
    for i,v in enumerate(vals): ax.text(i,v+.12,f'{v:+.2f}%',ha='center',fontsize=9)
fig.suptitle('AUTHENTIC OFFLINE DIAGNOSTICS | selected passing checks only; not solver qualification',fontsize=10); fig.tight_layout()
save(fig,'candidate_c2_passing_checks.png'); record('candidate_c2_passing_checks.png','AUTHENTIC offline numerical diagnostics',[cp,'scripts/validation/evaluate_candidate_meshes.py'],'Selected passing subchecks. Stiffness is undamaged elastic stiffness, not damaged-state compliance. Energy is mapped-state quadrature, not conservation after solver equilibration.')

sections=[
('1. Objective of the current work', 'Develop adaptive remeshing for Mode-I phase-field fracture while preserving the physical state. Method B establishes indicator-driven pre-refinement followed by a fresh solve from zero load. Method C aims to remesh during loading and continue from the transferred state. The requested Method D/C2 terminology is bounded explicitly in Section 5.'),
('2. Successful validated progress since the previous meeting', '- Method B: tested 1/2/4-step pre-analysis partitions produced identical recovered indicators and native 14,677-element geometry.\n- Corrected Method B: ligament refinement removed the sustained post-peak plateau in the recorded response; initial stiffness and peak are close to the reference.\n- Method C building block: guarded-predictor same-mesh continuation achieved 0.0264% endpoint force agreement in the specific experimental control.\n- Candidate C2: offline elastic stiffness and mapped fracture-energy checks meet their stated 5% and 2% criteria. These are subchecks, not a qualified transfer cycle.'),
('3. Mode I — Method B', 'Method B uses a preliminary load window to obtain MISESERI, generates a native adapted mesh, then solves the phase-field model afresh. The small companion stiffness permits indicator recovery with negligible measured force perturbation (relative discrepancy 5.50e-10). At fixed displacement resolution, the 1/2/4-step tests give max indicator difference zero and identical 14,677-element meshes. This is a tested pre-peak invariance result.\n\nThe propagation-resolved correction refines the ligament ahead of the notch. The corrected 14,483-element response has initial stiffness 137.9096 kN/mm versus reference 137.9455 kN/mm (about -0.026%) and peak 743.701 N versus 757.778 N (about -1.86%). The recorded response demonstrates the load drop without the original extended plateau. These successes establish a useful mesh-design correction; they do not establish full-horizon or universal adaptive accuracy.\n\nFigure 1 uses authentic recorded force data and integrated external work. Energy histories are shown over each available horizon only; unequal endpoints must not be interpreted as matched-horizon energy convergence.'),
('4. Mode I — Method C',''),
('4.1 Planned Method C workflow','Coarse simulation → extract displacement, damage, committed history and indicator → native remesh → transfer and re-equilibrate → continue loading → repeat. Each handoff must preserve boundary conditions, reaction force, energy and damage irreversibility before the next cycle. Figure 2 is conceptual and distinguishes planned stages from accepted building blocks.'),
('4.2 What has been successfully demonstrated','Native remeshing has generated authentic adapted geometry. A separate experimental offset-state same-mesh control, using extrapolation=NO, reaches 5.2881993 N versus continuous-control 5.2895973 N at u=0.00270 mm: -0.0264% endpoint discrepancy. Earlier increments differ by -1.7769% and -0.2283%; the endpoint number is not whole-trajectory equivalence. This is a controlled same-mesh continuation result using the experimental architecture, not nonmatching transfer qualification. Production UEL remains frozen.'),
('4.3 Current problems and limitations','The nonmatching state handoff is still scientifically unqualified. The independent Package 72 audit at u=0.00254 mm reports receiver 1.748264 N versus donor 7.8512395 N (-77.73%), 291/713 healing nodes, and +15.12% fracture-energy change. Solver Exit 0 does not satisfy physical continuity. This solver audit is distinct from the later offline prototype.\n\nThe newer Candidate C2 offline experiment passes selected mesh checks but reports +27.05% damaged stiffness error and an equilibrated-force deficit of 95.34%; it also does not converge within its reported 15 iterations. Thus resolution alone has not qualified the mapped damaged state. The mechanism remains a research hypothesis, not a universally proven interpolation failure. Zero complete sequential nonmatching remeshing-and-continuation cycles are qualified. Forward cycles remain on hold.'),
('5. Mode I — Method D / C2','Terminology boundary: no established Mode-I Method D definition was located in the reviewed evidence. Here the concrete successful C2 evidence is reported as Candidate C2, the recent crack-band-resolved receiver mesh. This does not equate it to the separately planned Method C2 wake-coarsening extension. Wake coarsening has no validated success claimed here.\n\nCandidate C2 has 2,300 quads and positive minimum Jacobian 3.125e-7. Offline undamaged elastic stiffness discrepancy is +4.5751% (criterion 5%); mapped fracture-energy discrepancy is +0.7944% (criterion 2%). Candidate C1 has corresponding +3.0339% and -0.1569%. These successful checks demonstrate mesh admissibility and selected mapped-field fidelity. They do not establish damaged-state equilibrium or loaded continuation. Figure 3 deliberately labels these as offline diagnostics.'),
('6. Visual summary of remeshing progression','Figure 4 compares authentic coarse and native adapted full-plate geometry with the separate Candidate C2 transfer-test mesh. These are distinct artifacts, not frames from an accepted sequential cycle. Figure 5 shows the actual native crack-tip refinement. The planned progression is Figure 2; the achieved state is mesh generation plus limited continuation controls, with the nonmatching handoff still unresolved.'),
('7. Conclusions for the supervisor meeting','Method B supplies reproducible pre-refinement and a demonstrated ligament-resolution improvement. Method C has meaningful mesh-generation and same-mesh continuation building blocks. Candidate C2 adds passing offline mesh and mapped-energy checks. A physically continuous nonmatching handoff remains the central unresolved dependency.'),
('8. Immediate next work','Review a bounded history-aware, profile-preserving transfer hypothesis against the authentic donor checkpoint. First compare mapped damaged stiffness, reaction force, phase/history residuals and irreversibility offline. Only after scientific review and technical qualification should a distinct serial single-handoff solver test be executed. Require reaction-force, energy and pointwise irreversibility acceptance before any sequential cycle or wake-coarsening extension.')]

images={2:[('method_b_response.png','Figure 1. Authentic solver histories; recorded horizons only.')],4:[('method_c_planned_workflow.png','Figure 2. Conceptual workflow and planned-versus-achieved comparison.')],7:[('candidate_c2_passing_checks.png','Figure 3. Authentic offline passing subchecks, not solver qualification.')],8:[('mesh_artifacts.png','Figure 4. Authentic mesh artifacts; separate models and scales.'),('native_crack_tip.png','Figure 5. Authentic native adapted crack-tip geometry.') ]}
sections[0]=(sections[0][0],sections[0][1].replace('The requested Method D/C2 terminology is bounded explicitly in Section 5.','Candidate C2 is a crack-band-resolved receiver mesh developed for Method C.'))
sections[7]=('5. Method C \u2014 Candidate C2: Crack-Band-Resolved Receiver Mesh','Candidate C2 is a receiver mesh developed for Method C. It contains 2,300 quadrilateral elements and 2,413 physical nodes, with crack-band element size 0.001 mm and positive minimum Jacobian 3.125e-7. Offline elastic stiffness discrepancy is 4.58% (PASS against 5%); mapped fracture-energy discrepancy is +0.79% (PASS against 2%). Candidate C1 has corresponding +3.03% and -0.16%. These are successful mesh-generation and partial verification results. Figure 3 shows passing checks; Figure 6 shows authentic C1/C2 geometry.\n\nZero damage healing is verified in the separate constrained 650-element PDAS correction prototype (0/713 healing nodes), a useful Method C building block. It cannot be attributed to Candidate C2: the current C2 mesh-convergence JSON records max_damage_healing=0.0021837. That discrepancy needs reconciliation before a zero-healing C2 claim is validated.\n\nThe unresolved Candidate C2 force-transfer result is reported separately in Section 4.3: 0.366 N versus donor 7.851 N (-95.34%, FAIL). Candidate C2 is not a qualified Method C continuation.')
sections[5]=(sections[5][0],sections[5][1]+' A separate offline constrained PDAS prototype verifies zero healing at all 713 receiver nodes; this result belongs to that prototype, not the C2 mesh-convergence experiment.')
images[8].append(('candidate_c1_c2_meshes.png','Figure 6. Authentic C1/C2 receiver meshes and crack-tip close-ups.'))
md=['# Supervisor meeting | 22 October 2026','Evidence reviewed 21 October 2026. Successful results are scoped to the tested case and evidence type.']
for i,(title,body) in enumerate(sections):
    level='##' if title.startswith('4.') and title[2:3].isdigit() else '#'
    md += [f'{level} {title}',body]
    for n,c in images.get(i,[]): md += [f'![{c}](figures/{n})',c]
md += ['## Evidence references','- Method B: `docs/reports/MODE1_METHOD_B_SCIENTIFIC_VALIDATION_AND_ADAPTIVE_LIMITATION_REPORT.md`; existing Method B final briefing in this folder.\n- Same-mesh control: `models/pandey_kumar_mode1/experimental_offset_uel/evidence_f1575/F1575_SAME_MESH_CONTINUATION_RESOLUTION.json`.\n- Solver handoff audit: `models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/PACKAGE72_STATE_TRANSFER_AUDIT.json`.\n- Candidate checks: `results/validation/mesh_convergence_prototype.json`.\n- Zero-healing control: `results/validation/mode1_f1597/correction_prototype.json`.\n- Figure paths and SHA-256 hashes: `FIGURE_SOURCES.md`.']
(OUT/'SUPERVISOR_REPORT_SUCCESSFUL_RESULTS_ONLY.md').write_text('\n\n'.join(md),encoding='utf-8')
styles=getSampleStyleSheet(); styles['BodyText'].fontSize=9.2; styles['BodyText'].leading=13; styles['Heading1'].fontSize=15; styles['Heading1'].leading=18
story=[]
for i,(title,body) in enumerate(sections):
    if i in (3,7,8): story.append(PageBreak())
    story.append(Paragraph(escape(title).replace('—','-'),styles['Heading2' if title.startswith(('4.1','4.2','4.3')) else 'Heading1']))
    for para in body.split('\n\n'):
        if para: story.append(Paragraph(escape(para).replace('→',' &gt; ').replace('—','-').replace('\n','<br/>'),styles['BodyText'])); story.append(Spacer(1,7))
    for n,c in images.get(i,[]):
        from PIL import Image as PILImage
        w,h=PILImage.open(FIG/n).size; width=475; height=h/w*width
        if n=='native_crack_tip.png': height=min(height,215); width=height*w/h
        if n=='candidate_c1_c2_meshes.png': story.append(PageBreak())
        story.append(Image(str(FIG/n),width=width,height=height)); story.append(Paragraph(c,styles['Italic'])); story.append(Spacer(1,8))
story.append(Spacer(1,10))
story.append(Paragraph('Evidence: Method B serial jobs 1411934 / 1412465; F1575 same-mesh continuation resolution; Package 72 independent state-transfer audit; mesh_convergence_prototype.json; separate mode1_f1597/correction_prototype.json. Full paths, evidence types and figure hashes are supplied in the accompanying Markdown report and FIGURE_SOURCES.md.',styles['BodyText']))
def footer(canvas,doc):
    canvas.setFont('Helvetica',8); canvas.setFillColor(colors.HexColor('#536777')); canvas.drawString(42,24,'Mode-I adaptive remeshing | Supervisor review | 22 October 2026'); canvas.drawRightString(553,24,str(doc.page))
SimpleDocTemplate(str(OUT/'SUPERVISOR_REPORT_SUCCESSFUL_RESULTS_ONLY.pdf'),pagesize=(595.28,841.89),leftMargin=48,rightMargin=48,topMargin=42,bottomMargin=42).build(story,onFirstPage=footer,onLaterPages=footer)
prov=['# Figure sources and evidence boundaries','All authentic figures are derived from actual project artifacts. Input geometry and offline diagnostics are explicitly distinguished from solver outputs. No synthetic fracture result is used.']
for name,kind,paths,desc in sources:
    prov += [f'## {name}',f'Type: **{kind}**. {desc}',f'Output SHA-256: `{hashlib.sha256((FIG/name).read_bytes()).hexdigest()}`']
    for p in paths: prov += [f'- `{p.as_posix()}` | SHA-256 `{hashlib.sha256((ROOT/p).read_bytes()).hexdigest()}`']
prov += ['## Rebuild','Run `python docs/supervisor_reports/22-10-2026/build_successful_results_report.py`. This renders existing evidence only and submits no jobs.','## Background reference','The prior 8 October report_main.pdf was checked as a 10-page style/context reference; none of its historical figures was relabeled as new work.']
(OUT/'FIGURE_SOURCES.md').write_text('\n\n'.join(prov),encoding='utf-8')
print('Created Markdown, PDF, six figures and provenance note.')
