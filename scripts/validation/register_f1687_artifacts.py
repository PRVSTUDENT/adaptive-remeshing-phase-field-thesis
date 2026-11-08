import hashlib
import os
import datetime

artifacts = [
    ('scripts/validation/audit_f1687_endeneri_candidate.py', 'analysis_script', 'Audit script computing element metrics and transverse width for ENDENERI candidate'),
    ('results/validation/f1687_endeneri_candidate_audit.json', 'validation_artifact', 'Detailed census and metric summary for terminal ENDENERI candidate mesh'),
    ('results/validation/f1687_endeneri_candidate_summary.csv', 'validation_artifact', 'Summary comparison table for terminal ENDENERI candidate mesh'),
    ('scripts/visualization/plot_f1687_endeneri_comparison.py', 'visualization_script', 'Publication plot script generating Figure 5.17 comparing ENDENERI and differential meshes'),
    ('MA_AdaptiveRemeshing_Report_2026/figures/fig_f1687_endeneri_comparison.pdf', 'publication_figure', 'Figure 5.17: Three-panel comparison of Baseline, Differential, and ENDENERI meshes'),
    ('MA_AdaptiveRemeshing_Report_2026/figures/fig_f1687_endeneri_comparison.png', 'publication_figure', 'Figure 5.17 PNG rasterization'),
    ('scripts/remeshing/inventory_mode1_donor_odb.py', 'analysis_script', 'Audit script extracting frames and peak load from companion Mode-I donor ODB'),
    ('results/validation/f1687_mode1_donor_inventory.json', 'validation_artifact', 'Inventory record of companion Mode-I donor frames and loading curve'),
    ('scripts/remeshing/generate_f1687_mode1_blind_mesh.py', 'analysis_script', 'Abaqus CAE script building Mode-I CAD model and running blind differential remeshing'),
    ('models/pandey_kumar_mode1/01_standard_pfm_reference/PK_MODE1_BLIND_DIFF_PHYS.inp', 'model_input_deck', 'Candidate physical mesh for Mode-I straight crack plate from locked differential rules'),
    ('scripts/validation/audit_f1687_mode1_blind_candidate.py', 'analysis_script', 'Audit script computing element metrics and transverse width for blind Mode-I candidate'),
    ('results/validation/f1687_mode1_blind_audit.json', 'validation_artifact', 'Detailed census and metric summary for blind Mode-I candidate mesh'),
    ('results/validation/f1687_mode1_blind_audit.csv', 'validation_artifact', 'Element-level audit CSV for blind Mode-I candidate mesh'),
    ('scripts/visualization/plot_f1687_synthesis_and_generalization.py', 'visualization_script', 'Publication plot script generating Figure 5.18 synthesis and Mode-I generalization wireframe'),
    ('MA_AdaptiveRemeshing_Report_2026/figures/fig_f1687_synthesis_and_generalization.pdf', 'publication_figure', 'Figure 5.18: Synthesis of selective remeshing and blind Mode-I generalization wireframe'),
    ('MA_AdaptiveRemeshing_Report_2026/figures/fig_f1687_synthesis_and_generalization.png', 'publication_figure', 'Figure 5.18 PNG rasterization'),
    ('tests/unit/test_f1687_endeneri_and_generalization_qualification.py', 'unit_test', 'Automated regression test suite validating H1 and H2 qualification and metrics')
]

now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
task_id = 'F1687-METHOD-A-ENDENERI-CONTROL-AND-DIFFERENTIAL-RULE-GENERALIZATION'
agent = 'gemini-antigravity'
reg_path = 'project_coordination/ARTIFACT_REGISTRY.csv'

with open(reg_path, 'a', encoding='utf-8') as f:
    for path, atype, desc in artifacts:
        if not os.path.exists(path):
            print(f'MISSING: {path}')
            continue
        size = os.path.getsize(path)
        with open(path, 'rb') as pf:
            h = hashlib.sha256(pf.read()).hexdigest().upper()
        line = f'{path},{atype},{h},{size},{agent},{task_id},"{desc}",{now_iso}\n'
        f.write(line)
        print(f'Appended: {path}')

print('Done appending.')
