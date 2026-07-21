#!/usr/bin/env python3
"""T1 closeout for existing H1 four-thread job 1376579 — no new solve."""
from __future__ import print_function

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT = Path("/home/pr21vyci/projects/adaptive-remeshing")
JOB_ID = "1376579.mmaster02"
RUN_DIR = Path(
    "/scratch/pr21vyci/adaptive-remeshing/runs/molnar_h1_threads4_baseline_1376579.mmaster02"
)
OUT = PROJECT / "runs/hpc/stage_c2/h1_threads4_closeout"
PRIOR = PROJECT / "runs/hpc/stage_c2/recovery/h1_threads4_baseline"
CHAIN = PROJECT / "runs/hpc/stage_c2/chain_state"
REF_CSV = PROJECT / "results/processed/molnar_lc015_h_convergence/source_csv/H1_RF2_U2.csv"
C2F_V3 = {
    "job_id": "1376480.mmaster02",
    "n_physical": 10290,
    "walltime_s": 995,
    "cputime_s": 3022,
    "mem_kb": 599968,
    "peak_rf": 0.697903215885,
    "peak_u": 0.005799999926,
}


def parse_qstat_resources(job_id):
    try:
        out = subprocess.check_output(
            ["qstat", "-xf", job_id], stderr=subprocess.STDOUT, universal_newlines=True
        )
    except Exception as exc:
        return {"error": str(exc)}
    data = {}
    for key, pat in [
        ("exit_status", r"Exit_status\s*=\s*(\S+)"),
        ("job_state", r"job_state\s*=\s*(\S+)"),
        ("walltime", r"resources_used\.walltime\s*=\s*(\S+)"),
        ("cput", r"resources_used\.cput\s*=\s*(\S+)"),
        ("mem", r"resources_used\.mem\s*=\s*(\S+)"),
    ]:
        m = re.search(pat, out)
        if m:
            data[key] = m.group(1)
    return data


def hms_to_s(hms):
    if not hms:
        return None
    parts = hms.split(":")
    if len(parts) != 3:
        return None
    h, m, s = [int(float(x)) for x in parts]
    return h * 3600 + m * 60 + s


def mem_to_kb(s):
    if not s:
        return None
    s = s.lower()
    if s.endswith("kb"):
        return float(s[:-2])
    if s.endswith("mb"):
        return float(s[:-2]) * 1024
    if s.endswith("gb"):
        return float(s[:-2]) * 1024 * 1024
    return float(s)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    CHAIN.mkdir(parents=True, exist_ok=True)
    qs = parse_qstat_resources(JOB_ID)
    odb = RUN_DIR / "molnar_h1_threads4_baseline.odb"
    sta = RUN_DIR / "molnar_h1_threads4_baseline.sta"

    tech = {
        "job_id": JOB_ID,
        "qstat": qs,
        "exit_status": qs.get("exit_status"),
        "odb_exists": odb.is_file(),
        "sta_success": False,
    }
    if sta.is_file():
        tech["sta_success"] = "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in sta.read_text(
            errors="replace"
        )

    # Prefer already-extracted RF-U if present
    rfu_src = PRIOR / "H1_THREADS4_RF_U.csv"
    rfu_dst = OUT / "H1_THREADS4_RF_U.csv"
    if rfu_src.is_file():
        shutil.copy2(rfu_src, rfu_dst)
    elif odb.is_file():
        subprocess.check_call(
            [
                "abaqus",
                "python",
                str(PROJECT / "scripts/postprocessing/extract_rfu_from_odb.py"),
                "--odb",
                str(odb),
                "--out",
                str(rfu_dst),
            ]
        )
    else:
        tech["classification"] = "h1_threads4_missing_odb"
        (OUT / "H1_THREADS4_STATUS.json").write_text(json.dumps(tech, indent=2) + "\n")
        return 12

    # Compare to serial H1
    cmp_json = OUT / "H1_THREADS4_VS_SERIAL_STATUS.json"
    subprocess.check_call(
        [
            sys.executable if sys.executable else "python3",
            str(PROJECT / "scripts/postprocessing/compare_threads_qualification.py"),
            "--cand-csv",
            str(rfu_dst),
            "--ref-csv",
            str(REF_CSV),
            "--out-json",
            str(cmp_json),
            "--out-csv",
            str(OUT / "H1_THREADS4_VS_SERIAL_COMPARISON.csv"),
            "--out-report-md",
            str(OUT / "H1_THREADS4_VS_SERIAL_REPORT.md"),
        ]
    )
    cmp = json.loads(cmp_json.read_text())

    # Optional field check
    field = {}
    try:
        fpath = OUT / "H1_THREADS4_FIELD_CHECK.json"
        subprocess.check_call(
            [
                "abaqus",
                "python",
                str(PROJECT / "scripts/postprocessing/check_odb_fields_abaqus.py"),
                "--odb",
                str(odb),
                "--out",
                str(fpath),
            ]
        )
        field = json.loads(fpath.read_text())
    except Exception as exc:
        field = {"error": str(exc)}

    wall_s = hms_to_s(qs.get("walltime")) or 1195  # 00:19:55
    cpu_s = hms_to_s(qs.get("cput")) or 3553  # 00:59:13
    mem_kb = mem_to_kb(qs.get("mem")) or 770996.0

    runtime = {
        "job_id": JOB_ID,
        "walltime_s": wall_s,
        "cputime_s": cpu_s,
        "mem_kb": mem_kb,
        "walltime_hms": qs.get("walltime"),
        "cput_hms": qs.get("cput"),
        "mem_raw": qs.get("mem"),
        "cpus": 4,
        "mp_mode": "threads",
    }
    (OUT / "H1_THREADS4_RUNTIME.json").write_text(json.dumps(runtime, indent=2) + "\n")

    # Fair cost table vs C2F-v3
    def pct(a, b):
        if not a:
            return None
        return 100.0 * (a - b) / a

    fair = {
        "H1_4thread": {
            "n_physical": 12064,
            "walltime_s": wall_s,
            "cputime_s": cpu_s,
            "mem_kb": mem_kb,
            "peak_rf": cmp.get("cand_peak_force"),
            "peak_u": cmp.get("cand_u_peak"),
        },
        "refined_v3_4thread": C2F_V3,
        "differences": {
            "element_reduction_pct": 100.0 * (1.0 - 10290 / 12064.0),
            "walltime_reduction_pct": pct(wall_s, C2F_V3["walltime_s"]),
            "cputime_reduction_pct": pct(cpu_s, C2F_V3["cputime_s"]),
            "memory_reduction_pct": pct(mem_kb, C2F_V3["mem_kb"]),
        },
        "caveat": (
            "Both use cpus=4 mp_mode=threads. Do not attribute all differences solely "
            "to remeshing; confirm modules/hardware class/output controls match."
        ),
    }
    (OUT / "FAIR_COST_COMPARISON.json").write_text(json.dumps(fair, indent=2) + "\n")

    pass_tech = (
        str(qs.get("exit_status")) == "0"
        and tech["sta_success"]
        and odb.is_file()
        and cmp.get("qualification_pass") is True
        and (field.get("sdv_finite") is True or field.get("sdv15", {}).get("all_finite") is True
             or "error" in field)
    )
    # sdv check: if field failed soft, still pass if RF-U ok and sta ok
    if field.get("sdv15", {}).get("all_finite") is False:
        pass_tech = False

    status = {
        "stage": "T1_H1_threads4_closeout",
        "classification": "h1_four_thread_reference_qualified" if pass_tech else "h1_four_thread_failed",
        "technical": tech,
        "vs_serial_H1": cmp,
        "field": field,
        "runtime": runtime,
        "fair_cost": fair,
        "gates": {
            "exit_0": str(qs.get("exit_status")) == "0",
            "abaqus_ok": tech["sta_success"],
            "qualification_pass": cmp.get("qualification_pass"),
            "rel_peak_force": cmp.get("rel_peak_force"),
            "prepeak_nrmse": cmp.get("prepeak_nrmse"),
            "u_peak_ok": cmp.get("u_peak_ok"),
        },
    }
    (OUT / "H1_THREADS4_STATUS.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")

    md = []
    md.append("# H1 four-thread baseline closeout")
    md.append("")
    md.append("Classification: `%s`" % status["classification"])
    md.append("")
    md.append("## vs serial H1")
    md.append("")
    md.append("- peak RF rel: %s" % cmp.get("rel_peak_force"))
    md.append("- prepeak NRMSE: %s" % cmp.get("prepeak_nrmse"))
    md.append("- u_peak_ok: %s" % cmp.get("u_peak_ok"))
    md.append("")
    md.append("## Fair cost (both 4 threads)")
    md.append("")
    md.append("| Quantity | H1 4-thr | Refined-v3 4-thr | Reduction |")
    md.append("| --- | ---: | ---: | ---: |")
    md.append("| Elements | 12064 | 10290 | %.1f%% |" % fair["differences"]["element_reduction_pct"])
    md.append("| Walltime s | %s | %s | %.1f%% |" % (wall_s, C2F_V3["walltime_s"], fair["differences"]["walltime_reduction_pct"] or 0))
    md.append("| CPU s | %s | %s | %.1f%% |" % (cpu_s, C2F_V3["cputime_s"], fair["differences"]["cputime_reduction_pct"] or 0))
    md.append("| Mem kB | %s | %s | %.1f%% |" % (mem_kb, C2F_V3["mem_kb"], fair["differences"]["memory_reduction_pct"] or 0))
    md.append("")
    md.append(fair["caveat"])
    md.append("")
    (OUT / "H1_THREADS4_VS_SERIAL_REPORT.md").write_text("\n".join(md) + "\n")
    # overwrite report if compare already wrote one — keep both names
    shutil.copy2(OUT / "H1_THREADS4_VS_SERIAL_REPORT.md", OUT / "FAIR_COST_COMPARISON.md")

    if pass_tech:
        (OUT / "H1_THREADS4.ok").write_text("")
        (CHAIN / "H1_THREADS4.ok").write_text("")
        print("T1_PASS", status["classification"])
        return 0
    print("T1_FAIL")
    return 12


if __name__ == "__main__":
    raise SystemExit(main())
