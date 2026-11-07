# -*- coding: utf-8 -*-
"""
evaluate_package157_continuation_acceptance.py
Mode-I Method C: Package 157 Revision 4 Continuation Physical Acceptance Evaluator.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Provides rigorous, independent post-processing and physical acceptance evaluation
for the Package 157 R4 C4 forward continuation experiment (PBS Job 1419147.mmaster02).

Gates Evaluated:
1. Substep coupled convergence:
   - Delta d <= 1.0e-5
   - Delta u <= 1.0e-9 mm
   - Delta H <= 1.0e-6 MPa
   - KKT active-set compliance (free_error <= 1.0e-6, dual_error <= 1.0e-6)
2. Committed state preservation:
   - Strict damage irreversibility: min(d_new - d_old) >= -1.0e-6
   - Physical phase bounds: 0.0 <= d <= 1.0
   - Full nodal state coverage: exactly 7,265 nodes
   - Full history Gauss-point coverage: exactly 28,224 Gauss points
   - Strict history monotonicity: H_new(e, g) >= H_old(e, g)
3. Matching-reference physical acceptance gates:
   - Reaction force discrepancy <= 5.0%
   - Raw total energy discrepancy <= 2.0%
   (Numerical convergence alone never establishes physical PASS).
"""
from __future__ import print_function, division
import csv
import json
import math
import os
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Canonical Tolerances and Gate Limits
GATE_RF2_TOL = 0.05             # 5.0% max force discrepancy
GATE_ENERGY_TOL = 0.02          # 2.0% max raw energy discrepancy
HEALING_TOL = 1e-6              # 1.0e-6 mm/mm healing tolerance
CONVERGENCE_DELTA_H_TOL = 1e-6  # 1.0e-6 MPa
CONVERGENCE_DELTA_D_TOL = 1e-5  # 1.0e-5
CONVERGENCE_DELTA_U_TOL = 1e-9  # 1.0e-9 mm
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
TOTAL_C4_NODES = 7265
TOTAL_C4_GPS = 28224

# Authentic Reference Datasets for Mode-I Candidate Donor C3 / h=0.0025 mm
DEFAULT_RF_CURVE_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "75_candidate_donor_h0025" / "evidence_1416259" / "donor_h0025_rf_curve.csv"
DEFAULT_ENERGY_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "75_candidate_donor_h0025" / "evidence_1416259" / "uel_energy_balance.csv"
DONOR_RUPTURE_UY_LIMIT = 0.00254010735  # Inc 111 rupture threshold (mm)

# Authentic Reference Anchor for Mode-I C4 Continuation at Baseline (uy = 0.00185031 mm)
# From step1_equilibrium_checkpoint_1419113_endpoint.json
BASELINE_UY = 0.0018503125442191958  # mm
BASELINE_RF2 = 0.18500999876019894   # kN
BASELINE_FRACTURE_ENERGY = 5.1169817948563804e-05  # kN*mm (J)


def evaluate_outer_iteration_convergence(iteration_dict):
    """
    Evaluates whether an individual outer iteration has converged according to
    coupled staggered criteria.
    """
    delta_d = iteration_dict.get("delta_d")
    delta_u = iteration_dict.get("delta_u")
    delta_h = iteration_dict.get("delta_h")
    free_error = iteration_dict.get("free_error", 0.0)
    dual_error = iteration_dict.get("dual_error", 0.0)

    reasons = []
    if delta_d is None or delta_d > CONVERGENCE_DELTA_D_TOL:
        reasons.append("delta_d %.3e > tol %.1e" % (delta_d if delta_d is not None else -1.0, CONVERGENCE_DELTA_D_TOL))
    if delta_u is None or delta_u > CONVERGENCE_DELTA_U_TOL:
        reasons.append("delta_u %.3e > tol %.1e" % (delta_u if delta_u is not None else -1.0, CONVERGENCE_DELTA_U_TOL))
    if delta_h is None or delta_h > CONVERGENCE_DELTA_H_TOL:
        reasons.append("delta_h %.3e > tol %.1e" % (delta_h if delta_h is not None else -1.0, CONVERGENCE_DELTA_H_TOL))
    if free_error is not None and free_error > 1e-6:
        reasons.append("free_error %.3e > tol 1e-6" % free_error)
    if dual_error is not None and dual_error > 1e-6:
        reasons.append("dual_error %.3e > tol 1e-6" % dual_error)

    passed = len(reasons) == 0
    return {
        "passed": passed,
        "delta_d": delta_d,
        "delta_u": delta_u,
        "delta_h": delta_h,
        "free_error": free_error,
        "dual_error": dual_error,
        "reasons": reasons
    }


def evaluate_state_preservation(prev_damage_dict, prev_history_dict,
                               curr_damage_dict, curr_history_dict):
    """
    Validates state coverage, damage bounds, damage irreversibility, and history monotonicity.
    prev_damage_dict: dict {node_id: d}
    prev_history_dict: dict {(elem_id, gp_id): H}
    curr_damage_dict: dict {node_id: d}
    curr_history_dict: dict {(elem_id, gp_id): H}
    """
    reasons = []

    # 1. Coverage
    if len(curr_damage_dict) != TOTAL_C4_NODES:
        reasons.append("Incomplete damage nodal count: %d (expected %d)" % (len(curr_damage_dict), TOTAL_C4_NODES))
    if len(curr_history_dict) != TOTAL_C4_GPS:
        reasons.append("Incomplete history GP count: %d (expected %d)" % (len(curr_history_dict), TOTAL_C4_GPS))

    # 2. Damage bounds & irreversibility
    min_delta_d = 0.0
    max_d = 0.0
    for node_id, d_new in curr_damage_dict.items():
        if not math.isfinite(d_new):
            reasons.append("Non-finite damage at node %s: %s" % (node_id, d_new))
            break
        if d_new < -1e-12 or d_new > 1.0 + 1e-6:
            reasons.append("Damage out of bounds [0, 1] at node %s: %s" % (node_id, d_new))
            break
        if d_new > max_d:
            max_d = d_new
        if prev_damage_dict and node_id in prev_damage_dict:
            d_old = prev_damage_dict[node_id]
            diff = d_new - d_old
            if diff < min_delta_d:
                min_delta_d = diff

    if min_delta_d < -HEALING_TOL:
        reasons.append("Damage healing violation: min delta_d = %.3e (limit -%.1e)" % (min_delta_d, HEALING_TOL))

    # 3. History monotonicity
    min_delta_h = 0.0
    for key, h_new in curr_history_dict.items():
        if not math.isfinite(h_new):
            reasons.append("Non-finite history at GP %s: %s" % (key, h_new))
            break
        if prev_history_dict and key in prev_history_dict:
            h_old = prev_history_dict[key]
            diff = h_new - h_old
            if diff < min_delta_h:
                min_delta_h = diff

    if min_delta_h < -1e-9:
        reasons.append("History monotonicity violation: min delta_H = %.3e" % min_delta_h)

    passed = len(reasons) == 0
    return {
        "passed": passed,
        "min_delta_d": min_delta_d,
        "max_d": max_d,
        "min_delta_h": min_delta_h,
        "nodes_checked": len(curr_damage_dict),
        "gps_checked": len(curr_history_dict),
        "reasons": reasons
    }


def load_authentic_reference_table(rf_path=DEFAULT_RF_CURVE_PATH, energy_path=DEFAULT_ENERGY_PATH):
    """
    Loads authentic matching-reference increments from candidate donor h0025 simulation evidence.
    Returns a sorted list of dicts with keys: inc, u_top_mm, rf2_kN, e_elastic, e_fracture, e_total.
    Returns None if reference files are missing or invalid.
    """
    rf_file = Path(rf_path)
    energy_file = Path(energy_path)
    if not rf_file.is_file() or not energy_file.is_file():
        return None

    rf_data = {}
    with rf_file.open("r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                inc = int(row["inc"])
                rf_data[inc] = {
                    "u_top_mm": float(row["u_top_mm"]),
                    "rf2_kN": float(row["rf2_kN"])
                }
            except (KeyError, ValueError):
                continue

    energy_data = {}
    with energy_file.open("r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("Step"):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 7:
                try:
                    inc = int(parts[1])
                    energy_data[inc] = {
                        "e_elastic": float(parts[4]),
                        "e_fracture": float(parts[5]),
                        "e_total": float(parts[6])
                    }
                except (ValueError, IndexError):
                    continue

    table = []
    for inc in sorted(rf_data.keys()):
        if inc in energy_data:
            table.append({
                "inc": inc,
                "u_top_mm": rf_data[inc]["u_top_mm"],
                "rf2_kN": rf_data[inc]["rf2_kN"],
                "e_elastic": energy_data[inc]["e_elastic"],
                "e_fracture": energy_data[inc]["e_fracture"],
                "e_total": energy_data[inc]["e_total"]
            })
    return table if table else None


def interpolate_authentic_reference(target_uy, ref_table=None, energy_type="total"):
    """
    Performs bracketing linear interpolation of reaction force and energy from authentic donor evidence.
    Valid domain: [u_min, DONOR_RUPTURE_UY_LIMIT] where DONOR_RUPTURE_UY_LIMIT = 0.0025401 mm.
    If outside domain or reference data is unavailable, returns dict with available=False.
    """
    if ref_table is None:
        ref_table = load_authentic_reference_table()
    if not ref_table:
        return {"available": False, "reason": "Authentic donor reference table missing or empty"}

    u_min = ref_table[0]["u_top_mm"]
    u_max = DONOR_RUPTURE_UY_LIMIT

    if target_uy < u_min or target_uy > u_max:
        return {
            "available": False,
            "reason": "target_uy=%.6e mm outside authentic domain [%.6e, %.6e] mm" % (target_uy, u_min, u_max)
        }

    lower = None
    upper = None
    for i in range(len(ref_table) - 1):
        r0 = ref_table[i]
        r1 = ref_table[i + 1]
        if r0["u_top_mm"] <= target_uy <= r1["u_top_mm"]:
            lower = r0
            upper = r1
            break

    if lower is None or upper is None:
        return {
            "available": False,
            "reason": "No bracketing reference increments found for target_uy=%.6e mm" % target_uy
        }

    span = upper["u_top_mm"] - lower["u_top_mm"]
    alpha = 0.0 if span <= 1e-15 else (target_uy - lower["u_top_mm"]) / span

    rf2_interp = lower["rf2_kN"] + alpha * (upper["rf2_kN"] - lower["rf2_kN"])

    e_key = "e_total" if energy_type == "total" else "e_fracture"
    energy_interp = lower[e_key] + alpha * (upper[e_key] - lower[e_key])

    return {
        "available": True,
        "target_uy_mm": target_uy,
        "rf2_kN": rf2_interp,
        "energy_kNmm": energy_interp,
        "energy_type": energy_type,
        "lower_inc": lower["inc"],
        "upper_inc": upper["inc"],
        "lower_u_mm": lower["u_top_mm"],
        "upper_u_mm": upper["u_top_mm"],
        "alpha": alpha
    }


def evaluate_physical_acceptance(target_uy, observed_rf2, observed_energy,
                                 ref_rf2=None, ref_energy=None, ref_table=None,
                                 energy_type="total"):
    """
    Evaluates reaction force discrepancy <= 5.0% and raw energy discrepancy <= 2.0%
    against matching-displacement authentic reference.
    If ref_rf2 or ref_energy is None, authentic reference values are interpolated
    from the donor reference dataset (donor_h0025_rf_curve.csv, uel_energy_balance.csv).
    If target_uy is outside the authentic reference domain, status is REFERENCE_UNAVAILABLE.
    """
    reasons = []

    if ref_rf2 is None or ref_energy is None:
        ref_lookup = interpolate_authentic_reference(target_uy, ref_table=ref_table, energy_type=energy_type)
        if not ref_lookup.get("available", False):
            reasons.append("Authentic reference unavailable for target_uy=%.6e mm: %s" %
                           (target_uy, ref_lookup.get("reason", "unknown error")))
            return {
                "passed": False,
                "gate_status": "REFERENCE_UNAVAILABLE",
                "target_uy_mm": target_uy,
                "observed_rf2_kN": observed_rf2,
                "ref_rf2_kN": None,
                "delta_rf2_rel": None,
                "rf2_gate_pass": False,
                "observed_energy_kNmm": observed_energy,
                "ref_energy_kNmm": None,
                "delta_energy_rel": None,
                "energy_gate_pass": False,
                "reasons": reasons
            }
        if ref_rf2 is None:
            ref_rf2 = ref_lookup["rf2_kN"]
        if ref_energy is None:
            ref_energy = ref_lookup["energy_kNmm"]

    delta_rf2_rel = abs(observed_rf2 - ref_rf2) / abs(ref_rf2)
    delta_energy_rel = abs(observed_energy - ref_energy) / abs(ref_energy)

    rf2_pass = delta_rf2_rel <= GATE_RF2_TOL
    energy_pass = delta_energy_rel <= GATE_ENERGY_TOL

    if not rf2_pass:
        reasons.append("RF2 discrepancy %.2f%% exceeds gate %.2f%% (observed=%.5f kN, ref=%.5f kN)" %
                       (delta_rf2_rel * 100.0, GATE_RF2_TOL * 100.0, observed_rf2, ref_rf2))
    if not energy_pass:
        reasons.append("Raw energy discrepancy %.2f%% exceeds gate %.2f%% (observed=%.5e, ref=%.5e)" %
                       (delta_energy_rel * 100.0, GATE_ENERGY_TOL * 100.0, observed_energy, ref_energy))

    passed = rf2_pass and energy_pass
    gate_status = "PASS" if passed else "FAIL"
    return {
        "passed": passed,
        "gate_status": gate_status,
        "target_uy_mm": target_uy,
        "observed_rf2_kN": observed_rf2,
        "ref_rf2_kN": ref_rf2,
        "delta_rf2_rel": delta_rf2_rel,
        "rf2_gate_pass": rf2_pass,
        "observed_energy_kNmm": observed_energy,
        "ref_energy_kNmm": ref_energy,
        "delta_energy_rel": delta_energy_rel,
        "energy_gate_pass": energy_pass,
        "reasons": reasons
    }


def query_remote_job_status(job_id="1419147.mmaster02"):
    """
    Queries live scheduler status for the specified job using Invoke-GuardedSsh.ps1.
    """
    ssh_wrapper = REPO_ROOT / ".agents" / "scripts" / "Invoke-GuardedSsh.ps1"
    cmd = [
        "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
        "-File", str(ssh_wrapper),
        "-RemoteCommand", "qstat -x " + job_id
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    raw_out = stdout.decode("utf-8", "replace")
    lines = [line.strip() for line in raw_out.splitlines() if line.strip() and not line.startswith("**")]

    job_state = "UNKNOWN"
    time_used = "00:00:00"
    queue = "UNKNOWN"
    for line in lines:
        parts = line.split()
        if len(parts) >= 6 and parts[0].startswith(job_id.split(".")[0]):
            time_used = parts[3]
            job_state = parts[4]
            queue = parts[5]
            break

    return {
        "job_id": job_id,
        "scheduler_state": job_state,
        "time_used": time_used,
        "queue": queue,
        "raw_output": raw_out
    }


def fetch_remote_telemetry(remote_telemetry_path="/scratch9/pr21vyci/runs/mode1_c4_package157_c1_2_continuation_r4/continuation_1419147.mmaster02/live_iteration_telemetry.json"):
    """
    Fetches and parses the live iteration telemetry array from the remote cluster.
    """
    ssh_wrapper = REPO_ROOT / ".agents" / "scripts" / "Invoke-GuardedSsh.ps1"
    cmd = [
        "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
        "-File", str(ssh_wrapper),
        "-RemoteCommand", "cat " + remote_telemetry_path
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        return None
    raw_out = stdout.decode("utf-8", "replace")
    clean_lines = [l for l in raw_out.splitlines() if not l.startswith("**") and not l.startswith("cat:")]
    clean_text = "\n".join(clean_lines).strip()
    try:
        return json.loads(clean_text)
    except Exception:
        return None


if __name__ == "__main__":
    print("Package 157 R4 Continuation Acceptance Evaluator loaded successfully.")
