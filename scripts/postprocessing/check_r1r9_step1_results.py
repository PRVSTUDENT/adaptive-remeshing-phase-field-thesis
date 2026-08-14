#!/usr/bin/env python3
import sys
from pathlib import Path

def main():
    pkg_dir = Path("/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R9")
    dat_path = pkg_dir / "M2STATE_FRACFIX_RESTART1R1R9_STEP1.dat"
    
    text = dat_path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    
    rp_rf1 = None
    bot_rf1_sum = 0.0
    bot_rf2_sum = 0.0
    
    in_node_table = False
    for l in lines:
        if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in l:
            in_node_table = True
            continue
        if in_node_table:
            if "THE FOLLOWING TABLE" in l or "MAXIMUM" in l:
                in_node_table = False
                continue
            parts = l.split()
            if not parts:
                continue
            try:
                nid = int(parts[0])
                if nid == 99999:
                    # Line format: 99999  5.0000000E-03  6.3678713E-02
                    rp_rf1 = float(parts[-1])
                elif len(parts) >= 6:
                    # Standard node line: NODE U1 U2 U3 RF1 RF2 RF3
                    rf1 = float(parts[4])
                    rf2 = float(parts[5])
                    bot_rf1_sum += rf1
                    bot_rf2_sum += rf2
            except (ValueError, IndexError):
                pass
                
    print("=== STEP 1 RESULTS FOR M2STATE_FRACFIX_RESTART1R1R9 ===")
    print("RP Node 99999 RF1: %.8f kN (%.4f N)" % (rp_rf1, rp_rf1 * 1000.0))
    print("Bottom Nodes RF1 Sum: %.8f kN" % bot_rf1_sum)
    print("Bottom Nodes RF2 Sum: %.8f kN" % bot_rf2_sum)
    
    global_balance_error = abs(rp_rf1 + bot_rf1_sum)
    print("Global RF1 Force Balance Error: %.6e kN" % global_balance_error)
    
    rf_predecessor = 0.064100
    rel_diff = abs(rp_rf1 - rf_predecessor) / rf_predecessor
    print("Relative RF1 difference to MM predecessor (0.064100 kN): %.6f (%.3f%%)" % (rel_diff, rel_diff * 100.0))
    
    if rel_diff <= 0.02:
        print("FORCE CONTINUITY GATE: PASS (<= 2.0%)")
    else:
        print("FORCE CONTINUITY GATE: FAIL (> 2.0%)")
        
    sdv_count = text.count("SDV16")
    print("SDV16 occurrences in DAT file:", sdv_count)
    if sdv_count > 0:
        print("SDV16 OUTPUT INSTRUMENTATION GATE: PASS")
    else:
        print("SDV16 OUTPUT INSTRUMENTATION GATE: FAIL")

if __name__ == "__main__":
    main()
