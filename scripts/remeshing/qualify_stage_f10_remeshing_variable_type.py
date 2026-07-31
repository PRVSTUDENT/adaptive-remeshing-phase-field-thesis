#!/usr/bin/env python
"""Canonical Stage F10 entrypoint for the reviewed F9 type-matrix core."""
from __future__ import print_function
import os

CORE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "qualify_stage_f9_remeshing_variable_type.py")
if not os.path.isfile(CORE):
    raise IOError("missing reviewed type-matrix core: %s" % CORE)
execfile(CORE)
