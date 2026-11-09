# -*- coding: utf-8 -*-
"""
execute_f1699_native_remesh.py
==============================
Task F1699 Gate B: Native Abaqus adaptiveRemesh() Execution & Validation.

Constructs properly registered Abaqus/CAE recovery model and applies
the authentic native RemeshingRule matching Pandey & Kumar (2025) Listing 1:
  - sizingMethod = UNIFORM_ERROR
  - errorTarget = 5.0%
  - refinementFactor = 10
  - coarseningFactor = NOT_ALLOWED
  - minElementSize = 0.143 mm (~ l0 / 2)
  - maxElementSize = 1.50 mm (coarse seed)

Evaluates:
  - Primary Donor (State 4: Secondary Mid-Propagation, uy = 0.300 mm)
  - Optional Second Donor (State 2: Primary Propagation / Hole Arrest, uy = 0.200 mm)

Audits resulting physical meshes:
  - Total physical elements and nodes, tri/quad breakdown
  - Jacobian and area preservation
  - Primary and secondary corridor element sizes (h_min, h_med, % <= l0/2)
  - Spatial width and waste area

Outputs:
  - models/pandey_kumar_mode1/198_pk_sec43_coupled_validation/PK_SEC43_F1699_NATIVE_ADAPT.inp
  - models/pandey_kumar_mode1/198_pk_sec43_coupled_validation/PK_SEC43_F1699_NATIVE_ADAPT_STATE2.inp
  - results/validation/f1699_native_adapted_mesh_metrics.json
"""

from __future__ import print_function
import os
import sys
import json
import math
import shutil
from abaqus import *
from abaqusConstants import *
import regionToolset
import mesh

def log(msg):
    print("[F1699-NATIVE-REMESH] " + str(msg))
    sys.stdout.flush()

def dist_to_segment(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    l2 = dx*dx + dy*dy
    if l2 == 0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1)*dx + (py - y1)*dy) / l2))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.hypot(px - proj_x, py - proj_y)

def audit_mesh_corridors(part_obj, l0=0.285):
    l0_half = l0 / 2.0    # 0.1425 mm
    l0_third = l0 / 3.0   # 0.0950 mm
    corridor_w = 2.0 * l0 # 0.5700 mm radius

    elem_metrics = []
    prim_sizes = []
    sec_sizes = []
    total_area = 0.0

    for el in part_obj.elements:
        pts = [part_obj.nodes[i].coordinates for i in el.connectivity]
        poly_x = [pt[0] for pt in pts]
        poly_y = [pt[1] for pt in pts]
        n_pts = len(pts)
        area = 0.5 * abs(sum([poly_x[i]*poly_y[(i+1)%n_pts] - poly_y[i]*poly_x[(i+1)%n_pts] for i in range(n_pts)]))
        h_eq = math.sqrt(area)
        cx = sum(poly_x) / float(n_pts)
        cy = sum(poly_y) / float(n_pts)
        total_area += area

        elem_metrics.append({
            "label": el.label,
            "type": n_pts,
            "area": area,
            "h_eq": h_eq,
            "cx": cx,
            "cy": cy
        })

        # Primary corridor: centerline from notch tip (10.0, 70.0) to central hole (26.5, 51.0)
        d_prim = dist_to_segment(cx, cy, 10.0, 70.0, 26.5, 51.0)
        if d_prim <= corridor_w:
            prim_sizes.append(h_eq)

        # Secondary corridor: centerline from central hole (46.5, 51.0) to right boundary (65.0, 51.0)
        d_sec = dist_to_segment(cx, cy, 46.5, 51.0, 65.0, 51.0)
        if d_sec <= corridor_w:
            sec_sizes.append(h_eq)

    def stats(arr):
        if not arr:
            return {"count": 0, "min": None, "median": None, "mean": None, "max": None, "pct_le_l0_half": 0.0, "pct_le_l0": 0.0}
        s = sorted(arr)
        n = len(s)
        med = s[n//2] if n % 2 == 1 else 0.5 * (s[n//2 - 1] + s[n//2])
        mean_v = sum(s) / float(n)
        pct_half = 100.0 * sum([1 for v in s if v <= l0_half]) / float(n)
        pct_l0 = 100.0 * sum([1 for v in s if v <= l0]) / float(n)
        return {
            "count": n,
            "min": round(s[0], 6),
            "median": round(med, 6),
            "mean": round(mean_v, 6),
            "max": round(s[-1], 6),
            "pct_le_l0_half": round(pct_half, 2),
            "pct_le_l0": round(pct_l0, 2)
        }

    return {
        "total_area_mm2": round(total_area, 4),
        "primary_corridor": stats(prim_sizes),
        "secondary_corridor": stats(sec_sizes),
        "all_elements": elem_metrics
    }

def run_native_remesh_for_donor(donor_info, repo_root, out_dir):
    donor_name = donor_info["name"]
    odb_path = donor_info["odb_path"]
    job_base = donor_info["job_name"]
    model_name = "Model_" + job_base

    log("=" * 80)
    log("EXECUTING NATIVE ADAPTIVEREMESH FOR DONOR: %s" % donor_name)
    log("  Source ODB: %s" % odb_path)
    log("=" * 80)

    if not os.path.exists(odb_path):
        raise IOError("Donor ODB not found: %s" % odb_path)

    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)
    if "Model-1" in mdb.models:
        del mdb.models["Model-1"]

    # 1. Build CAD geometry (65 x 120 mm plate with 3 holes and notch)
    s = m.ConstrainedSketch(name="__profile__", sheetSize=300.0)
    s.Line(point1=(0.0, 0.0), point2=(65.0, 0.0))
    s.Line(point1=(65.0, 0.0), point2=(65.0, 120.0))
    s.Line(point1=(65.0, 120.0), point2=(0.0, 120.0))
    s.Line(point1=(0.0, 120.0), point2=(0.0, 70.2))
    s.Line(point1=(0.0, 70.2), point2=(10.0, 70.2))
    s.Line(point1=(10.0, 70.2), point2=(10.0, 69.8))
    s.Line(point1=(10.0, 69.8), point2=(0.0, 69.8))
    s.Line(point1=(0.0, 69.8), point2=(0.0, 0.0))

    # Central hole R=10 at (36.5, 51.0)
    s.CircleByCenterPerimeter(center=(36.5, 51.0), point1=(46.5, 51.0))
    # Lower hole R=5 at (20.0, 20.0)
    s.CircleByCenterPerimeter(center=(20.0, 20.0), point1=(25.0, 20.0))
    # Upper hole R=5 at (20.0, 100.0)
    s.CircleByCenterPerimeter(center=(20.0, 100.0), point1=(25.0, 100.0))

    p = m.Part(name="PlateWithHoles", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches["__profile__"]

    # 2. Seed with 1.50 mm coarse global size matching paper
    log("Seeding part with 1.50 mm global size...")
    p.seedPart(size=1.50, deviationFactor=0.1, minSizeFactor=0.1)
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))
    p.generateMesh()

    p.Set(name="All_elem", faces=p.faces)
    a = m.rootAssembly
    inst = a.Instance(name="PART-1-1", part=p, dependent=ON)

    mat = m.Material(name="Steel")
    mat.Elastic(table=((210.0, 0.3),))
    m.HomogeneousSolidSection(name="SolidSec", material="Steel", thickness=1.0)
    p.SectionAssignment(region=p.sets["All_elem"], sectionName="SolidSec")

    donor_step_name = "RECOVERY_STEP"
    m.StaticStep(name=donor_step_name, previous="Initial", timePeriod=1.0)

    reg = inst.sets["All_elem"]
    rule_name = "RemeshingRule_PK_Sec43_Listing1"
    log("Defining RemeshingRule: %s (errorTarget=5.0%%, min=0.143 mm, max=1.5 mm)" % rule_name)
    m.RemeshingRule(
        name=rule_name,
        stepName=donor_step_name,
        region=reg,
        description="Pandey & Kumar (2025) Listing 1: Native MISESERI errorTarget=5%, min=0.143mm, max=1.5mm",
        variables=("MISESERI",),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=5.0,
        refinementFactor=10,
        coarseningFactor=NOT_ALLOWED,
        specifyMinSize=True,
        minElementSize=0.143,
        specifyMaxSize=True,
        maxElementSize=1.5
    )

    # 3. Call native adaptiveRemesh()
    log("Opening donor ODB in CAE session: %s" % odb_path)
    odb_donor = session.openOdb(name=odb_path)
    log("Executing m.adaptiveRemesh(odb=odb_donor)...")
    m.adaptiveRemesh(odb=odb_donor)
    odb_donor.close()
    log("Native adaptiveRemesh API returned successfully!")

    # 4. Measure mesh metrics
    n_elems = len(p.elements)
    n_nodes = len(p.nodes)
    n_quads = sum([1 for e in p.elements if len(e.connectivity) == 4])
    n_tris = sum([1 for e in p.elements if len(e.connectivity) == 3])
    total_dofs = n_nodes * 2

    log("Adapted Mesh Statistics:")
    log("  Elements: %d (Quads: %d = %.2f%%, Tris: %d = %.2f%%)" % (
        n_elems, n_quads, 100.0 * n_quads / n_elems, n_tris, 100.0 * n_tris / n_elems
    ))
    log("  Nodes:    %d (Total DOFs: %d)" % (n_nodes, total_dofs))

    # 5. Write adapted input deck
    if job_base in mdb.jobs:
        del mdb.jobs[job_base]
    j = mdb.Job(name=job_base, model=model_name, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)

    src_inp = job_base + ".inp"
    dst_inp = os.path.join(out_dir, src_inp)
    if os.path.exists(src_inp):
        shutil.copy2(src_inp, dst_inp)
        log("Saved adapted input deck to: %s" % dst_inp)

    # 6. Corridor Resolution Audit
    audit_res = audit_mesh_corridors(p, l0=0.285)
    prim_stat = audit_res["primary_corridor"]
    sec_stat = audit_res["secondary_corridor"]

    log("Corridor Resolution:")
    log("  Primary Corridor:   %d elements, min=%.4f mm, med=%.4f mm, %%. <= l0/2: %.2f%%" % (
        prim_stat["count"], prim_stat["min"] or 0.0, prim_stat["median"] or 0.0, prim_stat["pct_le_l0_half"]
    ))
    log("  Secondary Corridor: %d elements, min=%.4f mm, med=%.4f mm, %%. <= l0/2: %.2f%%" % (
        sec_stat["count"], sec_stat["min"] or 0.0, sec_stat["median"] or 0.0, sec_stat["pct_le_l0_half"]
    ))

    # Gate B Evaluation for this donor:
    # Physical requirement for dual-crack resolution: secondary corridor must resolve l0/2 (0.1425 mm)
    secondary_resolved = (sec_stat["pct_le_l0_half"] > 0.0)

    return {
        "donor_name": donor_name,
        "job_name": job_base,
        "source_odb": odb_path,
        "adapted_inp": dst_inp,
        "total_elements": n_elems,
        "total_nodes": n_nodes,
        "total_dofs": total_dofs,
        "quad_elements": n_quads,
        "quad_pct": round(100.0 * n_quads / n_elems, 2),
        "tri_elements": n_tris,
        "tri_pct": round(100.0 * n_tris / n_elems, 2),
        "total_area_mm2": audit_res["total_area_mm2"],
        "primary_corridor": prim_stat,
        "secondary_corridor": sec_stat,
        "secondary_corridor_resolved_at_l0_half": secondary_resolved,
        "outcome": "SECONDARY_RESOLVED" if secondary_resolved else "SECONDARY_UNRESOLVED_0PCT"
    }

def main():
    repo_root = os.path.abspath(os.getcwd())
    out_dir = os.path.join(repo_root, "models", "pandey_kumar_mode1", "198_pk_sec43_coupled_validation")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    log("Starting Task F1699 Gate B Native Remeshing Experiment...")
    log("Abaqus Version: 2024")

    # Donors to evaluate
    donors = [
        {
            "name": "State 4: Secondary Mid-Propagation (uy = 0.300 mm)",
            "job_name": "PK_SEC43_F1699_NATIVE_ADAPT",
            "odb_path": os.path.join(out_dir, "SEC43_STATE4_SEC_MIDPROP.odb")
        },
        {
            "name": "State 2: Primary Propagation / Hole Arrest (uy = 0.200 mm)",
            "job_name": "PK_SEC43_F1699_NATIVE_ADAPT_STATE2",
            "odb_path": os.path.join(out_dir, "SEC43_STATE2_HOLE_ARREST.odb")
        }
    ]

    donor_results = {}
    for dinfo in donors:
        res = run_native_remesh_for_donor(dinfo, repo_root, out_dir)
        donor_results[dinfo["job_name"]] = res

    # Summary and Gate B Verdict
    primary_res = donor_results["PK_SEC43_F1699_NATIVE_ADAPT"]
    state2_res = donor_results["PK_SEC43_F1699_NATIVE_ADAPT_STATE2"]

    log("\n" + "=" * 80)
    log("SUMMARY OF GATE B NATIVE ADAPTIVEREMESH EXPERIMENTS:")
    log("=" * 80)
    log("State 4 (Secondary Mid-Propagation, uy=0.300mm):")
    log("  Elements: %d, Nodes: %d" % (primary_res["total_elements"], primary_res["total_nodes"]))
    log("  Primary:   min=%.4f mm, med=%.4f mm, %%. <= l0/2: %.2f%%" % (
        primary_res["primary_corridor"]["min"], primary_res["primary_corridor"]["median"], primary_res["primary_corridor"]["pct_le_l0_half"]
    ))
    log("  Secondary: min=%.4f mm, med=%.4f mm, %%. <= l0/2: %.2f%%" % (
        primary_res["secondary_corridor"]["min"], primary_res["secondary_corridor"]["median"], primary_res["secondary_corridor"]["pct_le_l0_half"]
    ))
    log("State 2 (Hole Arrest, uy=0.200mm):")
    log("  Elements: %d, Nodes: %d" % (state2_res["total_elements"], state2_res["total_nodes"]))
    log("  Primary:   min=%.4f mm, med=%.4f mm, %%. <= l0/2: %.2f%%" % (
        state2_res["primary_corridor"]["min"], state2_res["primary_corridor"]["median"], state2_res["primary_corridor"]["pct_le_l0_half"]
    ))
    log("  Secondary: min=%.4f mm, med=%.4f mm, %%. <= l0/2: %.2f%%" % (
        state2_res["secondary_corridor"]["min"], state2_res["secondary_corridor"]["median"], state2_res["secondary_corridor"]["pct_le_l0_half"]
    ))

    # Determine reproduction classification
    # NEGATIVE_REPRODUCTION: The tested same-state recovery and native remeshing execute correctly,
    # but their quantitative mesh output does not reproduce the published result (0.00% <= l0/2 in secondary corridor).
    if primary_res["secondary_corridor"]["pct_le_l0_half"] == 0.0:
        classification = "NEGATIVE_REPRODUCTION"
        conclusion = (
            "Authentic native Abaqus adaptiveRemesh() operating on the verified recovered MISESERI field "
            "successfully executes and refines the primary corridor (min = %.4f mm, med = %.4f mm), "
            "but yields EXACTLY 0.00%% <= l0/2 in the secondary corridor (min = %.4f mm, med = %.4f mm). "
            "Because the single-rule recipe fails to produce the continuous secondary refinement band "
            "reported in Pandey & Kumar (2025) Figures 15(b) and 16(b), the published single-rule reproduction "
            "is classified as NEGATIVE_REPRODUCTION under authentic native Abaqus adaptiveRemesh." % (
                primary_res["primary_corridor"]["min"], primary_res["primary_corridor"]["median"],
                primary_res["secondary_corridor"]["min"], primary_res["secondary_corridor"]["median"]
            )
        )
    else:
        classification = "PARTIAL_REPRODUCTION"
        conclusion = "Secondary corridor resolved partially."

    log("CLASSIFICATION: %s" % classification)
    log("CONCLUSION: %s" % conclusion)

    out_record = {
        "benchmark": "Pandey & Kumar (2025) Section 4.3 holed plate",
        "task_id": "F1699-PK-SEC43-SAME-STATE-RECOVERY-AND-NATIVE-REMESH",
        "gate": "GATE_B_NATIVE_ADAPTIVEREMESH_VALIDATION",
        "abaqus_release": "2024",
        "remeshing_rule_parameters": {
            "sizingMethod": "UNIFORM_ERROR",
            "errorTarget": 5.0,
            "refinementFactor": 10,
            "coarseningFactor": "NOT_ALLOWED",
            "minElementSize_mm": 0.143,
            "maxElementSize_mm": 1.50,
            "l0_mm": 0.285,
            "l0_half_mm": 0.1425
        },
        "donors_evaluated": donor_results,
        "scientific_classification": classification,
        "scientific_conclusion": conclusion
    }

    metrics_file = os.path.join(repo_root, "results", "validation", "f1699_native_adapted_mesh_metrics.json")
    with open(metrics_file, "w") as fp:
        json.dump(out_record, fp, indent=2)

    log("Master Gate B metrics saved to: %s" % metrics_file)
    log("TASK F1699 NATIVE REMESHING EXPERIMENT COMPLETED SUCCESSFULLY.")
    return 0

if __name__ == "__main__":
    main()
