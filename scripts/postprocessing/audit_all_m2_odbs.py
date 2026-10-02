"""
Abaqus Python script to perform deep forensic audit of ODB files:
1. M2REF_H1_FULL_U050 (1389686.mmaster02)
2. M2CORR_H1_FREEU2_FULL_U050
3. M2CORR_H2_FREEU2_FULL_U050 (1389687.mmaster02)
4. M2CORR_PK10R1_CONTINUOUS_U050
5. M2CORR_PK10R2_TOPOLOGY_CORRECTED (1390056.mmaster02)
"""

import sys
import os
from odbAccess import openOdb

def audit_odb(odb_path):
    print("================================================================================")
    print("AUDITING ODB: " + odb_path)
    print("================================================================================")
    if not os.path.exists(odb_path):
        print("ERROR: ODB path does not exist: " + odb_path)
        return

    try:
        odb = openOdb(odb_path, readOnly=True)
    except Exception as e:
        print("ERROR opening ODB: " + str(e))
        return

    root = odb.rootAssembly

    for step_name, step in odb.steps.items():
        print("\n--- Step: " + step_name + " (Frames: " + str(len(step.frames)) + ") ---")

        frames = step.frames
        if len(frames) == 0:
            continue

        rp_records = []
        for f_idx, f in enumerate(frames):
            t = float(f.frameValue)
            u_field = f.fieldOutputs['U'] if 'U' in f.fieldOutputs.keys() else None
            rf_field = f.fieldOutputs['RF'] if 'RF' in f.fieldOutputs.keys() else None

            u_dict = {}
            rf_dict = {}
            if u_field:
                for v in u_field.values:
                    u_dict[v.nodeLabel] = v.data
            if rf_field:
                for v in rf_field.values:
                    rf_dict[v.nodeLabel] = v.data

            sum_pos_rf1 = 0.0
            sum_neg_rf1 = 0.0
            for n, rf in rf_dict.items():
                if rf[0] > 0.0:
                    sum_pos_rf1 += float(rf[0])
                elif rf[0] < 0.0:
                    sum_neg_rf1 += float(rf[0])

            # Check max positive RF1 node
            max_pos_node = None
            max_pos_rf1 = 0.0
            for n, rf in rf_dict.items():
                if rf[0] > max_pos_rf1:
                    max_pos_rf1 = float(rf[0])
                    max_pos_node = n

            # Check max negative RF1 node
            max_neg_node = None
            max_neg_rf1 = 0.0
            for n, rf in rf_dict.items():
                if rf[0] < max_neg_rf1:
                    max_neg_rf1 = float(rf[0])
                    max_neg_node = n

            # Check known RP nodes
            rp_node = None
            rp_rf1 = 0.0
            rp_u1 = 0.0
            for cand in [99999, 12383, 34261, 6250, 12065]:
                if cand in rf_dict:
                    rp_node = cand
                    rp_rf1 = float(rf_dict[cand][0])
                    if cand in u_dict:
                        rp_u1 = float(u_dict[cand][0])
                    break

            rp_records.append({
                "frame": f_idx,
                "time": t,
                "rp_node": rp_node,
                "rp_rf1": rp_rf1,
                "rp_u1": rp_u1,
                "sum_pos": sum_pos_rf1,
                "sum_neg": sum_neg_rf1,
                "max_pos_node": max_pos_node,
                "max_pos_rf1": max_pos_rf1,
                "max_neg_node": max_neg_node,
                "max_neg_rf1": max_neg_rf1
            })

        print("Frame | Time (mm) | RP Node |   RP RF1 (kN) |   RP U1 (mm) |  Sum +RF1 (kN) |  Sum -RF1 (kN) | Max+ Node | Max- Node")
        print("-" * 115)
        for r in rp_records[:10]:
            print("%5d | %9.6f | %7s | %13.6e | %12.6e | %13.6e | %13.6e | %9s | %9s" % (
                r["frame"], r["time"], str(r["rp_node"]), r["rp_rf1"], r["rp_u1"],
                r["sum_pos"], r["sum_neg"], str(r["max_pos_node"]), str(r["max_neg_node"])
            ))
        print("...")
        # Check peak across all frames for RP RF1 and Sum +RF1
        peak_rp = max(rp_records, key=lambda x: abs(x["rp_rf1"]))
        peak_pos = max(rp_records, key=lambda x: abs(x["sum_pos"]))
        last_r = rp_records[-1]

        print("PEAK RP RF1:  Frame %d, Time %f, RP Node %s, RF1 = %e kN, U1 = %e mm" % (
            peak_rp["frame"], peak_rp["time"], str(peak_rp["rp_node"]), peak_rp["rp_rf1"], peak_rp["rp_u1"]
        ))
        print("PEAK SUM+RF1: Frame %d, Time %f, Sum+RF1 = %e kN, Sum-RF1 = %e kN" % (
            peak_pos["frame"], peak_pos["time"], peak_pos["sum_pos"], peak_pos["sum_neg"]
        ))
        print("LAST FRAME:   Frame %d, Time %f, RP Node %s, RF1 = %e kN, U1 = %e mm, Sum+RF1 = %e kN" % (
            last_r["frame"], last_r["time"], str(last_r["rp_node"]), last_r["rp_rf1"], last_r["rp_u1"], last_r["sum_pos"]
        ))

        # Calculate K0 from increment 1
        if len(rp_records) > 1:
            r1 = rp_records[1]
            k0_rp = r1["rp_rf1"] / r1["rp_u1"] if r1["rp_u1"] != 0 else 0.0
            k0_sum = r1["sum_pos"] / r1["rp_u1"] if r1["rp_u1"] != 0 else 0.0
            print("\nINITIAL STIFFNESS (Frame 1):")
            print("  From RP Node (%s):   K0 = %.6f kN/mm (U1 = %e mm, RF1 = %e kN)" % (
                str(r1["rp_node"]), k0_rp, r1["rp_u1"], r1["rp_rf1"]
            ))
            print("  From Sum +RF1:       K0 = %.6f kN/mm (U1 = %e mm, Sum+RF1 = %e kN)" % (
                k0_sum, r1["rp_u1"], r1["sum_pos"]
            ))

    odb.close()

if __name__ == "__main__":
    for path in sys.argv[1:]:
        audit_odb(path)
