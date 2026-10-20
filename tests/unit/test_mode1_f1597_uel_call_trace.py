"""Synthetic records only. Never claim these fixtures are Abaqus output."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts/validation'))
import probe_mode1_f1597_uel_call_trace as trace


def fixture_rows():
    rows = []
    def row(event, edge, jtype, hc, ht):
        v = dict.fromkeys(trace.HEADER, 0.)
        v.update(seq=len(rows)+1, event=event, edge=edge, step=1, inc=1,
                 element=336, jtype=jtype)
        for i in range(1, 5): v[f'hc{i}'] = hc; v[f'ht{i}'] = ht
        rows.append([str(v[k]) for k in trace.HEADER])
    row(1, 0, 2, 0, 0); row(1, 1, 2, 0, 1)
    row(1, 0, 1, 0, 1); row(1, 1, 1, 0, 1)
    row(102, 0, 0, 0, 1); row(102, 1, 0, 1, 1)
    return rows


class TraceTests(unittest.TestCase):
    def test_source_restores_byte_for_byte(self):
        parent = (ROOT/trace.PARENT/'f42_experimental_offset_uel.for').read_bytes()
        instrumented = trace.instrument(parent)
        self.assertEqual(trace.strip_instrumentation(instrumented), parent)
        self.assertIn(b'STATUS=\'NEW\'', instrumented)
        self.assertIn(b'SEQ.GE.2048', instrumented)
        self.assertNotEqual(trace.sha(instrumented), trace.sha(parent))

    def test_changed_parent_rejected(self):
        with self.assertRaisesRegex(ValueError, 're-reviewed'):
            trace.instrument(b'not a qualified UEL\n')

    def test_real_call_fields_and_acceptance_distinguished(self):
        m, first = trace.analyze_trace(fixture_rows())
        self.assertEqual(m['uel_calls'], 2)
        self.assertEqual(m['accepted_element_callbacks'], 1)
        self.assertEqual(m['history_write_calls'], 1)
        self.assertEqual(first['element'], 336)

    def test_unaccepted_trace_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Incomplete'):
            trace.analyze_trace(fixture_rows()[:4])

    def test_committed_write_during_uel_rejected(self):
        rows = fixture_rows(); rows[1][trace.HEADER.index('hc1')] = '1'
        with self.assertRaisesRegex(ValueError, 'committed'):
            trace.analyze_trace(rows)

    def test_wrong_commit_rejected(self):
        rows = fixture_rows(); rows[-1][trace.HEADER.index('hc1')] = '0'
        with self.assertRaisesRegex(ValueError, 'commit mismatch'):
            trace.analyze_trace(rows)

    def test_trace_corruption_rejected(self):
        for value in ('NaN', 'TRACE_TRUNCATED', '999'):
            rows = copy.deepcopy(fixture_rows()); rows[2][0] = value
            with self.assertRaises(ValueError): trace.analyze_trace(rows)

    def test_missing_evidence_is_not_simulated(self):
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'TRACE_ACQUISITION_REQUIRED'):
                trace.probe(Path(folder))


if __name__ == '__main__': unittest.main()
