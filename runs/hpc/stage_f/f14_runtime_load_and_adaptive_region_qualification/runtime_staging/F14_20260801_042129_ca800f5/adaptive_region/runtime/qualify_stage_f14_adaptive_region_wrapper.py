from __future__ import print_function
import os
runtime = os.environ["F14_RUNTIME_DIR"]
core = os.path.join(runtime, "qualify_stage_f14_adaptive_region.py")
namespace = {"F14_RUNTIME_DIR": runtime}
exec(compile(open(core, "rb").read(), core, "exec"), namespace, namespace)
