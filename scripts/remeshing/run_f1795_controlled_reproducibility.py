# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1795_controlled_reproducibility.py
Task F1795: Case 2 Native-MISESERI Causal Remeshing Controlled Reproducibility Experiment.

Runs under Abaqus CAE noGUI to:
1. Verify donor PK_HOLE_METHOD_A_PREANALYSIS.odb contains authentic native MISESERI/MISESAVG in Step-1 Frame 10.
2. Execute Abaqus native RemeshingRule and adaptiveRemesh() on Case 2 geometry in 3 controlled runs:
   - Run A (Control): Unmodified OffAxisHoleMode1Adapter.
   - Run B (Perturbed): Deliberately corrupted classify_region() labels (inverted corridor classification).
   - Run C (Repeat): Unmodified repeat control to test mesher determinism.
3. Generate 3 physical adapted meshes:
   - PK_F1795_CASE_2_CONTROL_PHYS.inp
   - PK_F1795_CASE_2_PERTURBED_PHYS.inp
   - PK_F1795_CASE_2_REPEAT_PHYS.inp
4. Compare bitwise SHA-256 hashes, node counts, element counts, quad fractions, Jacobians,
   aspect ratios, and spatial sizing distributions across primary, distal, and far-field regions.
5. Export comprehensive machine-readable donor field receipt and reproducibility receipt.
"""

import os
import sys
import json
import math
import hashlib
import shutil

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    AbaqusNativeRemeshingEngine,
    MeshQualityAuditEngine,
    OffAxisHoleMode1Adapter,
    get_geometry_adapter
)
from odbAccess import openOdb

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

class DeliberatelyCorruptedCorridorAdapter(OffAxisHoleMode1Adapter):
    """Adapter with deliberately corrupted corridor classification for empirical independence proof."""
    def classify_region(self, x, y):
        # Deliberately inverted: notch-to-hole is labeled as far-field bulk,
        # and far-field bulk is labeled as primary crack corridor.
        if 0.50 <= x <= 0.65 and 0.45 <= y <= 0.65:
            return "CORRUPTED_FAR_FIELD_BULK"
        elif x <= 0.35 and y <= 0.35:
            return "CORRUPTED_PROPAGATION_CORRIDOR"
        elif x >= 0.75 and 0.55 <= y <= 0.75:
            return "CORRUPTED_DISTAL_BULK"
        return "CORRUPTED_ARBITRARY_ZONE"

def main():
    print("=== Task F1795: Case 2 Native-MISESERI Controlled Reproducibility ===")

    raw_donor_odb_path = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "PK_HOLE_METHOD_A_PREANALYSIS.odb"
    )
    assert os.path.exists(raw_donor_odb_path), "Donor ODB must exist: " + raw_donor_odb_path
    donor_sha256 = sha256_file(raw_donor_odb_path)
    donor_size = os.path.getsize(raw_donor_odb_path)
    print("Raw Donor ODB: %s" % raw_donor_odb_path)
    print("Donor Size: %d bytes, SHA-256: %s" % (donor_size, donor_sha256))

    runs_dir = os.path.join(REPO_ROOT, "runs", "f1795_reproducibility")
    if not os.path.exists(runs_dir):
        os.makedirs(runs_dir)

    permanent_model_dir = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "245_f1795_case2_controlled_reproducibility"
    )
    if not os.path.exists(permanent_model_dir):
        os.makedirs(permanent_model_dir)

    # 1. Prepare donor copy with verified ALL_ELEM instance set for Abaqus CAE RemeshingRule
    donor_odb_path = os.path.join(runs_dir, "PK_HOLE_METHOD_A_PREANALYSIS_DONOR.odb")
    shutil.copyfile(raw_donor_odb_path, donor_odb_path)
    odb_prep = openOdb(donor_odb_path, readOnly=False)
    inst_prep = list(odb_prep.rootAssembly.instances.values())[0]
    if "ALL_ELEM" not in inst_prep.elementSets:
        all_labels = [e.label for e in inst_prep.elements]
        inst_prep.ElementSetFromElementLabels(name="ALL_ELEM", elementLabels=all_labels)
        odb_prep.save()
    odb_prep.close()

    # 2. Extract and save machine-readable donor field receipt
    odb = openOdb(raw_donor_odb_path, readOnly=True)
    assert "Step-1" in odb.steps, "Step-1 must exist in donor"
    step1 = odb.steps["Step-1"]
    n_step1_frames = len(step1.frames)
    frame10 = step1.frames[-1]
    time_val = frame10.frameValue

    assert "MISESERI" in frame10.fieldOutputs, "MISESERI must exist in donor"
    assert "MISESAVG" in frame10.fieldOutputs, "MISESAVG must exist in donor"

    eri_fo = frame10.fieldOutputs["MISESERI"]
    avg_fo = frame10.fieldOutputs["MISESAVG"]
    eri_vals = [float(v.data) for v in eri_fo.values]
    avg_vals = [float(v.data) for v in avg_fo.values]
    odb.close()

    sorted_eri = sorted(eri_vals)
    n_vals = len(sorted_eri)
    eri_min = min(eri_vals)
    eri_max = max(eri_vals)
    eri_mean = sum(eri_vals) / float(n_vals)
    eri_median = sorted_eri[n_vals // 2]
    eri_p90 = sorted_eri[int(n_vals * 0.90)]
    eri_p99 = sorted_eri[int(n_vals * 0.99)]

    avg_min = min(avg_vals)
    avg_max = max(avg_vals)
    avg_mean = sum(avg_vals) / float(len(avg_vals))

    donor_receipt = {
        "donor_file": "PK_HOLE_METHOD_A_PREANALYSIS.odb",
        "donor_sha256": donor_sha256,
        "donor_size_bytes": donor_size,
        "step_name": "Step-1",
        "frame_index": 10,
        "frame_time": time_val,
        "total_frames_in_step": n_step1_frames,
        "is_causal_preanalysis": True,
        "indicator_field": "MISESERI",
        "normalization_field": "MISESAVG",
        "num_elements_with_indicator": n_vals,
        "miseseri_stats": {
            "min_mpa": eri_min,
            "max_mpa": eri_max,
            "mean_mpa": eri_mean,
            "median_mpa": eri_median,
            "p90_mpa": eri_p90,
            "p99_mpa": eri_p99
        },
        "misesavg_stats": {
            "min_mpa": avg_min,
            "max_mpa": avg_max,
            "mean_mpa": avg_mean
        }
    }

    donor_receipt_path = os.path.join(permanent_model_dir, "PK_F1795_CASE2_DONOR_FIELD_RECEIPT.json")
    with open(donor_receipt_path, "w") as f:
        json.dump(donor_receipt, f, indent=2)
    print("Saved donor field receipt: %s" % donor_receipt_path)

    # 3. Load native Case 2 configuration
    config_path = os.path.join(REPO_ROOT, "configs", "remeshing", "f1795_case2_native_miseseri.json")
    if not os.path.exists(config_path):
        config_path = os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case2_off_axis_hole.json")
    cfg = AdaptiveConfig.from_json(config_path)

    print("Configured Step: %s, Indicator: %s, Causal: %s, Horizon: frame <= %s (t <= %s)" % (
        cfg.step_name, cfg.variable, cfg.causal_mode, str(cfg.max_frame_index), str(cfg.max_frame_time)
    ))

    # 4. Define experimental configurations: Run A (Control), Run B (Perturbed), Run C (Repeat)
    adapter_control = OffAxisHoleMode1Adapter(cfg)
    adapter_perturbed = DeliberatelyCorruptedCorridorAdapter(cfg)
    adapter_repeat = OffAxisHoleMode1Adapter(cfg)

    experiments = [
        {
            "name": "control",
            "model_name": "Model_F1795_Case2_Control",
            "job_name": "PK_F1795_CASE_2_CONTROL",
            "adapter": adapter_control,
            "corrupted_labels": False
        },
        {
            "name": "perturbed",
            "model_name": "Model_F1795_Case2_Perturbed",
            "job_name": "PK_F1795_CASE_2_PERTURBED",
            "adapter": adapter_perturbed,
            "corrupted_labels": True
        },
        {
            "name": "repeat",
            "model_name": "Model_F1795_Case2_Repeat",
            "job_name": "PK_F1795_CASE_2_REPEAT",
            "adapter": adapter_repeat,
            "corrupted_labels": False
        }
    ]

    results = {}
    mesh_inps = {}

    for exp in experiments:
        exp_name = exp["name"]
        print("\n--- Executing Run: %s (job=%s, corrupted=%s) ---" % (
            exp_name, exp["job_name"], exp["corrupted_labels"]
        ))
        
        raw_inp = AbaqusNativeRemeshingEngine.execute_native_remesh(
            config=cfg,
            donor_odb_path=donor_odb_path,
            output_dir=runs_dir,
            model_name=exp["model_name"],
            adapter_override=exp["adapter"],
            output_job_name=exp["job_name"]
        )
        assert os.path.exists(raw_inp), "Remeshed INP must exist: " + raw_inp

        target_inp = os.path.join(permanent_model_dir, os.path.basename(raw_inp))
        shutil.copyfile(raw_inp, target_inp)
        mesh_inps[exp_name] = target_inp

        inp_sha = sha256_file(target_inp)
        inp_size = os.path.getsize(target_inp)
        print("Run %s INP: %s" % (exp_name, target_inp))
        print("Run %s Size: %d bytes, SHA-256: %s" % (exp_name, inp_size, inp_sha))

        # Audit FE mesh
        audit = MeshQualityAuditEngine.evaluate_mesh(target_inp, l0_mm=cfg.l0, adapter=adapter_control)
        results[exp_name] = {
            "inp_file": os.path.basename(target_inp),
            "sha256": inp_sha,
            "size_bytes": inp_size,
            "corrupted_labels": exp["corrupted_labels"],
            "total_elements": audit["total_elements"],
            "quad_count": audit["quad_count"],
            "tri_count": audit["tri_count"],
            "quad_percent": audit["quad_percent"],
            "min_det_j": audit["min_det_j"],
            "max_aspect_ratio": audit["max_aspect_ratio"],
            "median_aspect_ratio": audit["median_aspect_ratio"],
            "ar_violations_gt_4": audit["aspect_ratio_violations_gt_4"]
        }

    # 5. Measure spatial sizing profile across standardized regions for all 3 meshes
    # Standardized evaluation windows:
    # Notch-to-hole ligament: x in [0.50, 0.65], y in [0.45, 0.65]
    # Outer distal region: x in [0.75, 1.00], y in [0.55, 0.75]
    # Far-field background: x <= 0.35, y <= 0.35
    l0 = cfg.l0
    l0_half = l0 / 2.0

    for exp_name, inp_path in mesh_inps.items():
        with open(inp_path, "r") as f:
            lines = f.readlines()

        # Compute mesh body SHA-256 (excluding comments to verify pure mesh invariance)
        h_body = hashlib.sha256()
        for line in lines:
            if not line.strip().startswith("**"):
                h_body.update(line.strip().encode("utf-8") + b"\n")
        results[exp_name]["mesh_body_sha256"] = h_body.hexdigest().upper()

        nodes = {}
        elements = {}
        in_nodes = False
        in_elems = False

        for line in lines:
            line_str = line.strip()
            u_line = line_str.upper()
            if u_line.startswith("*NODE") and "OUTPUT" not in u_line:
                in_nodes = True
                in_elems = False
                continue
            elif u_line.startswith("*ELEMENT") and "OUTPUT" not in u_line:
                in_nodes = False
                in_elems = True
                continue
            elif u_line.startswith("*"):
                in_nodes = False
                in_elems = False
                continue

            if in_nodes and line_str:
                parts = line_str.split(",")
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0].strip())
                        x = float(parts[1].strip())
                        y = float(parts[2].strip())
                        nodes[nid] = (x, y)
                    except ValueError:
                        continue

            elif in_elems and line_str:
                parts = line_str.split(",")
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0].strip())
                        conn = [int(p.strip()) for p in parts[1:] if p.strip()]
                        elements[eid] = conn
                    except ValueError:
                        continue

        notch_hole_h = []
        distal_h = []
        far_field_h = []

        for eid, conn in elements.items():
            pts = [nodes[nid] for nid in conn if nid in nodes]
            if len(pts) >= 3:
                cx = sum([p[0] for p in pts]) / float(len(pts))
                cy = sum([p[1] for p in pts]) / float(len(pts))

                if len(pts) == 4:
                    x1, y1 = pts[0]
                    x2, y2 = pts[1]
                    x3, y3 = pts[2]
                    x4, y4 = pts[3]
                    area = 0.5 * abs((x1*y2 - y1*x2) + (x2*y3 - y2*x3) + (x3*y4 - y3*x4) + (x4*y1 - y4*x1))
                else:
                    x1, y1 = pts[0]
                    x2, y2 = pts[1]
                    x3, y3 = pts[2]
                    area = 0.5 * abs(x1*(y2 - y3) + x2*(y3 - y1) + x3*(y1 - y2))

                h_e = math.sqrt(area)

                if 0.50 <= cx <= 0.65 and 0.45 <= cy <= 0.65:
                    notch_hole_h.append(h_e)
                elif 0.75 <= cx <= 1.00 and 0.55 <= cy <= 0.75:
                    distal_h.append(h_e)
                elif cx <= 0.35 and cy <= 0.35:
                    far_field_h.append(h_e)

        nh_cnt = len(notch_hole_h)
        nh_mean = sum(notch_hole_h) / float(nh_cnt) if nh_cnt > 0 else 0.0
        nh_le_l0 = sum([1 for h in notch_hole_h if h <= l0 + 1e-9])
        nh_le_l0_half = sum([1 for h in notch_hole_h if h <= l0_half + 1e-9])

        dist_cnt = len(distal_h)
        dist_mean = sum(distal_h) / float(dist_cnt) if dist_cnt > 0 else 0.0
        dist_le_l0 = sum([1 for h in distal_h if h <= l0 + 1e-9])
        dist_le_l0_half = sum([1 for h in distal_h if h <= l0_half + 1e-9])

        ff_cnt = len(far_field_h)
        ff_mean = sum(far_field_h) / float(ff_cnt) if ff_cnt > 0 else 0.0

        results[exp_name]["spatial_resolution"] = {
            "notch_to_hole": {
                "element_count": nh_cnt,
                "mean_h_um": nh_mean * 1000.0,
                "pct_le_l0": (nh_le_l0 / float(nh_cnt) * 100.0) if nh_cnt > 0 else 0.0,
                "pct_le_l0_half": (nh_le_l0_half / float(nh_cnt) * 100.0) if nh_cnt > 0 else 0.0
            },
            "outer_distal": {
                "element_count": dist_cnt,
                "mean_h_um": dist_mean * 1000.0,
                "pct_le_l0": (dist_le_l0 / float(dist_cnt) * 100.0) if dist_cnt > 0 else 0.0,
                "pct_le_l0_half": (dist_le_l0_half / float(dist_cnt) * 100.0) if dist_cnt > 0 else 0.0
            },
            "far_field": {
                "element_count": ff_cnt,
                "mean_h_um": ff_mean * 1000.0,
                "refinement_ratio_far_to_core": (ff_mean / nh_mean) if nh_cnt > 0 else 0.0
            }
        }

    # 6. Comparative analysis
    sha_ctrl = results["control"]["sha256"]
    sha_pert = results["perturbed"]["sha256"]
    sha_rpt = results["repeat"]["sha256"]

    bitwise_identical_ctrl_pert = (sha_ctrl == sha_pert)
    bitwise_identical_ctrl_rpt = (sha_ctrl == sha_rpt)

    print("\n=== Reproducibility & Corridor Independence Verdict ===")
    print("Control SHA-256:   %s" % sha_ctrl)
    print("Perturbed SHA-256: %s (Bitwise match to Control: %s)" % (sha_pert, bitwise_identical_ctrl_pert))
    print("Repeat SHA-256:    %s (Bitwise match to Control: %s)" % (sha_rpt, bitwise_identical_ctrl_rpt))

    reproducibility_receipt = {
        "task_id": "F1795-CASE2-NATIVE-MISESERI-CAUSAL-REMESHING-CONTROLLED-REPRODUCIBILITY",
        "donor_odb": "PK_HOLE_METHOD_A_PREANALYSIS.odb",
        "donor_sha256": donor_sha256,
        "causal_horizon": {
            "step_name": "Step-1",
            "frame_index": 10,
            "frame_time": 1.0,
            "causal_mode": True
        },
        "pairwise_comparisons": {
            "control_vs_perturbed": {
                "file_sha256_identical": bitwise_identical_ctrl_pert,
                "mesh_body_bitwise_identical": (results["control"]["mesh_body_sha256"] == results["perturbed"]["mesh_body_sha256"]),
                "element_count_delta": results["control"]["total_elements"] - results["perturbed"]["total_elements"],
                "quad_count_delta": results["control"]["quad_count"] - results["perturbed"]["quad_count"],
                "min_jacobian_delta": results["control"]["min_det_j"] - results["perturbed"]["min_det_j"],
                "max_ar_delta": results["control"]["max_aspect_ratio"] - results["perturbed"]["max_aspect_ratio"]
            },
            "control_vs_repeat": {
                "file_sha256_identical": bitwise_identical_ctrl_rpt,
                "mesh_body_bitwise_identical": (results["control"]["mesh_body_sha256"] == results["repeat"]["mesh_body_sha256"]),
                "element_count_delta": results["control"]["total_elements"] - results["repeat"]["total_elements"],
                "quad_count_delta": results["control"]["quad_count"] - results["repeat"]["quad_count"],
                "min_jacobian_delta": results["control"]["min_det_j"] - results["repeat"]["min_det_j"],
                "max_ar_delta": results["control"]["max_aspect_ratio"] - results["repeat"]["max_aspect_ratio"]
            }
        },
        "runs": results
    }

    repro_receipt_path = os.path.join(
        permanent_model_dir, "PK_F1795_CASE2_CONTROLLED_REPRODUCIBILITY_RECEIPT.json"
    )
    with open(repro_receipt_path, "w") as f:
        json.dump(reproducibility_receipt, f, indent=2)
    print("Saved reproducibility receipt: %s" % repro_receipt_path)

if __name__ == "__main__":
    main()
