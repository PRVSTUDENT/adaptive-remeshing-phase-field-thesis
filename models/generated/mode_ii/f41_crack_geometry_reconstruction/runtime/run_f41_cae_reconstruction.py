#!/usr/bin/env python3
"""
F41 CAE Reconstruction Launcher Entrypoint (F41R3 Entrypoint Repair)
Executed inside Abaqus/CAE noGUI mode on HPC or local Abaqus environment.
Uses F41_RUNTIME_DIR or os.getcwd().
Writes F41_RECONSTRUCTION.returncode into F41_EVIDENCE_DIR.
"""

import os
import sys

def main():
    runtime_dir = os.environ.get("F41_RUNTIME_DIR", "").strip()
    if not runtime_dir:
        runtime_dir = os.getcwd()
    runtime_dir = os.path.abspath(runtime_dir)

    matrix_file = os.path.join(runtime_dir, "f41_cae_reconstruction_matrix.py")
    deck_file = os.path.join(runtime_dir, "source_deck.inp")

    if not os.path.exists(matrix_file):
        raise RuntimeError("Required matrix file missing: {0}".format(matrix_file))
    if not os.path.exists(deck_file):
        raise RuntimeError("Required source deck missing: {0}".format(deck_file))

    if runtime_dir not in sys.path:
        sys.path.insert(0, runtime_dir)

    import f41_cae_reconstruction_matrix as matrix

    rc = matrix.run_f41_matrix()

    evidence_dir = os.environ.get("F41_EVIDENCE_DIR", "").strip()
    if not evidence_dir:
        evidence_dir = runtime_dir
    if not os.path.exists(evidence_dir):
        try:
            os.makedirs(evidence_dir)
        except Exception:
            pass

    rc_file = os.path.join(evidence_dir, "F41_RECONSTRUCTION.returncode")
    with open(rc_file, 'w') as f:
        f.write("{0}\n".format(rc))

    local_rc = os.path.join(runtime_dir, "f41_reconstruction.returncode")
    with open(local_rc, 'w') as f:
        f.write("{0}\n".format(rc))

    return rc

if __name__ == "__main__":
    sys.exit(main())
