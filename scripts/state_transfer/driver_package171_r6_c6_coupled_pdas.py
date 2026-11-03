#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
driver_package171_r6_c6_coupled_pdas.py
=======================================
Mode-I Method C Cycle 3: Package 171-R6 Genuine C6 Coupled PDAS Re-Equilibration Driver.
Task: F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION -> R6 Candidate Qualification
Protocol Version: 2

Remediates the Phase-Field Data-Integrity Defect from Independent Review HND-F1602-R5-REVIEW-FD983824:
1. Fail-closed phase decoding:
   - Validates exactly 15,559 unique physical-node records matching receiver mesh nodes.
   - Rejects duplicate node records, missing nodes, unexpected nodes, and nonfinite values (NaN/Inf).
   - For phase subproblem: accepts ONLY explicitly verified damage-output layouts:
     * Documented 1-component scalar damage field (d)
     * Complete >=3 component displacement field with damage in U3 (index 2)
   - Rejects two-component phase output (U1, U2), mixed component counts, incomplete U3 coverage,
     and ambiguous extractor output. Never interprets v[-1] as damage by default.
   - Fails closed before clipping against d0, updating the damage field, or evaluating convergence.
   - Preserves original endpoint and provides exact diagnostic failure messages.
2. Preserves verified R5 remediations:
   - Restores distinct Gauss-point history loading from r[4+g] (61,008 GP histories across 15,252 quads).
   - Preserves string-based split_keyword_blocks() handling for mechanical and phase decks.
   - Preserves element-level *Initial Conditions, type=SOLUTION serialization (16 SDVs per quad).
   - Preserves extractor CLI flags (--physical-nodes 15559, --physical-elements 15252, --step).
3. Preserves R4/R5 rigorous acceptance logic:
   - Coupled consistency: delta_u <= 1e-9 mm, delta_h <= 1e-4 MPa.
   - Post-relaxation / final KKT stationarity <= 1e-6.
   - Thermodynamic consistency: H* >= psi+(u*) at all integration points.
   - History monotonicity: H* >= H0 (0 violations).
   - Damage irreversibility: healing violations == 0 (tolerance 1e-6).
   - Force and energy drift <= 2.0% relative to C5 donor reference.
   - Gated checkpoint commitment strictly conditional on physical_pass == True.
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


class Package171R6C6PDASDriver(object):
    def __init__(self, package, output, extractor, memory_gb=16, timeout=25200, max_outer=100, damping_omega_d=0.5, abaqus="abaqus"):
        self.package = Path(package).resolve()
        self.output = Path(output).resolve()
        self.extractor = Path(extractor).resolve()
        self.memory_gb = memory_gb
        self.timeout = timeout
        self.max_outer = max_outer
        self.damping_omega_d = float(damping_omega_d)
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
                if r:
                    self.u0[int(r[0])] = (float(r[1]), float(r[2]))

        d_csv = self.package / "nodal_phase_field_initial.csv"
        with d_csv.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for r in reader:
                if r:
                    self.d0[int(r[0])] = float(r[1])

        bounds_csv = self.package / "d_lower_bounds.csv"
        with bounds_csv.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)
            for r in reader:
                if r:
                    eid = int(r[0])
                    for k in range(1, 5):
                        self.h0[(eid, k)] = float(r[4 + k])

        if len(self.h0) != 61008:
            raise ValueError(f"Expected 61,008 Gauss-point histories (15,252 * 4), found {len(self.h0)}")

        # Validate transferred nonzero damage and history fields
        min_d0 = min(self.d0.values())
        max_d0 = max(self.d0.values())
        min_h0 = min(self.h0.values())
        max_h0 = max(self.h0.values())
        if min_d0 <= 0 or max_d0 < 0.5:
            raise ValueError(f"Critical verification failure: Transferred d0 lacks authentic damage bounds: min={min_d0}, max={max_d0}")
        if min_h0 <= 0:
            raise ValueError(f"Critical verification failure: Transferred h0 lacks authentic positive history: min={min_h0}")

        # Verify authentic nonuniformity of GP histories
        nonuniform_count = sum(
            1 for eid in self.mesh.elements
            if len({self.h0[(eid, g)] for g in range(1, 5)}) > 1
        )

        target_source = manifest.get("donor_source", {})
        self.target_uy = float(target_source.get("target_uy_mm", 0.0018703125442191958))
        print(f"Loaded Package 171-R6: 15,252 quads, 15,559 nodes, target_uy = {self.target_uy:.10g} mm")
        print(f"Verified transferred state: d0 in [{min_d0:.6f}, {max_d0:.6f}], H0 in [{min_h0:.4e}, {max_h0:.4e}]")
        print(f"Nonuniform history elements: {nonuniform_count} of {len(self.mesh.elements)}")
        print(f"Damage under-relaxation parameter omega_d = {self.damping_omega_d:.4f}")

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

    def finalize_coupled_acceptance(
        self, u_staggered, history_staggered, damage_relaxed, consistent_u,
        consistent_endpoint, solver, step_idx, outer, target_uy,
        delta_d=0.0, delta_u=0.0, delta_h=0.0, pdas_active_count=0, pdas_free_count=0
    ):
        """
        Executes final coupled-field consistency verification and evaluates joint physical acceptance.
        Atomic serialization of converged_checkpoint_01.json strictly requires all criteria to pass.
        """
        # 1. Final mechanical displacement consistency: ||u_final - u_staggered||_inf <= 1e-9 mm
        max_consistency_delta_u = max(
            abs(consistent_u[n][i] - u_staggered[n][i])
            for n in u_staggered for i in (0, 1)
        )
        consistency_u_pass = (max_consistency_delta_u <= 1e-9)
        print(f"  Coupled-field displacement consistency: max delta_u = {max_consistency_delta_u:.4e} mm (pass={consistency_u_pass})")

        # 2. Final history and history consistency: ||H_final - H_staggered||_inf <= 1e-4 MPa
        zero_baseline = {(e, g): 0.0 for e in self.mesh.elements for g in range(1, 5)}
        psi_final = driving_history(self.mesh, consistent_u, zero_baseline)
        history_final = {k: max(self.h0[k], psi_final[k]) for k in self.h0}
        max_consistency_delta_h = max(
            abs(history_final[k] - history_staggered[k]) for k in history_staggered
        )
        consistency_h_pass = (max_consistency_delta_h <= 1e-4)
        print(f"  Coupled-field history consistency: max delta_H = {max_consistency_delta_h:.4e} MPa (pass={consistency_h_pass})")

        # 3. Final KKT stationarity evaluated on relaxed damage under final history H*
        solver.h_gp = history_final
        kkt_final = solver.kkt(damage_relaxed, tau_active=1e-6, tau_free=1e-6)
        kkt_final_pass = (
            kkt_final["passed"] and
            kkt_final["free_error"] <= 1e-6 and
            kkt_final["dual_error"] <= 1e-6 and
            kkt_final["complementarity"] <= 1e-6
        )
        print(f"  Final-state KKT stationarity: free_err={kkt_final['free_error']:.4e}, "
              f"dual_err={kkt_final['dual_error']:.4e}, comp={kkt_final['complementarity']:.4e} (pass={kkt_final_pass})")

        # 4. Forces and energies from final mechanical solve
        rf2 = float(consistent_endpoint.get("rf2_kN", 0.0))
        e_el = float(consistent_endpoint.get("elastic_kNmm", 0.0))
        e_frac = float(consistent_endpoint.get("fracture_kNmm", 0.0))
        e_tot = e_el + e_frac

        force_discrepancy = abs(rf2 - DONOR_REFERENCE_FORCE_KN) / DONOR_REFERENCE_FORCE_KN
        energy_discrepancy = abs(e_tot - DONOR_REFERENCE_TOTAL_ENERGY_KNMM) / DONOR_REFERENCE_TOTAL_ENERGY_KNMM

        force_pass = (force_discrepancy <= 0.02)
        energy_pass = (energy_discrepancy <= 0.02)

        # 5. Thermodynamic verification: H* >= psi+(u*) at all integration points
        thermo_violations = [
            (e, g) for (e, g), psi in psi_final.items()
            if history_final[e, g] - psi < -1e-6
        ]
        thermo_consistent = (len(thermo_violations) == 0)

        # 6. History monotonicity: H* >= H0
        monotonicity_violations = [
            k for k in history_final
            if history_final[k] - self.h0[k] < -1e-9
        ]
        monotonicity_consistent = (len(monotonicity_violations) == 0)

        # 7. Healing violations check: d* >= d0
        healing_violations_count = sum(1 for n in damage_relaxed if damage_relaxed[n] - self.d0[n] < -HEALING_TOL)
        healing_pass = (healing_violations_count == 0)

        # Joint Physical Acceptance Predicate (all gates required)
        physical_pass = (
            force_pass and
            energy_pass and
            thermo_consistent and
            monotonicity_consistent and
            healing_pass and
            kkt_final_pass and
            consistency_u_pass and
            consistency_h_pass
        )

        summary = {
            "schema": 1,
            "contract": f"Package 171-R6 (C6 Coupled PDAS Re-Equilibration omega_d = {self.damping_omega_d:.2f})",
            "status": "CONVERGED",
            "damping_omega_d": self.damping_omega_d,
            "coupled_convergence": True,
            "physical_acceptance": "PASS" if physical_pass else "FAIL",
            "thermodynamic_consistency": "PASS" if thermo_consistent else "FAIL",
            "thermodynamic_violations_count": len(thermo_violations),
            "history_monotonicity": "PASS" if monotonicity_consistent else "FAIL",
            "history_monotonicity_violations_count": len(monotonicity_violations),
            "healing_violations_count": healing_violations_count,
            "healing_pass": healing_pass,
            "kkt_final_pass": kkt_final_pass,
            "coupled_field_consistency_u_pass": consistency_u_pass,
            "coupled_field_consistency_delta_u_mm": max_consistency_delta_u,
            "coupled_field_consistency_h_pass": consistency_h_pass,
            "coupled_field_consistency_delta_h_MPa": max_consistency_delta_h,
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
            "kkt_free_error": kkt_final["free_error"],
            "kkt_dual_error": kkt_final["dual_error"],
            "kkt_complementarity": kkt_final["complementarity"],
            "pdas_active_nodes_count": pdas_active_count,
            "pdas_free_nodes_count": pdas_free_count
        }

        chkpt_path = self.output / "converged_checkpoint_01.json"
        if physical_pass:
            # Serialized ONLY when physical acceptance strictly passes
            chkpt_data = {
                "schema": 1,
                "contract": "Package 171-R6 C6 Coupled PDAS Re-Equilibration",
                "damping_omega_d": self.damping_omega_d,
                "stage": "C3-0",
                "step": step_idx,
                "target_uy_mm": target_uy,
                "outer_iteration": outer,
                "coupled_convergence": True,
                "physical_acceptance": "PASS",
                "thermodynamic_consistency": "PASS",
                "displacement": [[n, consistent_u[n][0], consistent_u[n][1]] for n in sorted(consistent_u)],
                "damage": [[n, damage_relaxed[n]] for n in sorted(damage_relaxed)],
                "history": [[e, g, history_final[e, g]] for e, g in sorted(history_final)]
            }
            tmp_chkpt = self.output / "converged_checkpoint_01.json.tmp"
            with tmp_chkpt.open("w", encoding="utf-8") as f:
                json.dump(chkpt_data, f, indent=2)
            os.replace(str(tmp_chkpt), str(chkpt_path))
            print(f"  Physical acceptance verified: committed accepted checkpoint {chkpt_path}")
        else:
            if chkpt_path.is_file():
                chkpt_path.unlink()
            print(f"  PHYSICAL ACCEPTANCE FAILED! Checkpoint {chkpt_path} suppressed.")

        summary_path = self.output / "re_equilibration_summary.json"
        tmp_summary = self.output / "re_equilibration_summary.json.tmp"
        with tmp_summary.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        os.replace(str(tmp_summary), str(summary_path))

        return summary, physical_pass

    def solve_subproblem(self, step_idx, outer, inner, role, damage, active, displacement, history, target_u):
        if time.monotonic() >= self.deadline:
            raise RuntimeError("Stage C3-0 execution deadline exceeded")

        job = f"M1_C6_P171_R6_{role.upper()}_O{outer:02d}"
        if inner > 0:
            job += f"_I{inner:02d}"
        sub_dir = self.output / f"step_{step_idx:02d}_outer_{outer:02d}_{role}"
        if inner > 0:
            sub_dir = self.output / f"step_{step_idx:02d}_outer_{outer:02d}_{role}_consistency"
        sub_dir.mkdir(parents=True, exist_ok=True)

        deck_content = self._deck(step_idx, role, damage, active, displacement, history, target_u)
        (sub_dir / f"{job}.inp").write_text(deck_content, encoding="utf-8")
        shutil.copy2(str(self.package / "f42_mixed_uel.for"), str(sub_dir / "f42_mixed_uel.for"))

        endpoint = self.runner(sub_dir, job, role, step_idx)
        rows = endpoint.get("nodes", [])

        # 1. Require exactly 15,559 physical-node records matching receiver mesh node IDs
        node_ids_raw = [r[0] for r in rows]
        if len(node_ids_raw) != len(set(node_ids_raw)):
            raise ValueError(
                f"solve_subproblem({role}): duplicated node records in extractor output: "
                f"total={len(node_ids_raw)}, unique={len(set(node_ids_raw))}"
            )

        extracted_nodes = set(int(r[0]) for r in rows)
        expected_nodes = set(self.d0.keys())
        if len(extracted_nodes) != 15559 or extracted_nodes != expected_nodes:
            missing = expected_nodes - extracted_nodes
            unexpected = extracted_nodes - expected_nodes
            raise ValueError(
                f"solve_subproblem({role}): expected exactly 15,559 unique physical-node records matching receiver mesh, "
                f"got {len(extracted_nodes)} (missing={len(missing)}, unexpected={len(unexpected)})"
            )

        # 2. Reject nonfinite values
        fields = {}
        for r in rows:
            nid = int(r[0])
            vals = tuple(float(x) for x in r[1:])
            for val in vals:
                if math.isnan(val) or math.isinf(val):
                    raise ValueError(f"solve_subproblem({role}): nonfinite value {val} at node {nid}")
            fields[nid] = vals

        new_d = dict(damage)
        new_u = dict(displacement) if displacement else dict(self.u0)

        # 3. For phase subproblem: accept ONLY explicitly verified damage-output layouts
        if role == "phase":
            comp_lengths = set(len(v) for v in fields.values())
            if len(comp_lengths) != 1:
                raise ValueError(
                    f"solve_subproblem(phase): mixed component counts across nodes: {comp_lengths}; "
                    f"rejecting inconsistent phase-field output"
                )
            comp_len = next(iter(comp_lengths))
            if comp_len == 1:
                # Documented damage-only scalar field
                new_d = {n: v[0] for n, v in fields.items()}
            elif comp_len >= 3:
                # Complete >=3 component field with damage extracted from U3 (index 2)
                new_d = {n: v[2] for n, v in fields.items()}
            elif comp_len == 2:
                raise ValueError(
                    f"solve_subproblem(phase): rejected two-component phase output (U1, U2); "
                    f"cannot interpret mechanical displacement as phase damage U3"
                )
            else:
                raise ValueError(
                    f"solve_subproblem(phase): unsupported phase component count {comp_len}"
                )

            # Fail-closed checks passed. Now apply irreversible clipping against d0 and validate bounds
            for n in new_d:
                if new_d[n] < self.d0[n]:
                    new_d[n] = self.d0[n]
            validate_damage(new_d, self.d0)

        elif role == "mechanical":
            comp_lengths = set(len(v) for v in fields.values())
            if any(len(v) < 2 for v in fields.values()):
                raise ValueError(
                    f"solve_subproblem(mechanical): incomplete displacement output; all nodes must have >= 2 components, got lengths {comp_lengths}"
                )
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

        print(f"\nStarting coupled PDAS re-equilibration (Package 171-R6 Fail-Closed Phase Decoding Damped omega_d = {self.damping_omega_d}) on 15,252-quad C6 mesh (target_uy = {target_uy:.10g} mm)...")

        for outer in range(1, self.max_outer + 1):
            # 1. Mechanical subproblem solve
            damage, u, endpoint = self.solve_subproblem(
                step_idx, outer, 0, "mechanical", damage, set(damage),
                None, self.h0, target_uy
            )

            # 2. Non-accumulating history update:
            # H^(k) = max(H0, psi+(u^(k)))
            zero_baseline = {(e, g): 0.0 for e in self.mesh.elements for g in range(1, 5)}
            psi_k = driving_history(self.mesh, u, zero_baseline)
            history = {k: max(self.h0[k], psi_k[k]) for k in self.h0}
            solver.h_gp = history

            # 3. Pre-update KKT residuals for PDAS active-set partitioning
            kkt_pre = solver.kkt(damage, tau_active=1e-6, tau_free=1e-6)

            # 4. Canonical Hintermüller-Ito-Kunisch active-set update:
            c_pdas = 1.0e3    # (kN*mm)^-1
            eps_pdas = 1.0e-6 # dimensionless
            pdas_active = {
                n for n in damage
                if (damage[n] - c_pdas * kkt_pre["residual"][n]) <= (self.d0[n] + eps_pdas)
            }
            pdas_free = set(damage) - pdas_active

            # 5. Staggered phase solve with canonical PDAS active set
            new_damage_pdas, _, _ = self.solve_subproblem(
                step_idx, outer, 0, "phase", damage, pdas_active,
                u, history, target_uy
            )

            # 6. Damped Picard Under-Relaxation (omega_d = 0.5):
            # d^{(k+1)} = (1 - omega_d) * d^{(k)} + omega_d * d_PDAS^{(k+1)}
            relaxed_damage = {}
            for n in new_damage_pdas:
                val = (1.0 - self.damping_omega_d) * damage[n] + self.damping_omega_d * new_damage_pdas[n]
                relaxed_damage[n] = min(1.0, max(self.d0[n], val))

            # Post-relaxation KKT stationarity evaluation on relaxed_damage
            kkt_post = solver.kkt(relaxed_damage, tau_active=1e-6, tau_free=1e-6)

            # Increments
            delta_d = max(abs(relaxed_damage[n] - damage[n]) for n in relaxed_damage)
            delta_u = max(abs(u[n][i] - previous_u[n][i]) for n in u for i in (0, 1)) if previous_u else None
            delta_h = max(abs(history[k] - previous_h[k]) for k in history) if previous_h else None

            damage = relaxed_damage

            rec = {
                "step": step_idx, "outer": outer, "target_uy": target_uy,
                "damping_omega_d": self.damping_omega_d,
                "delta_d": delta_d, "delta_u": delta_u, "delta_h": delta_h,
                "free_error": kkt_post["free_error"], "dual_error": kkt_post["dual_error"],
                "complementarity": kkt_post["complementarity"],
                "kkt_post_passed": kkt_post["passed"],
                "pdas_active_count": len(pdas_active), "pdas_free_count": len(pdas_free),
                "kkt_active_count": len(kkt_post["active"]), "kkt_free_count": len(kkt_post["free"])
            }
            step_records.append(rec)
            self.iteration_records.append(rec)
            try:
                (self.output / "live_iteration_telemetry.json").write_text(json.dumps(self.iteration_records, indent=2))
            except Exception:
                pass

            print(f"  Outer {outer:02d}: actual delta_d={delta_d:.4e}, delta_u={delta_u or 0.0:.4e}, "
                  f"delta_h={delta_h or 0.0:.4e}, post_dual_err={kkt_post['dual_error']:.4e}, "
                  f"post_free_err={kkt_post['free_error']:.4e}, post_kkt_pass={kkt_post['passed']}, "
                  f"PDAS active={len(pdas_active)}, free={len(pdas_free)}")

            # Strict coupled convergence check with POST-UPDATE KKT enforcement
            if (previous_u is not None and
                delta_d <= 1e-5 and
                delta_u <= 1e-9 and
                (delta_h is not None and delta_h <= 1e-4) and
                kkt_post["passed"]):
                step_converged = True
                print(f"  Coupled convergence achieved at outer iteration {outer}!")

                # Final coupled-field consistency equilibration
                print("  Executing final coupled-field consistency equilibration step with converged damage field...")
                consistent_d, consistent_u, consistent_endpoint = self.solve_subproblem(
                    step_idx, outer, 1, "mechanical", damage, set(damage),
                    None, history, target_uy
                )

                summary, physical_pass = self.finalize_coupled_acceptance(
                    u_staggered=u,
                    history_staggered=history,
                    damage_relaxed=damage,
                    consistent_u=consistent_u,
                    consistent_endpoint=consistent_endpoint,
                    solver=solver,
                    step_idx=step_idx,
                    outer=outer,
                    target_uy=target_uy,
                    delta_d=delta_d,
                    delta_u=delta_u,
                    delta_h=delta_h,
                    pdas_active_count=len(pdas_active),
                    pdas_free_count=len(pdas_free)
                )

                if not physical_pass:
                    raise RuntimeError(
                        f"Package 171-R6 coupled convergence achieved at outer {outer}, but physical acceptance failed: "
                        f"force={summary['force_gate_pass']}, energy={summary['energy_gate_pass']}, "
                        f"thermo={summary['thermodynamic_consistency']}, monotonicity={summary['history_monotonicity']}, "
                        f"healing={summary['healing_pass']}, kkt={summary['kkt_final_pass']}, "
                        f"consistency_u={summary['coupled_field_consistency_u_pass']}, "
                        f"consistency_h={summary['coupled_field_consistency_h_pass']}"
                    )
                break

            previous_u = dict(u)
            previous_h = dict(history)

        if not step_converged:
            summary = {
                "schema": 1,
                "contract": f"Package 171-R6 (C6 Coupled PDAS Re-Equilibration omega_d = {self.damping_omega_d:.2f})",
                "status": "NONCONVERGED",
                "damping_omega_d": self.damping_omega_d,
                "outer_iterations_completed": self.max_outer,
                "target_uy_mm": target_uy,
                "last_delta_d": delta_d,
                "last_delta_u": delta_u,
                "last_delta_h": delta_h,
                "last_kkt_free_error": kkt_post["free_error"],
                "last_kkt_dual_error": kkt_post["dual_error"]
            }
            summary_path = self.output / "re_equilibration_summary.json"
            summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
            raise RuntimeError(f"Package 171-R6 C6 coupled re-equilibration failed to converge within {self.max_outer} iterations")

        return summary


def main():
    parser = argparse.ArgumentParser(description="Package 171-R6 C6 Coupled PDAS Re-Equilibration Driver")
    parser.add_argument("--package", required=True, help="Directory containing package input files and manifests")
    parser.add_argument("--output", required=True, help="Output directory for results and checkpoints")
    parser.add_argument("--extractor", required=True, help="Path to extract_package148_iteration.py")
    parser.add_argument("--memory-gb", type=int, default=16, help="Abaqus memory limit in GB")
    parser.add_argument("--timeout", type=int, default=25200, help="Walltime timeout in seconds")
    parser.add_argument("--max-outer", type=int, default=100, help="Maximum outer staggered iterations")
    parser.add_argument("--damping-omega-d", type=float, default=0.5, help="Picard damage under-relaxation factor (omega_d)")
    parser.add_argument("--abaqus", default="abaqus", help="Abaqus execution command")
    args = parser.parse_args()

    driver = Package171R6C6PDASDriver(
        package=args.package,
        output=args.output,
        extractor=args.extractor,
        memory_gb=args.memory_gb,
        timeout=args.timeout,
        max_outer=args.max_outer,
        damping_omega_d=args.damping_omega_d,
        abaqus=args.abaqus
    )
    driver.solve_coupled_equilibration()


if __name__ == "__main__":
    main()
