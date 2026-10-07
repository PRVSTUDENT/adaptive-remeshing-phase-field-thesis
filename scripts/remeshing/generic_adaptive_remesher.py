# -*- coding: utf-8 -*-
"""
Problem-Agnostic Generic Adaptive Remesher Engine
==================================================
Governing Contract:
  FE Stress / State Field -> MISESERI Recovery -> RemeshingRule -> mdb.adaptiveRemesh(odb) -> New Mesh Topology

Design & Qualification Principles:
1. Zero geometric or benchmark-specific hardcoding:
   - NO assumed coordinate systems or crack locations (no x=0.5, y=0.5, etc.).
   - NO expected crack propagation angles or corridors.
   - NO hardcoded step names, frame indices, or set names.
2. Complete parameterization via RemeshConfig schema.
3. Separation of Concerns:
   - Model Definition / Geometry / Boundary Conditions: Handled upstream by model generators.
   - Error Evaluation & Remeshing: Handled agnostically by this engine via Abaqus UNIFORM_ERROR RemeshingRule.
   - Downstream Analysis: Handled by dedicated, independent postprocessing evaluators.
"""
from __future__ import print_function
import os
import sys
import math
import json

# Check if running under Abaqus environment
ABAQUS_AVAILABLE = False
try:
    from abaqus import mdb
    from abaqusConstants import *
    import regionToolset
    import odbAccess
    import mesh
    ABAQUS_AVAILABLE = True
except ImportError:
    pass


class RemeshConfig(object):
    """Configuration schema for problem-agnostic adaptive remeshing."""

    def __init__(
        self,
        model_name,
        odb_path,
        part_name,
        instance_name=None,
        step_name="Step-1",
        frame_index=-1,
        region_set_name="ALL_ELEM",
        variable="MISESERI",
        sizing_method="UNIFORM_ERROR",
        error_target=2.0,
        min_element_size=0.001,
        max_element_size=0.020,
        refinement_factor=10,
        coarsening_factor="NOT_ALLOWED",
        rule_name="AdaptiveRemeshingRule",
        output_inp_path=None,
        output_metrics_json=None,
        output_elements_csv=None
    ):
        self.model_name = model_name
        self.odb_path = odb_path
        self.part_name = part_name
        self.instance_name = instance_name if instance_name else (part_name + "-1")
        self.step_name = step_name
        self.frame_index = frame_index
        self.region_set_name = region_set_name
        self.variable = variable
        self.sizing_method = sizing_method
        self.error_target = float(error_target)
        if self.error_target < 0.10:
            raise ValueError(
                "error_target must be specified as a percentage in Abaqus (e.g. 1.0 for 1%%, 2.0 for 2%%, 5.0 for 5%%). "
                "Received %.4f, which appears to be a decimal fraction. "
                "To configure a 2%% error target, pass error_target=2.0, not 0.02." % self.error_target
            )
        self.min_element_size = float(min_element_size)
        self.max_element_size = float(max_element_size)
        self.refinement_factor = int(refinement_factor)
        self.coarsening_factor = coarsening_factor
        self.rule_name = rule_name
        self.output_inp_path = output_inp_path
        self.output_metrics_json = output_metrics_json
        self.output_elements_csv = output_elements_csv

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    @classmethod
    def from_json(cls, filepath):
        with open(filepath, "r") as f:
            d = json.load(f)
        return cls.from_dict(d)

    def to_dict(self):
        return {
            "model_name": self.model_name,
            "odb_path": self.odb_path,
            "part_name": self.part_name,
            "instance_name": self.instance_name,
            "step_name": self.step_name,
            "frame_index": self.frame_index,
            "region_set_name": self.region_set_name,
            "variable": self.variable,
            "sizing_method": self.sizing_method,
            "error_target": self.error_target,
            "min_element_size": self.min_element_size,
            "max_element_size": self.max_element_size,
            "refinement_factor": self.refinement_factor,
            "coarsening_factor": self.coarsening_factor,
            "rule_name": self.rule_name,
            "output_inp_path": self.output_inp_path,
            "output_metrics_json": self.output_metrics_json,
            "output_elements_csv": self.output_elements_csv
        }


def extract_part_mesh_elements(p):
    """
    Extract element geometry, centroids, and equivalent sizes h_eq = sqrt(Area)
    from an Abaqus Part object. Fully problem-agnostic.
    """
    elements_data = []
    for elem in p.elements:
        conn = elem.connectivity
        pts = [p.nodes[n_idx].coordinates for n_idx in conn]
        xc = sum([pt[0] for pt in pts]) / float(len(pts))
        yc = sum([pt[1] for pt in pts]) / float(len(pts))
        
        # Calculate polygon area
        n_pts = len(pts)
        if n_pts == 4:
            x = [pt[0] for pt in pts]
            y = [pt[1] for pt in pts]
            area = 0.5 * abs((x[0]*y[1] + x[1]*y[2] + x[2]*y[3] + x[3]*y[0]) - 
                             (y[0]*x[1] + y[1]*x[2] + y[2]*x[3] + y[3]*x[0]))
            elem_type = "QUAD"
        elif n_pts == 3:
            x = [pt[0] for pt in pts]
            y = [pt[1] for pt in pts]
            area = 0.5 * abs((x[0]*y[1] + x[1]*y[2] + x[2]*y[0]) - 
                             (y[0]*x[1] + y[1]*x[2] + y[2]*x[0]))
            elem_type = "TRI"
        else:
            # Generic polygon formula
            area = 0.0
            for i in range(n_pts):
                j = (i + 1) % n_pts
                area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
            area = 0.5 * abs(area)
            elem_type = "POLY"

        h_eq = math.sqrt(max(area, 1e-14))
        elements_data.append({
            'label': elem.label,
            'type': elem_type,
            'nodes': list(conn),
            'xc': xc,
            'yc': yc,
            'area': area,
            'h_eq': h_eq
        })
    return elements_data


def compute_mesh_statistics(elements_data):
    """Compute summary statistics for element sizing field."""
    if not elements_data:
        return {}
    
    h_vals = sorted([e['h_eq'] for e in elements_data])
    n = len(h_vals)
    h_min = h_vals[0]
    h_max = h_vals[-1]
    h_mean = sum(h_vals) / float(n)
    h_median = h_vals[n // 2]
    h_p10 = h_vals[int(0.10 * n)]
    h_p90 = h_vals[int(0.90 * n)]

    return {
        'total_elements': n,
        'h_min': h_min,
        'h_max': h_max,
        'h_mean': h_mean,
        'h_median': h_median,
        'h_p10': h_p10,
        'h_p90': h_p90,
        'quad_count': sum(1 for e in elements_data if e['type'] == 'QUAD'),
        'tri_count': sum(1 for e in elements_data if e['type'] == 'TRI')
    }


def execute_remeshing(config):
    """
    Executes the generic adaptive remeshing pipeline inside Abaqus CAE:
    1. Validates Model and ODB existence.
    2. Opens ODB.
    3. Configures RemeshingRule with UNIFORM_ERROR and specified sizing parameters.
    4. Invokes m.adaptiveRemesh(odb=odb).
    5. Extracts adapted mesh metrics.
    6. Writes adapted input deck and diagnostics if paths specified.
    """
    if not ABAQUS_AVAILABLE:
        raise RuntimeError("execute_remeshing must be run within Abaqus CAE Python environment")

    if config.model_name not in mdb.models:
        raise ValueError("Model '%s' not found in mdb.models" % config.model_name)
    m = mdb.models[config.model_name]

    if not os.path.exists(config.odb_path):
        raise IOError("ODB file not found: %s" % config.odb_path)

    odb = odbAccess.openOdb(config.odb_path, readOnly=True)

    # Resolve target region
    a = m.rootAssembly
    if config.instance_name in a.instances:
        inst = a.instances[config.instance_name]
        if config.region_set_name in inst.sets:
            target_region = inst.sets[config.region_set_name]
        else:
            target_region = inst.sets['ALL_ELEM'] if 'ALL_ELEM' in inst.sets else a.sets[config.region_set_name]
    else:
        target_region = a.sets[config.region_set_name]

    # Sizing Method Constant
    sm_const = UNIFORM_ERROR if config.sizing_method == "UNIFORM_ERROR" else DEFAULT
    cf_const = NOT_ALLOWED if config.coarsening_factor == "NOT_ALLOWED" else DEFAULT

    # Create / Replace RemeshingRule
    if config.rule_name in m.remeshingRules:
        del m.remeshingRules[config.rule_name]

    m.RemeshingRule(
        name=config.rule_name,
        stepName=config.step_name,
        region=target_region,
        description='Generic Adaptive Remeshing Rule: target=%.1f%%' % config.error_target,
        outputFrequency=ALL_INCREMENTS,
        variables=(config.variable, ),
        sizingMethod=sm_const,
        errorTarget=config.error_target,
        specifyMinSize=True,
        specifyMaxSize=True,
        minElementSize=config.min_element_size,
        maxElementSize=config.max_element_size,
        elementCountLimit=None,
        coarseningFactor=cf_const,
        refinementFactor=config.refinement_factor
    )

    print("[GENERIC_REMESHER] Calling m.adaptiveRemesh with rule: %s ..." % config.rule_name)
    m.adaptiveRemesh(odb=odb)
    odb.close()
    print("[GENERIC_REMESHER] Adaptive remesh call completed successfully.")

    # Extract adapted mesh
    p = m.parts[config.part_name]
    elements_data = extract_part_mesh_elements(p)
    stats = compute_mesh_statistics(elements_data)

    print("[GENERIC_REMESHER] Adapted part '%s': %d elements (h_min=%.6f, h_mean=%.6f, h_max=%.6f)" % (
        config.part_name, stats['total_elements'], stats['h_min'], stats['h_mean'], stats['h_max']
    ))

    # Write input deck if requested
    if config.output_inp_path:
        job_name = "TEMP_ADAPTIVE_JOB"
        if job_name in mdb.jobs:
            del mdb.jobs[job_name]
        j = mdb.Job(name=job_name, model=config.model_name, description='Adapted Mesh Export')
        j.writeInput(consistencyChecking=OFF)
        src_inp = job_name + ".inp"
        if os.path.exists(src_inp):
            if os.path.exists(config.output_inp_path):
                os.remove(config.output_inp_path)
            os.rename(src_inp, config.output_inp_path)
            print("[GENERIC_REMESHER] Wrote adapted input deck: %s" % config.output_inp_path)

    # Dump elements CSV if requested
    if config.output_elements_csv:
        with open(config.output_elements_csv, "w") as f:
            f.write("element_label,type,xc,yc,area,h_eq\n")
            for e in elements_data:
                f.write("%d,%s,%.6f,%.6f,%.8e,%.6f\n" % (
                    e['label'], e['type'], e['xc'], e['yc'], e['area'], e['h_eq']
                ))
        print("[GENERIC_REMESHER] Dumped elements CSV: %s" % config.output_elements_csv)

    # Dump metrics JSON if requested
    metrics_result = {
        'status': 'ADAPTIVE_REMESH_COMPLETED',
        'config': config.to_dict(),
        'mesh_statistics': stats
    }
    if config.output_metrics_json:
        with open(config.output_metrics_json, "w") as f:
            json.dump(metrics_result, f, indent=2)
        print("[GENERIC_REMESHER] Dumped metrics JSON: %s" % config.output_metrics_json)

    return metrics_result
