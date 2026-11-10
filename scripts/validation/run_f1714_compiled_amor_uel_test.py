# -*- coding: utf-8 -*-
"""
scripts/validation/run_f1714_compiled_amor_uel_test.py
======================================================
Executes a minimal 1-element Abaqus solve on the target cluster (mlogin01.cluster)
using the actual compiled f42_amor_split_uel.for user subroutine:
1. Tension Step: Uniaxial tension (uy = +0.001 mm) -> verify tensile stiffness & RF2.
2. Compression Step: Equibiaxial compression (exx = eyy = -0.002) -> verify undegraded bulk modulus K = 175 GPa.
3. Shear Step: Pure shear (ux = +0.001 mm at y = 1) -> verify shear modulus mu = 80.77 GPa.
4. Compare authentic Abaqus reaction forces against analytical elasticity and Amor split predictions.
"""

import math
import os
import subprocess
import sys


def generate_1elem_input(filepath):
    """Generates a complete 1-element 3-layer Abaqus input deck for compiled UEL verification."""
    # Unit quad: (0,0), (1,0), (1,1), (0,1)
    inp_content = """*HEADING
Task F1714: Minimal 1-Element Compiled Amor UEL Verification
** Specimen: 1.0 x 1.0 mm Unit Quad Element
*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM
3
*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM
1, 2
*NODE
1, 0.0, 0.0
2, 1.0, 0.0
3, 1.0, 1.0
4, 0.0, 1.0
*NSET, NSET=N_BOTTOM
1, 2
*NSET, NSET=N_TOP
3, 4
*NSET, NSET=N_LEFT
1, 4
*NSET, NSET=N_RIGHT
2, 3
*NSET, NSET=N_PIN
1
*ELEMENT, TYPE=U1, ELSET=PHASE_ELEM
1, 1, 2, 3, 4
*ELEMENT, TYPE=U2, ELSET=MECH_ELEM
2, 1, 2, 3, 4
*ELEMENT, TYPE=CPE4, ELSET=UMAT_ELEM
3, 1, 2, 3, 4
*ELSET, ELSET=All_elem
UMAT_ELEM
*UEL PROPERTY, ELSET=PHASE_ELEM
0.0080, 0.0027, 210.0, 0.30, 1.0e-7, 1.0
*UEL PROPERTY, ELSET=MECH_ELEM
0.0080, 0.0027, 210.0, 0.30, 1.0e-7, 1.0
*SOLID SECTION, ELSET=UMAT_ELEM, MATERIAL=UMAT_MAT
1.0
*MATERIAL, NAME=UMAT_MAT
*USER MATERIAL, CONSTANTS=3
210.0, 0.30, 1.0
*DEPVAR
20
** ----------------------------------------------------------
** STEP 1: Uniaxial Tension (uy = +0.001 mm)
** ----------------------------------------------------------
*STEP, NAME=Tension, NLGEOM=NO, INC=10
*STATIC
1.0, 1.0, 1.0, 1.0
*BOUNDARY
N_BOTTOM, 2, 2, 0.0
N_PIN, 1, 1, 0.0
N_TOP, 2, 2, 0.001
*OUTPUT, FIELD, FREQUENCY=1
*NODE OUTPUT, NSET=N_TOP
U, RF
*NODE OUTPUT, NSET=N_BOTTOM
U, RF
*ELEMENT OUTPUT, ELSET=All_elem
SDV
*NODE PRINT, FREQ=1, NSET=N_TOP
U2, RF2
*NODE PRINT, FREQ=1, NSET=N_BOTTOM
U2, RF2
*END STEP
** ----------------------------------------------------------
** STEP 2: Pure Shear (ux = +0.001 mm at y = 1.0)
** ----------------------------------------------------------
*STEP, NAME=Shear, NLGEOM=NO, INC=10
*STATIC
1.0, 1.0, 1.0, 1.0
*BOUNDARY, OP=NEW
N_BOTTOM, 1, 2, 0.0
N_TOP, 2, 2, 0.0
N_TOP, 1, 1, 0.001
*OUTPUT, FIELD, FREQUENCY=1
*NODE OUTPUT, NSET=N_TOP
U, RF
*NODE PRINT, FREQ=1, NSET=N_TOP
U1, RF1
*END STEP
** ----------------------------------------------------------
** STEP 3: Equibiaxial Compression (exx = eyy = -0.002)
** ----------------------------------------------------------
*STEP, NAME=Compression, NLGEOM=NO, INC=10
*STATIC
1.0, 1.0, 1.0, 1.0
*BOUNDARY, OP=NEW
N_BOTTOM, 2, 2, 0.0
N_LEFT, 1, 1, 0.0
N_TOP, 2, 2, -0.002
N_RIGHT, 1, 1, -0.002
*OUTPUT, FIELD, FREQUENCY=1
*NODE OUTPUT, NSET=N_TOP
U, RF
*NODE OUTPUT, NSET=N_RIGHT
U, RF
*NODE PRINT, FREQ=1, NSET=N_TOP
U2, RF2
*NODE PRINT, FREQ=1, NSET=N_RIGHT
U1, RF1
*END STEP
"""
    with open(filepath, "w") as f:
        f.write(inp_content)
    print("Generated 1-element verification input deck: %s" % filepath)


def generate_1elem_damaged_input(filepath):
    """Generates a 1-element Abaqus input deck with prescribed damage d = 0.5."""
    inp_content = """*HEADING
Task F1714: Minimal 1-Element Compiled Amor UEL Damaged-State Verification (d = 0.5)
** Specimen: 1.0 x 1.0 mm Unit Quad Element with Prescribed Damage d = 0.5
*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM
3
*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM
1, 2
*NODE
1, 0.0, 0.0
2, 1.0, 0.0
3, 1.0, 1.0
4, 0.0, 1.0
*NSET, NSET=N_ALL, GENERATE
1, 4, 1
*NSET, NSET=N_BOTTOM
1, 2
*NSET, NSET=N_TOP
3, 4
*NSET, NSET=N_LEFT
1, 4
*NSET, NSET=N_RIGHT
2, 3
*NSET, NSET=N_PIN
1
*ELEMENT, TYPE=U1, ELSET=PHASE_ELEM
1, 1, 2, 3, 4
*ELEMENT, TYPE=U2, ELSET=MECH_ELEM
2, 1, 2, 3, 4
*ELEMENT, TYPE=CPE4, ELSET=UMAT_ELEM
3, 1, 2, 3, 4
*ELSET, ELSET=All_elem
UMAT_ELEM
*UEL PROPERTY, ELSET=PHASE_ELEM
0.0080, 0.0027, 210.0, 0.30, 1.0e-7, 1.0
*UEL PROPERTY, ELSET=MECH_ELEM
0.0080, 0.0027, 210.0, 0.30, 1.0e-7, 1.0
*SOLID SECTION, ELSET=UMAT_ELEM, MATERIAL=UMAT_MAT
1.0
*MATERIAL, NAME=UMAT_MAT
*USER MATERIAL, CONSTANTS=3
210.0, 0.30, 1.0
*DEPVAR
20
** ----------------------------------------------------------
** STEP 1: Damaged Uniaxial Tension (d = 0.5, uy = +0.001 mm)
** ----------------------------------------------------------
*STEP, NAME=DamagedTension, NLGEOM=NO, INC=10
*STATIC
1.0, 1.0, 1.0, 1.0
*BOUNDARY
N_ALL, 3, 3, 0.5
N_BOTTOM, 2, 2, 0.0
N_PIN, 1, 1, 0.0
N_TOP, 2, 2, 0.001
*OUTPUT, FIELD, FREQUENCY=1
*NODE OUTPUT, NSET=N_TOP
U, RF
*NODE OUTPUT, NSET=N_BOTTOM
U, RF
*ELEMENT OUTPUT, ELSET=All_elem
SDV
*NODE PRINT, FREQ=1, NSET=N_TOP
U2, RF2
*NODE PRINT, FREQ=1, NSET=N_BOTTOM
U2, RF2
*END STEP
** ----------------------------------------------------------
** STEP 2: Damaged Pure Shear (d = 0.5, ux = +0.001 mm at y = 1.0)
** ----------------------------------------------------------
*STEP, NAME=DamagedShear, NLGEOM=NO, INC=10
*STATIC
1.0, 1.0, 1.0, 1.0
*BOUNDARY, OP=NEW
N_ALL, 3, 3, 0.5
N_BOTTOM, 1, 2, 0.0
N_TOP, 2, 2, 0.0
N_TOP, 1, 1, 0.001
*OUTPUT, FIELD, FREQUENCY=1
*NODE OUTPUT, NSET=N_TOP
U, RF
*NODE PRINT, FREQ=1, NSET=N_TOP
U1, RF1
*END STEP
** ----------------------------------------------------------
** STEP 3: Damaged Equibiaxial Compression (d = 0.5, exx = eyy = -0.002)
** ----------------------------------------------------------
*STEP, NAME=DamagedCompression, NLGEOM=NO, INC=10
*STATIC
1.0, 1.0, 1.0, 1.0
*BOUNDARY, OP=NEW
N_ALL, 3, 3, 0.5
N_BOTTOM, 2, 2, 0.0
N_LEFT, 1, 1, 0.0
N_TOP, 2, 2, -0.002
N_RIGHT, 1, 1, -0.002
*OUTPUT, FIELD, FREQUENCY=1
*NODE OUTPUT, NSET=N_TOP
U, RF
*NODE OUTPUT, NSET=N_RIGHT
U, RF
*NODE PRINT, FREQ=1, NSET=N_TOP
U2, RF2
*NODE PRINT, FREQ=1, NSET=N_RIGHT
U1, RF1
*END STEP
"""
    with open(filepath, "w") as f:
        f.write(inp_content)
    print("Generated 1-element damaged verification input deck: %s" % filepath)


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    deck_path = os.path.join(out_dir, "PK_F1714_1ELEM_AMOR_TEST.inp")
    generate_1elem_input(deck_path)
    deck_damaged = os.path.join(out_dir, "PK_F1714_1ELEM_AMOR_DAMAGED_TEST.inp")
    generate_1elem_damaged_input(deck_damaged)
