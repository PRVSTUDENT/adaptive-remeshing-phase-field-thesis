#!/usr/bin/env python
"""Controlled Abaqus/CAE 2023 RemeshingRule variables-type matrix."""
from __future__ import print_function
import json
import os
import sys
import traceback
import hashlib
from abaqus import mdb
from abaqusConstants import MODEL, NOT_ALLOWED, ON, UNIFORM_ERROR


def write_json(path, data):
    with open(path, "w") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def main():
    out = os.environ["F8_OUTPUT_DIRECTORY"]
    if not os.path.isdir(out):
        os.makedirs(out)
    model = mdb.Model(name="F8_TYPE_MATRIX")
    model.StaticStep(name="SOURCE_STEP", previous="Initial")
    doc = getattr(model.RemeshingRule, "__doc__", None)
    attempts = []
    candidates = [
        ("byte_str", "MISESERI"),
        ("tuple_byte_str", ("MISESERI",)),
        ("ascii_from_unicode", unicode("MISESERI").encode("ascii")),
        ("tuple_ascii_from_unicode", (unicode("MISESERI").encode("ascii"),)),
    ]
    accepted = None
    for label, value in candidates:
        kwargs = dict(
            name="F8_%s" % label,
            stepName="SOURCE_STEP",
            variables=value,
            region=MODEL,
            sizingMethod=UNIFORM_ERROR,
            errorTarget=1.0,
            specifyMinSize=ON,
            minElementSize=0.001,
            specifyMaxSize=ON,
            maxElementSize=0.01,
            coarseningFactor=NOT_ALLOWED,
            refinementFactor=10,
        )
        record = {
            "label": label,
            "python_type": type(value).__name__,
            "repr": repr(value),
            "exact_kwargs_repr": repr(kwargs),
            "created": False,
            "exception": None,
        }
        try:
            model.RemeshingRule(**kwargs)
            record["created"] = True
            accepted = label
        except Exception as exc:
            record["exception"] = "%s: %s" % (type(exc).__name__, exc)
        attempts.append(record)
        if accepted:
            break
    audit = {
        "classification": (
            "remeshing_rule_type_contract_qualified"
            if accepted else "remeshing_rule_variables_type_unresolved"
        ),
        "accepted_representation": accepted,
        "attempts": attempts,
        "remeshing_rule_doc": doc,
        "symbolic_constants": {
            "MODEL": repr(MODEL), "UNIFORM_ERROR": repr(UNIFORM_ERROR),
            "NOT_ALLOWED": repr(NOT_ALLOWED), "ON": repr(ON),
        },
        "solver_execution_count": 0,
        "native_adaptive_analysis_count": 0,
        "candidate_deck_generated": False,
        "python_version": sys.version,
        "source_odb_sha256": sha256(os.environ["F8_SOURCE_ODB"]),
        "source_deck_sha256": sha256(os.environ["F8_SOURCE_DECK"]),
        "source_odb_hash_match": (
            sha256(os.environ["F8_SOURCE_ODB"]) ==
            "bfcdbec08669774a9f80939d67c9c86ffe7df707e760450b08b1f6073fc588ac"
        ),
        "source_deck_hash_match": (
            sha256(os.environ["F8_SOURCE_DECK"]) ==
            "a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2"
        ),
    }
    write_json(os.path.join(out, "TYPE_MATRIX_AUDIT.json"), audit)
    return 0 if accepted else 1


try:
    RC = main()
except Exception:
    out = os.environ.get("F8_OUTPUT_DIRECTORY", ".")
    write_json(os.path.join(out, "TYPE_MATRIX_FATAL.json"),
               {"traceback": traceback.format_exc(), "solver_execution_count": 0})
    RC = 2
sys.exit(RC)
