"""Distinct R7 packaging correction; never edits R6 or submits jobs."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'models/pandey_kumar_mode1'


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def prepare():
    old = BASE / '148_c4_package148_state_transfer_r6'
    new = BASE / '148_c4_package148_state_transfer_r7'
    new.mkdir(exist_ok=False)
    execution = json.loads((old / 'EXECUTION_MANIFEST.json').read_text())
    # Scientific metadata comes from the validated builder's R5 schema, with
    # every binding recomputed from actual artifacts, never inherited digests.
    package = json.loads((BASE / '148_c4_package148_state_transfer_r5/PACKAGE_MANIFEST.json').read_text())
    for name in execution['files']:
        if name == 'PACKAGE_MANIFEST.json':
            continue
        data = (old / name).read_bytes()
        dest = name.replace('R6', 'R7')
        if name.endswith(('.pbs', '.sh')):
            data = data.replace(b'_r6', b'_r7').replace(b'_R6', b'_R7')
        (new / dest).write_bytes(data)
    package['revision'] = 'R7'
    package['derived_from'] = (old / 'PACKAGE_MANIFEST.json').relative_to(ROOT).as_posix()
    package['derived_from_sha256'] = digest(old / 'PACKAGE_MANIFEST.json').upper()
    package['correction_notes'] = 'R7 repairs runtime manifest contract only; R6 scientific files, 7+8+3 encoding, 7200-second timeout, max_outer=25 and physical gates preserved.'
    for key in ('source_hashes', 'runtime_source_hashes'):
        package[key] = {name: digest(ROOT / name).upper() for name in package[key]}
    package['files'] = {p.name: digest(p).upper() for p in sorted(new.iterdir())}
    (new / 'PACKAGE_MANIFEST.json').write_text(json.dumps(package, indent=2)+'\n', encoding='utf-8')
    execution = json.loads(json.dumps(execution).replace('_r6', '_r7').replace('_R6', '_R7'))
    execution['files'] = {p.name: digest(p) for p in sorted(new.iterdir())}
    execution['runtime_source_hashes'] = dict(package['source_hashes'], **package['runtime_source_hashes'])
    execution['scientific_predecessor_review'] = 'results/validation/package148_r6_terminal_evaluation.json'
    execution['jobs'][0]['command_sha256'] = hashlib.sha256(execution['jobs'][0]['command'].encode()).hexdigest()
    execution['jobs'][0]['purpose'] = package['correction_notes']
    (new / 'EXECUTION_MANIFEST.json').write_text(json.dumps(execution, indent=2)+'\n', encoding='utf-8')
    print(new)


if __name__ == '__main__':
    prepare()
