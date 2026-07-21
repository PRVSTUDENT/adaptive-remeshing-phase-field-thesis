# Abaqus/CAE noGUI entry for Stage C Job 3 (env-var API).
#
# Required environment variables:
#   MISESERI_CASE_ID
#   MISESERI_ODB_PATH
#   MISESERI_OUTPUT_DIR
#   MISESERI_CONFIG_PATH
#
# This wrapper:
#   1) extracts MISESERI from the ODB (read-only, no Standard solve)
#   2) if system Python remesher is available via MISESERI_SYSTEM_PYTHON +
#      MISESERI_REMESH_SCRIPT, runs one-pass refined mesh export
#   3) otherwise leaves extraction artifacts for an external remesh step
#
# Prefer PBS orchestration:
#   abaqus cae noGUI=extract_miseseri_from_odb.py
#   python3 build_refined_mesh_from_miseseri.py ...

from __future__ import print_function

import os
import subprocess
import sys


def main():
    # Reuse extract module logic by exec.
    here = os.path.dirname(os.path.abspath(__file__))
    extract = os.path.join(here, "extract_miseseri_from_odb.py")
    # Run extract in-process by importing if possible; else execfile-like.
    sys.argv = [extract]
    # Ensure extract sees same env
    g = {"__name__": "__main__", "__file__": extract}
    with open(extract, "r") as stream:
        code = compile(stream.read(), extract, "exec")
    exec(code, g)

    outdir = os.environ["MISESERI_OUTPUT_DIR"]
    csv_path = os.path.join(outdir, "miseseri_element_field.csv")
    config_path = os.environ.get("MISESERI_CONFIG_PATH")
    py = os.environ.get("MISESERI_SYSTEM_PYTHON")
    remesh = os.environ.get(
        "MISESERI_REMESH_SCRIPT",
        os.path.join(here, "build_refined_mesh_from_miseseri.py"),
    )
    if py and config_path and os.path.isfile(csv_path) and os.path.isfile(remesh):
        cmd = [
            py,
            remesh,
            "--csv",
            csv_path,
            "--config",
            config_path,
            "--out",
            outdir,
        ]
        print("Running remesher: {0}".format(" ".join(cmd)))
        rc = subprocess.call(cmd)
        if rc != 0:
            sys.exit(rc)
        # Ensure refined_physical.inp exists
        if not os.path.isfile(os.path.join(outdir, "refined_physical.inp")):
            print("ERROR: refined_physical.inp missing after remesh")
            sys.exit(14)
        return 0

    print("Extraction complete; remesher not invoked in-process.")
    print("PBS should run build_refined_mesh_from_miseseri.py next.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:
        print("ERROR: {0}".format(exc))
        sys.exit(12)
