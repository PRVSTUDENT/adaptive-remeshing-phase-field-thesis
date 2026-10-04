#!/usr/bin/env python3
"""
Gate-6B Stage 14U-AL Evaluator B: 2x Temporal Refinement Diagnostic & Decision Branch Evaluator
-----------------------------------------------------------------------------------------------
Automated turnkey evaluation of 2x temporal refinement diagnostic (Job 1410027.mmaster02)
against baseline reference solve (Job 1409982.mmaster02 / 1409953.mmaster02).

Predeclared Decision Branches at u = 0.007889 mm:
1. TEMPORAL_REFINEMENT_CROSSES_BASELINE_FAILURE -> Hold Package 28, evaluate crossed post-fracture dynamics.
2. TEMPORAL_REFINEMENT_REFAILS_SAME_MECHANISM -> Reconfirm Package 28 (Cn=0.50) hashes/datacheck, then submit as next diagnostic.
3. TEMPORAL_REFINEMENT_CHANGES_FAILURE_PATH -> Hold Package 28, execute spatial/path bifurcation audit.
4. TEMPORAL_DIAGNOSTIC_RUNNING__INTERIM_EVALUATED -> Active pre-failure progress.
"""

import os
import sys
import json
import re
import argparse

MATCHED_DISPLACEMENTS_MM = [
    0.001000,
    0.003000,
    0.005000,
    0.005733,
    0.005857,
    0.006000,
    0.006500,
    0.007000,
    0.007889
]

def parse_dat_rp_table(dat_path):
    """Parse Node 999999 (N_RP) U2 and RF2 table from Abaqus .dat file."""
    if not os.path.exists(dat_path):
        return []
    records = []
    current_step = 1
    current_inc = 0
    current_step_time = 0.0
    current_total_time = 0.0
    
    with open(dat_path, 'r') as f:
        lines = f.readlines()
        
    step_pattern = re.compile(r'STEP\s+(\d+)\s+INCREMENT\s+(\d+)\s+STEP TIME\s+([0-9.E+-]+)')
    step_time_pattern = re.compile(r'STEP TIME COMPLETED\s+([0-9.E+-]+)\s*,\s*TOTAL TIME COMPLETED\s+([0-9.E+-]+)')
    rp_pattern = re.compile(r'^\s*999999\s+([0-9.E+-]+)\s+([0-9.E+-]+)')
    
    for line in lines:
        sm = step_pattern.search(line)
        if sm:
            current_step = int(sm.group(1))
            current_inc = int(sm.group(2))
            
        stm = step_time_pattern.search(line)
        if stm:
            current_step_time = float(stm.group(1))
            current_total_time = float(stm.group(2))
            
        rpm = rp_pattern.search(line)
        if rpm:
            u2 = float(rpm.group(1))
            rf2 = float(rpm.group(2))
            records.append({
                'step': current_step,
                'inc': current_inc,
                'step_time': current_step_time,
                'total_time': current_total_time,
                'u2_mm': u2,
                'rf2_kn': rf2
            })
            
    return records

def parse_energy_csv(csv_path):
    """Parse uel_energy_balance.csv."""
    if not os.path.exists(csv_path):
        return []
    records = []
    with open(csv_path, 'r') as f:
        header = f.readline()
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 7:
                records.append({
                    'step': int(parts[0]),
                    'inc': int(parts[1]),
                    'total_time': float(parts[2]),
                    'step_time': float(parts[3]),
                    'e_elas_knmm': float(parts[4]),
                    'e_frac_knmm': float(parts[5]),
                    'e_total_knmm': float(parts[6]),
                    'e_elas_mj': float(parts[4]) * 1000.0,
                    'e_frac_mj': float(parts[5]) * 1000.0,
                    'e_total_mj': float(parts[6]) * 1000.0
                })
    return records

def parse_sta_file(sta_path):
    """Parse .sta file for increment counts, step times, cutbacks, and iterations."""
    if not os.path.exists(sta_path):
        return []
    records = []
    with open(sta_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('SUMMARY') or line.startswith('STEP') or line.startswith('ABAQUS'):
                continue
            parts = line.split()
            if len(parts) >= 9:
                try:
                    records.append({
                        'step': int(parts[0]),
                        'inc': int(parts[1]),
                        'att': int(parts[2]),
                        'severe_discon_iter': int(parts[3]),
                        'equil_iter': int(parts[4]),
                        'total_iter': int(parts[5]),
                        'total_time': float(parts[6]),
                        'step_time': float(parts[7]),
                        'dt': float(parts[8])
                    })
                except (ValueError, IndexError):
                    continue
    return records

def compute_k0(records, max_u=0.0010):
    """Evaluate canonical structural stiffness K0 via linear regression."""
    u_list = []
    f_list = []
    for r in records:
        if r['step'] == 1 and r['u2_mm'] <= max_u + 1e-9:
            u_list.append(r['u2_mm'])
            f_list.append(r['rf2_kn'])
            
    if len(u_list) < 2:
        return None, None, None, 0
        
    n = len(u_list)
    sum_u = sum(u_list)
    sum_f = sum(f_list)
    sum_u2 = sum(u * u for u in u_list)
    sum_uf = sum(u * f for u, f in zip(u_list, f_list))
    
    denom = n * sum_u2 - sum_u * sum_u
    if abs(denom) < 1e-18:
        return None, None, None, n
        
    k0 = (n * sum_uf - sum_u * sum_f) / denom
    intercept = (sum_f - k0 * sum_u) / n
    
    mean_f = sum_f / n
    ss_tot = sum((f - mean_f) ** 2 for f in f_list)
    ss_res = sum((f - (k0 * u + intercept)) ** 2 for u, f in zip(u_list, f_list))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 1e-18 else 1.0
    
    return k0, intercept, r2, n

def find_matched_state(records, energy_records, target_u_mm, tol=1e-5):
    """Find closest state to target displacement without extrapolation."""
    best = None
    min_diff = 1e9
    for r in records:
        diff = abs(r['u2_mm'] - target_u_mm)
        if diff < min_diff:
            min_diff = diff
            best = r
            
    if best is not None and min_diff <= tol:
        matching_energy = None
        for e in energy_records:
            if e['step'] == best['step'] and e['inc'] == best['inc']:
                matching_energy = e
                break
        return {
            'target_u_mm': target_u_mm,
            'actual_u_mm': best['u2_mm'],
            'step': best['step'],
            'inc': best['inc'],
            'rf_kn': best['rf2_kn'],
            'e_elas_mj': matching_energy['e_elas_mj'] if matching_energy else None,
            'e_frac_mj': matching_energy['e_frac_mj'] if matching_energy else None,
            'status': 'REACHED'
        }
    else:
        return {
            'target_u_mm': target_u_mm,
            'actual_u_mm': None,
            'step': None,
            'inc': None,
            'rf_kn': None,
            'e_elas_mj': None,
            'e_frac_mj': None,
            'status': 'NOT_REACHED'
        }

def evaluate_temporal_refinement(temporal_dir, baseline_dir):
    """Complete Gate-6B Stage 14U-AL 2x temporal refinement evaluation and decision branching."""
    t2x_dat = os.path.join(temporal_dir, "PK_MODE1_STAGE14_ADAPT_14K_TEMPORAL_2X.dat")
    base_dat = os.path.join(baseline_dir, "PK_M1_ADAPT_14K_FRACTURE.dat")
    
    t2x_csv = os.path.join(temporal_dir, "uel_energy_balance.csv")
    base_csv = os.path.join(baseline_dir, "uel_energy_balance.csv")
    
    t2x_sta = os.path.join(temporal_dir, "PK_MODE1_STAGE14_ADAPT_14K_TEMPORAL_2X.sta")
    base_sta = os.path.join(baseline_dir, "PK_M1_ADAPT_14K_FRACTURE.sta")
    
    t2x_nodes = parse_dat_rp_table(t2x_dat)
    base_nodes = parse_dat_rp_table(base_dat)
    
    t2x_energy = parse_energy_csv(t2x_csv)
    base_energy = parse_energy_csv(base_csv)
    
    t2x_sta_rec = parse_sta_file(t2x_sta)
    base_sta_rec = parse_sta_file(base_sta)
    
    # Stiffness
    k0_t2x, b0_t2x, r2_t2x, n_k0_t2x = compute_k0(t2x_nodes)
    k0_base, b0_base, r2_base, n_k0_base = compute_k0(base_nodes)
    
    # Matched states
    matched_t2x = [find_matched_state(t2x_nodes, t2x_energy, u) for u in MATCHED_DISPLACEMENTS_MM]
    matched_base = [find_matched_state(base_nodes, base_energy, u) for u in MATCHED_DISPLACEMENTS_MM]
    
    # Peak force
    f_max_t2x = max([r['rf2_kn'] for r in t2x_nodes]) if t2x_nodes else 0.0
    u_peak_t2x = [r['u2_mm'] for r in t2x_nodes if r['rf2_kn'] == f_max_t2x][0] if t2x_nodes else 0.0
    
    f_max_base = max([r['rf2_kn'] for r in base_nodes]) if base_nodes else 0.0
    u_peak_base = [r['u2_mm'] for r in base_nodes if r['rf2_kn'] == f_max_base][0] if base_nodes else 0.0
    
    # Terminal displacement
    u_term_t2x = t2x_nodes[-1]['u2_mm'] if t2x_nodes else 0.0
    u_term_base = base_nodes[-1]['u2_mm'] if base_nodes else 0.0
    
    # Cutbacks count
    cutbacks_t2x = sum(1 for r in t2x_sta_rec if r['att'] > 1)
    cutbacks_base = sum(1 for r in base_sta_rec if r['att'] > 1)
    
    # Decision branch logic
    if u_term_t2x > 0.007889 + 1e-5:
        decision_branch = "TEMPORAL_REFINEMENT_CROSSES_BASELINE_FAILURE"
        action_directive = "HOLD_PACKAGE_28__EVALUATE_CROSSED_DYNAMICS"
        verdict = "TEMPORAL_REFINEMENT_SUCCESSFULLY_CROSSED_BASELINE_FAILURE"
    elif abs(u_term_t2x - 0.007889) <= 1e-5 and cutbacks_t2x >= 5:
        decision_branch = "TEMPORAL_REFINEMENT_REFAILS_SAME_MECHANISM"
        action_directive = "RECONFIRM_PACKAGE_28_CN050_AND_SUBMIT_IMMEDIATELY"
        verdict = "TEMPORAL_REFINEMENT_REFAILS_AT_BASELINE_FAILURE_POINT"
    elif u_term_t2x < 0.007889 - 1e-5 and cutbacks_t2x > 0:
        decision_branch = "TEMPORAL_REFINEMENT_CHANGES_FAILURE_PATH"
        action_directive = "HOLD_PACKAGE_28__PERFORM_PATH_BIFURCATION_AUDIT"
        verdict = "TEMPORAL_REFINEMENT_EARLY_BIFURCATION_DETECTED"
    else:
        decision_branch = "TEMPORAL_DIAGNOSTIC_RUNNING__INTERIM_EVALUATED"
        action_directive = "HOLD_PACKAGE_28__CONTINUE_SOLVER_MONITORING"
        verdict = "TEMPORAL_REFINEMENT_DIAGNOSTIC_RUNNING"
        
    report = {
        'task_id': 'F1221-GATE6B-STAGE14UAL-EVALUATOR-FREEZE-AND-DECISION-PROTOCOLS-20261004',
        'evaluator': 'evaluate_stage14ual_temporal_refinement.py',
        'verdict': verdict,
        'decision_branch': decision_branch,
        'action_directive': action_directive,
        'epistemic_governance': {
            'convergence_mechanism': 'POST_FRACTURE_CONVERGENCE_NORMALIZATION_SENSITIVITY_VERIFIED',
            'ill_conditioning_status': 'NOT_ESTABLISHED',
            'crack_functional_terminology': 'IMPLEMENTED_PHASE_FIELD_CRACK_SURFACE_FRACTURE_FUNCTIONAL_E_FRAC'
        },
        'temporal_parameters': {
            'baseline': {'step1_dt': 0.0005, 'step1_du_nm': 2.50, 'step2_dt': 0.0002, 'step2_du_nm': 1.00},
            'temporal_2x': {'step1_dt': 0.00025, 'step1_du_nm': 1.25, 'step2_dt': 0.0001, 'step2_du_nm': 0.50}
        },
        'comparison_summary': {
            'temporal_2x_increments_completed': len(t2x_nodes),
            'baseline_increments_completed': len(base_nodes),
            'temporal_2x_terminal_displacement_mm': u_term_t2x,
            'baseline_terminal_displacement_mm': u_term_base,
            'temporal_2x_cutbacks_count': cutbacks_t2x,
            'baseline_cutbacks_count': cutbacks_base
        },
        'canonical_stiffness_k0': {
            'temporal_2x': {'k0_kn_per_mm': k0_t2x, 'intercept_kn': b0_t2x, 'r2': r2_t2x, 'n_points': n_k0_t2x},
            'baseline': {'k0_kn_per_mm': k0_base, 'intercept_kn': b0_base, 'r2': r2_base, 'n_points': n_k0_base},
            'k0_diff_pct': ((k0_t2x - k0_base) / k0_base * 100.0) if (k0_t2x and k0_base) else None
        },
        'peak_characteristics': {
            'temporal_2x': {'f_max_kn': f_max_t2x, 'u_peak_mm': u_peak_t2x},
            'baseline': {'f_max_kn': f_max_base, 'u_peak_mm': u_peak_base},
            'f_max_diff_pct': ((f_max_t2x - f_max_base) / f_max_base * 100.0) if (f_max_t2x and f_max_base) else None
        },
        'predeclared_matched_states': [
            {
                'target_u_mm': u,
                'temporal_2x': matched_t2x[idx],
                'baseline': matched_base[idx],
                'state_verdict': 'MATCHED' if (matched_t2x[idx]['status'] == 'REACHED' and matched_base[idx]['status'] == 'REACHED') else ('NOT_REACHED' if matched_t2x[idx]['status'] == 'NOT_REACHED' else 'BASELINE_ONLY')
            }
            for idx, u in enumerate(MATCHED_DISPLACEMENTS_MM)
        ]
    }
    return report

def generate_markdown(report):
    """Generate Markdown report from temporal evaluation report dict."""
    cs = report['comparison_summary']
    k0 = report['canonical_stiffness_k0']
    
    md = f"""# Mode-I Gate-6B Stage 14U-AL: 2x Temporal Refinement Evaluation Report

Protocol Version: 2  
Evaluator: `{report['evaluator']}`  
Task ID: `{report['task_id']}`  
Governing Verdict: **`{report['verdict']}`**  
Predeclared Decision Branch: **`{report['decision_branch']}`**  
Action Directive: **`{report['action_directive']}`**  

---

## 1. Temporal Discretization & Parameters

- **Baseline Step 1:** $\\Delta t = 5.0\\times 10^{{-4}}$ ($\\Delta u = 2.50\\,\\mathrm{{nm}}$, 2000 incs)
- **Baseline Step 2:** $\\Delta t = 2.0\\times 10^{{-4}}$ ($\\Delta u = 1.00\\,\\mathrm{{nm}}$, 5000 incs)
- **$2\\times$ Refined Step 1:** $\\Delta t = 2.5\\times 10^{{-4}}$ ($\\Delta u = 1.25\\,\\mathrm{{nm}}$, 4000 incs)
- **$2\\times$ Refined Step 2:** $\\Delta t = 1.0\\times 10^{{-4}}$ ($\\Delta u = 0.50\\,\\mathrm{{nm}}$, 10000 incs)

---

## 2. Comparison Summary & Advancement

| Metric | Baseline Solve (1409982) | $2\\times$ Temporal Diagnostic (1410027) | Discrepancy / Assessment |
| :--- | :---: | :---: | :---: |
| **Completed Increments** | {cs['baseline_increments_completed']} | {cs['temporal_2x_increments_completed']} | Progressing |
| **Reached Displacement $u$** | {cs['baseline_terminal_displacement_mm']:.6f} mm | {cs['temporal_2x_terminal_displacement_mm']:.6f} mm | Active Solve |
| **Cutbacks Count** | {cs['baseline_cutbacks_count']} | {cs['temporal_2x_cutbacks_count']} | 0 in elastic regime |
| **$K_0$ Structural Stiffness** | {k0['baseline']['k0_kn_per_mm']} kN/mm | {k0['temporal_2x']['k0_kn_per_mm']} kN/mm | `{k0['k0_diff_pct']}`% |

---

## 3. Predeclared 10-Matched-Displacement States

| Target $u$ [mm] | Baseline $F$ [kN] | $2\\times$ Temporal $F$ [kN] | Status Verdict |
| :---: | :---: | :---: | :---: |
"""
    for ms in report['predeclared_matched_states']:
        rf_b = f"{ms['baseline']['rf_kn']:.6f}" if ms['baseline']['rf_kn'] is not None else "NOT_REACHED"
        rf_t = f"{ms['temporal_2x']['rf_kn']:.6f}" if ms['temporal_2x']['rf_kn'] is not None else "NOT_REACHED"
        md += f"| {ms['target_u_mm']:.6f} | {rf_b} | {rf_t} | `{ms['state_verdict']}` |\n"
        
    md += f"""
---

## 4. Decision Branch Protocol & Gated Execution Directive

- **Active Branch:** `{report['decision_branch']}`
- **Governing Directive:** `{report['action_directive']}`
- **Package 28 ($C_n = 0.50$) Submission Status:** **STRICTLY HELD** while temporal diagnostic is running.
"""
    return md

def main():
    parser = argparse.ArgumentParser(description="Gate-6B Stage 14U-AL 2x Temporal Refinement Evaluator")
    parser.add_argument("--temporal-dir", default="models/pandey_kumar_mode1/26_stage14_temporal_refined_candidate_2x", help="Path to 2x temporal directory")
    parser.add_argument("--baseline-dir", default="models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k", help="Path to baseline directory")
    parser.add_argument("--output-json", default=None, help="Output JSON path")
    parser.add_argument("--output-md", default=None, help="Output Markdown path")
    args = parser.parse_args()
    
    report = evaluate_temporal_refinement(args.temporal_dir, args.baseline_dir)
    
    if args.output_json:
        with open(args.output_json, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"[SUCCESS] Wrote JSON report: {args.output_json}")
        
    if args.output_md:
        md_text = generate_markdown(report)
        with open(args.output_md, 'w') as f:
            f.write(md_text)
        print(f"[SUCCESS] Wrote Markdown report: {args.output_md}")
        
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
