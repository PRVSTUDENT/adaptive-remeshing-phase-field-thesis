# Abaqus/CAE noGUI combined postprocessing entry for the h-convergence study.
# Run with:
#   abaqus cae noGUI=postprocess_molnar_h_convergence_combined.py -- \
#     <H0_odb> <H1_odb> <H2_odb> <outdir>
#
# This script postprocesses each available ODB with the single-case workflow
# and writes a combined listing. Numerical successive-mesh comparison is done
# later with system Python from the CAE-exported CSV/RPT files.

from __future__ import annotations

import json
import os
import sys


def _args():
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1 :]
    else:
        args = [a for a in sys.argv[1:] if not a.endswith(".py")]
    if len(args) < 4:
        raise RuntimeError(
            "Usage: abaqus cae noGUI=script.py -- <H0_odb> <H1_odb> <H2_odb> <outdir>"
        )
    return args[0], args[1], args[2], args[3]


def main():
    h0, h1, h2, outdir = _args()
    if not os.path.isdir(outdir):
        os.makedirs(outdir)

    # Import and reuse single-case logic by executing its main with patched argv.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    single = os.path.join(script_dir, "postprocess_molnar_h_convergence_case.py")
    # Load single-case module text and exec in isolated namespaces is awkward in CAE;
    # instead call openOdb workflow by re-invoking functions after import via runpy.
    import runpy

    records = []
    for case_id, odb in (("H0", h0), ("H1", h1), ("H2-PUB", h2)):
        if not odb or not os.path.isfile(odb):
            records.append({"case_id": case_id, "status": "odb_missing", "odb": odb})
            continue
        case_out = os.path.join(outdir, case_id)
        if not os.path.isdir(case_out):
            os.makedirs(case_out)
        sys.argv = [single, "--", odb, case_out, case_id]
        try:
            runpy.run_path(single, run_name="__main__")
            records.append({"case_id": case_id, "status": "postprocessed", "odb": odb, "outdir": case_out})
        except Exception as exc:
            records.append({"case_id": case_id, "status": "postprocess_failed", "error": str(exc), "odb": odb})

    with open(os.path.join(outdir, "combined_postprocess_manifest.json"), "w") as fh:
        json.dump({"cases": records}, fh, indent=2, sort_keys=True)

    with open(os.path.join(outdir, "combined_cae_commands.txt"), "w") as fh:
        fh.write(
            "abaqus cae noGUI=postprocess_molnar_h_convergence_combined.py -- "
            "{} {} {} {}\n".format(h0, h1, h2, outdir)
        )


if __name__ == "__main__":
    main()
