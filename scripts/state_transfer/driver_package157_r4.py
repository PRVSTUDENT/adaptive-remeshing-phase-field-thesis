"""Reviewed R4 loading subdivision, reusing the frozen R3 coupled solver.

Only a converged step commits d/u/H. Rejected outer iterates are never restart
data. No scheduler calls, tolerance changes, damage clipping or solver retry.
"""
from __future__ import print_function
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.state_transfer.driver_package150_c1_2_continuation import StageC12ContinuationController
from scripts.state_transfer.driver_package146_147_pdas_continuation import validate_damage

START = 0.0018503125442191958
TARGETS = [START + i * 1e-5 for i in range(1, 6)] + [START + 1e-4, .002]


def admissible(old_d, old_h, d, h):
    validate_damage(d, old_d)
    if set(h) != set(old_h) or min(d[n]-old_d[n] for n in d) < -1e-6:
        raise ValueError('Damage/state coverage or healing gate failed')
    if any(not math.isfinite(v) or v < old_h[k] for k, v in h.items()):
        raise ValueError('Committed history monotonicity gate failed')


class AdaptiveContinuation(StageC12ContinuationController):
    def load(self):
        super(AdaptiveContinuation, self).load()
        manifest = json.loads((self.package/'PACKAGE_MANIFEST.json').read_text())
        for name, expected in manifest['runtime_source_hashes'].items():
            if self._compute_sha256(ROOT/name).upper() != expected.upper():
                raise ValueError('Runtime source changed: '+name)
        if len(self.d0) != 7265 or len(self.h0) != 28224:
            raise ValueError('Incomplete authentic checkpoint')
        if manifest['baseline_uy_mm'] != START or manifest['targets_mm'] != TARGETS:
            raise ValueError('Unreviewed R4 schedule')
        self.attempts = []
        self.attempt_index = 0
        self.committed = []

    def advance(self, start, target, state, level=0):
        self.attempt_index += 1
        index = self.attempt_index
        d, u, h = state
        try:
            next_d, next_u, next_h, summary = self.solve_step(
                dict(step=index, target_uy=target), dict(d), dict(u), dict(h))
        except RuntimeError as error:
            if 'did not achieve coupled convergence within' not in str(error):
                raise
            self.attempts.append(dict(attempt=index, start=start, target=target,
                                      level=level, status='REJECTED', reason=str(error)))
            if level >= 2 or (target-start)/2 < 5e-6-1e-15:
                self.write_evidence('SUBDIVISION_LIMIT_REACHED')
                raise
            midpoint = (start+target)/2
            middle = self.advance(start, midpoint, state, level+1)
            return self.advance(midpoint, target, middle, level+1)
        admissible(d, h, next_d, next_h)
        self.attempts.append(dict(attempt=index, start=start, target=target,
                                  level=level, status='CONVERGED', summary=summary))
        self.committed.append(summary)
        checkpoint = dict(schema=1, target_uy_mm=target,
            displacement=[[n]+list(next_u[n]) for n in sorted(next_u)],
            damage=[[n,next_d[n]] for n in sorted(next_d)],
            history=[[e,g,next_h[e,g]] for e,g in sorted(next_h)],
            coupled_convergence=True, physical_acceptance='UNVERIFIED',
            physical_review='Matching-load reference comparison <=5% force and <=2% raw energy required')
        path = self.output/('converged_checkpoint_%02d.json' % index)
        with path.open('x') as stream:
            json.dump(checkpoint, stream, indent=2)
        self.write_evidence('CONTINUING')
        return next_d, next_u, next_h

    def write_evidence(self, status):
        (self.output/'runtime_report.json').write_text(json.dumps(dict(schema=1,
            status=status, attempts=self.attempts, converged_steps=self.committed,
            physical_acceptance='UNVERIFIED', automatic_retry=False), indent=2))

    def run(self):
        self.load()
        self.output.mkdir(parents=True, exist_ok=False)
        self.deadline = time.monotonic()+self.timeout
        state = dict(self.d0), dict(self.u0), dict(self.h0)
        start = START
        for target in TARGETS:
            state = self.advance(start, target, state)
            start = target
        self.write_evidence('COUPLED_CONTINUATION_COMPLETE_PHYSICAL_REVIEW_REQUIRED')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--extractor', required=True)
    parser.add_argument('--startup-only', action='store_true')
    args = parser.parse_args()
    startup_only = args.startup_only
    delattr(args, 'startup_only')
    controller = AdaptiveContinuation(max_outer=50, max_phase=20, timeout=25200,
                                      memory_gb=16, **vars(args))
    if startup_only:
        controller.load()
        print(json.dumps(dict(status='PASS', nodes=len(controller.d0), history=len(controller.h0),
                              baseline=START, targets=TARGETS, solver_executed=False)))
    else:
        controller.run()
