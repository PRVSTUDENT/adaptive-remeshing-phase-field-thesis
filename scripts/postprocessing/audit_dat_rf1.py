#!/usr/bin/env python3
"""
Inspect which node labels are present in the N O D E   O U T P U T tables in M2STATE_FRACFIX_RESTART1R1R5.dat,
and check whether any node has a non-NaN RF1, RF2, RF3, or U1, U2, U3 value.
"""

import sys
import os
import re
import json

def inspect_nodes_in_dat():
    dat_path = "M2STATE_FRACFIX_RESTART1R1R5.dat"
    with open(dat_path, 'r') as f:
        lines = f.readlines()
        
    in_table = False
    nodes_found = set()
    finite_rf_nodes = []
    
    for line in lines:
        if "N O D E   O U T P U T" in line:
            in_table = True
            continue
        if in_table:
            if "MAXIMUM" in line or "TOTAL" in line or "THE FOLLOWING TABLE" in line or "NODE FOOT-" in line or "NOTE" in line:
                continue
            if line.strip() == "":
                continue
            parts = line.split()
            if parts and parts[0].isdigit():
                node_id = int(parts[0])
                nodes_found.add(node_id)
                if len(parts) >= 7:
                    rf1_str = parts[4]
                    if rf1_str != "NaN" and rf1_str != "0.0000000E+00":
                        finite_rf_nodes.append((node_id, line.strip()))
                        
    print("Total unique nodes listed in DAT tables: {}".format(len(nodes_found)))
    print("Node min: {}, Node max: {}".format(min(nodes_found) if nodes_found else None, max(nodes_found) if nodes_found else None))
    print("Finite non-zero RF lines found: {}".format(len(finite_rf_nodes)))
    if finite_rf_nodes:
        print("Sample finite RF lines: {}".format(finite_rf_nodes[:5]))

if __name__ == "__main__":
    inspect_nodes_in_dat()
