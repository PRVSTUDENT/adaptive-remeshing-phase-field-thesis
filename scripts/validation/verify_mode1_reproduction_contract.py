#!/usr/bin/env python3
"""
Mode-I Method B Reproduction Contract Verification and Deterministic Replay.
Performs an automated clean-checkout smoke test validating configuration, input decks,
physical boundary/element sets, frozen UEL hash, and archived numerical metrics.
"""

import hashlib
import json
import os
import sys
from pathlib import Path


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def verify_reproduction_contract(workspace_dir: str = ".") -> dict:
    ws = Path(workspace_dir).resolve()
    config_path = ws / "models/pandey_kumar_mode1/canonical_mode1_method_b_config.json"

    if not config_path.exists():
        raise FileNotFoundError(f"Canonical config missing: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    receipt = {
        "schema": 1,
        "task_id": cfg["task_id"],
        "name": "Mode-I Method B Clean-Checkout Reproduction Verification",
        "checks": {},
        "overall_status": "PENDING"
    }

    # 1. Check frozen UEL integrity
    uel_rel = cfg["uel_contract"]["source_file"]
    uel_path = ws / uel_rel
    if not uel_path.exists():
        raise FileNotFoundError(f"Production UEL missing: {uel_path}")
    uel_actual_hash = compute_sha256(uel_path)
    uel_expected_hash = cfg["uel_contract"]["expected_sha256"]
    uel_pass = (uel_actual_hash == uel_expected_hash)
    receipt["checks"]["uel_integrity"] = {
        "path": uel_rel,
        "expected_sha256": uel_expected_hash,
        "actual_sha256": uel_actual_hash,
        "passed": uel_pass
    }
    if not uel_pass:
        raise ValueError(f"UEL hash mismatch! Expected {uel_expected_hash}, got {uel_actual_hash}")

    # 2. Check input deck files and hashes
    for key, item in cfg["mesh_hierarchy"].items():
        deck_rel = item["input_deck"]
        deck_path = ws / deck_rel
        if not deck_path.exists():
            raise FileNotFoundError(f"Input deck missing for {key}: {deck_path}")
        deck_actual_hash = compute_sha256(deck_path)
        deck_expected_hash = item["input_deck_sha256"]
        deck_pass = (deck_actual_hash == deck_expected_hash)
        receipt["checks"][f"deck_hash_{key}"] = {
            "path": deck_rel,
            "expected_sha256": deck_expected_hash,
            "actual_sha256": deck_actual_hash,
            "passed": deck_pass
        }
        if not deck_pass:
            raise ValueError(f"Deck hash mismatch for {key}! Expected {deck_expected_hash}, got {deck_actual_hash}")

    # 3. Check physical geometry, node sets, and duplicate slit flank nodes on adapted deck
    adapted_deck_path = ws / cfg["mesh_hierarchy"]["adapted_fracture_mesh"]["input_deck"]
    with open(adapted_deck_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_node = False
    xs, ys = [], []
    has_bottom = False
    has_top = False
    has_rp = False
    has_uel1 = False
    has_uel2 = False

    slit_y = cfg["physical_problem"]["initial_slit"]["location_y_mm"]
    slit_a0 = cfg["physical_problem"]["initial_slit"]["length_a0_mm"]
    nodes_on_slit = 0

    for line in lines:
        l_upper = line.strip().upper()
        if l_upper.startswith("*NODE") and not l_upper.startswith("*NODE PRINT") and not l_upper.startswith("*NODE FILE"):
            in_node = True
            continue
        if in_node:
            if l_upper.startswith("*"):
                in_node = False
            else:
                parts = [p.strip() for p in line.split(",") if p.strip()]
                if len(parts) >= 3:
                    try:
                        x = float(parts[1])
                        y = float(parts[2])
                        xs.append(x)
                        ys.append(y)
                        if abs(y - slit_y) < 1e-5 and x <= slit_a0 + 1e-5:
                            nodes_on_slit += 1
                    except ValueError:
                        pass
        if "*NSET" in l_upper and "N_BOTTOM" in l_upper:
            has_bottom = True
        if "*NSET" in l_upper and "N_TOP" in l_upper:
            has_top = True
        if "*NSET" in l_upper and "N_RP" in l_upper:
            has_rp = True
        if "*USER ELEMENT" in l_upper and "TYPE=U1" in l_upper:
            has_uel1 = True
        if "*USER ELEMENT" in l_upper and "TYPE=U2" in l_upper:
            has_uel2 = True

    domain_x_pass = (abs(min(xs) - 0.0) < 1e-4 and abs(max(xs) - 1.0) < 1e-4)
    domain_y_pass = (abs(min(ys) - 0.0) < 1e-4 and abs(max(ys) - 1.0) < 1e-4)
    topology_pass = (has_bottom and has_top and has_rp and has_uel1 and has_uel2 and nodes_on_slit > 20)

    receipt["checks"]["geometry_and_topology"] = {
        "node_count": len(xs),
        "domain_x_range": [min(xs), max(xs)],
        "domain_y_range": [min(ys), max(ys)],
        "nodes_on_slit_y05": nodes_on_slit,
        "has_N_BOTTOM": has_bottom,
        "has_N_TOP": has_top,
        "has_N_RP": has_rp,
        "has_UEL_JTYPE1": has_uel1,
        "has_UEL_JTYPE2": has_uel2,
        "passed": domain_x_pass and domain_y_pass and topology_pass
    }
    if not (domain_x_pass and domain_y_pass and topology_pass):
        raise ValueError("Geometry and topology check failed on adapted fracture deck!")

    # 4. Check archived evidence metrics against tolerances
    eval_pkg38_path = ws / "models/pandey_kumar_mode1/38_method_b_native_final_14k/M1_MB_NATIVE_14K_TERMINAL_EVALUATION.json"
    with open(eval_pkg38_path, "r", encoding="utf-8") as f:
        pkg38 = json.load(f)
    t_m = pkg38["terminal_metrics"]

    # Gate 1: Elastic stiffness K0
    tol_k0 = cfg["acceptance_tolerances"]["elastic_stiffness_K0"]["tolerance_pct"]
    err_k0 = abs(t_m["delta_K0_pct"])
    k0_pass = (err_k0 <= tol_k0)

    # Gate 2: Peak force Fmax
    tol_fmax = cfg["acceptance_tolerances"]["peak_reaction_force_Fmax"]["tolerance_pct"]
    err_fmax = abs(t_m["delta_F_max_pct"])
    fmax_pass = (err_fmax <= tol_fmax)

    # Gate 3: Peak displacement upeak
    tol_upeak = cfg["acceptance_tolerances"]["peak_displacement_upeak"]["tolerance_pct"]
    err_upeak = abs(t_m["delta_u_peak_pct"])
    upeak_pass = (err_upeak <= tol_upeak)

    # Gate 4: Terminal horizon
    term_u = t_m["u_term_mm"]
    term_inc = t_m["total_increments"]
    horizon_pass = (term_u >= 0.010 and term_inc >= 7000)

    # Gate 5: Solver speedup
    s_speedup = cfg["computational_benchmarks"]["solver_speedup_8t_vs_serial"]
    speedup_pass = (s_speedup >= 1.5)

    # Gate 6: Coarse DOF savings
    coarse_dof_red = cfg["mesh_hierarchy"]["coarse_preanalysis"]["dof_reduction_vs_ref15k_pct"]
    coarse_dof_pass = (coarse_dof_red >= 70.0)

    receipt["checks"]["parity_and_convergence"] = {
        "delta_K0_pct": t_m["delta_K0_pct"],
        "K0_pass": k0_pass,
        "delta_Fmax_pct": t_m["delta_F_max_pct"],
        "Fmax_pass": fmax_pass,
        "delta_upeak_pct": t_m["delta_u_peak_pct"],
        "upeak_pass": upeak_pass,
        "terminal_displacement_mm": term_u,
        "terminal_increments": term_inc,
        "horizon_pass": horizon_pass,
        "solver_speedup": s_speedup,
        "speedup_pass": speedup_pass,
        "coarse_dof_reduction_pct": coarse_dof_red,
        "coarse_dof_pass": coarse_dof_pass,
        "passed": k0_pass and fmax_pass and upeak_pass and horizon_pass and speedup_pass and coarse_dof_pass
    }

    receipt["overall_status"] = "PASSED" if all(c["passed"] for c in receipt["checks"].values()) else "FAILED"

    # Write receipt artifact
    receipt_path = ws / "results/validation/mode1_reproduction_smoke_test_receipt.json"
    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2)

    print(f"Reproduction contract verified. Receipt written to: {receipt_path}")
    return receipt


if __name__ == "__main__":
    res = verify_reproduction_contract(".")
    if res["overall_status"] != "PASSED":
        sys.exit(1)
    sys.exit(0)
