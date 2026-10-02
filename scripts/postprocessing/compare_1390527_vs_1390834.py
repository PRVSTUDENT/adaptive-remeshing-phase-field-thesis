#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Compare Default Baseline 1390527 vs Minimal Continuation 1390834
"""

import os
import sys
import json
import numpy as np

def main():
    csv_1390834 = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL/force_displacement_curve.csv"
    
    data_new = np.genfromtxt(csv_1390834, delimiter=',', names=True)
    print("New 1390834 total frames: %d" % len(data_new))
    for i in range(len(data_new)):
        print("Frame %2d: StepTime=%.6f, U1=%.6f mm, RF1=%.6f kN, d_max=%.6f" % (
            data_new['Frame'][i], data_new['StepTime'][i], data_new['U1_mm'][i], data_new['RF1_kN'][i], data_new['d_max'][i]))

if __name__ == "__main__":
    main()
