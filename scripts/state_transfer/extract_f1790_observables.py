# -*- coding: utf-8 -*-
"""
scripts/state_transfer/extract_f1790_observables.py
Task F1790 / F1791: Mode-I Method C Physical Observable Extraction Script (Repaired).

Maintains backward-compatible entrypoints for evaluate_physical_gates while forwarding
to the robust fail-closed implementation in extract_f1791_observables.py.
"""

import argparse
import csv
import json
import math
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from scripts.state_transfer.extract_f1791_observables import (
    DEFAULT_DONOR_REFERENCE,
    DEFAULT_THRESHOLDS,
    find_crack_tip_node_from_inp,
    parse_energy_csv,
    parse_reaction_force_dat,
    parse_residual_norm_msg,
    extract_damage_from_odb,
    evaluate_physical_gates as eval_gates_f1791,
    extract_all_observables,
)


def evaluate_physical_gates(
    solver_data: Dict[str, Any],
    donor_reference: Optional[Dict[str, float]] = None,
    output_json_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Evaluates Method C Gates C1-C5 against predeclared thresholds.
    Accepts both flat dictionary (legacy test format) and structured observation dictionary.
    """
    donor_ref = donor_reference or DEFAULT_DONOR_REFERENCE

    # If flat format was provided (legacy tests), convert to structured format
    structured_data = {}

    if "residual_norm" in solver_data:
        structured_data["residual_norm"] = solver_data["residual_norm"]
    elif "R_max_norm" in solver_data and solver_data["R_max_norm"] is not None:
        structured_data["residual_norm"] = {
            "found": True,
            "R_max_norm": solver_data["R_max_norm"],
            "R_max": solver_data.get("R_max", 0.0),
            "q_avg": solver_data.get("q_avg", 1.0),
        }

    if "reaction_force" in solver_data:
        structured_data["reaction_force"] = solver_data["reaction_force"]
    elif "RF2_N" in solver_data and solver_data["RF2_N"] is not None:
        structured_data["reaction_force"] = {
            "found": True,
            "RF2_N": solver_data["RF2_N"],
        }

    if "internal_energy" in solver_data:
        structured_data["internal_energy"] = solver_data["internal_energy"]
    elif "E_total_mJ" in solver_data and solver_data["E_total_mJ"] is not None:
        structured_data["internal_energy"] = {
            "found": True,
            "E_total_mJ": solver_data["E_total_mJ"],
        }

    if "damage_field" in solver_data:
        structured_data["damage_field"] = solver_data["damage_field"]
    elif "min_delta_d" in solver_data and solver_data["min_delta_d"] is not None:
        structured_data["damage_field"] = {
            "found": True,
            "min_delta_d": solver_data["min_delta_d"],
            "delta_d_tip": solver_data.get("delta_d_tip"),
            "tip_node": solver_data.get("tip_node", 209),
        }

    return eval_gates_f1791(structured_data, donor_ref, DEFAULT_THRESHOLDS, output_json_path)


def main():
    parser = argparse.ArgumentParser(description="Extract F1790/F1791 physical observables from Abaqus solver outputs.")
    parser.add_argument("--job-dir", type=Path, default=Path("."), help="Directory containing solver output files")
    parser.add_argument("--job-name", type=str, default="PK_F1790_CASE1_RELEASE_DIAGNOSTIC", help="Job name prefix")
    parser.add_argument("--inp-path", type=Path, default=None, help="Explicit input deck path for crack-tip resolution")
    parser.add_argument("--output-json", type=Path, default=Path("f1790_physical_gate_evaluation.json"), help="Output JSON path")
    args = parser.parse_args()

    solver_data = extract_all_observables(args.job_dir, args.job_name, args.inp_path)
    results = evaluate_physical_gates(solver_data, DEFAULT_DONOR_REFERENCE, args.output_json)
    print(f"Evaluation complete. Verdict: {results['verdict']}, All gates pass: {results['all_gates_pass']}")


if __name__ == "__main__":
    main()
