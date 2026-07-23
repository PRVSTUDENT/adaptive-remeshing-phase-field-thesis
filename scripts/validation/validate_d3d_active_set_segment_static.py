#!/usr/bin/env python3
"""Static validation for the D3D Route-B active-set-validity segment deck."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path


N_NODES = 6601
N_ELEM = 6400
N_IP = 4
EXPECTED_ACTIVE = 6446
EXPECTED_FREE = 155
SEGMENT_U2 = 0.0031
CHECKPOINT_U2 = 0.003000000026077032
R4_RUNTIME_H_SHA = "e4e2b2773c7c29161f4c99bbd7218fa6fe49c6ec3e48d6c2107f83419e97e07c"
R4_FORTRAN_SHA = "e056ed01a2af407f58292b884acc264f7332d132457d62a3f4cf0732ffb9fda4"


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_tracked(path: Path) -> bool:
    return (
        subprocess.run(
            ["git", "ls-files", "--error-unmatch", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def bool_value(text) -> bool:
    return str(text).strip().lower() in ("true", "1", "yes")


def runtime_validate(path: Path):
    failures = []
    seen = set()
    records = 0
    duplicates = 0
    h_min = None
    h_max = None
    with path.open(encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) != 3:
                failures.append("invalid runtime record: " + line)
                continue
            element, ip, h = int(parts[0]), int(parts[1]), float(parts[2])
            key = (element, ip)
            if key in seen:
                duplicates += 1
            seen.add(key)
            records += 1
            if not math.isfinite(h) or h < -1.0e-14:
                failures.append("bad H at %s" % (key,))
            h_min = h if h_min is None else min(h_min, h)
            h_max = h if h_max is None else max(h_max, h)
    expected = {(e, i) for e in range(1, N_ELEM + 1) for i in range(1, N_IP + 1)}
    missing = expected - seen
    if records != N_ELEM * N_IP:
        failures.append("records=%s" % records)
    if duplicates:
        failures.append("duplicates=%s" % duplicates)
    if missing:
        failures.append("missing=%s" % len(missing))
    return {
        "classification": (
            "stage_d3d_runtime_state_validation_pass"
            if not failures
            else "stage_d3d_runtime_state_validation_fail"
        ),
        "runtime_state_ok": not failures,
        "records": records,
        "duplicates": duplicates,
        "missing_records": len(missing),
        "minimum_H": h_min,
        "maximum_H": h_max,
        "sha256": sha256(path),
        "failures": failures,
    }


def parse_step_phase_bcs(inp_path: Path):
    steps = {}
    current = None
    in_boundary = False
    for raw in inp_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        upper = line.upper()
        if upper.startswith("*STEP"):
            current = None
            for part in line.split(","):
                if part.strip().lower().startswith("name="):
                    current = part.split("=", 1)[1].strip()
            steps[current] = {"phase_nodes": [], "top_u2": None}
            in_boundary = False
            continue
        if upper.startswith("*END STEP"):
            current = None
            in_boundary = False
            continue
        if current is None:
            continue
        if upper.startswith("*BOUNDARY"):
            in_boundary = True
            continue
        if upper.startswith("*"):
            in_boundary = False
            continue
        if in_boundary:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4:
                try:
                    label = parts[0]
                    dof1 = int(parts[1])
                    dof2 = int(parts[2])
                    value = float(parts[3])
                except ValueError:
                    continue
                if label == "TOP" and dof1 == 2 and dof2 == 2:
                    steps[current]["top_u2"] = value
                try:
                    node = int(label)
                except ValueError:
                    continue
                if 1 <= node <= N_NODES and dof1 == 3 and dof2 == 3:
                    steps[current]["phase_nodes"].append(node)
    return steps


def validate(args):
    failures = []
    exe = args.exe_dir
    package = args.package_dir
    deck = exe / "D3D_active_set_segment.inp"

    required_markers = [
        Path("runs/hpc/stage_d3/interrupted_transfer/D3A3_ACCEPTED_CLOSURE.json"),
        Path("runs/hpc/stage_d3/interrupted_transfer/target_ingestion_r4_compatible/D3A3.ok"),
        Path("runs/hpc/stage_d3/fracture_continuation_decision/D3D_ROUTE_B_PREPARATION_AUTHORIZATION.json"),
        Path("runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2/D3_PACKAGE_COMPATIBLE_R2.ok"),
    ]
    for path in required_markers:
        if not path.exists() or not git_tracked(path):
            failures.append("missing or untracked prerequisite: %s" % path)

    closure = json.loads(
        Path("runs/hpc/stage_d3/interrupted_transfer/D3A3_ACCEPTED_CLOSURE.json").read_text(
            encoding="utf-8"
        )
    )
    if closure.get("gate_classification") != "stage_d3a3_state_transfer_gate_closed":
        failures.append("D3A3 closure gate classification mismatch")
    auth = json.loads(
        Path(
            "runs/hpc/stage_d3/fracture_continuation_decision/D3D_ROUTE_B_PREPARATION_AUTHORIZATION.json"
        ).read_text(encoding="utf-8")
    )
    if auth.get("classification") != "stage_d3d_route_b_preparation_authorized":
        failures.append("Route B preparation authorization missing")
    if not auth.get("preparation_authorized", False):
        failures.append("preparation_authorized is false")

    active_rows = read_csv(package / "D3_ACTIVE_SET_BY_NODE.csv")
    active_nodes = sorted(int(r["node"]) for r in active_rows if bool_value(r["active_lower_bound"]))
    free_nodes = sorted(int(r["node"]) for r in active_rows if not bool_value(r["active_lower_bound"]))
    if len(active_nodes) != EXPECTED_ACTIVE:
        failures.append("active nodes=%s" % len(active_nodes))
    if len(free_nodes) != EXPECTED_FREE:
        failures.append("free nodes=%s" % len(free_nodes))
    if len(active_nodes) + len(free_nodes) != N_NODES:
        failures.append("active+free != 6601")
    if len(set(active_nodes)) != len(active_nodes) or set(active_nodes) & set(free_nodes):
        failures.append("duplicate or overlapping active/free labels")
    if set(active_nodes) | set(free_nodes) != set(range(1, N_NODES + 1)):
        failures.append("missing active/free labels")

    steps = parse_step_phase_bcs(deck)
    names = list(steps.keys())
    expected_names = [
        "INGEST_COMPATIBLE_R2",
        "CHECKPOINT_EQUILIBRATION_COMPATIBLE_R2_FIXED",
        "ACTIVE_SET_R2_RELEASE_HOLD",
        "ACTIVE_SET_VALIDITY_SEGMENT",
    ]
    if names != expected_names:
        failures.append("step names mismatch: %s" % names)
    counts = {n: len(steps[n]["phase_nodes"]) for n in names}
    if counts.get("INGEST_COMPATIBLE_R2") != N_NODES:
        failures.append("Step 1 phase BCs != 6601")
    if counts.get("CHECKPOINT_EQUILIBRATION_COMPATIBLE_R2_FIXED") != N_NODES:
        failures.append("Step 2 phase BCs != 6601")
    if counts.get("ACTIVE_SET_R2_RELEASE_HOLD") != EXPECTED_ACTIVE:
        failures.append("Step 3 active phase BCs != 6446")
    if counts.get("ACTIVE_SET_VALIDITY_SEGMENT") != EXPECTED_ACTIVE:
        failures.append("Step 4 active phase BCs != 6446")

    step3 = set(steps["ACTIVE_SET_R2_RELEASE_HOLD"]["phase_nodes"])
    step4 = set(steps["ACTIVE_SET_VALIDITY_SEGMENT"]["phase_nodes"])
    if step3 != set(active_nodes) or step4 != set(active_nodes):
        failures.append("Step 3/4 phase BC labels do not match active set")
    free3 = len(step3 & set(free_nodes))
    free4 = len(step4 & set(free_nodes))
    if free3 != 0 or free4 != 0:
        failures.append("free-node phase BCs nonzero: step3=%s step4=%s" % (free3, free4))

    top4 = steps["ACTIVE_SET_VALIDITY_SEGMENT"]["top_u2"]
    if top4 is None or abs(float(top4) - SEGMENT_U2) > 1.0e-15:
        failures.append("Step 4 final U2 != 0.0031: %s" % top4)

    # Exactly one continuation step beyond R4 prefix.
    if names.count("ACTIVE_SET_VALIDITY_SEGMENT") != 1:
        failures.append("continuation step count != 1")
    if "ACTIVE_SET_VALIDITY_SEGMENT_2" in deck.read_text(encoding="utf-8", errors="replace"):
        failures.append("automatic second segment present")

    runtime = runtime_validate(exe / "d3_transfer_h.dat")
    failures.extend("runtime: " + f for f in runtime["failures"])
    if runtime["sha256"] != R4_RUNTIME_H_SHA:
        failures.append("runtime H SHA changed from R4")
    fortran_sha = sha256(exe / "d3_transfer_uel.for")
    if fortran_sha != R4_FORTRAN_SHA:
        failures.append("Fortran SHA not byte-identical to R4")
    if (exe / "d3_transfer_table.inc").exists():
        failures.append("obsolete d3_transfer_table.inc present")
    deck_text = deck.read_text(encoding="utf-8", errors="replace")
    if "mp_mode=mpi" in deck_text.lower():
        failures.append("MPI present in deck")

    # Mesh sizes from model.
    nodes = read_csv(args.model_dir / "target" / "target_nodes.csv")
    elements = read_csv(args.model_dir / "target" / "target_elements.csv")
    if len(nodes) != N_NODES or len(elements) != N_ELEM:
        failures.append("mesh size mismatch")

    prefix = json.loads((exe / "D3D_R4_PREFIX_AUDIT.json").read_text(encoding="utf-8"))
    if not prefix.get("r4_steps_1_to_3_unchanged", False):
        failures.append("prefix audit failed")
    if not prefix.get("runtime_H_sha_unchanged", False):
        failures.append("prefix runtime-H audit failed")

    active_audit = {
        "classification": (
            "stage_d3d_active_set_boundary_audit_pass"
            if not failures
            else "stage_d3d_active_set_boundary_audit_fail"
        ),
        "active_nodes": len(active_nodes),
        "free_nodes": len(free_nodes),
        "active_plus_free": len(active_nodes) + len(free_nodes),
        "duplicate_active_labels": 0,
        "missing_labels": 0,
        "step_phase_bc_counts": counts,
        "step3_free_node_phase_bc_count": free3,
        "step4_free_node_phase_bc_count": free4,
        "step4_active_phase_bc_count": len(step4),
        "step4_final_u2": top4,
        "step3_active_boundary_exact": step3 == set(active_nodes),
        "step4_active_boundary_exact": step4 == set(active_nodes),
    }

    status = {
        "classification": (
            "stage_d3d_static_validation_pass" if not failures else "stage_d3d_static_validation_fail"
        ),
        "D3D_static_ok": not failures,
        "target_nodes": len(nodes),
        "target_elements": len(elements),
        "target_ips": N_ELEM * N_IP,
        "runtime_H_sha256": runtime["sha256"],
        "runtime_H_tracked": git_tracked(exe / "d3_transfer_h.dat"),
        "runtime_H_records": runtime["records"],
        "runtime_H_duplicates": runtime["duplicates"],
        "runtime_H_missing_records": runtime["missing_records"],
        "fortran_sha256": fortran_sha,
        "fortran_byte_identical_to_r4": fortran_sha == R4_FORTRAN_SHA,
        "runtime_H_sha_unchanged_from_r4": runtime["sha256"] == R4_RUNTIME_H_SHA,
        "obsolete_transfer_table_absent": not (exe / "d3_transfer_table.inc").exists(),
        "mpi_absent": "mp_mode=mpi" not in deck_text.lower(),
        "exactly_one_continuation_step": True,
        "automatic_second_segment": False,
        "checkpoint_u2": CHECKPOINT_U2,
        "segment_u2": SEGMENT_U2,
        "failures": failures,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "D3D_STATIC_VALIDATION.json", status)
    write_json(args.out_dir / "D3D_ACTIVE_SET_BOUNDARY_AUDIT.json", active_audit)
    write_json(args.out_dir / "D3D_RUNTIME_STATE_VALIDATION.json", runtime)
    write_json(
        args.out_dir / "D3D_INPUT_PROVENANCE.json",
        json.loads((exe / "D3D_INPUT_PROVENANCE.json").read_text(encoding="utf-8")),
    )
    write_json(args.out_dir / "D3D_R4_PREFIX_AUDIT.json", prefix)
    if status["D3D_static_ok"]:
        (args.out_dir / "D3D_PREPARATION.ok").write_text(
            "stage_d3d_static_validation_pass\n", encoding="utf-8"
        )
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exe-dir",
        type=Path,
        default=Path(
            "models/state_transfer/d3_interrupted_transfer/executable_d3d_active_set_segment_r1"
        ),
    )
    parser.add_argument(
        "--package-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2"),
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=Path("models/state_transfer/d3_interrupted_transfer"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment_datacheck"),
    )
    args = parser.parse_args()
    status = validate(args)
    print(json.dumps(status, indent=2, sort_keys=True))
    return 0 if status["D3D_static_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
