#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
driver_same_mesh_control_pdas.py
================================
Mode-I Method C Paired Same-Mesh Control PDAS Re-Equilibration Driver.
Task: F1622-METHOD-C-SAME-MESH-ABAQUS-CONTROL-STAGING
Protocol Version: 2

Solves the coupled staggered PDAS re-equilibration on the C5 mesh
(12,996 CPE4 quads, 13,278 physical nodes + RP 999999, 51,984 integration points)
at constant holding displacement (uy = 0.0018703125442191958 mm) following state transfer.

Used for the paired same-mesh control experiment:
- Arm 1 (Package 172): Control Old (Element-Averaged GP History, ~6.35 MPa perturbation)
- Arm 2 (Package 173): Control Corrected (Hardened Isoparametric GP History, < 1e-12 MPa error)

Governing Solver Settings (Identical across both arms):
1. Stage 1 Conservative Damped Picard Relaxation:
   - Phase under-relaxation factor omega_d = 0.50.
   - Mechanical displacement unrelaxed (omega_u = 1.00) during initial active-set contraction.
2. Compound Active-Set Transition Criteria:
   - Active-set cardinality: |A_k| <= 500
   - Symmetric difference: |Delta A_k| <= 10
   - Anti-expansion criterion: Delta A^+ = 0 (zero newly activated nodes)
   - Compound condition sustained for stabilization_window = 3 consecutive iterations.
3. Stage 2 Isolated Mechanical Displacement Under-Relaxation:
   - Phase relaxation accelerates to omega_d = 0.85.
   - Mechanical displacement under-relaxed with omega_u = 0.85:
       u_trial^{(k)} = (1 - omega_u) * u_trial^{(k-1)} + omega_u * u_Abaqus^{(k)}
   - Rejects false smoothing convergence: requires BOTH Delta u_relaxed <= 1e-9 mm AND Delta u_raw <= 1e-9 mm.
4. Anderson Acceleration: STRICTLY DISABLED (anderson_enabled = False) to isolate history transfer effect.
5. Consistent Residual-Based Rollback Safeguards with Atomic State Retention:
   - Evaluates intrinsic unrelaxed PDAS correction step norm ||d_PDAS - d^(k)||_inf.
   - Residual growth safeguard (1.05) and divergence safeguard (1.50).
   - Catastrophic step cap (0.05).
6. Rigorous Physical Acceptance & Coupled Consistency Verification:
   - Independent final mechanical solve with converged damage d* and history H*: K(d*) u_consistent = f_ext.
   - Coupled field displacement consistency: ||u_consistent - u_trial*||_inf <= 1e-9 mm.
   - Coupled field history consistency: ||H(u_consistent) - H*||_inf <= 1e-4 MPa.
   - Post-relaxation signed KKT stationarity <= 1e-6.
   - Pointwise damage irreversibility: d* >= d0 (0 healing violations, tol 1e-6).
   - Pointwise history monotonicity: H* >= H0 (0 monotonicity violations).
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

# Reference values from accepted C5 Checkpoint 03 (Job 1419566.mmaster02)
DONOR_REFERENCE_FORCE_KN = 0.17992419004440308
DONOR_REFERENCE_TOTAL_ENERGY_KNMM = 0.00022639903
DONOR_REFERENCE_ELASTIC_ENERGY_KNMM = 0.00016825724
DONOR_REFERENCE_FRACTURE_ENERGY_KNMM = 5.814179e-05

# Contextual Comparator B (Job 1419543)
REFERENCE_B_FORCE_KN = 0.18302963
REFERENCE_B_TOTAL_ENERGY_KNMM = 0.00022603386


def compute_active_set_symmetric_difference(set_current, set_previous):
    """
    Computes exact node-resolved symmetric difference:
      Delta A = (set_current \\ set_previous) U (set_previous \\ set_current)
      Delta A^+ = set_current \\ set_previous (newly added nodes)
      Delta A^- = set_previous \\ set_current (removed nodes)
    """
    if set_previous is None:
        return set(), set(), 0
    added = set_current - set_previous
    removed = set_previous - set_current
    sym_count = len(added) + len(removed)
    return added, removed, sym_count


class SameMeshControlPDASDriver(object):
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
        omega_u_stage1=1.00,
        omega_u_stage2=0.85,
        max_active_cardinality=500,
        max_symmetric_diff=10,
        max_added_nodes=0,
        stabilization_window=3,
        rollback_factor=1.05,
        divergence_factor=1.50,
        catastrophic_delta_d_cap=0.05,
        master_deck_name=None,
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
        self.omega_u_stage1 = float(omega_u_stage1)
        self.omega_u_stage2 = float(omega_u_stage2)
        self.max_active_cardinality = int(max_active_cardinality)
        self.max_symmetric_diff = int(max_symmetric_diff)
        self.max_added_nodes = int(max_added_nodes)
        self.stabilization_window = int(stabilization_window)
        self.rollback_factor = float(rollback_factor)
        self.divergence_factor = float(divergence_factor)
        self.catastrophic_delta_d_cap = float(catastrophic_delta_d_cap)
        self.master_deck_name = master_deck_name
        self.deck_path = None
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
        self.previous_u_trial = None
        self.previous_u_abaqus = None
        self.rollback_count = 0
        self.divergence_rollback_count = 0
        self.growth_rollback_count = 0
        self.transition_count = 0

    def load(self):
        manifest_p = self.package / "PACKAGE_MANIFEST.json"
        if not manifest_p.is_file():
            raise FileNotFoundError(f"Missing PACKAGE_MANIFEST.json in {self.package}")
        manifest = json.loads(manifest_p.read_text(encoding="utf-8"))

        if self.master_deck_name is not None:
            deck_path = self.package / self.master_deck_name
            if not deck_path.is_file():
                raise FileNotFoundError(
                    f"Explicit master input deck '{self.master_deck_name}' not found in {self.package}"
                )
        else:
            # Deterministic selection: exclude datacheck decks (*_DC.inp) and generated per-iteration decks (*_ITER*.inp)
            candidates = [
                p for p in self.package.glob("*.inp")
                if not p.name.endswith("_DC.inp")
                and "_ITER" not in p.name.upper()
                and ("_REEQUILIBRATION" in p.name.upper() or "_RESTART" in p.name.upper() or "_MASTER" in p.name.upper())
            ]
            if len(candidates) == 1:
                deck_path = candidates[0]
            elif len(candidates) == 0:
                raise FileNotFoundError(
                    f"Deterministic master deck selection failed in {self.package}: "
                    f"no *_REEQUILIBRATION.inp or *_RESTART.inp found (all .inp: {[p.name for p in self.package.glob('*.inp')]})"
                )
            else:
                raise ValueError(
                    f"Ambiguous master input deck in {self.package}: "
                    f"multiple candidates found: {[p.name for p in candidates]}"
                )

        self.deck_path = deck_path
        self.template = deck_path.read_text(encoding="utf-8")
        self.mesh = Mesh2D.from_inp(deck_path, name="C5_Receiver", max_physical_node=13278)

        if len(self.mesh.elements) != 12996:
            raise ValueError(f"Expected 12,996 C5 elements, found {len(self.mesh.elements)}")
        if len(self.mesh.nodes) != 13278:
            raise ValueError(f"Expected 13,278 C5 nodes, found {len(self.mesh.nodes)}")

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

        if len(self.h0) != 51984:
            raise ValueError(f"Expected 51,984 Gauss-point histories (12,996 * 4), found {len(self.h0)}")

        # Validate transferred state bounds
        min_d0 = min(self.d0.values())
        max_d0 = max(self.d0.values())
        min_h0 = min(self.h0.values())
        max_h0 = max(self.h0.values())
        if min_d0 < 0 or max_d0 < 0.5:
            raise ValueError(f"Transferred d0 lacks authentic bounds: min={min_d0}, max={max_d0}")
        if min_h0 < 0:
            raise ValueError(f"Transferred h0 lacks authentic nonnegative bounds: min={min_h0}")

        nonuniform_count = sum(
            1 for eid in self.mesh.elements
            if len({self.h0[(eid, g)] for g in range(1, 5)}) > 1
        )

        target_source = manifest.get("donor_source", {})
        self.target_uy = float(target_source.get("target_uy_mm", 0.0018703125442191958))
        pkg_id = manifest.get("package_id", self.package.name)
        label = manifest.get("label", "Same-Mesh Control")
        print(f"Loaded {pkg_id} ({label}): 12,996 quads, 13,278 nodes, target_uy = {self.target_uy:.10g} mm")
        print(f"Transferred state: d0 in [{min_d0:.6f}, {max_d0:.6f}], H0 in [{min_h0:.4e}, {max_h0:.4e}]")
        print(f"Nonuniform history elements: {nonuniform_count} of {len(self.mesh.elements)}")
        print(f"Phase Relaxation: Stage 1 omega_d={self.omega_d_stage1:.2f}, Stage 2 omega_d={self.omega_d_stage2:.2f}")
        print(f"Displacement Relaxation: Stage 1 omega_u={self.omega_u_stage1:.2f}, Stage 2 omega_u={self.omega_u_stage2:.2f}")
        print(f"Compound Switching criteria: |A_k| <= {self.max_active_cardinality}, |Delta A_k| <= {self.max_symmetric_diff}, "
              f"Delta A^+ <= {self.max_added_nodes} for {self.stabilization_window} consecutive iterations")
        print(f"Rollback threshold factor: {self.rollback_factor:.2f}, divergence factor: {self.divergence_factor:.2f}, max_outer: {self.max_outer}")
        print("Anderson Acceleration: DISABLED (anderson_enabled = False)")

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
            f"*Step, name=C5_Control_Step{step_idx}_{role}, nlgeom=NO, inc=1\n",
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
            "*Node Print, frequency=1\nU\n",
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
        step_name = f"C5_Control_Step{step_idx}_{role}"
        ext_cmd = [
            self.abaqus, "python", str(self.extractor),
            "--odb", str(odb_path),
            "--output", str(endpoint_path),
            "--physical-nodes", "13278",
            "--physical-elements", "12996",
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
        if len(pdas_active) > self.max_active_cardinality:
            return False
        if delta_active_sym is not None and delta_active_sym > self.max_symmetric_diff:
            return False
        if added_nodes is not None and len(added_nodes) > self.max_added_nodes:
            return False
        return True

    def solve_subproblem(self, step_idx, outer, sub_idx, role, damage, active, displacement, history, target_u):
        subdir = self.output / f"outer_{outer:02d}_{role}"
        subdir.mkdir(parents=True, exist_ok=True)
        job = f"c5_ctrl_o{outer:02d}_{role[:4]}"
        deck_text = self._deck(step_idx, role, damage, active, displacement, history, target_u)
        inp_path = subdir / f"{job}.inp"
        inp_path.write_text(deck_text, encoding="utf-8")

        shutil.copy2(self.package / "f42_mixed_uel.for", subdir / "f42_mixed_uel.for")
        res = self.runner(subdir, job, role, step_idx)

        new_d = dict(damage)
        new_u = dict(displacement) if displacement else {}

        # 1. Primary extractor format from extract_package148_iteration.py: "nodes": [[nid, u1, u2, d], ...]
        if "nodes" in res and isinstance(res["nodes"], list):
            rows = res["nodes"]
            extracted_nodes = set(int(r[0]) for r in rows)
            expected_nodes = set(self.mesh.nodes.keys())
            if extracted_nodes != expected_nodes:
                missing = expected_nodes - extracted_nodes
                unexpected = extracted_nodes - expected_nodes
                raise ValueError(
                    f"solve_subproblem({role}): expected exactly {len(expected_nodes)} nodes matching mesh, "
                    f"got {len(extracted_nodes)} (missing={len(missing)}, unexpected={len(unexpected)})"
                )

            fields = {}
            for r in rows:
                nid = int(r[0])
                vals = tuple(float(x) for x in r[1:])
                for val in vals:
                    if math.isnan(val) or math.isinf(val):
                        raise ValueError(f"solve_subproblem({role}): nonfinite value {val} at node {nid}")
                fields[nid] = vals

            if role == "mechanical":
                if any(len(v) < 2 for v in fields.values()):
                    raise ValueError(f"solve_subproblem(mechanical): incomplete displacement output; all nodes must have >= 2 components")
                new_u = {n: v[:2] for n, v in fields.items()}
            elif role == "phase":
                comp_lengths = set(len(v) for v in fields.values())
                comp_len = next(iter(comp_lengths))
                if comp_len == 1:
                    raw_d = {n: v[0] for n, v in fields.items()}
                elif comp_len >= 3:
                    raw_d = {n: v[2] for n, v in fields.items()}
                elif comp_len == 2:
                    raise ValueError(
                        f"solve_subproblem(phase): rejected two-component phase output (U1, U2); "
                        f"cannot interpret mechanical displacement as phase damage U3"
                    )
                else:
                    raise ValueError(f"solve_subproblem(phase): unsupported phase component count {comp_len}")

                # Validate raw phase field bounds and finiteness
                for n, val in raw_d.items():
                    if not math.isfinite(val):
                        raise ValueError(f"solve_subproblem(phase): non-finite raw damage at node {n}: {val}")
                    if val < -0.05 or val > 1.05:
                        raise ValueError(
                            f"solve_subproblem(phase): unphysical raw damage out of bounds at node {n}: {val:.6e} "
                            f"(valid physical range [-0.05, 1.05])"
                        )

                # Record raw healing diagnostics BEFORE projection
                raw_healing_min = min(raw_d[n] - self.d0[n] for n in raw_d)
                raw_healing_violations = sum(1 for n in raw_d if raw_d[n] < (self.d0[n] - HEALING_TOL))
                res["raw_damage"] = dict(raw_d)
                res["raw_healing_min"] = raw_healing_min
                res["raw_healing_violations"] = raw_healing_violations

                # Enforce documented damage irreversibility projection against d0
                new_d = {n: min(1.0, max(self.d0[n], raw_d[n])) for n in raw_d}
                validate_damage(new_d, self.d0)
        # 2. Legacy fallback format: "nodal_displacement" and "nodal_damage" dicts
        elif role == "mechanical" and "nodal_displacement" in res:
            for n_str, (u1, u2) in res.get("nodal_displacement", {}).items():
                nid = int(n_str)
                if nid in self.mesh.nodes:
                    new_u[nid] = (u1, u2)
        elif role == "phase" and "nodal_damage" in res:
            raw_d = {}
            for n_str, d_val in res.get("nodal_damage", {}).items():
                nid = int(n_str)
                if nid in self.mesh.nodes:
                    raw_d[nid] = float(d_val)
            for n, val in raw_d.items():
                if not math.isfinite(val):
                    raise ValueError(f"solve_subproblem(phase): non-finite raw damage at node {n}: {val}")
                if val < -0.05 or val > 1.05:
                    raise ValueError(f"solve_subproblem(phase): unphysical raw damage out of bounds at node {n}: {val:.6e}")
            raw_healing_min = min(raw_d[n] - self.d0[n] for n in raw_d)
            raw_healing_violations = sum(1 for n in raw_d if raw_d[n] < (self.d0[n] - HEALING_TOL))
            res["raw_damage"] = dict(raw_d)
            res["raw_healing_min"] = raw_healing_min
            res["raw_healing_violations"] = raw_healing_violations
            new_d = {n: min(1.0, max(self.d0[n], raw_d[n])) for n in raw_d}
            validate_damage(new_d, self.d0)
        else:
            raise KeyError(
                f"solve_subproblem({role}): unrecognised extractor output format; "
                f"expected 'nodes' list or 'nodal_{role}' dict in keys: {list(res.keys())}"
            )

        return new_d, new_u, res

    def finalize_coupled_acceptance(
        self,
        u_trial,
        u_abaqus,
        history_trial,
        damage_relaxed,
        consistent_u,
        consistent_endpoint,
        solver,
        step_idx,
        outer,
        target_uy,
        delta_d,
        delta_u_relaxed,
        delta_u_raw,
        delta_h,
        pdas_active_count,
        pdas_free_count
    ):
        print("\nEvaluating comprehensive physical acceptance criteria:")

        # 1. Authentic extractor field names from extract_package148_iteration.py
        raw_rf = (
            consistent_endpoint.get("rf2_kN")
            if "rf2_kN" in consistent_endpoint
            else consistent_endpoint.get("reaction_force_kn")
        )
        if raw_rf is None and "reaction_force_kN" in consistent_endpoint:
            raw_rf = consistent_endpoint["reaction_force_kN"]

        raw_energy = (
            consistent_endpoint.get("total_energy_kNmm")
            if "total_energy_kNmm" in consistent_endpoint
            else consistent_endpoint.get("total_energy_knmm")
        )

        raw_elastic = (
            consistent_endpoint.get("elastic_kNmm")
            if "elastic_kNmm" in consistent_endpoint
            else consistent_endpoint.get("strain_energy_knmm")
        )

        raw_fracture = (
            consistent_endpoint.get("fracture_kNmm")
            if "fracture_kNmm" in consistent_endpoint
            else consistent_endpoint.get("fracture_energy_knmm")
        )

        # Fail-closed validation: reject missing or nonfinite force/energy rather than defaulting to 0.0
        if raw_rf is None:
            raise KeyError(
                f"finalize_coupled_acceptance: missing reaction force in consistent_endpoint; "
                f"expected 'rf2_kN' (found: {list(consistent_endpoint.keys())})"
            )
        rf_val = float(raw_rf)
        if not math.isfinite(rf_val):
            raise ValueError(f"finalize_coupled_acceptance: non-finite reaction force: {rf_val}")

        if raw_energy is None:
            raise KeyError(
                f"finalize_coupled_acceptance: missing total energy in consistent_endpoint; "
                f"expected 'total_energy_kNmm' (found: {list(consistent_endpoint.keys())})"
            )
        energy_val = float(raw_energy)
        if not math.isfinite(energy_val):
            raise ValueError(f"finalize_coupled_acceptance: non-finite total energy: {energy_val}")

        rf_consistent = abs(rf_val)
        energy_consistent = energy_val
        elastic_consistent = float(raw_elastic) if (raw_elastic is not None and math.isfinite(float(raw_elastic))) else 0.0
        fracture_consistent = float(raw_fracture) if (raw_fracture is not None and math.isfinite(float(raw_fracture))) else 0.0

        force_drift_pct = abs(rf_consistent - DONOR_REFERENCE_FORCE_KN) / DONOR_REFERENCE_FORCE_KN * 100.0
        energy_drift_pct = abs(energy_consistent - DONOR_REFERENCE_TOTAL_ENERGY_KNMM) / DONOR_REFERENCE_TOTAL_ENERGY_KNMM * 100.0

        disp_consistency_inf = max(
            abs(consistent_u[n][i] - u_trial[n][i]) for n in consistent_u for i in (0, 1)
        )
        disp_consistency_pass = (disp_consistency_inf <= 1.0e-9)

        zero_baseline = {(e, g): 0.0 for e in self.mesh.elements for g in range(1, 5)}
        psi_consistent = driving_history(self.mesh, consistent_u, zero_baseline)
        h_consistent = {k: max(self.h0[k], psi_consistent[k]) for k in self.h0}
        h_consistency_inf = max(abs(h_consistent[k] - history_trial[k]) for k in self.h0)
        h_consistency_pass = (h_consistency_inf <= 1.0e-4)

        healing_violations = sum(1 for n in damage_relaxed if damage_relaxed[n] < (self.d0[n] - HEALING_TOL))
        bounds_violations = sum(1 for n in damage_relaxed if (damage_relaxed[n] < 0.0 or damage_relaxed[n] > 1.0 + 1e-6))
        monotonicity_violations = sum(1 for k in history_trial if history_trial[k] < (self.h0[k] - 1e-6))
        thermodynamic_violations = sum(1 for k in history_trial if history_trial[k] < (psi_consistent[k] - 1e-6))

        solver.h_gp = history_trial
        kkt_final = solver.kkt(damage_relaxed, tau_active=1e-6, tau_free=1e-6)

        force_gate_pass = (force_drift_pct <= 2.0)
        energy_gate_pass = (energy_drift_pct <= 2.0)
        healing_pass = (healing_violations == 0)
        bounds_pass = (bounds_violations == 0)
        monotonicity_pass = (monotonicity_violations == 0)
        thermo_pass = (thermodynamic_violations == 0)
        kkt_pass = kkt_final["passed"]

        all_physical_pass = (
            force_gate_pass and energy_gate_pass and healing_pass and
            bounds_pass and monotonicity_pass and thermo_pass and
            kkt_pass and disp_consistency_pass and h_consistency_pass
        )

        print(f"  Reaction Force: consistent = {rf_consistent:.6f} kN, ref = {DONOR_REFERENCE_FORCE_KN:.6f} kN, drift = {force_drift_pct:.3f}% ({'PASS' if force_gate_pass else 'FAIL'})")
        print(f"  Total Energy: consistent = {energy_consistent:.6e} kNmm, ref = {DONOR_REFERENCE_TOTAL_ENERGY_KNMM:.6e} kNmm, drift = {energy_drift_pct:.3f}% ({'PASS' if energy_gate_pass else 'FAIL'})")
        print(f"  Coupled Consistency u: ||u_consistent - u_trial||_inf = {disp_consistency_inf:.4e} mm ({'PASS' if disp_consistency_pass else 'FAIL'})")
        print(f"  Coupled Consistency H: ||H_consistent - H_trial||_inf = {h_consistency_inf:.4e} MPa ({'PASS' if h_consistency_pass else 'FAIL'})")
        print(f"  Damage Healing: {healing_violations} violations ({'PASS' if healing_pass else 'FAIL'})")
        print(f"  History Monotonicity: {monotonicity_violations} violations ({'PASS' if monotonicity_pass else 'FAIL'})")
        print(f"  Thermodynamic H >= psi+: {thermodynamic_violations} violations ({'PASS' if thermo_pass else 'FAIL'})")
        print(f"  Signed KKT Post: free={kkt_final['free_error']:.4e}, dual={kkt_final['dual_error']:.4e}, comp={kkt_final['complementarity']:.4e} ({'PASS' if kkt_pass else 'FAIL'})")
        print(f"  Overall Physical Acceptance: {'ACCEPTED' if all_physical_pass else 'REJECTED'}")

        manifest_p = self.package / "PACKAGE_MANIFEST.json"
        manifest = json.loads(manifest_p.read_text(encoding="utf-8")) if manifest_p.is_file() else {}
        pkg_id = manifest.get("package_id", self.package.name)

        summary = {
            "schema": 1,
            "task_id": manifest.get("task_id", "F1626-METHOD-C-SAME-MESH-REPAIRED-CONTROL-EXECUTION"),
            "package_id": pkg_id,
            "label": manifest.get("label", "Same-Mesh Control"),
            "status": "CONVERGED" if all_physical_pass else "CONVERGED_PHYSICAL_ACCEPTANCE_FAILED",
            "physical_acceptance": "ACCEPTED" if all_physical_pass else "FAILED",
            "step_index": step_idx,
            "outer_iterations_completed": outer,
            "target_uy_mm": target_uy,
            "stage_at_convergence": self.stage,
            "applied_omega_d": self.omega_d_stage2 if self.stage == 2 else self.omega_d_stage1,
            "applied_omega_u": self.omega_u_stage2 if self.stage == 2 else self.omega_u_stage1,
            "anderson_enabled": False,
            "total_transitions": self.transition_count,
            "total_rollbacks": self.rollback_count,
            "divergence_rollbacks": self.divergence_rollback_count,
            "growth_rollbacks": self.growth_rollback_count,
            "final_pdas_active_nodes": pdas_active_count,
            "final_pdas_free_nodes": pdas_free_count,
            "last_delta_d": delta_d,
            "last_delta_u_relaxed": delta_u_relaxed,
            "last_delta_u_raw": delta_u_raw,
            "last_delta_h": delta_h,
            "reaction_force_kN": rf_consistent,
            "rf2_kN": rf_consistent,
            "donor_reference_force_kN": DONOR_REFERENCE_FORCE_KN,
            "force_drift_pct": force_drift_pct,
            "force_gate_pass": force_gate_pass,
            "total_energy_kNmm": energy_consistent,
            "elastic_energy_kNmm": elastic_consistent,
            "fracture_energy_kNmm": fracture_consistent,
            "donor_reference_total_energy_kNmm": DONOR_REFERENCE_TOTAL_ENERGY_KNMM,
            "energy_drift_pct": energy_drift_pct,
            "energy_gate_pass": energy_gate_pass,
            "coupled_field_consistency_u_inf_mm": disp_consistency_inf,
            "coupled_field_consistency_u_pass": disp_consistency_pass,
            "coupled_field_consistency_h_inf_MPa": h_consistency_inf,
            "coupled_field_consistency_h_pass": h_consistency_pass,
            "healing_violations": healing_violations,
            "healing_pass": healing_pass,
            "monotonicity_violations": monotonicity_violations,
            "history_monotonicity": monotonicity_pass,
            "thermodynamic_violations": thermodynamic_violations,
            "thermodynamic_consistency": thermo_pass,
            "kkt_free_error": kkt_final["free_error"],
            "kkt_dual_error": kkt_final["dual_error"],
            "kkt_complementarity": kkt_final["complementarity"],
            "kkt_final_pass": kkt_pass,
            "all_gates_pass": all_physical_pass,
            "iteration_history": self.iteration_records
        }

        with (self.output / "same_mesh_control_equilibration_summary.json").open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        if all_physical_pass:
            ckpt_path = self.output / "converged_same_mesh_control_checkpoint.json"
            ckpt_data = {
                "schema": 1,
                "package_id": pkg_id,
                "step_index": step_idx,
                "outer_iteration": outer,
                "target_uy_mm": target_uy,
                "reaction_force_kN": rf_consistent,
                "total_energy_kNmm": energy_consistent,
                "elastic_energy_kNmm": elastic_consistent,
                "fracture_energy_kNmm": fracture_consistent,
                "displacement": {str(n): list(u_trial[n]) for n in sorted(u_trial)},
                "damage": {str(n): damage_relaxed[n] for n in sorted(damage_relaxed)},
                "history": [[e, g, history_trial[e, g]] for e, g in sorted(history_trial)]
            }
            with ckpt_path.open("w", encoding="utf-8") as f:
                json.dump(ckpt_data, f, indent=2)
            print(f"\nCreated validated checkpoint: {ckpt_path.name}")

        return summary, all_physical_pass

    def solve_coupled_equilibration(self):
        self.load()
        self.output.mkdir(parents=True, exist_ok=True)
        self.deadline = time.time() + self.timeout

        step_idx = 1
        outer = 0
        damage = dict(self.d0)
        history = dict(self.h0)
        target_uy = self.target_uy

        solver = PDASReEquilibrationSolver(self.mesh, damage, history)

        previous_u_trial = None
        previous_u_abaqus = None
        step_converged = False

        print(f"\nBeginning coupled staggered PDAS re-equilibration (max_outer = {self.max_outer})...")

        step_records = []
        for outer in range(1, self.max_outer + 1):
            if time.time() > self.deadline:
                print(f"Execution timeout reached after {self.timeout} seconds.")
                break

            prior_raw_delta_d = self.previous_raw_delta_d

            # 1. Staggered mechanical solve with trial damage
            _, u_abaqus, _ = self.solve_subproblem(
                step_idx, outer, 0, "mechanical", damage, set(damage),
                None, history, target_uy
            )

            # 2. Stage-dependent displacement update
            if self.stage == 2 and previous_u_trial is not None:
                applied_omega_u = self.omega_u_stage2
                u_trial = {}
                for n in u_abaqus:
                    u_trial[n] = (
                        (1.0 - applied_omega_u) * previous_u_trial[n][0] + applied_omega_u * u_abaqus[n][0],
                        (1.0 - applied_omega_u) * previous_u_trial[n][1] + applied_omega_u * u_abaqus[n][1]
                    )
            else:
                applied_omega_u = self.omega_u_stage1
                u_trial = dict(u_abaqus)

            delta_u_raw = None
            delta_u_relaxed = None
            if previous_u_trial is not None:
                delta_u_raw = max(abs(u_abaqus[n][i] - previous_u_trial[n][i]) for n in u_abaqus for i in (0, 1))
                delta_u_relaxed = max(abs(u_trial[n][i] - previous_u_trial[n][i]) for n in u_trial for i in (0, 1))

            # 3. Qualified History Construction
            zero_baseline = {(e, g): 0.0 for e in self.mesh.elements for g in range(1, 5)}
            psi_k = driving_history(self.mesh, u_trial, zero_baseline)
            history = {k: max(self.h0[k], psi_k[k]) for k in self.h0}
            solver.h_gp = history

            # 4. Pre-update KKT residuals for PDAS active-set partitioning
            kkt_pre = solver.kkt(damage, tau_active=1e-6, tau_free=1e-6)

            # 5. Canonical Hintermüller-Ito-Kunisch active-set update
            c_pdas = 1.0e3    # (kN*mm)^-1
            eps_pdas = 1.0e-6 # dimensionless
            pdas_active = {
                n for n in damage
                if (damage[n] - c_pdas * kkt_pre["residual"][n]) <= (self.d0[n] + eps_pdas)
            }
            pdas_free = set(damage) - pdas_active

            # 6. Active-Set Membership Telemetry
            added_nodes, removed_nodes, delta_active_sym = compute_active_set_symmetric_difference(
                pdas_active, self.previous_active_set
            )
            delta_active_card = (
                abs(len(pdas_active) - len(self.previous_active_set))
                if self.previous_active_set is not None else None
            )

            # Compound Stabilization Tracking
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
                print(f"  [STAGE TRANSITION] Activated Stage 2 acceleration (omega_d={self.omega_d_stage2:.2f}, omega_u={self.omega_u_stage2:.2f}) at outer {outer:02d}: "
                      f"{self.consecutive_stable_iterations} consecutive iterations meeting compound criteria "
                      f"(|A|={len(pdas_active)}<={self.max_active_cardinality}, |Delta A|={delta_active_sym}<={self.max_symmetric_diff}, added={len(added_nodes)}==0)")

            applied_omega_d = self.omega_d_stage2 if self.stage == 2 else self.omega_d_stage1

            # 7. Staggered phase solve
            new_damage_pdas, _, _ = self.solve_subproblem(
                step_idx, outer, 0, "phase", damage, pdas_active,
                u_trial, history, target_uy
            )

            # 8. Candidate Intrinsic Unrelaxed PDAS Correction & Under-Relaxation Step
            cand_raw_delta_d = max(abs(new_damage_pdas[n] - damage[n]) for n in new_damage_pdas)
            cand_damage = {}
            for n in new_damage_pdas:
                val = (1.0 - applied_omega_d) * damage[n] + applied_omega_d * new_damage_pdas[n]
                cand_damage[n] = min(1.0, max(self.d0[n], val))
            cand_delta_d = max(abs(cand_damage[n] - damage[n]) for n in cand_damage)

            # 9. Consistent Residual-Based Rollback Safeguards (Stage 2 Only)
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
                    rollback_reason = f"unrelaxed divergence: cand_raw_delta_d={cand_raw_delta_d:.4e} > {self.divergence_factor} * prev={self.previous_raw_delta_d:.4e}"
                    self.divergence_rollback_count += 1
                elif is_growth:
                    rollback_triggered = True
                    rollback_reason = f"unrelaxed growth: cand_raw_delta_d={cand_raw_delta_d:.4e} > {self.rollback_factor} * prev={self.previous_raw_delta_d:.4e}"
                    self.growth_rollback_count += 1

            if rollback_triggered:
                self.rollback_count += 1
                applied_omega_d = self.omega_d_stage1
                applied_omega_u = self.omega_u_stage1
                self.stage = 1
                self.consecutive_stable_iterations = 0

                damage_new = {}
                for n in new_damage_pdas:
                    val = (1.0 - applied_omega_d) * damage[n] + applied_omega_d * new_damage_pdas[n]
                    damage_new[n] = min(1.0, max(self.d0[n], val))
                delta_d = max(abs(damage_new[n] - damage[n]) for n in damage_new)
                raw_delta_d = cand_raw_delta_d
                print(f"  [ROLLBACK #{self.rollback_count}] Outer {outer:02d}: Reverted to Stage 1 (wd={applied_omega_d:.2f}, wu={applied_omega_u:.2f}). Reason: {rollback_reason}")
            else:
                damage_new = cand_damage
                delta_d = cand_delta_d
                raw_delta_d = cand_raw_delta_d

            # 10. Compute Field Increments
            delta_h = None
            if self.previous_delta_d is not None and hasattr(self, "previous_history") and self.previous_history is not None:
                delta_h = max(abs(history[k] - self.previous_history[k]) for k in history)

            kkt_post = solver.kkt(damage_new, tau_active=1e-6, tau_free=1e-6)

            self.previous_active_set = set(pdas_active)
            self.previous_delta_d = delta_d
            self.previous_raw_delta_d = raw_delta_d
            self.previous_history = dict(history)
            damage = damage_new

            rec = {
                "outer": outer,
                "stage": self.stage,
                "applied_omega_d": applied_omega_d,
                "applied_omega_u": applied_omega_u,
                "anderson_enabled": False,
                "pdas_active_count": len(pdas_active),
                "pdas_free_count": len(pdas_free),
                "delta_active_cardinality": delta_active_card,
                "delta_active_symmetric": delta_active_sym,
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
                "delta_u_relaxed": delta_u_relaxed,
                "delta_u_raw": delta_u_raw,
                "delta_u": delta_u_relaxed,
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
            u_rel_str = f"{delta_u_relaxed:.4e}" if delta_u_relaxed is not None else "N/A"
            u_raw_str = f"{delta_u_raw:.4e}" if delta_u_raw is not None else "N/A"
            print(f"  Outer {outer:02d} [Stage {self.stage}, wd={applied_omega_d:.2f}, wu={applied_omega_u:.2f}]: "
                  f"delta_d={delta_d:.4e}, delta_u_rel={u_rel_str}, delta_u_raw={u_raw_str}, delta_h={delta_h or 0.0:.4e}, "
                  f"|Delta A|={sym_str} (card={card_str}, added={added_str}), stable_count={self.consecutive_stable_iterations}, "
                  f"post_kkt_pass={kkt_post['passed']}, PDAS active={len(pdas_active)}")

            # Strict coupled convergence check
            if (previous_u_trial is not None and
                delta_d <= 1e-5 and
                delta_u_relaxed <= 1e-9 and
                delta_u_raw <= 1e-9 and
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
                    u_trial=u_trial,
                    u_abaqus=u_abaqus,
                    history_trial=history,
                    damage_relaxed=damage,
                    consistent_u=consistent_u,
                    consistent_endpoint=consistent_endpoint,
                    solver=solver,
                    step_idx=step_idx,
                    outer=outer,
                    target_uy=target_uy,
                    delta_d=delta_d,
                    delta_u_relaxed=delta_u_relaxed,
                    delta_u_raw=delta_u_raw,
                    delta_h=delta_h,
                    pdas_active_count=len(pdas_active),
                    pdas_free_count=len(pdas_free)
                )

                if not physical_pass:
                    raise RuntimeError(
                        f"Coupled convergence achieved at outer {outer}, but physical acceptance failed."
                    )
                break

            previous_u_trial = dict(u_trial)
            previous_u_abaqus = dict(u_abaqus)
            previous_h_trial = dict(history)

        if not step_converged:
            applied_omega_d = self.omega_d_stage2 if self.stage == 2 else self.omega_d_stage1
            applied_omega_u = self.omega_u_stage2 if self.stage == 2 else self.omega_u_stage1
            manifest_p = self.package / "PACKAGE_MANIFEST.json"
            manifest = json.loads(manifest_p.read_text(encoding="utf-8")) if manifest_p.is_file() else {}
            pkg_id = manifest.get("package_id", self.package.name)

            summary = {
                "schema": 1,
                "task_id": manifest.get("task_id", "F1626-METHOD-C-SAME-MESH-REPAIRED-CONTROL-EXECUTION"),
                "package_id": pkg_id,
                "label": manifest.get("label", "Same-Mesh Control"),
                "status": "NONCONVERGED",
                "physical_acceptance": "NOT_EVALUATED_NONCONVERGED",
                "step_index": step_idx,
                "outer_iterations_completed": outer,
                "target_uy_mm": target_uy,
                "stage_at_termination": self.stage,
                "applied_omega_d": applied_omega_d,
                "applied_omega_u": applied_omega_u,
                "anderson_enabled": False,
                "total_transitions": self.transition_count,
                "total_rollbacks": self.rollback_count,
                "divergence_rollbacks": self.divergence_rollback_count,
                "growth_rollbacks": self.growth_rollback_count,
                "last_delta_d": self.previous_delta_d,
                "last_delta_u_relaxed": delta_u_relaxed,
                "last_delta_u_raw": delta_u_raw,
                "last_delta_h": delta_h,
                "all_gates_pass": False,
                "iteration_history": self.iteration_records
            }
            with (self.output / "same_mesh_control_equilibration_summary.json").open("w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)

        return summary


def main():
    parser = argparse.ArgumentParser(description="Same-Mesh Control Coupled PDAS Re-Equilibration Driver")
    parser.add_argument("--package", required=True, help="Path to package directory")
    parser.add_argument("--output", required=True, help="Output directory for execution")
    parser.add_argument("--extractor", required=True, help="Path to extractor script")
    parser.add_argument("--memory-gb", type=int, default=16, help="Abaqus memory limit in GB")
    parser.add_argument("--timeout", type=int, default=25200, help="Execution timeout in seconds")
    parser.add_argument("--max-outer", type=int, default=140, help="Maximum outer staggered iterations")
    parser.add_argument("--omega-d-stage1", type=float, default=0.50, help="Stage 1 damage relaxation factor")
    parser.add_argument("--omega-d-stage2", type=float, default=0.85, help="Stage 2 damage relaxation factor")
    parser.add_argument("--omega-u-stage1", type=float, default=1.00, help="Stage 1 displacement relaxation factor")
    parser.add_argument("--omega-u-stage2", type=float, default=0.85, help="Stage 2 displacement relaxation factor")
    parser.add_argument("--max-active-cardinality", type=int, default=500, help="Maximum active set cardinality for Stage 2")
    parser.add_argument("--max-symmetric-diff", type=int, default=10, help="Maximum symmetric difference |Delta A| for Stage 2")
    parser.add_argument("--max-added-nodes", type=int, default=0, help="Maximum newly added nodes Delta A^+ for Stage 2")
    parser.add_argument("--stabilization-window", type=int, default=3, help="Consecutive iterations required for Stage 2")
    parser.add_argument("--rollback-factor", type=float, default=1.05, help="Residual growth threshold factor")
    parser.add_argument("--divergence-factor", type=float, default=1.50, help="Divergence threshold factor")
    parser.add_argument("--catastrophic-delta-d-cap", type=float, default=0.05, help="Catastrophic delta_d cap")
    parser.add_argument("--master-deck", default=None, help="Explicit filename of master input deck")
    parser.add_argument("--abaqus", default="abaqus", help="Abaqus execution command")
    args = parser.parse_args()

    driver = SameMeshControlPDASDriver(
        package=args.package,
        output=args.output,
        extractor=args.extractor,
        memory_gb=args.memory_gb,
        timeout=args.timeout,
        max_outer=args.max_outer,
        omega_d_stage1=args.omega_d_stage1,
        omega_d_stage2=args.omega_d_stage2,
        omega_u_stage1=args.omega_u_stage1,
        omega_u_stage2=args.omega_u_stage2,
        max_active_cardinality=args.max_active_cardinality,
        max_symmetric_diff=args.max_symmetric_diff,
        max_added_nodes=args.max_added_nodes,
        stabilization_window=args.stabilization_window,
        rollback_factor=args.rollback_factor,
        divergence_factor=args.divergence_factor,
        catastrophic_delta_d_cap=args.catastrophic_delta_d_cap,
        master_deck_name=args.master_deck,
        abaqus=args.abaqus
    )
    summary = driver.solve_coupled_equilibration()
    print("\nExecution complete.")
    print(f"Status: {summary.get('status')}")


if __name__ == "__main__":
    main()
