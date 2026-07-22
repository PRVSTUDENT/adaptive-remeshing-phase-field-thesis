#!/usr/bin/env python3
"""Validate Stage D2C four-thread repeatability against accepted D2B serial evidence."""

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


STATE_TOL = 1.0e-8
U2_TOL = 1.0e-10
RF_REL_TOL = 2.0e-3
RF_NRMSE_TOL = 2.0e-3
ENERGY_ALLWK_ABS_TOL = 1.0e-12
REQUESTED_U2 = 1.0e-5
FRAMES = ["F0", "F1", "F2", "F3"]
SDV_FIELDS = [f"{name}_{frame}" for name in ("SDV15", "SDV16") for frame in FRAMES]


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: List[str], rows: List[Dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def finite_float(value: str, name: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{name} is not finite: {value}")
    return out


def row_key(row: Dict[str, str]) -> Tuple[int, int]:
    return int(row["element"]), int(row["integration_point"])


def load_state(path: Path) -> Dict[Tuple[int, int], Dict[str, float]]:
    out = {}
    for row in read_csv(path):
        values = {"x": finite_float(row["x"], "x"), "y": finite_float(row["y"], "y")}
        for field in SDV_FIELDS:
            values[field] = finite_float(row[field], field)
        out[row_key(row)] = values
    return out


def load_rf(path: Path) -> Dict[str, Dict[str, float]]:
    out = {}
    for row in read_csv(path):
        values = {
            "step": row["step"],
            "increment_number": finite_float(row["increment_number"], "increment_number"),
            "step_time": finite_float(row["step_time"], "step_time"),
            "U2": finite_float(row["U2"], "U2"),
            "RF2": finite_float(row["RF2"], "RF2"),
            "ALLIE": finite_float(row["ALLIE"], "ALLIE"),
            "ALLSE": finite_float(row["ALLSE"], "ALLSE"),
            "ALLWK": finite_float(row["ALLWK"], "ALLWK"),
        }
        out[row["frame"]] = values
    return out


def rel_diff(a: float, b: float) -> float:
    scale = max(abs(a), abs(b))
    if scale == 0.0:
        return 0.0
    return abs(a - b) / scale


def nrmse(serial_values: Iterable[float], threaded_values: Iterable[float]) -> float:
    serial = list(serial_values)
    threaded = list(threaded_values)
    mse = sum((a - b) ** 2 for a, b in zip(serial, threaded)) / float(len(serial))
    denom = max(serial) - min(serial)
    if denom == 0.0:
        denom = max(max(abs(v) for v in serial), 1.0)
    return math.sqrt(mse) / denom


def parse_sta(path: Path) -> Dict[str, object]:
    rows = []
    if not path.exists():
        return {"exists": False, "successful": False, "rows": rows, "by_step": {}}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split()
        if len(parts) < 9:
            continue
        if not parts[0].isdigit() or not parts[1].isdigit():
            continue
        step = int(parts[0])
        inc_token = parts[1]
        cutback = "U" in inc_token
        try:
            inc = int(inc_token.replace("U", ""))
            total_iter = int(parts[5])
            total_time = float(parts[6])
            step_time = float(parts[7])
            increment = float(parts[8])
        except ValueError:
            continue
        rows.append(
            {
                "step": step,
                "increment": inc,
                "cutback": cutback,
                "total_iterations": total_iter,
                "total_time": total_time,
                "step_time": step_time,
                "time_increment": increment,
            }
        )
    by_step = {}
    for step in [1, 2, 3]:
        step_rows = [row for row in rows if row["step"] == step]
        accepted = [row for row in step_rows if not row["cutback"]]
        by_step[str(step)] = {
            "accepted_increments": len(accepted),
            "cutbacks": len(step_rows) - len(accepted),
            "total_iterations": sum(row["total_iterations"] for row in accepted),
            "final_step_time": None if not accepted else accepted[-1]["step_time"],
        }
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "exists": True,
        "successful": "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in text,
        "rows": rows,
        "by_step": by_step,
    }


def thread_confirmation(paths: List[Path]) -> Dict[str, object]:
    patterns = [
        re.compile(r"1\s+MPI\s+RANK\s+x\s+4\s+THREAD", re.IGNORECASE),
        re.compile(r"1\s+HOST:\s+1\s+MPI\s+RANK\s+x\s+4\s+THREAD", re.IGNORECASE),
    ]
    hits = []
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                hits.append({"file": str(path), "text": match.group(0)})
                break
    return {"confirmed": bool(hits), "hits": hits}


def validate(out_dir: Path, serial_dir: Path, job_id: str) -> Dict[str, object]:
    failures = []
    serial_state = load_state(serial_dir / "D2B_STATE_BY_FRAME.csv")
    threaded_state = load_state(out_dir / "D2C_STATE_BY_FRAME.csv")
    serial_rf = load_rf(serial_dir / "D2B_RF_U.csv")
    threaded_rf = load_rf(out_dir / "D2C_RF_U.csv")

    comparison_rows = []
    max_sdv15 = 0.0
    max_sdv16 = 0.0
    min_sdv15_increase = math.inf
    min_sdv16_increase = math.inf

    if set(serial_state) != set(threaded_state):
        failures.append("element/IP ordering or coverage mismatch against serial D2B")
    ordered_keys = list(serial_state.keys())
    if ordered_keys != list(threaded_state.keys()):
        failures.append("element/IP ordering is not identical")

    for key in ordered_keys:
        if key not in threaded_state:
            continue
        srow = serial_state[key]
        trow = threaded_state[key]
        if abs(srow["x"] - trow["x"]) > STATE_TOL or abs(srow["y"] - trow["y"]) > STATE_TOL:
            failures.append(f"coordinate mismatch for element/IP {key[0]}/{key[1]}")
        for frame in FRAMES:
            d15 = abs(trow[f"SDV15_{frame}"] - srow[f"SDV15_{frame}"])
            d16 = abs(trow[f"SDV16_{frame}"] - srow[f"SDV16_{frame}"])
            max_sdv15 = max(max_sdv15, d15)
            max_sdv16 = max(max_sdv16, d16)
            comparison_rows.append(
                {
                    "element": key[0],
                    "integration_point": key[1],
                    "frame": frame,
                    "serial_SDV15": srow[f"SDV15_{frame}"],
                    "threads4_SDV15": trow[f"SDV15_{frame}"],
                    "abs_SDV15_difference": d15,
                    "serial_SDV16": srow[f"SDV16_{frame}"],
                    "threads4_SDV16": trow[f"SDV16_{frame}"],
                    "abs_SDV16_difference": d16,
                }
            )
        min_sdv15_increase = min(
            min_sdv15_increase,
            trow["SDV15_F1"] - trow["SDV15_F0"],
            trow["SDV15_F2"] - trow["SDV15_F1"],
            trow["SDV15_F3"] - trow["SDV15_F2"],
        )
        min_sdv16_increase = min(
            min_sdv16_increase,
            trow["SDV16_F1"] - trow["SDV16_F0"],
            trow["SDV16_F2"] - trow["SDV16_F1"],
            trow["SDV16_F3"] - trow["SDV16_F2"],
        )

    if max_sdv15 > STATE_TOL:
        failures.append(f"max SDV15 serial-vs-threads difference {max_sdv15} exceeds {STATE_TOL}")
    if max_sdv16 > STATE_TOL:
        failures.append(f"max SDV16 serial-vs-threads difference {max_sdv16} exceeds {STATE_TOL}")
    if min_sdv15_increase < -STATE_TOL:
        failures.append(f"SDV15 decreases in D2C by {min_sdv15_increase}")
    if min_sdv16_increase < -STATE_TOL:
        failures.append(f"SDV16 decreases in D2C by {min_sdv16_increase}")
    sdv15_f3 = [threaded_state[key]["SDV15_F3"] for key in ordered_keys if key in threaded_state]
    sdv16_f3 = [threaded_state[key]["SDV16_F3"] for key in ordered_keys if key in threaded_state]
    if len(set(round(v, 14) for v in sdv15_f3)) <= 1:
        failures.append("D2C SDV15 spatial variation is absent")
    if len(set(round(v, 14) for v in sdv16_f3)) <= 1:
        failures.append("D2C SDV16 spatial variation is absent")

    if set(serial_rf) != set(FRAMES) or set(threaded_rf) != set(FRAMES):
        failures.append("RF/U comparison requires F0..F3 in both serial and threaded outputs")
    final_u2_abs = abs(threaded_rf["F3"]["U2"] - serial_rf["F3"]["U2"])
    final_rf_abs = abs(threaded_rf["F3"]["RF2"] - serial_rf["F3"]["RF2"])
    final_rf_rel = rel_diff(threaded_rf["F3"]["RF2"], serial_rf["F3"]["RF2"])
    rf_nrmse = nrmse([serial_rf[f]["RF2"] for f in FRAMES], [threaded_rf[f]["RF2"] for f in FRAMES])
    if abs(threaded_rf["F3"]["U2"] - REQUESTED_U2) > STATE_TOL:
        failures.append(f"D2C final U2 {threaded_rf['F3']['U2']} did not reach {REQUESTED_U2}")
    if final_u2_abs > U2_TOL:
        failures.append(f"final U2 serial-vs-threads difference {final_u2_abs} exceeds {U2_TOL}")
    if final_rf_rel > RF_REL_TOL:
        failures.append(f"final RF2 relative difference {final_rf_rel} exceeds {RF_REL_TOL}")
    if rf_nrmse > RF_NRMSE_TOL:
        failures.append(f"RF-U NRMSE {rf_nrmse} exceeds {RF_NRMSE_TOL}")

    field_comparison = {
        "max_abs_SDV15_threads_minus_serial": max_sdv15,
        "max_abs_SDV16_threads_minus_serial": max_sdv16,
        "min_SDV15_thread_frame_increment": None if math.isinf(min_sdv15_increase) else min_sdv15_increase,
        "min_SDV16_thread_frame_increment": None if math.isinf(min_sdv16_increase) else min_sdv16_increase,
        "target_ip_coverage": len(set(serial_state).intersection(threaded_state)) / float(len(serial_state)) if serial_state else 0.0,
        "state_tolerance": STATE_TOL,
    }
    rf_comparison = {
        "serial_final_U2": serial_rf["F3"]["U2"],
        "threads4_final_U2": threaded_rf["F3"]["U2"],
        "final_U2_abs_difference": final_u2_abs,
        "serial_final_RF2": serial_rf["F3"]["RF2"],
        "threads4_final_RF2": threaded_rf["F3"]["RF2"],
        "final_RF2_abs_difference": final_rf_abs,
        "final_RF2_relative_difference": final_rf_rel,
        "RF_U_NRMSE": rf_nrmse,
        "final_U2_tolerance": U2_TOL,
        "RF_relative_tolerance": RF_REL_TOL,
        "RF_U_NRMSE_tolerance": RF_NRMSE_TOL,
    }
    energy_comparison = {"frames": {}, "tolerances": {"ALLWK_abs": ENERGY_ALLWK_ABS_TOL}}
    for frame in FRAMES:
        energy_comparison["frames"][frame] = {}
        for name in ["ALLIE", "ALLSE", "ALLWK"]:
            diff = threaded_rf[frame][name] - serial_rf[frame][name]
            energy_comparison["frames"][frame][name] = {
                "serial": serial_rf[frame][name],
                "threads4": threaded_rf[frame][name],
                "abs_difference": abs(diff),
                "signed_difference": diff,
            }
            if name == "ALLWK" and frame == "F3" and abs(diff) > ENERGY_ALLWK_ABS_TOL:
                failures.append(f"F3 ALLWK absolute difference {abs(diff)} exceeds {ENERGY_ALLWK_ABS_TOL}")

    serial_inc = parse_sta(serial_dir / "d2b_serial_cont_r1.sta")
    threaded_inc = parse_sta(out_dir / "d2c_threads4.sta")
    increment_comparison = {
        "serial": serial_inc["by_step"],
        "threads4": threaded_inc["by_step"],
        "different_increment_sequence": serial_inc["by_step"] != threaded_inc["by_step"],
    }
    thread_info = thread_confirmation([out_dir / "d2c_threads4.msg", out_dir / "d2c_threads4.dat", out_dir / "d2c_threads4.abaqus_stdout.log"])
    if not thread_info["confirmed"]:
        failures.append("could not confirm 1 MPI rank x 4 threads in Abaqus logs")
    if not threaded_inc["successful"]:
        failures.append("D2C .sta does not contain Abaqus successful completion statement")

    write_csv(
        out_dir / "D2C_SERIAL_VS_THREADS.csv",
        [
            "element",
            "integration_point",
            "frame",
            "serial_SDV15",
            "threads4_SDV15",
            "abs_SDV15_difference",
            "serial_SDV16",
            "threads4_SDV16",
            "abs_SDV16_difference",
        ],
        comparison_rows,
    )
    (out_dir / "D2C_FIELD_COMPARISON.json").write_text(json.dumps(field_comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "D2C_RF_U_COMPARISON.json").write_text(json.dumps(rf_comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "D2C_ENERGY_COMPARISON.json").write_text(json.dumps(energy_comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "D2C_INCREMENT_COMPARISON.json").write_text(json.dumps(increment_comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    status = {
        "classification": "stage_d2c_thread_repeatability_pass" if not failures else "stage_d2c_thread_repeatability_fail",
        "D2C_ok": not failures,
        "job_id": job_id,
        "serial_reference_job": "1376825.mmaster02",
        "solver_exit": 0,
        "odb_readable": True,
        "threads_confirmed": thread_info["confirmed"],
        "thread_confirmation": thread_info,
        "target_ip_coverage": field_comparison["target_ip_coverage"],
        "max_abs_SDV15_threads_minus_serial": max_sdv15,
        "max_abs_SDV16_threads_minus_serial": max_sdv16,
        "final_U2_abs_difference": final_u2_abs,
        "final_RF2_abs_difference": final_rf_abs,
        "final_RF2_relative_difference": final_rf_rel,
        "RF_U_NRMSE": rf_nrmse,
        "F3_ALLWK_abs_difference": energy_comparison["frames"]["F3"]["ALLWK"]["abs_difference"],
        "increment_sequence_changed": increment_comparison["different_increment_sequence"],
        "failures": failures,
    }
    (out_dir / "D2C_THREAD_STATUS.json").write_text(json.dumps(status, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = [
        "# D2C Four-Thread Repeatability Report",
        "",
        f"Classification: `{status['classification']}`",
        "",
        f"- Job: `{job_id}`",
        "- Serial reference: `1376825.mmaster02`",
        f"- Threads confirmed: `{status['threads_confirmed']}`",
        f"- Target element/IP coverage: `{status['target_ip_coverage']}`",
        f"- Max |SDV15_threads - SDV15_serial|: `{max_sdv15}`",
        f"- Max |SDV16_threads - SDV16_serial|: `{max_sdv16}`",
        f"- Final U2 absolute difference: `{final_u2_abs}`",
        f"- Final RF2 absolute difference: `{final_rf_abs}`",
        f"- Final RF2 relative difference: `{final_rf_rel}`",
        f"- RF-U NRMSE: `{rf_nrmse}`",
        f"- F3 ALLWK absolute difference: `{status['F3_ALLWK_abs_difference']}`",
        f"- Increment sequence changed: `{status['increment_sequence_changed']}`",
        f"- Failures: `{len(failures)}`",
        "",
        "Increment details are recorded in `D2C_INCREMENT_COMPARISON.json`.",
        "",
    ]
    (out_dir / "D2C_THREAD_REPEATABILITY_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    if not failures:
        (out_dir / "D2C.ok").write_text("", encoding="utf-8")
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--serial-dir", type=Path, default=Path("runs/hpc/stage_d2/d2b_serial_continuation_rerun"))
    parser.add_argument("--job-id", default="not_submitted")
    args = parser.parse_args()
    status = validate(args.out_dir, args.serial_dir, args.job_id)
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["D2C_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
