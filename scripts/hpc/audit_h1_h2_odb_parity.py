#!/usr/bin/env python
"""Audit parity between H1 (1379482.mmaster02) and H2 (1379578.mmaster02) ODBs on cluster."""

from __future__ import print_function
import sys
import os

from odbAccess import openOdb

def audit_odb(label, path):
    print("=== AUDIT FOR %s: %s ===" % (label, path))
    if not os.path.exists(path):
        print("ERROR: Path does not exist!")
        return
    odb = openOdb(path, readOnly=True)
    print("Steps:", list(odb.steps.keys()))
    
    # Root assembly sets
    root = odb.rootAssembly
    print("Root Assembly nodeSets:", list(root.nodeSets.keys()))
    print("Root Assembly elementSets:", list(root.elementSets.keys()))
    print("Root Assembly instances:", list(root.instances.keys()))

    if "RP" in root.nodeSets:
        rp_set = root.nodeSets["RP"]
        print("RP nodeSet size:", len(rp_set.nodes[0]) if rp_set.nodes else 0)
        for inst_nodes in rp_set.nodes:
            for node in inst_nodes:
                print("RP Node label: %d, instance: %s, coordinates: %s" % (node.label, node.instanceName, str(node.coordinates)))

    # Frame inspection
    for sname in sorted(odb.steps.keys()):
        step = odb.steps[sname]
        print("Step %s: domain %s, n_frames=%d, totalTime=%f" % (sname, step.domain, len(step.frames), step.totalTime))
        f_first = step.frames[0]
        f_last = step.frames[-1]
        print("  First frame time: %f, Last frame time: %f" % (f_first.frameValue, f_last.frameValue))
        
        # Check RP values
        if "RP" in root.nodeSets:
            rp_set = root.nodeSets["RP"]
            if "U" in f_last.fieldOutputs:
                u_fo = f_last.fieldOutputs["U"].getSubset(region=rp_set)
                if len(u_fo.values) > 0:
                    print("  Last frame U at RP: %s" % str(u_fo.values[0].data))
            if "RF" in f_last.fieldOutputs:
                rf_fo = f_last.fieldOutputs["RF"].getSubset(region=rp_set)
                if len(rf_fo.values) > 0:
                    print("  Last frame RF at RP: %s" % str(rf_fo.values[0].data))

    odb.close()
    print("")

def main():
    h1_path = "/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h1_sweep_u020_1379482.mmaster02/m2h1_u020.odb"
    h2_path = "/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h2_serial_1379578.mmaster02/ModeII_H2_uniform_serial.odb"

    audit_odb("H1 U020", h1_path)
    audit_odb("H2 UNIFORM", h2_path)

if __name__ == "__main__":
    main()
