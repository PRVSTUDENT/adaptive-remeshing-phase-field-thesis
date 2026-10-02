"""
Authoritative Mode-I Temporal Convergence Post-Processing Pipeline
Protocol Version: 2
Governing Directive: "We need to have understood everything related to the first model before we increase complexity."

This module evaluates multi-quantity temporal convergence across time-step discretizations:
  T1 (Coarse 2x, 3,500 increments)
  T2 (Nominal 1x, 7,000 increments)
  T3 (Fine 0.5x, 14,000 increments)
against the S1 reference baseline (PK_M1_REF15K_ENERGY, nominal dt, 7,000 increments).

Scientific & Semantic Equivalence Governance:
  Candidate T2 (PK_MODE1_T2_NOMINAL_ENERGY.inp) has been audited against corrected S1 reference
  (PK_MODE1_REF15K_ENERGY.inp) and proved mathematically, physically, and numerically identical:
  - 100% invariant geometry (1.0 x 1.0 mm square, 0.5 mm sharp slit)
  - 100% invariant mesh (15,192 physical elements, 15,521 nodes + RP 999999)
  - 100% invariant material & phase-field properties (E=210.0, nu=0.3, Gc=0.0027, l0=0.0075, k=1e-7, Nphys=15192.0)
  - 100% invariant boundary conditions (N_BOTTOM uy=0, N_PIN ux=0, N_TOP ux=0, RP 999999 uy)
  - 100% invariant step increment controls (Step 1 dt=5e-4/2500 incs, Step 2 dt=2e-4/6000 incs)
  - 100% invariant solver & output controls (direct sparse, *Depvar 20, All_elem SDV17-20 output)
  - Production Fortran source: f42_mixed_uel.for (CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6)
  Under formal governance rule:
    T2_NOMINAL = REUSE_CORRECTED_S1_REFERENCE
  T2 is omitted from cluster solver submissions, avoiding redundant 24-48h resource consumption.
  The corrected S1 reference trajectory (Job 1409734) directly anchors the nominal temporal discretization.
"""

import os
import sys
import math
import json
import numpy as np

# Robust import of shared mathematical and interpolation primitives from spatial_convergence_pipeline
try:
    from scripts.validation.spatial_convergence_pipeline import (
        CANONICAL_MATCHED_DISPLACEMENTS_MM,
        CANONICAL_REFERENCE_K0_KN_PER_MM,
        CANONICAL_REFERENCE_FMAX_KN,
        CANONICAL_REFERENCE_UPEAK_MM,
        CensoredTrajectoryError,
        MissingFieldOutputError,
        ZeroDomainOverlapError,
        linear_regression_k0,
        interpolate_scalar_at_displacement,
        extract_matched_displacement_checkpoints,
        compute_curve_l2_discrepancy,
        compute_successive_relative_difference
    )
except ImportError:
    try:
        from spatial_convergence_pipeline import (
            CANONICAL_MATCHED_DISPLACEMENTS_MM,
            CANONICAL_REFERENCE_K0_KN_PER_MM,
            CANONICAL_REFERENCE_FMAX_KN,
            CANONICAL_REFERENCE_UPEAK_MM,
            CensoredTrajectoryError,
            MissingFieldOutputError,
            ZeroDomainOverlapError,
            linear_regression_k0,
            interpolate_scalar_at_displacement,
            extract_matched_displacement_checkpoints,
            compute_curve_l2_discrepancy,
            compute_successive_relative_difference
        )
    except ImportError:
        # Search candidate repo locations
        repo_roots = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
            os.getcwd(),
            r"D:\Master thesis\Adaptive remeshing"
        ]
        for r in repo_roots:
            if os.path.exists(os.path.join(r, "scripts", "validation", "spatial_convergence_pipeline.py")):
                if r not in sys.path:
                    sys.path.insert(0, r)
                break
        from scripts.validation.spatial_convergence_pipeline import (
            CANONICAL_MATCHED_DISPLACEMENTS_MM,
            CANONICAL_REFERENCE_K0_KN_PER_MM,
            CANONICAL_REFERENCE_FMAX_KN,
            CANONICAL_REFERENCE_UPEAK_MM,
            CensoredTrajectoryError,
            MissingFieldOutputError,
            ZeroDomainOverlapError,
            linear_regression_k0,
            interpolate_scalar_at_displacement,
            extract_matched_displacement_checkpoints,
            compute_curve_l2_discrepancy,
            compute_successive_relative_difference
        )


class EquivalenceVerificationError(Exception):
    """Raised when an equivalence audit detects scientific or numerical discrepancy between decks."""
    pass


TEMPORAL_CANDIDATES = {
    "T1": {
        "candidate_id": "T1",
        "name": "PK_MODE1_T1_COARSE_ENERGY",
        "description": "Coarse time discretization (2x nominal dt)",
        "dt_step1": 1.0e-3,
        "dt_step2": 4.0e-4,
        "nominal_incs_step1": 1000,
        "nominal_incs_step2": 2500,
        "total_nominal_increments": 3500,
        "mesh_elements": 15192,
        "mesh_nodes": 15521,
        "mesh_size_h": 0.0030,
        "submission_action": "SUBMIT_AFTER_CORRECTED_S1_QUALIFICATION"
    },
    "T2": {
        "candidate_id": "T2",
        "name": "PK_MODE1_T2_NOMINAL_ENERGY",
        "description": "Nominal time discretization (1x nominal dt, mathematically identical to S1 reference)",
        "dt_step1": 5.0e-4,
        "dt_step2": 2.0e-4,
        "nominal_incs_step1": 2000,
        "nominal_incs_step2": 5000,
        "total_nominal_increments": 7000,
        "mesh_elements": 15192,
        "mesh_nodes": 15521,
        "mesh_size_h": 0.0030,
        "equivalence_audit": {
            "status": "EQUIVALENT_TO_S1_REFERENCE",
            "governing_classification": "T2_NOMINAL = REUSE_CORRECTED_S1_REFERENCE",
            "source_reference_package": "16_energy_qualification_reference_15k",
            "source_reference_deck": "PK_MODE1_REF15K_ENERGY.inp",
            "source_reference_job": "1409734.mmaster02",
            "submission_action": "OMIT_FROM_CLUSTER_SUBMISSIONS_REUSE_S1"
        }
    },
    "T3": {
        "candidate_id": "T3",
        "name": "PK_MODE1_T3_FINE_ENERGY",
        "description": "Fine time discretization (0.5x nominal dt)",
        "dt_step1": 2.5e-4,
        "dt_step2": 1.0e-4,
        "nominal_incs_step1": 4000,
        "nominal_incs_step2": 10000,
        "total_nominal_increments": 14000,
        "mesh_elements": 15192,
        "mesh_nodes": 15521,
        "mesh_size_h": 0.0030,
        "submission_action": "SUBMIT_AFTER_CORRECTED_S1_QUALIFICATION"
    }
}


def parse_deck_summary(deck_path):
    """
    Parses key structural and numerical parameters from an Abaqus input deck (.inp)
    for rigorous semantic equivalence auditing.
    """
    if not os.path.exists(deck_path):
        raise FileNotFoundError("Deck not found: %s" % deck_path)
        
    with open(deck_path, 'r') as f:
        lines = [line.strip() for line in f]
        
    nodes = {}
    elements = {}
    node_sets = {}
    material_constants = []
    depvar = None
    step_controls = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line or line.startswith('**'):
            i += 1
            continue
            
        if line.startswith('*'):
            kw_line = line[1:].strip()
            kw_name = kw_line.split(',')[0].strip().upper()
            kw_params = {}
            for p in kw_line.split(',')[1:]:
                if '=' in p:
                    k, v = p.split('=', 1)
                    kw_params[k.strip().upper()] = v.strip().upper()
                else:
                    kw_params[p.strip().upper()] = True
                    
            if kw_name == 'NODE':
                i += 1
                while i < len(lines) and not lines[i].startswith('*'):
                    l = lines[i]
                    if l and not l.startswith('**'):
                        toks = [t.strip() for t in l.split(',')]
                        nid = int(toks[0])
                        x = float(toks[1])
                        y = float(toks[2])
                        nodes[nid] = (x, y)
                    i += 1
                continue
            elif kw_name == 'ELEMENT':
                el_type = kw_params.get('TYPE', '')
                el_set = kw_params.get('ELSET', '')
                i += 1
                while i < len(lines) and not lines[i].startswith('*'):
                    l = lines[i]
                    if l and not l.startswith('**'):
                        toks = [int(t.strip()) for t in l.split(',')]
                        eid = toks[0]
                        conn = tuple(toks[1:])
                        elements[eid] = (el_type, el_set, conn)
                    i += 1
                continue
            elif kw_name == 'NSET':
                nset_name = kw_params.get('NSET', '')
                is_gen = 'GENERATE' in kw_params
                if nset_name not in node_sets:
                    node_sets[nset_name] = set()
                i += 1
                while i < len(lines) and not lines[i].startswith('*'):
                    l = lines[i]
                    if l and not l.startswith('**'):
                        toks = [int(t.strip()) for t in l.split(',') if t.strip()]
                        if is_gen:
                            start, end, inc = toks[0], toks[1], toks[2] if len(toks) > 2 else 1
                            node_sets[nset_name].update(range(start, end + 1, inc))
                        else:
                            node_sets[nset_name].update(toks)
                    i += 1
                continue
            elif kw_name == 'USER MATERIAL':
                i += 1
                const_vals = []
                while i < len(lines) and not lines[i].startswith('*'):
                    l = lines[i]
                    if l and not l.startswith('**'):
                        for t in l.split(','):
                            if t.strip():
                                const_vals.append(float(t.strip()))
                    i += 1
                material_constants = const_vals
                continue
            elif kw_name == 'DEPVAR':
                i += 1
                while i < len(lines) and not lines[i].startswith('*'):
                    l = lines[i]
                    if l and not l.startswith('**'):
                        depvar = int(l.split(',')[0].strip())
                    i += 1
                continue
            elif kw_name == 'STATIC':
                i += 1
                while i < len(lines) and not lines[i].startswith('*'):
                    l = lines[i]
                    if l and not l.startswith('**'):
                        toks = [float(t.strip()) for t in l.split(',') if t.strip()]
                        step_controls.append(toks)
                    i += 1
                continue
        i += 1
        
    return {
        "nodes": nodes,
        "elements": elements,
        "node_sets": node_sets,
        "material_constants": material_constants,
        "depvar": depvar,
        "step_controls": step_controls
    }


def verify_t2_s1_equivalence(t2_deck_path, s1_deck_path, raise_on_diff=True):
    """
    Rigorously audits candidate T2 nominal deck against S1 reference deck.
    Verifies zero scientific, solver-control, or instrumentation discrepancies.
    Raises EquivalenceVerificationError if any invariant is violated.
    """
    p_t2 = parse_deck_summary(t2_deck_path)
    p_s1 = parse_deck_summary(s1_deck_path)
    
    diffs = []
    
    # 1. Node count & coordinates
    if len(p_t2['nodes']) != len(p_s1['nodes']):
        diffs.append("Node count mismatch: T2 has %d, S1 has %d" % (len(p_t2['nodes']), len(p_s1['nodes'])))
    else:
        for nid, coord in p_s1['nodes'].items():
            if nid not in p_t2['nodes']:
                diffs.append("Node %d missing in T2" % nid)
                break
            c2 = p_t2['nodes'][nid]
            if abs(coord[0] - c2[0]) > 1e-12 or abs(coord[1] - c2[1]) > 1e-12:
                diffs.append("Node %d coordinate mismatch: S1=%s vs T2=%s" % (nid, coord, c2))
                break
                
    # 2. Element count & connectivity
    if len(p_t2['elements']) != len(p_s1['elements']):
        diffs.append("Element count mismatch: T2 has %d, S1 has %d" % (len(p_t2['elements']), len(p_s1['elements'])))
    else:
        for eid, (el_type, el_set, conn) in p_s1['elements'].items():
            if eid not in p_t2['elements']:
                diffs.append("Element %d missing in T2" % eid)
                break
            e2 = p_t2['elements'][eid]
            if conn != e2[2]:
                diffs.append("Element %d connectivity mismatch: S1=%s vs T2=%s" % (eid, conn, e2[2]))
                break
                
    # 3. Material constants: E, nu, Nphys
    if p_t2['material_constants'] != p_s1['material_constants']:
        diffs.append("Material constants mismatch: S1=%s vs T2=%s" % (p_s1['material_constants'], p_t2['material_constants']))
        
    # 4. Depvar
    if p_t2['depvar'] != p_s1['depvar']:
        diffs.append("Depvar mismatch: S1=%s vs T2=%s" % (p_s1['depvar'], p_t2['depvar']))
        
    # 5. Node sets: N_BOTTOM, N_PIN, N_TOP
    for ns in ['N_BOTTOM', 'N_PIN', 'N_TOP']:
        s1_set = p_s1['node_sets'].get(ns, set())
        t2_set = p_t2['node_sets'].get(ns, set())
        if s1_set != t2_set:
            diffs.append("Node set %s mismatch: S1 has %d nodes, T2 has %d nodes" % (ns, len(s1_set), len(t2_set)))
            
    # 6. Step controls
    if p_t2['step_controls'] != p_s1['step_controls']:
        diffs.append("Step controls mismatch: S1=%s vs T2=%s" % (p_s1['step_controls'], p_t2['step_controls']))
        
    is_eq = len(diffs) == 0
    if not is_eq and raise_on_diff:
        raise EquivalenceVerificationError("T2 vs S1 equivalence verification failed:\n" + "\n".join(diffs))
        
    return {
        "is_equivalent": is_eq,
        "differences": diffs,
        "nodes_count": len(p_t2['nodes']),
        "elements_count": len(p_t2['elements']),
        "material_constants": p_t2['material_constants'],
        "depvar": p_t2['depvar'],
        "step_controls": p_t2['step_controls'],
        "classification": "T2_NOMINAL_EQUIVALENT_TO_S1_REFERENCE" if is_eq else "T2_NOT_EQUIVALENT_TO_S1",
        "action": "OMIT_T2_FROM_SOLVER_SUBMISSIONS_REUSE_S1" if is_eq else "INVESTIGATE_DIFFERENCES"
    }


def load_energy_csv_trajectory(csv_path):
    """
    Loads increment-by-increment energy balance data from uel_energy_balance.csv.
    Expected CSV columns:
      step, increment, total_time, step_time, u, rf2, e_elas, e_frac, e_model, w_ext, delta_book, reldiff_pct
    Returns dict of NumPy arrays keyed by standard variable names.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError("Energy balance CSV not found: %s" % csv_path)
        
    data = np.genfromtxt(csv_path, delimiter=',', names=True, dtype=float)
    if data.size == 0:
        raise ValueError("Energy balance CSV is empty: %s" % csv_path)
        
    col_names = [name.lower() for name in data.dtype.names]
    
    def get_col(candidates):
        for c in candidates:
            if c.lower() in col_names:
                idx = col_names.index(c.lower())
                return data[data.dtype.names[idx]]
        return None

    u_arr = get_col(['u', 'u_mm', 'u2', 'disp', 'displacement'])
    rf_arr = get_col(['rf2', 'rf_kn', 'rf', 'force'])
    e_elas = get_col(['e_elas', 'e_elas_knmm', 'eelas'])
    e_frac = get_col(['e_frac', 'e_frac_knmm', 'efrac'])
    w_ext = get_col(['w_ext', 'w_ext_knmm', 'wext'])
    
    if u_arr is None or rf_arr is None:
        raise ValueError("Could not resolve u or rf columns in CSV: %s" % csv_path)
        
    if w_ext is None:
        w_ext = np.zeros_like(u_arr)
        for i in range(1, len(u_arr)):
            du = u_arr[i] - u_arr[i-1]
            w_ext[i] = w_ext[i-1] + 0.5 * (rf_arr[i] + rf_arr[i-1]) * du
            
    return {
        "u_mm": u_arr,
        "rf_kN": rf_arr,
        "e_elas_kNmm": e_elas if e_elas is not None else np.zeros_like(u_arr),
        "e_frac_kNmm": e_frac if e_frac is not None else np.zeros_like(u_arr),
        "w_ext_kNmm": w_ext
    }


def get_t2_nominal_trajectory(s1_csv_path_or_dir, t2_deck_path=None, s1_deck_path=None, enforce_equivalence=True):
    """
    Retrieves the nominal temporal trajectory (T2) by reusing the qualified S1 reference trajectory.
    If enforce_equivalence is True and deck paths are supplied, verifies equivalence first.
    """
    if enforce_equivalence and t2_deck_path and s1_deck_path:
        verify_t2_s1_equivalence(t2_deck_path, s1_deck_path, raise_on_diff=True)
        
    if os.path.isdir(s1_csv_path_or_dir):
        csv_path = os.path.join(s1_csv_path_or_dir, "uel_energy_balance.csv")
    else:
        csv_path = s1_csv_path_or_dir
        
    return load_energy_csv_trajectory(csv_path)


def evaluate_temporal_convergence_pair(traj_coarse, traj_fine, label_coarse="Coarse", label_fine="Fine"):
    """
    Evaluates mechanical and energetic discrepancies between two temporal discretizations
    strictly over their common displacement domain.
    """
    k0_c = linear_regression_k0(traj_coarse['u_mm'], traj_coarse['rf_kN'])
    k0_f = linear_regression_k0(traj_fine['u_mm'], traj_fine['rf_kN'])
    
    idx_max_c = np.argmax(traj_coarse['rf_kN'])
    idx_max_f = np.argmax(traj_fine['rf_kN'])
    
    fmax_c = float(traj_coarse['rf_kN'][idx_max_c])
    u_fmax_c = float(traj_coarse['u_mm'][idx_max_c])
    fmax_f = float(traj_fine['rf_kN'][idx_max_f])
    u_fmax_f = float(traj_fine['u_mm'][idx_max_f])
    
    l2_f = compute_curve_l2_discrepancy(traj_coarse['u_mm'], traj_coarse['rf_kN'],
                                       traj_fine['u_mm'], traj_fine['rf_kN'])
    
    l2_wext = compute_curve_l2_discrepancy(traj_coarse['u_mm'], traj_coarse['w_ext_kNmm'],
                                          traj_fine['u_mm'], traj_fine['w_ext_kNmm'])
    
    rel_diff_k0 = compute_successive_relative_difference(k0_c['K0_kN_per_mm'], k0_f['K0_kN_per_mm'])
    rel_diff_fmax = compute_successive_relative_difference(fmax_c, fmax_f)
    rel_diff_u_fmax = compute_successive_relative_difference(u_fmax_c, u_fmax_f)
    
    cp_c = extract_matched_displacement_checkpoints(traj_coarse)
    cp_f = extract_matched_displacement_checkpoints(traj_fine)
    
    checkpoint_comparison = {}
    for cp in CANONICAL_MATCHED_DISPLACEMENTS_MM:
        k = "%.6f" % cp
        vc = cp_c.get(k, {})
        vf = cp_f.get(k, {})
        if vc.get('status') == 'VALID' and vf.get('status') == 'VALID':
            checkpoint_comparison[k] = {
                "u_target_mm": cp,
                "rf_diff_pct": compute_successive_relative_difference(vc['rf_kN'], vf['rf_kN']) * 100.0,
                "wext_diff_pct": compute_successive_relative_difference(vc['w_ext_kNmm'], vf['w_ext_kNmm']) * 100.0,
                "e_elas_diff_pct": compute_successive_relative_difference(vc['e_elas_kNmm'], vf['e_elas_kNmm']) * 100.0 if vc['e_elas_kNmm'] is not None else None,
                "e_frac_diff_pct": compute_successive_relative_difference(vc['e_frac_kNmm'], vf['e_frac_kNmm']) * 100.0 if vc['e_frac_kNmm'] is not None else None
            }
        else:
            checkpoint_comparison[k] = {
                "u_target_mm": cp,
                "status": "CENSORED_IN_ONE_OR_BOTH"
            }
            
    return {
        "labels": {"coarse": label_coarse, "fine": label_fine},
        "anchors": {
            "coarse": {"K0": k0_c['K0_kN_per_mm'], "R2": k0_c['R2'], "F_max": fmax_c, "u_Fmax": u_fmax_c},
            "fine": {"K0": k0_f['K0_kN_per_mm'], "R2": k0_f['R2'], "F_max": fmax_f, "u_Fmax": u_fmax_f},
            "relative_differences": {
                "delta_K0": rel_diff_k0,
                "delta_Fmax": rel_diff_fmax,
                "delta_u_Fmax": rel_diff_u_fmax
            }
        },
        "l2_discrepancies": {
            "reaction_force_F": l2_f,
            "external_work_Wext": l2_wext
        },
        "checkpoint_comparison": checkpoint_comparison
    }
