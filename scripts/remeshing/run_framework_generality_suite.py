#!/usr/bin/env python3
"""
Test Driver for Generalized 2D Field-Driven Adaptive Remeshing Framework.
Executes the three required validation cases:
- Case 1: Mode-I off-axis hole plate with authentic precritical phase-field indicators.
- Case 2: Shifted circular hole plate with synthetic test field.
- Case 3: Plate without hole with synthetic test field.
"""

import os
import sys
sys.path.insert(0, os.path.abspath('.'))
import json
from scripts.remeshing.generalized_field_adaptive_remesher import (
    SpecimenGeometry2D,
    NumericalFieldSource,
    execute_adaptive_remeshing_pipeline
)

def load_mesh_from_inp(inp_path):
    nodes = {}
    elems = {}
    in_nodes = in_elems = False
    with open(inp_path) as f:
        for line in f:
            l = line.strip()
            if l.upper().startswith('*NODE'):
                in_nodes, in_elems = True, False
                continue
            elif l.upper().startswith('*ELEMENT'):
                in_nodes, in_elems = False, True
                continue
            elif l.startswith('*'):
                in_nodes = in_elems = False
                continue
            if in_nodes:
                p = [x.strip() for x in l.split(',') if x.strip()]
                if len(p) >= 3:
                    nodes[int(p[0])] = (float(p[1]), float(p[2]))
            elif in_elems:
                try:
                    p = [int(x.strip()) for x in l.split(',') if x.strip()]
                    if len(p) >= 4:
                        elems[p[0]] = p[1:]
                except ValueError:
                    pass
    return nodes, elems

def run_suite():
    out_dir = "models/pandey_kumar_mode1/176_method_a_plate_with_hole"
    base_mesh_inp = os.path.join(out_dir, "PK_HOLE_METHOD_A_PROD_PHYS.inp")
    damage_csv = "results/validation/f1642_pilot_localized_damage.csv"

    print("Loading base 46k physical mesh for field mapping...")
    nodes, elems = load_mesh_from_inp(base_mesh_inp)

    results = {}

    # -------------------------------------------------------------
    # CASE 1: Authentic Off-Axis Hole Benchmark
    # -------------------------------------------------------------
    print("\n>>> EXECUTING CASE 1: Mode-I Off-Axis Hole Plate (Authentic Indicators) <<<")
    geom1 = SpecimenGeometry2D(name="Plate_OffAxis_Hole", width=1.0, height=1.0)
    geom1.add_slit_notch(x_start=0.0, y=0.5, length=0.5, half_opening=0.001)
    geom1.add_circular_hole(center_x=0.65, center_y=0.65, radius=0.10)

    field1 = NumericalFieldSource(nodes, elems)
    field1.load_authentic_damage_csv(damage_csv)

    res1 = execute_adaptive_remeshing_pipeline(
        geometry=geom1,
        field_source=field1,
        indicator_strategy="damage_diffuse",
        indicator_threshold=0.05,
        buffer_radius=0.0225,
        job_prefix="PK_HOLE_METHOD_A_GEN",
        output_dir=out_dir,
        run_meshing=True
    )
    results["case_1_authentic_off_axis_hole"] = res1

    # -------------------------------------------------------------
    # CASE 2: Generality Test — Shifted Hole Geometry (Synthetic Field)
    # -------------------------------------------------------------
    print("\n>>> EXECUTING CASE 2: Shifted Hole Plate [SYNTHETIC TEST FIELD] <<<")
    geom2 = SpecimenGeometry2D(name="Plate_Shifted_Hole", width=1.0, height=1.0)
    geom2.add_slit_notch(x_start=0.0, y=0.5, length=0.45, half_opening=0.001)
    geom2.add_circular_hole(center_x=0.60, center_y=0.40, radius=0.08)

    field2 = NumericalFieldSource(nodes, elems)
    # Synthetic hotspots: notch tip (0.45, 0.50) and shifted hole flank (0.60, 0.32)
    field2.generate_synthetic_test_field(
        field_type="synthetic_damage",
        centers=[(0.45, 0.50), (0.68, 0.40)],
        radii=[0.05, 0.04],
        peak_values=[0.45, 0.25]
    )

    res2 = execute_adaptive_remeshing_pipeline(
        geometry=geom2,
        field_source=field2,
        indicator_strategy="synthetic_damage",
        indicator_threshold=0.10,
        buffer_radius=0.020,
        job_prefix="TEST_CASE2_SHIFTED_HOLE",
        output_dir=out_dir,
        run_meshing=True
    )
    results["case_2_shifted_hole_synthetic"] = res2

    # -------------------------------------------------------------
    # CASE 3: Generality Test — Notch Specimen Without Hole (Synthetic Field)
    # -------------------------------------------------------------
    print("\n>>> EXECUTING CASE 3: Plate Without Hole [SYNTHETIC TEST FIELD] <<<")
    geom3 = SpecimenGeometry2D(name="Plate_No_Hole", width=1.0, height=1.0)
    geom3.add_slit_notch(x_start=0.0, y=0.5, length=0.5, half_opening=0.001)
    # No holes added

    field3 = NumericalFieldSource(nodes, elems)
    # Synthetic hotspot: crack process zone extending horizontally from notch tip
    field3.generate_synthetic_test_field(
        field_type="synthetic_crack_band",
        centers=[(0.52, 0.50), (0.58, 0.50)],
        radii=[0.04, 0.04],
        peak_values=[0.50, 0.35]
    )

    res3 = execute_adaptive_remeshing_pipeline(
        geometry=geom3,
        field_source=field3,
        indicator_strategy="synthetic_crack_band",
        indicator_threshold=0.10,
        buffer_radius=0.020,
        job_prefix="TEST_CASE3_NO_HOLE",
        output_dir=out_dir,
        run_meshing=True
    )
    results["case_3_no_hole_synthetic"] = res3

    # Save summary JSON
    summary_path = "results/validation/framework_generality_summary.json"
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    print("\nSaved framework generality summary to:", summary_path)

if __name__ == '__main__':
    run_suite()
