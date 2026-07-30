#!/usr/bin/env python
"""Qualify Abaqus/CAE RemeshingRule without launching an analysis.

This file intentionally uses Python-2.7-compatible syntax for Abaqus 2023.
"""
from __future__ import print_function

import argparse
import hashlib
import json
import os
import platform
import sys
import traceback


def sha256_file(path):
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
    with open(path, "r") as stream:
        json.load(stream)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--odb", required=True)
    parser.add_argument("--deck", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir)

    with open(args.config) as stream:
        config = json.load(stream)
    source = config["source"]
    baseline = config["publication_faithful_baseline"]
    odb_actual = sha256_file(args.odb)
    deck_actual = sha256_file(args.deck)

    audit = {
        "abaqus_python_version": sys.version,
        "platform": platform.platform(),
        "source_odb_path": os.path.abspath(args.odb),
        "source_odb_sha256_expected": source["odb_sha256"],
        "source_odb_sha256_actual": odb_actual,
        "source_odb_hash_match": odb_actual == source["odb_sha256"],
        "source_deck_sha256_expected": source["deck_sha256"],
        "source_deck_sha256_actual": deck_actual,
        "source_deck_hash_match": deck_actual == source["deck_sha256"],
        "api_owner": "mdb.models[name]",
        "api_method": "RemeshingRule",
        "accepted_keywords": [],
        "symbolic_constants": {},
        "rule_creation_passed": False,
        "native_remesh_execution_count": 0,
        "solver_execution_count": 0,
        "candidate_refined_deck_generated": False,
    }
    status = {
        "job_name": "M2RMAPI1",
        "pbs_job_id": os.environ.get("PBS_JOBID", "unknown"),
        "classification": "remeshing_api_incompatible",
        "source_odb_hash_match": audit["source_odb_hash_match"],
        "source_deck_hash_match": audit["source_deck_hash_match"],
        "rule_creation_passed": False,
        "native_remesh_execution_count": 0,
        "solver_execution_count": 0,
        "candidate_refined_deck_generated": False,
        "final_exit_code": 1,
    }
    rc = 1
    try:
        if not audit["source_odb_hash_match"]:
            status["classification"] = "source_odb_hash_mismatch"
            raise ValueError("source ODB hash mismatch")
        if not audit["source_deck_hash_match"]:
            status["classification"] = "source_deck_hash_mismatch"
            raise ValueError("source deck hash mismatch")

        from abaqus import Mdb, mdb
        from abaqusConstants import (
            MODEL, NOT_ALLOWED, OFF, ON, UNIFORM_ERROR
        )
        audit["symbolic_constants"] = {
            "MODEL": str(MODEL), "NOT_ALLOWED": str(NOT_ALLOWED),
            "OFF": str(OFF), "ON": str(ON),
            "UNIFORM_ERROR": str(UNIFORM_ERROR),
        }
        Mdb()
        model_name = "F6_REMESH_API_QUALIFICATION"
        model = mdb.Model(name=model_name)
        model.StaticStep(name="SOURCE_STEP", previous="Initial")
        keywords = {
            "name": "PUBLICATION_FAITHFUL_MISESERI",
            "stepName": "SOURCE_STEP",
            "variables": tuple(baseline["variables"]),
            "region": MODEL,
            "sizingMethod": UNIFORM_ERROR,
            "errorTarget": float(baseline["errorTarget"]),
            "specifyMinSize": ON,
            "minElementSize": float(config["project_selected"]["minimum_element_size_mm"]),
            "specifyMaxSize": ON,
            "maxElementSize": float(config["project_selected"]["maximum_element_size_mm"]),
            "coarseningFactor": NOT_ALLOWED,
            "refinementFactor": int(baseline["refinementFactor"]),
        }
        rule = model.RemeshingRule(**keywords)
        audit["accepted_keywords"] = sorted(keywords.keys())
        audit["rule_creation_passed"] = True
        audit["rule_repository_path"] = "mdb.models[%s].remeshingRules[%s]" % (
            model_name, rule.name)
        audit["rule_members"] = {}
        for key in sorted(keywords.keys()):
            if key == "name":
                continue
            try:
                audit["rule_members"][key] = str(getattr(rule, key))
            except Exception:
                audit["rule_members"][key] = "not_exposed"
        status["classification"] = "native_remesh_api_qualified_generation_deferred"
        status["rule_creation_passed"] = True
        status["final_exit_code"] = 0
        rc = 0
    except Exception as exc:
        audit["exception_type"] = exc.__class__.__name__
        audit["exception"] = str(exc)
        audit["traceback"] = traceback.format_exc()
        status["failure_reason"] = "%s: %s" % (exc.__class__.__name__, exc)

    manifest = {
        "classification": status["classification"],
        "publication_faithful_baseline": baseline,
        "project_selected": config["project_selected"],
        "source_job_id": source["job_id"],
        "rule_creation_passed": audit["rule_creation_passed"],
        "native_remesh_executed": False,
        "solver_execution_count": 0,
        "candidate_refined_deck_generated": False,
        "generation_deferred_reason": (
            "Generating a remeshed model requires a separate adaptive process; "
            "no solver or adaptivity execution is authorized."
        ),
    }
    write_json(os.path.join(args.output_dir, "API_AUDIT.json"), audit)
    write_json(os.path.join(args.output_dir, "REMESH_RULE_MANIFEST.json"), manifest)
    write_json(os.path.join(args.output_dir, "STATUS.json"), status)
    return rc


if __name__ == "__main__":
    sys.exit(main())
