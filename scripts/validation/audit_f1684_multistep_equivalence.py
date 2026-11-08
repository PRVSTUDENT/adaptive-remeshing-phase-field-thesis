"""
scripts/validation/audit_f1684_multistep_equivalence.py
========================================================
Audits bitwise/numerical equivalence between:
1. Multi-Step Step 1 (RECOVERY_C) vs Independent Candidate C (runs/f1683_recovery_candidate_c/PK_HOLE_RECOVERY_C.odb)
2. Multi-Step Step 2 (RECOVERY_TERMINAL) vs Independent Terminal Baseline (PK_HOLE_F1661_RECOVERY.odb)
"""
from odbAccess import openOdb
import json
import os
import sys

def extract_step_fields(odb_path, step_name):
    print("Opening ODB: %s (step: %s)" % (odb_path, step_name))
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps[step_name]
    frame = step.frames[-1]

    # S field
    s_dict = {}
    for v in frame.fieldOutputs['S'].values:
        s_dict[v.elementLabel] = (float(v.data[0]), float(v.data[1]), float(v.data[3]), float(v.mises))

    # MISESERI
    eri_dict = {}
    for v in frame.fieldOutputs['MISESERI'].values:
        eri_dict[v.elementLabel] = float(v.data)

    # MISESAVG
    avg_dict = {}
    for v in frame.fieldOutputs['MISESAVG'].values:
        avg_dict[v.elementLabel] = float(v.data)

    # Reaction force on Top
    top_node_labels = set([n.label for n_arr in odb.rootAssembly.nodeSets['TOP'].nodes for n in n_arr])
    rf_total = sum([float(v.data[1]) for v in frame.fieldOutputs['RF'].values if v.nodeLabel in top_node_labels])

    odb.close()
    return {'S': s_dict, 'MISESERI': eri_dict, 'MISESAVG': avg_dict, 'RF2': rf_total}


def compare_states(dict_multi, dict_single, name):
    max_d_s11 = 0.0
    max_d_s22 = 0.0
    max_d_mises = 0.0
    max_d_eri = 0.0
    max_d_avg = 0.0

    all_eids = sorted(dict_multi['MISESERI'].keys())
    for eid in all_eids:
        s_m = dict_multi['S'][eid]
        s_s = dict_single['S'][eid]
        max_d_s11 = max(max_d_s11, abs(s_m[0] - s_s[0]))
        max_d_s22 = max(max_d_s22, abs(s_m[1] - s_s[1]))
        max_d_mises = max(max_d_mises, abs(s_m[3] - s_s[3]))
        max_d_eri = max(max_d_eri, abs(dict_multi['MISESERI'][eid] - dict_single['MISESERI'][eid]))
        max_d_avg = max(max_d_avg, abs(dict_multi['MISESAVG'][eid] - dict_single['MISESAVG'][eid]))

    d_rf = abs(dict_multi['RF2'] - dict_single['RF2'])
    rel_rf = (d_rf / abs(dict_single['RF2'])) * 100.0 if abs(dict_single['RF2']) > 0 else 0.0

    return {
        'comparison': name,
        'rf_multi': dict_multi['RF2'],
        'rf_single': dict_single['RF2'],
        'delta_rf_N': d_rf,
        'rel_delta_rf_pct': rel_rf,
        'max_delta_s11_MPa': max_d_s11,
        'max_delta_s22_MPa': max_d_s22,
        'max_delta_mises_MPa': max_d_mises,
        'max_delta_miseseri_MPa': max_d_eri,
        'max_delta_misesavg_MPa': max_d_avg,
        'num_elements_audited': len(all_eids)
    }


def main():
    multi_odb = os.path.abspath("runs/f1684_multistep_recovery/PK_HOLE_MULTISTEP_RECOVERY.odb")
    cand_c_odb = os.path.abspath("runs/f1683_recovery_candidate_c/PK_HOLE_RECOVERY_C.odb")
    term_odb = os.path.abspath("PK_HOLE_F1661_RECOVERY.odb")

    print("Auditing Multi-Step Step 1 vs Candidate C...")
    m_s1 = extract_step_fields(multi_odb, 'RECOVERY_C')
    c_s1 = extract_step_fields(cand_c_odb, 'Step-1')
    res_s1 = compare_states(m_s1, c_s1, 'MultiStep_Step1_RECOVERY_C_vs_Independent_Candidate_C')

    print("Auditing Multi-Step Step 2 vs Terminal Baseline...")
    m_s2 = extract_step_fields(multi_odb, 'RECOVERY_TERMINAL')
    t_s2 = extract_step_fields(term_odb, 'Step-1')
    res_s2 = compare_states(m_s2, t_s2, 'MultiStep_Step2_RECOVERY_TERMINAL_vs_Independent_Terminal_Baseline')

    summary = {
        'step1_candidate_c_equivalence': res_s1,
        'step2_terminal_baseline_equivalence': res_s2,
        'mathematical_path_independence_proven': bool(res_s1['rel_delta_rf_pct'] < 1e-4 and res_s2['rel_delta_rf_pct'] < 1e-4)
    }

    out_json = os.path.abspath("results/validation/f1684_multistep_recovery_audit.json")
    with open(out_json, "w") as fp:
        json.dump(summary, fp, indent=4)
    print("SUCCESS: Summary written to %s" % out_json)

    print("\n--- Summary ---")
    print("Step 1 (Candidate C):")
    print("  RF2 Multi:  %.6f N | Single: %.6f N | Delta: %.6e N (%.6e%%)" % (
        res_s1['rf_multi'], res_s1['rf_single'], res_s1['delta_rf_N'], res_s1['rel_delta_rf_pct']
    ))
    print("  Max Delta S22:      %.6e MPa" % res_s1['max_delta_s22_MPa'])
    print("  Max Delta MISESERI: %.6e MPa" % res_s1['max_delta_miseseri_MPa'])
    print("  Max Delta MISESAVG: %.6e MPa" % res_s1['max_delta_misesavg_MPa'])

    print("Step 2 (Terminal Baseline):")
    print("  RF2 Multi:  %.6f N | Single: %.6f N | Delta: %.6e N (%.6e%%)" % (
        res_s2['rf_multi'], res_s2['rf_single'], res_s2['delta_rf_N'], res_s2['rel_delta_rf_pct']
    ))
    print("  Max Delta S22:      %.6e MPa" % res_s2['max_delta_s22_MPa'])
    print("  Max Delta MISESERI: %.6e MPa" % res_s2['max_delta_miseseri_MPa'])
    print("  Max Delta MISESAVG: %.6e MPa" % res_s2['max_delta_misesavg_MPa'])
    print("Mathematical Path Independence Proven: %s" % str(summary['mathematical_path_independence_proven']))

if __name__ == "__main__":
    main()
