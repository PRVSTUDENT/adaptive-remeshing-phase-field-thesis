import json
from pathlib import Path
import pytest
from scripts.state_transfer.driver_package157_r5_seg1 import AdaptiveContinuationR5, START, TARGETS, admissible

ROOT = Path(__file__).resolve().parents[2]


def controller(tmp_path, solve):
    instance = AdaptiveContinuationR5.__new__(AdaptiveContinuationR5)
    instance.output = tmp_path
    instance.attempt_index = 0
    instance.attempts = []
    instance.committed = []
    instance.solve_step = solve
    return instance


def test_schedule_and_actual_full_checkpoint_load():
    package = ROOT / 'models/pandey_kumar_mode1/157_c4_package157_c1_2_continuation_r5'
    c = AdaptiveContinuationR5(package, package / 'unused', ROOT / 'scripts/validation/extract_package148_iteration.py', max_outer=100)
    c.load()
    assert len(c.h0) == 28224 and len(c.d0) == 7265
    assert c.max_outer == 100
    assert len(TARGETS) == 5
    assert all(abs((TARGETS[i] - (START if i == 0 else TARGETS[i - 1])) - 1e-5) < 1e-15 for i in range(5))
    assert abs(TARGETS[-1] - 0.0019003125442191958) < 1e-15


def test_rejected_step_rolls_back_and_two_smaller_steps_commit(tmp_path):
    calls = []

    def solve(info, d, u, h):
        calls.append((info['target_uy'], dict(d), dict(h)))
        if len(calls) == 1:
            d[1] = 0.9
            h[1, 1] = 999.0
            raise RuntimeError('Step 1 did not achieve coupled convergence within 100 iterations')
        return {1: d[1] + 0.01}, {1: (0.0, info['target_uy'])}, {(1, 1): h[1, 1] + 0.1}, {'target': info['target_uy']}

    c = controller(tmp_path, solve)
    state = ({1: 0.2}, {1: (0.0, START)}, {(1, 1): 1.0})
    result = c.advance(START, START + 1e-5, state)
    assert state[0][1] == 0.2 and state[2][1, 1] == 1.0
    assert calls[1][1] == {1: 0.2} and calls[1][2] == {(1, 1): 1.0}
    assert calls[2][1][1] == pytest.approx(0.21)
    assert result[0][1] == pytest.approx(0.22)
    assert len(list(tmp_path.glob('converged_checkpoint_*.json'))) == 2
    assert [r['status'] for r in c.attempts] == ['REJECTED', 'CONVERGED', 'CONVERGED']
    for path in tmp_path.glob('converged_checkpoint_*.json'):
        assert json.loads(path.read_text())['physical_acceptance'] == 'UNVERIFIED'


def test_minimum_increment_failure_never_creates_checkpoint(tmp_path):
    def solve(*args):
        raise RuntimeError('Step 1 did not achieve coupled convergence within 100 iterations')

    c = controller(tmp_path, solve)
    with pytest.raises(RuntimeError):
        c.advance(START, START + 5e-6, ({1: 0.2}, {1: (0.0, START)}, {(1, 1): 1.0}))
    assert c.attempt_index == 1 and not list(tmp_path.glob('converged_checkpoint_*.json'))


def test_technical_failure_is_not_adaptive_retry(tmp_path):
    def solve(*args):
        raise RuntimeError('Extractor missing')

    c = controller(tmp_path, solve)
    with pytest.raises(RuntimeError, match='Extractor missing'):
        c.advance(START, START + 1e-5, ({1: 0.2}, {1: (0.0, START)}, {(1, 1): 1.0}))
    assert c.attempt_index == 1
