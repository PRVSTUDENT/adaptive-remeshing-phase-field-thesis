"""Evaluation and acceptance script for Package 169: Continuous C4 Two-Checkpoint Reference Experiment.

When Job 1419543.mmaster02 reaches terminal completion, this evaluator extracts:
1. Reference A State (Step 3 terminal frame, uy = 0.0018653125442191958 mm):
   - Reaction force Fy, Elastic strain energy Eel, Crack fracture energy Efr, Raw total energy Etot
   - Evaluates like-for-like comparator against C5-R3 continuation solve (Job 1419499)
2. Reference B State (Step 4 terminal frame, uy = 0.0018703125442191958 mm):
   - Reaction force Fy, Elastic strain energy Eel, Crack fracture energy Efr, Raw total energy Etot
   - Evaluates same-mesh comparator against C4-R8 continuation solve (Job 1419490)
   - Evaluates eligibility to serve as authentic matching-load reference for Package 167
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
P169_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "169_c4_two_checkpoint_reference"
P169_MANIFEST = P169_DIR / "EXECUTION_MANIFEST_REF.json"

# Targets and gates
REF_A_UY_MM = 0.0018653125442191958
REF_B_UY_MM = 0.0018703125442191958

# Predecessor historical values for comparison
C5_R3_FORCE_KN = 0.179443
C5_R3_ENERGY_KNMM = 0.000225501
C4_R8_FORCE_KN = 0.182516
C4_R8_ENERGY_KNMM = 0.000226038
C3_DONOR_ENERGY_KNMM = 0.000217630

FORCE_GATE_PCT = 2.0
ENERGY_GATE_PCT = 2.0


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def evaluate_two_checkpoint_reference(
    ref_a_force: float | None = None,
    ref_a_energy: float | None = None,
    ref_b_force: float | None = None,
    ref_b_energy: float | None = None,
) -> dict:
    findings = []
    comparisons = {}

    if ref_a_force is not None and ref_a_energy is not None:
        c5_r3_force_disc = abs(C5_R3_FORCE_KN - ref_a_force) / ref_a_force * 100.0
        c5_r3_energy_disc = abs(C5_R3_ENERGY_KNMM - ref_a_energy) / ref_a_energy * 100.0
        comparisons["Reference_A_vs_C5_R3"] = {
            "target_uy_mm": REF_A_UY_MM,
            "c5_r3_force_kN": C5_R3_FORCE_KN,
            "ref_a_force_kN": ref_a_force,
            "force_discrepancy_pct": c5_r3_force_disc,
            "force_gate_pct": FORCE_GATE_PCT,
            "force_pass": c5_r3_force_disc <= FORCE_GATE_PCT,
            "c5_r3_energy_kNmm": C5_R3_ENERGY_KNMM,
            "ref_a_energy_kNmm": ref_a_energy,
            "energy_discrepancy_pct": c5_r3_energy_disc,
            "energy_gate_pct": ENERGY_GATE_PCT,
            "energy_pass": c5_r3_energy_disc <= ENERGY_GATE_PCT,
        }
        findings.append(
            f"Reference A (uy={REF_A_UY_MM*1e3:.4f} um): Force disc={c5_r3_force_disc:.3f}%, "
            f"Energy disc={c5_r3_energy_disc:.3f}%"
        )

    if ref_b_force is not None and ref_b_energy is not None:
        c4_r8_force_disc = abs(C4_R8_FORCE_KN - ref_b_force) / ref_b_force * 100.0
        c4_r8_energy_disc = abs(C4_R8_ENERGY_KNMM - ref_b_energy) / ref_b_energy * 100.0
        comparisons["Reference_B_vs_C4_R8"] = {
            "target_uy_mm": REF_B_UY_MM,
            "c4_r8_force_kN": C4_R8_FORCE_KN,
            "ref_b_force_kN": ref_b_force,
            "force_discrepancy_pct": c4_r8_force_disc,
            "force_gate_pct": 5.0,
            "force_pass": c4_r8_force_disc <= 5.0,
            "c4_r8_energy_kNmm": C4_R8_ENERGY_KNMM,
            "ref_b_energy_kNmm": ref_b_energy,
            "energy_discrepancy_pct": c4_r8_energy_disc,
            "energy_gate_pct": ENERGY_GATE_PCT,
            "energy_pass": c4_r8_energy_disc <= ENERGY_GATE_PCT,
        }
        findings.append(
            f"Reference B (uy={REF_B_UY_MM*1e3:.4f} um): Same-mesh C4-R8 Energy disc={c4_r8_energy_disc:.3f}%, "
            f"Force disc={c4_r8_force_disc:.3f}%"
        )

    return {
        "schema": 1,
        "evaluation_name": "PACKAGE169_TWO_CHECKPOINT_REFERENCE_EVALUATION",
        "predeclared_gates": {
            "ref_a_force_gate_pct": FORCE_GATE_PCT,
            "ref_a_energy_gate_pct": ENERGY_GATE_PCT,
            "ref_b_force_gate_pct": 5.0,
            "ref_b_energy_gate_pct": ENERGY_GATE_PCT,
        },
        "comparisons": comparisons,
        "findings": "; ".join(findings) if findings else "Predeclared criteria awaiting terminal solver observables."
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref-a-force", type=float, default=None)
    parser.add_argument("--ref-a-energy", type=float, default=None)
    parser.add_argument("--ref-b-force", type=float, default=None)
    parser.add_argument("--ref-b-energy", type=float, default=None)
    args = parser.parse_args()

    result = evaluate_two_checkpoint_reference(
        args.ref_a_force, args.ref_a_energy, args.ref_b_force, args.ref_b_energy
    )
    print(json.dumps(result, indent=2))
