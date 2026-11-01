#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
driver_package165_c5_contract_a.py
Mode-I Method C Cycle 2: Candidate Package 165 Contract A Driver.
Task: F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160
Protocol Version: 2

Executes Stage C2-0 coupled staggered PDAS re-equilibration on Candidate Mesh C5
under Contract A (Frozen Transferred History H = H0):
1. Freezes H = H0 during re-equilibration iterations, eliminating trial history ratcheting.
2. Canonical Hintermüller-Ito-Kunisch active-set updates with dimensionally consistent penalty.
3. Pointwise damage irreversibility d >= d0 enforced at all iterations.
4. Coupled convergence gates: delta_d <= 1e-5, delta_u <= 1e-9 mm, dual_error <= 1e-6 kN*mm.
5. Post-convergence thermodynamic verification: independent evaluation of psi+(u*) at all 51,984 GPs
   requiring H0 >= psi+(u*) within numerical tolerance.
6. Physical acceptance gates: force drift <= 2%, total energy drift <= 2%.
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
import argparse
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

# Reference values from Checkpoint 01 (Package 157 R5 Step 1 endpoint)
DONOR_REFERENCE_FORCE_KN = 0.184117075783354
DONOR_REFERENCE_TOTAL_ENERGY_KNMM = 0.00022418821945


class ContractAReEquilibrationSolver(object):
    """
    Contract A solver preserving immutable H0 baseline during re-equilibration.
    """
    def __init__(self, mesh, d0, h0):
        self.mesh = mesh
        self.d0 = dict(d0)
        self.h0 = dict(h0)
        self.delta_h = 0.0


class Package165Driver(object):
    """
    Coupled staggered PDAS re-equilibration controller on 12,996-quad C5 mesh
    implementing Contract A (Frozen Transferred History H = H0).
    """

    def __init__(self, package, output, extractor=None, abaqus="abaqus",
                 max_outer=100, max_phase=20, timeout=25200, memory_gb=16,
                 runner=None):
        self.package = Path(package).resolve()
        self.output = Path(output).resolve()
        if extractor is not None:
            self.extractor = Path(extractor).resolve()
        else:
            self.extractor = self.package / "runtime/scripts/validation/extract_package148_iteration.py"
        self.abaqus = abaqus
        self.max_outer = max_outer
        self.max_phase = max_phase
        self.timeout = timeout
        self.memory_gb = memory_gb
        self.runner = runner or self._run_abaqus
        self.iteration_records = []
        self.mesh = None
        self.template = None
        self.target_uy = None
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
            # Check fallback in repo
            cand = REPO_ROOT / "scripts/validation/extract_package148_iteration.py"
            if cand.is_file():
                self.extractor = cand
            else:
                raise ValueError(f"Missing endpoint extractor: {self.extractor}")

        manifest_path = self.package / "PACKAGE_MANIFEST.json"
        if not manifest_path.is_file():
            raise ValueError("Missing PACKAGE_MANIFEST.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        uel_path = self.package / "f42_mixed_uel.for"
        actual_uel = self._compute_sha256(uel_path)
        if actual_uel.lower() != FROZEN_UEL_SHA256.lower():
            raise ValueError(f"Frozen UEL hash violation: {actual_uel} != {FROZEN_UEL_SHA256}")

        # Locate master template deck
        deck_path = None
        for cand in [self.package / "M1_C5_PACKAGE165_C2_0_REEQUILIBRATION.inp",
                     self.package / "M1_C5_PACKAGE160_C2_0_REEQUILIBRATION.inp"]:
            if cand.is_file():
                deck_path = cand
                break
        if deck_path is None:
            inps = [p for p in self.package.glob("*.inp") if not p.name.endswith("_DC.inp")]
            if inps:
                deck_path = inps[0]
            else:
                raise FileNotFoundError("Could not find master input deck in package")

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

        self.target_uy = float(manifest["donor_source"]["donor_target_uy_mm"])
        print(f"Loaded Package 165 (Contract A): 12996 quads, 13278 nodes, holding target_uy = {self.target_uy:.10g} mm")
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
            f"*Step, name=C2_0_Step{step_idx}, nlgeom=NO, inc=1\n",
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
            # Enforce authentic lower obstacle d0[n] ONLY on active set nodes
            # Nodes outside the active set are free to evolve on DOF 3
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
            raise RuntimeError("Stage C2-0 runtime deadline exceeded")
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

    def solve_subproblem(self, step_idx, outer, inner, role, damage, active,
                         displacement, history, target_u):
        if time.monotonic() >= self.deadline:
            raise RuntimeError("Stage C2-0 deadline exceeded")

        sub_dir = self.output / f"step_{step_idx:02d}_outer_{outer:02d}_{role}"
        sub_dir.mkdir(parents=True, exist_ok=True)
        job = f"M1_C5_P165_{role.upper()}_O{outer:02d}"

        deck_content = self._deck(
            step_idx, role, damage, active, displacement, history, target_u
        )
        (sub_dir / f"{job}.inp").write_text(deck_content, encoding="utf-8")
        shutil.copy2(str(self.package / "f42_mixed_uel.for"), str(sub_dir / "f42_mixed_uel.for"))

        endpoint = self.runner(sub_dir, job, role)

        # Reconstruct updated fields from authentic endpoint
        rows = endpoint.get("nodes", [])
        fields = {int(r[0]): tuple(float(x) for x in r[1:]) for r in rows}

        new_d = dict(damage)
        new_u = dict(displacement) if displacement else dict(self.u0)

        if role == "phase":
            if all(len(v) == 1 for v in fields.values()):
                new_d = {n: v[0] for n, v in fields.items()}
            elif all(len(v) >= 3 for v in fields.values()):
                new_d = {n: v[2] for n, v in fields.items()}
            else:
                new_d = {n: v[-1] for n, v in fields.items()}
            validate_damage(new_d, self.d0)
        elif role == "mechanical":
            new_u = {n: v[:2] for n, v in fields.items()}

        return new_d, new_u, endpoint

    def solve_coupled_equilibration(self):
        self.deadline = time.monotonic() + self.timeout
        self.load()
        self.output.mkdir(parents=True, exist_ok=True)

        step_idx = 1
        target_uy = self.target_uy

        # Under Contract A, solver.h_gp is strictly frozen to transferred baseline self.h0
        solver = PDASReEquilibrationSolver(self.mesh, self.d0, self.h0)
        damage = dict(self.d0)
        history = dict(self.h0)
        previous_u = None
        previous_d = dict(damage)

        step_records = []
        step_converged = False
        summary = None

        print(f"\nStarting coupled PDAS re-equilibration (Contract A) on 12,996-quad mesh (target_uy = {target_uy:.10g} mm)...")

        for outer in range(1, self.max_outer + 1):
            # 1. Mechanical subproblem solve
            damage, u, endpoint = self.solve_subproblem(
                step_idx, outer, 0, "mechanical", damage, set(damage),
                None, self.h0, target_uy
            )

            # 2. Contract A: History H is strictly frozen to transferred baseline H0
            # solver.h_gp remains unchanged (= self.h0) to prevent trial history ratcheting
            solver.h_gp = self.h0

            # 3. Evaluate KKT residuals with consistent tolerances
            kkt = solver.kkt(damage, tau_active=1e-6, tau_free=1e-6)

            # 4. Canonical Hintermüller-Ito-Kunisch active-set update:
            c_pdas = 1.0e3    # (kN*mm)^-1
            eps_pdas = 1.0e-6 # dimensionless
            pdas_active = {
                n for n in damage
                if (damage[n] - c_pdas * kkt["residual"][n]) <= (self.d0[n] + eps_pdas)
            }
            pdas_free = set(damage) - pdas_active

            delta_d = max(abs(damage[n] - previous_d[n]) for n in damage)
            delta_u = max(abs(u[n][i] - previous_u[n][i]) for n in u for i in (0, 1)) if previous_u else None
            delta_h = 0.0 # Strictly zero under Contract A

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

            print(f"  Outer {outer:02d}: delta_d={delta_d:.4e}, delta_u={delta_u or 0.0:.4e}, "
                  f"delta_h={delta_h:.4e}, dual_err={kkt['dual_error']:.4e}, "
                  f"free_err={kkt['free_error']:.4e}, PDAS active={len(pdas_active)}, free={len(pdas_free)}")

            if (previous_u is not None and delta_d <= 1e-5 and delta_u <= 1e-9 and kkt["passed"]):
                step_converged = True
                print(f"  Coupled convergence achieved at outer iteration {outer}!")

                # Synchronized physical evaluation from current outer iteration
                rf2 = float(endpoint["rf2_kN"])
                e_el = float(endpoint["elastic_kNmm"])
                e_frac = float(endpoint["fracture_kNmm"])
                e_tot = e_el + e_frac

                force_discrepancy = abs(rf2 - DONOR_REFERENCE_FORCE_KN) / DONOR_REFERENCE_FORCE_KN
                energy_discrepancy = abs(e_tot - DONOR_REFERENCE_TOTAL_ENERGY_KNMM) / DONOR_REFERENCE_TOTAL_ENERGY_KNMM

                # 5. Post-convergence thermodynamic verification: H0 >= psi+(u*)
                zero_baseline = {(e, g): 0.0 for e in self.mesh.elements for g in range(1, 5)}
                psi_star = driving_history(self.mesh, u, zero_baseline)
                thermo_violations = [
                    (e, g) for (e, g), psi in psi_star.items()
                    if self.h0[e, g] - psi < -1e-6
                ]
                thermo_consistent = (len(thermo_violations) == 0)

                # Physical acceptance gates: <= 2% force discrepancy, <= 2% energy discrepancy, 0 thermo violations
                force_pass = (force_discrepancy <= 0.02)
                energy_pass = (energy_discrepancy <= 0.02)
                physical_pass = force_pass and energy_pass and thermo_consistent

                summary = {
                    "schema": 1,
                    "contract": "Contract A (Frozen Transferred History H = H0)",
                    "status": "CONVERGED",
                    "physical_acceptance": "PASS" if physical_pass else "FAIL",
                    "thermodynamic_consistency": "PASS" if thermo_consistent else "FAIL",
                    "thermodynamic_violations_count": len(thermo_violations),
                    "step": step_idx,
                    "target_uy_mm": target_uy,
                    "converged_outer_iteration": outer,
                    "reaction_force_kN": rf2,
                    "donor_reference_force_kN": DONOR_REFERENCE_FORCE_KN,
                    "force_discrepancy_pct": force_discrepancy * 100.0,
                    "force_gate_pass": force_pass,
                    "elastic_energy_kNmm": e_el,
                    "fracture_energy_kNmm": e_frac,
                    "total_energy_kNmm": e_tot,
                    "donor_reference_total_energy_kNmm": DONOR_REFERENCE_TOTAL_ENERGY_KNMM,
                    "energy_discrepancy_pct": energy_discrepancy * 100.0,
                    "energy_gate_pass": energy_pass,
                    "delta_d_inf": delta_d,
                    "delta_u_inf": delta_u,
                    "delta_h_inf": delta_h,
                    "kkt_free_error": kkt["free_error"],
                    "kkt_dual_error": kkt["dual_error"],
                    "pdas_active_nodes_count": len(pdas_active),
                    "pdas_free_nodes_count": len(pdas_free),
                    "healing_violations_count": sum(1 for n in damage if damage[n] - self.d0[n] < -HEALING_TOL),
                    "history_monotonicity_violations_count": sum(1 for k in history if history[k] - self.h0[k] < -1e-9)
                }

                # Atomic checkpoint commitment
                chkpt_path = self.output / "converged_checkpoint_01.json"
                chkpt_data = {
                    "schema": 1,
                    "contract": "Contract A",
                    "stage": "C2-0",
                    "step": step_idx,
                    "target_uy_mm": target_uy,
                    "outer_iteration": outer,
                    "coupled_convergence": True,
                    "physical_acceptance": summary["physical_acceptance"],
                    "thermodynamic_consistency": summary["thermodynamic_consistency"],
                    "displacement": [[n, u[n][0], u[n][1]] for n in sorted(u)],
                    "damage": [[n, damage[n]] for n in sorted(damage)],
                    "history": [[e, g, self.h0[e, g]] for e, g in sorted(self.h0)]
                }
                tmp_chkpt = self.output / "converged_checkpoint_01.json.tmp"
                with tmp_chkpt.open("w", encoding="utf-8") as f:
                    json.dump(chkpt_data, f, indent=2)
                os.replace(str(tmp_chkpt), str(chkpt_path))

                summary_path = self.output / "re_equilibration_summary.json"
                tmp_summary = self.output / "re_equilibration_summary.json.tmp"
                with tmp_summary.open("w", encoding="utf-8") as f:
                    json.dump(summary, f, indent=2)
                os.replace(str(tmp_summary), str(summary_path))
                print(f"  Committed checkpoint: {chkpt_path} ({summary['physical_acceptance']})")
                break

            # 5. Staggered phase solve for next outer iteration with canonical PDAS active set
            damage, _, _ = self.solve_subproblem(
                step_idx, outer, 0, "phase", damage, pdas_active,
                u, self.h0, target_uy
            )
            previous_d = dict(damage)
            previous_u = dict(u)

        if not step_converged:
            summary = {
                "schema": 1,
                "contract": "Contract A (Frozen Transferred History H = H0)",
                "status": "NONCONVERGED",
                "physical_acceptance": "FAIL",
                "step": step_idx,
                "target_uy_mm": target_uy,
                "max_outer": self.max_outer,
                "pdas_active_count": len(pdas_active),
                "pdas_free_count": len(pdas_free),
                "reason": f"Maximum outer iterations ({self.max_outer}) reached without coupled convergence"
            }
            summary_path = self.output / "re_equilibration_summary.json"
            with summary_path.open("w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
            print(f"  Coupled re-equilibration non-converged within {self.max_outer} outer iterations.")
            sys.exit(1)

        return summary


def parse_args():
    p = argparse.ArgumentParser(description="Package 165 Contract A Driver")
    p.add_argument("--package", required=True, help="Path to package directory")
    p.add_argument("--output", required=True, help="Path to output directory")
    p.add_argument("--extractor", default=None, help="Path to endpoint extractor script")
    p.add_argument("--memory-gb", type=int, default=16, help="Memory in GB")
    p.add_argument("--target-uy", type=float, default=None, help="Target holding displacement [mm]")
    p.add_argument("--max-outer", type=int, default=100, help="Maximum outer iterations")
    p.add_argument("--timeout", type=int, default=25200, help="Timeout in seconds")
    p.add_argument("--abaqus", default="abaqus", help="Abaqus command")
    return p.parse_args()


def main():
    args = parse_args()
    driver = Package165Driver(
        args.package, args.output, extractor=args.extractor,
        abaqus=args.abaqus, max_outer=args.max_outer,
        timeout=args.timeout, memory_gb=args.memory_gb
    )
    driver.solve_coupled_equilibration()


if __name__ == "__main__":
    main()
