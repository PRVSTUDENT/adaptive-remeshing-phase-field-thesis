#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_same_mesh_control_packages.py
===================================
Constructs the paired same-mesh Abaqus control experiment packages:
- Package 172: Arm 1 (Control Old - Element-Averaged GP History, ~6.35 MPa perturbation)
- Package 173: Arm 2 (Control Corrected - Hardened Isoparametric GP History, < 1e-12 MPa error)

Task: F1622-METHOD-C-SAME-MESH-ABAQUS-CONTROL-STAGING
Protocol Version: 2

Pre-Staging Verification:
1. Identical C5 mesh topology (12,996 quads, 13,278 physical nodes + RP 999999).
2. Identical nodal displacement, damage, boundary conditions, and lower bounds from accepted Checkpoint 03 (Job 1419566).
3. Frozen UEL bit-for-bit identical (SHA-256 CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6).
4. Equal coupled convergence criteria, two-phase adaptive relaxation (w_d=0.5/0.85, w_u=1.0/0.85), Anderson acceleration DISABLED.
5. Decks differ strictly in transferred GP history and necessary job/output names.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path
from collections import defaultdict
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.remeshing.c5_to_c6_adaptive_integration import load_c5_mesh
from scripts.state_transfer.isoparametric_gp_transfer import (
    transfer_isoparametric_gp_history,
    QUAD_GP_LOCAL,
    Q_GAUSS
)

C5_SOURCE_DIR = REPO_ROOT / "models/pandey_kumar_mode1/167_c5_package167_r3_c2_2_continuation"
C5_CP03_PATH = C5_SOURCE_DIR / "evidence/1419566.mmaster02/converged_checkpoint_03.json"
FROZEN_UEL_PATH = C5_SOURCE_DIR / "f42_mixed_uel.for"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

PKG172_DIR = REPO_ROOT / "models/pandey_kumar_mode1/172_c5_same_mesh_old_control"
PKG173_DIR = REPO_ROOT / "models/pandey_kumar_mode1/173_c5_same_mesh_corrected_control"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def build_same_mesh_control_packages():
    print("=" * 80)
    print("BUILDING PAIRED SAME-MESH ABAQUS CONTROL PACKAGES (TASK F1622)")
    print("=" * 80)

    # 1. Verify frozen production UEL
    uel_hash = sha256_file(FROZEN_UEL_PATH)
    assert uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch: {uel_hash} != {FROZEN_UEL_HASH}"
    print(f"\n1. Verified frozen production UEL: {uel_hash}")

    # 2. Load C5 Donor Checkpoint 03
    print(f"\n2. Loading accepted C5 Checkpoint 03 from {C5_CP03_PATH.name}...")
    with open(C5_CP03_PATH, "r", encoding="utf-8") as f:
        cp03 = json.load(f)

    target_uy = float(cp03["target_uy_mm"])
    ref_rf = float(cp03["reaction_force_kN"])
    ref_energy = float(cp03["total_energy_kNmm"])
    print(f"Donor Checkpoint 03: target_uy = {target_uy:.10f} mm, RF = {ref_rf:.6f} kN, Energy = {ref_energy:.6e} kNmm")

    donor_history_dict = {}
    for item in cp03["history"]:
        eid = int(item[0])
        gp = int(item[1])
        h_val = float(item[2])
        donor_history_dict[(eid, gp)] = h_val

    assert len(donor_history_dict) == 12996 * 4 == 51984
    donor_peak_H = max(donor_history_dict.values())
    donor_min_H = min(donor_history_dict.values())
    print(f"Donor history records: {len(donor_history_dict)} GPs, peak = {donor_peak_H:.4f} MPa, min = {donor_min_H:.6f} MPa")

    # 3. Load C5 Mesh
    print("\n3. Loading C5 mesh structure...")
    c5_mesh = load_c5_mesh()
    c5_nodes = c5_mesh["nodes"]
    c5_quads = c5_mesh["quads"]
    assert len(c5_quads) == 12996
    assert len(c5_nodes) == 13279  # 13,278 physical + RP 999999

    # Slit pairs
    upper_nodes = set()
    for eid, conn in c5_quads.items():
        cy = sum(c5_nodes[n][1] for n in conn) / 4.0
        if cy > 0.050:
            upper_nodes.update(conn)

    slit_dict = defaultdict(list)
    for nid, (x, y) in c5_nodes.items():
        if abs(y - 0.050) < 1e-6 and x <= 0.040 + 1e-6 and nid != 999999:
            slit_dict[round(x, 7)].append(nid)

    c5_slit_pairs = []
    for x_val, nids in sorted(slit_dict.items()):
        if len(nids) == 2:
            n_lower = min(nids, key=lambda n: n in upper_nodes)
            n_upper = max(nids, key=lambda n: n in upper_nodes)
            c5_slit_pairs.append((n_lower, n_upper, x_val))

    c5_mesh["coincident_slit_pairs"] = c5_slit_pairs
    print(f"C5 mesh: 12,996 quads, 13,278 physical nodes + RP 999999, {len(c5_slit_pairs)} slit pairs.")

    # 4. Generate Arm 1: Control Old (Element-Averaged GP History)
    print("\n4. Generating Arm 1 (Control Old: Element-Averaged History)...")
    old_history_dict = {}
    for eid in sorted(c5_quads.keys()):
        h_donor = [donor_history_dict[(eid, g)] for g in range(1, 5)]
        h_mean = sum(h_donor) / 4.0
        for g in range(1, 5):
            old_history_dict[(eid, g)] = h_mean

    old_diffs = [abs(old_history_dict[k] - donor_history_dict[k]) for k in donor_history_dict]
    max_err_old = max(old_diffs)
    rms_err_old = math.sqrt(sum(d**2 for d in old_diffs) / len(old_diffs))
    print(f"Arm 1 (Control Old) History Perturbation:")
    print(f"  Max |Delta H| = {max_err_old:.4f} MPa (expected ~6.3491 MPa)")
    print(f"  RMS |Delta H| = {rms_err_old:.4f} MPa (expected ~0.0681 MPa)")
    assert abs(max_err_old - 6.3491) < 0.01

    # 5. Generate Arm 2: Control Corrected (Hardened Isoparametric Bilinear GP History)
    print("\n5. Generating Arm 2 (Control Corrected: Hardened Isoparametric History)...")
    cand_res = transfer_isoparametric_gp_history(
        c5_mesh, donor_history_dict, c5_mesh, limiter_mode="convex_clamp", bypass_same_mesh_shortcut=True
    )
    corr_history_dict = cand_res["transferred_history_dict"]
    corr_diffs = [abs(corr_history_dict[k] - donor_history_dict[k]) for k in donor_history_dict]
    max_err_corr = max(corr_diffs)
    rms_err_corr = math.sqrt(sum(d**2 for d in corr_diffs) / len(corr_diffs))
    print(f"Arm 2 (Control Corrected) History Perturbation:")
    print(f"  Max |Delta H| = {max_err_corr:.4e} MPa (tolerance <= 1.0e-12 MPa) -> {'PASS' if max_err_corr <= 1e-12 else 'FAIL'}")
    print(f"  RMS |Delta H| = {rms_err_corr:.4e} MPa")
    assert max_err_corr <= 1e-12

    # 6. Write initial_conditions_solution.inc for both arms
    def write_initial_conditions_solution(filepath: Path, history_map: dict):
        with open(filepath, "w", encoding="utf-8") as f:
            for eid in sorted(c5_quads.keys()):
                h1 = history_map[(eid, 1)]
                h2 = history_map[(eid, 2)]
                h3 = history_map[(eid, 3)]
                h4 = history_map[(eid, 4)]
                f.write(f"{eid}, 0, 0, 0, 0, 0, 0, 0\n")
                f.write(f"0, {h1:.18e}, {h2:.18e}, {h3:.18e}, {h4:.18e}, 0, 0, 0\n")
                f.write("0, 0, 0\n")

    # Clean / prepare output directories
    PKG172_DIR.mkdir(parents=True, exist_ok=True)
    PKG173_DIR.mkdir(parents=True, exist_ok=True)

    inc172_path = PKG172_DIR / "initial_conditions_solution.inc"
    inc173_path = PKG173_DIR / "initial_conditions_solution.inc"
    write_initial_conditions_solution(inc172_path, old_history_dict)
    write_initial_conditions_solution(inc173_path, corr_history_dict)
    print(f"Written {inc172_path.name} for Package 172 ({inc172_path.stat().st_size} bytes)")
    print(f"Written {inc173_path.name} for Package 173 ({inc173_path.stat().st_size} bytes)")

    # 7. Write d_lower_bounds.csv specifically for each arm
    # Read element nodal damages from C5 Package 167 d_lower_bounds.csv
    elem_nodal_d = {}
    with open(C5_SOURCE_DIR / "d_lower_bounds.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for r in reader:
            if r:
                eid = int(r[0])
                elem_nodal_d[eid] = [r[1], r[2], r[3], r[4]]

    def write_d_lower_bounds(output_path: Path, history_dict: dict):
        with open(output_path, "w", encoding="utf-8", newline="\n") as f:
            writer = csv.writer(f)
            writer.writerow(["element_id", "d_node1", "d_node2", "d_node3", "d_node4", "h_gp1", "h_gp2", "h_gp3", "h_gp4"])
            for eid in sorted(c5_quads.keys()):
                d_nodes = elem_nodal_d[eid]
                h_vals = [f"{history_dict[(eid, g)]:.18e}" for g in range(1, 5)]
                writer.writerow([eid] + d_nodes + h_vals)

    write_d_lower_bounds(PKG172_DIR / "d_lower_bounds.csv", old_history_dict)
    write_d_lower_bounds(PKG173_DIR / "d_lower_bounds.csv", corr_history_dict)
    print(f"Written tailored d_lower_bounds.csv for Package 172 and Package 173")

    # 8. Copy common shared assets from Package 167
    common_files = [
        "active_set_boundary_cards.inc",
        "nodal_displacements_initial.csv",
        "nodal_phase_field_initial.csv",
        "job_notifications.sh"
    ]
    for fn in common_files:
        src = C5_SOURCE_DIR / fn
        assert src.is_file(), f"Missing source file: {src}"
        shutil.copy2(src, PKG172_DIR / fn)
        shutil.copy2(src, PKG173_DIR / fn)

    # Copy driver_same_mesh_control_pdas.py
    driver_src = REPO_ROOT / "scripts/state_transfer/driver_same_mesh_control_pdas.py"
    if driver_src.is_file():
        shutil.copy2(driver_src, PKG172_DIR / "driver_same_mesh_control_pdas.py")
        shutil.copy2(driver_src, PKG173_DIR / "driver_same_mesh_control_pdas.py")

    # Copy frozen production UEL
    shutil.copy2(FROZEN_UEL_PATH, PKG172_DIR / "f42_mixed_uel.for")
    shutil.copy2(FROZEN_UEL_PATH, PKG173_DIR / "f42_mixed_uel.for")
    assert sha256_file(PKG172_DIR / "f42_mixed_uel.for") == FROZEN_UEL_HASH
    assert sha256_file(PKG173_DIR / "f42_mixed_uel.for") == FROZEN_UEL_HASH

    # 9. Create input decks and datacheck decks
    # Base input deck from C5 Package 167
    base_inp_path = C5_SOURCE_DIR / "M1_C5_PACKAGE167_C2_2_CONTINUATION.inp"
    with open(base_inp_path, "r", encoding="utf-8") as f:
        base_inp_lines = f.readlines()

    def create_deck(output_path: Path, pkg_id: str, title: str):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"*Heading\n")
            f.write(f"** {title}\n")
            f.write(f"** Package: {pkg_id}\n")
            f.write(f"** Elements: 12996 Quads, Nodes: 13278 physical + RP 999999\n")
            f.write(f"** Prescribed target: uy = 0.0018703125442191958 mm\n")
            for line in base_inp_lines[5:]:  # skip original heading lines 0..4
                f.write(line)

    create_deck(
        PKG172_DIR / "M1_C5_PACKAGE172_OLD_CONTROL_REEQUILIBRATION.inp",
        "PACKAGE172_OLD_CONTROL",
        "Mode-I Method C Same-Mesh Control Arm 1 (Element-Averaged History Operator)"
    )
    create_deck(
        PKG173_DIR / "M1_C5_PACKAGE173_CORRECTED_CONTROL_REEQUILIBRATION.inp",
        "PACKAGE173_CORRECTED_CONTROL",
        "Mode-I Method C Same-Mesh Control Arm 2 (Hardened Isoparametric Bilinear GP Transfer)"
    )

    # Datacheck decks from Package 167
    base_mech_dc = C5_SOURCE_DIR / "P167_R3_MECHANICAL_DC.inp"
    base_phase_dc = C5_SOURCE_DIR / "P167_R3_PHASE_DC.inp"
    with open(base_mech_dc, "r", encoding="utf-8") as f:
        mech_dc_lines = f.readlines()
    with open(base_phase_dc, "r", encoding="utf-8") as f:
        phase_dc_lines = f.readlines()

    def create_dc_deck(output_path: Path, lines: list, title: str):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"*Heading\n")
            f.write(f"** {title}\n")
            for line in lines[5:]:
                f.write(line)

    create_dc_deck(
        PKG172_DIR / "P172_MECHANICAL_DC.inp",
        mech_dc_lines,
        "Package 172 Control Old Mechanical Datacheck"
    )
    create_dc_deck(
        PKG172_DIR / "P172_PHASE_DC.inp",
        phase_dc_lines,
        "Package 172 Control Old Phase Datacheck"
    )
    create_dc_deck(
        PKG173_DIR / "P173_MECHANICAL_DC.inp",
        mech_dc_lines,
        "Package 173 Control Corrected Mechanical Datacheck"
    )
    create_dc_deck(
        PKG173_DIR / "P173_PHASE_DC.inp",
        phase_dc_lines,
        "Package 173 Control Corrected Phase Datacheck"
    )

    # 9. Create run_datacheck.sh for both packages
    def create_run_datacheck_sh(pkg_dir: Path, pkg_prefix: str):
        content = f"""#!/bin/bash
set -euo pipefail
RUN_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
cd "${{RUN_DIR}}"

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

echo "=== Running Mechanical Subproblem Datacheck ({pkg_prefix}) ==="
abaqus job={pkg_prefix}_MECHANICAL_DC user=f42_mixed_uel.for input={pkg_prefix}_MECHANICAL_DC.inp cpus=1 memory="8 gb" datacheck interactive > {pkg_prefix}_MECHANICAL_DC.stdout.txt 2>&1
test -f "{pkg_prefix}_MECHANICAL_DC.dat"
grep -q 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' "{pkg_prefix}_MECHANICAL_DC.dat" || grep -q 'ANALYSIS DATACHECK COMPLETE' "{pkg_prefix}_MECHANICAL_DC.dat"
if grep -q '\\*\\*\\*ERROR' "{pkg_prefix}_MECHANICAL_DC.dat"; then echo "MECHANICAL DATACHECK ERROR"; exit 66; fi
echo "{pkg_prefix}_MECHANICAL_DC: AUTHENTIC_DATACHECK_PASS"

echo "=== Running Phase Subproblem Datacheck ({pkg_prefix}) ==="
abaqus job={pkg_prefix}_PHASE_DC user=f42_mixed_uel.for input={pkg_prefix}_PHASE_DC.inp cpus=1 memory="8 gb" datacheck interactive > {pkg_prefix}_PHASE_DC.stdout.txt 2>&1
test -f "{pkg_prefix}_PHASE_DC.dat"
grep -q 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' "{pkg_prefix}_PHASE_DC.dat" || grep -q 'ANALYSIS DATACHECK COMPLETE' "{pkg_prefix}_PHASE_DC.dat"
if grep -q '\\*\\*\\*ERROR' "{pkg_prefix}_PHASE_DC.dat"; then echo "PHASE DATACHECK ERROR"; exit 67; fi
echo "{pkg_prefix}_PHASE_DC: AUTHENTIC_DATACHECK_PASS"
"""
        sh_path = pkg_dir / "run_datacheck.sh"
        with open(sh_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

    create_run_datacheck_sh(PKG172_DIR, "P172")
    create_run_datacheck_sh(PKG173_DIR, "P173")

    # 10. Create smoke_import.py for remote environment verification
    smoke_py = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path

cur_dir = Path(__file__).resolve().parent
repo = cur_dir / "runtime"
if str(repo) not in sys.path:
    sys.path.insert(0, str(repo))

try:
    import scripts.state_transfer.driver_same_mesh_control_pdas as same_mesh_driver
    assert hasattr(same_mesh_driver, "SameMeshControlPDASDriver"), "Driver class missing"
    assert hasattr(same_mesh_driver, "DONOR_REFERENCE_FORCE_KN"), "Reference constants missing"
    print("REMOTE_IMPORT_SUCCESS: True")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""
    with open(PKG172_DIR / "smoke_import.py", "w", encoding="utf-8", newline="\n") as f:
        f.write(smoke_py)
    with open(PKG173_DIR / "smoke_import.py", "w", encoding="utf-8", newline="\n") as f:
        f.write(smoke_py)

    # 11. Create submit PBS templates (zero submissions authorized under F1622)
    def create_pbs(pkg_dir: Path, job_name: str, run_dir_name: str):
        content = f"""#!/bin/bash
#PBS -N {job_name}
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=08:00:00
#PBS -q entry_imfdfkmq
#PBS -j oe
#PBS -r n
#PBS -o /scratch9/pr21vyci/runs/{run_dir_name}/pbs_execution.log
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -euo pipefail
RUN_DIR="/scratch9/pr21vyci/runs/{run_dir_name}"
cd "${{RUN_DIR}}"

export JOB_NAME="{job_name}"
export NOTIFICATION_CONFIG="${{NOTIFICATION_CONFIG:-${{HOME}}/.config/adaptive-remeshing/notifications.env}}"
source "${{RUN_DIR}}/job_notifications.sh"
notification_load_config
notification_install_terminal_trap
notify_start

if ! type module >/dev/null 2>&1; then
    source /etc/profile.d/lmod.sh 2>/dev/null || source /usr/share/Modules/init/bash 2>/dev/null || true
fi
module purge
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023
command -v ifort

repo="${{RUN_DIR}}/runtime"
python3 "${{repo}}/scripts/state_transfer/driver_same_mesh_control_pdas.py" \\
    --package "${{RUN_DIR}}" \\
    --output "${{RUN_DIR}}/equilibration_${{PBS_JOBID}}" \\
    --extractor "${{repo}}/scripts/validation/extract_package148_iteration.py" \\
    --memory-gb 16 \\
    --timeout 25200 \\
    --max-outer 140 \\
    --omega-d-stage1 0.50 \\
    --omega-d-stage2 0.85 \\
    --omega-u-stage1 1.00 \\
    --omega-u-stage2 0.85 \\
    --max-active-cardinality 500 \\
    --max-symmetric-diff 10 \\
    --max-added-nodes 0 \\
    --stabilization-window 3 \\
    --rollback-factor 1.05 \\
    --divergence-factor 1.50 \\
    --catastrophic-delta-d-cap 0.05
EXIT_CODE=$?

echo "Same-Mesh Control Re-equilibration finished with exit code: ${{EXIT_CODE}}"
exit ${{EXIT_CODE}}
"""
        with open(pkg_dir / f"submit_{job_name}.pbs", "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

    create_pbs(PKG172_DIR, "M1_C5_P172_OLD_CONTROL", "mode1_c5_package172_old_control")
    create_pbs(PKG173_DIR, "M1_C5_P173_CORRECTED_CONTROL", "mode1_c5_package173_corrected_control")

    # 12. Create PACKAGE_MANIFEST.json for both packages
    def write_package_manifest(pkg_dir: Path, pkg_id: str, label: str, operator_name: str, pert_peak: float, pert_rms: float):
        files_dict = {}
        for p in sorted(pkg_dir.iterdir()):
            if p.is_file() and p.name != "PACKAGE_MANIFEST.json":
                files_dict[p.name] = {
                    "sha256": sha256_file(p),
                    "size_bytes": p.stat().st_size
                }

        manifest = {
            "schema": 1,
            "package_id": pkg_id,
            "label": label,
            "description": f"Method C Same-Mesh Abaqus Control Experiment: {label}",
            "frozen_uel_sha256": FROZEN_UEL_HASH,
            "donor_source": {
                "checkpoint": "Checkpoint 03 (Job 1419566.mmaster02)",
                "target_uy_mm": target_uy,
                "donor_reference_force_kN": ref_rf,
                "donor_reference_total_energy_kNmm": ref_energy
            },
            "receiver_mesh": {
                "name": "C5_Identical_Receiver",
                "elements_quad": 12996,
                "physical_nodes": 13278,
                "reference_point_id": 999999,
                "slit_pairs": len(c5_slit_pairs)
            },
            "transfer_operator": {
                "operator_name": operator_name,
                "history_perturbation_peak_MPa": pert_peak,
                "history_perturbation_rms_MPa": pert_rms
            },
            "numerical_parameters": {
                "damping_omega_d_stage1": 0.5,
                "damping_omega_d_stage2": 0.85,
                "damping_omega_u_stage1": 1.0,
                "damping_omega_u_stage2": 0.85,
                "anderson_enabled": False,
                "max_active_cardinality": 500,
                "max_symmetric_diff": 10,
                "max_added_nodes": 0,
                "stabilization_window": 3,
                "rollback_factor": 1.05,
                "divergence_factor": 1.5,
                "catastrophic_delta_d_cap": 0.05,
                "max_outer_iterations": 140,
                "delta_d_tol": 1e-05,
                "delta_u_tol_mm": 1e-09,
                "delta_h_tol_MPa": 0.0001,
                "kkt_tol": 1e-06
            },
            "files": files_dict
        }

        with open(pkg_dir / "PACKAGE_MANIFEST.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    write_package_manifest(
        PKG172_DIR, "package172_same_mesh_old_control",
        "Arm 1: CONTROL OLD (Element-Averaged History)",
        "element_averaged_mean",
        max_err_old, rms_err_old
    )
    write_package_manifest(
        PKG173_DIR, "package173_same_mesh_corrected_control",
        "Arm 2: CONTROL CORRECTED (Hardened Isoparametric Bilinear GP Transfer)",
        "hardened_isoparametric_gp_convex_clamp",
        max_err_corr, rms_err_corr
    )

    print("\nPackage generation complete:")
    print(f"  Package 172: {PKG172_DIR} ({len(list(PKG172_DIR.iterdir()))} files)")
    print(f"  Package 173: {PKG173_DIR} ({len(list(PKG173_DIR.iterdir()))} files)")


if __name__ == "__main__":
    build_same_mesh_control_packages()
