"""Package 157 Revision 7 continuation driver.

Implements +10 nm forward continuation step from authentic accepted Checkpoint 01 of R6
(uy = 0.0018653125442191958 mm) to target uy = 0.0018753125442191958 mm
with max_outer = 120 outer iterations and max_phase = 20.
Reuses frozen UEL and authentic R6 converged restart state.
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

# Baseline: Authentic R6 endpoint
START = 0.0018653125442191958
# Target: +10 nm single step
TARGETS = [0.0018753125442191958]


def admissible(old_d, old_h, d, h):
    validate_damage(d, old_d)
    if set(h) != set(old_h) or min(d[n] - old_d[n] for n in d) < -1e-6:
        raise ValueError('Damage/state coverage or healing gate failed')
    if any(not math.isfinite(v) or v < old_h[k] for k, v in h.items()):
        raise ValueError('Committed history monotonicity gate failed')


class AdaptiveContinuationR7(StageC12ContinuationController):
    def load(self):
        super(AdaptiveContinuationR7, self).load()
        manifest_path = self.package / 'PACKAGE_MANIFEST.json'
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text())
            for name, expected in manifest.get('runtime_source_hashes', {}).items():
                actual = self._compute_sha256(ROOT / name).upper()
                if actual != expected.upper():
                    raise ValueError('Runtime source changed: ' + name)
            if manifest.get('baseline_uy_mm') != START or manifest.get('targets_mm') != TARGETS:
                raise ValueError('Unreviewed R7 schedule')
        if len(self.d0) != 7265 or len(self.h0) != 28224:
            raise ValueError('Incomplete authentic checkpoint: nodes=%d, history=%d' % (len(self.d0), len(self.h0)))
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
            self.write_evidence('MAX_OUTER_EXCEEDED')
            raise
        admissible(d, h, next_d, next_h)
        self.attempts.append(dict(attempt=index, start=start, target=target,
                                  level=level, status='CONVERGED', summary=summary))
        self.committed.append(summary)
        checkpoint = dict(schema=1, target_uy_mm=target,
            displacement=[[n] + list(next_u[n]) for n in sorted(next_u)],
            damage=[[n, next_d[n]] for n in sorted(next_d)],
            history=[[e, g, next_h[e, g]] for e, g in sorted(next_h)],
            coupled_convergence=True, physical_acceptance='UNVERIFIED',
            physical_review='Matching-load reference comparison <=5% force and <=2% raw energy required')
        path = self.output / ('converged_checkpoint_%02d.json' % index)
        with path.open('x') as stream:
            json.dump(checkpoint, stream, indent=2)
        self.write_evidence('COUPLED_CONTINUATION_COMPLETE_PHYSICAL_REVIEW_REQUIRED')
        return next_d, next_u, next_h

    def write_evidence(self, status):
        (self.output / 'runtime_report.json').write_text(json.dumps(dict(schema=1,
            status=status, attempts=self.attempts, converged_steps=self.committed,
            physical_acceptance='UNVERIFIED', automatic_retry=False), indent=2))

    def run(self):
        self.load()
        self.output.mkdir(parents=True, exist_ok=False)
        self.deadline = time.monotonic() + self.timeout
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
    controller = AdaptiveContinuationR7(max_outer=120, max_phase=20, timeout=27000,
                                        memory_gb=16, **vars(args))
    if startup_only:
        controller.load()
        print(json.dumps(dict(status='PASS', nodes=len(controller.d0), history=len(controller.h0),
                              baseline=START, targets=TARGETS, solver_executed=False,
                              max_outer=controller.max_outer)))
    else:
        controller.run()
