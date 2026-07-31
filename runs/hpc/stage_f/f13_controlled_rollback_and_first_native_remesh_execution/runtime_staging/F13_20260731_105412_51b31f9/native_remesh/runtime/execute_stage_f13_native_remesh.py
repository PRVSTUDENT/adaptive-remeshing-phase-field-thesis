from __future__ import print_function
import os
runtime = os.environ["F13_RUNTIME_DIR"]
core = os.path.join(runtime, "execute_stage_f13_native_remesh_core.py")
namespace = {"F13_RUNTIME_DIR": runtime}
exec(compile(open(core, "rb").read(), core, "exec"), namespace, namespace)
