# -*- coding: utf-8 -*-
"""
driver_package150_c1_2_continuation.py
Mode-I Method C: Stage C1-2 Multi-Step Forward-Loading Continuation Driver.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Solves the multi-step forward loading continuation problem from the accepted
Stage C1-1 equilibrium state (uy = 0.001800312544 mm) to the target displacement
uy = 0.002000000000 mm on the C4 candidate mesh (7,056 quads, 7,265 nodes, 28,224 GPs).

Loading Schedule:
  Step 1: uy = 0.0018503125442191958 mm (Delta uy = 5.0e-5 mm)
  Step 2: uy = 0.0019003125442191958 mm (Delta uy = 5.0e-5 mm)
  Step 3: uy = 0.0019503125442191958 mm (Delta uy = 5.0e-5 mm)
  Step 4: uy = 0.0020000000000000000 mm (Delta uy = 4.9687e-5 mm)

Key Features:
1. Strict pointwise damage irreversibility: d_step(x) >= d_prev(x).
2. Strict pointwise history monotonicity: H_step(x) >= H_prev(x).
3. Coupled staggered PDAS re-equilibration at each displacement step.
4. Acceptance at each step: Delta H <= 1e-6 MPa, Delta d <= 1e-5, Delta u <= 1e-9 mm.
5. Canonical 7+8+3 solution card serialization for Abaqus restarts.
"""
from __future__ import print_function, division
import os
import sys
import math
import json
import shutil
import hashlib
import csv
import subprocess
import time
import signal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.c3_int_to_c4_spatial_mapping import (
    Mesh2D, quad_shape_functions
)
from scripts.state_transfer.driver_package146_147_pdas_continuation import (
    PDASReEquilibrationSolver, validate_damage, driving_history,
    split_keyword_blocks, UEL_GP_LOCAL, FROZEN_UEL_SHA256,
    GC_DEFAULT, L0_DEFAULT, E_MODULUS, NU_POISSON,
    HEALING_TOL, DAT_DAMAGE_RECOVERY_TOL
)

LOADING_STEPS = [
    {"step": 1, "target_uy": 0.0018503125442191958, "delta_uy": 0.000050000000},
    {"step": 2, "target_uy": 0.0019003125442191958, "delta_uy": 0.000050000000},
    {"step": 3, "target_uy": 0.0019503125442191958, "delta_uy": 0.000050000000},
    {"step": 4, "target_uy": 0.0020000000000000000, "delta_uy": 0.0000496874557808042}
]


class StageC12ContinuationController(object):
    """
    Multi-step continuation controller for Stage C1-2 forward loading.
    """

    def __init__(self, package, output, extractor, abaqus="abaqus",
                 max_outer=30, max_phase=20, timeout=25200, memory_gb=16,
                 runner=None):
        self.package = Path(package).resolve()
        self.output = Path(output).resolve()
        self.extractor = Path(extractor).resolve()
        self.abaqus = abaqus
        self.max_outer = max_outer
        self.max_phase = max_phase
        self.timeout = timeout
        self.memory_gb = memory_gb
        self.runner = runner or self._run_abaqus
        self.step_records = []
        self.iteration_records = []

    def _compute_sha256(self, filepath):
        h = hashlib.sha256()
        with open(str(filepath), "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest().lower()

    def load(self):
        if not self.extractor.is_file():
            raise ValueError("Missing endpoint extractor: %s" % self.extractor)

        manifest_path = self.package / "PACKAGE_MANIFEST.json"
        if not manifest_path.is_file():
            raise ValueError("Missing PACKAGE_MANIFEST.json")
        manifest = json.loads(manifest_path.read_text())

        for name, digest in manifest["files"].items():
            fpath = self.package / name
            if not fpath.is_file() or self._compute_sha256(fpath) != digest:
                raise ValueError("Package file integrity failed: %s" % name)

        uel_path = self.package / "f42_mixed_uel.for"
        if self._compute_sha256(uel_path).upper() != FROZEN_UEL_SHA256:
            raise ValueError("Frozen production UEL hash mismatch")

        # Load mesh template
        deck_path = self.package / "M1_C4_PACKAGE150_C1_2_CONTINUATION.inp"
        self.template = deck_path.read_text()
        self.mesh = Mesh2D.from_inp(str(deck_path), max_physical_node=7265)

        # Load initial nodal damage d0
        with (self.package / "nodal_phase_field_initial.csv").open() as f:
            rows = list(csv.DictReader(f))
        self.d0 = {int(r["node_id"]): float(r["d"]) for r in rows}
        validate_damage(self.d0, self.mesh.nodes)

        # Load initial displacements u0
        with (self.package / "nodal_displacements_initial.csv").open() as f:
            rows = list(csv.DictReader(f))
        self.u0 = {int(r["node_id"]): (float(r["u1"]), float(r["u2"])) for r in rows}

        # Load initial driving history H0
        with (self.package / "d_lower_bounds.csv").open() as f:
            rows = list(csv.DictReader(f))
        self.h0 = {(int(r["element_id"]), gp): float(r["h0_" + str(col)])
                   for r in rows for gp, col in [(1, 1), (2, 2), (3, 4), (4, 3)]}

    def _deck(self, step_idx, role, damage, active, displacement, history, target_u):
        validate_damage(damage, self.d0)
        blocks = split_keyword_blocks(self.template)
        prefix = []
        for block in blocks:
            key = block.split("\n", 1)[0].strip().lower()
            if key.startswith("*step"):
                break
            if key.startswith(("*boundary", "*include")):
                continue
            if role == "phase" and key.startswith("*equation"):
                continue
            prefix.append(block)

        cards = ["".join(prefix), "*Initial Conditions, type=SOLUTION\n"]
        for eid in sorted(self.mesh.elements):
            cards.append("%d, 0, 0, 0, 0, 0, 0, 0\n" % eid)
            cards.append("0, " + ", ".join("%.17g" % history[eid, g] for g in range(1, 5)) + ", 0, 0, 0\n0, 0, 0\n")

        cards += [
            "*Amplitude, name=FIXED\n0., 1., 1., 1.\n",
            "*Step, name=C1_2_Step%d, nlgeom=NO, inc=1\n" % step_idx,
            "*Static\n1., 1., 1., 1.\n*Boundary, amplitude=FIXED\n"
        ]

        if role == "mechanical":
            cards += [
                "N_BOTTOM, 2, 2, 0.\nN_PIN, 1, 1, 0.\nN_TOP, 1, 1, 0.\n",
                "N_RP, 1, 1, 0.\nN_RP, 2, 2, %.17g\n" % target_u
            ]
            prescribed = damage
        else:
            for n in sorted(self.mesh.nodes):
                cards += [
                    "%d, 1, 1, %.17g\n%d, 2, 2, %.17g\n" %
                    (n, displacement[n][0], n, displacement[n][1])
                ]
            prescribed = {n: damage[n] for n in active}

        cards += ["%d, 3, 3, %.17g\n" % (n, prescribed[n]) for n in sorted(prescribed)]
        cards += [
            "*Output, field, frequency=1\n*Node Output\nU, RF\n",
            "*Element Output, elset=umatelem\nSDV\n",
            "*Node Print, frequency=1\nU\n",
            "*End Step\n"
        ]
        return "".join(cards)

    def _command(self, args, directory, logfile):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError("Stage C1-2 runtime deadline exceeded")
        with logfile.open("x") as log:
            proc = subprocess.Popen(
                args, cwd=str(directory), stdout=log, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, start_new_session=(os.name == "posix")
            )
            try:
                code = proc.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                if os.name == "posix":
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()
                proc.wait()
                raise
            if code != 0:
                raise subprocess.CalledProcessError(code, args)

    def _run_abaqus(self, directory, job, role):
        self._command(
            [self.abaqus, "job=" + job, "input=" + job + ".inp",
             "user=f42_mixed_uel.for", "cpus=1", "memory=%d gb" % self.memory_gb,
             "output_precision=full", "interactive"], directory, directory / "solver.stdout.txt"
        )
        sta = directory / (job + ".sta")
        if not sta.is_file() or "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" not in sta.read_text():
            raise RuntimeError("Abaqus job %s did not complete successfully" % job)

        self._command(
            [self.abaqus, "python", str(self.extractor),
             "--odb", str(directory / (job + ".odb")),
             "--output", str(directory / "endpoint.json"),
             "--physical-nodes", str(len(self.mesh.nodes)),
             "--physical-elements", str(len(self.mesh.elements))],
            directory, directory / "extractor.stdout.txt"
        )
        endpoint = directory / "endpoint.json"
        if not endpoint.is_file():
            raise RuntimeError("Missing endpoint extraction for %s" % job)
        return json.loads(endpoint.read_text())

    def solve_subproblem(self, step_idx, outer, inner, role, damage, active,
                         displacement, history, target_u):
        if time.monotonic() >= self.deadline:
            raise RuntimeError("Stage C1-2 deadline exceeded")

        job = "P150_S%d_%02d_%02d_%s" % (step_idx, outer, inner, role)
        directory = self.output / job
        directory.mkdir(parents=True, exist_ok=True)

        shutil.copyfile(str(self.package / "f42_mixed_uel.for"), str(directory / "f42_mixed_uel.for"))
        text = self._deck(step_idx, role, damage, active, displacement, history, target_u)
        (directory / (job + ".inp")).write_text(text)

        result = self.runner(directory, job, role)
        expected = set(self.mesh.nodes)

        rows = result["nodes"]
        fields = {int(r[0]): tuple(float(x) for x in r[1:]) for r in rows}
        if len(fields) != len(rows) or set(fields) != expected:
            raise ValueError("Endpoint node coverage mismatch")

        if role == "mechanical":
            u = {n: v[:2] for n, v in fields.items()}
            d = dict(damage)
        else:
            d = {n: v[2] for n, v in fields.items()}
            u = {n: v[:2] for n, v in fields.items()}
            validate_damage(d, self.d0)

        record = {"job": job, "role": role, "step": step_idx, "outer": outer,
                  "inner": inner, "endpoint": result}
        (directory / "receipt.json").write_text(json.dumps(record, indent=2))
        return d, u, result

    def solve_step(self, step_info, current_d, current_u, current_h):
        step_idx = step_info["step"]
        target_uy = step_info["target_uy"]

        solver = PDASReEquilibrationSolver(self.mesh, current_d, current_h)
        damage = dict(current_d)
        history = dict(current_h)
        previous_u, previous_h = None, None
        previous_d = dict(damage)

        step_records = []
        step_converged = False

        for outer in range(1, self.max_outer + 1):
            damage, u, endpoint = self.solve_subproblem(
                step_idx, outer, 0, "mechanical", damage, set(damage),
                None, current_h, target_uy
            )
            history = driving_history(self.mesh, u, current_h)
            solver.h_gp = history
            kkt = solver.kkt(damage)

            delta_d = max(abs(damage[n] - previous_d[n]) for n in damage)
            delta_u = max(abs(u[n][i] - previous_u[n][i]) for n in u for i in (0, 1)) if previous_u else None
            delta_h = max(abs(history[k] - previous_h[k]) for k in history) if previous_h else None

            rec = {
                "step": step_idx, "outer": outer, "target_uy": target_uy,
                "delta_d": delta_d, "delta_u": delta_u, "delta_h": delta_h,
                "free_error": kkt["free_error"], "dual_error": kkt["dual_error"]
            }
            step_records.append(rec)
            self.iteration_records.append(rec)
            try:
                (self.output / "live_iteration_telemetry.json").write_text(json.dumps(self.iteration_records, indent=2))
            except Exception:
                pass

            if (previous_u is not None and delta_d <= 1e-5 and delta_u <= 1e-9
                    and delta_h <= 1e-6 and kkt["passed"]):
                step_converged = True
                break

            previous_d, previous_u, previous_h = dict(damage), u, history
            diag, _, _ = solver.assemble_system()
            active = {n for n in damage if damage[n] - kkt["residual"][n] / diag[n] <= current_d[n] + 1e-12}

            for inner in range(1, self.max_phase + 1):
                damage, _, _ = self.solve_subproblem(
                    step_idx, outer, inner, "phase", damage, active, u, history, target_uy
                )
                kkt = solver.kkt(damage)
                step_records[-1]["phase_iterations"] = inner
                if kkt["passed"]:
                    break

        if not step_converged:
            raise RuntimeError("Step %d did not achieve coupled convergence within %d iterations" % (step_idx, self.max_outer))

        rf2 = float(endpoint["rf2_kN"])
        e_el = float(endpoint["elastic_kNmm"])
        e_frac = float(endpoint["fracture_kNmm"])
        e_tot = e_el + e_frac

        summary = {
            "step": step_idx,
            "target_uy_mm": target_uy,
            "rf2_kN": rf2,
            "elastic_energy_kNmm": e_el,
            "fracture_energy_kNmm": e_frac,
            "total_energy_kNmm": e_tot,
            "damage_max": max(damage.values()),
            "min_delta_d": min(damage[n] - current_d[n] for n in damage),
            "converged_outer_iteration": outer,
            "final_delta_h_MPa": delta_h,
            "final_delta_d": delta_d,
            "final_delta_u_mm": delta_u,
        }
        self.step_records.append(summary)
        return damage, u, history, summary

    def run(self):
        self.load()
        self.output.mkdir(parents=True, exist_ok=True)
        self.deadline = time.monotonic() + self.timeout

        current_d = dict(self.d0)
        current_u = dict(self.u0)
        current_h = dict(self.h0)

        for step_info in LOADING_STEPS:
            current_d, current_u, current_h, step_summary = self.solve_step(
                step_info, current_d, current_u, current_h
            )

        # Write final equilibrium checkpoint at uy = 0.002000 mm
        final_checkpoint = {
            "schema": 1,
            "stage": "STAGE_C1_2_FORWARD_CONTINUATION",
            "target_uy_mm": LOADING_STEPS[-1]["target_uy"],
            "displacement": [[n, current_u[n][0], current_u[n][1]] for n in sorted(current_u)],
            "damage": [[n, current_d[n]] for n in sorted(current_d)],
            "history": [[e, g, current_h[e, g]] for e, g in sorted(current_h)],
            "history_semantics": "max(authentic transferred H0, frozen UEL POS_M at converged endpoint)",
            "step_summaries": self.step_records
        }
        cp_path = self.output / "c1_2_continuation_checkpoint.json"
        cp_path.write_text(json.dumps(final_checkpoint, indent=2))

        # Write runtime report
        report = {
            "schema": 1,
            "status": "STAGE_C1_2_PASS",
            "completed_steps": len(self.step_records),
            "target_uy_final_mm": LOADING_STEPS[-1]["target_uy"],
            "steps": self.step_records,
            "checkpoint_sha256": self._compute_sha256(cp_path)
        }
        rep_path = self.output / "runtime_report.json"
        rep_path.write_text(json.dumps(report, indent=2))
        return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Stage C1-2 Forward Continuation Driver")
    parser.add_argument("--package", required=True, help="Package directory path")
    parser.add_argument("--output", required=True, help="Output run directory path")
    parser.add_argument("--extractor", required=True, help="Path to extract_package148_iteration.py")
    parser.add_argument("--abaqus", default="abaqus", help="Abaqus executable name")
    parser.add_argument("--max-outer", type=int, default=30, help="Max outer iterations per step")
    parser.add_argument("--timeout", type=int, default=25200, help="Total execution timeout (seconds)")
    parser.add_argument("--memory-gb", type=int, default=16, help="Abaqus memory limit (GB)")
    args = parser.parse_args()

    controller = StageC12ContinuationController(
        package=args.package, output=args.output, extractor=args.extractor,
        abaqus=args.abaqus, max_outer=args.max_outer, timeout=args.timeout,
        memory_gb=args.memory_gb
    )
    report = controller.run()
    print("Stage C1-2 Continuation Completed: Status=%s" % report["status"])


if __name__ == "__main__":
    main()
