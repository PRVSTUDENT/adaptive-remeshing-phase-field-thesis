#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_experimental_uel_regularization.py
Updates models/pandey_kumar_mode1/105_c3_irreversible_continuation/f42_experimental_irreversible_uel.for
with the C1-smooth Huber regularized active-set penalty formulation:
- GAMMA_PEN = 10.0D0 (calibrated penalty stiffness, condition number ~ 1e4)
- DELTA_PEN = 1.0D-4 (transition band width)
- C1-smooth quadratic transition for 0 < delta_d < DELTA_PEN
- Linear penalty for delta_d >= DELTA_PEN
- Zero jumps in tangent matrix AMATRX
"""

import sys
from pathlib import Path

def apply_update():
    uel_path = Path("models/pandey_kumar_mode1/105_c3_irreversible_continuation/f42_experimental_irreversible_uel.for")
    with open(uel_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Declaration in UEL
    target_decl = (
        "      DOUBLE PRECISION D_LOWER_BOUND(N_CAPACITY,4)\n"
        "      DOUBLE PRECISION H_INITIAL_BOUND(N_CAPACITY,4)\n"
        "      LOGICAL IRREV_ACTIVE\n"
        "      COMMON /CB_IRREV_STATE/ D_LOWER_BOUND, H_INITIAL_BOUND,\n"
        "     1                        IRREV_ACTIVE\n"
        "      DOUBLE PRECISION DIFF_D\n"
        "\n"
        "      DOUBLE PRECISION W4(4), XG4(4), YG4(4)\n"
        "      DOUBLE PRECISION W3(3), XG3(3), YG3(3)\n"
        "      DOUBLE PRECISION B(3,8), B_PHASE(2,4), B_TRI(3,6), B_PHTRI(2,3)"
    )

    replacement_decl = (
        "      DOUBLE PRECISION D_LOWER_BOUND(N_CAPACITY,4)\n"
        "      DOUBLE PRECISION H_INITIAL_BOUND(N_CAPACITY,4)\n"
        "      LOGICAL IRREV_ACTIVE\n"
        "      COMMON /CB_IRREV_STATE/ D_LOWER_BOUND, H_INITIAL_BOUND,\n"
        "     1                        IRREV_ACTIVE\n"
        "      DOUBLE PRECISION DIFF_D, PEN_FORCE, PEN_STIFF\n"
        "      DOUBLE PRECISION GAMMA_PEN, DELTA_PEN\n"
        "      PARAMETER (GAMMA_PEN = 10.0D0, DELTA_PEN = 1.0D-4)\n"
        "\n"
        "      DOUBLE PRECISION W4(4), XG4(4), YG4(4)\n"
        "      DOUBLE PRECISION W3(3), XG3(3), YG3(3)\n"
        "      DOUBLE PRECISION B(3,8), B_PHASE(2,4), B_TRI(3,6), B_PHTRI(2,3)"
    )

    # 2. Quad element regularized penalty (JTYPE = 1)
    target_quad = (
        "C       Enforce damage irreversibility via active-set penalty / restoring force\n"
        "        IF (IRREV_ACTIVE) THEN\n"
        "          DO I=1, 4\n"
        "            IF (U(I) .LT. D_LOWER_BOUND(PHYSIDX, I)) THEN\n"
        "              DIFF_D = D_LOWER_BOUND(PHYSIDX, I) - U(I)\n"
        "              RHS(I,1) = RHS(I,1) + 1.0D8 * DIFF_D\n"
        "              AMATRX(I,I) = AMATRX(I,I) + 1.0D8\n"
        "            ENDIF\n"
        "          ENDDO\n"
        "        ENDIF"
    )

    replacement_quad = (
        "C       Enforce damage irreversibility via C1-smooth regularized penalty\n"
        "        IF (IRREV_ACTIVE) THEN\n"
        "          DO I=1, 4\n"
        "            DIFF_D = D_LOWER_BOUND(PHYSIDX, I) - U(I)\n"
        "            IF (DIFF_D .GT. ZERO) THEN\n"
        "              IF (DIFF_D .LT. DELTA_PEN) THEN\n"
        "C               C1-smooth quadratic transition band (delta = 1.0D-4)\n"
        "                PEN_FORCE = (GAMMA_PEN / (TWO * DELTA_PEN)) *\n"
        "     1                      (DIFF_D**2)\n"
        "                PEN_STIFF = (GAMMA_PEN / DELTA_PEN) * DIFF_D\n"
        "              ELSE\n"
        "C               Linear penalty zone\n"
        "                PEN_FORCE = GAMMA_PEN * (DIFF_D - HALF * DELTA_PEN)\n"
        "                PEN_STIFF = GAMMA_PEN\n"
        "              ENDIF\n"
        "              RHS(I,1) = RHS(I,1) + PEN_FORCE\n"
        "              AMATRX(I,I) = AMATRX(I,I) + PEN_STIFF\n"
        "            ENDIF\n"
        "          ENDDO\n"
        "        ENDIF"
    )

    # 3. Tri element regularized penalty (JTYPE = 3)
    target_tri = (
        "C       Enforce damage irreversibility via active-set penalty / restoring force\n"
        "        IF (IRREV_ACTIVE) THEN\n"
        "          DO I=1, 3\n"
        "            IF (U(I) .LT. D_LOWER_BOUND(PHYSIDX, I)) THEN\n"
        "              DIFF_D = D_LOWER_BOUND(PHYSIDX, I) - U(I)\n"
        "              RHS(I,1) = RHS(I,1) + 1.0D8 * DIFF_D\n"
        "              AMATRX(I,I) = AMATRX(I,I) + 1.0D8\n"
        "            ENDIF\n"
        "          ENDDO\n"
        "        ENDIF"
    )

    replacement_tri = (
        "C       Enforce damage irreversibility via C1-smooth regularized penalty\n"
        "        IF (IRREV_ACTIVE) THEN\n"
        "          DO I=1, 3\n"
        "            DIFF_D = D_LOWER_BOUND(PHYSIDX, I) - U(I)\n"
        "            IF (DIFF_D .GT. ZERO) THEN\n"
        "              IF (DIFF_D .LT. DELTA_PEN) THEN\n"
        "C               C1-smooth quadratic transition band (delta = 1.0D-4)\n"
        "                PEN_FORCE = (GAMMA_PEN / (TWO * DELTA_PEN)) *\n"
        "     1                      (DIFF_D**2)\n"
        "                PEN_STIFF = (GAMMA_PEN / DELTA_PEN) * DIFF_D\n"
        "              ELSE\n"
        "C               Linear penalty zone\n"
        "                PEN_FORCE = GAMMA_PEN * (DIFF_D - HALF * DELTA_PEN)\n"
        "                PEN_STIFF = GAMMA_PEN\n"
        "              ENDIF\n"
        "              RHS(I,1) = RHS(I,1) + PEN_FORCE\n"
        "              AMATRX(I,I) = AMATRX(I,I) + PEN_STIFF\n"
        "            ENDIF\n"
        "          ENDDO\n"
        "        ENDIF"
    )

    assert target_decl in content, "target_decl not found!"
    assert target_quad in content, "target_quad not found!"
    assert target_tri in content, "target_tri not found!"

    content = content.replace(target_decl, replacement_decl)
    content = content.replace(target_quad, replacement_quad)
    content = content.replace(target_tri, replacement_tri)

    with open(uel_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(content)

    print("[PASS] Successfully updated f42_experimental_irreversible_uel.for with C1-smooth Huber regularization.")

if __name__ == "__main__":
    apply_update()
