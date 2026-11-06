#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch authentic terminal evidence for F1630 PBS jobs 1420429.mmaster02 and 1420430.mmaster02
via Invoke-GuardedSsh.ps1.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SSH_SCRIPT = REPO_ROOT / ".agents" / "scripts" / "Invoke-GuardedSsh.ps1"


def run_remote(cmd: str) -> str:
    res = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(SSH_SCRIPT),
            "-RemoteCommand",
            cmd,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return res.stdout


def fetch_job_evidence(pkg_dir: Path, job_id: str, remote_run_dir: str, job_name: str) -> None:
    ev_dir = pkg_dir / "evidence" / job_id
    ev_dir.mkdir(parents=True, exist_ok=True)
    eq_dir = f"{remote_run_dir}/equilibration_{job_id}"

    # 1. qstat_xf.txt
    qstat_txt = run_remote(f"qstat -xf {job_id}")
    (ev_dir / "qstat_xf.txt").write_text(qstat_txt, encoding="utf-8")

    # 2. pbs_execution.log
    pbs_log = run_remote(f"cat {remote_run_dir}/pbs_execution.log")
    (ev_dir / "pbs_execution.log").write_text(pbs_log, encoding="utf-8")

    # 3. re_equilibration_summary.json
    summary_txt = run_remote(f"cat {eq_dir}/re_equilibration_summary.json")
    (ev_dir / "re_equilibration_summary.json").write_text(summary_txt, encoding="utf-8")

    # 4. live_iteration_telemetry.json
    telem_txt = run_remote(f"cat {eq_dir}/live_iteration_telemetry.json")
    (ev_dir / "live_iteration_telemetry.json").write_text(telem_txt, encoding="utf-8")

    # 5. step_01_outer_140_mechanical/uel_energy_balance.csv
    uel_csv = run_remote(f"cat {eq_dir}/step_01_outer_140_mechanical/uel_energy_balance.csv")
    (ev_dir / "outer_140_uel_energy_balance.csv").write_text(uel_csv, encoding="utf-8")

    # 6. step_01_outer_140_mechanical/endpoint.json -> extract scalar endpoint summary
    ep_raw = run_remote(f"cat {eq_dir}/step_01_outer_140_mechanical/endpoint.json")
    ep_obj = json.loads(ep_raw.strip())
    nodes = ep_obj.get("nodes", [])
    d_vals = [float(r[3]) for r in nodes if len(r) >= 4]
    endpoint_scalars = {
        "schema": ep_obj.get("schema", 1),
        "step_name": ep_obj.get("step_name"),
        "increment": ep_obj.get("increment"),
        "step_time": ep_obj.get("step_time"),
        "precision": ep_obj.get("precision"),
        "rp_u2": ep_obj.get("rp_u2"),
        "rf2_kN": ep_obj.get("rf2_kN"),
        "reaction_force_kN": ep_obj.get("rf2_kN"),
        "elastic_kNmm": ep_obj.get("elastic_kNmm"),
        "fracture_kNmm": ep_obj.get("fracture_kNmm"),
        "total_energy_kNmm": ep_obj.get("total_energy_kNmm"),
        "odb_sha256": ep_obj.get("odb_sha256"),
        "extractor_sha256": ep_obj.get("extractor_sha256"),
        "nodes_count": len(nodes),
        "min_d": min(d_vals) if d_vals else None,
        "max_d": max(d_vals) if d_vals else None,
    }
    (ev_dir / "endpoint.json").write_text(json.dumps(endpoint_scalars, indent=2), encoding="utf-8")

    print(f"Fetched authentic terminal evidence for {job_id} into {ev_dir}")


def main() -> None:
    fetch_job_evidence(
        REPO_ROOT / "models" / "pandey_kumar_mode1" / "174_c6_r12_picard_baseline",
        "1420429.mmaster02",
        "/scratch9/pr21vyci/runs/mode1_c6_r12_picard_baseline",
        "M1_C6_R12_PICARD_BASELINE",
    )
    fetch_job_evidence(
        REPO_ROOT / "models" / "pandey_kumar_mode1" / "175_c6_r12_anderson_m2",
        "1420430.mmaster02",
        "/scratch9/pr21vyci/runs/mode1_c6_r12_anderson_m2",
        "M1_C6_R12_ANDERSON_M2",
    )


if __name__ == "__main__":
    main()
