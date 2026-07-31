from __future__ import print_function
import os, sys, traceback

runtime = os.environ.get("F12_RUNTIME_DIR")
if not runtime:
    raise RuntimeError("F12_RUNTIME_DIR is required")
core = os.path.join(runtime, "prepare_stage_f12_native_remesh_core.py")
namespace = {"F12_RUNTIME_DIR": runtime}
execfile(core, namespace, namespace)
