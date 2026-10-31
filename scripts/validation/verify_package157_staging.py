"""Cluster-compatible immutable-file and datacheck evidence reader."""
import hashlib
import json
from pathlib import Path
import socket
import sys

package=Path(sys.argv[1])
batch=json.loads((package/'EXECUTION_MANIFEST.json').read_text())
for name, expected in batch['files'].items():
    assert hashlib.sha256((package/name).read_bytes()).hexdigest()==expected, name
for name, expected in batch['runtime_source_hashes'].items():
    assert hashlib.sha256((package/'runtime'/name).read_bytes()).hexdigest().upper()==expected, name
result=dict(schema=1, files='PASS', runtime='PASS', host=socket.gethostname())
if len(sys.argv)>2:
    directory=package/sys.argv[2]
    result['datachecks']={}
    for role in ('MECHANICAL','PHASE'):
        name='P157_'+role+'_DC.dat'
        data=(directory/name).read_bytes()
        assert b'ANALYSIS DATACHECK COMPLETE' in data and b'***ERROR' not in data
        result['datachecks'][name]=hashlib.sha256(data).hexdigest()
print(json.dumps(result,indent=2))
