# -*- coding: utf-8 -*-
"""Register F1642 execution evidence in ARTIFACT_REGISTRY.csv."""
import hashlib
from pathlib import Path

files = [
    ('F1642-pilot-extracted-summary', 'results/validation/f1642_pilot_extracted_summary.json', 'EVIDENCE', 'COMPLETED'),
    ('F1642-pilot-uel-energy-balance', 'results/validation/f1642_pilot_uel_energy_balance.csv', 'EVIDENCE', 'COMPLETED'),
    ('F1642-pilot-pbs-execution-log', 'results/validation/f1642_pilot_pbs_execution.log', 'EVIDENCE', 'COMPLETED'),
    ('F1642-pilot-sta-file', 'results/validation/f1642_pilot_PK_HOLE_METHOD_A_PROD.sta', 'EVIDENCE', 'COMPLETED'),
    ('F1642-pilot-dat-file', 'results/validation/f1642_pilot_PK_HOLE_METHOD_A_PROD.dat', 'EVIDENCE', 'COMPLETED'),
    ('F1642-pilot-rf-displacement-csv', 'results/validation/f1642_pilot_rf_displacement.csv', 'EVIDENCE', 'COMPLETED'),
    ('F1642-pilot-damage-distribution', 'results/validation/f1642_pilot_damage_distribution.json', 'EVIDENCE', 'COMPLETED'),
    ('F1642-pilot-top-damage-elements', 'results/validation/f1642_pilot_top_damage_elements.csv', 'EVIDENCE', 'COMPLETED'),
    ('F1642-bridge-dispatch-script', 'scripts/controller/Dispatch-F1642-PilotHandoff.ps1', 'SCRIPT', 'READY')
]

registry_path = Path('project_coordination/ARTIFACT_REGISTRY.csv')
existing = registry_path.read_text(encoding='utf-8')

new_entries = []
for art_id, rel_path, art_type, status in files:
    if f'"{rel_path}"' in existing:
        continue
    p = Path(rel_path)
    if not p.exists():
        continue
    sha = hashlib.sha256(p.read_bytes()).hexdigest().upper()
    entry = f'"{art_id}","Mode-I","{rel_path}","{art_type}","{status}","gemini-antigravity","d04a699b662fe213cbfbc61737be74a62174c81a","{sha}","","F1642 Method A hole physical state pilot authentic execution evidence"'
    new_entries.append(entry)

if new_entries:
    with open(registry_path, 'a', encoding='utf-8') as f:
        for entry in new_entries:
            f.write(entry + '\n')
    print(f'Added {len(new_entries)} evidence artifacts to ARTIFACT_REGISTRY.csv')
else:
    print('All artifacts already in ARTIFACT_REGISTRY.csv')
