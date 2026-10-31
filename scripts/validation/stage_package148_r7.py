"""Bounded R7 staging using only guarded SSH; preserve all older packages."""
import base64
import json
import shlex
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/validation'))
from stage_package148_r6 import run_guarded_ssh

REMOTE = '/scratch9/pr21vyci/runs/mode1_c4_package148_state_transfer_r7'
OLD = REMOTE.replace('_r7', '_r6')
PACKAGE = ROOT / 'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r7'


def upload(local, remote):
    data = base64.b64encode(zlib.compress(local.read_bytes())).decode()
    # Keep each Windows command below the process command-line limit.
    for offset in range(0, len(data), 6000):
        chunk = data[offset:offset+6000]
        mode = 'w' if offset == 0 else 'a'
        code = "open(%r,%r).write(%r)" % (remote+'.upload', mode, chunk)
        run_code(code)
    code = "import base64,zlib;open(%r,'wb').write(zlib.decompress(base64.b64decode(open(%r).read())))" % (remote, remote+'.upload')
    run_code(code)


def run_code(code):
    # Avoid embedded double quotes in the legacy Windows SSH wrapper's
    # ProcessStartInfo argument string. Remote shell removes these escapes.
    encoded = code.encode().hex()
    return run_guarded_ssh("python3 -c exec\\(bytes.fromhex\\(\\'"+encoded+"\\'\\)\\)")


def stage():
    run_guarded_ssh('test ! -e '+REMOTE+'/pbs_execution.log && mkdir -p '+REMOTE)
    batch = json.loads((PACKAGE/'EXECUTION_MANIFEST.json').read_text())
    for name in batch['files']:
        if name.endswith(('.json', '.sh', '.pbs')):
            upload(PACKAGE/name, REMOTE+'/'+name)
        else:
            run_guarded_ssh('cp -p '+OLD+'/'+name+' '+REMOTE+'/'+name)
    upload(PACKAGE/'EXECUTION_MANIFEST.json', REMOTE+'/EXECUTION_MANIFEST.json')
    run_guarded_ssh('cp -rp '+OLD+'/runtime '+REMOTE+'/runtime')
    for name in batch['runtime_source_hashes']:
        upload(ROOT/name, REMOTE+'/runtime/'+name)
    upload(ROOT/'scripts/validation/validate_package148_r7_startup.py', REMOTE+'/runtime/scripts/validation/validate_package148_r7_startup.py')
    # Actual runtime startup path, on cluster hardware, before datachecks.
    result = run_guarded_ssh('python3 '+REMOTE+'/runtime/scripts/validation/validate_package148_r7_startup.py '+REMOTE)
    proof = json.loads(result)
    assert proof['status'] == 'PASS' and proof['history_mappings'] == 28224
    (ROOT/'results/validation/package148_r7_cluster_startup.json').write_text(json.dumps(proof, indent=2)+'\n')
    print(result, flush=True)
    for role in ('mechanical', 'phase'):
        result = run_guarded_ssh('bash '+REMOTE+'/run_datacheck.sh '+role, timeout=180)
        assert 'AUTHENTIC_DATACHECK_PASS' in result
        print(result, flush=True)
    record_datachecks()


def record_datachecks():
    code = "import hashlib,json;from pathlib import Path;p=Path(%r);names=['P148_MECHANICAL_DC.dat','P148_PHASE_DC.dat'];assert all((p/n).is_file() and 'ANALYSIS DATACHECK COMPLETE' in (p/n).read_text() and '***ERROR' not in (p/n).read_text() for n in names);print(json.dumps({n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in names}))" % REMOTE
    hashes = json.loads(run_code(code))
    (ROOT/'results/validation/package148_r7_datachecks.json').write_text(json.dumps(dict(status='PASS_BOTH', hashes=hashes), indent=2)+'\n')


if __name__ == '__main__':
    if sys.argv[1:] == ['--record-datachecks']:
        record_datachecks()
    else:
        stage()
