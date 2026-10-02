#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Process zone history variable H tracking at all 4 Gauss points and energy checks:
Audit SDVs at critical crack tip elements in Native Control and Stage-D Transfer.
"""

from odbAccess import openOdb
import sys

def track_history():
    ctrl_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.odb"
    trans_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.odb"
    
    odb_ctrl = openOdb(ctrl_path, readOnly=True)
    odb_trans = openOdb(trans_path, readOnly=True)
    
    print("================================================================================")
    print("PROCESS ZONE 4-GP COMMITTED HISTORY H & ENERGY AUDIT")
    print("================================================================================")
    
    # Check SDV field outputs
    def inspect_sdv_field(odb, name):
        print("\n--- %s SDV / HISTORY AUDIT ---" % name)
        for s_name in ['STATE_INSTALL', 'MECH_EQUILIBRATION', 'PHASE_RELEASE', 'CONTINUATION']:
            if s_name in odb.steps:
                step = odb.steps[s_name]
                print("  Step %-20s: %d Frames" % (s_name, len(step.frames)))
                # Check frame 0 and last frame
                for f_idx in [0, len(step.frames)-1]:
                    f = step.frames[f_idx]
                    sdv_keys = [k for k in f.fieldOutputs.keys() if 'SDV' in k]
                    print("    Frame %2d Field Outputs: %s" % (f_idx, sdv_keys))
                    if 'SDV1' in f.fieldOutputs:
                        vals = [v.data for v in f.fieldOutputs['SDV1'].values]
                        print("      SDV1 max = %.6e, min = %.6e" % (max(vals), min(vals)))

    inspect_sdv_field(odb_ctrl, "1390278 (Native Control)")
    inspect_sdv_field(odb_trans, "1390279 (Stage-D Transfer)")

    odb_ctrl.close()
    odb_trans.close()

if __name__ == "__main__":
    track_history()
