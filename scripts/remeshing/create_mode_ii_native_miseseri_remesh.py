#!/usr/bin/env python
"""Audit-first native Abaqus MISESERI remeshing preparation.

The JSON document stored with a .yaml suffix is intentionally valid YAML and
parseable by Abaqus' standard-library Python without PyYAML.
"""
from __future__ import print_function

import argparse
import hashlib
import json
import os
import sys


REQUIRED_BASELINE = {
    "variables": ["MISESERI"],
    "sizingMethod": "UNIFORM_ERROR",
    "errorTarget": 1.0,
    "specifyMinSize": True,
    "specifyMaxSize": True,
    "coarseningFactor": "NOT_ALLOWED",
    "refinementFactor": 10,
}


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_config(path):
    with open(path) as stream:
        config = json.load(stream)
    baseline = config["publication_faithful_baseline"]
    for key, expected in REQUIRED_BASELINE.items():
        if baseline.get(key) != expected:
            raise ValueError("invalid publication baseline parameter %s" % key)
    if config["execution"]["solver_launch_allowed"]:
        raise ValueError("solver launch must remain disabled")
    return config


def audit(config, odb_path=None):
    result = {
        "classification": "native_miseseri_remesh_audit_pass",
        "mode": "audit",
        "source_job_id": config["source"]["job_id"],
        "source_odb_sha256_expected": config["source"]["odb_sha256"],
        "source_odb_verified": False,
        "rule_parameters": config["publication_faithful_baseline"],
        "project_selected": config["project_selected"],
        "native_remesh_executed": False,
        "refined_deck_generated": False,
        "solver_execution_count": 0,
    }
    if odb_path:
        actual = file_sha256(odb_path)
        if actual != config["source"]["odb_sha256"]:
            raise ValueError("official source ODB SHA-256 mismatch")
        result["source_odb_verified"] = True
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--odb")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--execute-native-remesh", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    if args.execute_native_remesh:
        raise SystemExit(
            "Native execution is intentionally blocked until the installed "
            "Abaqus/2023 RemeshingRule keyword audit is preserved."
        )
    result = audit(config, args.odb)
    parent = os.path.dirname(args.manifest)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(args.manifest, "w") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
