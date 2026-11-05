#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
driver_package171_r9_c6_coupled_pdas.py
=======================================
Mode-I Method C Cycle 3: Package 171-R9 Genuine C6 Coupled PDAS Re-Equilibration Driver.
Task: F1610-PACKAGE171-R9-C6-CORRECTIVE-QUALIFICATION
Protocol Version: 2

Implements the R9 Two-Phase Safeguarded Adaptive Under-Relaxation Mechanism with Consistent Residual Rollback:
1. Stage 1 Conservative Damped Picard Relaxation:
   - Uniform under-relaxation parameter omega_d = 0.50.
   - Robust convergence baseline preserving numerical stability in early active-set contraction.

2. Compound Active-Set Transition Criteria:
   - Evaluates node-resolved active-set membership:
     * Active-set cardinality: |A_k| <= 500
     * Symmetric difference: |Delta A_k| <= 10 (where |Delta A_k| = |A_k \\ A_{k-1}| + |A_{k-1} \\ A_k|)
     * Anti-expansion criterion: Delta A^+ = 0 (zero newly activated nodes: |A_k \\ A_{k-1}| == 0)
   - Requires compound condition sustained for 3 consecutive iterations (stabilization_window = 3).
   - Strictly prevents premature Stage 2 acceleration during active-set expansion or boundary churning.

3. Stage 2 Accelerated Damping Transition:
   - Transitions to omega_d = 0.85 ONLY after compound condition is satisfied for 3 consecutive iterations.
   - Recalibrated iteration budget: max_outer = 140 (providing 51 relaxation iterations after outer 89 trigger).

4. Consistent Residual-Based Rollback Safeguards (R9 Correction):
   - In R8, comparing relaxed increments Delta d across stage transition introduced an artificial 70% jump:
     omega_2 / omega_1 = 0.85 / 0.50 = 1.70 > 1.50 (divergence factor).
     This triggered 18 false-positive divergence rollbacks and trapped R8 in Stage 1.
   - R9 evaluates residual growth and divergence on the intrinsic unrelaxed PDAS correction norm:
     delta_d_raw^{(cand)} = ||d_PDAS^{(cand)} - d^{(k)}||_inf
     delta_d_raw^{(prev)} = ||d_PDAS^{(prev)} - d^{(k-1)}||_inf
   - Residual growth safeguard (preserved 5% threshold):
     delta_d_raw^{(cand)} > 1.05 * delta_d_raw^{(prev)}
   - Divergence safeguard (preserved 50% threshold):
     delta_d_raw^{(cand)} > 1.50 * delta_d_raw^{(prev)}
   - Catastrophic cap safeguard (preserved applied step cap):
     delta_d^{(cand)} > 0.05
   - Reverts candidate step to conservative relaxation (omega_d = 0.50) upon genuine unrelaxed step growth or divergence.
   - Restores consistent trial state: conservative damage, stage = 1, switching counters reset to 0.

5. Rigorous Physical Acceptance and Gate Enforcement:
   - Immutable donor lower bounds: d^{(k)} >= d0 (healing violations == 0, tolerance 1e-6).
   - History monotonicity: H^{(k)} >= H0 (0 violations).
   - Strict fail-closed phase decoding: exactly 15,559 receiver nodes, reject 2-component output,
     reject missing/duplicate/unexpected nodes, reject nonfinite values.
   - Post-relaxation signed KKT stationarity <= 1e-6.
   - Final mechanical re-equilibration step with converged damage field.
   - Coupled consistency: delta_u <= 1e-9 mm, delta_H <= 1e-4 MPa.
   - Thermodynamic consistency: H* >= psi+(u*).
   - Reaction force and total energy drift <= 2.0% relative to C5 donor reference.
   - Preserves frozen production UEL SHA-256 CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6.
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


def compute_active_set_symmetric_difference(set_current, set_previous):
    """
    Computes exact node-resolved symmetric difference:
      Delta A = (set_current \\ set_previous) U (set_previous \\ set_current)
      Delta A^+ = set_current \\ set_previous (newly added nodes)
      Delta A^- = set_previous \\ set_current (removed nodes)
    Returns:
      added_nodes: set of nodes added to active set
      removed_nodes: set of nodes removed from active set
      symmetric_difference_count: |Delta A|
    """
    if set_previous is None:
        return set(), set(), 0
    added = set_current - set_previous
    removed = set_previous - set_current
    sym_count = len(added) + len(removed)
    return added, removed, sym_count


class Package171R9C6PDASDriver(object):
    def __init__(
        self,
        package,
        output,
        extractor,
        memory_gb=16,
        timeout=25200,
        max_outer=140,
        omega_d_stage1=0.50,
        omega_d_stage2=0.85,
        max_active_cardinality=500,
        max_symmetric_diff=10,
        max_added_nodes=0,
        stabilization_window=3,
        rollback_factor=1.05,
        divergence_factor=1.50,
        catastrophic_delta_d_cap=0.05,
        abaqus="abaqus"
    ):
        self.package = Path(package).resolve()
        self.output = Path(output).resolve()
        self.extractor = Path(extractor).resolve()
        self.memory_gb = memory_gb
        self.timeout = timeout
        self.max_outer = int(max_outer)
        self.omega_d_stage1 = float(omega_d_stage1)
        self.omega_d_stage2 = float(omega_d_stage2)
        self.max_active_cardinality = int(max_active_cardinality)
        self.max_symmetric_diff = int(max_symmetric_diff)
        self.max_added_nodes = int(max_added_nodes)
        self.stabilization_window = int(stabilization_window)
        self.rollback_factor = float(rollback_factor)
        self.divergence_factor = float(divergence_factor)
        self.catastrophic_delta_d_cap = float(catastrophic_delta_d_cap)
        self.abaqus = abaqus

        self.mesh = None
        self.template = None
        self.target_uy = None
        self.d0 = {}
        self.h0 = {}
        self.u0 = {}
        self.iteration_records = []
        self.deadline = 0

        # Adaptive state tracking
        self.stage = 1
        self.consecutive_stable_iterations = 0
        self.previous_active_set = None
        self.previous_delta_d = None
        self.previous_raw_delta_d = None
        self.rollback_count = 0
        self.divergence_rollback_count = 0
        self.growth_rollback_count = 0
        self.transition_count = 0

    def load(self):
        manifest_p = self.package / "PACKAGE_MANIFEST.json"
        if not manifest_p.is_file():
            raise FileNotFoundError(f"Missing PACKAGE_MANIFEST.json in {self.package}")
        manifest = json.loads(manifest_p.read_text(encoding="utf-8"))

        deck_path = self.package / "M1_C6_PACKAGE171_R9_C3_0_ADAPTIVE_REEQUILIBRATION.inp"
        if not deck_path.is_file():
            deck_path = self.package / "M1_C6_PACKAGE171_R8_C3_0_ADAPTIVE_REEQUILIBRATION.inp"
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
        print(f"Loaded Package 171-R9: 15,252 quads, 15,559 nodes, target_uy = {self.target_uy:.10g} mm")
        print(f"Verified transferred state: d0 in [{min_d0:.6f}, {max_d0:.6f}], H0 in [{min_h0:.4e}, {max_h0:.4e}]")
        print(f"Nonuniform history elements: {nonuniform_count} of {len(self.mesh.elements)}")
        print(f"R9 Adaptive Relaxation: Stage 1 omega_d={self.omega_d_stage1:.2f}, Stage 2 omega_d={self.omega_d_stage2:.2f}")
        print(f"Compound Switching criteria: |A_k| <= {self.max_active_cardinality}, |Delta A_k| <= {self.max_symmetric_diff}, "
              f"Delta A^+ <= {self.max_added_nodes} for {self.stabilization_window} consecutive iterations")
        print(f"Rollback threshold factor: {self.rollback_factor:.2f}, divergence factor: {self.divergence_factor:.2f}, max_outer: {self.max_outer}")

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

    def check_compound_stability(self, pdas_active, delta_active_sym, added_nodes):
        """
        Evaluates the R8 compound active-set stability condition:
          1. Cardinality check: |A_k| <= max_active_cardinality (500)
          2. Symmetric difference check: |Delta A_k| <= max_symmetric_diff (10)
          3. Anti-expansion check: |added_nodes| <= max_added_nodes (0 newly activated nodes)
        Returns:
          is_stable (bool)
        """
        cardinality_ok = (len(pdas_active) <= self.max_active_cardinality)
        sym_diff_ok = (delta_active_sym <= self.max_symmetric_diff)
        anti_expansion_ok = (len(added_nodes) <= self.max_added_nodes)
        return cardinality_ok and sym_diff_ok and anti_expansion_ok

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

        effective_omega_d = self.omega_d_stage2 if self.stage == 2 else self.omega_d_stage1

        summary = {
            "schema": 1,
            "contract": f"Package 171-R9 (C6 Coupled PDAS Re-Equilibration Adaptive omega_d: S1={self.omega_d_stage1:.2f}, S2={self.omega_d_stage2:.2f})",
            "status": "CONVERGED",
            "stage": self.stage,
            "effective_omega_d": effective_omega_d,
            "transition_count": self.transition_count,
            "rollback_count": self.rollback_count,
            "growth_rollback_count": self.growth_rollback_count,
            "divergence_rollback_count": self.divergence_rollback_count,
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
            chkpt_data = {
                "schema": 1,
                "contract": "Package 171-R8 C6 Coupled PDAS Re-Equilibration",
                "stage_mode": self.stage,
                "effective_omega_d": effective_omega_d,
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

        job = f"M1_C6_P171_R9_{role.upper()}_O{outer:02d}"
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
                new_d = {n: v[0] for n, v in fields.items()}
            elif comp_len >= 3:
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

            # Fail-closed checks passed. Apply irreversible clipping against d0 and validate bounds
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

        print(f"\nStarting R9 coupled PDAS re-equilibration (Two-Phase Safeguarded Relaxation S1={self.omega_d_stage1}, S2={self.omega_d_stage2}) on 15,252-quad C6 mesh (target_uy = {target_uy:.10g} mm)...")

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

            # 5. Node-Resolved Active-Set Membership Telemetry
            added_nodes, removed_nodes, delta_active_sym = compute_active_set_symmetric_difference(
                pdas_active, self.previous_active_set
            )
            delta_active_card = (
                abs(len(pdas_active) - len(self.previous_active_set))
                if self.previous_active_set is not None else None
            )

            # R8 Compound Stabilization Tracking:
            # Requires: |A_k| <= max_active_cardinality (500)
            #           |Delta A_k| <= max_symmetric_diff (10)
            #           len(added_nodes) <= max_added_nodes (0)
            if self.previous_active_set is not None:
                is_compound_stable = self.check_compound_stability(pdas_active, delta_active_sym, added_nodes)
                if is_compound_stable:
                    self.consecutive_stable_iterations += 1
                else:
                    self.consecutive_stable_iterations = 0
            else:
                self.consecutive_stable_iterations = 0

            # Switching Evaluation (Stage 1 -> Stage 2)
            attempted_transition = False
            transition_activated = False
            if self.stage == 1 and self.consecutive_stable_iterations >= self.stabilization_window:
                attempted_transition = True
                self.stage = 2
                transition_activated = True
                self.transition_count += 1
                print(f"  [STAGE TRANSITION] Activated Stage 2 acceleration (omega_d={self.omega_d_stage2:.2f}) at outer {outer:02d}: "
                      f"{self.consecutive_stable_iterations} consecutive iterations meeting compound criteria "
                      f"(|A|={len(pdas_active)}<={self.max_active_cardinality}, |Delta A|={delta_active_sym}<={self.max_symmetric_diff}, added={len(added_nodes)}==0)")

            effective_omega_d = self.omega_d_stage2 if self.stage == 2 else self.omega_d_stage1

            # 6. Staggered phase solve with canonical PDAS active set
            new_damage_pdas, _, _ = self.solve_subproblem(
                step_idx, outer, 0, "phase", damage, pdas_active,
                u, history, target_uy
            )

            # 7. Candidate Intrinsic Unrelaxed PDAS Correction & Damped Under-Relaxation Step:
            # Intrinsic unrelaxed PDAS fixed-point step norm: ||d_PDAS - d^(k)||_inf
            cand_raw_delta_d = max(abs(new_damage_pdas[n] - damage[n]) for n in new_damage_pdas)

            # Relaxed update: d^{(cand)} = (1 - omega_d) * d^{(k)} + omega_d * d_PDAS^{(k+1)}
            cand_damage = {}
            for n in new_damage_pdas:
                val = (1.0 - effective_omega_d) * damage[n] + effective_omega_d * new_damage_pdas[n]
                cand_damage[n] = min(1.0, max(self.d0[n], val))
            cand_delta_d = max(abs(cand_damage[n] - damage[n]) for n in cand_damage)

            # 8. Consistent Residual-Based Rollback Safeguards (Stage 2 Only - R9 Correction)
            # Evaluates the invariant unrelaxed solver step norm to eliminate the 1.70x relaxation-scaling trap
            rollback_triggered = False
            rollback_reason = None
            if self.stage == 2 and self.previous_raw_delta_d is not None and self.previous_raw_delta_d > 0:
                is_growth = (cand_raw_delta_d > self.rollback_factor * self.previous_raw_delta_d)
                is_divergence = (cand_raw_delta_d > self.divergence_factor * self.previous_raw_delta_d)
                is_catastrophic = (cand_delta_d > self.catastrophic_delta_d_cap)

                if is_catastrophic:
                    rollback_triggered = True
                    rollback_reason = f"catastrophic jump: cand_delta_d={cand_delta_d:.4e} > cap={self.catastrophic_delta_d_cap}"
                    self.divergence_rollback_count += 1
                elif is_divergence:
                    rollback_triggered = True
                    rollback_reason = f"divergence factor exceeded: cand_raw_delta_d={cand_raw_delta_d:.4e} > {self.divergence_factor:.2f} * prev_raw_delta_d"
                    self.divergence_rollback_count += 1
                elif is_growth:
                    rollback_triggered = True
                    rollback_reason = f"residual growth: cand_raw_delta_d={cand_raw_delta_d:.4e} > {self.rollback_factor:.2f} * prev_raw_delta_d"
                    self.growth_rollback_count += 1

                if rollback_triggered:
                    self.rollback_count += 1
                    print(f"  [ROLLBACK] Outer {outer:02d}: Stage 2 {rollback_reason}. "
                          f"Reverting to conservative step (omega_d={self.omega_d_stage1:.2f}) and resetting Stage 1.")
                    # Revert candidate step using conservative relaxation factor
                    effective_omega_d = self.omega_d_stage1
                    cand_damage = {}
                    for n in new_damage_pdas:
                        val = (1.0 - effective_omega_d) * damage[n] + effective_omega_d * new_damage_pdas[n]
                        cand_damage[n] = min(1.0, max(self.d0[n], val))
                    cand_delta_d = max(abs(cand_damage[n] - damage[n]) for n in cand_damage)
                    cand_raw_delta_d = max(abs(new_damage_pdas[n] - damage[n]) for n in new_damage_pdas)
                    # Reset stage state and switching counters
                    self.stage = 1
                    self.consecutive_stable_iterations = 0

            relaxed_damage = cand_damage
            delta_d = cand_delta_d
            raw_delta_d = cand_raw_delta_d

            # Post-relaxation KKT stationarity evaluation on relaxed_damage
            kkt_post = solver.kkt(relaxed_damage, tau_active=1e-6, tau_free=1e-6)

            # Coupled field increments
            delta_u = max(abs(u[n][i] - previous_u[n][i]) for n in u for i in (0, 1)) if previous_u else None
            delta_h = max(abs(history[k] - previous_h[k]) for k in history) if previous_h else None

            # Capture previous iteration's raw step norm before updating state for next iteration
            prior_raw_delta_d = self.previous_raw_delta_d

            damage = relaxed_damage
            self.previous_delta_d = delta_d
            self.previous_raw_delta_d = raw_delta_d
            self.previous_active_set = set(pdas_active)

            rec = {
                "step": step_idx,
                "outer": outer,
                "target_uy": target_uy,
                "stage": self.stage,
                "effective_omega_d": effective_omega_d,
                "pdas_active_count": len(pdas_active),
                "pdas_free_count": len(pdas_free),
                "active_set_symmetric_diff": delta_active_sym,
                "active_set_cardinality_diff": delta_active_card,
                "added_nodes_count": len(added_nodes),
                "removed_nodes_count": len(removed_nodes),
                "consecutive_stable_iterations": self.consecutive_stable_iterations,
                "attempted_transition": attempted_transition,
                "transition_activated": transition_activated,
                "rollback_triggered": rollback_triggered,
                "rollback_reason": rollback_reason,
                "delta_d": delta_d,
                "raw_delta_d": raw_delta_d,
                "cand_raw_delta_d": cand_raw_delta_d,
                "prev_raw_delta_d": prior_raw_delta_d,
                "delta_u": delta_u,
                "delta_h": delta_h,
                "free_error": kkt_post["free_error"],
                "dual_error": kkt_post["dual_error"],
                "complementarity": kkt_post["complementarity"],
                "kkt_post_passed": kkt_post["passed"],
                "kkt_active_count": len(kkt_post["active"]),
                "kkt_free_count": len(kkt_post["free"])
            }
            step_records.append(rec)
            self.iteration_records.append(rec)
            try:
                (self.output / "live_iteration_telemetry.json").write_text(json.dumps(self.iteration_records, indent=2))
            except Exception:
                pass

            sym_str = f"{delta_active_sym}" if delta_active_sym is not None else "N/A"
            card_str = f"{delta_active_card}" if delta_active_card is not None else "N/A"
            added_str = f"{len(added_nodes)}" if added_nodes is not None else "N/A"
            print(f"  Outer {outer:02d} [Stage {self.stage}, w={effective_omega_d:.2f}]: delta_d={delta_d:.4e}, "
                  f"delta_u={delta_u or 0.0:.4e}, delta_h={delta_h or 0.0:.4e}, "
                  f"|Delta A|={sym_str} (card={card_str}, added={added_str}), stable_count={self.consecutive_stable_iterations}, "
                  f"post_kkt_pass={kkt_post['passed']}, PDAS active={len(pdas_active)}")

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
                        f"Package 171-R8 coupled convergence achieved at outer {outer}, but physical acceptance failed: "
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
                "contract": f"Package 171-R9 (C6 Coupled PDAS Re-Equilibration Adaptive omega_d: S1={self.omega_d_stage1:.2f}, S2={self.omega_d_stage2:.2f})",
                "status": "NONCONVERGED",
                "stage": self.stage,
                "outer_iterations_completed": self.max_outer,
                "target_uy_mm": target_uy,
                "last_delta_d": delta_d,
                "last_delta_u": delta_u,
                "last_delta_h": delta_h,
                "transition_count": self.transition_count,
                "rollback_count": self.rollback_count,
                "growth_rollback_count": self.growth_rollback_count,
                "divergence_rollback_count": self.divergence_rollback_count,
                "last_kkt_free_error": kkt_post["free_error"],
                "last_kkt_dual_error": kkt_post["dual_error"]
            }
            summary_path = self.output / "re_equilibration_summary.json"
            summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
            raise RuntimeError(f"Package 171-R9 C6 coupled re-equilibration failed to converge within {self.max_outer} iterations")

        return summary


def main():
    parser = argparse.ArgumentParser(description="Package 171-R9 C6 Coupled PDAS Re-Equilibration Driver")
    parser.add_argument("--package", required=True, help="Directory containing package input files and manifests")
    parser.add_argument("--output", required=True, help="Output directory for results and checkpoints")
    parser.add_argument("--extractor", required=True, help="Path to extract_package148_iteration.py")
    parser.add_argument("--memory-gb", type=int, default=16, help="Abaqus memory limit in GB")
    parser.add_argument("--timeout", type=int, default=25200, help="Walltime timeout in seconds")
    parser.add_argument("--max-outer", type=int, default=140, help="Maximum outer staggered iterations")
    parser.add_argument("--omega-d-stage1", type=float, default=0.50, help="Stage 1 conservative relaxation factor")
    parser.add_argument("--omega-d-stage2", type=float, default=0.85, help="Stage 2 accelerated relaxation factor")
    parser.add_argument("--max-active-cardinality", type=int, default=500, help="Max active set cardinality for Stage 2")
    parser.add_argument("--max-symmetric-diff", type=int, default=10, help="Max symmetric difference nodes for Stage 2")
    parser.add_argument("--max-added-nodes", type=int, default=0, help="Max newly added nodes for Stage 2")
    parser.add_argument("--stabilization-window", type=int, default=3, help="Consecutive iterations required for Stage 2")
    parser.add_argument("--rollback-factor", type=float, default=1.05, help="Residual growth threshold factor for rollback")
    parser.add_argument("--divergence-factor", type=float, default=1.50, help="Divergence factor threshold for rollback")
    parser.add_argument("--catastrophic-cap", type=float, default=0.05, help="Catastrophic delta_d cap for rollback")
    parser.add_argument("--abaqus", default="abaqus", help="Abaqus execution command")
    args = parser.parse_args()

    driver = Package171R9C6PDASDriver(
        package=args.package,
        output=args.output,
        extractor=args.extractor,
        memory_gb=args.memory_gb,
        timeout=args.timeout,
        max_outer=args.max_outer,
        omega_d_stage1=args.omega_d_stage1,
        omega_d_stage2=args.omega_d_stage2,
        max_active_cardinality=args.max_active_cardinality,
        max_symmetric_diff=args.max_symmetric_diff,
        max_added_nodes=args.max_added_nodes,
        stabilization_window=args.stabilization_window,
        rollback_factor=args.rollback_factor,
        divergence_factor=args.divergence_factor,
        catastrophic_delta_d_cap=args.catastrophic_cap,
        abaqus=args.abaqus
    )
    driver.solve_coupled_equilibration()


if __name__ == "__main__":
    main()
