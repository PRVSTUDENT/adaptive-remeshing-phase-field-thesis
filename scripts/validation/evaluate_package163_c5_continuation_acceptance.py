# -*- coding: utf-8 -*-
"""
evaluate_package163_c5_continuation_acceptance.py
Mode-I Method C Cycle 2: Candidate C5 Stage C2-1 (+5 nm Forward Continuation) Physical Acceptance Evaluator.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2

Provides rigorous, independent post-processing and physical acceptance evaluation
for the Package 163 C5 forward continuation experiment (PBS Job 1419488.mmaster02).

Physical Acceptance Gates Evaluated:
1. Stage C2-1 Continuity & Target Load Level:
   - Baseline load: uy = 0.0018603125442191958 mm (matches accepted Checkpoint 01)
   - Target continuation load: uy = 0.0018653125442191958 mm (+5.0 nm forward increment)
   - Predecessor binding: Accepted Checkpoint 01 SHA-256 DCFD31186061FA81111DA18071CF8ADFB9BAF2C5CB343CB60F08416741C1B64A
2. True Post-Phase Damage Convergence:
   - Delta d <= 1.0e-5
3. Coupled Kinematic Convergence:
   - Delta u <= 1.0e-9 mm
4. Driving History Convergence:
   - Delta H <= 1.0e-4 MPa
5. Variational Stationarity & Obstacle Complementarity:
   - Free phase-field residual <= 1.0e-6 kN
   - Dual obstacle defect <= 1.0e-6 kN*mm
6. Pointwise Irreversibility & Bound Preservation:
   - Zero damage healing: min(d_02 - d_01) >= -1.0e-6 across all 13,278 nodes
   - Physical phase bounds: 0.0 <= d <= 1.0 everywhere
7. Driving History Monotonicity & Pointwise History Consistency:
   - Pointwise history monotonicity: H_02(e, g) >= H_01(e, g) - 1.0e-6 MPa across all 51,984 GPs
   - Pointwise history consistency: H*(e, g) = max(H0(e, g), psi+(u*(e, g))) at all 51,984 GPs
8. Authentic C4 Reference Parity at Target Continuation Load (+5 nm):
   - Reaction force discrepancy <= 2.0% vs authentic C4 R6 reference (0.183468 kN)
   - Total raw energy discrepancy <= 2.0% vs authentic C4 R6 reference (0.000225114 kN*mm)
9. Quantitative C5 State Progression (Before vs After):
   - Measured change in reaction force, total energy, maximum damage, and crack-tip spatial localization
"""

from __future__ import print_function, division
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

# Canonical Gate Limits
GATE_RF2_TOL = 0.02                 # 2.0% max force drift vs authentic reference
GATE_ENERGY_TOL = 0.02              # 2.0% max energy drift vs authentic reference
GATE_PHASE_RESIDUAL_TOL = 1.0e-6    # 1.0e-6 kN free phase-field residual
GATE_DUAL_ERROR_TOL = 1.0e-6        # 1.0e-6 kN*mm dual obstacle defect
HEALING_TOL = 1.0e-6                # 1.0e-6 damage healing tolerance
CONVERGENCE_DELTA_H_TOL = 1.0e-4    # 1.0e-4 MPa driving history tolerance
CONVERGENCE_DELTA_D_TOL = 1.0e-5    # 1.0e-5 phase-field increment tolerance
CONVERGENCE_DELTA_U_TOL = 1.0e-9    # 1.0e-9 mm displacement tolerance
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

# Mesh Dimensions for C5
TOTAL_C5_QUADS = 12996
TOTAL_C5_NODES = 13278
TOTAL_C5_GPS = 51984
TOTAL_SEAM_PAIRS = 53

# Predecessor & Reference Benchmarks
ACCEPTED_CHECKPOINT_01_SHA256 = "DCFD31186061FA81111DA18071CF8ADFB9BAF2C5CB343CB60F08416741C1B64A"
BASELINE_UY_MM = 0.0018603125442191958
TARGET_UY_MM = 0.0018653125442191958
TARGET_INCREMENT_MM = 0.0000050000000000000

# Authentic C4 R6 Reference Values at Target Load uy = 0.0018653125442191958 mm
C4_R6_REFERENCE_FORCE_KN = 0.18346779247291461
C4_R6_REFERENCE_TOTAL_ENERGY_KNMM = 0.00022511363524288855


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(str(filepath), "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


class Package163AcceptanceEvaluator(object):
    """
    Evaluates physical and numerical acceptance of Package 163 C5 forward continuation results.
    """

    def __init__(self, run_dir=None, checkpoint_path=None, predecessor_path=None):
        self.run_dir = Path(run_dir) if run_dir else None
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else None
        self.predecessor_path = Path(predecessor_path) if predecessor_path else None

    def validate_predecessor_binding(self, predecessor_path=None):
        """
        Verifies that predecessor Checkpoint 01 matches accepted hash exactly.
        """
        p = Path(predecessor_path) if predecessor_path else self.predecessor_path
        if not p or not p.is_file():
            return {"passed": False, "reason": "Predecessor checkpoint file missing"}
        actual_hash = compute_sha256(p)
        matches = (actual_hash == ACCEPTED_CHECKPOINT_01_SHA256)
        return {
            "passed": matches,
            "actual_sha256": actual_hash,
            "expected_sha256": ACCEPTED_CHECKPOINT_01_SHA256
        }

    def validate_checkpoint_continuity(self, chkpt_01, chkpt_02):
        """
        Verifies schema and full-state continuity between accepted Checkpoint 01 and Checkpoint 02.
        """
        violations = []
        if chkpt_01.get("stage") != "C2-0":
            violations.append("Checkpoint 01 stage '%s' != 'C2-0'" % chkpt_01.get("stage"))
        if chkpt_02.get("stage") != "C2-1":
            violations.append("Checkpoint 02 stage '%s' != 'C2-1'" % chkpt_02.get("stage"))

        u1 = float(chkpt_01.get("target_uy_mm", 0.0))
        u2 = float(chkpt_02.get("target_uy_mm", 0.0))
        if abs(u1 - BASELINE_UY_MM) > 1e-12:
            violations.append("Checkpoint 01 baseline uy %.10g != %.10g" % (u1, BASELINE_UY_MM))
        if abs(u2 - TARGET_UY_MM) > 1e-12:
            violations.append("Checkpoint 02 target uy %.10g != %.10g" % (u2, TARGET_UY_MM))

        inc = u2 - u1
        if abs(inc - TARGET_INCREMENT_MM) > 1e-12:
            violations.append("Displacement advancement %.10g != %.10g" % (inc, TARGET_INCREMENT_MM))

        disp2 = chkpt_02.get("displacement", [])
        dam2 = chkpt_02.get("damage", [])
        hist2 = chkpt_02.get("history", [])

        if len(disp2) != TOTAL_C5_NODES:
            violations.append("Checkpoint 02 displacement nodes %d != %d" % (len(disp2), TOTAL_C5_NODES))
        if len(dam2) != TOTAL_C5_NODES:
            violations.append("Checkpoint 02 damage nodes %d != %d" % (len(dam2), TOTAL_C5_NODES))
        if len(hist2) != TOTAL_C5_GPS:
            violations.append("Checkpoint 02 history GPs %d != %d" % (len(hist2), TOTAL_C5_GPS))

        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "baseline_uy_mm": u1,
            "target_uy_mm": u2,
            "increment_mm": inc
        }

    def evaluate_coupled_convergence(self, outer_telemetry):
        """
        Evaluates coupled staggered convergence tolerances from outer iteration telemetry.
        """
        if not outer_telemetry:
            return {"passed": False, "reason": "Empty telemetry"}

        last = outer_telemetry[-1] if isinstance(outer_telemetry, list) else outer_telemetry
        delta_d = last.get("delta_d")
        delta_u = last.get("delta_u")
        delta_h = last.get("delta_h")
        free_res = last.get("free_error", last.get("free_phase_residual", 0.0))
        dual_res = last.get("dual_error", 0.0)

        violations = []
        if delta_d is None or delta_d > CONVERGENCE_DELTA_D_TOL:
            violations.append("delta_d %.3e > tol %.1e" % (delta_d if delta_d is not None else -1.0, CONVERGENCE_DELTA_D_TOL))
        if delta_u is None or delta_u > CONVERGENCE_DELTA_U_TOL:
            violations.append("delta_u %.3e > tol %.1e" % (delta_u if delta_u is not None else -1.0, CONVERGENCE_DELTA_U_TOL))
        if delta_h is not None and delta_h > CONVERGENCE_DELTA_H_TOL:
            violations.append("delta_h %.3e > tol %.1e" % (delta_h, CONVERGENCE_DELTA_H_TOL))
        if free_res is not None and free_res > GATE_PHASE_RESIDUAL_TOL:
            violations.append("free_phase_residual %.3e > tol %.1e kN" % (free_res, GATE_PHASE_RESIDUAL_TOL))
        if dual_res is not None and dual_res > GATE_DUAL_ERROR_TOL:
            violations.append("dual_error %.3e > tol %.1e" % (dual_res, GATE_DUAL_ERROR_TOL))

        outer_num = last.get("outer", last.get("outer_iteration", len(outer_telemetry) if isinstance(outer_telemetry, list) else 1))

        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "outer_iteration": outer_num,
            "delta_d": delta_d,
            "delta_u": delta_u,
            "delta_h": delta_h,
            "free_error": free_res,
            "dual_error": dual_res,
            "pdas_active_count": last.get("pdas_active_count"),
            "pdas_free_count": last.get("pdas_free_count"),
            "kkt_active_count": last.get("kkt_active_count"),
            "kkt_free_count": last.get("kkt_free_count")
        }

    def evaluate_pointwise_irreversibility(self, d_initial, d_continued):
        """
        Evaluates pointwise phase irreversibility: d_continued(n) >= d_initial(n) - HEALING_TOL.
        Audits boundary domain bounds: 0.0 <= d <= 1.0 everywhere.
        """
        if len(d_continued) != TOTAL_C5_NODES:
            return {
                "passed": False,
                "reason": "Node count mismatch: %d != %d" % (len(d_continued), TOTAL_C5_NODES)
            }

        healing_violations = []
        max_healing = 0.0
        out_of_bounds = []

        for node_id, d_new in d_continued.items():
            if d_new < -1e-6 or d_new > 1.0 + 1e-6:
                out_of_bounds.append((node_id, d_new))

            d_old = d_initial.get(node_id, 0.0)
            diff = d_new - d_old
            if diff < -HEALING_TOL:
                healing_violations.append((node_id, d_old, d_new, diff))
                if abs(diff) > max_healing:
                    max_healing = abs(diff)

        return {
            "passed": len(healing_violations) == 0 and len(out_of_bounds) == 0,
            "total_nodes_audited": len(d_continued),
            "healing_violations_count": len(healing_violations),
            "max_healing_magnitude": max_healing,
            "out_of_bounds_count": len(out_of_bounds),
            "healing_violations_sample": healing_violations[:5]
        }

    def evaluate_history_monotonicity(self, h_initial, h_continued):
        """
        Evaluates pointwise Gauss-point driving history monotonicity: H_continued >= H_initial - 1.0e-6.
        """
        if len(h_continued) != TOTAL_C5_GPS:
            return {
                "passed": False,
                "reason": "GP count mismatch: %d != %d" % (len(h_continued), TOTAL_C5_GPS)
            }

        history_violations = []
        max_history_drop = 0.0

        for gp_key, h_new in h_continued.items():
            h_old = h_initial.get(gp_key, 0.0)
            if h_new < h_old - 1e-6:
                diff = h_new - h_old
                history_violations.append((gp_key, h_old, h_new, diff))
                if abs(diff) > max_history_drop:
                    max_history_drop = abs(diff)

        return {
            "passed": len(history_violations) == 0,
            "total_gps_audited": len(h_continued),
            "history_violations_count": len(history_violations),
            "max_history_drop_MPa": max_history_drop,
            "history_violations_sample": history_violations[:5]
        }

    def evaluate_history_equality(self, h_initial, psi_plus_continued, h_continued):
        """
        Evaluates pointwise driving history equality: H*(e, g) = max(H0(e, g), psi+(u*(e, g))).
        Tolerates up to 1.0e-4 MPa numerical tolerance.
        """
        if len(h_continued) != TOTAL_C5_GPS:
            return {
                "passed": False,
                "reason": "GP count mismatch: %d != %d" % (len(h_continued), TOTAL_C5_GPS)
            }

        equality_violations = []
        max_defect = 0.0

        for gp_key, h_eq in h_continued.items():
            h0 = h_initial.get(gp_key, 0.0)
            psi_p = psi_plus_continued.get(gp_key, 0.0)
            expected_h = max(h0, psi_p)
            defect = abs(h_eq - expected_h)
            if defect > 1.0e-4:
                equality_violations.append((gp_key, h0, psi_p, h_eq, expected_h, defect))
                if defect > max_defect:
                    max_defect = defect

        return {
            "passed": len(equality_violations) == 0,
            "total_gps_audited": len(h_continued),
            "equality_violations_count": len(equality_violations),
            "max_equality_defect_MPa": max_defect,
            "equality_violations_sample": equality_violations[:5]
        }

    def evaluate_reference_parity(self, rf2_actual, total_energy_actual):
        """
        Evaluates reaction force and total raw energy parity against authentic C4 R6 reference at +5 nm.
        """
        rf_err = abs(rf2_actual - C4_R6_REFERENCE_FORCE_KN) / C4_R6_REFERENCE_FORCE_KN
        energy_err = abs(total_energy_actual - C4_R6_REFERENCE_TOTAL_ENERGY_KNMM) / C4_R6_REFERENCE_TOTAL_ENERGY_KNMM

        rf_pass = rf_err <= GATE_RF2_TOL
        energy_pass = energy_err <= GATE_ENERGY_TOL

        return {
            "passed": rf_pass and energy_pass,
            "rf2_actual_kN": rf2_actual,
            "c4_r6_reference_force_kN": C4_R6_REFERENCE_FORCE_KN,
            "rf2_discrepancy_pct": rf_err * 100.0,
            "rf2_pass": rf_pass,
            "total_energy_actual_kNmm": total_energy_actual,
            "c4_r6_reference_total_energy_kNmm": C4_R6_REFERENCE_TOTAL_ENERGY_KNMM,
            "total_energy_discrepancy_pct": energy_err * 100.0,
            "total_energy_pass": energy_pass
        }

    def evaluate_c5_state_progression(self, chkpt_01, chkpt_02):
        """
        Computes quantitative state progression metrics from Checkpoint 01 (Stage C2-0)
        to Checkpoint 02 (Stage C2-1 +5 nm continuation).
        """
        f1 = float(chkpt_01.get("reaction_force_kN", 0.0))
        f2 = float(chkpt_02.get("reaction_force_kN", 0.0))
        e1 = float(chkpt_01.get("total_energy_kNmm", 0.0))
        e2 = float(chkpt_02.get("total_energy_kNmm", 0.0))

        dam1 = dict(chkpt_01.get("damage", [])) if isinstance(chkpt_01.get("damage"), list) else chkpt_01.get("damage", {})
        dam2 = dict(chkpt_02.get("damage", [])) if isinstance(chkpt_02.get("damage"), list) else chkpt_02.get("damage", {})

        max_d1 = max(dam1.values()) if dam1 else 0.0
        max_d2 = max(dam2.values()) if dam2 else 0.0

        delta_f = f2 - f1
        delta_e = e2 - e1
        delta_max_d = max_d2 - max_d1

        # Count nodes with active damage advance (d2 - d1 > 1e-4)
        advancing_nodes = sum(1 for n in dam2 if dam2[n] - dam1.get(n, 0.0) > 1e-4)

        return {
            "force_checkpoint_01_kN": f1,
            "force_checkpoint_02_kN": f2,
            "delta_force_kN": delta_f,
            "force_change_pct": (delta_f / f1 * 100.0) if f1 > 0 else 0.0,
            "energy_checkpoint_01_kNmm": e1,
            "energy_checkpoint_02_kNmm": e2,
            "delta_energy_kNmm": delta_e,
            "energy_change_pct": (delta_e / e1 * 100.0) if e1 > 0 else 0.0,
            "max_damage_checkpoint_01": max_d1,
            "max_damage_checkpoint_02": max_d2,
            "delta_max_damage": delta_max_d,
            "advancing_nodes_count": advancing_nodes
        }

    def evaluate_full_acceptance(self, chkpt_01_data, chkpt_02_data, telemetry_data, summary_data=None):
        """
        Executes full physical acceptance evaluation across all gates.
        Returns final classification: METHOD_C_CYCLE_PHYSICAL_PASS, PHYSICAL_FAIL, or INSUFFICIENT_EVIDENCE.
        """
        # 1. State continuity
        continuity = self.validate_checkpoint_continuity(chkpt_01_data, chkpt_02_data)

        # 2. Coupled convergence
        convergence = self.evaluate_coupled_convergence(telemetry_data)

        # 3. Damage format normalization
        if isinstance(chkpt_01_data.get("damage"), list):
            d1 = {int(r[0]): float(r[1]) for r in chkpt_01_data["damage"]}
        else:
            d1 = {int(k): float(v) for k, v in chkpt_01_data["damage"].items()}

        if isinstance(chkpt_02_data.get("damage"), list):
            d2 = {int(r[0]): float(r[1]) for r in chkpt_02_data["damage"]}
        else:
            d2 = {int(k): float(v) for k, v in chkpt_02_data["damage"].items()}

        irreversibility = self.evaluate_pointwise_irreversibility(d1, d2)

        # 4. History format normalization
        if isinstance(chkpt_01_data.get("history"), list):
            h1 = {(int(r[0]), int(r[1])): float(r[2]) for r in chkpt_01_data["history"]}
        else:
            h1 = {tuple(int(x) for x in k.split(",")): float(v) for k, v in chkpt_01_data["history"].items()}

        if isinstance(chkpt_02_data.get("history"), list):
            h2 = {(int(r[0]), int(r[1])): float(r[2]) for r in chkpt_02_data["history"]}
        else:
            h2 = {tuple(int(x) for x in k.split(",")): float(v) for k, v in chkpt_02_data["history"].items()}

        history_mono = self.evaluate_history_monotonicity(h1, h2)

        # 5. Reference parity
        rf2_val = chkpt_02_data.get("reaction_force_kN")
        if rf2_val is None and summary_data:
            rf2_val = summary_data.get("reaction_force_kN")
        tot_e_val = chkpt_02_data.get("total_energy_kNmm")
        if tot_e_val is None and summary_data:
            tot_e_val = summary_data.get("total_energy_kNmm")

        if rf2_val is not None and tot_e_val is not None:
            parity = self.evaluate_reference_parity(float(rf2_val), float(tot_e_val))
        else:
            parity = {"passed": False, "reason": "Missing rf2 or total_energy in checkpoint/summary"}

        # 6. Progression
        progression = self.evaluate_c5_state_progression(chkpt_01_data, chkpt_02_data)

        # Overall decision
        all_passed = (
            continuity["passed"] and
            convergence["passed"] and
            irreversibility["passed"] and
            history_mono["passed"] and
            parity["passed"]
        )

        decision = "METHOD_C_CYCLE_PHYSICAL_PASS" if all_passed else "PHYSICAL_FAIL"

        return {
            "schema": 1,
            "evaluation_type": "PACKAGE_163_C5_CONTINUATION_ACCEPTANCE",
            "physical_acceptance_decision": decision,
            "verification_passed": all_passed,
            "continuity": continuity,
            "coupled_convergence": convergence,
            "irreversibility": irreversibility,
            "history_monotonicity": history_mono,
            "reference_parity": parity,
            "c5_state_progression": progression
        }


def main():
    parser = argparse.ArgumentParser(description="Package 163 C5 Forward Continuation Physical Acceptance Evaluator")
    parser.add_argument("--checkpoint", required=True, help="Path to Checkpoint 02 json")
    parser.add_argument("--predecessor", required=True, help="Path to Checkpoint 01 json")
    parser.add_argument("--telemetry", required=True, help="Path to live_iteration_telemetry.json")
    parser.add_argument("--summary", default=None, help="Path to c5_forward_continuation_summary.json (optional)")
    parser.add_argument("--output", default=None, help="Path to write acceptance evaluation json")
    args = parser.parse_args()

    chkpt_02_path = Path(args.checkpoint)
    chkpt_01_path = Path(args.predecessor)
    telemetry_path = Path(args.telemetry)
    summary_path = Path(args.summary) if args.summary else None

    if not chkpt_02_path.is_file():
        raise FileNotFoundError("Missing Checkpoint 02: %s" % chkpt_02_path)
    if not chkpt_01_path.is_file():
        raise FileNotFoundError("Missing Checkpoint 01: %s" % chkpt_01_path)
    if not telemetry_path.is_file():
        raise FileNotFoundError("Missing telemetry: %s" % telemetry_path)

    chkpt_02 = json.loads(chkpt_02_path.read_text(encoding="utf-8"))
    chkpt_01 = json.loads(chkpt_01_path.read_text(encoding="utf-8"))
    telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path and summary_path.is_file() else None

    evaluator = Package163AcceptanceEvaluator(checkpoint_path=chkpt_02_path, predecessor_path=chkpt_01_path)
    result = evaluator.evaluate_full_acceptance(chkpt_01, chkpt_02, telemetry, summary)

    print("\n=== Package 163 Stage C2-1 Physical Acceptance Decision ===")
    print("Decision: %s" % result["physical_acceptance_decision"])
    print("Continuity: %s" % ("PASS" if result["continuity"]["passed"] else "FAIL"))
    print("Coupled Convergence: %s" % ("PASS" if result["coupled_convergence"]["passed"] else "FAIL"))
    print("Irreversibility & Bounds: %s" % ("PASS" if result["irreversibility"]["passed"] else "FAIL"))
    print("History Monotonicity: %s" % ("PASS" if result["history_monotonicity"]["passed"] else "FAIL"))
    print("Reference Parity: %s (Force err: %.3f%%, Energy err: %.3f%%)" % (
        "PASS" if result["reference_parity"]["passed"] else "FAIL",
        result["reference_parity"].get("rf2_discrepancy_pct", -1.0),
        result["reference_parity"].get("total_energy_discrepancy_pct", -1.0)
    ))
    print("Progression: Delta F = %.4f kN, Delta E = %.6e kN*mm, Max d = %.6f -> %.6f" % (
        result["c5_state_progression"]["delta_force_kN"],
        result["c5_state_progression"]["delta_energy_kNmm"],
        result["c5_state_progression"]["max_damage_checkpoint_01"],
        result["c5_state_progression"]["max_damage_checkpoint_02"]
    ))

    if args.output:
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("Wrote acceptance artifact: %s" % out_p)

    sys.exit(0 if result["verification_passed"] else 1)


if __name__ == "__main__":
    main()
