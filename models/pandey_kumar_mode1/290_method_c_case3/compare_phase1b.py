import os, sys, json
sys.path.insert(0, r"D:\Master thesis\Adaptive remeshing")
from tests.unit.test_method_c_framework_phase1a import parse_dat_rf2
from tests.unit.test_method_c_framework_phase1b import parse_inp_element_count

val_dir = r"D:\mc3_local\validation_phase1b"
app_dir = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\290_method_c_case3\local_windows_full_run"

print("CYCLE COMPARISON (Phase 1b Wake-Preserving vs Approved Full Run):")
header = f"{'Cycle':5s} | {'Full Els':8s} | {'Ph1b Els':8s} | {'El Delta %':10s} | {'Ph1b Quad%':10s} | {'Full Tip (x, y)':17s} | {'Ph1b Tip (x, y)':17s} | {'Step1 RF2':9s} | {'Term RF2':8s} | {'Hold Jump':9s}"
print(header)
print("-" * len(header))

for c in [49, 50, 51, 52]:
    phys_p = os.path.join(val_dir, f"PK_METHOD_C_CASE3_CYCLE{c}_PHYS.inp")
    state_p = os.path.join(val_dir, f"PK_METHOD_C_CASE3_CYCLE{c}_state.json")
    dat_p = os.path.join(val_dir, f"PK_METHOD_C_CASE3_CYCLE{c}.dat")
    
    counts = parse_inp_element_count(phys_p)
    rf2_info = parse_dat_rf2(dat_p)
    with open(state_p) as f:
        state = json.load(f)
        
    app_sum_p = os.path.join(app_dir, f"PK_METHOD_C_CASE3_CYCLE{c}_SUMMARY.json")
    with open(app_sum_p) as f:
        app_sum = json.load(f)
        
    if c == 49:
        donor_rf2 = 2.31174
    else:
        prev_dat = os.path.join(val_dir, f"PK_METHOD_C_CASE3_CYCLE{c-1}.dat")
        donor_rf2 = parse_dat_rf2(prev_dat)["terminal_rf2"]
        
    hold_jump = ((rf2_info["step1_rf2"] - donor_rf2) / donor_rf2) * 100.0 if rf2_info["step1_rf2"] else 0.0
    el_delta_pct = ((counts["total"] - app_sum["mesh_total_elements"]) / app_sum["mesh_total_elements"]) * 100.0
    
    row = f"{c:5d} | {app_sum['mesh_total_elements']:8d} | {counts['total']:8d} | {el_delta_pct:9.2f}% | {counts['quad_fraction']*100:9.2f}% | ({app_sum['tip_x']:5.2f}, {app_sum['tip_y']:5.2f})   | ({state['tip_x']:5.2f}, {state['tip_y']:5.2f})   | {rf2_info['step1_rf2']:9.4f} | {rf2_info['terminal_rf2']:8.4f} | {hold_jump:8.2f}%"
    print(row)
