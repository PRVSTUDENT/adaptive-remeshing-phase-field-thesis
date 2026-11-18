"""Documentation only: F1860 meeting package from frozen local evidence."""
from pathlib import Path
import json, hashlib, subprocess, re, shutil, html
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.enums import TA_LEFT

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'docs/supervisor_reports/19-11-2026'
OUT.mkdir(parents=True,exist_ok=True)
EVID=Path(__file__).parent
SHA=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
def load(p): return json.loads((ROOT/p).read_text(encoding='utf-8-sig'))
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
S=load('results/validation/f1852_driver_selection_summary.json')
OLD=load('models/pandey_kumar_mode1/261_f1812_crack_path_refinement/PK_F1812_UNIVERSAL_CRACK_PATH_REFINEMENT_RECEIPT.json')
C={i:load(f'models/pandey_kumar_mode1/279_f1849_damage_envelope/case{i}_config.json') for i in (1,2,3,5)}
sources=['scripts/remeshing/generalized_2d_adaptive_framework_driver_selection_f1852.py','scripts/remeshing/generalized_2d_adaptive_framework_damage_envelope_f1849.py','scripts/remeshing/generalized_2d_adaptive_framework_f1846.py','docs/validation/F1812_UNIVERSAL_CRACK_PATH_REFINEMENT_REPORT.md','docs/validation/F1852_DRIVER_SELECTION_REPORT.md','results/validation/f1852_driver_selection_summary.json','scripts/remeshing/run_f1812_single_target.py','docs/validation/F1851_NATIVE_MISESERI_DIAGNOSTICS_REPORT.md']+[f'models/pandey_kumar_mode1/279_f1849_damage_envelope/case{i}_config.json' for i in C]
manifest=[]
for p in sources:
    committed=subprocess.run(['git','cat-file','-e',f'{SHA}:{p}'],cwd=ROOT,capture_output=True).returncode==0
    assert committed,p
    frozen=subprocess.check_output(['git','show',f'{SHA}:{p}'],cwd=ROOT)
    assert frozen.replace(b'\r\n',b'\n')==(ROOT/p).read_bytes().replace(b'\r\n',b'\n'),p
    manifest.append({'path':p,'sha256':digest(ROOT/p),'commit':SHA})

flow=ROOT/'results/figures/fig_f1860_framework_vs_pandey_kumar_flowchart.png'
fig,ax=plt.subplots(figsize=(12,7));ax.set(xlim=(0,12),ylim=(0,8));ax.axis('off')
heads=['Pandey & Kumar | native pipeline','Our F1852 | measured driver selection']
left=['Coarse Job-1: layered UEL + UMAT','In-analysis recovered-stress MISESERI\nFacsimile All_elem; single selected frame','One Abaqus UNIFORM_ERROR remesh\nNative error/base fields; Mode-I target 5%','Build refined layered Job-2\nRun and evaluate response / cost']
right=['Coarse Job-1: measured SDV1 history','max damage >= 0.5: damage-envelope sizing\nOtherwise: gated native final-frame fields\nInvalid native signal with weak damage: BLOCKED','One Abaqus UNIFORM_ERROR remesh\nSynthetic pair on damage branch; raw native fallback','Build refined layered Job-2\nAccuracy / cost comparison still pending']
for col,(title,rows) in enumerate(zip(heads,[left,right])):
    x=.25+col*6
    ax.text(x+2.75,7.65,title,ha='center',va='center',fontsize=15,fontweight='bold',color='#163653')
    for j,t in enumerate(rows):
        y=6.1-j*1.65
        ax.add_patch(FancyBboxPatch((x,y),5.5,1.12,boxstyle='round,pad=.04',facecolor=('#e7eff7' if col==0 else '#e7f2ed'),edgecolor='#516a7a'))
        ax.text(x+2.75,y+.56,t,ha='center',va='center',fontsize=11)
        if j<3: ax.annotate('',xy=(x+2.75,y-.48),xytext=(x+2.75,y-.06),arrowprops={'arrowstyle':'->','color':'#516a7a','lw':1.5})
ax.text(6,.1,'Same remeshing backend; different indicator construction. F1852 does not reproduce the paper.',ha='center',fontsize=12)
fig.savefig(flow,dpi=200,bbox_inches='tight');plt.close(fig)

parts=[]
def h(t): parts.append('## '+t+'\n')
def p(t): parts.append(t+'\n')
def table(headers,rows):
    parts.append('| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)+'\n')
def image(path,caption): parts.append(f'![{caption}]({path})\n\n{caption}\n')
p('# Supervisor meeting | 19 November 2026')
p('F1860 | Evidence cut-off: 18 November 2026 | Master research goal: OPEN | Documentation only; zero new PBS jobs.')
p('**Meeting assessment.** F1852 provides automatic, field-driven mesh generation, but accuracy and total computational savings are not yet demonstrated. Cases 1 and 5 fail far-field coarsening; Case 3 remains expensive. The intended paper Mode-II benchmark is not the geometry currently called Case 2 in our results.')
p('**Evidence labels.** DIRECTLY_VERIFIED means checked against the committed code or recorded audit at the source revision below, not an independent rerun of Abaqus. REPORTED_ONLY means historical report or user/AGY status without independently verified underlying solver evidence. INFERRED means an interpretation. MISSING means unsupported or unavailable. PENDING is an unavailable result expected from the ongoing comparison.')
p(f'Source freeze: `{SHA}`. Individual source and image hashes are recorded in the accompanying evidence manifest. AGY retains its F1859 session; no framework, model, scheduler or shared session state is changed by this report.')
h('1. Our framework: algorithm and indicator construction')
p('DIRECTLY_VERIFIED [S1-S3]. F1852 selects a driver from measured Job-1 SDV1. If maximum available damage is at least D_CORE = 0.5, it preserves the F1849 constructed damage-envelope branch. The core-element fraction is recorded, not used as another fitted threshold. With weaker damage, native fields are accepted only through the native audit gate. Weak damage plus absent/anomalous native fields yields BLOCKED. Invalid non-finite or negative damage also fails. No case coordinates enter this selection rule.')
p('DIRECTLY_VERIFIED [S2]. On the damage branch, Step-2 frames are sampled at indices 0, 5, 10, ... plus the last available frame. The per-element running maximum SDV1 defines the damage envelope. This is automatic history sampling, rather than hand-selected crack-path coordinates or selected MISESERI frames. Driver-strength measurement uses all available SDV1 frames. The frozen remesh is a full-history offline comparison; it does not establish online causal prediction of future cracks.')
table(['Maximum sampled damage d','Target size h_target'],[['d >= 0.5','l0 / 2.5'],['0.1 <= d < 0.5','Linear interpolation: l0 / 1.2 at d=0.1 to l0 / 2.5 at d=0.5'],['0.01 <= d < 0.1','Linear interpolation: background h_bg to l0 / 1.2'],['d < 0.01','Background h_bg']])
p('DIRECTLY_VERIFIED [S2]. With h_old = sqrt(element area), the sizing encoding is MISESERI_synthetic = 100 * error_target * h_old / h_target, MISESAVG_synthetic = 100, and EVOL = element area. Synthetic frameId 9999 is a constructed container, not a physical Job-1 time/frame. Field names make this compatible with Abaqus sizing; they do not turn damage into recovered-stress error. Material thresholds and min/max size limits are calibrated implementation choices.')
p('DIRECTLY_VERIFIED [S1, S3, S5, S6]. F1852 native fallback uses audited raw native fields from one last available donor frame. Case 5 uses the original coarse ODB, Step-2 index 171, frameId 341, time 0.7788659334. It does not perform a new recovery solve here. Native stress-recovery output produced by Abaqus must be distinguished from the historical separate degraded-elasticity recovery solves and their synthesized envelopes.')
p('REPORTED_ONLY [S4]; DIRECTLY_VERIFIED recorded parameters [S7]. F1812 assembled several degraded-modulus continuum recovery states and a maximum-error envelope. Case 1 reported source frame IDs 400, 420, 450, 460 and 470. Historical error targets for Cases 1/2/3/5 were 4.5%, 4.0%, 3.0%, 5.68%. Current frozen F1849 configs instead contain 1.85%, 2.30%, 3.00%, 5.68%; these generations must not be conflated. The F1833 local error/base normalization variant is a separate historical construction.')
p('INFERRED operational sequence: coarse fracture Job-1 -> donor validation and extraction -> measured driver selection -> one native remeshing call -> build layered Job-2 -> evaluate response and total cost. Remeshing alone does not validate fracture accuracy. Total cost must include Job-1, extraction, any recovery solves, remeshing and Job-2.')
h('2. Comparison with Pandey and Kumar')
image('../../results/figures/fig_f1860_framework_vs_pandey_kumar_flowchart.png','Figure 1. Side-by-side pipelines; the damage branch is explicitly synthetic.')
table(['Feature','Pandey and Kumar','Our frozen F1852'],[['Donor','Coarse layered UEL + UMAT Job-1','Coarse fracture Job-1 SDV1 history; gated native alternative'],['Indicator','Native in-analysis stress-recovery error on All_elem','Constructed damage envelope for Cases 1/2/3; raw native Case 5'],['Temporal use','One remeshing state in the one-shot sequence','Sampled damage maximum; native fallback last available frame'],['Backend','Abaqus UNIFORM_ERROR','Abaqus UNIFORM_ERROR'],['Target','Mode-I study adopts 5%; Listing 1 uses example 1.0','Per-case and revision-dependent settings'],['Outcome','Refined Job-2 then response/cost comparison','Job-2 comparison pending; no reproduction claim']])
p('DIRECTLY_VERIFIED paper source [P], Sections 3.2-3.3 and 4.1.3. The shared backend does not imply equivalent indicators. Our primary method is damage-informed adaptive sizing. A uniform damage strategy is not qualified as reproducing F1779 across all four cases; F1779 mixed historical methods. REPORTED_ONLY historical F1779 counts: 20,232 / 17,280 / 9,975 / 15,330.')
h('3. Benchmark identity and sourced setups')
p('**Identity correction (DIRECTLY_VERIFIED [S10]).** The intended paper Case 2 is Section 4.2, an edge-cracked plate under Mode-II shear. Our committed Case 2 config is explicitly OFF_AXIS_HOLE_PLATE under EDGE_PULL. Its mesh and F1859 comparison must retain that identity. No verified F1852 Mode-II result is available. The following blocks separate the intended benchmark from the implemented dataset instead of relabeling the hole mesh.')
names={1:'Case 1: Mode-I edge-cracked plate (paper Section 4.1)',2:'Case 2: intended Mode-II shear (paper Section 4.2); implemented dataset differs',3:'Case 3: rectangular notched plate with a hole and pins (paper Section 4.3)',5:'Case 5: seven-hole plate (paper Section 4.6)'}
for i,c in C.items():
    p('### '+names[i])
    g,m,l,rr=c['geometry'],c['material'],c['loading'],c['remeshing_rule']
    p(f'DIRECTLY_VERIFIED committed setup [S{9+list(C).index(i)}]: plate {g["plate_width"]} x {g["plate_height"]} mm; geometry type {c["geometry_type"]}. '+(f'Notch from left edge to x={g["notch_length"]} mm at y={g.get("notch_y")} mm; slit opening {g.get("notch_slit_opening")} mm.' if g.get('notch_length') else 'No initial notch specified.'))
    if g.get('voids'): p('Hole centres (x,y) and radii in mm: '+ '; '.join(f'({v["x"]}, {v["y"]}), r={v["r"]}' for v in g['voids'])+'.')
    p(f'E={m["youngs_modulus_mpa"]:g} MPa (210 GPa), nu={m["poisson_ratio"]}, Gc={m["gc_kn_per_mm"]} kN/mm, l0={m["length_scale_l0_mm"]} mm; residual stiffness={m["residual_stiffness_k"]}.')
    p(f'Configured displacement control: {l["loading_type"]}; Step-1 u2={l["step1_precritical_u2"]} mm, Step-2 u2={l["step2_fracture_u2"]} mm. '+('Lower pin hole fixed, upper pin hole driven; exact applied pin constraints require deck verification.' if i==3 else 'Bottom u2=0, bottom-left u1=0, top edge pulled vertically.')+' These are committed configuration values, not an assertion that every historical donor used the identical deck.')
    p(f'Frozen remeshing config: target {rr["error_target"]}%; h_min={rr["min_element_size_mm"]} mm, h_max={rr["max_element_size_mm"]} mm; refinementFactor={rr["refinement_factor"]}; coarsening={rr["coarsening_factor"]}. Historical F1812 target: '+{1:'4.5%',2:'4.0%',3:'3.0%',5:'5.68%'}[i]+'.')
    if i==2: p('DIRECTLY_VERIFIED [P, Section 4.2]: intended shear model fixes the bottom and drives horizontal top displacement; l0=0.015 mm. MISSING: corresponding committed Mode-II F1852 donor/config/results. The off-axis-hole count cannot be compared as the same problem.')
    if i==3: p('DIRECTLY_VERIFIED mismatch: paper Section 4.3 states notch width 0.4 mm; committed config uses slit opening 0.2 mm. Establish equivalence before claiming exact setup reproduction.')
table(['Dataset','Coarse donor elements','F1812','F1852','F1779 historical','Paper proposed'],[[i,c['audit']['damage_strength']['element_count'],OLD['selected_cases'][f'case_{i}']['audit'].get('total_physical_elements',OLD['selected_cases'][f'case_{i}']['audit'].get('total_elements')),c['audit']['total_elements'],{1:20232,2:17280,3:9975,5:15330}[i],{1:'13,941 (reported)',2:'19,963 Mode-II [P]; different geometry',3:'12,168 (reported)',5:'MISSING: verified count; config target 15,714 is not paper proof'}[i]] for i,c in [(c['case_id'],c) for c in S['cases']]])
p('Coarse counts are the F1852 recorded damage-history element populations, not independently recounted Job-1 decks. F1812 and F1852 counts are DIRECTLY_VERIFIED recorded audits [S4-S6]; F1779 and paper counts lacking a directly inspected figure are REPORTED_ONLY. The requested 23,618 value is not the Section 4.2 narrative value and is not adopted as Mode-II ground truth.')
h('4. Mesh results, resolution and gates')
p('DIRECTLY_VERIFIED recorded audits [S4-S7]. Gate 06 is mean far-field h / mean process-region h >= 2.0, with h=sqrt(area). A budget pass or low count does not imply adequate resolution. Historical critical masks and current process masks differ; their percentages below are not matched-mask improvement claims.')
table(['Dataset case','F1812 critical count coverage','F1812 Gate 06','F1852 process count % <=l0 / <=l0/2','F1852 process area % <=l0 / <=l0/2','F1852 Gate 06'],[[c['case_id'],{1:'Full ligament 97.19% <=l0/2',2:'Outer ligament 100% <=l0/2',3:'Secondary 93.84% <=l0',5:'Inter-hole 99.04% <=l0'}[c['case_id']],{1:'2.3867 PASS',2:'1.9349 FAIL',3:'1.4462 FAIL',5:'2.1174 PASS'}[c['case_id']],f'{c["coverage"]["process"]["count_pct_l0"]:.2f} / {c["coverage"]["process"]["count_pct_half_l0"]:.2f}',f'{c["coverage"]["process"]["area_pct_l0"]:.2f} / {c["coverage"]["process"]["area_pct_half_l0"]:.2f}',f'{c["audit"]["refinement_ratio_far_to_core"]:.4f} '+('PASS' if c['audit']['refinement_ratio_far_to_core']>=2 else 'FAIL')] for c in S['cases']])
p('Gate 07 was redefined in F1812 from a universal <=30,000 elements to 30,000 for Cases 1/5 and 80,000 for Cases 2/3 [S7, lines 373-375]. All four F1812 and F1852 counts fit those redefined budgets. Under the original universal cap, F1812 Cases 2/3 fail and F1852 Case 3 fails. This is a gate redefinition, not an efficiency gain.')
table(['Case','F1852 quads %','min detJ','max aspect ratio','remesh + audit seconds'],[[c['case_id'],f'{c["audit"]["quad_percent"]:.2f}',f'{c["audit"]["min_det_j"]:.3g}',f'{c["audit"]["max_aspect_ratio"]:.3f}',f'{c["audit"]["remesh_seconds"]:.3f}'] for c in S['cases']])
p('All four recorded meshes have zero non-positive Jacobians. Timings exclude donor solution, initial hashing and damage extraction; they cannot establish end-to-end speedup. F1852 Case 3 has 45,009 elements despite its narrowly passing 2.004 coarsening ratio. Current Case 1 process count coverage <=l0/2 is 58.65%; historical full-ligament 97.19% is a different mask and cannot be claimed preserved from this table.')
for i in C: image(f'../../results/figures/fig_f1852_case_{i}_mesh.png',f'Figure {list(C).index(i)+2}. Existing frozen F1852 Case {i} mesh, reused unchanged. '+('Repository off-axis-hole Mode-I dataset; not paper Mode-II.' if i==2 else 'Recorded geometry and resolution audit above apply.'))
h('5. F1859 reference versus Job-2 comparison: pending')
p('REPORTED_ONLY status: the user/AGY reports eight comparison jobs in parallel (four adaptive Job-2 and four reference solves), cumulative PBS 45. No completed committed F1859 comparison report is available at this report cut-off. The local F1859 staging receipt still labels jobs STAGED_READY_FOR_EXECUTION; staging alone does not independently prove live scheduler state. No scheduler commands were issued for this documentation task.')
p('INFERRED reference qualification issue: the staging receipt describes historical target-aligned comparison meshes, including Case 1 with 13,960 and Case 3 with 12,110 elements. Those are not demonstrably highly refined or converged references. Before interpreting accuracy differences, require mesh convergence, matched material/formulation/loading and donor provenance. Do not infer accuracy from agreement with a potentially under-resolved comparator.')
for i in C:
    p(f'### Comparison dataset Case {i}'+(' (off-axis-hole Mode-I, not paper Mode-II)' if i==2 else ''))
    table(['Metric','Reference solve','Framework Job-2','Relative difference'],[[k,'PENDING','PENDING','PENDING'] for k in ['Physical element count','Walltime (s)','CPU time (s)','Peak reaction load','Displacement at peak (mm)','Crack path / coverage']])
p('PENDING means completed results unavailable; running status is REPORTED_ONLY. If a run does not complete, replace with MISSING and its solver reason. Do not substitute configured mesh counts for extracted comparison results. Relative scalar difference = 100*(adaptive-reference)/reference; zero denominator -> undefined. Walltime and CPU definitions must match across jobs; crack comparison needs a common damage threshold, geometric distance and same-region coverage rather than a scalar percent invented from pictures.')
h('6. Limitations and open evidence')
p('DIRECTLY_VERIFIED: Case 1 Gate 06 = 1.9187 FAIL and Case 5 = 1.9387 FAIL [S5-S6]. Case 3 remains diffuse and expensive at 45,009 elements. Shared code and mesh-quality passes do not qualify all geometries or prove fracture accuracy. Full-history extraction includes available crack wake and cannot establish causal online refinement.')
p('INFERRED historical mechanism: F1833 local error/base ratios can be amplified by small local stress denominators and retained by a maximum across states. This is a strong diagnostic suspect for that historical variant, not established causation and not the F1852 damage-envelope formula. A matched ablation is required before attribution.')
p('DIRECTLY_VERIFIED recorded F1851 diagnostic [S8]: the Case 2 pilot has CPE3 triangles with zero stress tensors and zero MISESAVG. Treat native error validity as a prerequisite; an ODB field existing is insufficient. F1852 Case 5 records no such zero-stress/base elements. This does not independently establish mechanical neutrality or completed fracture evolution.')
p('REPORTED_ONLY unresolved provenance: the F1850 bridge transport response remains unreconciled; this report proceeds on the direct user request, not a manufactured review approval. F1828 Job-2 status was previously unknown. A newer local F1859 staging receipt reports no usable completed F1828 Job-2 outputs (Case 1 datacheck only; other cases not run); independent scheduler/solver verification is MISSING here, so no completed-result claim is made.')
p('MISSING acceptance evidence: independently reviewed four-case accuracy/cost comparison, a verified Mode-II dataset, converged reference qualification, matched critical-region coverage across revisions, and reliable generalization beyond the tested configurations. Historical F1779 Case 3 efficiency is not reproduced by the present uniform damage strategy.')
h('7. Supervisor decisions and timeline')
table(['When','Decision / action','Measurable evidence needed'],[['19 November meeting','Confirm the four intended benchmark identities; separate Mode-II from off-axis-hole dataset','Correct geometry, loading, formulation and input hashes before any paper-equivalence claim'],['After F1859 completes','Review completed response/cost results and reference validity','Force-displacement, peak metrics, crack geometry, convergence and full pipeline cost'],['Before research freeze: 13 December 2026','Prioritize Case 1/5 coarsening and Case 3 efficiency','Gate 06 >=2 without critical-resolution loss; lower count/cost with matched-mask coverage'],['If supervisor directs native reproduction','Scope remaining native interface / single-state remeshing / Job-2 tasks (Tasks 4-6)','Full-scale damage-converged donors, valid native stress fields and mechanical parity; no new jobs authorized here'],['Submission: 13 January 2027','Consolidate only validated conclusions and preserved failures','Reviewed frozen evidence package and reproducible provenance']])
p('The master goal remains OPEN. The meeting should select a numerical hypothesis after the pending comparison; report preparation is not framework finalization.')
h('Sources and evidence register')
p('[P] Pandey, A. and Kumar, S. (2025), A Simple and Robust Mesh Refinement Implementation in Abaqus for Phase Field Modelling of Brittle Fracture, CMES 144(3), 3251-3286. DOI: 10.32604/cmes.2025.067858. https://www.techscience.com/CMES/v144n3/63944/html (checked 18 November 2026; Sections 3.2-3.3, 4.1.3, 4.2, 4.3 and 4.6).')
for n,path in enumerate(sources,1): p(f'[S{n}] `{path}`; committed revision {SHA[:12]}; SHA256 {digest(ROOT/path)}.')
p('Additional recorded audit: `models/pandey_kumar_mode1/261_f1812_crack_path_refinement/PK_F1812_UNIVERSAL_CRACK_PATH_REFINEMENT_RECEIPT.json`. Live/uncommitted status only: `models/pandey_kumar_mode1/286_f1859_four_benchmark_reference_comparison/f1859_suite_receipt.json`; not used as completed numerical evidence. Meeting scope is explicitly authorized by the attached F1860 request.')
md='\n'.join(parts)
target=ROOT/'docs/validation/F1860_SUPERVISOR_MEETING_REPORT.md';target.write_text(md,encoding='utf-8')
(OUT/'supervisor_report_19-11-2026.md').write_text(md.replace('../../results/','../../../results/'),encoding='utf-8')

styles=getSampleStyleSheet()
styles['BodyText'].fontSize=9;styles['BodyText'].leading=13;styles['BodyText'].spaceAfter=7
styles['Heading1'].fontSize=19;styles['Heading1'].leading=23
styles['Heading2'].fontSize=14;styles['Heading2'].leading=18
styles['Heading3'].fontSize=11;styles['Heading3'].leading=15
styles.add(styles['BodyText'].clone('SmallCell',fontSize=7.4,leading=10,spaceAfter=2))
def clean(t):
    t=t.replace('/', '/ ').replace('_', '_ ')
    t=html.escape(t);t=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',t);t=re.sub(r'`(.*?)`',r'\1',t)
    # Long hashes/paths must wrap without exceeding table/page widths.
    t=re.sub(r'([a-f0-9]{32,64})',lambda m:'<font size="6">'+' '.join(m[0][j:j+16] for j in range(0,len(m[0]),16))+'</font>',t)
    return t
story=[]; lines=md.splitlines();k=0
while k<len(lines):
    line=lines[k]
    if not line.strip():k+=1;continue
    if line.startswith('## 5.') or line.startswith('## 6.') or line.startswith('### Comparison dataset Case 3') or line.startswith('## Sources and evidence register'):
        story.append(PageBreak())
    if line.startswith('|'):
        rows=[]
        while k<len(lines) and lines[k].startswith('|'):
            vals=[v.strip() for v in lines[k].strip('|').split('|')]
            if not all(re.fullmatch(r'[:\- ]+',v) for v in vals): rows.append(vals)
            k+=1
        n=len(rows[0]); width=487
        cells=[[Paragraph(clean(v),styles['SmallCell']) for v in row] for row in rows]
        t=Table(cells,colWidths=[width/n]*n,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dce7ef')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#becbd3')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        story.append(KeepTogether([t,Spacer(1,10)]));continue
    if line.startswith('!['):
        path=re.search(r'\]\((.*?)\)',line)[1];ip=(target.parent/path).resolve();iw,ih=ImageReader(str(ip)).getSize();w=487;hh=w*ih/iw
        if hh>520:w*=520/hh;hh=520
        story.extend([Image(str(ip),width=w,height=hh),Spacer(1,7)])
    elif line.startswith('# '):story.append(Paragraph(clean(line[2:]),styles['Heading1']))
    elif line.startswith('## '):story.append(Paragraph(clean(line[3:]),styles['Heading2']))
    elif line.startswith('### '):story.append(Paragraph(clean(line[4:]),styles['Heading3']))
    else:story.append(Paragraph(clean(line),styles['BodyText']))
    k+=1
pdf=ROOT/'docs/validation/F1860_SUPERVISOR_MEETING_REPORT.pdf'
def footer(canvas,doc):
    canvas.saveState();canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#516675'));canvas.drawString(54,31,'Supervisor meeting | 19 November 2026 | F1860 | Research goal OPEN');canvas.drawRightString(541,31,str(doc.page));canvas.restoreState()
SimpleDocTemplate(str(pdf),pagesize=(595,842),rightMargin=54,leftMargin=54,topMargin=45,bottomMargin=49,title='Supervisor meeting - 19 November 2026',author='Adaptive remeshing research').build(story,onFirstPage=footer,onLaterPages=footer)
shutil.copyfile(pdf,OUT/'supervisor_report_19-11-2026.pdf')
imgs=[]
for i in C:
    path=ROOT/f'results/figures/fig_f1852_case_{i}_mesh.png'
    expected=next(x['sha256'] for x in S['images'] if x['path']==str(path.relative_to(ROOT)).replace('\\','/'))
    assert digest(path)==expected
    imgs.append({'case':i,'path':path.relative_to(ROOT).as_posix(),'sha256':expected,'reuse_unchanged':True})
(EVID/'source_manifest.json').write_text(json.dumps({'source_revision':SHA,'sources':manifest,'reused_mesh_images':imgs,'scope':'User-authorized documentation parallel to AGY F1859; no shared ownership changes','excluded_from_writes':['framework','models except F1860 evidence','AGY session','HPC']},indent=2))
(OUT/'README.md').write_text('# Supervisor meeting - 19 November 2026\n\nOpen supervisor_report_19-11-2026.pdf. Markdown is provided for revisions. Canonical report: docs/validation/F1860_SUPERVISOR_MEETING_REPORT.md. Existing F1852 images are reused unchanged; no new numerical results.\n')
summary={'task_id':'F1860-SUPERVISOR-MEETING-REPORT','meeting_date':'2026-11-19','source_revision':SHA,'new_pbs':0,'master_goal_status':'OPEN','F1859':'PENDING; no completed committed comparison report','identity_conflict':'Repository Case 2 is Mode-I off-axis-hole, not paper Section 4.2 Mode-II','artifacts':[{ 'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)} for p in (target,pdf,flow)],'mesh_images_reused_unchanged':True}
(ROOT/'results/validation/f1860_supervisor_meeting_report_summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
