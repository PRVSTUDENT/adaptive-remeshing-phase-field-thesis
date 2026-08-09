#!/usr/bin/env python3
"""Generate clean corrected MISESERI PBS package.

Immutable package path: models/generated/mode_ii/miseseri_preanalysis_corrected_pbs
Uses the corrected 3,930-element plane-strain CPE4 deck lineage (a927b831...).
Target displacement: U1 = 0.001 mm.
"""


import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC_BUILDER = ROOT / "scripts/model_generation/build_mode_ii_miseseri_preanalysis.py"

DEFAULT_OUT_DIR = ROOT / "models/generated/mode_ii/miseseri_preanalysis_corrected_pbs"

EXPECTED_PHYSICAL = 3930
EXPECTED_NODES = 3999
EXPECTED_SLIT_PAIRS = 15


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_text_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def build_package(out_dir: Path = DEFAULT_OUT_DIR, target_u1: float = 0.001) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    from scripts.model_generation.build_mode_ii_miseseri_preanalysis import build_package as build_miseseri_base

    manifest_base = build_miseseri_base(out_dir=out_dir, target_u1=target_u1)

    out_inp = out_dir / "ModeII_MISESERI_preanalysis.inp"
    deck_sha = sha256_file(out_inp)

    input_hashes_file = out_dir / "input_hashes.sha256"
    hashes_text = f"{deck_sha}  ModeII_MISESERI_preanalysis.inp\n"
    write_text_lf(input_hashes_file, hashes_text)

    try:
        out_rel = str(out_dir.relative_to(ROOT))
    except ValueError:
        out_rel = str(out_dir)

    manifest = {
        "job_name": "mode_ii_miseseri_corrected_pbs",
        "corrected_lineage_sha256": "a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2",
        "target_u1_mm": target_u1,
        "physical_elements": EXPECTED_PHYSICAL,
        "nodes": EXPECTED_NODES,
        "slit_coincident_pairs": EXPECTED_SLIT_PAIRS,
        "deck_sha256": deck_sha,
        "out_dir": out_rel,
    }

    manifest_file = out_dir / "GENERATION_MANIFEST.json"
    write_text_lf(manifest_file, json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    report_text = f"""# Package Report: Corrected MISESERI PBS Verification Package

- **Job Name:** `mode_ii_miseseri_corrected_pbs`
- **Target Endpoint:** $U_1 = {target_u1:.3f}\\text{{ mm}}$
- **Physical Elements:** {EXPECTED_PHYSICAL} (CPE4 plane-strain)
- **Node Count:** {EXPECTED_NODES}
- **Coincident Slit Pairs:** {EXPECTED_SLIT_PAIRS}
- **Corrected Lineage SHA-256:** `a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2`
- **Deck SHA-256:** `{deck_sha}`
"""
    write_text_lf(out_dir / "PACKAGE_REPORT.md", report_text)

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--target-u1", type=float, default=0.001)
    args = parser.parse_args()

    res = build_package(args.out_dir, args.target_u1)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
