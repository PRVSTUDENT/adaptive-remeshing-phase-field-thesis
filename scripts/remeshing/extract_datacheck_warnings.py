# -*- coding: utf-8 -*-
import re
import sys

def parse_warnings(dat_file):
    with open(dat_file, "r") as f:
        text = f.read()

    # Find all warning blocks starting with ***WARNING
    lines = text.splitlines()
    warning_blocks = []
    current_block = []
    in_warn = False

    for line in lines:
        if "***WARNING" in line:
            if current_block:
                warning_blocks.append("\n".join(current_block))
                current_block = []
            in_warn = True
            current_block.append(line)
        elif in_warn:
            if line.startswith("   ") or line.strip() == "":
                current_block.append(line)
            else:
                warning_blocks.append("\n".join(current_block))
                current_block = []
                in_warn = False

    if current_block:
        warning_blocks.append("\n".join(current_block))

    print("Found %d warning blocks:" % len(warning_blocks))
    for i, w in enumerate(warning_blocks, 1):
        print("=== Warning %d ===" % i)
        print(w.strip())
        print()

if __name__ == "__main__":
    dat = sys.argv[1] if len(sys.argv) > 1 else "PK_HOLE_METHOD_A_DC.dat"
    parse_warnings(dat)
