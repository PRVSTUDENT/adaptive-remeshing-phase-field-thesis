import hashlib
import os
import datetime

artifacts = [
    ('models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_PHYS.inp', 'input_deck', 'Original 2,906 physical element mesh extracted from preanalysis ODB'),
    ('models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.inp', 'input_deck', 'Coupled 3-layer UEL/UMAT Job 1 deck (8,718 elements) on 2,906 physical mesh'),
    ('models/pandey_kumar_mode1/176_method_a_plate_with_hole/METHOD_A_HOLE_COARSE_AUTHORIZATION.json', 'authorization_record', 'Qualified HPC execution manifest for Job 1421063.mmaster02'),
    ('scripts/remeshing/generate_coarse_job1_deck.py', 'script', 'Deck generator for coarse physical and 3-layer UEL models'),
    ('scripts/remeshing/extract_coarse_job1_results.py', 'extractor_script', 'Abaqus Python extractor for RF-U, field history, and MISESERI'),
    ('scripts/remeshing/execute_method_a_native_remesh.py', 'script', 'Abaqus CAE driver attempting native RemeshingRule on coarse coupled ODB'),
    ('scripts/validation/analyze_coarse_crack_topology.py', 'validator_script', 'Topological analyzer for crack initiation, propagation, and branch paths'),
    ('scripts/visualization/plot_coarse_method_a_figures.py', 'script', 'Publication figure generator rendering Figures 1 to 6 (PNG and PDF)'),
    ('results/validation/coarse_job1_summary.json', 'validation_artifact', 'Execution and convergence summary for coarse coupled Job 1'),
    ('results/validation/coarse_job1_rf_u.csv', 'validation_artifact', 'Reaction force vs displacement history for coarse coupled Job 1'),
    ('results/validation/coarse_job1_fields.json', 'validation_artifact', 'Nodal and element field distributions across key increments'),
    ('results/validation/coarse_crack_topology_summary.json', 'validation_artifact', 'Topological analysis of primary and secondary crack damage clusters'),
    ('docs/MA_AdaptiveRemeshing_Report_2026_main/figures/fig_coarse_method_a_figure1_damage_evolution.png', 'figure', 'FIGURE 1: Coarse coupled Job 1 damage field evolution across loading stages'),
    ('docs/MA_AdaptiveRemeshing_Report_2026_main/figures/fig_coarse_method_a_figure2_coupled_miseseri_and_rf.png', 'figure', 'FIGURE 2: Coupled MISESERI field (identically zero) and reaction force-displacement curve'),
    ('docs/MA_AdaptiveRemeshing_Report_2026_main/figures/fig_coarse_method_a_figure3_mesh_comparison.png', 'figure', 'FIGURE 3: Original 2,906 mesh vs native adapted mesh showing zero refinement'),
    ('docs/MA_AdaptiveRemeshing_Report_2026_main/figures/fig_coarse_method_a_figure4_size_distribution.png', 'figure', 'FIGURE 4: Element size distribution h_max and h_area for coarse Job 1 mesh'),
    ('docs/MA_AdaptiveRemeshing_Report_2026_main/figures/fig_coarse_method_a_figure5_zoomed_notch_hole_damage.png', 'figure', 'FIGURE 5: Zoomed view of damage entering hole and secondary right-flank crack'),
    ('docs/MA_AdaptiveRemeshing_Report_2026_main/figures/fig_coarse_method_a_figure6_damage_support_overlay.png', 'figure', 'FIGURE 6: Authentic coarse Job 1 damage support overlaid on 2,906-element mesh')
]

now_iso = datetime.datetime.now().astimezone().isoformat()
task_id = 'F1653-PANDEY-KUMAR-ORIGINAL-METHOD-A-COARSE-COUPLED-JOB1'

with open('project_coordination/ARTIFACT_REGISTRY.csv', 'a', encoding='utf-8') as f:
    for rel_path, art_type, desc in artifacts:
        if os.path.exists(rel_path):
            with open(rel_path, 'rb') as af:
                data = af.read()
                h = hashlib.sha256(data).hexdigest().upper()
                sz = len(data)
            clean_path = rel_path.replace('\\', '/')
            line = f'{clean_path},{art_type},{h},{sz},gemini-antigravity,{task_id},"{desc}",{now_iso}\n'
            f.write(line)
            print(f'Registered: {clean_path}')
        else:
            print(f'Missing: {rel_path}')
