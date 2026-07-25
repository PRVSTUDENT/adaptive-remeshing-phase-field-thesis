#!/usr/bin/env python3
"""Temporary cluster-side helper for F1-P0 inventories (not a scientific model)."""
from __future__ import annotations

import csv
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(".").resolve()
PATHS = [
    "models/generated/mode_ii/h0_serial/ModeII_H0_serial.inp",
    "models/generated/mode_ii/h0_serial/ModeII_H0_serial.for",
    "models/generated/mode_ii/h0_serial/PACKAGE_MANIFEST.json",
    "models/generated/mode_ii/h0_serial/input_hashes.sha256",
    "models/generated/mode_ii/h0_serial/STATIC_VALIDATION.json",
    "runs/hpc/stage_f/mode_ii_h0/MODE_II_H0_AUTHORIZATION.json",
    "runs/hpc/stage_f/mode_ii_h0/README.md",
    "scripts/hpc/stage_f/01_mode_ii_h0_datacheck.pbs",
    "scripts/hpc/stage_f/submit_mode_ii_h0_datacheck.sh",
    "scripts/validation/validate_mode_ii_h0_static.py",
    "scripts/validation/validate_mode_ii_h0_submission_preflight.py",
    "scripts/validation/check_multi_agent_bootstrap.py",
    "configs/studies/mode_ii_molnar_shear.yaml",
    "docs/studies/STAGE_F_MODE_II_BENCHMARK_PROTOCOL.md",
    "AGENTS.md",
    "project_coordination/CURRENT_STATE.md",
    "project_coordination/ACTIVE_TASK.json",
]


def main() -> None:
    rev = subprocess.check_output(["git", "rev-parse", "HEAD"], universal_newlines=True).strip()
    rows = []
    for rel in PATHS:
        p = ROOT / rel
        st = p.stat()
        tracked = (
            subprocess.call(
                ["git", "ls-files", "--error-unmatch", rel],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            == 0
        )
        rows.append(
            {
                "relative_path": rel,
                "type": p.suffix.lstrip(".") or "noext",
                "size_bytes": st.st_size,
                "last_modified": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
                "git_status": "tracked" if tracked else "untracked",
                "canonical_or_generated": (
                    "generated" if ("generated" in rel or rel.startswith("runs/")) else "canonical"
                ),
                "stage": "Stage F" if ("mode_ii" in rel or "stage_f" in rel) else "coordination",
                "notes": f"cluster_rev={rev}",
            }
        )
    out = Path("/tmp/HPC_REPOSITORY_INVENTORY_F1P0.csv")
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    srows = []
    for root_s in (
        "/scratch/pr21vyci/adaptive-remeshing",
        "/scratch9/pr21vyci/adaptive-remeshing",
    ):
        root = Path(root_s)
        print("scratch_root", root_s, "exists", root.exists())
        if not root.exists():
            continue
        try:
            print("children", [p.name for p in sorted(root.iterdir())[:40]])
        except OSError as exc:
            print("list_err", exc)
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d != ".git"]
            rel = dirpath
            interesting = ("mode_ii" in rel) or ("stage_f" in rel) or ("mode_ii_h0" in rel)
            if not interesting:
                dirnames[:] = [
                    d
                    for d in dirnames
                    if d in {"runs", "mode_ii_h0_staged", "stage_f"}
                    or "mode_ii" in d
                    or "stage_f" in d
                ]
                continue
            for name in filenames:
                fp = Path(dirpath) / name
                try:
                    st = fp.stat()
                except OSError:
                    continue
                srows.append(
                    {
                        "stage": "Stage F",
                        "task_id": "F1-P0",
                        "job_id": "",
                        "classification": "scratch_path_observed",
                        "path": str(fp),
                        "size_bytes": st.st_size,
                        "modified_at": datetime.fromtimestamp(
                            st.st_mtime, tz=timezone.utc
                        ).isoformat(),
                        "sha256": "",
                        "retention_status": "present_on_scratch",
                    }
                )
    if not srows:
        srows.append(
            {
                "stage": "Stage F",
                "task_id": "F1-P0",
                "job_id": "",
                "classification": "no_stage_f_scratch_outputs_found",
                "path": "/scratch*/pr21vyci/adaptive-remeshing (no mode_ii/stage_f outputs)",
                "size_bytes": 0,
                "modified_at": "",
                "sha256": "",
                "retention_status": "none_found",
            }
        )
    sout = Path("/tmp/HPC_SCRATCH_EVIDENCE_INDEX_F1P0.csv")
    with sout.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(srows[0].keys()))
        writer.writeheader()
        writer.writerows(srows)
    print("repo_inventory", out, len(rows))
    print("scratch_index", sout, len(srows))
    print(out.read_text(encoding="utf-8"))
    print("---SCRATCH---")
    print(sout.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
