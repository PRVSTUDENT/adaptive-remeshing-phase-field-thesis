#!/usr/bin/env python
"""F11 Abaqus/CAE entrypoint using only the explicit staged runtime root."""
from __future__ import print_function
import os

runtime = os.environ["F11_RUNTIME_DIR"]
core = os.path.join(runtime, "qualify_stage_f11_remeshing_variable_type_core.py")
if not os.path.isfile(core):
    raise IOError("missing F11 type-matrix core: %s" % core)
execfile(core, globals())
