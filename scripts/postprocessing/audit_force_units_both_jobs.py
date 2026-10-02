import os
import sys
import json
from odbAccess import openOdb
import numpy as np

def audit_forces():
    results = {}
    
    # 1. Inspect 1388948 (Restart1)
    odb1_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6R2/M2STATE_FRACFIX_RESTART1R1R6R2.odb"
    if os.path.exists(odb1_path):
        odb1 = openOdb(odb1_path, readOnly=True)
        step2_1 = odb1.steps["Step-2-Continuation"]
        f13 = step2_1.frames[13]
        
        # Check fieldOutputs in f13
        fields1 = list(f13.fieldOutputs.keys())
        u_f13 = f13.fieldOutputs["U"] if "U" in f13.fieldOutputs else None
        rf_f13 = f13.fieldOutputs["RF"] if "RF" in f13.fieldOutputs else None
        
        rp_u1 = 0.0
        rp_rf1 = 0.0
        if u_f13:
            for v in u_f13.values:
                if v.nodeLabel == 99999:
                    rp_u1 = float(v.data[0])
        if rf_f13:
            for v in rf_f13.values:
                if v.nodeLabel == 99999:
                    rp_rf1 = float(v.data[0])
                    
        # Check history outputs
        history_regions = list(step2_1.historyRegions.keys())
        rp_hist_rf1 = None
        for hr_name, hr in step2_1.historyRegions.items():
            if "99999" in hr_name or "RP" in hr_name or "Assembly" in hr_name:
                if "RF1" in hr.historyOutputs:
                    rp_hist_rf1 = hr.historyOutputs["RF1"].data
                    
        results["1388948"] = {
            "fields": fields1,
            "rp_u1_f13": rp_u1,
            "rp_rf1_f13": rp_rf1,
            "history_regions": history_regions,
            "rp_hist_rf1_sample": rp_hist_rf1[:5] if rp_hist_rf1 else None,
            "rp_hist_rf1_f13": rp_hist_rf1[13] if rp_hist_rf1 and len(rp_hist_rf1) > 13 else None
        }
        odb1.close()
    else:
        results["1388948"] = {"error": "ODB not found"}

    # 2. Inspect 1389229 (Restart2)
    odb2_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R7/M2STATE_FRACFIX_RESTART2R7.odb"
    if os.path.exists(odb2_path):
        odb2 = openOdb(odb2_path, readOnly=True)
        step1_2 = odb2.steps["Step-1-PhaseInit"]
        step2_2 = odb2.steps["Step-2-Continuation"]
        
        f1_step1 = step1_2.frames[-1]
        f_last_step2 = step2_2.frames[-1]
        
        fields2_step1 = list(f1_step1.fieldOutputs.keys())
        fields2_step2 = list(f_last_step2.fieldOutputs.keys())
        
        # Check history outputs
        history_regions2 = list(step2_2.historyRegions.keys())
        rp2_hist_rf1 = None
        for hr_name, hr in step2_2.historyRegions.items():
            if "99999" in hr_name or "RP" in hr_name or "Assembly" in hr_name:
                if "RF1" in hr.historyOutputs:
                    rp2_hist_rf1 = hr.historyOutputs["RF1"].data
                    
        results["1389229"] = {
            "fields_step1": fields2_step1,
            "fields_step2": fields2_step2,
            "history_regions": history_regions2,
            "rp2_hist_rf1_len": len(rp2_hist_rf1) if rp2_hist_rf1 else 0,
            "rp2_hist_rf1_start": rp2_hist_rf1[0] if rp2_hist_rf1 else None,
            "rp2_hist_rf1_end": rp2_hist_rf1[-1] if rp2_hist_rf1 else None
        }
        odb2.close()
    else:
        results["1389229"] = {"error": "ODB not found"}

    with open("FORCE_UNIT_AUDIT.json", "w") as f:
        json.dump(results, f, indent=2)
    print("FORCE_UNIT_AUDIT.json written successfully.")

if __name__ == "__main__":
    audit_forces()
