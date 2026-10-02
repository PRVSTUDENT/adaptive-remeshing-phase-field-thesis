#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract serial/parallel comparison metrics from PK_M1_MINI dat/sta files."""

import sys
import os

def parse_dat_file(dat_path):
    if not os.path.exists(dat_path):
        print("File not found:", dat_path)
        return None

    results = {
        "checkpoints": [],
        "K0": None,
        "max_d": None,
        "max_H": None
    }

    with open(dat_path, "r") as f:
        lines = f.readlines()

    reading_rp = False
    for i, line in enumerate(lines):
        if "THE FOLLOWING TABLE IS PRINTED FOR NODES BELONGING TO NODE SET N_RP" in line:
            # Table starts a few lines down
            for j in range(i+1, min(i+10, len(lines))):
                parts = lines[j].strip().split()
                if len(parts) == 3 and parts[0] == "999999":
                    try:
                        u = float(parts[1])
                        rf = float(parts[2])
                        results["checkpoints"].append((u, rf))
                    except ValueError:
                        pass
                    break

    if results["checkpoints"]:
        u1, rf1 = results["checkpoints"][0]
        results["K0"] = rf1 / u1 if u1 > 0 else 0.0

    print("Parsed %s:" % dat_path)
    print("  K0 = %.6f kN/mm" % (results["K0"] if results["K0"] else 0.0))
    print("  Checkpoints (u, RF2):")
    for idx, (u, rf) in enumerate(results["checkpoints"]):
        print("    Inc %d: u = %.6e mm, RF2 = %.8e kN" % (idx+1, u, rf))

    return results

if __name__ == "__main__":
    dat = sys.argv[1] if len(sys.argv) > 1 else "PK_M1_MINI_SERIAL.dat"
    parse_dat_file(dat)
