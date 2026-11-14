# -*- coding: utf-8 -*-
"""
Audit script for Task F1752 reconciliation:
1. Exact character and byte comparison of line 96209 between parent and continuation decks.
2. Complete full-file diff audit across all lines.
3. Node count reconciliation across physical mesh and reference point.
4. Peak force reconciliation across Job 1423271 and reference datasets.
5. In-depth Fortran source inspection of f42_mixed_uel.for COMMON blocks and restart handling.
"""

import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

parent_deck = REPO_ROOT / "models" / "pandey_kumar_mode1" / "224_f1734_case2_distal_refinement" / "PK_F1728_CASE_2_PROD.inp"
cont_deck = REPO_ROOT / "models" / "pandey_kumar_mode1" / "234_f1752_case2_continuation" / "PK_F1752_CASE_2_CONTINUATION.inp"
uel_src = REPO_ROOT / "models" / "pandey_kumar_mode1" / "234_f1752_case2_continuation" / "f42_mixed_uel.for"

print("=" * 80)
print("1. EXACT LINE 96209 AND FULL FILE DIFF AUDIT")
print("=" * 80)

with open(parent_deck, "r", encoding="utf-8") as f:
    parent_lines = f.readlines()
with open(cont_deck, "r", encoding="utf-8") as f:
    cont_lines = f.readlines()

print(f"Parent deck total lines: {len(parent_lines)}")
print(f"Cont   deck total lines: {len(cont_lines)}")

diffs = [(i, p, c) for i, (p, c) in enumerate(zip(parent_lines, cont_lines)) if p != c]
print(f"Total differing lines across entire 96,219-line file: {len(diffs)}")

for idx, p, c in diffs:
    print(f"\nDiff at line number {idx + 1}:")
    print(f"  Parent line: {repr(p)}")
    print(f"  Parent bytes: {[ord(ch) for ch in p]}")
    print(f"  Cont   line: {repr(c)}")
    print(f"  Cont   bytes: {[ord(ch) for ch in c]}")

    # Check individual numbers split by comma
    p_tokens = [t.strip() for t in p.strip().split(",")]
    c_tokens = [t.strip() for t in c.strip().split(",")]
    print(f"  Parent parsed tokens: {p_tokens}")
    print(f"  Cont   parsed tokens: {c_tokens}")

    for t_idx, (pt, ct) in enumerate(zip(p_tokens, c_tokens)):
        status = "IDENTICAL" if pt == ct else "MODIFIED"
        print(f"    Token {t_idx + 1}: parent={repr(pt)}, cont={repr(ct)} [{status}]")

print("\n" + "=" * 80)
print("2. NODE COUNT RECONCILIATION")
print("=" * 80)

# Count nodes in cont_deck
in_node_block = False
mesh_node_count = 0
all_node_ids = []
for line in cont_lines:
    if line.startswith("*NODE") or line.startswith("*Node"):
        in_node_block = True
        continue
    elif line.startswith("*"):
        in_node_block = False
        continue
    if in_node_block:
        parts = line.strip().split(",")
        if parts and parts[0].isdigit():
            all_node_ids.append(int(parts[0]))

print(f"Total node definitions found in *NODE block: {len(all_node_ids)}")
if all_node_ids:
    print(f"Node ID min: {min(all_node_ids)}, max: {max(all_node_ids)}")
    # Check if node 999999 is in all_node_ids
    has_999999 = 999999 in all_node_ids
    physical_mesh_nodes = [nid for nid in all_node_ids if nid != 999999]
    print(f"Is Node 999999 (RP) defined in *NODE block: {has_999999}")
    print(f"Physical mesh nodes count (excluding RP 999999): {len(physical_mesh_nodes)}")
    print(f"Total nodes defined in deck including RP: {len(all_node_ids)}")

print("\n" + "=" * 80)
print("3. PEAK FORCE RECONCILIATION")
print("=" * 80)

# Check Job 1423271 summary JSON if available
f1735_summary = REPO_ROOT / "results" / "validation" / "f1735_case2_odb_summary.json"
if f1735_summary.exists():
    import json
    with open(f1735_summary, "r") as f:
        f1735_data = json.load(f)
    print("F1735 summary keys:", list(f1735_data.keys()))
    if "rf2_max_kn" in f1735_data:
        print(f"Job 1423271 rf2_max_kn: {f1735_data['rf2_max_kn']} kN ({f1735_data['rf2_max_kn']*1000:.2f} N)")
    if "f_max_kn" in f1735_data:
        print(f"Job 1423271 f_max_kn: {f1735_data['f_max_kn']} kN ({f1735_data['f_max_kn']*1000:.2f} N)")
    if "peak_force" in f1735_data:
        print(f"Job 1423271 peak_force: {f1735_data['peak_force']}")

# Also check f1751_case2_diagnosis_summary.json
f1751_summary = REPO_ROOT / "results" / "validation" / "f1751_case2_diagnosis_summary.json"
if f1751_summary.exists():
    import json
    with open(f1751_summary, "r") as f:
        f1751_data = json.load(f)
    print("F1751 summary peak force data:", {k: v for k, v in f1751_data.items() if "force" in k.lower() or "rf" in k.lower() or "peak" in k.lower()})

print("\n" + "=" * 80)
print("4. FORTRAN SOURCE RESTART & COMMON BLOCK AUDIT")
print("=" * 80)

with open(uel_src, "r") as f:
    uel_lines = f.readlines()

print(f"Total lines in f42_mixed_uel.for: {len(uel_lines)}")

common_blocks = []
for i, line in enumerate(uel_lines):
    if "COMMON" in line.upper():
        common_blocks.append((i + 1, line.strip()))

print(f"Total COMMON block statements found: {len(common_blocks)}")
for line_no, stmt in common_blocks:
    print(f"  Line {line_no}: {stmt}")

# Check all occurrences of SV_H_COMMITTED and SV_H_TRIAL
sv_h_occurrences = []
for i, line in enumerate(uel_lines):
    if "SV_H_" in line.upper():
        sv_h_occurrences.append((i + 1, line.strip()))

print(f"\nAll occurrences of SV_H_ (total {len(sv_h_occurrences)}):")
for line_no, stmt in sv_h_occurrences:
    print(f"  Line {line_no}: {stmt}")

# Check any restart-related calls or keywords in UEL
restart_keywords = ["RESTART", "REST", "RES", "KSTEP", "KINC", "POSFIL", "URDFIL", "GETVRM"]
print("\nSubroutine keywords search:")
for kw in restart_keywords:
    matches = [(i + 1, line.strip()) for i, line in enumerate(uel_lines) if re.search(r'\b' + kw + r'\b', line, re.IGNORECASE)]
    print(f"  Keyword '{kw}': {len(matches)} occurrences")
    if kw in ["KSTEP", "KINC"]:
        for lno, txt in matches[:5]:
            print(f"    Line {lno}: {txt}")
