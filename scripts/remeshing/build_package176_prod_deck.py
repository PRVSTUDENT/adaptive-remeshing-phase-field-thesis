# -*- coding: utf-8 -*-
"""
scripts/remeshing/build_package176_prod_deck.py
===============================================
Generates PK_HOLE_METHOD_A_PROD.inp from PK_HOLE_METHOD_A_PROD_PHYS.inp
with 3-layer UEL + UMAT architecture and Step 1 bounded precritical loading.
"""
from __future__ import print_function
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.remeshing.generate_plate_with_hole_method_a import generate_uel_deck


def main():
    pkg_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole"
    src_phys = pkg_dir / "PK_HOLE_METHOD_A_PROD_PHYS.inp"
    dst_uel = pkg_dir / "PK_HOLE_METHOD_A_PROD.inp"

    if not src_phys.exists():
        raise FileNotFoundError("Missing physical mesh deck: %s" % src_phys)

    print("Building production deck from: %s" % src_phys)
    generate_uel_deck(
        str(src_phys),
        str(dst_uel),
        job_name="PK_HOLE_METHOD_A_PROD",
        plate_h=1.0,
        step1_only=True
    )
    print("Successfully created: %s (size: %d bytes)" % (dst_uel, dst_uel.stat().st_size))


if __name__ == "__main__":
    main()
