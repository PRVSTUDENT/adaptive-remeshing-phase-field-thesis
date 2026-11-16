# -*- coding: utf-8 -*-
"""
scripts/remeshing/audit_f1803_recovery_donor.py
==============================================
Audits MISESERI, MISESAVG, and regional stress recovery error distribution
in SEC43_STATE2_HIGH_FIDELITY_RECOVERY.odb.
"""

from __future__ import print_function
import os
import sys
import json
import math
import odbAccess

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
ODB_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "253_f1803_case3_accurate_recovery", "SEC43_STATE2_HIGH_FIDELITY_RECOVERY.odb")
RECEIPT_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "253_f1803_case3_accurate_recovery", "PK_F1803_CASE3_ACCURATE_DONOR_RECEIPT.json")

def main():
    print("Opening ODB: %s" % ODB_PATH)
    odb = odbAccess.openOdb(ODB_PATH)
    step = odb.steps["RECOVERY_STEP"]
    frame = step.frames[1]
    
    print("Available field outputs:", list(frame.fieldOutputs.keys()))
    assert "MISESERI" in frame.fieldOutputs, "MISESERI missing in frame"
    assert "MISESAVG" in frame.fieldOutputs, "MISESAVG missing in frame"
    
    eri_field = frame.fieldOutputs["MISESERI"]
    avg_field = frame.fieldOutputs["MISESAVG"]
    
    eri_by_elem = {}
    for val in eri_field.values:
        eri_by_elem[val.elementLabel] = float(val.data)
        
    avg_by_elem = {}
    for val in avg_field.values:
        avg_by_elem[val.elementLabel] = float(val.data)
        
    root_inst = odb.rootAssembly.instances[list(odb.rootAssembly.instances.keys())[0]]
    
    # Compute element centroids
    elem_centroids = {}
    node_coords = {n.label: (n.coordinates[0], n.coordinates[1]) for n in root_inst.nodes}
    for elem in root_inst.elements:
        coords = [node_coords[nl] for nl in elem.connectivity]
        cx = sum(c[0] for c in coords) / len(coords)
        cy = sum(c[1] for c in coords) / len(coords)
        elem_centroids[elem.label] = (cx, cy)
        
    odb.close()
    
    eri_vals = list(eri_by_elem.values())
    avg_vals = list(avg_by_elem.values())
    
    # Classify regions
    primary_eids = []
    secondary_eids = []
    far_field_eids = []
    
    for eid, (cx, cy) in elem_centroids.items():
        # Primary corridor: notch to central hole (x in [0, 36.5], y in [45, 57])
        if cx <= 36.5 and 45.0 <= cy <= 57.0:
            primary_eids.append(eid)
        # Secondary corridor: hole to right boundary (x >= 36.5, y in [45, 57])
        elif cx >= 36.5 and 45.0 <= cy <= 57.0:
            secondary_eids.append(eid)
        else:
            far_field_eids.append(eid)
            
    print("Regional counts: primary=%d, secondary=%d, far_field=%d" % (
        len(primary_eids), len(secondary_eids), len(far_field_eids)
    ))
    
    def stats(eids, field_dict):
        vals = [field_dict[e] for e in eids if e in field_dict]
        return {
            "count": len(vals),
            "min": min(vals) if vals else 0.0,
            "max": max(vals) if vals else 0.0,
            "mean": sum(vals)/len(vals) if vals else 0.0
        }
        
    primary_eri = stats(primary_eids, eri_by_elem)
    secondary_eri = stats(secondary_eids, eri_by_elem)
    far_field_eri = stats(far_field_eids, eri_by_elem)
    global_eri = stats(list(eri_by_elem.keys()), eri_by_elem)
    
    primary_avg = stats(primary_eids, avg_by_elem)
    secondary_avg = stats(secondary_eids, avg_by_elem)
    far_field_avg = stats(far_field_eids, avg_by_elem)
    global_avg = stats(list(avg_by_elem.keys()), avg_by_elem)
    
    ratio_sec_to_prim = secondary_eri["mean"] / primary_eri["mean"] if primary_eri["mean"] > 0 else 0.0
    print("MISESERI Global: min=%.6e, max=%.6e, mean=%.6e kN/mm^2" % (
        global_eri["min"], global_eri["max"], global_eri["mean"]
    ))
    print("MISESERI Primary: mean=%.6e kN/mm^2, max=%.6e" % (primary_eri["mean"], primary_eri["max"]))
    print("MISESERI Secondary: mean=%.6e kN/mm^2, max=%.6e" % (secondary_eri["mean"], secondary_eri["max"]))
    print("Ratio Secondary / Primary MISESERI mean: %.4f" % ratio_sec_to_prim)
    
    # Update receipt
    with open(RECEIPT_PATH, "r") as f:
        rc = json.load(f)
        
    rc["regional_error_distribution_kn_per_mm2"] = {
        "global_miseseri": global_eri,
        "primary_corridor_miseseri": primary_eri,
        "secondary_corridor_miseseri": secondary_eri,
        "far_field_miseseri": far_field_eri,
        "ratio_secondary_to_primary_mean": ratio_sec_to_prim,
        "global_misesavg": global_avg,
        "primary_corridor_misesavg": primary_avg,
        "secondary_corridor_misesavg": secondary_avg,
        "far_field_misesavg": far_field_avg
    }
    
    with open(RECEIPT_PATH, "w") as f:
        json.dump(rc, f, indent=2)
    print("Updated donor receipt with detailed regional error distribution.")

if __name__ == "__main__":
    main()
