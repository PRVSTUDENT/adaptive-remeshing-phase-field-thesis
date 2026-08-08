#!/usr/bin/env python3
"""
Real Abaqus/CAE 2023 Kernel Rule Probe for F43REM4 Sensitivity Batch (PK1, PK5, MM).
Executes inside Abaqus 2023 kernel (abaqus cae noGUI=...).
Constructs each candidate RemeshingRule on a temporary writable copy of the source CAE,
reads back attributes, and exits BEFORE calling m.adaptiveRemesh(odb).
"""

import sys
import os
import json
import hashlib

from abaqus import *
from abaqusConstants import *
import caeModules

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BATCH_DIR = os.path.join(
    PROJECT_ROOT, "models", "generated", "mode_ii", "f43_stage_c_bridge", "remesh_sensitivity_batch"
)
SOURCE_CAE_PATH = os.path.join(
    PROJECT_ROOT, "models", "generated", "mode_ii", "f43_stage_c_bridge", "ModeII_Geometry_Source_Abaqus2023.cae"
)

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=== STARTING REAL ABAQUS 2023 KERNEL RULE PROBES FOR F43REM4 BATCH ===")
    
    expected_cae_sha = "0d5b32fe48b70ed0817e8b9c439bfdb39165dee5e8d157fcb6d0b3075efe1baa"
    actual_cae_sha = sha256_file(SOURCE_CAE_PATH)
    print("Source CAE SHA256:", actual_cae_sha)
    assert actual_cae_sha == expected_cae_sha, "Source CAE SHA mismatch"

    tmp_cae = "/tmp/f43rem4_real_abaqus_probe_work.cae"
    if os.path.exists(tmp_cae):
        os.remove(tmp_cae)

    import shutil
    shutil.copyfile(SOURCE_CAE_PATH, tmp_cae)
    openMdb(pathName=tmp_cae)
    m = mdb.models['ModeII_Geometry_Model']
    print("Opened MDB model: ModeII_Geometry_Model")

    assert 'Step-1' in m.steps, "Step-1 missing"
    
    probe_results = {}
    candidates = ["pk1", "pk5", "mm"]

    for cand_id in candidates:
        config_path = os.path.join(BATCH_DIR, "remesh_sensitivity_config_{}.json".format(cand_id))
        with open(config_path, "r") as f:
            cfg = json.load(f)

        rule_cfg = cfg["remeshing_rule"]
        rule_name = str(rule_cfg["name"])

        if rule_name in m.remeshingRules:
            del m.remeshingRules[rule_name]

        if rule_cfg["sizingMethod"] == "UNIFORM_ERROR":
            r = m.RemeshingRule(
                name=rule_name,
                stepName='Step-1',
                variables=('MISESERI',),
                region=MODEL,
                sizingMethod=UNIFORM_ERROR,
                errorTarget=float(rule_cfg["errorTarget"]),
                specifyMinSize=ON if rule_cfg["specifyMinSize"] else OFF,
                minElementSize=float(rule_cfg["minElementSize"]),
                specifyMaxSize=ON if rule_cfg["specifyMaxSize"] else OFF,
                maxElementSize=float(rule_cfg["maxElementSize"]),
                coarseningFactor=NOT_ALLOWED,
                refinementFactor=int(rule_cfg["refinementFactor"]),
            )
        elif rule_cfg["sizingMethod"] == "MINIMUM_MAXIMUM":
            r = m.RemeshingRule(
                name=rule_name,
                stepName='Step-1',
                variables=('MISESERI',),
                region=MODEL,
                sizingMethod=MINIMUM_MAXIMUM,
                maxSolutionErrorTarget=float(rule_cfg["maxSolutionErrorTarget"]),
                minSolutionErrorTarget=float(rule_cfg["minSolutionErrorTarget"]),
                meshBias=int(rule_cfg["meshBias"]),
                specifyMinSize=ON if rule_cfg["specifyMinSize"] else OFF,
                minElementSize=float(rule_cfg["minElementSize"]),
                specifyMaxSize=ON if rule_cfg["specifyMaxSize"] else OFF,
                maxElementSize=float(rule_cfg["maxElementSize"]),
            )

        print("Constructed real Abaqus RemeshingRule:", r.name)
        print("  sizingMethod:", r.sizingMethod)
        print("  specifyMinSize:", r.specifyMinSize, "minElementSize:", r.minElementSize)
        print("  specifyMaxSize:", r.specifyMaxSize, "maxElementSize:", r.maxElementSize)

        probe_results[cfg["candidate_id"]] = {
            "probe_status": "PASS",
            "rule_name": str(r.name),
            "sizingMethod": str(r.sizingMethod),
            "adaptiveRemesh_called": False,
            "Abaqus_Standard_called": False,
            "qsub_called": False
        }

    output_json_path = os.path.join(BATCH_DIR, "F43REM4_REAL_ABAQUS2023_PROBE_EVIDENCE.json")
    with open(output_json_path, "w") as f:
        json.dump(probe_results, f, indent=2)

    print("\nWrote real Abaqus 2023 kernel probe evidence to:", output_json_path)
    print("=== REAL ABAQUS 2023 KERNEL PROBES COMPLETE: PASS ===")

if __name__ == "__main__":
    main()
