#!/usr/bin/env python3
"""Build isolated D3D Route-B active-set-validity segment deck from accepted R4."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path


CHECKPOINT_U2 = 0.003000000026077032
SEGMENT_U2 = 0.0031
EXPECTED_ACTIVE = 6446
EXPECTED_FREE = 155
N_NODES = 6601
N_ELEM = 6400
N_IP = 4

DEFAULT_R4_EXE = Path("models/state_transfer/d3_interrupted_transfer/executable_r4_compatible_r2")
DEFAULT_PACKAGE = Path("runs/hpc/stage_d3/interrupted_transfer/package_compatible_r2")
DEFAULT_OUT = Path(
    "models/state_transfer/d3_interrupted_transfer/executable_d3d_active_set_segment_r1"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bool_value(text) -> bool:
    return str(text).strip().lower() in ("true", "1", "yes")


def append_step4(r4_inp: Path, out_inp: Path, package_dir: Path):
    text = r4_inp.read_text(encoding="utf-8")
    if "ACTIVE_SET_VALIDITY_SEGMENT" in text:
        raise SystemExit("R4 source already contains ACTIVE_SET_VALIDITY_SEGMENT")
    if text.count("*End Step") != 3:
        raise SystemExit("expected exactly three *End Step markers in R4 prefix")

    active_rows = read_csv(package_dir / "D3_ACTIVE_SET_BY_NODE.csv")
    lower = {
        int(row["node"]): float(row["d_lower_bound"])
        for row in read_csv(package_dir / "D3_LOWER_BOUND_NODAL_D.csv")
    }
    active_nodes = sorted(
        int(row["node"]) for row in active_rows if bool_value(row["active_lower_bound"])
    )
    free_nodes = sorted(
        int(row["node"]) for row in active_rows if not bool_value(row["active_lower_bound"])
    )
    if len(active_nodes) != EXPECTED_ACTIVE or len(free_nodes) != EXPECTED_FREE:
        raise SystemExit(
            "active/free counts %s/%s expected %s/%s"
            % (len(active_nodes), len(free_nodes), EXPECTED_ACTIVE, EXPECTED_FREE)
        )

    lines = [
        "",
        "*Step, name=ACTIVE_SET_VALIDITY_SEGMENT, nlgeom=NO",
        "*Static",
        "0.1, 1.0, 1.0e-08, 0.1",
        "*Controls, parameters=time incrementation",
        " , 100",
        "*Boundary, op=NEW",
        "BOTTOM, 2, 2, 0.0",
        "ANCHOR, 1, 1, 0.0",
        # Exact absolute displacement required by Route B protocol (not binary float dump).
        "TOP, 2, 2, 0.0031",
    ]
    for node in active_nodes:
        lines.append("%d, 3, 3, %.17g" % (node, lower[node]))
    lines += [
        "*Output, field, frequency=1",
        "*Element Output, elset=UMATVIS",
        "SDV",
        "*Node Output",
        "U, RF",
        "*End Step",
        "",
    ]
    # Ensure static card matches requested: initial 0.1, period 1.0, min 1e-8, max 0.1
    # Abaqus *Static: initial, time period, min, max
    # Already: 0.1, 1.0, 1.0e-08, 0.1

    out_inp.parent.mkdir(parents=True, exist_ok=True)
    out_inp.write_text(text.rstrip() + "\n" + "\n".join(lines), encoding="utf-8")
    return {
        "active_nodes": active_nodes,
        "free_nodes": free_nodes,
        "step4_active_bc_count": len(active_nodes),
        "step4_free_bc_count": 0,
        "step4_final_u2": SEGMENT_U2,
    }


def build(args):
    args.out_dir.mkdir(parents=True, exist_ok=True)
    r4_fortran = args.r4_exe_dir / "d3_transfer_uel.for"
    r4_h = args.r4_exe_dir / "d3_transfer_h.dat"
    r4_inp = args.r4_exe_dir / "D3A3_R4_compatible_hold.inp"

    dst_fortran = args.out_dir / "d3_transfer_uel.for"
    dst_h = args.out_dir / "d3_transfer_h.dat"
    dst_inp = args.out_dir / "D3D_active_set_segment.inp"

    shutil.copyfile(r4_fortran, dst_fortran)
    shutil.copyfile(r4_h, dst_h)
    step4 = append_step4(r4_inp, dst_inp, args.package_dir)

    r4_for_sha = sha256(r4_fortran)
    d3d_for_sha = sha256(dst_fortran)
    r4_h_sha = sha256(r4_h)
    d3d_h_sha = sha256(dst_h)
    if r4_for_sha != d3d_for_sha:
        raise SystemExit("Fortran copy not byte-identical to R4")
    if r4_h_sha != d3d_h_sha:
        raise SystemExit("runtime-H copy not byte-identical to R4")

    # Prefix audit: R4 steps 1-3 text is exact prefix of D3D deck before step 4.
    r4_text = r4_inp.read_text(encoding="utf-8").rstrip() + "\n"
    d3d_text = dst_inp.read_text(encoding="utf-8")
    if not d3d_text.startswith(r4_text):
        # Allow only trailing newline normalization differences by comparing without step4
        prefix = d3d_text.split("*Step, name=ACTIVE_SET_VALIDITY_SEGMENT")[0]
        if prefix.rstrip() + "\n" != r4_text and prefix.rstrip() != r4_text.rstrip():
            raise SystemExit("D3D deck Steps 1-3 are not an unchanged R4 prefix")

    runtime_manifest = {
        "classification": "stage_d3d_runtime_h_state_copied",
        "source": str(r4_h.as_posix()),
        "runtime_state_file": str(dst_h.as_posix()),
        "records": N_ELEM * N_IP,
        "sha256": d3d_h_sha,
        "byte_identical_to_r4": True,
        "r4_runtime_H_sha256": r4_h_sha,
    }
    write_json(args.out_dir / "D3D_RUNTIME_MANIFEST.json", runtime_manifest)

    provenance = {
        "classification": "stage_d3d_input_prepared",
        "route": "B_one_d3d_active_set_segment",
        "deck": str(dst_inp.as_posix()),
        "package": str(args.package_dir.as_posix()),
        "r4_exe_dir": str(args.r4_exe_dir.as_posix()),
        "r4_fortran_sha256": r4_for_sha,
        "d3d_fortran_sha256": d3d_for_sha,
        "fortran_byte_identical_to_r4": True,
        "runtime_H_sha256": d3d_h_sha,
        "runtime_H_byte_identical_to_r4": True,
        "active_nodes": len(step4["active_nodes"]),
        "free_nodes": len(step4["free_nodes"]),
        "start_u2_mm": CHECKPOINT_U2,
        "end_u2_mm": SEGMENT_U2,
        "continuation_steps": 1,
        "automatic_second_segment": False,
        "steps": [
            "INGEST_COMPATIBLE_R2",
            "CHECKPOINT_EQUILIBRATION_COMPATIBLE_R2_FIXED",
            "ACTIVE_SET_R2_RELEASE_HOLD",
            "ACTIVE_SET_VALIDITY_SEGMENT",
        ],
        "mesh": {"nodes": N_NODES, "elements": N_ELEM, "ips": N_ELEM * N_IP},
    }
    write_json(args.out_dir / "D3D_INPUT_PROVENANCE.json", provenance)

    prefix_audit = {
        "classification": "stage_d3d_r4_prefix_audit_pass",
        "r4_steps_1_to_3_unchanged": True,
        "r4_fortran_sha_unchanged": True,
        "runtime_H_sha_unchanged": True,
        "package_compatible_r2_source": str(args.package_dir.as_posix()),
        "package_r2_ok": "D3_PACKAGE_COMPATIBLE_R2.ok",
        "mesh_unchanged": {"nodes": N_NODES, "elements": N_ELEM, "ips": N_ELEM * N_IP},
        "r4_fortran_sha256": r4_for_sha,
        "runtime_H_sha256": d3d_h_sha,
        "step4_final_u2": SEGMENT_U2,
        "step4_active_phase_bc_count": step4["step4_active_bc_count"],
        "step4_free_phase_bc_count": 0,
        "exactly_one_continuation_step": True,
        "automatic_second_segment": False,
    }
    write_json(args.out_dir / "D3D_R4_PREFIX_AUDIT.json", prefix_audit)
    print(json.dumps(provenance, indent=2, sort_keys=True))
    return provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--r4-exe-dir", type=Path, default=DEFAULT_R4_EXE)
    parser.add_argument("--package-dir", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    build(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
