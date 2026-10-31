"""Receipt repair must verify data, not merely refresh stale digests."""
import copy
from scripts.validation.reconcile_turn381_receipt import verify, summary_from_rows, ROOT, CSV
import csv
import pytest


def test_original_bound_distribution_reproduces_entire_current_audit():
    _, mismatches, summary = verify()
    assert len(mismatches) == 1
    assert summary['total_elements'] == 7056
    assert summary['refinement_metrics']['elements_above_threshold'] == 266


def test_inconsistent_indicator_rejected():
    with (ROOT/CSV).open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    changed = copy.deepcopy(rows)
    changed[0]['eta_relative_error'] = str(float(changed[0]['eta_relative_error']) + .1)
    with pytest.raises(AssertionError):
        summary_from_rows(changed)


def test_duplicate_element_rejected():
    with (ROOT/CSV).open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    rows[0] = rows[1]
    with pytest.raises(AssertionError):
        summary_from_rows(rows)
