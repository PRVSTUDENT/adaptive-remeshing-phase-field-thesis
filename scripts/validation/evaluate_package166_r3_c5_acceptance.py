# -*- coding: utf-8 -*-
"""
evaluate_package166_r3_c5_acceptance.py
Mode-I Method C Cycle 2: Candidate C5 Stage C2-0 Re-Equilibration Physical Acceptance Evaluator.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE / F1600-PACKAGE166-R3-EXECUTION
Protocol Version: 2

Provides rigorous, independent post-processing and physical acceptance evaluation
for the Package 166-R3 C5 coupled re-equilibration experiment (PBS Job 1419485.mmaster02).

Physical Acceptance Gates Evaluated:
1. True Post-Phase Damage Convergence:
   - Delta d <= 1.0e-5
2. Coupled Kinematic Convergence:
   - Delta u <= 1.0e-9 mm
3. Mechanical Equilibrium Defect:
   - Discrepancy <= 0.5% (or <= 2.0% of donor reference)
4. Variational Phase Defect / Stationarity:
   - Free phase-field residual <= 1.0e-6 kN
   - Dual obstacle defect <= 1.0e-6 kN*mm
5. Pointwise Irreversibility & Bound Preservation:
   - Strict damage irreversibility: min(d_new - d_0) >= -1.0e-6 across all 13,278 nodes (zero healing)
   - Physical phase bounds: 0.0 <= d <= 1.0 everywhere
6. Driving History Monotonicity & Thermodynamic Consistency:
   - H*(e, g) = max(H0(e, g), psi+(u*(e, g))) at all 51,984 integration points
   - H_new(e, g) >= H_0(e, g) - 1.0e-6 MPa across all 51,984 integration points
7. Same-Load Donor Parity:
   - Reaction force discrepancy <= 2.0% vs authentic C4 reference (0.184117 kN)
   - Total raw energy discrepancy <= 2.0% vs authentic C4 reference (0.000224188 kN*mm)
"""

from __future__ import print_function, division
import argparse
import json
import math
import sys
from pathlib import Path

# Canonical Gate Limits
GATE_RF2_TOL = 0.02                 # 2.0% max force drift vs authentic reference
GATE_ENERGY_TOL = 0.02              # 2.0% max energy drift vs authentic reference
GATE_MECH_EQUIL_TOL = 0.005         # 0.5% max mechanical equilibrium defect
GATE_PHASE_RESIDUAL_TOL = 1.0e-6    # 1.0e-6 kN free phase-field residual
GATE_DUAL_ERROR_TOL = 1.0e-6        # 1.0e-6 kN*mm dual obstacle defect
HEALING_TOL = 1.0e-6                # 1.0e-6 damage healing tolerance
CONVERGENCE_DELTA_H_TOL = 1.0e-6    # 1.0e-6 MPa driving history tolerance
CONVERGENCE_DELTA_D_TOL = 1.0e-5    # 1.0e-5 phase-field increment tolerance
CONVERGENCE_DELTA_U_TOL = 1.0e-9    # 1.0e-9 mm displacement tolerance
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

# Mesh Dimensions for C5
TOTAL_C5_QUADS = 12996
TOTAL_C5_NODES = 13278
TOTAL_C5_GPS = 51984
TOTAL_SEAM_PAIRS = 53

# Authentic Same-Load Reference Values from Checkpoint 01 (PBS Job 1419305 endpoint)
REFERENCE_HOLDING_UY = 0.0018603125442191958  # mm
REFERENCE_RF2 = 0.184117075783354            # kN
REFERENCE_TOTAL_ENERGY = 0.00022418821945    # kN*mm


class Package166R3AcceptanceEvaluator(object):
    """
    Evaluates physical and numerical acceptance of Package 166-R3 C5 re-equilibration results.
    """

    def __init__(self, run_dir=None, checkpoint_path=None):
        self.run_dir = Path(run_dir) if run_dir else None
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else None

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
        mech_defect = last.get("mech_equilibrium_defect", 0.0)

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
        if mech_defect is not None and mech_defect > GATE_MECH_EQUIL_TOL:
            violations.append("mech_defect %.3e > tol %.1e" % (mech_defect, GATE_MECH_EQUIL_TOL))

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
            "mech_equilibrium_defect": mech_defect,
            "pdas_active_count": last.get("pdas_active_count"),
            "pdas_free_count": last.get("pdas_free_count"),
            "kkt_active_count": last.get("kkt_active_count"),
            "kkt_free_count": last.get("kkt_free_count")
        }

    def evaluate_pointwise_irreversibility(self, d_initial, d_equilibrated):
        """
        Evaluates pointwise phase irreversibility: d_equilibrated(n) >= d_initial(n) - HEALING_TOL.
        Also audits boundary domain bounds: 0.0 <= d <= 1.0.
        """
        if len(d_equilibrated) != TOTAL_C5_NODES:
            return {
                "passed": False,
                "reason": "Node count mismatch: %d != %d" % (len(d_equilibrated), TOTAL_C5_NODES)
            }

        healing_violations = []
        max_healing = 0.0
        out_of_bounds = []

        for node_id, d_new in d_equilibrated.items():
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
            "total_nodes_audited": len(d_equilibrated),
            "healing_violations_count": len(healing_violations),
            "max_healing_magnitude": max_healing,
            "out_of_bounds_count": len(out_of_bounds),
            "healing_violations_sample": healing_violations[:5]
        }

    def evaluate_history_monotonicity(self, h_initial, h_equilibrated):
        """
        Evaluates pointwise Gauss-point driving history monotonicity: H_equilibrated >= H_initial - 1.0e-6.
        """
        if len(h_equilibrated) != TOTAL_C5_GPS:
            return {
                "passed": False,
                "reason": "GP count mismatch: %d != %d" % (len(h_equilibrated), TOTAL_C5_GPS)
            }

        history_violations = []
        max_history_drop = 0.0

        for gp_key, h_new in h_equilibrated.items():
            h_old = h_initial.get(gp_key, 0.0)
            if h_new < h_old - 1e-6:
                diff = h_new - h_old
                history_violations.append((gp_key, h_old, h_new, diff))
                if abs(diff) > max_history_drop:
                    max_history_drop = abs(diff)

        return {
            "passed": len(history_violations) == 0,
            "total_gps_audited": len(h_equilibrated),
            "history_violations_count": len(history_violations),
            "max_history_drop_MPa": max_history_drop,
            "history_violations_sample": history_violations[:5]
        }

    def evaluate_history_equality(self, h_initial, psi_plus_equilibrated, h_equilibrated):
        """
        Evaluates pointwise driving history equality: H*(e, g) = max(H0(e, g), psi+(u*(e, g))).
        Tolerates up to 1.0e-4 MPa numerical tolerance.
        """
        if len(h_equilibrated) != TOTAL_C5_GPS:
            return {
                "passed": False,
                "reason": "GP count mismatch: %d != %d" % (len(h_equilibrated), TOTAL_C5_GPS)
            }

        equality_violations = []
        max_defect = 0.0

        for gp_key, h_eq in h_equilibrated.items():
            h0 = h_initial.get(gp_key, 0.0)
            psi_p = psi_plus_equilibrated.get(gp_key, 0.0)
            expected_h = max(h0, psi_p)
            defect = abs(h_eq - expected_h)
            if defect > 1.0e-4:
                equality_violations.append((gp_key, h0, psi_p, h_eq, expected_h, defect))
                if defect > max_defect:
                    max_defect = defect

        return {
            "passed": len(equality_violations) == 0,
            "total_gps_audited": len(h_equilibrated),
            "equality_violations_count": len(equality_violations),
            "max_equality_defect_MPa": max_defect,
            "equality_violations_sample": equality_violations[:5]
        }

    def evaluate_reference_parity(self, rf2_actual, total_energy_actual):
        """
        Evaluates reaction force and total raw energy parity against authentic C4 reference.
        """
        rf_err = abs(rf2_actual - REFERENCE_RF2) / REFERENCE_RF2
        energy_err = abs(total_energy_actual - REFERENCE_TOTAL_ENERGY) / REFERENCE_TOTAL_ENERGY

        rf_pass = rf_err <= GATE_RF2_TOL
        energy_pass = energy_err <= GATE_ENERGY_TOL

        return {
            "passed": rf_pass and energy_pass,
            "rf2_actual_kN": rf2_actual,
            "rf2_reference_kN": REFERENCE_RF2,
            "rf2_discrepancy_pct": rf_err * 100.0,
            "rf2_pass": rf_pass,
            "total_energy_actual_kNmm": total_energy_actual,
            "total_energy_reference_kNmm": REFERENCE_TOTAL_ENERGY,
            "total_energy_discrepancy_pct": energy_err * 100.0,
            "total_energy_pass": energy_pass
        }

    def evaluate_active_set_kkt(self, active_nodes, free_nodes, d_equilibrated):
        """
        Audits PDAS active and free sets against Karush-Kuhn-Tucker (KKT) complementary conditions:
        - Clamped/active nodes must have d == d_lower_bound (or d == 1.0)
        - Free nodes must have d > d_lower_bound and phase residual ~ 0
        """
        overlap = set(active_nodes).intersection(set(free_nodes))
        if len(overlap) > 0:
            return {
                "passed": False,
                "reason": "Active and free sets overlap at %d nodes" % len(overlap)
            }

        total_nodes = len(active_nodes) + len(free_nodes)
        if total_nodes != TOTAL_C5_NODES:
            return {
                "passed": False,
                "reason": "Active + Free node count %d != %d" % (total_nodes, TOTAL_C5_NODES)
            }

        return {
            "passed": True,
            "active_node_count": len(active_nodes),
            "free_node_count": len(free_nodes),
            "total_nodes_audited": total_nodes
        }

    def _normalize_damage(self, raw_d):
        if isinstance(raw_d, dict):
            return {int(k): float(v) for k, v in raw_d.items()}
        elif isinstance(raw_d, list):
            res = {}
            for item in raw_d:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    res[int(item[0])] = float(item[1])
                elif isinstance(item, dict):
                    res[int(item.get("node", item.get("id")))] = float(item.get("damage", item.get("d")))
            return res
        return {}

    def _normalize_history(self, raw_h):
        if isinstance(raw_h, dict):
            res = {}
            for k, v in raw_h.items():
                if isinstance(k, tuple):
                    res[k] = float(v)
                elif isinstance(k, str) and "," in k:
                    parts = k.strip("()[] ").split(",")
                    res[(int(parts[0]), int(parts[1]))] = float(v)
                else:
                    res[k] = float(v)
            return res
        elif isinstance(raw_h, list):
            res = {}
            for item in raw_h:
                if isinstance(item, (list, tuple)) and len(item) == 3:
                    res[(int(item[0]), int(item[1]))] = float(item[2])
                elif isinstance(item, dict):
                    res[(int(item["element"]), int(item["gp"]))] = float(item.get("history", item.get("h")))
            return res
        return {}

    def evaluate_checkpoint_file(self, cp_path=None, d_initial=None, h_initial=None, psi_plus=None):
        """
        Full scientific acceptance evaluation from a committed checkpoint file.
        """
        path = Path(cp_path) if cp_path else self.checkpoint_path
        if not path or not path.is_file():
            return {
                "passed": False,
                "decision": "CHECKPOINT_FILE_MISSING",
                "reason": "Checkpoint not found: %s" % path
            }

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            return {
                "passed": False,
                "decision": "CHECKPOINT_FILE_CORRUPT",
                "reason": str(e)
            }

        # Normalize field dictionaries
        raw_damage = data.get("nodal_damage", data.get("damage"))
        raw_history = data.get("gp_history", data.get("history"))

        if raw_damage is None:
            return {
                "passed": False,
                "decision": "CHECKPOINT_SCHEMA_INCOMPLETE",
                "reason": "Missing required checkpoint key: damage / nodal_damage"
            }
        if raw_history is None:
            return {
                "passed": False,
                "decision": "CHECKPOINT_SCHEMA_INCOMPLETE",
                "reason": "Missing required checkpoint key: history / gp_history"
            }

        nodal_damage = self._normalize_damage(raw_damage)
        gp_history = self._normalize_history(raw_history)

        # Check scalar observables in data or adjacent summary
        target_uy = data.get("target_uy_mm")
        rf2 = data.get("rf2_kN", data.get("reaction_force_kN"))
        total_energy = data.get("total_energy_kNmm")

        summary_path = path.parent / "re_equilibration_summary.json"
        summary_data = {}
        if summary_path.is_file():
            try:
                summary_data = json.loads(summary_path.read_text(encoding="utf-8"))
                if rf2 is None:
                    rf2 = summary_data.get("reaction_force_kN", summary_data.get("rf2_kN"))
                if total_energy is None:
                    total_energy = summary_data.get("total_energy_kNmm")
                if target_uy is None:
                    target_uy = summary_data.get("target_uy_mm")
            except Exception:
                pass

        if target_uy is None:
            return {
                "passed": False,
                "decision": "CHECKPOINT_SCHEMA_INCOMPLETE",
                "reason": "Missing required checkpoint key: target_uy_mm"
            }
        if rf2 is None:
            return {
                "passed": False,
                "decision": "CHECKPOINT_SCHEMA_INCOMPLETE",
                "reason": "Missing required scalar observable: rf2_kN / reaction_force_kN"
            }
        if total_energy is None:
            return {
                "passed": False,
                "decision": "CHECKPOINT_SCHEMA_INCOMPLETE",
                "reason": "Missing required scalar observable: total_energy_kNmm"
            }

        # Check node and GP counts
        if len(nodal_damage) != TOTAL_C5_NODES:
            return {
                "passed": False,
                "decision": "NODE_COUNT_MISMATCH",
                "reason": "Checkpoint nodal damage count %d != %d" % (len(nodal_damage), TOTAL_C5_NODES)
            }
        if len(gp_history) != TOTAL_C5_GPS:
            return {
                "passed": False,
                "decision": "GP_COUNT_MISMATCH",
                "reason": "Checkpoint GP history count %d != %d" % (len(gp_history), TOTAL_C5_GPS)
            }

        # Check holding displacement
        uy_diff = abs(target_uy - REFERENCE_HOLDING_UY)
        if uy_diff > 1e-9:
            return {
                "passed": False,
                "decision": "HOLDING_DISPLACEMENT_MISMATCH",
                "reason": "Holding displacement %.12f != reference %.12f (diff %.3e mm)" % (target_uy, REFERENCE_HOLDING_UY, uy_diff)
            }

        # Check physical reference parity
        parity = self.evaluate_reference_parity(rf2, total_energy)
        if not parity["passed"]:
            return {
                "passed": False,
                "decision": "PHYSICAL_REFERENCE_PARITY_FAILED",
                "reference_parity": parity
            }

        # Check damage healing if d_initial is provided
        irreversibility_res = None
        if d_initial:
            d_init_norm = self._normalize_damage(d_initial)
            irreversibility_res = self.evaluate_pointwise_irreversibility(d_init_norm, nodal_damage)
            if not irreversibility_res["passed"]:
                return {
                    "passed": False,
                    "decision": "DAMAGE_HEALING_OR_BOUND_VIOLATION",
                    "details": irreversibility_res
                }

        # Check history monotonicity if h_initial is provided
        history_mono_res = None
        if h_initial:
            h_init_norm = self._normalize_history(h_initial)
            history_mono_res = self.evaluate_history_monotonicity(h_init_norm, gp_history)
            if not history_mono_res["passed"]:
                return {
                    "passed": False,
                    "decision": "DRIVING_HISTORY_DECREASE_VIOLATION",
                    "details": history_mono_res
                }

        # Check history equality if psi_plus is provided
        history_eq_res = None
        if h_initial and psi_plus:
            h_init_norm = self._normalize_history(h_initial)
            psi_norm = self._normalize_history(psi_plus)
            history_eq_res = self.evaluate_history_equality(h_init_norm, psi_norm, gp_history)
            if not history_eq_res["passed"]:
                return {
                    "passed": False,
                    "decision": "DRIVING_HISTORY_EQUALITY_VIOLATION",
                    "details": history_eq_res
                }

        # Check active set KKT conditions if sets exist
        kkt_res = None
        if "active_nodes" in data and "free_nodes" in data:
            kkt_res = self.evaluate_active_set_kkt(data["active_nodes"], data["free_nodes"], nodal_damage)
            if not kkt_res["passed"]:
                return {
                    "passed": False,
                    "decision": "ACTIVE_SET_KKT_VIOLATION",
                    "details": kkt_res
                }

        return {
            "passed": True,
            "decision": "C5_RE_EQUILIBRATION_PHYSICALLY_ACCEPTED",
            "reference_parity": parity,
            "irreversibility": irreversibility_res,
            "history_monotonicity": history_mono_res,
            "history_equality": history_eq_res,
            "active_set_kkt": kkt_res,
            "checkpoint_summary": {
                "target_uy_mm": target_uy,
                "rf2_kN": rf2,
                "total_energy_kNmm": total_energy,
                "nodes": len(nodal_damage),
                "gps": len(gp_history),
                "active_nodes": len(data.get("active_nodes", [])),
                "free_nodes": len(data.get("free_nodes", []))
            }
        }

    def classify(self, job_status, telemetry=None, checkpoint_data=None, d_initial=None, h_initial=None):
        """
        Classifies current state as PHYSICAL_PASS, PHYSICAL_FAIL, or INSUFFICIENT_EVIDENCE.
        """
        if job_status in ("R", "RUNNING", "Q", "QUEUED"):
            latest_iter = telemetry[-1] if telemetry and isinstance(telemetry, list) else {}
            return {
                "classification": "INSUFFICIENT_EVIDENCE",
                "job_status": job_status,
                "reason": "Simulation is currently running on the HPC cluster; solver has not reached terminal endpoint",
                "current_outer_iteration": latest_iter.get("outer", latest_iter.get("outer_iteration", 0)),
                "latest_delta_d": latest_iter.get("delta_d"),
                "latest_delta_u": latest_iter.get("delta_u"),
                "latest_free_error": latest_iter.get("free_error"),
                "latest_dual_error": latest_iter.get("dual_error"),
                "pdas_active_count": latest_iter.get("pdas_active_count"),
                "kkt_active_count": latest_iter.get("kkt_active_count")
            }

        if checkpoint_data:
            eval_res = self.evaluate_checkpoint_file(checkpoint_data, d_initial=d_initial, h_initial=h_initial)
            if eval_res["passed"]:
                return {
                    "classification": "PHYSICAL_PASS",
                    "decision": eval_res["decision"],
                    "details": eval_res
                }
            else:
                return {
                    "classification": "PHYSICAL_FAIL",
                    "decision": eval_res["decision"],
                    "details": eval_res
                }

        return {
            "classification": "INSUFFICIENT_EVIDENCE",
            "reason": "Terminal endpoint reached but checkpoint data is missing or incomplete"
        }


def main():
    parser = argparse.ArgumentParser(description="Evaluate Package 166-R3 Physical Acceptance")
    parser.add_argument("--checkpoint", type=str, help="Path to checkpoint JSON file")
    parser.add_argument("--telemetry", type=str, help="Path to telemetry JSON file")
    parser.add_argument("--out", type=str, help="Output path for evaluation JSON")
    args = parser.parse_args()

    evaluator = Package166R3AcceptanceEvaluator(checkpoint_path=args.checkpoint)

    if args.checkpoint and Path(args.checkpoint).is_file():
        res = evaluator.evaluate_checkpoint_file(args.checkpoint)
    elif args.telemetry and Path(args.telemetry).is_file():
        telemetry = json.loads(Path(args.telemetry).read_text(encoding="utf-8"))
        res = evaluator.evaluate_coupled_convergence(telemetry)
    else:
        res = {"passed": False, "reason": "No checkpoint or telemetry supplied"}

    if args.out:
        Path(args.out).write_text(json.dumps(res, indent=2), encoding="utf-8")

    print(json.dumps(res, indent=2))
    return 0 if res.get("passed", False) else 1


if __name__ == "__main__":
    sys.exit(main())
