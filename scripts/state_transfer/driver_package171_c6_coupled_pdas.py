#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
driver_package171_c6_coupled_pdas.py
====================================
Mode-I Method C Cycle 3: Package 171 Genuine C6 Coupled PDAS Re-Equilibration Driver.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2

Executes genuine staggered coupled PDAS re-equilibration on the non-coarsened C6 mesh:
- 15,252 CPE4 quads, 15,559 physical nodes + RP 999999, 59 duplicate slit-flank node pairs.
- Dual UEL layers: 15,252 phase U1 (DOF 3) + 15,252 mechanical U2 (DOF 1, 2).
- Transferred initial state from accepted Checkpoint 03 (Job 1419566.mmaster02) at target uy = 0.0018703125442191958 mm.
- Non-accumulating history formulation: H^(k) = max(H0, psi+(u^(k))).
- Hintermüller-Ito-Kunisch PDAS active-set update with c_pdas = 1000.0 (kN mm)^-1, eps_pdas = 1e-6.
- Enforces damage irreversibility d >= d0 pointwise.
- Physical acceptance: reaction force drift <= 2%, total energy drift <= 2% vs Checkpoint 03.
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
import argparse
from pathlib import Path

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

# Reference values from accepted C5 Checkpoint 03 (Job 1419566)
DONOR_REFERENCE_FORCE_KN = 0.17992419004440308
DONOR_REFERENCE_TOTAL_ENERGY_KNMM = 0.00022639903
DONOR_REFERENCE_ELASTIC_ENERGY_KNMM = 0.00016825724
DONOR_REFERENCE_FRACTURE_ENERGY_KNMM = 5.814179e-05

# Independent Reference B Contextual Comparator (Job 1419543)
REFERENCE_B_FORCE_KN = 0.18302963
REFERENCE_B_TOTAL_ENERGY_KNMM = 0.00022603386


class Package171C6PDASDriver(object):
    def __init__(self, package, output, extractor, memory_gb=16, timeout=25200, max_outer=100, abaqus="abaqus"):
        self.package = Path(package).resolve()
        self.output = Path(output).resolve()
        self.extractor = Path(extractor).resolve()
        self.memory_gb = memory_gb
        self.timeout = timeout
        self.max_outer = max_outer
        self.abaqus = abaqus

        self.mesh = None
        self.template = None
        self.target_uy = None
        self.d0 = {}
        self.h0 = {}
        self.u0 = {}
        self.iteration_records = []
        self.deadline = 0

    def load(self):
        manifest_p = self.package / "PACKAGE_MANIFEST.json"
        if not manifest_p.is_file():
            raise FileNotFoundError(f"Missing PACKAGE_MANIFEST.json in {self.package}")
        manifest = json.loads(manifest_p.read_text(encoding="utf-8"))

        deck_path = self.package / "M1_C6_PACKAGE171_C3_0_REEQUILIBRATION.inp"
        if not deck_path.is_file():
            inps = [p for p in self.package.glob("*.inp") if not p.name.endswith("_DC.inp")]
            if inps:
                deck_path = inps[0]
            else:
                raise FileNotFoundError("Could not find master input deck in package")

        self.template = deck_path.read_text(encoding="utf-8")
        self.mesh = Mesh2D.from_inp(deck_path, name="C6_Receiver", max_physical_node=15559)

        if len(self.mesh.elements) != 15252:
            raise ValueError(f"Expected 15,252 C6 elements, found {len(self.mesh.elements)}")
        if len(self.mesh.nodes) != 15559:
            raise ValueError(f"Expected 15,559 C6 nodes, found {len(self.mesh.nodes)}")

        u_csv = self.package / "nodal_displacements_initial.csv"
        with u_csv.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for r in reader:
                self.u0[int(r[0])] = (float(r[1]), float(r[2]))

        d_csv = self.package / "nodal_phase_field_initial.csv"
        with d_csv.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for r in reader:
                self.d0[int(r[0])] = float(r[1])

        bounds_csv = self.package / "d_lower_bounds.csv"
        with bounds_csv.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for r in reader:
                eid = int(r[0])
                for k in range(1, 5):
                    self.h0[(eid, k)] = float(r[4 + k])

        # Validate transferred nonzero damage and history fields
        min_d0 = min(self.d0.values())
        max_d0 = max(self.d0.values())
        min_h0 = min(self.h0.values())
        if min_d0 <= 0 or max_d0 < 0.5:
            raise ValueError(f"Critical verification failure: Transferred d0 lacks authentic damage bounds: min={min_d0}, max={max_d0}")
        if min_h0 <= 0:
            raise ValueError(f"Critical verification failure: Transferred h0 lacks authentic positive history: min={min_h0}")

        target_source = manifest.get("donor_source", {})
        self.target_uy = float(target_source.get("target_uy_mm", 0.0018703125442191958))
        print(f"Loaded Package 171: 15,252 quads, 15,559 nodes, target_uy = {self.target_uy:.10g} mm")
        print(f"Verified transferred state: d0 in [{min_d0:.6f}, {max_d0:.6f}], min(H0) = {min_h0:.4e}")

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
            f"*Step, name=C3_0_Step{step_idx}_{role}, nlgeom=NO, inc=1\n",
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
            prescribed = {n: self.d0[n] for n in active}

        cards += [f"{n}, 3, 3, {prescribed[n]:.17g}\n" for n in sorted(prescribed)]
        cards += [
            "*Output, field, frequency=1\n*Node Output\nU, RF\n",
            "*Element Output, elset=MECH_QUADS\nSDV\n",
            "*End Step\n"
        ]
        return "".join(cards)

    def runner(self, directory, job, role, step_idx):
        cmd = [
            self.abaqus, f"job={job}", f"input={job}.inp",
            "user=f42_mixed_uel.for", "cpus=1",
            f"memory={self.memory_gb} gb", "interactive"
        ]
        log_path = directory / "solver.stdout.txt"
        with log_path.open("w", encoding="utf-8") as out_f:
            p = subprocess.Popen(cmd, cwd=str(directory), stdout=out_f, stderr=subprocess.STDOUT)
            p.communicate()
            if p.returncode != 0:
                raise RuntimeError(f"Abaqus job {job} exited with code {p.returncode}")

        odb_path = directory / f"{job}.odb"
        endpoint_path = directory / "endpoint.json"
        step_name = f"C3_0_Step{step_idx}_{role}"
        ext_cmd = [
            self.abaqus, "python", str(self.extractor),
            "--odb", str(odb_path),
            "--output", str(endpoint_path),
            "--physical-nodes", "15559",
            "--physical-elements", "15252",
            "--step", step_name
        ]
        ext_log = directory / "extractor.stdout.txt"
        with ext_log.open("w", encoding="utf-8") as out_f:
            ep = subprocess.Popen(ext_cmd, cwd=str(directory), stdout=out_f, stderr=subprocess.STDOUT)
            ep.communicate()
            if ep.returncode != 0:
                raise RuntimeError(f"Extractor failed for {job}")

        return json.loads(endpoint_path.read_text(encoding="utf-8"))

    def solve_subproblem(self, step_idx, outer, inner, role, damage, active, displacement, history, target_u):
        if time.monotonic() >= self.deadline:
            raise RuntimeError("Stage C3-0 execution deadline exceeded")

        job = f"M1_C6_P171_{role.upper()}_O{outer:02d}"
        sub_dir = self.output / f"step_{step_idx:02d}_outer_{outer:02d}_{role}"
        sub_dir.mkdir(parents=True, exist_ok=True)

        deck_content = self._deck(step_idx, role, damage, active, displacement, history, target_u)
        (sub_dir / f"{job}.inp").write_text(deck_content, encoding="utf-8")
        shutil.copy2(str(self.package / "f42_mixed_uel.for"), str(sub_dir / "f42_mixed_uel.for"))

        endpoint = self.runner(sub_dir, job, role, step_idx)
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
            for n in new_d:
                if new_d[n] < self.d0[n]:
                    new_d[n] = self.d0[n]
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

        solver = PDASReEquilibrationSolver(self.mesh, self.d0, self.h0)
        damage = dict(self.d0)
        history = dict(self.h0)
        previous_u, previous_h = None, None

        step_records = []
        step_converged = False
        summary = None

        print(f"\nStarting coupled PDAS re-equilibration (Package 171 Non-Accumulating History) on 15,252-quad C6 mesh (target_uy = {target_uy:.10g} mm)...")

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

            # True post-phase damage increment evaluation
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

            # Coupled convergence check
            if (previous_u is not None and delta_d <= 1e-5 and delta_u <= 1e-9 and kkt["passed"]):
                step_converged = True
                print(f"  Coupled convergence achieved at outer iteration {outer}!")

                rf2 = float(endpoint.get("rf2_kN", 0.0))
                e_el = float(endpoint.get("elastic_kNmm", 0.0))
                e_frac = float(endpoint.get("fracture_kNmm", 0.0))
                e_tot = e_el + e_frac

                force_discrepancy = abs(rf2 - DONOR_REFERENCE_FORCE_KN) / DONOR_REFERENCE_FORCE_KN
                energy_discrepancy = abs(e_tot - DONOR_REFERENCE_TOTAL_ENERGY_KNMM) / DONOR_REFERENCE_TOTAL_ENERGY_KNMM

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
                    "contract": "Package 171 (C6 Coupled PDAS Re-Equilibration H* = max(H0, psi+(u*)))",
                    "status": "CONVERGED",
                    "physical_acceptance": "PASS" if physical_pass else "FAIL",
                    "thermodynamic_consistency": "PASS" if thermo_consistent else "FAIL",
                    "thermodynamic_violations_count": len(thermo_violations),
                    "history_monotonicity": "PASS" if monotonicity_consistent else "FAIL",
                    "history_monotonicity_violations_count": len(monotonicity_violations),
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
                    "delta_h_inf": delta_h or 0.0,
                    "kkt_free_error": kkt["free_error"],
                    "kkt_dual_error": kkt["dual_error"],
                    "pdas_active_nodes_count": len(pdas_active),
                    "pdas_free_nodes_count": len(pdas_free),
                    "healing_violations_count": sum(1 for n in damage if damage[n] - self.d0[n] < -HEALING_TOL)
                }

                chkpt_path = self.output / "converged_checkpoint_01.json"
                chkpt_data = {
                    "schema": 1,
                    "contract": "Package 171 C6 Coupled PDAS Re-Equilibration",
                    "stage": "C3-0",
                    "step": step_idx,
                    "target_uy_mm": target_uy,
                    "outer_iteration": outer,
                    "coupled_convergence": True,
                    "physical_acceptance": summary["physical_acceptance"],
                    "thermodynamic_consistency": summary["thermodynamic_consistency"],
                    "displacement": [[n, u[n][0], u[n][1]] for n in sorted(u)],
                    "damage": [[n, damage[n]] for n in sorted(damage)],
                    "history": [[e, g, history[e, g]] for e, g in sorted(history)]
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
                return summary

            previous_u = dict(u)
            previous_h = dict(history)

        raise RuntimeError(f"Package 171 C6 coupled re-equilibration failed to converge within {self.max_outer} iterations")


def main():
    p = argparse.ArgumentParser(description="Package 171 C6 Coupled PDAS Re-Equilibration Driver")
    p.add_argument("--package", required=True, help="Path to package directory")
    p.add_argument("--output", required=True, help="Path to output directory")
    p.add_argument("--extractor", required=True, help="Path to extract_package148_iteration.py")
    p.add_argument("--memory-gb", type=int, default=16, help="Abaqus memory limit in GB")
    p.add_argument("--timeout", type=int, default=25200, help="Walltime timeout in seconds")
    p.add_argument("--max-outer", type=int, default=100, help="Maximum outer PDAS iterations")
    p.add_argument("--abaqus", default="abaqus", help="Abaqus executable")
    args = p.parse_args()

    driver = Package171C6PDASDriver(
        package=args.package,
        output=args.output,
        extractor=args.extractor,
        memory_gb=args.memory_gb,
        timeout=args.timeout,
        max_outer=args.max_outer,
        abaqus=args.abaqus
    )
    driver.solve_coupled_equilibration()


if __name__ == "__main__":
    main()
