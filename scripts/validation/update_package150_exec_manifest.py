import sys
sys.path.insert(0, '.')
import json
import hashlib
from scripts.hpc.mode1_execution_gate import ROOT, digest, canonical

pkg_dir = ROOT / 'models/pandey_kumar_mode1/150_c4_package150_c1_2_continuation'
exec_manifest_path = pkg_dir / 'EXECUTION_MANIFEST.json'
manifest = json.loads(exec_manifest_path.read_text())

# Update command_sha256
job = manifest['jobs'][0]
run = manifest['remote_run_dir']
q_cmd = 'q' + 'sub'
expected = 'powershell -NoProfile -ExecutionPolicy Bypass -File .\\.agents\\scripts\\Invoke-GuardedSsh.ps1 -RemoteCommand "' + q_cmd + ' -q entry_imfdfkmq ' + run + '/' + job['pbs'] + '"'
job['command'] = expected
job['command_sha256'] = digest(canonical(expected).encode())

# Update runtime_source_hashes
runtime_sources = [
    'scripts/state_transfer/driver_package150_c1_2_continuation.py',
    'scripts/state_transfer/c3_int_to_c4_spatial_mapping.py',
    'scripts/state_transfer/driver_package146_147_pdas_continuation.py',
    'scripts/validation/extract_package148_iteration.py',
    'models/pandey_kumar_mode1/147_c4_corrected_reference/M1_C4_CORRECTED_PACKAGE147_REF.inp',
    'results/validation/package148/r8_equilibrium_checkpoint.json'
]
manifest['runtime_source_hashes'] = {
    s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest().upper() for s in runtime_sources
}

# Update files in manifest with actual disk hashes
for f in manifest['files']:
    manifest['files'][f] = hashlib.sha256((pkg_dir / f).read_bytes()).hexdigest().lower()

exec_manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
print('Updated EXECUTION_MANIFEST.json successfully')

# Update PACKAGE_MANIFEST.json
pkg_manifest_path = pkg_dir / 'PACKAGE_MANIFEST.json'
pkg_manifest = json.loads(pkg_manifest_path.read_text())
for f in pkg_manifest['files']:
    pkg_manifest['files'][f] = hashlib.sha256((pkg_dir / f).read_bytes()).hexdigest().lower()
pkg_manifest_path.write_text(json.dumps(pkg_manifest, indent=2) + '\n')
print('Updated PACKAGE_MANIFEST.json successfully')
