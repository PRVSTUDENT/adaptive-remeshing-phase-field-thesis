#!/usr/bin/env python3
import json
from pathlib import Path
from scripts.validation.validate_mode_ii_reference_contract import parse_deck_structure

for case in ["M2REF_H0", "M2REF_H1", "M2REF_H2"]:
    p = Path(f"models/generated/mode_ii/reference_convergence/{case}/{case}.inp")
    if p.is_file():
        struct = parse_deck_structure(p)
        print(f"=== {case} ===")
        print(f"  Nodes: {struct['n_nodes']}")
        print(f"  Duplicates: {struct['duplicate_node_count']}")
        print(f"  RP Node ID: {struct['rp_node_id']} (Max Physical Node: {struct['max_physical_node_id']})")
        print(f"  RP Valid: {struct['rp_is_valid']}")
        print(f"  Zero-area Elems: {struct['zero_area_elems']}")
        print(f"  Undefined Node Refs: {struct['undefined_node_refs']}")
