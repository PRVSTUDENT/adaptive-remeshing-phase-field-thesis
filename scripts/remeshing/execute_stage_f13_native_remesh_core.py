from __future__ import print_function
import hashlib, json, math, os, sys, traceback
from abaqus import mdb
from abaqusConstants import MODEL, NOT_ALLOWED, ON, UNIFORM_ERROR
from odbAccess import openOdb

root = F13_RUNTIME_DIR
out = os.environ.get("F13_OUTPUT_DIR", os.getcwd())
deck = os.path.join(root, "source_deck.inp")
odb_path = os.environ["F13_SOURCE_ODB"]
status = {"source_solver_execution_count": 0, "adaptive_process_execution_count": 0,
          "remesh_operation_count": 0, "refined_mesh_solver_execution_count": 0,
          "candidate_generated": False, "variables_repr": "('MISESERI',)",
          "variables_element_type": "str"}
try:
    model = mdb.ModelFromInputFile(name="F13_MISESERI_COARSE", inputFileName=deck)
    step_name = list(model.steps.keys())[-1]
    variables = (str("MISESERI"),)
    kwargs = dict(name="F13_MISESERI_RULE", stepName=step_name, variables=variables,
                  region=MODEL, sizingMethod=UNIFORM_ERROR, errorTarget=1.0,
                  specifyMinSize=ON, minElementSize=0.001,
                  specifyMaxSize=ON, maxElementSize=0.010,
                  coarseningFactor=NOT_ALLOWED, refinementFactor=10)
    model.RemeshingRule(**kwargs)
    odb = openOdb(path=odb_path, readOnly=True)
    step = odb.steps[odb.steps.keys()[-1]]
    field = step.frames[-1].fieldOutputs["MISESERI"]
    values = [float(v.data) for v in field.values]
    finite = [v for v in values if not math.isnan(v) and not math.isinf(v)]
    if not finite or len(finite) != len(values):
        raise ValueError("MISESERI field is absent or non-finite")
    status["miseseri_statistics"] = {"count": len(finite), "minimum": min(finite),
                                     "maximum": max(finite)}
    status["exact_api_commands"] = ["model.RemeshingRule(**%r)" % kwargs,
                                    "odb = openOdb(path=F13_SOURCE_ODB, readOnly=True)",
                                    "model.adaptiveRemesh(odb)"]
    model.adaptiveRemesh(odb)
    odb.close()
    status.update(source_solver_execution_count=0, adaptive_process_execution_count=0,
                  remesh_operation_count=1)
    out_job = mdb.Job(name="F13_MISESERI_CANDIDATE_INPUT", model=model.name)
    out_job.writeInput(consistencyChecking=ON)
    candidate_path = os.path.join(os.getcwd(), "F13_MISESERI_CANDIDATE_INPUT.inp")
    if os.path.isfile(candidate_path):
        status.update(candidate_generated=True, generated_model_name=model.name,
                      candidate_input="F13_MISESERI_CANDIDATE_INPUT.inp",
                      classification="native_miseseri_remesh_execution_pass_candidate_generated")
    else:
        status["classification"] = "native_miseseri_remesh_operation_failed"
except Exception:
    status.update(classification="native_miseseri_execution_inconclusive",
                  traceback=traceback.format_exc())
with open(os.path.join(out, "NATIVE_REMESH_EXECUTION_STATUS.json"), "wb") as f:
    f.write((json.dumps(status, indent=2, sort_keys=True) + "\n").encode("utf-8"))
sys.exit(0 if status.get("candidate_generated") else 1)
