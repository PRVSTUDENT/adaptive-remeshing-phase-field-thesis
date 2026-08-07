#!/usr/bin/env python3
"""
F41 CAE Reconstruction Launcher Entrypoint
Executed inside Abaqus/CAE noGUI mode on HPC or local Abaqus environment.
"""

import os
import sys

def main():
    runtime_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, runtime_dir)

    import f41_cae_reconstruction_matrix as matrix

    rc = matrix.run_f41_matrix()

    rc_file = os.path.join(runtime_dir, "f41_reconstruction.returncode")
    with open(rc_file, 'w') as f:
        f.write("{0}\n".format(rc))

    return rc

if __name__ == "__main__":
    sys.exit(main())
