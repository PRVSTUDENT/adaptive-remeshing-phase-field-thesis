# -*- coding: utf-8 -*-
"""
inspect_case3_staggered_odb.py
==============================
Inspects all converged frames in PK_SEC43_STAGGERED_JOB1.odb on the cluster
to identify transient crack propagation states across the primary notch-to-hole ligament.
"""
from __future__ import print_function
import sys
import os
import json
from odbAccess import openOdb

def main():
    odb_path = "/scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1/PK_SEC43_STAGGERED_JOB1.odb"
    if len(sys.argv) > 1:
        odb_path = sys.argv[1]

    if not os.path.exists(odb_path):
        print("ODB not found at: %s" % odb_path)
        sys.exit(1)

    print("Opening ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)

    root_assembly = odb.rootAssembly
    inst_name = list(root_assembly.instances.keys())[0]
    inst = root_assembly.instances[inst_name]
    print("Instance: %s (%d elements, %d nodes)" % (inst_name, len(inst.elements), len(inst.nodes)))

    nodes_dict = {}
    for n in inst.nodes:
        nodes_dict[n.label] = (float(n.coordinates[0]), float(n.coordinates[1]))

    elem_centroids = {}
    for el in inst.elements:
        if len(el.connectivity) >= 3:
            raw_eid = el.label
            pts = [nodes_dict[nid] for nid in el.connectivity if nid in nodes_dict]
            if len(pts) >= 3:
                cx = sum(p[0] for p in pts) / float(len(pts))
                cy = sum(p[1] for p in pts) / float(len(pts))
                elem_centroids[raw_eid] = (cx, cy)

    print("Loaded %d element centroids." % len(elem_centroids))

    # Corridor geometric definitions
    # Primary: Notch Tip (10.0, 70.0) -> Hole Flank (26.5, 51.0) mm
    # Secondary: Hole Flank (46.5, 51.0) -> Right Edge (65.0, 51.0) mm
    p_x0, p_y0 = 10.0, 70.0
    p_x1, p_y1 = 26.5, 51.0
    p_dx = p_x1 - p_x0
    p_dy = p_y1 - p_y0
    p_len = (p_dx**2 + p_dy**2)**0.5

    s_x0, s_y0 = 46.5, 51.0
    s_x1, s_y1 = 65.0, 51.0
    s_dx = s_x1 - s_x0
    s_dy = s_y1 - s_y0
    s_len = (s_dx**2 + s_dy**2)**0.5

    w_perp = 2.0 * 0.285  # 2 * l0 = 0.57 mm

    primary_eids = []
    secondary_eids = []

    for eid, (cx, cy) in elem_centroids.items():
        # Primary projection
        t = ((cx - p_x0) * p_dx + (cy - p_y0) * p_dy) / (p_len**2)
        if 0.0 <= t <= 1.0:
            proj_x = p_x0 + t * p_dx
            proj_y = p_y0 + t * p_dy
            dist = ((cx - proj_x)**2 + (cy - proj_y)**2)**0.5
            if dist <= w_perp:
                primary_eids.append((eid, t))

        # Secondary projection
        t_s = ((cx - s_x0) * s_dx + (cy - s_y0) * s_dy) / (s_len**2)
        if 0.0 <= t_s <= 1.0:
            proj_x = s_x0 + t_s * s_dx
            proj_y = s_y0 + t_s * s_dy
            dist_s = ((cx - proj_x)**2 + (cy - proj_y)**2)**0.5
            if dist_s <= w_perp:
                secondary_eids.append((eid, t_s))

    print("Elements in Primary Corridor (w_perp=%.2f mm): %d" % (w_perp, len(primary_eids)))
    print("Elements in Secondary Corridor (w_perp=%.2f mm): %d" % (w_perp, len(secondary_eids)))

    timeline = []

    for step_name in odb.steps.keys():
        step = odb.steps[step_name]
        n_frames = len(step.frames)
        print("\nStep: %s, total frames: %d" % (step_name, n_frames))

        for f_idx in range(n_frames):
            frame = step.frames[f_idx]
            frame_val = float(frame.frameValue)
            total_time = frame_val if step_name == "Step-1" else 1.0 + frame_val

            sdv1_field = None
            for k in frame.fieldOutputs.keys():
                if 'SDV1' in k:
                    sdv1_field = frame.fieldOutputs[k]
                    break

            if sdv1_field is None:
                continue

            elem_d = {}
            for v in sdv1_field.values:
                eid = v.elementLabel
                if eid not in elem_d:
                    elem_d[eid] = []
                elem_d[eid].append(float(v.data))

            # Average per element
            avg_d = {eid: sum(vals)/float(len(vals)) for eid, vals in elem_d.items()}

            # Primary corridor stats
            p_d_vals = [avg_d.get(eid, 0.0) for eid, t in primary_eids]
            p_broken = [t for eid, t in primary_eids if avg_d.get(eid, 0.0) >= 0.8]
            p_max_d = max(p_d_vals) if p_d_vals else 0.0
            p_crack_front_t = max(p_broken) if p_broken else 0.0

            # Secondary corridor stats
            s_d_vals = [avg_d.get(eid, 0.0) for eid, t in secondary_eids]
            s_broken = [t for eid, t in secondary_eids if avg_d.get(eid, 0.0) >= 0.8]
            s_max_d = max(s_d_vals) if s_d_vals else 0.0
            s_crack_front_t = max(s_broken) if s_broken else 0.0

            record = {
                "step": step_name,
                "frame": f_idx,
                "time": total_time,
                "p_max_d": p_max_d,
                "p_broken_count": len(p_broken),
                "p_crack_front_s": p_crack_front_t * p_len,
                "p_crack_front_fraction": p_crack_front_t,
                "s_max_d": s_max_d,
                "s_broken_count": len(s_broken),
                "s_crack_front_s": s_crack_front_t * s_len,
                "s_crack_front_fraction": s_crack_front_t
            }
            timeline.append(record)

    out_json = "/scratch9/pr21vyci/runs/mode1_pk_sec43_staggered_job1/f1742_case3_transient_timeline.json"
    with open(out_json, "w") as fp:
        json.dump(timeline, fp, indent=2)

    print("\nSaved timeline with %d frames to %s" % (len(timeline), out_json))

    # Print summary table of interesting frames (where damage changes or crack advances)
    print("\n" + "="*95)
    print("STEP     FRAME   TIME [s]   P_MAX_D   P_BROKEN  P_FRONT [mm]   S_MAX_D   S_BROKEN  S_FRONT [mm]")
    print("="*95)
    last_p_front = -1.0
    last_s_front = -1.0
    for r in timeline:
        # print if crack front changed or at intervals
        p_front = r["p_crack_front_fraction"]
        s_front = r["s_crack_front_fraction"]
        if p_front != last_p_front or s_front != last_s_front or r["frame"] % 10 == 0:
            print("%-8s %4d   %8.4f   %7.4f   %7d   %8.2f (%4.1f%%)   %7.4f   %7d   %8.2f (%4.1f%%)" % (
                r["step"], r["frame"], r["time"],
                r["p_max_d"], r["p_broken_count"], r["p_crack_front_s"], p_front * 100.0,
                r["s_max_d"], r["s_broken_count"], r["s_crack_front_s"], s_front * 100.0
            ))
            last_p_front = p_front
            last_s_front = s_front
    print("="*95)

    odb.close()

if __name__ == '__main__':
    main()
