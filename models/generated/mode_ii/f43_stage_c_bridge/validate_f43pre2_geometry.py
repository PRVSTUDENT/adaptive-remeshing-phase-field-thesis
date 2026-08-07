#!/usr/bin/env python3
"""
Offline Validator for F43PRE2_GEOM Geometry-Backed Mode-II Benchmark Source.
Audits canonical geometry parameters, benchmark manifests, pair contract, and orphan-mesh rejection.
"""

import sys
import os
import json
import hashlib

def validate_f43pre2_geometry(package_dir="."):
    package_dir = os.path.abspath(package_dir)
    source_manifest_path = os.path.join(package_dir, "F43PRE2_SOURCE_MANIFEST.json")
    
    results = {
        "source_manifest_exists": False,
        "geometry_backed_contract_valid": False,
        "orphan_mesh_prohibited": False,
        "deterministic_names_valid": False,
        "adaptivity_mesh_controls_valid": False,
        "benchmark_spec_verified": False,
        "reference_1384674_isolated": False,
        "overall_passed": False,
        "failures": []
    }

    if not os.path.exists(source_manifest_path):
        results["failures"].append("F43PRE2_SOURCE_MANIFEST.json missing in " + package_dir)
        return False, results

    results["source_manifest_exists"] = True

    with open(source_manifest_path, "r") as fp:
        manifest = json.load(fp)

    # 1. Non-orphan-mesh constraint & CAD geometry contract
    if manifest.get("builder_ready") and not manifest.get("orphan_mesh", True):
        results["orphan_mesh_prohibited"] = True
        results["geometry_backed_contract_valid"] = True
    else:
        results["failures"].append("Source manifest permits orphan mesh or geometry contract is unverified!")

    # 2. Deterministic names check
    model_name = manifest.get("model_name", manifest.get("benchmark_spec", {}).get("deterministic_names", {}).get("model_name"))
    part_name = manifest.get("part_name", manifest.get("benchmark_spec", {}).get("deterministic_names", {}).get("part_name"))
    step_name = manifest.get("step_name", manifest.get("benchmark_spec", {}).get("deterministic_names", {}).get("step_name"))

    if model_name == "ModeII_Geometry_Model" and part_name == "PlatePart" and step_name == "Step-1":
        results["deterministic_names_valid"] = True
    else:
        results["failures"].append("Deterministic names mismatch: model=" + str(model_name) + ", part=" + str(part_name))

    # 3. Adaptivity-compatible mesh controls (QUAD_DOMINATED, FREE, ADVANCING_FRONT, allowMapped=False)
    mesh_spec = manifest.get("benchmark_spec", {}).get("mesh", {})
    if (mesh_spec.get("elem_shape") == "QUAD_DOMINATED" and
        mesh_spec.get("technique") == "FREE" and
        mesh_spec.get("algorithm") == "ADVANCING_FRONT" and
        mesh_spec.get("allow_mapped") is False):
        results["adaptivity_mesh_controls_valid"] = True
    else:
        results["failures"].append("Mesh controls incompatible with native adaptivity: " + str(mesh_spec))

    # 4. Scientific Provenance Verification
    bench_spec = manifest.get("benchmark_spec", {})
    geo_src = bench_spec.get("benchmark_geometry_physics_source")
    wf_src = bench_spec.get("refinement_workflow_source")
    if (geo_src and "Molnar" in geo_src and wf_src and "Pandey-Kumar" in wf_src and
        bench_spec.get("width_mm") == 1.0 and
        bench_spec.get("height_mm") == 1.0 and
        bench_spec.get("notch_length_mm") == 0.5 and
        bench_spec.get("material", {}).get("youngs_modulus_MPa") == 210000.0):
        results["benchmark_spec_verified"] = True
    else:
        results["failures"].append("Canonical benchmark dimensions/provenance mismatch!")

    # 5. Isolation of 1384674 reference (must not be treated as direct remesh predecessor)
    pred_odb = manifest.get("predecessor_odb_sha256")
    if pred_odb != "3a201a6d405b92f4588e3d7e68177797706fd80ca9fa541e36ed0b10fdfb0534":
        results["reference_1384674_isolated"] = True
    else:
        results["failures"].append("Legacy ODB 1384674 incorrectly set as direct native remeshing predecessor!")

    results["cae_generated"] = manifest.get("cae_generated", False)
    results["cae_reopen_persistence_verified"] = manifest.get("cae_reopen_persistence_verified", False)
    results["seam_verified"] = manifest.get("seam_verified", False)
    elem_count = manifest.get("mesh_element_count", 0)
    results["element_count"] = elem_count
    results["cpe4_count"] = manifest.get("cpe4_count", 0)
    results["cpe3_count"] = manifest.get("cpe3_count", 0)

    if (results["cae_generated"] and
        results["cae_reopen_persistence_verified"] and
        results["seam_verified"] and
        3500 <= elem_count <= 4300):
        results["cae_eligibility_gate_passed"] = True
    else:
        results["failures"].append("CAE generation / persistence / seam / element count check failed! count=" + str(elem_count))

    results["overall_passed"] = (
        results["source_manifest_exists"] and
        results["geometry_backed_contract_valid"] and
        results["orphan_mesh_prohibited"] and
        results["deterministic_names_valid"] and
        results["adaptivity_mesh_controls_valid"] and
        results["benchmark_spec_verified"] and
        results["reference_1384674_isolated"] and
        results.get("cae_eligibility_gate_passed", False)
    )

    return results["overall_passed"], results

if __name__ == "__main__":
    pkg = sys.argv[1] if len(sys.argv) > 1 else "."
    passed, res = validate_f43pre2_geometry(pkg)
    print(json.dumps(res, indent=2))
    sys.exit(0 if passed else 1)
