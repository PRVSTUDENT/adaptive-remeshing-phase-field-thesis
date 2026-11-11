# -*- coding: utf-8 -*-
"""
scripts/method_a_framework/pipeline.py
======================================
Unified Entry Point for the Reusable Method A Adaptive-Remeshing Framework.

Executes the complete workflow:
1. Input validation & configuration checking.
2. Geometry & topology audit.
3. Pre-analysis error indicator processing.
4. Adaptive production deck generation.
5. Post-simulation extraction & thermodynamic verification.
6. Publication figure generation.
7. Machine-readable validation report export.
"""

import os
import sys
import json
import hashlib

from .config import FrameworkConfig
from .input_validator import InputModelValidator
from .indicator import MiseseriIndicator
from .deck_builder import ProductionDeckBuilder
from .postprocessor import SimulationPostprocessor
from .visualizer import FrameworkVisualizer


def compute_file_sha256(filepath):
    if not os.path.isfile(filepath):
        return ""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


class MethodAFrameworkPipeline(object):
    """
    Main orchestration class for the Method A Adaptive-Remeshing Framework.
    """

    def __init__(self, config_or_path):
        if isinstance(config_or_path, FrameworkConfig):
            self.config = config_or_path
        elif isinstance(config_or_path, str):
            self.config = FrameworkConfig.load(config_or_path)
        elif isinstance(config_or_path, dict):
            self.config = FrameworkConfig(config_or_path)
            self.config.validate()
        else:
            raise TypeError("Expected FrameworkConfig, filepath string, or dict.")

        self.validator = None
        self.indicator = None
        self.deck_builder = None
        self.postprocessor = None
        self.visualizer = FrameworkVisualizer(self.config)
        self.execution_record = {}

    def run_preprocessing_and_deck_generation(self, coarse_inp_path, adapted_phys_inp_path, output_prod_inp_path):
        """
        Executes Stages 1-8 of the Method A workflow:
        1. Validates coarse mesh geometry & topology.
        2. Validates adapted physical mesh.
        3. Constructs 3-layer production deck.
        Returns execution summary dict.
        """
        print("=== [Method A Framework] Stage 1-2: Validating Coarse Input Deck ===")
        coarse_val = InputModelValidator(coarse_inp_path)
        coarse_summary = coarse_val.parse()
        print("Coarse Mesh: %d elements (%d quads, %d tris), %d nodes" % (
            coarse_summary["element_count"], coarse_summary["quad_count"],
            coarse_summary["tri_count"], coarse_summary["node_count"]
        ))

        print("\n=== [Method A Framework] Stage 3-5: Validating Adapted Physical Mesh ===")
        phys_val = InputModelValidator(adapted_phys_inp_path)
        phys_summary = phys_val.parse()
        print("Adapted Physical Mesh: %d elements (%d quads, %d tris), %d nodes" % (
            phys_summary["element_count"], phys_summary["quad_count"],
            phys_summary["tri_count"], phys_summary["node_count"]
        ))
        print("Mesh Quality: det(J) > 0: %s, aspect ratio min/mean/max: %.2f / %.2f / %.2f" % (
            phys_summary["quality"]["all_jacobians_positive"],
            phys_summary["quality"]["aspect_ratio_min"],
            phys_summary["quality"]["aspect_ratio_mean"],
            phys_summary["quality"]["aspect_ratio_max"]
        ))

        print("\n=== [Method A Framework] Stage 6-8: Building 3-Layer Production Deck ===")
        self.deck_builder = ProductionDeckBuilder(adapted_phys_inp_path, self.config)
        deck_summary = self.deck_builder.build_deck(output_prod_inp_path)
        print("Production Deck generated at: %s" % output_prod_inp_path)
        print("Layered elements: %d, Nodes: %d (including reference node)" % (
            deck_summary["layered_elements"], deck_summary["nodes"]
        ))

        self.execution_record["preprocessing"] = {
            "coarse_mesh": coarse_summary,
            "adapted_physical_mesh": phys_summary,
            "production_deck": deck_summary,
            "production_deck_sha256": compute_file_sha256(output_prod_inp_path)
        }
        return self.execution_record["preprocessing"]

    def run_postprocessing_and_validation(self, raw_telemetry_or_json, out_report_json=None):
        """
        Executes Stages 10-11 of the Method A workflow:
        Validates reaction force equilibrium, domain energies, and damage bounds.
        """
        if isinstance(raw_telemetry_or_json, str) and os.path.isfile(raw_telemetry_or_json):
            with open(raw_telemetry_or_json, "r") as f:
                telemetry = json.load(f)
        elif isinstance(raw_telemetry_or_json, dict):
            telemetry = raw_telemetry_or_json
        else:
            raise ValueError("Invalid telemetry input; expected file path or dictionary.")

        print("\n=== [Method A Framework] Stage 10-11: Postprocessing & Verification ===")
        self.postprocessor = SimulationPostprocessor(self.config)
        post_summary = self.postprocessor.process_telemetry(telemetry)
        print("Peak Force: %.4f kN at u = %.4f mm, Initial Stiffness: %.2f kN/mm" % (
            post_summary["peak_force_kN"], post_summary["displacement_at_peak_mm"],
            post_summary["initial_stiffness_kN_per_mm"]
        ))
        print("External Work: %.6f kN*mm (J)" % post_summary["external_work_kNmm"])

        self.execution_record["validation"] = post_summary
        if out_report_json:
            with open(out_report_json, "w") as f:
                json.dump(self.execution_record, f, indent=2)
            print("Validation report saved to: %s" % out_report_json)

        return post_summary
