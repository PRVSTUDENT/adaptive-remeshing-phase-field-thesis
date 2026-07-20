# Combined CAE entry is deprecated for production h-convergence use.
# Use sequential env-var invocations of postprocess_molnar_h_convergence_case.py
# from scripts/hpc/molnar_lc015_hconv_cae_replay_all.pbs instead.
#
# This file remains only as a thin wrapper that refuses argv-based paths.

import os
import sys


def main():
    print("Abaqus argv: {0}".format(repr(sys.argv)))
    raise RuntimeError(
        "postprocess_molnar_h_convergence_combined.py is not used for "
        "production recovery. Export MOLNAR_CASE_ID, MOLNAR_ODB_PATH, "
        "MOLNAR_OUTPUT_DIR and run postprocess_molnar_h_convergence_case.py "
        "once per case via molnar_lc015_hconv_cae_replay_all.pbs."
    )


if __name__ == "__main__":
    main()
