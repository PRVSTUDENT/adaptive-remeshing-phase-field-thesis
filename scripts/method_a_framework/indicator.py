# -*- coding: utf-8 -*-
"""
scripts/method_a_framework/indicator.py
=======================================
Superconvergent Patch Recovery (SPR) error indicator extraction and sizing field calculation
for the Reusable Method A Adaptive-Remeshing Framework.
"""

import os
import json
import math


class MiseseriIndicator(object):
    """
    Manages extraction and normalization of the MISESERI recovery-based
    stress discretization error indicator.
    """

    def __init__(self, config):
        self.config = config
        self.raw_indicator_data = {}   # eid -> {"miseseri": ..., "misesavg": ..., "eta_e": ...}
        self.global_stats = {}

    def load_from_field_data(self, element_records):
        """
        Loads indicator data from a list of element records:
        each record: {"element_id": int, "miseseri": float, "misesavg": float}
        """
        self.raw_indicator_data = {}
        miseseri_vals = []
        misesavg_vals = []
        eta_vals = []

        target_pct = self.config.remeshing["error_target_pct"]
        exceeding_count = 0

        for r in element_records:
            eid = int(r["element_id"])
            eri = float(r["miseseri"])
            avg = float(r["misesavg"])
            eta = (eri / avg * 100.0) if avg > 1.0e-12 else 0.0

            if eta > target_pct:
                exceeding_count += 1

            self.raw_indicator_data[eid] = {
                "miseseri": eri,
                "misesavg": avg,
                "eta_e": eta
            }
            miseseri_vals.append(eri)
            misesavg_vals.append(avg)
            eta_vals.append(eta)

        n_elem = len(self.raw_indicator_data)
        self.global_stats = {
            "element_count": n_elem,
            "error_target_pct": target_pct,
            "elements_exceeding_target": exceeding_count,
            "fraction_exceeding_target": round(exceeding_count / float(n_elem), 4) if n_elem > 0 else 0.0,
            "miseseri_min": round(min(miseseri_vals), 4) if miseseri_vals else 0.0,
            "miseseri_mean": round(sum(miseseri_vals) / len(miseseri_vals), 4) if miseseri_vals else 0.0,
            "miseseri_max": round(max(miseseri_vals), 4) if miseseri_vals else 0.0,
            "eta_min": round(min(eta_vals), 4) if eta_vals else 0.0,
            "eta_mean": round(sum(eta_vals) / len(eta_vals), 4) if eta_vals else 0.0,
            "eta_max": round(max(eta_vals), 4) if eta_vals else 0.0
        }
        return self.global_stats

    def compute_target_sizing(self, h_coarse=0.020, convergence_rate=1.0):
        """
        Computes local target element size h_e for each element based on:
        h_e = h_coarse * (eta_target / eta_e)**(1.0 / p)
        clamped to [h_min, h_max].
        """
        h_min = self.config.remeshing["h_min"]
        h_max = self.config.remeshing["h_max"]
        target = self.config.remeshing["error_target_pct"]

        sizing_field = {}
        for eid, edata in self.raw_indicator_data.items():
            eta = edata["eta_e"]
            if eta <= 1.0e-9:
                h_target = h_max
            else:
                ratio = target / eta
                h_target = h_coarse * (ratio ** (1.0 / convergence_rate))
                h_target = max(h_min, min(h_max, h_target))
            sizing_field[eid] = round(h_target, 6)

        return sizing_field

    def export_json(self, json_path):
        payload = {
            "benchmark": self.config.benchmark_name,
            "global_stats": self.global_stats,
            "elements": self.raw_indicator_data
        }
        with open(json_path, "w") as f:
            json.dump(payload, f, indent=2)
        return json_path
