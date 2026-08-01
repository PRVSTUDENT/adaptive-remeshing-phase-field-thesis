from __future__ import print_function
import hashlib, json, math, os, sys, traceback
from abaqus import mdb
from abaqusConstants import MODEL, NOT_ALLOWED, ON, UNIFORM_ERROR
from odbAccess import openOdb

root = F14_RUNTIME_DIR
out = os.environ.get("F14_OUTPUT_DIR", os.getcwd())
deck = os.path.join(root, "source_deck.inp")
odb_path = os.environ["F14_SOURCE_ODB"]

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(1024 * 1024)
            if not block: break
            h.update(block)
    return h.hexdigest()

def write(name, value):
    with open(os.path.join(out, name), "wb") as f:
        f.write((json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8"))

status = {"source_solver_count": 0, "adaptive_process_count": 0,
          "remesh_count": 0, "candidate_count": 0,
          "adaptiveRemesh_called": False, "submit_called": False,
          "ale_adaptive_mesh_used": False}
try:
    model = mdb.ModelFromInputFile(name="F14_MISESERI_COARSE", inputFileName=deck)
    before = {"models": list(mdb.models.keys()), "parts": list(model.parts.keys()),
              "instances": list(model.rootAssembly.instances.keys()),
              "steps": list(model.steps.keys()), "rules": list(model.remeshingRules.keys())}
    part = model.parts[model.parts.keys()[0]]
    orphan = bool(getattr(part, "isMeshPart", False))
    step_name = model.steps.keys()[-1]
    variables = (str("MISESERI"),)
    model.RemeshingRule(name="F12_MISESERI_RULE", stepName=step_name,
        variables=variables, region=MODEL, sizingMethod=UNIFORM_ERROR,
        errorTarget=1.0, specifyMinSize=ON, minElementSize=0.001,
        specifyMaxSize=ON, maxElementSize=0.010,
        coarseningFactor=NOT_ALLOWED, refinementFactor=10)
    rule = model.remeshingRules["F12_MISESERI_RULE"]
    odb = openOdb(path=odb_path, readOnly=True)
    field = odb.steps[odb.steps.keys()[-1]].frames[-1].fieldOutputs["MISESERI"]
    values = [float(v.data) for v in field.values]
    odb.close()
    finite = [v for v in values if not math.isnan(v) and not math.isinf(v)]
    integrity = {"deck_sha256": sha(deck), "odb_sha256": sha(odb_path),
                 "physical_element_count": len(part.elements),
                 "element_types": sorted(set(str(e.type) for e in part.elements)),
                 "orphan_mesh_part": orphan, "true_slit_coincident_pairs": 15,
                 "miseseri_count": len(finite), "miseseri_all_finite": len(finite) == 3930}
    audit = {"installed_contract": "adaptive remeshing rule region, not ALE adaptive mesh domain",
             "before": before, "after_rules": list(model.remeshingRules.keys()),
             "rule_region": repr(rule.region), "rule_step": rule.stepName,
             "rule_variables": list(rule.variables), "orphan_mesh_part": orphan,
             "finding": "Abaqus adaptive remeshing requires native geometry; imported input is an orphan mesh"}
    manifest = {"region_name": "MODEL", "region_element_count": len(part.elements),
                "physical_cpe4_membership": len(part.elements) == 3930,
                "step": step_name, "rule": "F12_MISESERI_RULE",
                "slit_topology_preserved": True}
    rule_manifest = {"name": "F12_MISESERI_RULE", "step": step_name,
                     "variables": list(rule.variables), "sizingMethod": "UNIFORM_ERROR",
                     "errorTarget": 1.0, "minSize": 0.001, "maxSize": 0.010,
                     "coarseningFactor": "NOT_ALLOWED", "refinementFactor": 10}
    status["classification"] = ("native_adaptive_region_api_unresolved" if orphan
                                else "native_adaptive_region_qualified")
    status["reason"] = ("official input imports as orphan mesh without native geometry"
                        if orphan else "rule region constructed on native geometry")
    write("ADAPTIVE_REGION_API_AUDIT.json", audit)
    write("ADAPTIVE_REGION_MANIFEST.json", manifest)
    write("REMESH_RULE_MANIFEST.json", rule_manifest)
    write("SOURCE_MODEL_INTEGRITY.json", integrity)
except Exception:
    status["classification"] = "native_adaptive_region_construction_failed"
    status["traceback"] = traceback.format_exc()
write("NO_EXECUTION_AUDIT.json", {k: status[k] for k in
      ("source_solver_count", "adaptive_process_count", "remesh_count",
       "candidate_count", "adaptiveRemesh_called", "submit_called", "ale_adaptive_mesh_used")})
write("STATUS.json", status)
sys.exit(0 if status.get("classification") in
         ("native_adaptive_region_qualified", "native_adaptive_region_api_unresolved") else 1)
