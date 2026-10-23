#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_c3_companion_deck.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: fbcc6f27-f8c5-4646-b45c-bbc02b5b241a
Protocol Version: 2

Generates the authentic companion continuum input deck for the C3 mesh:
models/pandey_kumar_mode1/91_c3_companion_miseseri/M1_C3_COMPANION_FRAME6.inp

Physics:
- Standard Abaqus CPE4 plane strain continuum elements on the 2650 physical quad elements
- Linear isotropic elasticity: E = 210.0 kN/mm^2 (210 GPa), nu = 0.3
- Slit flanks at y = 0.50 mm (x <= 0.040 mm) physically separated
- Bottom edge roller (U2 = 0) and pin (U1 = U2 = 0 at bottom left)
- Top edge kinematic coupling in DOF 2 to N_RP (node 999999), DOF 1 free
- Prescribed displacement at N_RP: U2 = 0.002036693 mm (matching Package 90-R1 Frame 6)
- Element output: S, MISESERI, MISESAVG, EVOL
"""

import os
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
C3_MESH_INP = REPO_ROOT / "models/pandey_kumar_mode1/90_r1_c3_active_set_transfer/candidate_crack_band_mesh_c3.inp"
OUT_DIR = REPO_ROOT / "models/pandey_kumar_mode1/91_c3_companion_miseseri"
OUT_INP = OUT_DIR / "M1_C3_COMPANION_FRAME6.inp"

FRAME6_U2_MM = 0.002036693040281534

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(C3_MESH_INP, "r", encoding="utf-8") as f:
        c3_text = f.read()

    # Extract nodes section
    nodes_part = c3_text.split("*Node\n")[1].split("** ==========================================================\n** LAYER 1")[0].strip()
    
    # Extract element definitions for quads 1..2650
    elem_part = c3_text.split("*Element, type=U1, elset=PHASE_QUADS\n")[1].split("** ==========================================================\n** LAYER 2")[0].strip()

    # Extract node sets and equations (strictly up to INITIAL BOUNDARY CONDITIONS)
    nsets_equations_part = c3_text.split("** NODE SETS & BOUNDARY CONDITIONS\n** ==========================================================\n")[1].split("** ==========================================================\n** INITIAL BOUNDARY CONDITIONS")[0].strip()

    companion_lines = [
        "*Heading",
        "** Mode-I C3 Companion Continuum Model for Authentic MISESERI Error Recovery",
        "** State: Package 90-R1 Step 4 Frame 6 Equivalent Loading (U2 = %.9f mm)" % FRAME6_U2_MM,
        "** Protocol Version: 2 (Task F1597)",
        "*Preprint, echo=NO, model=NO, history=NO, contact=NO",
        "** ----------------------------------------------------------",
        "** NODES (2769 physical nodes + RP 999999)",
        "** ----------------------------------------------------------",
        "*Node",
        nodes_part,
        "** ----------------------------------------------------------",
        "** CONTINUUM CPE4 ELEMENTS (2650 Quads)",
        "** ----------------------------------------------------------",
        "*Element, type=CPE4, elset=ALL_QUADS",
        elem_part,
        "** ----------------------------------------------------------",
        "** NODE SETS & EQUATIONS (Preserving Flanks & Coupling)",
        "** ----------------------------------------------------------",
        nsets_equations_part,
        "** ----------------------------------------------------------",
        "** SOLID SECTION & ISOTROPIC ELASTICITY",
        "** ----------------------------------------------------------",
        "*Solid Section, elset=ALL_QUADS, material=STEEL",
        "1.0",
        "*Material, name=STEEL",
        "*Elastic",
        "210.0, 0.3",
        "** ----------------------------------------------------------",
        "** BOUNDARY CONDITIONS & STATIC ELASTIC SOLVE",
        "** ----------------------------------------------------------",
        "*Boundary",
        "N_PIN, 1, 1, 0.0",
        "N_BOTTOM, 2, 2, 0.0",
        "999999, 1, 1, 0.0",
        "*Step, name=STATIC_ELASTIC, perturb",
        "*Static",
        "*Boundary",
        "999999, 2, 2, %.9f" % FRAME6_U2_MM,
        "** ----------------------------------------------------------",
        "** ELEMENT OUTPUT FOR AUTHENTIC MISESERI RECOVERY",
        "** ----------------------------------------------------------",
        "*Output, field, frequency=1",
        "*Element Output",
        "S, MISESERI, MISESAVG, EVOL",
        "*Node Output",
        "U, RF",
        "*Output, history, frequency=1",
        "*Node Output, nset=N_RP",
        "RF2, U2",
        "*End Step"
    ]

    with open(OUT_INP, "w", encoding="utf-8") as f:
        f.write("\n".join(companion_lines) + "\n")
    print("Wrote companion deck: %s (%d lines)" % (OUT_INP, len(companion_lines)))

if __name__ == "__main__":
    main()
