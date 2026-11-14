# -*- coding: utf-8 -*-
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.audit_five_case_candidates import audit_candidates

def test_audit_candidates():
    matches = audit_candidates()
    assert len(matches) > 0
