#!/usr/bin/env python
"""Bounded Abaqus 2023 RemeshingRule variables-entry type qualification."""
from __future__ import print_function
import csv
import hashlib
import json
import os
import sys
import traceback

ODB_SHA = "bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac"
DECK_SHA = "a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2"
MAX_ATTEMPTS = 6


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def write_json(path, data):
    with open(path, "w") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")
    with open(path) as stream:
        json.load(stream)


def nested_types(value):
    if isinstance(value, (tuple, list)):
        return [type(item).__name__ for item in value]
    return []


def main():
    runtime = os.environ["F11_RUNTIME_DIR"]
    out = os.environ["F11_OUTPUT_DIRECTORY"]
    if not os.path.isdir(out):
        os.makedirs(out)
    odb_hash = sha256(os.path.join(runtime, "source.odb"))
    deck_hash = sha256(os.path.join(runtime, "source_deck.inp"))
    if odb_hash != ODB_SHA or deck_hash != DECK_SHA:
        raise ValueError("source hash mismatch")
    from abaqus import Mdb, mdb
    from abaqusConstants import MODEL, NOT_ALLOWED, ON, UNIFORM_ERROR
    Mdb()
    model = mdb.Model(name="F11_REMESH_TYPE")
    model.StaticStep(name="SOURCE_STEP", previous="Initial")
    doc = getattr(model.RemeshingRule, "__doc__", None)
    with open(os.path.join(out, "REMESHINGRULE_DOC_AUDIT.txt"), "w") as stream:
        stream.write("Abaqus Python: %s\n" % sys.version)
        stream.write("RemeshingRule.__doc__:\n%s\n" % (doc,))
        stream.write("MODEL=%r UNIFORM_ERROR=%r NOT_ALLOWED=%r ON=%r\n"
                     % (MODEL, UNIFORM_ERROR, NOT_ALLOWED, ON))
    uvalue = unicode("MISESERI")
    candidates = [
        ("byte_string", "MISESERI"),
        ("byte_string_tuple", ("MISESERI",)),
        ("ascii_unicode_tuple", (uvalue.encode("ascii"),)),
        ("variable_component_tuple", (("MISESERI", ""),)),
        ("byte_string_list", ["MISESERI"]),
    ]
    attempts = []
    accepted = None
    for sequence, item in enumerate(candidates, 1):
        label, variables = item
        kwargs = dict(
            name="F11_%02d_%s" % (sequence, label), stepName="SOURCE_STEP",
            variables=variables, region=MODEL, sizingMethod=UNIFORM_ERROR,
            errorTarget=1.0, specifyMinSize=ON, minElementSize=0.001,
            specifyMaxSize=ON, maxElementSize=0.010,
            coarseningFactor=NOT_ALLOWED, refinementFactor=10)
        row = {
            "sequence": sequence, "label": label,
            "python_type": type(variables).__name__,
            "nested_element_types": repr(nested_types(variables)),
            "repr": repr(variables),
            "exact_api_call": "model.RemeshingRule(**%r)" % kwargs,
            "exception": "", "rule_object_created": False}
        try:
            rule = model.RemeshingRule(**kwargs)
            row["rule_object_created"] = True
            accepted = {
                "label": label, "variables_type": type(variables).__name__,
                "nested_element_types": nested_types(variables),
                "variables_repr": repr(variables),
                "api_call": row["exact_api_call"], "repository_key": rule.name}
        except Exception as exc:
            row["exception"] = "%s: %s" % (type(exc).__name__, exc)
        attempts.append(row)
        if accepted:
            break
    with open(os.path.join(out, "REMESHINGRULE_TYPE_MATRIX.csv"), "wb") as stream:
        names = ["sequence", "label", "python_type", "nested_element_types",
                 "repr", "exact_api_call", "exception", "rule_object_created"]
        writer = csv.DictWriter(stream, fieldnames=names)
        writer.writeheader()
        writer.writerows(attempts)
    classification = ("remeshing_rule_type_contract_qualified" if accepted
                      else "remeshing_rule_variables_type_unresolved")
    decision = {
        "classification": classification, "attempt_count": len(attempts),
        "attempt_limit": MAX_ATTEMPTS, "accepted": accepted,
        "source_odb_sha256": odb_hash, "source_deck_sha256": deck_hash,
        "source_hashes_match": True, "installed_python_version": sys.version,
        "rule_object_created": bool(accepted), "solver_execution_count": 0,
        "native_adaptive_analysis_count": 0, "remesh_execution_count": 0,
        "candidate_deck_generated": False}
    write_json(os.path.join(out, "STATUS.json"), decision)
    return 0 if accepted else 1


try:
    RESULT = main()
except Exception:
    output = os.environ.get("F11_OUTPUT_DIRECTORY", ".")
    if not os.path.isdir(output):
        os.makedirs(output)
    write_json(os.path.join(output, "STATUS.json"), {
        "classification": "remeshing_rule_other_api_incompatibility",
        "traceback": traceback.format_exc(), "solver_execution_count": 0,
        "native_adaptive_analysis_count": 0, "remesh_execution_count": 0})
    RESULT = 2
sys.exit(RESULT)
