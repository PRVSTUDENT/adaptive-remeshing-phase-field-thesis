#!/usr/bin/env python3
"""Audit final thesis evidence traceability and create the freeze manifest."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--latex-log", type=Path)
    args = parser.parse_args()
    final_paths = [
        ROOT / "docs/thesis/THESIS_CLOSEOUT_BUILD.tex",
        ROOT / "docs/thesis/STAGE_A_MOLNAR_BENCHMARK_CHAPTER.tex",
        ROOT / "docs/thesis/STAGE_C_OFFLINE_REFINEMENT_CHAPTER.tex",
        ROOT / "docs/thesis/STAGE_D_STATE_TRANSFER_SYNTHESIS.tex",
        ROOT / "docs/thesis/STAGE_D3D_A1_CHECKPOINT_CORRECTION_AND_LIMITATION.tex",
        ROOT / "docs/thesis/EXTERNALDB_COMMONBLOCK_PARALLELIZATION_STUDY.tex",
        ROOT / "docs/thesis/FINAL_RECOMMENDATIONS_AND_DECISION_TREE.tex",
        ROOT / "docs/thesis/FINAL_CLAIM_MATRIX.md",
        ROOT / "docs/reports/STAGE_A_BASELINE_REPORT.tex",
        ROOT / "docs/reports/STAGE_A_EXECUTION_AND_FAILURE_LOG.tex",
        ROOT / "docs/reports/STAGE_B_RESULTS_REPORT.tex",
        ROOT / "docs/reports/STAGE_B_EXECUTION_AND_FAILURE_LOG.tex",
        ROOT / "docs/decisions/FINAL_THESIS_TOLERANCE_POLICY.md",
        ROOT / "docs/decisions/WP6_ABAQUSER_EXTERNAL_BLOCK_CLOSURE.md",
        ROOT / "docs/decisions/STAGE_P_FINAL_SCIENTIFIC_CLOSURE.md",
        ROOT / "docs/decisions/WP7_FINAL_CLOSEOUT_RECONCILIATION.md",
        ROOT / "results/final/WP7_DOCUMENTATION_GATES.json",
        ROOT / "results/final/WP7_LATEX_BUILD_GATE.txt",
        ROOT / "results/final/stage_d/FIGURE_PROVENANCE.json",
        ROOT / "results/final/stage_d/STAGE_D_FINAL_METRICS.json",
    ]
    final_paths += sorted((ROOT / "results/final/stage_d/figures").glob("*.png"))
    final_paths += sorted((ROOT / "results/final/stage_d/tables").glob("*.csv"))
    checks = {}
    checks["all_final_paths_exist"] = all(path.is_file() for path in final_paths)
    tracked_odb = git("ls-files", "*.odb").splitlines()
    checks["no_odb_tracked"] = not tracked_odb
    prohibited_binary_suffixes = {
        ".odb", ".sim", ".res", ".mdl", ".stt", ".pac", ".abq", ".sel",
        ".lck", ".exe", ".dll", ".so",
    }
    tracked_unapproved_binaries = [
        path
        for path in git("ls-files").splitlines()
        if Path(path).suffix.lower() in prohibited_binary_suffixes
    ]
    checks["no_unapproved_generated_binary_tracked"] = not tracked_unapproved_binaries
    final_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in final_paths
        if path.suffix.lower() in {".tex", ".md", ".json", ".csv"}
    )
    dependency_paths = [
        ROOT / "docs/thesis/THESIS_CLOSEOUT_BUILD.tex",
        ROOT / "docs/thesis/STAGE_A_MOLNAR_BENCHMARK_CHAPTER.tex",
        ROOT / "docs/thesis/STAGE_C_OFFLINE_REFINEMENT_CHAPTER.tex",
        ROOT / "docs/thesis/STAGE_D_STATE_TRANSFER_SYNTHESIS.tex",
        ROOT / "docs/thesis/STAGE_D3D_A1_CHECKPOINT_CORRECTION_AND_LIMITATION.tex",
        ROOT / "docs/thesis/EXTERNALDB_COMMONBLOCK_PARALLELIZATION_STUDY.tex",
        ROOT / "docs/thesis/FINAL_RECOMMENDATIONS_AND_DECISION_TREE.tex",
        ROOT / "docs/decisions/WP7_FINAL_CLOSEOUT_RECONCILIATION.md",
    ]
    dependency_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in dependency_paths
    )
    checks["no_permanent_scratch_dependency"] = (
        "/scratch/" not in dependency_text and "/scratch9/" not in dependency_text
    )
    checks["withheld_online_remesh_claim"] = "online adaptive remeshing" in final_text and "not validated" in final_text
    checks["withheld_d3e_claim"] = "D3E" in final_text and ("not performed" in final_text or "remain prohibited" in final_text)
    checks["mechanical_restart_unproven"] = "mechanical restart" in final_text and ("unproven" in final_text or "not an accepted" in final_text)
    checks["stage_a_frozen_with_limitations"] = (
        final_text.count("frozen_with_residual_scientific_limitations")
        + final_text.count(r"frozen\_with\_residual\_scientific\_limitations")
    ) >= 2
    checks["stage_b_report_pair_present"] = all(
        (ROOT / path).is_file()
        for path in (
            "docs/reports/STAGE_B_RESULTS_REPORT.tex",
            "docs/reports/STAGE_B_EXECUTION_AND_FAILURE_LOG.tex",
        )
    )
    checks["wp6_external_block_visible"] = (
        "WP6 remains externally blocked" in final_text
        or "WP6 & IMFD/ABAQUSER integration & externally blocked" in final_text
    )
    checks["stage_p_scientific_boundary_visible"] = (
        "technically inconclusive for threaded" in final_text
        and "no general thread-safety" in final_text
    )
    try:
        documentation_gates = json.loads(
            (ROOT / "results/final/WP7_DOCUMENTATION_GATES.json").read_text()
        )
        checks["wp7_documentation_gates_pass"] = (
            documentation_gates.get("classification")
            == "wp7_documentation_gates_pass"
            and all(
                str(value).startswith("pass")
                for value in documentation_gates.get("checks", {}).values()
            )
            and not any(documentation_gates.get("execution", {}).values())
        )
    except Exception:
        checks["wp7_documentation_gates_pass"] = False
    checks["job_ids_recorded"] = all(job in final_text for job in ("1378003", "1378004", "1378005"))
    commit_pattern = re.compile(r"\b[0-9a-f]{40}\b")
    checks["commit_sha_recorded"] = bool(commit_pattern.search(final_text))
    try:
        provenance = json.loads((ROOT / "results/final/stage_d/FIGURE_PROVENANCE.json").read_text())
        checks["figure_provenance_complete"] = (
            provenance.get("classification") == "stage_d_final_figure_provenance_complete"
            and len(provenance.get("figures", {})) == 5
        )
    except Exception:
        checks["figure_provenance_complete"] = False
    latex_pass = False
    if args.latex_log and args.latex_log.is_file():
        log_text = args.latex_log.read_text(encoding="utf-8", errors="replace")
        latex_pass = "Output written on" in log_text or "THESIS_LATEX_BUILD_PASS" in log_text
    checks["latex_build_pass"] = latex_pass

    manifest = {
        "classification": "final_thesis_evidence_manifest_pass" if all(checks.values()) else "final_thesis_evidence_manifest_fail",
        "source_commit": git("rev-parse", "HEAD"),
        "checks": checks,
        "tracked_odb_files": tracked_odb,
        "tracked_unapproved_binaries": tracked_unapproved_binaries,
        "files": [
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in final_paths
            if path.is_file()
        ],
    }
    out = ROOT / "results/final/FINAL_EVIDENCE_MANIFEST.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# Final Reproducibility Audit",
        "",
        f"Classification: `{manifest['classification']}`",
        "",
        "| Check | Result |",
        "|---|---|",
    ]
    lines.extend(f"| `{name}` | {'pass' if value else 'fail'} |" for name, value in checks.items())
    lines += [
        "",
        f"Audited source revision: `{manifest['source_commit']}`.",
        "",
        "The audit is local/offline and authorizes no solver execution.",
    ]
    report = ROOT / "docs/reports/FINAL_REPRODUCIBILITY_AUDIT.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"classification": manifest["classification"], "checks": checks}, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
