# -*- coding: utf-8 -*-
"""
cycle_data_audit_schema.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Standardized reproducible cycle-data audit schema and descriptive H1 classifier
for Alternating Minimization (AM) / Primal-Dual Active-Set (PDAS) staggered solvers.
"""

from __future__ import print_function, division
import math

CYCLE_SCHEMA_FIELDS = [
    "cycle",
    "uRP_mm",
    "RF2_N",
    "delta_RF2_N",
    "mechanical_residual_kN",
    "dmax",
    "delta_d_Linf",
    "free_phase_residual_kN_per_mm",
    "active_KKT_min_kN_per_mm",
    "healing_count",
    "active_free_nodes",
    "Eelas_mJ",
    "Efrac_local_mJ",
    "Efrac_gradient_mJ",
    "Etotal_mJ",
    "committed_history_status",
    "solver_status",
]

MIN_NUMERICAL_DENOMINATOR = 1.0e-12


def validate_cycle_record(rec):
    """
    Validates a single cycle record against the cycle schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    for f in CYCLE_SCHEMA_FIELDS:
        if f not in rec:
            errors.append("Missing required field: %s" % f)
    if errors:
        return False, errors

    # Check numeric types
    int_fields = ["cycle", "healing_count", "active_free_nodes"]
    float_fields = [
        "uRP_mm", "RF2_N", "delta_RF2_N", "mechanical_residual_kN",
        "dmax", "delta_d_Linf", "free_phase_residual_kN_per_mm",
        "active_KKT_min_kN_per_mm", "Eelas_mJ", "Efrac_local_mJ",
        "Efrac_gradient_mJ", "Etotal_mJ"
    ]
    str_fields = ["committed_history_status", "solver_status"]

    for f in int_fields:
        if rec[f] is not None and not isinstance(rec[f], (int,)):
            # allow int-like float
            if isinstance(rec[f], float) and rec[f].is_integer():
                pass
            else:
                errors.append("Field %s must be int, got %s" % (f, type(rec[f])))

    for f in float_fields:
        if rec[f] is not None and not isinstance(rec[f], (int, float)):
            errors.append("Field %s must be float, got %s" % (f, type(rec[f])))

    for f in str_fields:
        if rec[f] is not None and not isinstance(rec[f], (str,)):
            errors.append("Field %s must be str, got %s" % (f, type(rec[f])))

    return len(errors) == 0, errors


def compute_contraction_factors(cycle_records):
    """
    Computes consecutive-cycle contraction factors:
      rho_d = delta_d_Linf^(k) / delta_d_Linf^(k-1)
      rho_F = |delta_RF2_N^(k)| / |delta_RF2_N^(k-1)|
    Factors are computed ONLY when denominators are positive and >= MIN_NUMERICAL_DENOMINATOR.
    Missing or non-calculable values remain None (explicitly missing, not fabricated zeros).
    """
    augmented = []
    for i, rec in enumerate(cycle_records):
        item = dict(rec)
        if i == 0:
            item["rho_d"] = None
            item["rho_F"] = None
        else:
            prev = cycle_records[i - 1]
            # rho_d
            d_curr = rec.get("delta_d_Linf")
            d_prev = prev.get("delta_d_Linf")
            if (d_curr is not None and d_prev is not None and
                    d_prev >= MIN_NUMERICAL_DENOMINATOR):
                item["rho_d"] = float(d_curr / d_prev)
            else:
                item["rho_d"] = None

            # rho_F
            f_curr = abs(rec.get("delta_RF2_N", 0.0)) if rec.get("delta_RF2_N") is not None else None
            f_prev = abs(prev.get("delta_RF2_N", 0.0)) if prev.get("delta_RF2_N") is not None else None
            if (f_curr is not None and f_prev is not None and
                    f_prev >= MIN_NUMERICAL_DENOMINATOR):
                item["rho_F"] = float(f_curr / f_prev)
            else:
                item["rho_F"] = None
        augmented.append(item)
    return augmented


def classify_descriptive_h1(cycle_records):
    """
    Predeclared descriptive H1 classification criteria:
    - SUSTAINED_CONTRACTION_SUPPORTED:
        Both update magnitudes (delta_d_Linf and |delta_RF2_N|) decrease across
        the final five available cycles, with geometric-mean contraction factors below 0.95.
    - LOSS_OF_CONTRACTION_DETECTED:
        Both factors exceed 1.0 across at least three consecutive cycles.
    - INCONCLUSIVE:
        Any other pattern or insufficient telemetry.

    Note: These criteria classify observed iteration behavior, not mathematical
    existence or nonexistence of equilibrium.
    """
    augmented = compute_contraction_factors(cycle_records)
    n = len(augmented)

    # Check loss of contraction: both rho_d > 1.0 and rho_F > 1.0 for at least 3 consecutive cycles
    consecutive_expansion_count = 0
    max_consecutive_expansion = 0
    expansion_start_cycle = None

    for rec in augmented:
        rho_d = rec.get("rho_d")
        rho_F = rec.get("rho_F")
        if rho_d is not None and rho_F is not None and rho_d > 1.0 and rho_F > 1.0:
            consecutive_expansion_count += 1
            if consecutive_expansion_count > max_consecutive_expansion:
                max_consecutive_expansion = consecutive_expansion_count
                if expansion_start_cycle is None:
                    expansion_start_cycle = rec["cycle"]
        else:
            consecutive_expansion_count = 0
            expansion_start_cycle = None

    if max_consecutive_expansion >= 3:
        return {
            "classification": "LOSS_OF_CONTRACTION_DETECTED",
            "consecutive_expansion_cycles": max_consecutive_expansion,
            "scientific_interpretation": (
                "Three or more consecutive expansion factors demonstrate loss of contraction "
                "over those cycles, but do not mathematically prove that no stationary equilibrium "
                "exists or that additional iterations could never converge under a different scheme."
            ),
            "h1_hypothesis_verdict": "REFUTED_OBSERVED_BEHAVIOR",
            "extended_retry_supported": False
        }

    # Check sustained contraction over final 5 cycles
    if n >= 6: # need at least 6 records to have 5 consecutive rho values
        final_5 = augmented[-5:]
        all_rho_d = [r.get("rho_d") for r in final_5]
        all_rho_F = [r.get("rho_F") for r in final_5]

        if all(r is not None and r < 1.0 for r in all_rho_d) and all(r is not None and r < 1.0 for r in all_rho_F):
            # Geometric mean
            geo_mean_d = math.exp(sum(math.log(r) for r in all_rho_d) / 5.0)
            geo_mean_F = math.exp(sum(math.log(r) for r in all_rho_F) / 5.0)
            if geo_mean_d < 0.95 and geo_mean_F < 0.95:
                return {
                    "classification": "SUSTAINED_CONTRACTION_SUPPORTED",
                    "geo_mean_rho_d": geo_mean_d,
                    "geo_mean_rho_F": geo_mean_F,
                    "scientific_interpretation": (
                        "Both update magnitudes decrease across the final five cycles with geometric-mean "
                        "contraction below 0.95, indicating asymptotic contraction toward stationarity."
                    ),
                    "h1_hypothesis_verdict": "SUPPORTED_OBSERVED_BEHAVIOR",
                    "extended_retry_supported": True
                }

    return {
        "classification": "INCONCLUSIVE",
        "consecutive_expansion_cycles": max_consecutive_expansion,
        "scientific_interpretation": (
            "Observed convergence updates do not meet either the sustained contraction threshold "
            "or the loss-of-contraction threshold; sequence is inconclusive."
        ),
        "h1_hypothesis_verdict": "INCONCLUSIVE",
        "extended_retry_supported": False
    }
