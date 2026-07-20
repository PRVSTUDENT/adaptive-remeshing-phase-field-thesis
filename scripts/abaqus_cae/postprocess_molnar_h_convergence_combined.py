# Abaqus/CAE noGUI combined postprocessing entry for the h-convergence study.
# Run with:
#   abaqus cae noGUI=postprocess_molnar_h_convergence_combined.py -- \
#     <H0_odb> <H1_odb> <H2_odb> <outdir>
#
# Compatibility: Abaqus Python (no f-strings, no type annotations, no pathlib).

import json
import os
import sys


def _args():
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1 :]
    else:
        args = []
        for a in sys.argv[1:]:
            if not a.endswith(".py"):
                args.append(a)
    if len(args) < 4:
        raise RuntimeError(
            "Usage: abaqus cae noGUI=script.py -- <H0_odb> <H1_odb> <H2_odb> <outdir>"
        )
    return args[0], args[1], args[2], args[3]


def _ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def main():
    h0, h1, h2, outdir = _args()
    _ensure_dir(outdir)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    single = os.path.join(script_dir, "postprocess_molnar_h_convergence_case.py")

    records = []
    for case_id, odb in (("H0", h0), ("H1", h1), ("H2-PUB", h2)):
        if not odb or not os.path.isfile(odb):
            records.append(
                {"case_id": case_id, "status": "odb_missing", "odb": odb}
            )
            continue
        case_out = os.path.join(outdir, case_id)
        _ensure_dir(case_out)
        # Execute single-case script by path with argv rewrite.
        old_argv = sys.argv
        sys.argv = [single, "--", odb, case_out, case_id]
        try:
            # Prefer execfile-style loading for broad Abaqus Python support.
            global_ns = {"__name__": "__main__", "__file__": single}
            fh = open(single, "r")
            try:
                source = fh.read()
            finally:
                fh.close()
            code = compile(source, single, "exec")
            exec(code, global_ns)
            records.append(
                {
                    "case_id": case_id,
                    "status": "postprocessed",
                    "odb": odb,
                    "outdir": case_out,
                }
            )
        except Exception:
            records.append(
                {
                    "case_id": case_id,
                    "status": "postprocess_failed",
                    "error": str(sys.exc_info()[1]),
                    "odb": odb,
                }
            )
        finally:
            sys.argv = old_argv

    manifest = os.path.join(outdir, "combined_postprocess_manifest.json")
    fh = open(manifest, "w")
    try:
        json.dump({"cases": records}, fh, indent=2, sort_keys=True)
    finally:
        fh.close()

    cmd = os.path.join(outdir, "combined_cae_commands.txt")
    fh = open(cmd, "w")
    try:
        fh.write(
            "abaqus cae noGUI=postprocess_molnar_h_convergence_combined.py -- "
            "{0} {1} {2} {3}\n".format(h0, h1, h2, outdir)
        )
    finally:
        fh.close()


if __name__ == "__main__":
    main()
