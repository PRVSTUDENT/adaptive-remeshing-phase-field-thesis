#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
driver_package163_c5_continuation.py
Mode-I Method C Cycle 2: Stage C2-1 +5 nm Forward Continuation Driver on C5 Mesh.
Task: F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160
Protocol Version: 2

Solves the coupled staggered PDAS forward continuation problem on Candidate C5 mesh
(12,996 quads, 13,278 nodes, 51,984 integration points) from the accepted Checkpoint 01
(uy = 0.0018603125442191958 mm) to the target +5 nm increment:
  uy_target = 0.0018653125442191958 mm
This exact load matches the accepted C4 R6 load level for direct same-load physical comparison.

Physical Invariants Enforced:
1. Strict pointwise damage irreversibility: d_outer(x) >= d0(x) (healing >= -1e-6).
2. Strict pointwise history monotonicity: H_outer(x) >= H0(x).
3. Active-set Dirichlet obstacle clamp: prescribes self.d0[n] on active nodes.
4. Holds target displacement target_uy = 0.0018653125442191958 mm constant.
5. Immediate atomic checkpoint commitment (converged_checkpoint_02.json) upon coupled acceptance.
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
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.c4_to_c5_spatial_mapping import Mesh2D, QUAD_GP_LOCAL
from scripts.state_transfer.driver_package146_147_pdas_continuation import (
    PDASReEquilibrationSolver, validate_damage, driving_history,
    split_keyword_blocks, FROZEN_UEL_SHA256,
    GC_DEFAULT, L0_DEFAULT, E_MODULUS, NU_POISSON,
    HEALING_TOL
)

# Reference values: C4 R6 accepted endpoint at uy = 0.0018653125442191958 mm
C4_R6_REFERENCE_FORCE_KN = 0.18346779247291461
C4_R6_REFERENCE_TOTAL_ENERGY_KNMM = 0.00022511363524288855

BASELINE_UY_MM = 0.0018603125442191958
TARGET_UY_MM = 0.0018653125442191958  # +5 nm forward increment
DISPLACEMENT_INCREMENT_MM = 0.0000050000000000000


class C5ForwardContinuationController(object):
    """
    Coupled staggered PDAS forward continuation controller on 12,996-quad C5 mesh.
    Advances from uy = 0.0018603125442191958 mm to 0.0018653125442191958 mm (+5 nm).
    """

    def __init__(self, package, output, extractor, abaqus="abaqus",
                 max_outer=100, max_phase=20, timeout=25200, memory_gb=16,
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
        self.iteration_records = []
        self.mesh = None
        self.template = None
        self.baseline_uy = BASELINE_UY_MM
        self.target_uy = TARGET_UY_MM
        self.d0 = {}
        self.h0 = {}
        self.u0 = {}

    def _compute_sha256(self, filepath):
        h = hashlib.sha256()
        with open(str(filepath), "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest().upper()

    def load(self):
        if not self.extractor.is_file():
            raise ValueError(f"Missing endpoint extractor: {self.extractor}")

        manifest_path = self.package / "PACKAGE_MANIFEST.json"
        if not manifest_path.is_file():
            raise ValueError("Missing PACKAGE_MANIFEST.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        for name, digest in manifest["files"].items():
            fpath = self.package / name
            if not fpath.is_file():
                raise FileNotFoundError(f"Missing package file: {name}")
            actual = self._compute_sha256(fpath)
            if actual.lower() != digest.lower():
                raise ValueError(f"Checksum mismatch for {name}: {actual} != {digest}")

        # Verify frozen UEL
        uel_path = self.package / "f42_mixed_uel.for"
        actual_uel = self._compute_sha256(uel_path)
        if actual_uel != FROZEN_UEL_SHA256:
            raise ValueError(f"Frozen UEL hash violation: {actual_uel} != {FROZEN_UEL_SHA256}")

        # Load receiver mesh template from package deck
        deck_path = self.package / "M1_C5_PACKAGE163_C2_1_CONTINUATION.inp"
        if not deck_path.is_file():
            # Fallback to general C5 deck if candidate-specific deck not yet placed
            deck_path = self.package / "M1_C5_PACKAGE160_C2_0_REEQUILIBRATION.inp"
        self.template = deck_path.read_text(encoding="utf-8")
        self.mesh = Mesh2D.from_inp(deck_path, name="C5_Receiver", max_physical_node=13278)
        if len(self.mesh.elements) != 12996 or len(self.mesh.nodes) != 13278:
            raise ValueError(f"Receiver mesh topology mismatch: {len(self.mesh.elements)} elems, {len(self.mesh.nodes)} nodes")

        # Load initial displacement u0
        with open(self.package / "nodal_displacements_initial.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            for r in reader:
                nid = int(r[0])
                self.u0[nid] = (float(r[1]), float(r[2]))

        # Load initial damage d0
        with open(self.package / "nodal_phase_field_initial.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            for r in reader:
                nid = int(r[0])
                self.d0[nid] = float(r[1])
        validate_damage(self.d0, self.mesh.nodes)

        # Load lower bounds (d0, h0)
        with open(self.package / "d_lower_bounds.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            for r in reader:
                eid = int(r[0])
                for k in range(1, 5):
                    self.h0[(eid, k)] = float(r[4 + k])

        if len(self.u0) != 13278 or len(self.d0) != 13278 or len(self.h0) != 51984:
            raise ValueError("Incomplete state coverage on C5 mesh")

        print(f"Loaded Package 163 C5 Forward Continuation: 12996 quads, 13278 nodes, advancing to target_uy = {self.target_uy:.10g} mm (+5 nm)")
        return manifest

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
            cards.append(f"{eid}, 0, 0, 0, 0, 0, 0, 0\n")
            cards.append("0, " + ", ".join(f"{history[eid, g]:.17g}" for g in range(1, 5)) + ", 0, 0, 0\n0, 0, 0\n")

        cards += [
            "*Amplitude, name=FIXED\n0., 1., 1., 1.\n",
            f"*Step, name=C2_1_Step{step_idx}, nlgeom=NO, inc=1\n",
            "*Static\n1., 1., 1., 1.\n*Boundary, amplitude=FIXED\n"
        ]

        if role == "mechanical":
            cards += [
                "N_BOTTOM, 2, 2, 0.\nN_PIN, 1, 1, 0.\nN_TOP, 1, 1, 0.\n",
                f"N_RP, 1, 1, 0.\nN_RP, 2, 2, {target_u:.17g}\n"
            ]
            prescribed = damage
        else:
            for n in sorted(self.mesh.nodes):
                cards += [
                    f"{n}, 1, 1, {displacement[n][0]:.17g}\n{n}, 2, 2, {displacement[n][1]:.17g}\n"
                ]
            # Enforce authentic lower obstacle d0[n] on active set nodes
            prescribed = {n: self.d0[n] for n in active}

        cards += [f"{n}, 3, 3, {prescribed[n]:.17g}\n" for n in sorted(prescribed)]
        cards += [
            "*Output, field, frequency=1\n*Node Output\nU, RF\n",
            "*Element Output, elset=MECH_QUADS\nSDV\n",
            "*Node Print, frequency=1\nU\n",
            "*End Step\n"
        ]
        return "".join(cards)

    def _command(self, args, directory, logfile):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError("Stage C2-1 runtime deadline exceeded")
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
             "user=f42_mixed_uel.for", "cpus=1", f"memory={self.memory_gb} gb",
             "output_precision=full", "interactive"], directory, directory / "solver.stdout.txt"
        )
        sta = directory / (job + ".sta")
        if not sta.is_file() or "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" not in sta.read_text():
            raise RuntimeError(f"Abaqus job {job} did not complete successfully")

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
            raise RuntimeError(f"Missing endpoint extraction for {job}")
        return json.loads(endpoint.read_text())

    def solve_subproblem(self, step_idx, outer, inner, role, damage, active, displacement, history, target_u):
        if time.monotonic() > self.deadline:
            raise RuntimeError("Stage C2-1 runtime deadline exceeded")

        job = f"P163_S{step_idx}_{outer:02d}_{inner:02d}_{role}"
        directory = self.output / job
        directory.mkdir(parents=True, exist_ok=True)

        shutil.copyfile(str(self.package / "f42_mixed_uel.for"), str(directory / "f42_mixed_uel.for"))
        text = self._deck(step_idx, role, damage, active, displacement, history, target_u)
        (directory / f"{job}.inp").write_text(text, encoding="utf-8")

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

    def solve_continuation_step(self):
        """
        Executes coupled staggered PDAS forward continuation at target_uy.
        Immediately commits converged checkpoint upon coupled acceptance.
        """
        self.deadline = time.monotonic() + self.timeout
        self.output.mkdir(parents=True, exist_ok=True)

        step_idx = 1
        target_uy = self.target_uy

        solver = PDASReEquilibrationSolver(self.mesh, self.d0, self.h0)
        damage = dict(self.d0)
        history = dict(self.h0)
        previous_u, previous_h = None, None

        step_records = []
        step_converged = False
        summary = None

        print(f"\nStarting C5 forward continuation (Package 163 Non-Accumulating History) on 12,996-quad mesh (target_uy = {target_uy:.10g} mm)...")

        for outer in range(1, self.max_outer + 1):
            # 1. Mechanical subproblem solve
            damage, u, endpoint = self.solve_subproblem(
                step_idx, outer, 0, "mechanical", damage, set(damage),
                None, self.h0, target_uy
            )

            # 2. Non-accumulating history update:
            # Recompute trial history directly from immutable baseline self.h0:
            # H^(k) = max(H0, psi+(u^(k)))
            zero_baseline = {(e, g): 0.0 for e in self.mesh.elements for g in range(1, 5)}
            psi_k = driving_history(self.mesh, u, zero_baseline)
            history = {k: max(self.h0[k], psi_k[k]) for k in self.h0}
            solver.h_gp = history

            # 3. Evaluate KKT residuals with consistent tolerances under current history
            kkt = solver.kkt(damage, tau_active=1e-6, tau_free=1e-6)

            # 4. Canonical Hintermüller-Ito-Kunisch active-set update:
            c_pdas = 1.0e3    # (kN*mm)^-1
            eps_pdas = 1.0e-6 # dimensionless
            pdas_active = {
                n for n in damage
                if (damage[n] - c_pdas * kkt["residual"][n]) <= (self.d0[n] + eps_pdas)
            }
            pdas_free = set(damage) - pdas_active

            # 5. Staggered phase solve with canonical PDAS active set
            new_damage, _, _ = self.solve_subproblem(
                step_idx, outer, 0, "phase", damage, pdas_active,
                u, history, target_uy
            )

            # Corrected: True post-phase damage increment evaluation
            delta_d = max(abs(new_damage[n] - damage[n]) for n in new_damage)
            delta_u = max(abs(u[n][i] - previous_u[n][i]) for n in u for i in (0, 1)) if previous_u else None
            delta_h = max(abs(history[k] - previous_h[k]) for k in history) if previous_h else None

            damage = new_damage

            rec = {
                "step": step_idx, "outer": outer, "target_uy": target_uy,
                "delta_d": delta_d, "delta_u": delta_u, "delta_h": delta_h,
                "free_error": kkt["free_error"], "dual_error": kkt["dual_error"],
                "pdas_active_count": len(pdas_active), "pdas_free_count": len(pdas_free),
                "kkt_active_count": len(kkt["active"]), "kkt_free_count": len(kkt["free"])
            }
            step_records.append(rec)
            self.iteration_records.append(rec)
            try:
                (self.output / "live_iteration_telemetry.json").write_text(json.dumps(self.iteration_records, indent=2))
            except Exception:
                pass

            print(f"  Outer {outer:02d}: actual delta_d={delta_d:.4e}, delta_u={delta_u or 0.0:.4e}, "
                  f"delta_h={delta_h or 0.0:.4e}, dual_err={kkt['dual_error']:.4e}, "
                  f"free_err={kkt['free_error']:.4e}, PDAS active={len(pdas_active)}, free={len(pdas_free)}")

            # Coupled convergence check:
            if (previous_u is not None and delta_d <= 1e-5 and delta_u <= 1e-9 and (delta_h is None or delta_h <= 1e-4) and kkt["passed"]):
                step_converged = True
                print(f"  Coupled continuation achieved at outer iteration {outer}!")

                rf2 = float(endpoint["rf2_kN"])
                e_el = float(endpoint["elastic_kNmm"])
                e_frac = float(endpoint["fracture_kNmm"])
                e_tot = e_el + e_frac

                force_discrepancy = abs(rf2 - C4_R6_REFERENCE_FORCE_KN) / C4_R6_REFERENCE_FORCE_KN
                energy_discrepancy = abs(e_tot - C4_R6_REFERENCE_TOTAL_ENERGY_KNMM) / C4_R6_REFERENCE_TOTAL_ENERGY_KNMM

                # Thermodynamic verification: H* >= psi+(u*) at all integration points
                thermo_violations = [
                    (e, g) for (e, g), psi in psi_k.items()
                    if history[e, g] - psi < -1e-6
                ]
                thermo_consistent = (len(thermo_violations) == 0)

                # History monotonicity: H* >= H0
                monotonicity_violations = [
                    k for k in history
                    if history[k] - self.h0[k] < -1e-9
                ]
                monotonicity_consistent = (len(monotonicity_violations) == 0)

                force_pass = (force_discrepancy <= 0.02)
                energy_pass = (energy_discrepancy <= 0.02)
                physical_pass = force_pass and energy_pass and thermo_consistent and monotonicity_consistent

                summary = {
                    "schema": 1,
                    "contract": "Package 163 Stage C2-1 +5 nm Forward Continuation",
                    "status": "CONVERGED",
                    "physical_acceptance": "PASS" if physical_pass else "FAIL",
                    "thermodynamic_consistency": "PASS" if thermo_consistent else "FAIL",
                    "thermodynamic_violations_count": len(thermo_violations),
                    "history_monotonicity": "PASS" if monotonicity_consistent else "FAIL",
                    "history_monotonicity_violations_count": len(monotonicity_violations),
                    "step": step_idx,
                    "baseline_uy_mm": self.baseline_uy,
                    "target_uy_mm": target_uy,
                    "increment_mm": target_uy - self.baseline_uy,
                    "converged_outer_iteration": outer,
                    "reaction_force_kN": rf2,
                    "c4_r6_reference_force_kN": C4_R6_REFERENCE_FORCE_KN,
                    "force_discrepancy_pct": force_discrepancy * 100.0,
                    "force_gate_pass": force_pass,
                    "elastic_energy_kNmm": e_el,
                    "fracture_energy_kNmm": e_frac,
                    "total_energy_kNmm": e_tot,
                    "c4_r6_reference_total_energy_kNmm": C4_R6_REFERENCE_TOTAL_ENERGY_KNMM,
                    "energy_discrepancy_pct": energy_discrepancy * 100.0,
                    "energy_gate_pass": energy_pass,
                    "delta_d_inf": delta_d,
                    "delta_u_inf": delta_u,
                    "delta_h_inf": delta_h or 0.0,
                    "kkt_free_error": kkt["free_error"],
                    "kkt_dual_error": kkt["dual_error"],
                    "pdas_active_nodes_count": len(pdas_active),
                    "pdas_free_nodes_count": len(pdas_free),
                    "healing_violations_count": sum(1 for n in damage if damage[n] - self.d0[n] < -HEALING_TOL),
                    "history_monotonicity_violations_count": len(monotonicity_violations)
                }

                # Atomic checkpoint commitment
                chkpt_path = self.output / "converged_checkpoint_02.json"
                chkpt_data = {
                    "schema": 1,
                    "contract": "Package 163 Stage C2-1 Forward Continuation",
                    "stage": "C2-1",
                    "step": step_idx,
                    "baseline_uy_mm": self.baseline_uy,
                    "target_uy_mm": target_uy,
                    "increment_mm": target_uy - self.baseline_uy,
                    "outer_iteration": outer,
                    "coupled_convergence": True,
                    "reaction_force_kN": rf2,
                    "total_energy_kNmm": e_tot,
                    "displacement": [[n, u[n][0], u[n][1]] for n in sorted(u)],
                    "damage": [[n, damage[n]] for n in sorted(damage)],
                    "history": [[e, g, history[e, g]] for e, g in sorted(history)]
                }
                tmp_chkpt = self.output / "converged_checkpoint_02.json.tmp"
                with tmp_chkpt.open("w", encoding="utf-8") as f:
                    json.dump(chkpt_data, f, indent=2)
                os.replace(str(tmp_chkpt), str(chkpt_path))

                summary_path = self.output / "c5_forward_continuation_summary.json"
                tmp_summary = self.output / "c5_forward_continuation_summary.json.tmp"
                with tmp_summary.open("w", encoding="utf-8") as f:
                    json.dump(summary, f, indent=2)
                os.replace(str(tmp_summary), str(summary_path))
                print(f"  Committed checkpoint: {chkpt_path}")
                break

            previous_u = dict(u)
            previous_h = dict(history)

        if not step_converged:
            summary = {
                "schema": 1,
                "status": "NONCONVERGED",
                "reason": f"Maximum outer iterations ({self.max_outer}) reached without meeting coupled tolerances."
            }
            summary_path = self.output / "c5_forward_continuation_summary.json"
            summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
            print("  Stage C2-1 reached max outer iterations without coupled convergence.")

        return summary


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Package 163 C5 Forward Continuation Driver")
    parser.add_argument("--package", required=True, help="Path to Package 163 directory")
    parser.add_argument("--output", required=True, help="Path to output directory")
    parser.add_argument("--extractor", required=True, help="Path to endpoint extractor")
    parser.add_argument("--abaqus", default="abaqus", help="Abaqus command")
    parser.add_argument("--memory-gb", type=int, default=16, help="Memory in GB")
    parser.add_argument("--timeout", type=int, default=25200, help="Timeout in seconds")
    parser.add_argument("--max-outer", type=int, default=100, help="Maximum outer iterations")
    parser.add_argument("--startup-only", action="store_true", help="Perform load and initialization checks only")
    args = parser.parse_args()

    controller = C5ForwardContinuationController(
        package=args.package, output=args.output, extractor=args.extractor,
        abaqus=args.abaqus, max_outer=args.max_outer, timeout=args.timeout,
        memory_gb=args.memory_gb
    )
    manifest = controller.load()
    if args.startup_only:
        print("Startup verification completed successfully.")
        sys.exit(0)

    summary = controller.solve_continuation_step()
    if summary.get("status") != "CONVERGED":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
