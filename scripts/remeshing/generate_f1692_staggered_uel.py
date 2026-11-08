import re
from pathlib import Path

repo = Path(r"D:\Master thesis\Adaptive remeshing")
src = repo / "models/pandey_kumar_mode1/f42_mixed_uel.for"
dst = repo / "models/pandey_kumar_mode1/192_pk_sec43_staggered_job1/f42_staggered_variant_uel.for"

text = src.read_text(encoding="utf-8")

# 1. Update header
old_hdr = """C User Subroutines UEL, UMAT & UEXTERNALDB for Abaqus
C Staggered Transactional Phase-Field Fracture Formulation
C Revision: f42_mixed_uel_energy_qualified_v2.for"""

new_hdr = """C User Subroutines UEL, UMAT & UEXTERNALDB for Abaqus
C Staggered Operator-Split Formulation for Phase-Field Fracture
C Variant: f42_staggered_variant_uel.for (Task F1692 / HND-F1691-STAGGERED-001)
C Separate Solver Variant — Models/pandey_kumar_mode1/f42_mixed_uel.for stays BITWISE UNTOUCHED"""

assert old_hdr in text, "Could not find header to replace"
text = text.replace(old_hdr, new_hdr, 1)

# 2. In JTYPE 1 (Quad Phase): read HIST from SV_H_COMMITTED
text = text.replace(
    "HIST = SV_H_TRIAL(PHYSIDX, KPT)",
    "HIST = SV_H_COMMITTED(PHYSIDX, KPT)",
    1
)

# In JTYPE 1: enforce irreversibility on D_AVG
old_j1_davg = """        D_AVG = 0.25D0 * (U(1) + U(2) + U(3) + U(4))
        SV_PHASE_TRIAL(PHYSIDX) = D_AVG"""

new_j1_davg = """        D_AVG = 0.25D0 * (U(1) + U(2) + U(3) + U(4))
C       Strict Irreversibility Guard (no healing beyond numerical precision)
        IF (D_AVG .LT. SV_PHASE_COMMITTED(PHYSIDX)) THEN
          D_AVG = SV_PHASE_COMMITTED(PHYSIDX)
        ENDIF
        IF (D_AVG .GT. ONE) D_AVG = ONE
        SV_PHASE_TRIAL(PHYSIDX) = D_AVG"""

assert old_j1_davg in text, "Could not find JTYPE 1 D_AVG"
text = text.replace(old_j1_davg, new_j1_davg, 1)

# 3. In JTYPE 2 (Quad Mech): read D_VAL from SV_PHASE_COMMITTED
text = text.replace(
    "D_VAL = SV_PHASE_TRIAL(PHYSIDX)",
    "D_VAL = SV_PHASE_COMMITTED(PHYSIDX)",
    1
)

# 4. In JTYPE 3 (Tri Phase): read HIST from SV_H_COMMITTED
text = text.replace(
    "HIST = SV_H_TRIAL(PHYSIDX, KPT)",
    "HIST = SV_H_COMMITTED(PHYSIDX, KPT)",
    1
)

# In JTYPE 3: enforce irreversibility on D_AVG
old_j3_davg = """        D_AVG = (U(1) + U(2) + U(3)) / THREE
        SV_PHASE_TRIAL(PHYSIDX) = D_AVG"""

new_j3_davg = """        D_AVG = (U(1) + U(2) + U(3)) / THREE
C       Strict Irreversibility Guard (no healing beyond numerical precision)
        IF (D_AVG .LT. SV_PHASE_COMMITTED(PHYSIDX)) THEN
          D_AVG = SV_PHASE_COMMITTED(PHYSIDX)
        ENDIF
        IF (D_AVG .GT. ONE) D_AVG = ONE
        SV_PHASE_TRIAL(PHYSIDX) = D_AVG"""

assert old_j3_davg in text, "Could not find JTYPE 3 D_AVG"
text = text.replace(old_j3_davg, new_j3_davg, 1)

# 5. In JTYPE 4 (Tri Mech): read D_VAL from SV_PHASE_COMMITTED
text = text.replace(
    "D_VAL = SV_PHASE_TRIAL(PHYSIDX)",
    "D_VAL = SV_PHASE_COMMITTED(PHYSIDX)",
    1
)

dst.write_text(text, encoding="utf-8")
print(f"Generated {dst} successfully! ({len(text.splitlines())} lines)")
