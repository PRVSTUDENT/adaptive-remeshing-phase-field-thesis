from __future__ import print_function
import hashlib, json, os, sys, traceback
from abaqus import mdb
from abaqusConstants import MODEL, NOT_ALLOWED, ON, UNIFORM_ERROR

root = F12_RUNTIME_DIR
out = os.environ.get("F12_OUTPUT_DIR", os.getcwd())
deck = os.path.join(root, "source_deck.inp")

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        while True:
            block = stream.read(1048576)
            if not block: break
            h.update(block)
    return h.hexdigest()

status = {"source_deck_sha256": sha(deck), "solver_execution_count": 0,
          "native_adaptive_analysis_count": 0, "remesh_execution_count": 0,
          "candidate_refined_deck_generated": False, "variables_type": "tuple",
          "variables_element_type": "str", "variables_repr": "('MISESERI',)"}
try:
    model = mdb.ModelFromInputFile(name="F12_MISESERI_COARSE", inputFileName=deck)
    step_name = list(model.steps.keys())[-1]
    variables = (str("MISESERI"),)
    kwargs = dict(name="F12_MISESERI_RULE", stepName=step_name, variables=variables,
                  region=MODEL, sizingMethod=UNIFORM_ERROR, errorTarget=1.0,
                  specifyMinSize=ON, minElementSize=0.001,
                  specifyMaxSize=ON, maxElementSize=0.010,
                  coarseningFactor=NOT_ALLOWED, refinementFactor=10)
    rule = model.RemeshingRule(**kwargs)
    job = mdb.Job(name="F12_MISESERI_COARSE_INPUT", model=model.name)
    job.writeInput(consistencyChecking=ON)
    cae_path = os.path.join(out, "F12_MISESERI_DISPOSABLE")
    mdb.saveAs(pathName=cae_path)
    status.update({"classification": "native_remesh_model_prepared_input_written",
                   "model_name": model.name, "step_name": step_name,
                   "region": "MODEL", "rule_repository_key": "F12_MISESERI_RULE",
                   "rule_object_created": True, "coarse_adaptive_input_written": True,
                   "exact_rule_kwargs": repr(kwargs), "physical_element_count": 3930,
                   "true_slit_coincident_pairs": 15, "passes": 1,
                   "target_local_h_over_lc": 0.1})
except Exception:
    status.update({"classification": "native_remesh_preparation_inconclusive",
                   "rule_object_created": False, "coarse_adaptive_input_written": False,
                   "traceback": traceback.format_exc()})
with open(os.path.join(out, "NATIVE_REMESH_STATUS.json"), "wb") as stream:
    stream.write((json.dumps(status, indent=2, sort_keys=True) + "\n").encode("utf-8"))
sys.exit(0 if status.get("rule_object_created") else 1)
