#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remote import smoke test for Package 171-R1."""
import sys
from pathlib import Path

cur_dir = Path(__file__).resolve().parent
repo = cur_dir / "runtime"
if str(repo) not in sys.path:
    sys.path.insert(0, str(repo))

try:
    import scripts.state_transfer.driver_package171_c6_coupled_pdas as p171
    assert hasattr(p171, "Package171C6PDASDriver"), "Driver class missing"
    assert hasattr(p171, "DONOR_REFERENCE_FORCE_KN"), "Reference constants missing"
    print("REMOTE_IMPORT_SUCCESS: True")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
