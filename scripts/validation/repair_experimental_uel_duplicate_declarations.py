import os
from pathlib import Path

path = Path("models/pandey_kumar_mode1/104_experimental_irreversible_uel/f42_experimental_irreversible_uel.for")
text = path.read_text(encoding="utf-8")

# Duplicate block in UEXTERNALDB
dup_block = """      DOUBLE PRECISION D_LOWER_BOUND(N_CAPACITY,4)
      DOUBLE PRECISION H_INITIAL_BOUND(N_CAPACITY,4)
      LOGICAL IRREV_ACTIVE
      COMMON /CB_IRREV_STATE/ D_LOWER_BOUND, H_INITIAL_BOUND,
     1                        IRREV_ACTIVE
      DOUBLE PRECISION DIFF_D

      DOUBLE PRECISION D_LOWER_BOUND(N_CAPACITY,4)
      DOUBLE PRECISION H_INITIAL_BOUND(N_CAPACITY,4)
      LOGICAL IRREV_ACTIVE
      COMMON /CB_IRREV_STATE/ D_LOWER_BOUND, H_INITIAL_BOUND,
     1                        IRREV_ACTIVE"""

clean_block = """      DOUBLE PRECISION D_LOWER_BOUND(N_CAPACITY,4)
      DOUBLE PRECISION H_INITIAL_BOUND(N_CAPACITY,4)
      LOGICAL IRREV_ACTIVE
      COMMON /CB_IRREV_STATE/ D_LOWER_BOUND, H_INITIAL_BOUND,
     1                        IRREV_ACTIVE
      DOUBLE PRECISION DIFF_D"""

text_crlf = text.replace("\r\n", "\n")
if dup_block in text_crlf:
    repaired = text_crlf.replace(dup_block, clean_block, 1)
    path.write_text(repaired, encoding="utf-8")
    print("SUCCESS: Duplicate declaration removed.")
else:
    print("WARNING: dup_block not found in text_crlf.")
