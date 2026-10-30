"""Stage exact committed reviewed files through guarded SSH; no qsub calls.

Remote entrypoint: python3 <this script> --remote COMMIT. Uses git show on
an explicit allowlist; never scans the large cluster tree or overwrites evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

PACKAGE = 'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r1'
RUN = Path('/scratch9/pr21vyci/runs/mode1_c4_package148_state_transfer_r1')


def remote_stage(commit):
    import re
    if not re.fullmatch('[0-9a-f]{40}', commit):
        raise ValueError('Exact committed revision required')
    repo = Path.home()/'projects/adaptive-remeshing'
    def blob(name):
        return subprocess.check_output(['git','-C',str(repo),'show',commit+':'+name], timeout=30)
    batch = json.loads(blob(PACKAGE+'/EXECUTION_MANIFEST.json').decode('utf-8-sig'))
    RUN.mkdir(parents=True, exist_ok=True)
    items = [(RUN/name, PACKAGE+'/'+name, digest) for name,digest in batch['files'].items()]
    items += [(RUN/'EXECUTION_MANIFEST.json', PACKAGE+'/EXECUTION_MANIFEST.json', None)]
    items += [(RUN/'runtime'/name, name, digest) for name,digest in batch['runtime_source_hashes'].items()]
    for destination, name, expected in items:
        data = blob(name)
        actual = hashlib.sha256(data).hexdigest()
        if expected and actual.lower() != expected.lower():
            raise ValueError('Commit differs from reviewed hash: '+name)
        if destination.exists():
            if destination.read_bytes() != data:
                raise ValueError('Existing staged artifact differs; preserve and diagnose: '+str(destination))
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb') as stream: stream.write(data)
    print(json.dumps({'staging':'PASS','commit':commit,'files_verified':len(items)}))


def generate(root):
    import sys
    root=Path(root).resolve();sys.path.insert(0,str(root))
    from scripts.state_transfer.driver_package146_147_pdas_continuation import CoupledAbaqusRuntime
    package=root/PACKAGE
    runtime=CoupledAbaqusRuntime(package, package/'unused_preflight_output',root/'scripts/validation/extract_package148_iteration.py',0.1873079389333725,0.00021270454)
    runtime.load()
    decks={'P148_MECHANICAL_DC.inp':runtime._deck('mechanical',runtime.d0,set(runtime.d0),None,runtime.h0),
           'P148_PHASE_DC.inp':runtime._deck('phase',runtime.d0,set(),{n:(0.,0.) for n in runtime.mesh.nodes},runtime.h0)}
    for name, text in decks.items():
        path=package/name
        data=text.encode('utf-8')
        if path.exists() and path.read_bytes()!=data:raise ValueError('Preserve changed preflight deck: '+name)
        if not path.exists():path.write_bytes(data)
    batch_path=package/'EXECUTION_MANIFEST.json'
    batch=json.loads(batch_path.read_text())
    for name in [*decks,'run_datacheck.sh']:
        batch['files'][name]=hashlib.sha256((package/name).read_bytes()).hexdigest()
    batch['jobs'][0]['input']='P148_MECHANICAL_DC.inp'
    batch_path.write_text(json.dumps(batch,indent=2)+'\n')
    print('Authentic runtime-generated mechanical and phase datacheck decks prepared; no solver executed.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--remote');parser.add_argument('--generate',action='store_true')
    args=parser.parse_args()
    if args.remote:remote_stage(args.remote)
    elif args.generate:generate(Path(__file__).resolve().parents[2])
    else:parser.error('Explicit --generate or --remote COMMIT required')
