#!/usr/bin/env python3
"""Classify the 160400-element C2C attempt as scientifically over-refined."""
from __future__ import print_function

import json
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path("/home/pr21vyci/projects/adaptive-remeshing")
C2B = PROJECT / "runs/hpc/stage_c2/C2B_REFINED_MESH"
OUT = PROJECT / "runs/hpc/stage_c2/recovery"
H0, H1, H2 = 3930, 12064, 33852


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    man = json.loads((C2B / "remeshing_rule_manifest.json").read_text(encoding="utf-8"))
    summary = json.loads((C2B / "C2B_FIELD_SUMMARY.json").read_text(encoding="utf-8"))
    n = int(man.get("n_elements", 160400))
    sizing = man.get("sizing") or {}
    zone = man.get("refined_zone") or {}
    corridor = man.get("corridor_h") or {}

    status = {
        "stage": "C2C",
        "job_id_rebuild": "1376410.mmaster02",
        "technical_rebuild": "pass",
        "adaptive_efficiency": "fail",
        "classification": "refined_mesh_scientifically_over_refined",
        "C2E_release": False,
        "C2F_release": False,
        "n_physical": n,
        "n_layered": n * 3,
        "references": {"H0": H0, "H1": H1, "H2_PUB": H2},
        "ratios": {
            "vs_H0": n / float(H0),
            "vs_H1": n / float(H1),
            "vs_H2_PUB": n / float(H2),
        },
        "element_size_stats_corridor": corridor,
        "marked_fraction": sizing.get("fraction_marked"),
        "n_marked": sizing.get("n_marked"),
        "refined_zone": zone,
        "rule_as_applied": {
            "errorTarget": sizing.get("errorTarget", 0.05),
            "incorrect_interpretation": "absolute raw MISESERI > errorTarget",
            "correct_interpretation": "relative MISESERI/max(MISESERI) > errorTarget",
            "max_MISESERI_field": summary.get("checks", {}).get("max_MISESERI"),
        },
        "root_cause": (
            "apply_marks used `if MISESERI > errorTarget` with errorTarget=0.05 while "
            "continuum MISESERI reaches ~1390, marking ~99.9% of elements; bounding box "
            "then covered nearly the full plate; X-axis used refined-to-end at minElementSize."
        ),
        "preserve_as": "failed_design_evidence_do_not_delete",
        "deck_path": str(
            PROJECT
            / "models/generated/molnar_gravouil_2017/unified_preprocessing/H0_refined_layered"
        ),
        "written_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (OUT / "C2C_ADAPTIVE_EFFICIENCY_STATUS.json").write_text(
        json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    md = [
        "# C2C Adaptive Efficiency Review (v1 / 160400 elements)",
        "",
        "## Classification",
        "",
        "| Field | Value |",
        "| --- | --- |",
        "| technical_rebuild | **pass** (job 1376410) |",
        "| adaptive_efficiency | **fail** |",
        "| classification | `refined_mesh_scientifically_over_refined` |",
        "| C2E_release | **no** |",
        "| C2F_release | **no** |",
        "",
        "## Counts and ratios",
        "",
        "| Mesh | N_physical | Ratio to this mesh |",
        "| --- | ---: | ---: |",
        "| H0 | 3930 | %.2f× smaller |" % (n / float(H0)),
        "| H1 | 12064 | this mesh is **%.2f× H1** |" % (n / float(H1)),
        "| H2-PUB | 33852 | this mesh is **%.2f× H2-PUB** |" % (n / float(H2)),
        "| **C2C v1** | **%d** | 1.00× |" % n,
        "| Layered (U1+U2+CPS4) | %d | — |" % (n * 3),
        "",
        "## Size / mark evidence",
        "",
        "- marked fraction (absolute rule): **%s**" % sizing.get("fraction_marked"),
        "- n_marked: **%s**" % sizing.get("n_marked"),
        "- refined zone: `%s`" % json.dumps(zone),
        "- corridor h stats: `%s`" % json.dumps(corridor),
        "- max MISESERI (C2B): **%s**" % summary.get("checks", {}).get("max_MISESERI"),
        "",
        "## Why global / near-global refinement occurred",
        "",
        "1. **Wrong marking threshold.** `errorTarget=0.05` was applied as an *absolute*",
        "   raw-MISESERI cutoff (`MISESERI > 0.05`). The continuum field reaches",
        "   ~1390, so almost every element was marked (~99.9%).",
        "2. **Bounding-box zone.** Marked centroids spanned nearly the full plate;",
        "   padding expanded the refined window further.",
        "3. **X-axis refined-to-end.** The mesh builder refined at `minElementSize`",
        "   from `x_min` all the way to the right boundary, not a bounded patch.",
        "4. **Result.** ~160k physical elements (~13.3× H1, ~4.7× H2-PUB) — not an",
        "   efficient adaptive mesh. **Do not use for C2E/C2F.**",
        "",
        "## Preservation",
        "",
        "The 160400-element deck and C2B remesh products are retained as",
        "**failed-design evidence** and must not be overwritten by C2C-v2.",
        "",
    ]
    (OUT / "C2C_ADAPTIVE_EFFICIENCY_REVIEW.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
