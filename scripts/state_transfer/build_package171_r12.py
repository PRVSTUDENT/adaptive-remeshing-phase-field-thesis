#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/state_transfer/build_package171_r12.py
Task: F1628-METHOD-C-ISOPARAMETRIC-C6-ADAPTIVE-REEQUILIBRATION
Protocol Version: 2

Assembles Package 171 Revision 12 (C6 nonmatching adaptive remeshed receiver):
1. Loads C5 donor mesh (12,996 CPE4 quads) and Checkpoint 03 (Job 1419566).
2. Loads C6 receiver mesh (15,252 CPE4 quads, 15,559 physical nodes).
3. Executes gradient-preserving isoparametric bilinear GP history transfer.
4. Generates initial_conditions_solution.inc with intra-element varying history.
5. Performs quantitative comparison against original element-averaged history:
   - Max/mean/RMS differences across all 61,008 Gauss points
   - Near-tip gradient characterization (r <= 0.01 mm of tip x=0.04, y=0.05)
   - Extrapolation, clamping, and thermodynamic admissibility verification
   - Exports results/validation/c6_isoparametric_vs_averaged_history_comparison.json
6. Staged decks and manifests for zero-PBS Abaqus datachecks.
"""

from __future__ import print_function, division
import os
import sys
import math
import json
import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.c4_to_c5_spatial_mapping import Mesh2D
from scripts.state_transfer.isoparametric_gp_transfer import transfer_isoparametric_gp_history

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
SLIT_TIP_X = 0.040
SLIT_TIP_Y = 0.050


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def parse_solution_inc(inc_path: Path) -> Dict[int, List[float]]:
    """Parses initial_conditions_solution.inc returning eid -> [H1, H2, H3, H4]."""
    history_by_elem: Dict[int, List[float]] = {}
    with open(inc_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("*"):
            i += 1
            continue
        # Format in UEL:
        # line i:   eid, 0, 0, 0, 0, 0, 0, 0
        # line i+1: 0, H1, H2, H3, H4, 0, 0, 0
        # line i+2: 0, 0, 0
        parts0 = [p.strip() for p in line.split(",") if p.strip()]
        if len(parts0) >= 1 and parts0[0].isdigit():
            eid = int(parts0[0])
            if i + 1 < len(lines):
                parts1 = [p.strip() for p in lines[i+1].split(",") if p.strip()]
                if len(parts1) >= 5:
                    h1 = float(parts1[1])
                    h2 = float(parts1[2])
                    h3 = float(parts1[3])
                    h4 = float(parts1[4])
                    history_by_elem[eid] = [h1, h2, h3, h4]
            i += 3
        else:
            i += 1
    return history_by_elem


def format_solution_inc(history_by_elem: Dict[int, List[float]]) -> str:
    """Formats initial_conditions_solution.inc for Abaqus UEL."""
    out = ["*Initial Conditions, type=SOLUTION"]
    for eid in sorted(history_by_elem.keys()):
        h1, h2, h3, h4 = history_by_elem[eid]
        out.append(f"{eid}, 0, 0, 0, 0, 0, 0, 0")
        out.append(f"0, {h1:.17e}, {h2:.17e}, {h3:.17e}, {h4:.17e}, 0, 0, 0")
        out.append("0, 0, 0")
    return "\n".join(out) + "\n"


def main():
    pkg_r11_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "171_c6_package171_r11_c3_0_adaptive_reequilibration"
    pkg_r12_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "171_c6_package171_r12_c3_0_adaptive_reequilibration"
    pkg_r12_dir.mkdir(parents=True, exist_ok=True)

    c5_inp = REPO_ROOT / "models" / "pandey_kumar_mode1" / "172_c5_same_mesh_old_control" / "P172_MECHANICAL_DC.inp"
    cp03_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "167_c5_package167_r3_c2_2_continuation" / "evidence" / "1419566.mmaster02" / "converged_checkpoint_03.json"
    c6_inp = pkg_r11_dir / "P171_MECHANICAL_DC.inp"

    print("=== Step 1: Loading Meshes & Checkpoint 03 ===")
    m_c5 = Mesh2D.from_inp(c5_inp, name="C5_Donor", max_physical_node=13278)
    m_c6 = Mesh2D.from_inp(c6_inp, name="C6_Receiver", max_physical_node=15559)

    with open(cp03_path, "r", encoding="utf-8") as f:
        cp03 = json.load(f)

    donor_history_dict = {
        (int(rec[0]), int(rec[1])): float(rec[2])
        for rec in cp03["history"]
    }
    print(f"Loaded C5 donor mesh: {len(m_c5.elements)} elements, {len(m_c5.nodes)} nodes")
    print(f"Loaded C6 receiver mesh: {len(m_c6.elements)} elements, {len(m_c6.nodes)} nodes")
    print(f"Loaded C5 CP03 history: {len(donor_history_dict)} GP records, range [{min(donor_history_dict.values()):.4e}, {max(donor_history_dict.values()):.4e}] MPa")

    print("\n=== Step 2: Executing Isoparametric Bilinear GP Transfer ===")
    donor_mesh_dict = {"nodes": m_c5.nodes, "elements": m_c5.elements}
    receiver_mesh_dict = {
        "nodes": m_c6.nodes,
        "elements": m_c6.elements,
        "coincident_slit_pairs": [(p[0], p[1]) for p in m_c6.seam_pairs]
    }

    transfer_res = transfer_isoparametric_gp_history(
        donor_mesh=donor_mesh_dict,
        donor_history_dict=donor_history_dict,
        receiver_mesh=receiver_mesh_dict,
        limiter_mode="convex_clamp",
        slit_y=SLIT_TIP_Y,
        slit_a0=SLIT_TIP_X,
        bin_size=0.005
    )
    isoparametric_history = transfer_res["transferred_history"]
    print(f"Isoparametric transfer complete: {len(isoparametric_history)} elements, {len(isoparametric_history)*4} GPs")

    print("\n=== Step 3: Loading Original Element-Averaged C6 History ===")
    orig_inc_path = pkg_r11_dir / "initial_conditions_solution.inc"
    original_history = parse_solution_inc(orig_inc_path)
    print(f"Loaded original C6 history: {len(original_history)} elements")

    print("\n=== Step 4: Quantitative Comparison (Isoparametric vs Averaged) ===")
    diffs = []
    diffs_near_tip = []
    tip_radius = 0.010  # 10 um radius around crack tip

    non_uniform_elems = 0
    for eid in sorted(m_c6.elements.keys()):
        iso_vals = isoparametric_history[eid]
        orig_vals = original_history[eid]

        # Check intra-element variation in isoparametric
        if max(iso_vals) - min(iso_vals) > 1e-6:
            non_uniform_elems += 1

        # Element centroid distance to crack tip
        cx = sum(m_c6.nodes[n][0] for n in m_c6.elements[eid]) / 4.0
        cy = sum(m_c6.nodes[n][1] for n in m_c6.elements[eid]) / 4.0
        dist_to_tip = math.sqrt((cx - SLIT_TIP_X)**2 + (cy - SLIT_TIP_Y)**2)

        for g in range(4):
            d = abs(iso_vals[g] - orig_vals[g])
            diffs.append(d)
            if dist_to_tip <= tip_radius:
                diffs_near_tip.append(d)

    max_diff = max(diffs)
    mean_diff = sum(diffs) / len(diffs)
    rms_diff = math.sqrt(sum(d**2 for d in diffs) / len(diffs))

    max_diff_tip = max(diffs_near_tip) if diffs_near_tip else 0.0
    mean_diff_tip = sum(diffs_near_tip) / len(diffs_near_tip) if diffs_near_tip else 0.0

    all_iso_vals = [v for vals in isoparametric_history.values() for v in vals]
    all_orig_vals = [v for vals in original_history.values() for v in vals]

    comparison_summary = {
        "schema": 1,
        "task_id": "F1628-METHOD-C-ISOPARAMETRIC-C6-ADAPTIVE-REEQUILIBRATION",
        "donor_source": {
            "checkpoint": "converged_checkpoint_03.json",
            "job_id": "1419566.mmaster02",
            "elements": len(m_c5.elements),
            "gp_count": len(donor_history_dict)
        },
        "receiver_mesh": {
            "name": "C6_Receiver",
            "elements": len(m_c6.elements),
            "physical_nodes": len(m_c6.nodes),
            "gp_count": len(all_iso_vals)
        },
        "transfer_telemetry": {
            "limiter_mode": "convex_clamp",
            "slit_tip_x_mm": SLIT_TIP_X,
            "slit_tip_y_mm": SLIT_TIP_Y,
            "extrapolation_count": transfer_res["extrapolation_count"],
            "clamped_count": transfer_res["clamped_count"],
            "negative_prevented_count": transfer_res["negative_prevented_count"],
            "max_extrapolation_distance": transfer_res["max_extrapolation_distance"],
            "non_uniform_elements_count": non_uniform_elems,
            "non_uniform_elements_pct": (non_uniform_elems / len(m_c6.elements)) * 100.0
        },
        "history_field_ranges": {
            "original_averaged": {
                "min_MPa": min(all_orig_vals),
                "max_MPa": max(all_orig_vals),
                "sum_MPa": sum(all_orig_vals)
            },
            "corrected_isoparametric": {
                "min_MPa": min(all_iso_vals),
                "max_MPa": max(all_iso_vals),
                "sum_MPa": sum(all_iso_vals)
            }
        },
        "discrepancy_metrics": {
            "whole_domain": {
                "max_absolute_diff_MPa": max_diff,
                "mean_absolute_diff_MPa": mean_diff,
                "rms_diff_MPa": rms_diff
            },
            "near_tip_zone_r_10um": {
                "sample_points_count": len(diffs_near_tip),
                "max_absolute_diff_MPa": max_diff_tip,
                "mean_absolute_diff_MPa": mean_diff_tip
            }
        },
        "thermodynamic_admissibility": {
            "strictly_nonnegative": min(all_iso_vals) >= 0.0,
            "min_history_value": min(all_iso_vals),
            "max_history_value": max(all_iso_vals),
            "finite_values_only": all(math.isfinite(v) for v in all_iso_vals)
        }
    }

    out_json = REPO_ROOT / "results" / "validation" / "c6_isoparametric_vs_averaged_history_comparison.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(comparison_summary, f, indent=2)
    print(f"Comparison written to: {out_json}")
    print(f"Max whole-domain diff: {max_diff:.4f} MPa, RMS diff: {rms_diff:.4f} MPa")
    print(f"Max near-tip diff (r<=10um): {max_diff_tip:.4f} MPa, Mean: {mean_diff_tip:.4f} MPa")
    print(f"Non-uniform elements in C6: {non_uniform_elems}/{len(m_c6.elements)} ({comparison_summary['transfer_telemetry']['non_uniform_elements_pct']:.1f}%)")

    print("\n=== Step 5: Assembling Package 171-R12 Assets ===")
    # 1. Write initial_conditions_solution.inc
    inc_content = format_solution_inc(isoparametric_history)
    (pkg_r12_dir / "initial_conditions_solution.inc").write_text(inc_content, encoding="utf-8")
    print("Wrote initial_conditions_solution.inc")

    # 1b. Write updated d_lower_bounds.csv with synchronized isoparametric history
    r11_bounds = pkg_r11_dir / "d_lower_bounds.csv"
    r12_bounds = pkg_r12_dir / "d_lower_bounds.csv"
    with open(r11_bounds, "r", encoding="utf-8") as f_in, open(r12_bounds, "w", encoding="utf-8") as f_out:
        header = f_in.readline()
        f_out.write(header)
        for line in f_in:
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(",") if p.strip()]
            eid = int(parts[0])
            d0_1, d0_2, d0_3, d0_4 = parts[1], parts[2], parts[3], parts[4]
            h1, h2, h3, h4 = isoparametric_history[eid]
            f_out.write(f"{eid},{d0_1},{d0_2},{d0_3},{d0_4},{h1:.17e},{h2:.17e},{h3:.17e},{h4:.17e}\n")
    print("Wrote synchronized d_lower_bounds.csv")

    # 2. Copy unchanged assets from R11
    copy_files = [
        "active_set_boundary_cards.inc",
        "f42_mixed_uel.for",
        "job_notifications.sh",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "P171_MECHANICAL_DC.inp",
        "P171_PHASE_DC.inp",
        "smoke_import.py"
    ]
    for cf in copy_files:
        src_f = pkg_r11_dir / cf
        if src_f.is_file():
            shutil.copy2(src_f, pkg_r12_dir / cf)

    # Verify frozen UEL
    uel_hash = sha256_file(pkg_r12_dir / "f42_mixed_uel.for")
    assert uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch! Expected {FROZEN_UEL_HASH}, got {uel_hash}"
    print(f"Verified frozen UEL hash: {uel_hash}")

    # 3. Create master deck and PBS script
    master_inp_content = (pkg_r11_dir / "M1_C6_PACKAGE171_R11_C3_0_ADAPTIVE_REEQUILIBRATION.inp").read_text(encoding="utf-8").replace("\r\n", "\n")
    master_inp_content = master_inp_content.replace("R11", "R12").replace("r11", "r12")
    (pkg_r12_dir / "M1_C6_PACKAGE171_R12_C3_0_ADAPTIVE_REEQUILIBRATION.inp").write_bytes(master_inp_content.encode("utf-8"))

    pbs_content = (pkg_r11_dir / "submit_M1_C6_P171_R11_C3_0.pbs").read_text(encoding="utf-8").replace("\r\n", "\n")
    pbs_content = pbs_content.replace("R11", "R12").replace("r11", "r12").replace("    --anderson-enabled \\\n", "")
    pbs_content = pbs_content.replace("Safeguarded Anderson Acceleration", "Gradient-Preserving Isoparametric Bilinear GP Transfer")
    (pkg_r12_dir / "submit_M1_C6_P171_R12_C3_0.pbs").write_bytes(pbs_content.encode("utf-8"))

    # 4. Generate dynamic iteration 1 decks with restored Node Print cards
    # Mechanical deck
    mech_dc_content = (pkg_r12_dir / "P171_MECHANICAL_DC.inp").read_text(encoding="utf-8").replace("\r\n", "\n")
    mech_iter1 = mech_dc_content.replace("*Output, field", "*Node Print, frequency=1\nU\n*Output, field") if "*Node Print" not in mech_dc_content else mech_dc_content
    (pkg_r12_dir / "P171_ITER1_MECH.inp").write_bytes(mech_iter1.encode("utf-8"))

    # Phase deck
    phase_dc_content = (pkg_r12_dir / "P171_PHASE_DC.inp").read_text(encoding="utf-8").replace("\r\n", "\n")
    phase_iter1 = phase_dc_content.replace("*Output, field", "*Node Print, frequency=1\nU\n*Output, field") if "*Node Print" not in phase_dc_content else phase_dc_content
    (pkg_r12_dir / "P171_ITER1_PHASE.inp").write_bytes(phase_iter1.encode("utf-8"))

    # 5. Create run_datacheck.sh
    run_dc_sh = """#!/usr/bin/env bash
set -euo pipefail

echo "Running Abaqus 2023 Mechanical Datacheck on Package 171-R12..."
abaqus 2023 job=P171_MECHANICAL_DC input=P171_MECHANICAL_DC.inp datacheck interactive -standard_parallel all -cpus 1 memory="16gb"

echo "Running Abaqus 2023 Phase Datacheck on Package 171-R12..."
abaqus 2023 job=P171_PHASE_DC input=P171_PHASE_DC.inp user=f42_mixed_uel.for datacheck interactive -standard_parallel all -cpus 1 memory="16gb"

echo "Running Dynamic Iteration 1 Mechanical Datacheck..."
abaqus 2023 job=P171_ITER1_MECH input=P171_ITER1_MECH.inp datacheck interactive -standard_parallel all -cpus 1 memory="16gb"

echo "Running Dynamic Iteration 1 Phase Datacheck..."
abaqus 2023 job=P171_ITER1_PHASE input=P171_ITER1_PHASE.inp user=f42_mixed_uel.for datacheck interactive -standard_parallel all -cpus 1 memory="16gb"

echo "All 4 Package 171-R12 Datachecks Completed Successfully!"
"""
    (pkg_r12_dir / "run_datacheck.sh").write_text(run_dc_sh, encoding="utf-8")

    # 6. Generate PACKAGE_MANIFEST.json
    manifest_files = {}
    for fpath in sorted(pkg_r12_dir.glob("*")):
        if fpath.is_file() and fpath.name != "PACKAGE_MANIFEST.json":
            manifest_files[fpath.name] = {
                "sha256": sha256_file(fpath),
                "size_bytes": fpath.stat().st_size
            }

    pkg_manifest = {
        "schema": 1,
        "package_id": "package171_r12_c3_0_adaptive_reequilibration",
        "model": "pandey_kumar_mode1",
        "description": "Package 171 Revision 12: C6 nonmatching receiver re-equilibration with gradient-preserving isoparametric bilinear GP history transfer",
        "files_count": len(manifest_files),
        "files": manifest_files
    }
    with open(pkg_r12_dir / "PACKAGE_MANIFEST.json", "w", encoding="utf-8") as f:
        json.dump(pkg_manifest, f, indent=2)

    print(f"\nPackage 171-R12 assembled successfully at {pkg_r12_dir} ({len(manifest_files)} registered files).")


if __name__ == "__main__":
    main()
