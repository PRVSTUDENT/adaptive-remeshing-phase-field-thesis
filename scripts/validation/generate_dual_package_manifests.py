#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate and freeze SHA-256 manifests for both packages:
1. M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL
2. M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL
"""

import os
import hashlib
import json

def hash_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fp:
        while True:
            c = fp.read(65536)
            if not c:
                break
            h.update(c)
    return h.hexdigest()

def main():
    # 1. Native Control
    d1 = '/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL'
    f_list1 = [
        'M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.inp',
        'f44_mixed_uel_restart_stateinit.for',
        'STAGE_D_PRIMARY_STATE_BOUNDARY.inp',
        'STAGE_D_U3_ONLY_BOUNDARY.inp',
        'STAGE_D_COMMITTED_STATE.bin',
        'submit_job.pbs'
    ]
    m1 = {
        'package_name': 'M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL',
        'files': {f: hash_file(os.path.join(d1, f)) for f in f_list1}
    }
    with open(os.path.join(d1, 'manifest.json'), 'w') as fp:
        json.dump(m1, fp, indent=2)
    print('--- NATIVE BOUNDED CONTROL MANIFEST ---')
    print(json.dumps(m1, indent=2))

    # 2. Stage-D Nonmatching Transfer
    d2 = '/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL'
    f_list2 = [
        'M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.inp',
        'f44_mixed_uel_restart_stateinit.for',
        'STAGE_D_PRIMARY_STATE_BOUNDARY.inp',
        'STAGE_D_U3_ONLY_BOUNDARY.inp',
        'STAGE_D_COMMITTED_STATE.bin',
        'submit_job.pbs'
    ]
    m2 = {
        'package_name': 'M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL',
        'files': {f: hash_file(os.path.join(d2, f)) for f in f_list2}
    }
    with open(os.path.join(d2, 'manifest.json'), 'w') as fp:
        json.dump(m2, fp, indent=2)
    print('\n--- STAGE-D NONMATCHING BOUNDED TRANSFER MANIFEST ---')
    print(json.dumps(m2, indent=2))

if __name__ == "__main__":
    main()
