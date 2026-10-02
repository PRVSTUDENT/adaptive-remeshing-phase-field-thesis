#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix line endings in submit_job.pbs to Unix LF
"""

import os
import sys

def main():
    paths = [
        'models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL/submit_job.pbs',
        'models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_CONTINUATION_VAL/submit_job.pbs'
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, 'rb') as fp:
                c = fp.read()
            c = c.replace(b'\r\n', b'\n')
            with open(p, 'wb') as fp:
                fp.write(c)
            print("Converted %s to Unix LF (bytes: %d)" % (p, len(c)))

if __name__ == "__main__":
    main()
