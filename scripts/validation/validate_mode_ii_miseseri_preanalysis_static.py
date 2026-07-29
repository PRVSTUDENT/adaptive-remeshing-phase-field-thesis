#!/usr/bin/env python3
"""Static validator for Stage F Candidate Job B: Pandey-Kumar MISESERI pre-analysis package."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = ROOT / "models/generated/mode_ii/miseseri_preanalysis"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_miseseri_static(package_dir: Path = PACKAGE_DIR) -> dict:
    failures = []
    checks = []

    def check(condition: bool, msg: str) -> None:
        checks.append(msg)
        if not condition:
            failures.append(msg)

    check(package_dir.is_dir(), f"package directory exists ({package_dir.relative_to(ROOT)})")

    out_inp = package_dir / "ModeII_MISESERI_preanalysis.inp"
    manifest_json = package_dir / "GENERATION_MANIFEST.json"
    topo_json = package_dir / "TOPOLOGY_AUDIT.json"
    output_json = package_dir / "OUTPUT_REQUEST_AUDIT.json"
    provenance_json = package_dir / "PROVENANCE.json"
    mesh_stats_json = package_dir / "mesh_statistics.json"

    check(out_inp.is_file(), f"MISESERI deck exists ({out_inp.name})")
    check(manifest_json.is_file(), f"Manifest JSON exists ({manifest_json.name})")
    check(topo_json.is_file(), f"Topology audit JSON exists ({topo_json.name})")
    check(output_json.is_file(), f"Output request audit JSON exists ({output_json.name})")
    check(provenance_json.is_file(), f"Provenance JSON exists ({provenance_json.name})")
    check(mesh_stats_json.is_file(), f"Mesh statistics JSON exists ({mesh_stats_json.name})")

    deck_text = out_inp.read_text(encoding="utf-8") if out_inp.is_file() else ""

    # Header check
    check("Pandey-Kumar MISESERI pre-analysis" in deck_text, "Deck header contains Pandey-Kumar pre-analysis description")
    # Output requests check
    check("MISESERI" in deck_text and "MISESAVG" in deck_text, "Deck requests MISESERI and MISESAVG error indicator output")
    check("EVOL" in deck_text, "Deck requests EVOL element volume output")
    # Element type check
    check("CPE4" in deck_text, "Deck uses standard CPE4 plane strain continuum elements")
    # Material check
    check("*Elastic" in deck_text and "210., 0.3" in deck_text, "Deck uses standard Abaqus linear elastic material")
    # Notch node sets check
    check("notch_lower_face" in deck_text and "notch_upper_face" in deck_text, "Deck defines notch_lower_face and notch_upper_face node sets")

    # Topology audit check
    if topo_json.is_file():
        topo_data = json.loads(topo_json.read_text(encoding="utf-8"))
        check(topo_data.get("true_slit_topology_established") is True, "Topology audit confirms true slit topology established")
        check(topo_data.get("coincident_node_pairs_count") == 15, "Topology audit confirms 15 coincident node pairs")
        check(topo_data.get("shared_nodes_across_slit_count") == 0, "Topology audit confirms 0 shared nodes across slit")

    passed = len(failures) == 0

    return {
        "job_name": "mode_ii_miseseri_preanalysis",
        "passed": passed,
        "total_checks": len(checks),
        "failures": failures,
        "deck_sha256": sha256_file(out_inp) if out_inp.is_file() else "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, default=PACKAGE_DIR)
    args = parser.parse_args()

    res = validate_miseseri_static(args.package_dir)
    print(json.dumps(res, indent=2))
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
