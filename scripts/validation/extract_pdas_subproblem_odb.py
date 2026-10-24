#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_pdas_subproblem_odb.py
Abaqus Python extraction script for iterative PDAS subproblem outputs (Turn 74/75).

Compatible with Abaqus SMAPython (Python 2.7) and modern Python (mock/fallback).
Extracts:
1. Control reference node 999999 displacement U2 and reaction force RF2.
2. Nodal displacements (U1, U2).
3. Nodal phase field (d = U3 if 3-component U exists, otherwise reconstructed
   from companion element SDV1 via element-nodal averaging).
4. Gauss-point damage (SDV1) and committed history (SDV2) from Layer 3 companion elements.
5. Integrated fracture energy (SDV17) and elastic strain energy (SDV18).
6. Outputs standardized CSV for consumption by pdas_cluster_execution_adapter.py.
"""

import sys
import os
import csv
import argparse
from collections import defaultdict

def extract_odb(odb_path, output_csv_path):
    if not os.path.exists(odb_path):
        sys.stderr.write("ERROR: ODB file not found: %s\n" % odb_path)
        sys.exit(1)

    try:
        from odbAccess import openOdb, ELEMENT_NODAL
    except ImportError:
        sys.stderr.write("ERROR: odbAccess module unavailable. Must run via 'abaqus python'.\n")
        sys.exit(1)

    print("[extract_pdas_subproblem_odb] Opening ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)

    try:
        # Determine target step (the last active step)
        step_names = list(odb.steps.keys())
        if not step_names:
            sys.stderr.write("ERROR: No steps found in ODB: %s\n" % odb_path)
            sys.exit(1)

        target_step_name = step_names[-1]
        step = odb.steps[target_step_name]
        print("[extract_pdas_subproblem_odb] Reading step '%s' (%d frames)" % (target_step_name, len(step.frames)))

        if not step.frames:
            sys.stderr.write("ERROR: No frames in step '%s'\n" % target_step_name)
            sys.exit(1)

        # Get last frame (equilibrated state)
        frame = step.frames[-1]
        print("[extract_pdas_subproblem_odb] Frame value: %f" % frame.frameValue)

        field_u = frame.fieldOutputs['U'] if 'U' in frame.fieldOutputs else None
        field_rf = frame.fieldOutputs['RF'] if 'RF' in frame.fieldOutputs else None
        field_sdv1 = frame.fieldOutputs['SDV1'] if 'SDV1' in frame.fieldOutputs else None
        field_sdv2 = frame.fieldOutputs['SDV2'] if 'SDV2' in frame.fieldOutputs else None
        field_sdv17 = frame.fieldOutputs['SDV17'] if 'SDV17' in frame.fieldOutputs else None
        field_sdv18 = frame.fieldOutputs['SDV18'] if 'SDV18' in frame.fieldOutputs else None

        rf2_rp = 0.0
        u2_rp = 0.0

        if field_rf is not None:
            for val in field_rf.values:
                if val.nodeLabel == 999999:
                    rf2_rp = float(val.data[1])
                    break

        u_dict = {}
        if field_u is not None:
            for val in field_u.values:
                u_dict[val.nodeLabel] = val.data
                if val.nodeLabel == 999999:
                    u2_rp = float(val.data[1])

        # Reconstruct nodal phase field from SDV1 (element-nodal extrapolation)
        # if standard planar U does not contain U3 (Do not assume planar ODB U3 exists)
        nodal_d_from_sdv = {}
        if field_sdv1 is not None:
            try:
                sdv1_en = field_sdv1.getSubset(position=ELEMENT_NODAL)
                node_sums = defaultdict(float)
                node_counts = defaultdict(int)
                for val in sdv1_en.values:
                    node_sums[val.nodeLabel] += float(val.data)
                    node_counts[val.nodeLabel] += 1
                for nid in node_sums:
                    nodal_d_from_sdv[nid] = node_sums[nid] / float(node_counts[nid])
            except Exception as e:
                sys.stderr.write("WARNING: Failed element-nodal extrapolation of SDV1: %s\n" % str(e))

        # Open output CSV
        with open(output_csv_path, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(["RECORD_TYPE", "ID", "VAL1", "VAL2", "VAL3", "VAL4"])
            writer.writerow(["RF2", "999999", str(rf2_rp), "0.0", "0.0", "0.0"])
            writer.writerow(["U2_RP", "999999", str(u2_rp), "0.0", "0.0", "0.0"])

            # Nodal phase and displacement across all known physical nodes
            all_physical_nodes = set(nodal_d_from_sdv.keys())
            for nid in u_dict.keys():
                if nid != 999999:
                    all_physical_nodes.add(nid)

            for nid in sorted(all_physical_nodes):
                u_data = u_dict.get(nid, None)
                u1 = float(u_data[0]) if u_data is not None else 0.0
                u2 = float(u_data[1]) if (u_data is not None and len(u_data) >= 2) else 0.0
                if u_data is not None and len(u_data) >= 3:
                    d = float(u_data[2])
                else:
                    d = nodal_d_from_sdv.get(nid, 0.0)
                writer.writerow(["NODE", str(nid), str(u1), str(u2), str(d), "0.0"])

            # Gauss-point history and damage from companion elements if present
            if field_sdv1 is not None and field_sdv2 is not None:
                d_dict = {}
                for val in field_sdv1.values:
                    eid = val.elementLabel
                    kpt = val.integrationPoint
                    d_dict[(eid, kpt)] = float(val.data)

                for val in field_sdv2.values:
                    eid = val.elementLabel
                    kpt = val.integrationPoint
                    h_val = float(val.data)
                    d_val = d_dict.get((eid, kpt), 0.0)
                    writer.writerow(["ELEM_GP", str(eid), str(kpt), str(d_val), str(h_val), "0.0"])

            # Integrated energies from SDV17 (E_frac) and SDV18 (E_elas)
            if field_sdv17 is not None and field_sdv18 is not None:
                e_frac_tot = sum(float(v.data) for v in field_sdv17.values)
                e_elas_tot = sum(float(v.data) for v in field_sdv18.values)
                writer.writerow(["ENERGY", "GLOBAL", str(e_frac_tot), str(e_elas_tot), str(e_frac_tot + e_elas_tot), "0.0"])

        print("[extract_pdas_subproblem_odb] Successfully wrote extracted state to %s" % output_csv_path)

    finally:
        odb.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract Abaqus PDAS Subproblem ODB")
    parser.add_argument("--odb", required=True, help="Path to input ODB file")
    parser.add_argument("--output", required=True, help="Path to output CSV file")
    args = parser.parse_args()

    extract_odb(args.odb, args.output)
