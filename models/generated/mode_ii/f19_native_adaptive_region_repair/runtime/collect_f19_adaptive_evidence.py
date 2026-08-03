from __future__ import print_function
import argparse
import hashlib
import json
import os
import shutil

EXPECTED = {
    'ABAQUS_PYTHON_COMPATIBILITY.json': 'compatibility_helper',
    'ADAPTIVE_REGION_API_AUDIT.json': 'abaqus_cae',
    'SOURCE_MODEL_INTEGRITY.json': 'abaqus_cae',
    'REMESH_RULE_MANIFEST.json': 'abaqus_cae',
    'NO_EXECUTION_AUDIT.json': 'abaqus_cae',
    'STATUS.json': 'abaqus_cae',
}

def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()

def collect(work_dir, final_dir, compatibility_rc, cae_rc):
    if not os.path.isdir(work_dir) or not os.path.isdir(final_dir):
        raise ValueError('both evidence directories must exist')
    command_rc = {'compatibility_helper': compatibility_rc, 'abaqus_cae': cae_rc}
    inventory = []
    for name in sorted(os.listdir(work_dir)):
        source = os.path.join(work_dir, name)
        if not os.path.isfile(source):
            continue
        target = os.path.join(final_dir, name)
        shutil.copy2(source, target)
        inventory.append({'path': name, 'size': os.path.getsize(source), 'sha256': sha256(source)})
    missing = []
    for name, command in sorted(EXPECTED.items()):
        path = os.path.join(work_dir, name)
        if not os.path.isfile(path):
            missing.append({'expected_path': path, 'searched_directories': [work_dir, final_dir], 'exists': False,
                            'responsible_command': command, 'generating_command_return_code': command_rc[command]})
        else:
            with open(path, 'rb') as handle:
                json.loads(handle.read().decode('utf-8'))
    with open(os.path.join(final_dir, 'WORK_EVIDENCE_INVENTORY.json'), 'wb') as handle:
        handle.write((json.dumps(inventory, indent=2, sort_keys=True) + '\n').encode('utf-8'))
    with open(os.path.join(final_dir, 'MISSING_EVIDENCE_REPORT.json'), 'wb') as handle:
        handle.write((json.dumps(missing, indent=2, sort_keys=True) + '\n').encode('utf-8'))
    if missing:
        return 1
    manifest_path = os.path.join(final_dir, 'EVIDENCE_MANIFEST.sha256')
    names = sorted(EXPECTED) + ['WORK_EVIDENCE_INVENTORY.json', 'MISSING_EVIDENCE_REPORT.json']
    with open(manifest_path, 'wb') as handle:
        for name in names:
            line = '%s  %s\n' % (sha256(os.path.join(final_dir, name)), name)
            handle.write(line.encode('ascii'))
    return 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--work-dir', required=True)
    parser.add_argument('--final-dir', required=True)
    parser.add_argument('--compatibility-rc', type=int, required=True)
    parser.add_argument('--cae-rc', type=int, required=True)
    args = parser.parse_args()
    return collect(args.work_dir, args.final_dir, args.compatibility_rc, args.cae_rc)

if __name__ == '__main__':
    raise SystemExit(main())
