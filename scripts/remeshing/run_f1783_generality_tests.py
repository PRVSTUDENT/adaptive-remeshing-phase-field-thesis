# -*- coding: utf-8 -*-
"""
run_f1783_generality_tests.py
Task F1783 Reproducible Generality and Adaptive Refinement Runner:
Executes under Abaqus CAE noGUI environment:
  abaqus cae noGUI=scripts/remeshing/run_f1783_generality_tests.py
Validates:
1. Test A (Geometry Perturbation):
   - Modifies Case 3 dimensions (W=70, H=130, a=15, w=0.4, central hole (42,60,r=12), pins r=6) via config.
   - Measures actual Abaqus CAE Part face area: p.faces[0].getSize().
   - Compares with analytical area (8,409.416 mm^2), meshes part, audits FE quality, exports PK_TEST_A_PERT_PHYS.inp.
2. Test B (Indicator Perturbation):
   - Unchanged 1x1 mm Mode-I geometry.
   - Generates two synthetic donor ODBs:
     * DONOR_HORIZ.odb: error localized along horizontal line y = 0.50
     * DONOR_DIAG.odb:  error localized along rising diagonal path y = 0.50 + 0.70*(x - 0.50) terminating at y = 0.85
   - Executes Abaqus native execute_native_remesh() for both donors under identical RemeshingRule.
   - Audits spatial inspection windows at right boundary (x in [0.85, 1.00]):
     * Horizontal Window (y in [0.45, 0.55])
     * Diagonal Window   (y in [0.75, 0.90])
3. Compiles full execution receipts, logs, and SHA-256 hashes to:
   results/validation/f1783_generality_evidence.json.
"""
from __future__ import print_function
import os
import sys
import copy
import math
import json
import shutil
import hashlib

# Add framework to path
REPO_ROOT = os.path.abspath(os.getcwd())
sys.path.append(os.path.join(REPO_ROOT, "scripts", "remeshing"))

from reusable_2d_adaptive_framework import (
    AdaptiveConfig, get_geometry_adapter,
    AbaqusNativeRemeshingEngine, MeshQualityAuditEngine
)

from abaqus import mdb, backwardCompatibility
from abaqusConstants import *
from odbAccess import openOdb
backwardCompatibility.setValues(includeDeprecated=True, reportDeprecated=False)


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()


def run_test_a():
    print("\n" + "=" * 80)
    print("TEST A: GEOMETRY PERTURBATION (CASE 3 NOTCHED PLATE)")
    print("=" * 80)
    cfg_path = os.path.join(REPO_ROOT, "configs", "remeshing", "f1783_test_a_perturbed_case3.json")
    out_dir = os.path.join(REPO_ROOT, "runs", "test_a_geometry_perturbation")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    cfg = AdaptiveConfig.from_json(cfg_path)
    adapter = get_geometry_adapter(cfg)
    print("Loaded Perturbed Config: %s" % cfg_path)
    print("Plate: %.1f x %.1f mm, Notch: a=%.1f, w=%.2f" % (cfg.plate_w, cfg.plate_h, cfg.notch_a, cfg.notch_w))
    print("Holes: %s" % str(adapter.get_hole_definitions()))

    # Analytical area calculation:
    # Plate 70x130, notch 15x(2*0.4), central hole r=12, pin holes r=6 and r=6
    area_plate = 70.0 * 130.0
    area_notch = 15.0 * (2.0 * 0.4)
    area_holes = math.pi * (12.0**2 + 6.0**2 + 6.0**2)
    analytical_area = area_plate - area_notch - area_holes

    # Build CAE Part in Abaqus
    mname = "Model_TestA_Perturbed"
    if mname in mdb.models:
        del mdb.models[mname]
    m = mdb.Model(name=mname)

    p, a, inst = AbaqusNativeRemeshingEngine.build_cae_geometry(
        m, adapter, cfg, seed_size=1.5, part_name="PART_TESTA", instance_name="PART_TESTA_1"
    )

    cad_area = p.faces[0].getSize()
    delta_area = abs(cad_area - analytical_area)
    print("Analytical Face Area: %.6f mm^2" % analytical_area)
    print("Abaqus CAE Face Area:  %.6f mm^2" % cad_area)
    print("Delta Area:           %.6f mm^2" % delta_area)

    # Mesh and export physical INP
    p.generateMesh()
    m.rootAssembly.regenerate()

    mesh_inp_path = os.path.join(out_dir, "PK_TEST_A_PERT_PHYS.inp")
    job_name = "Job_TestA"
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
    j = mdb.Job(name=job_name, model=mname, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)

    raw_inp = job_name + ".inp"
    if os.path.exists(raw_inp):
        if os.path.exists(mesh_inp_path):
            os.remove(mesh_inp_path)
        shutil.move(raw_inp, mesh_inp_path)

    audit = MeshQualityAuditEngine.evaluate_mesh(mesh_inp_path, l0_mm=cfg.l0, adapter=adapter)
    print("Physical Mesh Elements: %d (%.2f%% Quads, min det(J)=%.3e, max AR=%.3f)" % (
        audit["total_elements"], audit["quad_percent"], audit["min_det_j"], audit["max_aspect_ratio"]
    ))

    receipt = {
        "test": "Test A: Geometry Perturbation",
        "benchmark": "Case 3 (Notched Plate with Pins)",
        "config_path": cfg_path,
        "config_sha256": compute_sha256(cfg_path),
        "physical_mesh_path": mesh_inp_path,
        "physical_mesh_sha256": compute_sha256(mesh_inp_path),
        "analytical_area_mm2": analytical_area,
        "measured_cad_area_mm2": cad_area,
        "area_discrepancy_mm2": delta_area,
        "elements": audit["total_elements"],
        "quad_percent": audit["quad_percent"],
        "min_det_j": audit["min_det_j"],
        "max_aspect_ratio": audit["max_aspect_ratio"],
        "status": "PASS" if delta_area < 0.01 and audit["min_det_j"] > 0 else "FAIL"
    }
    return receipt


def run_test_b():
    print("\n" + "=" * 80)
    print("TEST B: INDICATOR PERTURBATION (RESPONSIVE ADAPTIVE REFINEMENT)")
    print("=" * 80)
    cfg_path = os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case1_mode1_edge_crack.json")
    cfg = AdaptiveConfig.from_json(cfg_path)
    out_dir = os.path.join(REPO_ROOT, "runs", "test_b_indicator_perturbation")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    donor_template = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "211_f1719_coarse_recovery", "PK_F1719_REC_STATE0_PHYS.odb")
    odb_horiz_path = os.path.join(out_dir, "DONOR_HORIZ.odb")
    odb_diag_path = os.path.join(out_dir, "DONOR_DIAG.odb")

    # Generate synthetic donor ODBs
    shutil.copyfile(donor_template, odb_horiz_path)
    shutil.copyfile(donor_template, odb_diag_path)

    for odb_path, mode in [(odb_horiz_path, 'HORIZ'), (odb_diag_path, 'DIAG')]:
        odb = openOdb(odb_path, readOnly=False)
        step = odb.steps['RECOVERY_STEP']
        frame = step.frames[-1]
        inst = odb.rootAssembly.instances['PART-1-1']

        eri_fo = frame.fieldOutputs['MISESERI']
        elem_labels = [v.elementLabel for v in eri_fo.values]
        node_coords = {n.label: (n.coordinates[0], n.coordinates[1]) for n in inst.nodes}

        new_eri = []
        for v in eri_fo.values:
            el = v.elementLabel
            elem = inst.elements[el - 1]
            pts = [node_coords[nl] for nl in elem.connectivity if nl in node_coords]
            cx = sum([p[0] for p in pts]) / float(len(pts))
            cy = sum([p[1] for p in pts]) / float(len(pts))

            if mode == 'HORIZ':
                # Active along horizontal ligament y = 0.50, x in [0.50, 1.00]
                dist = abs(cy - 0.50) if cx >= 0.45 else 1.0
            else:
                # Active along rising diagonal line from (0.50, 0.50) to (1.00, 0.85)
                if cx >= 0.45:
                    y_line = 0.50 + 0.70 * (cx - 0.50)
                    dist = abs(cy - y_line)
                else:
                    dist = 1.0

            # High error (requires fine mesh) if dist < 0.03, else low error
            if dist < 0.03:
                val = 200.0
            else:
                val = 2.0
            new_eri.append((val,))

        new_frame = step.Frame(frameId=1001, frameValue=10.0, description='Controlled Test Indicator (%s)' % mode)
        evol_vals = [(v.data,) for v in frame.fieldOutputs['EVOL'].values]
        fo_evol = new_frame.FieldOutput(name='EVOL', description='Element volume', type=SCALAR)
        fo_evol.addData(position=WHOLE_ELEMENT, instance=inst, labels=elem_labels, data=evol_vals)

        fo_new = new_frame.FieldOutput(name='MISESERI', description='Controlled Test Indicator (%s)' % mode, type=SCALAR)
        fo_new.addData(position=WHOLE_ELEMENT, instance=inst, labels=elem_labels, data=new_eri)

        avg_vals = [(100.0,) for _ in elem_labels]
        fo_avg = new_frame.FieldOutput(name='MISESAVG', description='Uniform Reference Average Stress', type=SCALAR)
        fo_avg.addData(position=WHOLE_ELEMENT, instance=inst, labels=elem_labels, data=avg_vals)

        odb.save()
        odb.close()

    print("Created Donor 1 (Horizontal Indicator) and Donor 2 (Diagonal Indicator).")

    # Execute Abaqus native remeshing for both
    cfg.step_name = 'RECOVERY_STEP'
    cfg.output_frequency = "LAST_INCREMENT"
    cfg.error_target = 10.0
    out_dir_horiz = os.path.join(out_dir, "horiz")
    out_dir_diag = os.path.join(out_dir, "diag")
    if not os.path.exists(out_dir_horiz): os.makedirs(out_dir_horiz)
    if not os.path.exists(out_dir_diag): os.makedirs(out_dir_diag)

    print("Executing Adaptive Remesh for Donor 1 (Horizontal)...")
    inp_horiz = AbaqusNativeRemeshingEngine.execute_native_remesh(
        config=cfg, donor_odb_path=odb_horiz_path, output_dir=out_dir_horiz, model_name='Model_Horiz'
    )

    print("Executing Adaptive Remesh for Donor 2 (Diagonal)...")
    inp_diag = AbaqusNativeRemeshingEngine.execute_native_remesh(
        config=cfg, donor_odb_path=odb_diag_path, output_dir=out_dir_diag, model_name='Model_Diag'
    )

    # Spatial audit in the two boundary inspection windows (x in [0.85, 1.00]):
    # Window H (Horizontal): y in [0.45, 0.55]
    # Window D (Diagonal):   y in [0.75, 0.90]
    def audit_boundary_windows(inp_path):
        nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(inp_path)
        all_elems = dict(quads)
        all_elems.update(tris)

        h_win = []
        d_win = []
        for eid, conn in all_elems.items():
            pts = [nodes[n] for n in conn if n in nodes]
            cx = sum([p[0] for p in pts]) / float(len(pts))
            cy = sum([p[1] for p in pts]) / float(len(pts))
            if len(pts) == 4:
                x1, y1 = pts[0]; x2, y2 = pts[1]; x3, y3 = pts[2]; x4, y4 = pts[3]
                area = 0.5 * abs((x1*y2 - x2*y1) + (x2*y3 - x3*y2) + (x3*y4 - x4*y3) + (x4*y1 - x1*y4))
            else:
                x1, y1 = pts[0]; x2, y2 = pts[1]; x3, y3 = pts[2]
                area = 0.5 * abs(x1*(y2 - y3) + x2*(y3 - y1) + x3*(y1 - y2))
            h = math.sqrt(max(1e-12, area))

            if 0.85 <= cx <= 1.00 and 0.45 <= cy <= 0.55:
                h_win.append(h)
            if 0.85 <= cx <= 1.00 and 0.75 <= cy <= 0.90:
                d_win.append(h)

        mean_h = (sum(h_win) / float(len(h_win)) * 1000.0) if h_win else 0.0
        mean_d = (sum(d_win) / float(len(d_win)) * 1000.0) if d_win else 0.0
        return {
            "total_elements": len(all_elems),
            "horiz_window_elements": len(h_win),
            "horiz_window_mean_h_um": mean_h,
            "diag_window_elements": len(d_win),
            "diag_window_mean_h_um": mean_d,
            "size_ratio_diag_over_horiz": (mean_d / mean_h) if mean_h > 0 else 0.0
        }

    h_metrics = audit_boundary_windows(inp_horiz)
    d_metrics = audit_boundary_windows(inp_diag)

    ratio_h = h_metrics["size_ratio_diag_over_horiz"]
    ratio_d = d_metrics["size_ratio_diag_over_horiz"]
    inversion_factor = (ratio_h / ratio_d) if ratio_d > 0 else 0.0

    print("\nMesh 1 (Horizontal Donor): Total=%d, Horiz Win=%d (mean h=%.2f um), Diag Win=%d (mean h=%.2f um), Ratio=%.3f" % (
        h_metrics["total_elements"], h_metrics["horiz_window_elements"], h_metrics["horiz_window_mean_h_um"],
        h_metrics["diag_window_elements"], h_metrics["diag_window_mean_h_um"], ratio_h
    ))
    print("Mesh 2 (Diagonal Donor):   Total=%d, Horiz Win=%d (mean h=%.2f um), Diag Win=%d (mean h=%.2f um), Ratio=%.3f" % (
        d_metrics["total_elements"], d_metrics["horiz_window_elements"], d_metrics["horiz_window_mean_h_um"],
        d_metrics["diag_window_elements"], d_metrics["diag_window_mean_h_um"], ratio_d
    ))
    print("Ratio Inversion Factor: %.2fx" % inversion_factor)

    receipt = {
        "test": "Test B: Indicator Perturbation",
        "benchmark": "Case 1 Mode-I Domain (1x1 mm)",
        "donor_horizontal": {
            "path": odb_horiz_path,
            "sha256": compute_sha256(odb_horiz_path)
        },
        "donor_diagonal": {
            "path": odb_diag_path,
            "sha256": compute_sha256(odb_diag_path)
        },
        "mesh_horizontal": {
            "path": inp_horiz,
            "sha256": compute_sha256(inp_horiz),
            "metrics": h_metrics
        },
        "mesh_diagonal": {
            "path": inp_diag,
            "sha256": compute_sha256(inp_diag),
            "metrics": d_metrics
        },
        "ratio_horizontal_mesh": ratio_h,
        "ratio_diagonal_mesh": ratio_d,
        "inversion_factor": inversion_factor,
        "status": "PASS" if inversion_factor > 1.5 else "FAIL"
    }
    return receipt


def main():
    print("=" * 80)
    print("TASK F1783 REPRODUCIBLE GENERALITY RUNNER (ABAQUS CAE noGUI)")
    print("=" * 80)

    receipt_a = run_test_a()
    receipt_b = run_test_b()

    evidence = {
        "task_id": "F1783-METHOD-A-QUALIFICATION-AND-EVIDENCE-CORRECTION",
        "test_a_geometry_perturbation": receipt_a,
        "test_b_indicator_perturbation": receipt_b,
        "overall_status": "PASS" if receipt_a["status"] == "PASS" and receipt_b["status"] == "PASS" else "FAIL"
    }

    out_json = os.path.join(REPO_ROOT, "results", "validation", "f1783_generality_evidence.json")
    out_dir = os.path.dirname(out_json)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    with open(out_json, "w") as f:
        json.dump(evidence, f, indent=2)

    print("\n" + "=" * 80)
    print("GENERALITY TESTS COMPLETED. Summary published to:")
    print("  %s" % out_json)
    print("Test A Status: %s" % receipt_a["status"])
    print("Test B Status: %s" % receipt_b["status"])
    print("Overall Status: %s" % evidence["overall_status"])
    print("=" * 80)


if __name__ == '__main__':
    main()
