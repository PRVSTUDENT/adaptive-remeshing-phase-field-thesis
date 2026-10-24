#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_mode1_turn112_diagnostic_patch.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 112)
Constructs the genuine Abaqus 2023 input deck and initial lower bounds table
for the 4-element diagnostic patch verifying experimental irreversible UEL.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TARGET_DIR = REPO_ROOT / "models/pandey_kumar_mode1/104_experimental_irreversible_uel/diagnostic_patch"
TARGET_DIR.mkdir(parents=True, exist_ok=True)

# 1. d_lower_bounds.csv
# Format expected by f42_experimental_irreversible_uel.for:
# Header line (skipped by READ(107, *, END=26))
# EID_IN, D0(1..4), H0(1..4)
# Elem 1: [1, 2, 5, 4] -> Node 5 is local node 3
# Elem 2: [2, 3, 6, 5] -> Node 5 is local node 4
# Elem 3: [4, 5, 8, 7] -> Node 5 is local node 2
# Elem 4: [5, 6, 9, 8] -> Node 5 is local node 1
csv_lines = [
    "element_id,d0_1,d0_2,d0_3,d0_4,h0_1,h0_2,h0_3,h0_4\n",
    "1, 0.05, 0.05, 0.60, 0.05, 0.05, 0.05, 0.05, 0.05\n",
    "2, 0.05, 0.05, 0.05, 0.60, 0.05, 0.05, 0.05, 0.05\n",
    "3, 0.05, 0.60, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05\n",
    "4, 0.60, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05\n"
]
csv_path = TARGET_DIR / "d_lower_bounds.csv"
csv_path.write_text("".join(csv_lines), encoding="utf-8")
print(f"Created {csv_path}")

# 2. M1_DIAGNOSTIC_4ELEM_IRREV.inp
inp_text = """*Heading
** 4-Element Diagnostic Patch for Experimental Irreversible UEL
** Geometry: 0.10 x 0.10 mm (4 quads of 0.05 x 0.05 mm)
** Central node 5 shared by all 4 quads
** Properties: E=210.0 kN/mm^2, nu=0.3, Gc=0.0027 kN/mm, l0=0.015 mm, k=1.0e-7, N_PHYS=4
*Preprint, echo=NO, model=NO, history=NO, contact=NO
** ----------------------------------------------------------------
** USER ELEMENTS (Phase U1: DOF 3, Mech U2: DOFs 1, 2)
** ----------------------------------------------------------------
*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM
3
*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM
1, 2
** ----------------------------------------------------------------
** NODES (3x3 grid)
** ----------------------------------------------------------------
*Node
1, 0.000000, 0.000000
2, 0.050000, 0.000000
3, 0.100000, 0.000000
4, 0.000000, 0.050000
5, 0.050000, 0.050000
6, 0.100000, 0.050000
7, 0.000000, 0.100000
8, 0.050000, 0.100000
9, 0.100000, 0.100000
** ----------------------------------------------------------------
** LAYER 1: Phase Elements (Type U1: 1..4)
** ----------------------------------------------------------------
*Element, type=U1, elset=PHASE_QUADS
1, 1, 2, 5, 4
2, 2, 3, 6, 5
3, 4, 5, 8, 7
4, 5, 6, 9, 8
** ----------------------------------------------------------------
** LAYER 2: Mechanical Elements (Type U2: 5..8)
** ----------------------------------------------------------------
*Element, type=U2, elset=MECH_QUADS
5, 1, 2, 5, 4
6, 2, 3, 6, 5
7, 4, 5, 8, 7
8, 5, 6, 9, 8
** ----------------------------------------------------------------
** LAYER 3: Visualization CPE4 Elements (9..12)
** ----------------------------------------------------------------
*Element, type=CPE4, elset=VIS_QUADS
9,  1, 2, 5, 4
10, 2, 3, 6, 5
11, 4, 5, 8, 7
12, 5, 6, 9, 8
** ----------------------------------------------------------------
** NODE SETS
** ----------------------------------------------------------------
*Nset, nset=N_BOTTOM
1, 2, 3
*Nset, nset=N_TOP
7, 8, 9
*Nset, nset=N_PIN
1
*Nset, nset=N_CENTER
5
*Nset, nset=N_ALL
1, 2, 3, 4, 5, 6, 7, 8, 9
** ----------------------------------------------------------------
** UEL PROPERTIES (l0, Gc, E, nu, k, N_PHYS)
** ----------------------------------------------------------------
*UEL PROPERTY, ELSET=PHASE_QUADS
0.015, 0.0027, 210.0, 0.3, 1.0e-7, 4.
*UEL PROPERTY, ELSET=MECH_QUADS
0.015, 0.0027, 210.0, 0.3, 1.0e-7, 4.
** ----------------------------------------------------------------
** VISUALIZATION SOLID SECTION & UMAT
** ----------------------------------------------------------------
*Solid Section, elset=VIS_QUADS, material=DUMMY_MAT
1.0
*Material, name=DUMMY_MAT
*User Material, constants=3
210.0, 0.3, 4.
*Depvar
18
** ================================================================
** STEP 1: Stage-A Damage Retention (H = 0.05 kN/mm^2, u_y = 0.0018808 mm)
** ================================================================
*Step, name=Stage-A, nlgeom=NO, inc=20
*Static
1.0, 1.0, 1.0E-5, 1.0
*Boundary
N_BOTTOM, 2, 2, 0.0
N_PIN, 1, 1, 0.0
N_TOP, 1, 1, 0.0
N_TOP, 2, 2, 0.0018808
*Output, field, frequency=1
*Node Output
U, RF
*Element Output, elset=VIS_QUADS
SDV, S, E
*Output, history, frequency=1
*Energy Output
ALLSE, ALLIE, ALLWK, ALLFD, ALLCD, ALLVD, ALLPD, ALLAE, ETOTAL
*End Step
** ================================================================
** STEP 2: Stage-B Damage Advancement (H = 2.50 kN/mm^2, u_y = 0.01330 mm)
** ================================================================
*Step, name=Stage-B, nlgeom=NO, inc=50
*Static
0.2, 1.0, 1.0E-5, 0.2
*Boundary
N_TOP, 2, 2, 0.01330
*Output, field, frequency=1
*Node Output
U, RF
*Element Output, elset=VIS_QUADS
SDV, S, E
*Output, history, frequency=1
*Energy Output
ALLSE, ALLIE, ALLWK, ALLFD, ALLCD, ALLVD, ALLPD, ALLAE, ETOTAL
*End Step
"""

inp_path = TARGET_DIR / "M1_DIAGNOSTIC_4ELEM_IRREV.inp"
inp_path.write_text(inp_text, encoding="utf-8")
print(f"Created {inp_path}")
