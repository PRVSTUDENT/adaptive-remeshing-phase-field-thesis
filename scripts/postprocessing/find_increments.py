#!/usr/bin/env python
# -*- coding: utf-8 -*-
with open('models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL.msg', 'r') as f:
    for line in f:
        if 'INCREMENT' in line:
            print(line.rstrip())
