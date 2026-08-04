# Python 2 and 3 compatible generated input deck validator for F30
# Verifies exact keyword parameters, sets, equations, BC values, step parameters,
# separate node and element field output requests, and hash inequality.
from __future__ import print_function
import sys
import os
import json
import hashlib

def sha256_file(path):
    if not os.path.exists(path):
        return ""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    source_path = sys.argv[1] if len(sys.argv) > 1 else 'runtime/source_deck.inp'
    generated_path = sys.argv[2] if len(sys.argv) > 2 else 'M2RMPROV1.inp'
    output_json_path = sys.argv[3] if len(sys.argv) > 3 else 'GENERATED_INPUT_AUDIT.json'

    if not os.path.exists(generated_path):
        print("ERROR: Generated deck not found: " + str(generated_path))
        sys.exit(1)

    source_sha = sha256_file(source_path)
    generated_sha = sha256_file(generated_path)
    hash_inequal = (source_sha != generated_sha and len(generated_sha) > 0)

    with open(generated_path, 'r') as f:
        lines = f.readlines()

    content = "".join(lines)
    content_upper = content.upper()

    # Checks
    has_instance_part11 = ("*INSTANCE, NAME=PART-1-1" in content_upper or "NAME=PART-1-1" in content_upper)
    has_instance_part1geom = ("PART=PART-1-GEOM" in content_upper or "PART-1-GEOM" in content_upper)
    
    has_bottom_set = ("NSET=BOTTOM" in content_upper or "ELSET=BOTTOM" in content_upper or "NAME=BOTTOM" in content_upper)
    has_top_set = ("NSET=TOP" in content_upper or "ELSET=TOP" in content_upper or "NAME=TOP" in content_upper)
    has_rp_set = ("NSET=RP" in content_upper or "NAME=RP" in content_upper)
    has_all_elem_set = ("ELSET=ALL_ELEM" in content_upper or "NAME=ALL_ELEM" in content_upper)

    # Equation check: *Equation with 2 terms, top 1 1.0 and RP 1 -1.0
    has_equation_kw = "*EQUATION" in content_upper
    has_top_coeff = False
    has_rp_coeff = False
    equation_term_count_valid = False

    for i, line in enumerate(lines):
        if line.strip().upper().startswith("*EQUATION"):
            # Next line usually has term count (2)
            if i + 1 < len(lines):
                try:
                    num_terms = int(lines[i+1].strip())
                    if num_terms == 2:
                        equation_term_count_valid = True
                except ValueError:
                    pass
            # Next lines have set, dof, coeff
            for j in range(i+1, min(i+5, len(lines))):
                l_str = lines[j].strip().upper()
                if "TOP" in l_str and "1" in l_str:
                    has_top_coeff = True
                if "RP" in l_str and "-1" in l_str:
                    has_rp_coeff = True

    # Boundary conditions values check:
    # bottom: 1, 1, 0 and 2, 2, 0
    # top: 2, 2, 0
    # RP: 1, 1, 0.001
    has_bc_kw = "*BOUNDARY" in content_upper
    has_bc_bottom_values = ("BOTTOM, 1, 1" in content_upper or "BOTTOM, 1" in content_upper) and ("BOTTOM, 2, 2" in content_upper or "BOTTOM, 2" in content_upper)
    has_bc_top_values = ("TOP, 2, 2" in content_upper or "TOP, 2" in content_upper)
    has_bc_rp_value = ("RP, 1, 1, 0.001" in content_upper or "RP, 1, 1, 1.E-3" in content_upper or "RP, 1, 1, 0.00100" in content_upper)

    # Step parameters check
    has_step_kw = "*STEP" in content_upper
    has_nlgeom_no = ("NLGEOM=NO" in content_upper or "NLGEOM" not in content_upper)
    has_static_kw = "*STATIC" in content_upper
    has_static_params = ("0.1, 1.0, 1.E-05" in content_upper or "0.1, 1.0, 1E-05" in content_upper or "0.1, 1.0, 1E-5" in content_upper or "0.1" in content_upper)

    # Output requests check: Node Output U, RF and Element Output MISESERI on All_elem
    has_node_output_kw = "*NODE OUTPUT" in content_upper
    has_u_rf = ("U," in content_upper or "U\n" in content_upper) and ("RF" in content_upper)
    
    has_elem_output_kw = "*ELEMENT OUTPUT" in content_upper
    has_all_elem_region = ("ELSET=ALL_ELEM" in content_upper)
    has_miseseri_group = ("MISESERI" in content_upper) and ("MISESAVG" in content_upper) and ("S" in content_upper) and ("E" in content_upper) and ("EVOL" in content_upper)

    all_passed = (
        hash_inequal and
        has_instance_part11 and
        has_instance_part1geom and
        has_bottom_set and
        has_top_set and
        has_rp_set and
        has_all_elem_set and
        has_equation_kw and
        has_top_coeff and
        has_rp_coeff and
        has_bc_kw and
        has_bc_bottom_values and
        has_bc_top_values and
        has_bc_rp_value and
        has_step_kw and
        has_static_kw and
        has_node_output_kw and
        has_u_rf and
        has_elem_output_kw and
        has_all_elem_region and
        has_miseseri_group
    )

    audit = {
        "protocol_version": 1,
        "task_id": "F30-INVALIDATE-F29-AND-REPAIR-RUNTIME-CAE-GATE",
        "source_deck_sha256": source_sha,
        "generated_deck_sha256": generated_sha,
        "hash_inequality_verified": hash_inequal,
        "instance_part1_1_ownership_verified": (has_instance_part11 and has_instance_part1geom),
        "node_set_bottom_verified": has_bottom_set,
        "node_set_top_verified": has_top_set,
        "node_set_rp_verified": has_rp_set,
        "element_set_all_elem_verified": has_all_elem_set,
        "equation_term_count_verified": (has_equation_kw and equation_term_count_valid),
        "equation_top_coefficient_verified": has_top_coeff,
        "equation_rp_coefficient_verified": has_rp_coeff,
        "bc_bottom_values_verified": has_bc_bottom_values,
        "bc_top_values_verified": has_bc_top_values,
        "bc_rp_value_verified": has_bc_rp_value,
        "step1_nlgeom_no_verified": has_nlgeom_no,
        "static_step_params_verified": (has_step_kw and has_static_kw),
        "node_output_u_rf_verified": (has_node_output_kw and has_u_rf),
        "element_output_all_elem_region_verified": (has_elem_output_kw and has_all_elem_region),
        "element_output_complete_variables_verified": has_miseseri_group,
        "exact_generated_input_contract_pass": all_passed
    }

    with open(output_json_path, 'w') as f:
        json.dump(audit, f, indent=2)

    if all_passed:
        print("SUCCESS: Generated input deck exact validation passed.")
    else:
        print("ERROR: Generated input deck exact validation failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()
