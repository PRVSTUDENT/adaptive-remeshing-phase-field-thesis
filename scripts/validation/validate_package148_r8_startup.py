"""Exercise actual runtime.load and independently decode all history cards for R8.

Works on cluster Python 3.6; no Abaqus solve, scheduler call or package writes.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.state_transfer.driver_package146_147_pdas_continuation import CoupledAbaqusRuntime


def validate(package):
    package = Path(package).resolve()
    runtime = CoupledAbaqusRuntime(package, package / 'unused_startup_output',
        ROOT / 'scripts/validation/extract_package148_iteration.py',
        0.1873079389333725, 0.00021270454000000001, timeout=7200, max_outer=40)
    runtime.load()
    expected_uel = 'ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6'
    assert hashlib.sha256((package/'f42_mixed_uel.for').read_bytes()).hexdigest() == expected_uel
    lines = [l for l in (package/'initial_conditions_solution.inc').read_text().splitlines()
             if l.strip() and not l.startswith('*')]
    assert len(lines) == 7056 * 3
    count = 0
    seen = set()
    for i in range(0, len(lines), 3):
        rows = [[float(x) for x in line.split(',') if x.strip()] for line in lines[i:i+3]]
        assert [len(r) for r in rows] == [8, 8, 3]
        eid = int(rows[0][0])
        assert eid not in seen
        seen.add(eid)
        state = rows[0][1:] + rows[1] + rows[2]
        for gp in range(1, 5):
            # Frozen includes use %.8e; compare against that exact encoding.
            assert state[7+gp] == float('%.8e' % runtime.h0[eid, gp])
            count += 1
    assert count == len(runtime.h0) == 28224
    return dict(schema=1, status='PASS', startup_path='CoupledAbaqusRuntime.load',
                history_mappings=count, elements=len(seen), nodes=len(runtime.d0),
                frozen_uel_sha256=expected_uel, solver_executed=False,
                timeout=runtime.timeout, max_outer=runtime.max_outer,
                python=sys.version, package=str(package))


if __name__ == '__main__':
    print(json.dumps(validate(sys.argv[1]), indent=2))
