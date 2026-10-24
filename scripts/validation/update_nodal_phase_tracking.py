#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_nodal_phase_tracking.py
Replaces element-average damage bound updates at LOP=2 with exact nodal phase tracking:
- Adds SV_NODAL_PHASE(N_CAPACITY, 4) to /CB_STATE_TRANS/
- In UEL (JTYPE=1 and JTYPE=3), records exact nodal phase U(I) into SV_NODAL_PHASE(PHYSIDX, I)
- At LOP=2 in UEXTERNALDB, ratchets D_LOWER_BOUND(I, KPT) against SV_NODAL_PHASE(I, KPT)
Eliminates artificial nodal lower bound dilution/perturbation from element averaging.
"""

from pathlib import Path

def apply_nodal_tracking():
    uel_path = Path("models/pandey_kumar_mode1/105_c3_irreversible_continuation/f42_experimental_irreversible_uel.for")
    with open(uel_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update /CB_STATE_TRANS/ declarations across all subroutines
    old_cb_decl = (
        "      DOUBLE PRECISION SV_PHASE_COMMITTED(N_CAPACITY)\n"
        "      DOUBLE PRECISION SV_PHASE_TRIAL(N_CAPACITY)\n"
        "      DOUBLE PRECISION SV_H_COMMITTED(N_CAPACITY,4)\n"
        "      DOUBLE PRECISION SV_H_TRIAL(N_CAPACITY,4)\n"
        "      DOUBLE PRECISION SV_E_FRAC(N_CAPACITY)\n"
        "      DOUBLE PRECISION SV_E_ELAS(N_CAPACITY)\n"
        "      DOUBLE PRECISION SV_PSI_F(N_CAPACITY)\n"
        "      DOUBLE PRECISION SV_PSI_E(N_CAPACITY)\n"
        "\n"
        "      COMMON /CB_STATE_TRANS/ SV_PHASE_COMMITTED, SV_PHASE_TRIAL,\n"
        "     1                        SV_H_COMMITTED, SV_H_TRIAL,\n"
        "     2                        SV_E_FRAC, SV_E_ELAS,\n"
        "     3                        SV_PSI_F, SV_PSI_E"
    )

    new_cb_decl = (
        "      DOUBLE PRECISION SV_PHASE_COMMITTED(N_CAPACITY)\n"
        "      DOUBLE PRECISION SV_PHASE_TRIAL(N_CAPACITY)\n"
        "      DOUBLE PRECISION SV_H_COMMITTED(N_CAPACITY,4)\n"
        "      DOUBLE PRECISION SV_H_TRIAL(N_CAPACITY,4)\n"
        "      DOUBLE PRECISION SV_E_FRAC(N_CAPACITY)\n"
        "      DOUBLE PRECISION SV_E_ELAS(N_CAPACITY)\n"
        "      DOUBLE PRECISION SV_PSI_F(N_CAPACITY)\n"
        "      DOUBLE PRECISION SV_PSI_E(N_CAPACITY)\n"
        "      DOUBLE PRECISION SV_NODAL_PHASE(N_CAPACITY,4)\n"
        "\n"
        "      COMMON /CB_STATE_TRANS/ SV_PHASE_COMMITTED, SV_PHASE_TRIAL,\n"
        "     1                        SV_H_COMMITTED, SV_H_TRIAL,\n"
        "     2                        SV_E_FRAC, SV_E_ELAS,\n"
        "     3                        SV_PSI_F, SV_PSI_E,\n"
        "     4                        SV_NODAL_PHASE"
    )

    assert content.count(old_cb_decl) == 3, f"Expected 3 occurrences of old_cb_decl, found {content.count(old_cb_decl)}"
    content = content.replace(old_cb_decl, new_cb_decl)

    # 2. Update LOP=2 ratchet in UEXTERNALDB
    old_lop2 = (
        "        IF (IRREV_ACTIVE) THEN\n"
        "          DO I=1, N_CAPACITY\n"
        "            DO KPT=1, 4\n"
        "              IF (SV_PHASE_COMMITTED(I) .GT. D_LOWER_BOUND(I, KPT)) THEN\n"
        "                D_LOWER_BOUND(I, KPT) = SV_PHASE_COMMITTED(I)\n"
        "              ENDIF\n"
        "            ENDDO\n"
        "          ENDDO\n"
        "        ENDIF"
    )

    new_lop2 = (
        "        IF (IRREV_ACTIVE) THEN\n"
        "          DO I=1, N_CAPACITY\n"
        "            DO KPT=1, 4\n"
        "              IF (SV_NODAL_PHASE(I, KPT) .GT. D_LOWER_BOUND(I, KPT)) THEN\n"
        "                D_LOWER_BOUND(I, KPT) = SV_NODAL_PHASE(I, KPT)\n"
        "              ENDIF\n"
        "            ENDDO\n"
        "          ENDDO\n"
        "        ENDIF"
    )

    assert old_lop2 in content, "old_lop2 not found!"
    content = content.replace(old_lop2, new_lop2)

    # 3. Update UEL JTYPE=1 to record SV_NODAL_PHASE
    old_jtype1_head = (
        "        D_AVG = 0.25D0 * (U(1) + U(2) + U(3) + U(4))\n"
        "        SV_PHASE_TRIAL(PHYSIDX) = D_AVG"
    )

    new_jtype1_head = (
        "        D_AVG = 0.25D0 * (U(1) + U(2) + U(3) + U(4))\n"
        "        SV_PHASE_TRIAL(PHYSIDX) = D_AVG\n"
        "        DO I=1, 4\n"
        "          SV_NODAL_PHASE(PHYSIDX, I) = U(I)\n"
        "        ENDDO"
    )

    assert old_jtype1_head in content, "old_jtype1_head not found!"
    content = content.replace(old_jtype1_head, new_jtype1_head)

    # 4. Update UEL JTYPE=3 to record SV_NODAL_PHASE
    old_jtype3_head = (
        "        D_AVG = (U(1) + U(2) + U(3)) / THREE\n"
        "        SV_PHASE_TRIAL(PHYSIDX) = D_AVG"
    )

    new_jtype3_head = (
        "        D_AVG = (U(1) + U(2) + U(3)) / THREE\n"
        "        SV_PHASE_TRIAL(PHYSIDX) = D_AVG\n"
        "        DO I=1, 3\n"
        "          SV_NODAL_PHASE(PHYSIDX, I) = U(I)\n"
        "        ENDDO"
    )

    assert old_jtype3_head in content, "old_jtype3_head not found!"
    content = content.replace(old_jtype3_head, new_jtype3_head)

    with open(uel_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(content)

    print("[PASS] Successfully updated f42_experimental_irreversible_uel.for with exact nodal phase tracking.")

if __name__ == "__main__":
    apply_nodal_tracking()
