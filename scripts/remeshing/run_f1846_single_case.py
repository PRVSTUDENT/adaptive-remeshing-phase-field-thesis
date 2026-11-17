# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1846_single_case.py
==========================================
Isolated Abaqus CAE execution script for running a single benchmark case
with scripts/remeshing/generalized_2d_adaptive_framework_f1846.py.
"""

from __future__ import print_function
import os
import sys

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.generalized_2d_adaptive_framework_f1846 import (
    AdaptiveConfig,
    run_method_a_case
)

def main():
    if len(sys.argv) < 5:
        sys.stderr.write("Usage: abaqus cae noGUI=run_f1846_single_case.py -- <config_json> <donor_odb> <output_dir> <error_target>\n")
        sys.exit(1)

    config_path = sys.argv[-4]
    donor_odb = sys.argv[-3]
    out_dir = sys.argv[-2]
    error_target = float(sys.argv[-1])

    cfg = AdaptiveConfig.from_json(config_path)
    cfg.error_target = error_target

    print("Executing generalized Method A for config=%s, target=%.2f%%, out_dir=%s" % (config_path, error_target, out_dir))
    res = run_method_a_case(
        cfg,
        authentic_donor_odb=donor_odb,
        output_directory=out_dir,
        fail_closed=True
    )
    print("Execution completed with status: %s" % res["status"])
    print("Physical mesh: %s" % res["physical_mesh"])

if __name__ == '__main__':
    main()
