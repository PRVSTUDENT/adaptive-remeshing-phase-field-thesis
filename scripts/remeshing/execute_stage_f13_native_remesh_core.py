from __future__ import print_function
import hashlib, json, os, sys, traceback
from abaqus import mdb
from abaqusConstants import MODEL, NOT_ALLOWED, ON, UNIFORM_ERROR

root = F13_RUNTIME_DIR
out = os.environ.get("F13_OUTPUT_DIR", os.getcwd())
deck = os.path.join(root, "source_deck.inp")
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
    job = mdb.Job(name="F13_MISESERI_SOURCE", model=model.name)
    process = mdb.AdaptivityProcess(name="F13_MISESERI_ADAPTIVITY", job=job,
                                    maxIterations=1)
    status["exact_api_commands"] = ["model.RemeshingRule(**%r)" % kwargs,
                                    "mdb.AdaptivityProcess(name='F13_MISESERI_ADAPTIVITY', job=job, maxIterations=1)",
                                    "process.submit(waitForCompletion=True)"]
    process.submit(waitForCompletion=True)
    status.update(source_solver_execution_count=1, adaptive_process_execution_count=1,
                  remesh_operation_count=1)
    candidates = [name for name in mdb.models.keys() if name != "F13_MISESERI_COARSE"]
    if candidates:
        candidate = mdb.models[candidates[-1]]
        out_job = mdb.Job(name="F13_MISESERI_CANDIDATE_INPUT", model=candidate.name)
        out_job.writeInput(consistencyChecking=ON)
        status.update(candidate_generated=True, generated_model_name=candidate.name,
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
