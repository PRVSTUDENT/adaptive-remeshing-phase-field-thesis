#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
compare_re_equilibrated_displacements.py
========================================
Falsification Test for Hypothesis 1 and Hypothesis 4:
Compares the static re-equilibrated displacement field u* from Job 1414563
(M1_MC_STAGE_C1_1_SAMEMESH_CONSISTENT_RELHOLD.odb, Step 1)
against the authentic continuous ground truth u_cont from Job 1414571.
"""

import json
import math
import sys
import os

try:
    from odbAccess import openOdb
except ImportError:
    print("Must be run inside Abaqus Python")
    sys.exit(1)

gt_json_path = "/scratch9/pr21vyci/runs/mode1_fine_baseline_enriched/fine_baseline_ground_truth_u0050.json"
odb_path = "/scratch9/pr21vyci/runs/mode1_stage_c1_1_nonmatching_transfer/M1_MC_STAGE_C1_1_SAMEMESH_CONSISTENT_RELHOLD.odb"

print("=" * 70)
print("COMPARING RE-EQUILIBRATED DISPLACEMENTS u* vs GROUND TRUTH u_cont")
print("=" * 70)

print("Loading ground truth from: %s" % gt_json_path)
with open(gt_json_path, "r") as f:
    gt_data = json.load(f)

gt_nodal = gt_data["nodal_state"]
print("Loaded ground truth for %d nodes." % len(gt_nodal))
gt_rf2 = gt_data["metadata"]["rf2_rp_N"]
print("Ground truth RF2 = %g N" % gt_rf2)

print("Opening ODB: %s" % odb_path)
odb = openOdb(odb_path, readOnly=True)

step_names = list(odb.steps.keys())
print("Step names in ODB: %s" % step_names)

step1_name = step_names[0]
step1 = odb.steps[step1_name]
frame1 = step1.frames[-1]
print("Step 1 (%s) terminal frame: %s | val: %g" % (step1_name, frame1.frameId, frame1.frameValue))

u_field1 = frame1.fieldOutputs["U"]
rf_field1 = frame1.fieldOutputs["RF"]

rf2_step1 = 0.0
for v in rf_field1.values:
    if v.nodeLabel == 999999:
        val = float(v.data[1])
        # In Abaqus, RF is in kN if forces are in kN; convert to N if < 100
        rf2_step1 = val * 1000.0 if abs(val) < 100.0 else val
        break
print("Job 1414563 Step-1 RF2 = %g N (deficit: %g N / %.2f%%)" % (
    rf2_step1, rf2_step1 - gt_rf2, (rf2_step1 - gt_rf2)/gt_rf2 * 100.0
))

l2_err_sq = 0.0
l2_ref_sq = 0.0
max_diff = 0.0
max_diff_node = -1

top_nodes_gt_ux = []
top_nodes_u_star_ux = []
bot_nodes_gt_uy = []
bot_nodes_u_star_uy = []

node_count = 0
for v in u_field1.values:
    n = int(v.nodeLabel)
    if n == 999999:
        continue
    
    n_str = str(n)
    if n_str not in gt_nodal:
        continue
    
    node_count += 1
    gt_node = gt_nodal[n_str]
    x, y = gt_node["coord"]
    ux_gt = gt_node["ux"]
    uy_gt = gt_node["uy"]
    
    ux_star = float(v.data[0])
    uy_star = float(v.data[1])
    
    diff_x = ux_star - ux_gt
    diff_y = uy_star - uy_gt
    diff_mag = math.sqrt(diff_x**2 + diff_y**2)
    ref_mag = math.sqrt(ux_gt**2 + uy_gt**2)
    
    l2_err_sq += diff_mag**2
    l2_ref_sq += ref_mag**2
    
    if diff_mag > max_diff:
        max_diff = diff_mag
        max_diff_node = n
        
    if abs(y - 1.0) < 1e-5:
        top_nodes_gt_ux.append(ux_gt)
        top_nodes_u_star_ux.append(ux_star)
        
    if abs(y - 0.0) < 1e-5:
        bot_nodes_gt_uy.append(uy_gt)
        bot_nodes_u_star_uy.append(uy_star)

odb.close()

rel_l2_err = math.sqrt(l2_err_sq) / math.sqrt(l2_ref_sq) if l2_ref_sq > 0 else 0.0
print("-" * 70)
print("DISPLACEMENT COMPARISON RESULTS (across %d nodes):" % node_count)
print("  Relative L2 Displacement Error ||u* - u_cont||_L2 / ||u_cont||_L2: %.4f%%" % (rel_l2_err * 100.0))
print("  Max Absolute Difference: %g mm at Node %d" % (max_diff, max_diff_node))
if str(max_diff_node) in gt_nodal:
    gt_m = gt_nodal[str(max_diff_node)]
    print("    Node %d Coord: %s" % (max_diff_node, gt_m["coord"]))
    print("    Ground Truth (ux, uy): (%g, %g)" % (gt_m["ux"], gt_m["uy"]))

print("-" * 70)
print("BOUNDARY CONDITION AUDIT:")
print("  Top Boundary Nodes (y=1.0, N=%d):" % len(top_nodes_gt_ux))
max_gt_top_ux = max([abs(x) for x in top_nodes_gt_ux]) if top_nodes_gt_ux else 0.0
max_star_top_ux = max([abs(x) for x in top_nodes_u_star_ux]) if top_nodes_u_star_ux else 0.0
mean_star_top_ux = sum([abs(x) for x in top_nodes_u_star_ux])/len(top_nodes_u_star_ux) if top_nodes_u_star_ux else 0.0
print("    Ground Truth max |ux|: %g mm (restrained u_x = 0)" % max_gt_top_ux)
print("    Job 1414563 u* max |ux|: %g mm (lateral contraction!)" % max_star_top_ux)
print("    Job 1414563 u* mean |ux|: %g mm" % mean_star_top_ux)

if max_star_top_ux > 1e-6 and max_gt_top_ux < 1e-10:
    print("  -> CONFIRMED: Top boundary lateral constraint (u_x = 0) was OMITTED in Job 1414563!")
    print("     The top edge contracted laterally by up to %g mm, directly lowering specimen stiffness." % max_star_top_ux)

node1_gt = gt_nodal.get("1", {})
node33_gt = gt_nodal.get("33", {})
print("-" * 70)
print("PIN NODE AUDIT:")
print("  Node 1 Coord: %s | GT (ux, uy): (%g, %g)" % (
    node1_gt.get("coord"), node1_gt.get("ux", 0), node1_gt.get("uy", 0)
))
print("  Node 33 Coord: %s | GT (ux, uy): (%g, %g)" % (
    node33_gt.get("coord"), node33_gt.get("ux", 0), node33_gt.get("uy", 0)
))

results_summary = {
    "node_count": node_count,
    "rel_l2_displacement_error_pct": rel_l2_err * 100.0,
    "max_displacement_diff_mm": max_diff,
    "max_displacement_diff_node": max_diff_node,
    "ground_truth_rf2_N": gt_rf2,
    "re_equilibrated_rf2_N": rf2_step1,
    "force_deficit_N": rf2_step1 - gt_rf2,
    "force_deficit_pct": (rf2_step1 - gt_rf2)/gt_rf2 * 100.0,
    "top_boundary": {
        "num_nodes": len(top_nodes_gt_ux),
        "gt_max_abs_ux": max_gt_top_ux,
        "u_star_max_abs_ux": max_star_top_ux,
        "mean_u_star_abs_ux": mean_star_top_ux,
        "lateral_contraction_detected": bool(max_star_top_ux > 1e-6 and max_gt_top_ux < 1e-10)
    },
    "pin_nodes": {
        "node_1": node1_gt,
        "node_33": node33_gt
    }
}

out_summary_path = "/scratch9/pr21vyci/runs/mode1_fine_baseline_enriched/displacement_comparison_summary.json"
with open(out_summary_path, "w") as f:
    json.dump(results_summary, f, indent=2)
print("Saved summary to: %s" % out_summary_path)
print("=" * 70)
