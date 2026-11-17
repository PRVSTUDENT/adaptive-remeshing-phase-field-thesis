"""Preserve historical registry bytes; append only the newly registered rows."""
from pathlib import Path
import subprocess
r=Path(__file__).resolve().parents[2]
p=r/'project_coordination/ARTIFACT_REGISTRY.csv'
current=p.read_bytes()
new=b''.join(line for line in current.splitlines(keepends=True) if line.startswith(b'F1849_'))
base=subprocess.check_output(['git','show','963becf1d0136068460c9ee4190664c514f74b3d:project_coordination/ARTIFACT_REGISTRY.csv'],cwd=r)
p.write_bytes(base+(b'\n' if not base.endswith(b'\n') else b'')+new)
assert p.read_bytes().startswith(base)
print('Historical registry bytes restored exactly; F1849 rows retained.')
